# Agent notes

- Read `PRD-0.md`, `TEST-CONTRACT-v1.0.md`, `game.contract.json`, `docs/notes/phase-1-assumptions.md`, `docs/notes/phase-2-spec.md`, `docs/notes/phase-2-assumptions.md`, and `shared/maps/night1..3.json` before changing gameplay.
- Keep the simulation deterministic at 60 Hz and preserve the headless CLI and JSONL contract. Update tuning in `game.py`, `game.contract.json`, and `shared/maps/*.json` together.
- `python game.py` is the unified 3D web launcher; `python game.py --headless ...` is the contract runner. Do not reintroduce Tkinter or pseudo-3D as the default GUI.
- Run `python -m py_compile game.py tools/verify_phase1.py tools/capture_phase1_evidence.py` and `python tools/verify_phase1.py` after gameplay changes; once added, also run the Phase 2 verifier/evidence tools.
- Regenerate checked-in artifacts only with `python tools/capture_phase1_evidence.py` or `python tools/capture_phase2_evidence.py`; never edit captured output to make a check pass.
- Build the web GUI with `python tools/build_web.py` and serve it locally with `python tools/serve_web.py`. Do not commit `build/`, `godot/.godot/`, or export templates.
- Keep GUI-only decoration out of headless simulation state and output.
- Record changed assumptions, replaced tests, and any incomplete requirement in the phase notes.
