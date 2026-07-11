"""Focused tests for live DB package-local model loading."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from chiplib import (
    ModelLoadError,
    clear_model_cache,
    create_live_db_chip,
    load_model_factory,
    resolve_model_path,
)
from chiplib.model_loader import load_live_chip_memory


class ModelLoaderTests(unittest.TestCase):
    def tearDown(self) -> None:
        clear_model_cache()

    def test_resolves_each_active_model_group_deterministically(self) -> None:
        expected = {
            "74HC00": ("74xx", "74HC00"),
            "AT28C256": ("memory", "AT28C256"),
            "LM358": ("support", "LM358"),
        }
        for part, (group, folder) in expected.items():
            with self.subTest(part=part):
                path = resolve_model_path(part)
                self.assertEqual(path.parts[-4:], (group, folder, "simulation", "model.py"))
                self.assertEqual(path, resolve_model_path(part))

    def test_factory_is_cached_and_chip_carries_provenance(self) -> None:
        first = load_model_factory("74HC00")
        second = load_model_factory("74HC00")
        self.assertIs(first, second)
        self.assertEqual(first.model_provenance["source"], "live_db_package")
        self.assertEqual(first.model_provenance["part"], "74HC00")

        chip = create_live_db_chip("74HC00", "U7")
        self.assertEqual(chip.name, "U7")
        self.assertEqual(chip.part, "74HC00")
        self.assertEqual(chip.model_provenance, first.model_provenance)

        clear_model_cache()
        self.assertIsNot(first, load_model_factory("74HC00"))

    def test_public_memory_loader_accepts_memory_and_rejects_private_state(self) -> None:
        memory = create_live_db_chip("AT28C256", "ROM1")
        with tempfile.NamedTemporaryFile(suffix=".bin") as image:
            image.write(b"\x12\x34")
            image.flush()
            self.assertEqual(2, load_live_chip_memory(memory, image.name, offset=3))
        self.assertEqual(b"\x12\x34", bytes(memory.data[3:5]))

        logic = create_live_db_chip("74HC00", "U1")
        with self.assertRaisesRegex(ModelLoadError, "public mutable data bytearray"):
            load_live_chip_memory(logic, "unused.bin")

    def test_missing_model_has_clear_error(self) -> None:
        with self.assertRaisesRegex(ModelLoadError, "live DB model not found.*NO_SUCH_PART"):
            resolve_model_path("NO_SUCH_PART")

    def test_rejects_invalid_part_paths(self) -> None:
        with self.assertRaisesRegex(ModelLoadError, "invalid component part identity"):
            resolve_model_path("../74HC00")

    def test_rejects_duplicate_package_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_package(root, "74xx", "DUP")
            self._write_package(root, "memory", "DUP")
            with self.assertRaisesRegex(ModelLoadError, "duplicate live DB model.*DUP"):
                resolve_model_path("DUP", root=root)

    def test_rejects_definition_identity_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_package(root, "support", "EXPECTED", definition_part="OTHER")
            with self.assertRaisesRegex(ModelLoadError, "definition identity mismatch"):
                resolve_model_path("EXPECTED", root=root)

    def test_rejects_missing_factory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_package(root, "support", "NOFACTORY", model="value = 1\n")
            with self.assertRaisesRegex(ModelLoadError, "no callable create"):
                load_model_factory("NOFACTORY", root=root)

    def test_rejects_factory_part_identity_mismatch(self) -> None:
        model = """\
from chiplib.core import Chip, pins_from
class Wrong(Chip):
    part = "OTHER"
    def __init__(self, name="U"):
        super().__init__(name, pins_from({}))
def create(name="U"):
    return Wrong(name)
"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_package(root, "74xx", "EXPECTED", model=model)
            with self.assertRaisesRegex(ModelLoadError, "factory identity mismatch"):
                create_live_db_chip("EXPECTED", root=root)

    @staticmethod
    def _write_package(
        root: Path,
        group: str,
        part: str,
        *,
        definition_part: str | None = None,
        model: str = "def create(name='U'):\n    return None\n",
    ) -> None:
        package = root / group / part
        (package / "definition").mkdir(parents=True)
        (package / "simulation").mkdir()
        (package / "definition" / "definition.json").write_text(
            json.dumps({"part": definition_part or part}), encoding="utf-8"
        )
        (package / "simulation" / "model.py").write_text(model, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
