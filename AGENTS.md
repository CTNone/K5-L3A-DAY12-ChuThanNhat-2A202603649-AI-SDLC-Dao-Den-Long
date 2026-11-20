# Agent notes

- Read `PRD-0.md`, `TEST-CONTRACT-v1.0.md`, `game.contract.json`, and `docs/notes/phase-1-assumptions.md` before changing gameplay.
- Keep the simulation deterministic at 60 Hz and preserve the headless CLI and JSONL contract. Update tuning in both `game.py` and `game.contract.json` together.
- Run `python -m py_compile game.py tools/verify_phase1.py tools/capture_phase1_evidence.py` and `python tools/verify_phase1.py` after gameplay changes.
- Regenerate checked-in Phase 1 artifacts only with `python tools/capture_phase1_evidence.py`; never edit captured output to make a check pass.
- Keep GUI-only decoration out of headless simulation state and output.
- Record changed assumptions, replaced tests, and any incomplete requirement in the phase notes.
