# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

Proxygenesis AI is a Python CLI application for intelligent proxy discovery, validation, and classification using machine learning. There is no web UI, no database, and no Docker setup. All code lives under `proxygenesis_ai/`.

### Running the application

All commands must be run from `proxygenesis_ai/` (modules use relative imports):

- **Full pipeline:** `python3 main.py` (runs 3 cycles by default, each ~60s apart)
- **Quick demo:** `python3 demo.py` (single cycle, 20 proxies — fastest way to verify the system works)
- **Integration tests:** `python3 test_system.py` (tests scraper, checker, trainer individually)
- **Individual modules:** `python3 scraper.py`, `python3 checker.py`, `python3 trainer.py`

See `proxygenesis_ai/README.md` for full usage details.

### Non-obvious caveats

- **Working directory matters:** All scripts use relative imports (`from scraper import ...`), so they must be invoked with `proxygenesis_ai/` as the cwd, not from the repo root.
- **Network-dependent:** The scraper and checker contact external proxy list URLs and test proxies against `httpbin.org`. Some sources return 404 — this is expected and handled gracefully.
- **ML trainer minimum samples:** The trainer requires at least 10 samples to train. When running `test_system.py` (which only validates 5 proxies), the trainer will report "Dados insuficientes" — this is expected behavior, not an error.
- **No formal test framework:** There is no pytest/unittest suite. `test_system.py` is a manual integration script. Syntax/compile checks can be done via `py_compile` or `flake8`.
- **No linter configured in repo:** Install `flake8` if needed: `pip install flake8`. Run with `flake8 --max-line-length=150 *.py`.
- **Optional external services (Shodan, masscan):** These are not required for basic operation. The system falls back gracefully when they are unavailable.
- **Data files:** `data/` and `models/` directories are created automatically on first run.
