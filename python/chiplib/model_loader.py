"""Load executable chip models directly from active DB packages."""

from __future__ import annotations

from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

from .core import Chip
from .db import db_root
from .loader import ImageFormat, ImageLoadError, load_memory


ModelFactory = Callable[[str], Chip]
ACTIVE_MODEL_GROUPS = ("74xx", "memory", "support")


class ModelLoadError(RuntimeError):
    """Raised when a DB package cannot provide a valid live Python model."""


def resolve_model_path(part: str, *, root: str | Path | None = None) -> Path:
    """Resolve one active package model, rejecting missing or duplicate parts."""

    requested = _clean_part(part)
    database = _database_root(root)
    matches = [
        database / group / requested / "simulation" / "model.py"
        for group in ACTIVE_MODEL_GROUPS
        if (database / group / requested / "simulation" / "model.py").is_file()
    ]
    if not matches:
        raise ModelLoadError(
            f"live DB model not found for {requested!r} under "
            f"{', '.join(ACTIVE_MODEL_GROUPS)} in {database}"
        )
    if len(matches) != 1:
        locations = ", ".join(path.as_posix() for path in matches)
        raise ModelLoadError(f"duplicate live DB model for {requested!r}: {locations}")

    path = matches[0].resolve()
    package_part = path.parents[1].name
    if package_part != requested:
        raise ModelLoadError(
            f"model package identity mismatch: requested {requested!r}, folder is {package_part!r}"
        )
    _validate_definition_identity(path, requested)
    return path


def load_model_factory(part: str, *, root: str | Path | None = None) -> ModelFactory:
    """Return the cached ``create`` factory from a package-local model."""

    requested = _clean_part(part)
    path = resolve_model_path(requested, root=root)
    return _load_factory(path, requested)


def create_live_db_chip(
    part: str,
    name: str = "U",
    *,
    root: str | Path | None = None,
) -> Chip:
    """Create a chip from its live DB package without using ``create_chip``."""

    requested = _clean_part(part)
    factory = load_model_factory(requested, root=root)
    try:
        chip = factory(name)
    except Exception as exc:
        raise ModelLoadError(
            f"live DB factory for {requested!r} failed while creating {name!r}: {exc}"
        ) from exc
    if not isinstance(chip, Chip):
        raise ModelLoadError(
            f"live DB factory for {requested!r} returned {type(chip).__name__}, expected Chip"
        )
    actual_part = str(getattr(chip, "part", "")).strip()
    if actual_part != requested:
        raise ModelLoadError(
            f"live DB factory identity mismatch for {requested!r}: chip part is {actual_part!r}"
        )
    chip.model_provenance = dict(getattr(factory, "model_provenance"))
    return chip


def load_live_chip_memory(
    chip: Chip,
    image: str | Path,
    *,
    offset: int = 0,
    fmt: ImageFormat = "auto",
    clear: int | None = None,
) -> int:
    """Load a public memory image without reaching into private model state."""

    data = getattr(chip, "data", None)
    if not isinstance(data, bytearray):
        raise ModelLoadError(
            f"live DB model {chip.part!r} does not expose a public mutable data bytearray"
        )
    try:
        return load_memory(chip, image, offset=offset, fmt=fmt, clear=clear)
    except (ImageLoadError, OSError, TypeError, ValueError) as exc:
        raise ModelLoadError(f"cannot load memory image into {chip.name} ({chip.part}): {exc}") from exc


def clear_model_cache() -> None:
    """Discard imported package-local model factories (primarily for tooling/tests)."""

    _load_factory.cache_clear()


@lru_cache(maxsize=None)
def _load_factory(path: Path, requested: str) -> ModelFactory:
    module = _load_module(path, requested)
    factory = getattr(module, "create", None)
    if not callable(factory):
        raise ModelLoadError(f"live DB model for {requested!r} has no callable create(): {path}")
    provenance = _provenance(path, requested)
    try:
        factory.model_provenance = provenance
    except (AttributeError, TypeError) as exc:
        raise ModelLoadError(f"cannot attach provenance to factory for {requested!r}: {path}") from exc
    return factory


def _load_module(path: Path, requested: str) -> ModuleType:
    digest = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:16]
    module_name = f"chiplib_live_db_{digest}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ModelLoadError(f"cannot create import spec for live DB model {requested!r}: {path}")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise ModelLoadError(f"cannot import live DB model {requested!r} from {path}: {exc}") from exc
    return module


def _validate_definition_identity(model_path: Path, requested: str) -> None:
    definition_path = model_path.parents[1] / "definition" / "definition.json"
    if not definition_path.is_file():
        raise ModelLoadError(f"definition missing for live DB model {requested!r}: {definition_path}")
    try:
        definition = json.loads(definition_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelLoadError(f"cannot read definition for live DB model {requested!r}: {exc}") from exc
    if not isinstance(definition, dict):
        raise ModelLoadError(f"definition for live DB model {requested!r} must be a JSON object")
    actual_part = str(definition.get("part", "")).strip()
    if actual_part != requested:
        raise ModelLoadError(
            f"definition identity mismatch for {requested!r}: part is {actual_part!r} in {definition_path}"
        )


def _provenance(path: Path, part: str) -> dict[str, Any]:
    database = path.parents[3]
    return {
        "source": "live_db_package",
        "part": part,
        "group": path.parents[2].name,
        "model_path": path.relative_to(database.parent).as_posix(),
        "definition_path": (path.parents[1] / "definition" / "definition.json")
        .relative_to(database.parent)
        .as_posix(),
    }


def _database_root(root: str | Path | None) -> Path:
    return (Path(root) if root is not None else db_root()).expanduser().resolve()


def _clean_part(part: str) -> str:
    clean = str(part).strip()
    if not clean or clean in {".", ".."} or Path(clean).name != clean:
        raise ModelLoadError(f"invalid component part identity: {part!r}")
    return clean
