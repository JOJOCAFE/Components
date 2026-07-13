# Components Board — first local workbench

This is the smallest real Board client: Drawing is on the left, readable
Component text is upper-right, and a short bounded Terminal is lower-right.
It has no npm dependencies, no plugin host, no network requirement after
startup, and no hidden canvas circuit model.

Run from the Components repository root:

```sh
PYTHONPATH=python python3 -B -m chiplib.api --http --host 127.0.0.1 --port 8765
```

Open <http://127.0.0.1:8765/>. The Python API serves this folder, so the Board
and Component service share one local origin.

First slice included:

- the real NOT-gate Component fixture, parser, resolver, Board JSON view, and
  declared `inversion` runtime test;
- local draft autosave/recovery through browser local storage;
- selection-to-readable-source highlighting and a Learning Lens explanation;
- bounded Terminal commands: `run`, `drive`, `watch`, `connect`,
  `disconnect`, and `help`; and
- checked Board/Terminal connect/disconnect source patches. An invalid edit
  leaves text and resolved topology unchanged.

This is intentionally a dependency-free browser proof. A later Tauri wrapper
must consume this same local JSON/source-edit boundary; it must not introduce
a second circuit model.
