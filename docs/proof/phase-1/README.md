# Phase 1 verification evidence

Captured from the current working tree on Windows with Python 3.11.9. Recreate the headless artifacts with:

```powershell
python -m py_compile game.py tools/verify_phase1.py tools/capture_phase1_evidence.py
python tools/verify_phase1.py
python tools/capture_phase1_evidence.py
```

`tools/capture_phase1_evidence.py` writes the exact JSON scenario/input files, raw JSONL, stderr, boundary check, and same-seed comparison beside this file. The harness also checks the pickup/deposit, pulse, hit, win, loss, tick-limit, snapshot cadence, zero-tick and invalid-input results before it reports success.

| Requirement | Evidence | Result |
|---|---|---|
| Build/parse | command above; `python -m py_compile ...` | Pass, exit 0 |
| Tick 0 before input, one step after pulse input | `pulse-inputs.json`, `pulse.jsonl` | Pass: initial snapshot tick 0, pulse event and state snapshot tick 1 |
| Pickup and light a lantern | `pickup-deposit-scenario.json`, `pickup-deposit-inputs.json`, `pickup-deposit.jsonl` | Pass: five pickup events and `lantern_lit` |
| Pulse | `pulse-scenario.json`, `pulse-inputs.json`, `pulse.jsonl` | Pass: consumes one carried mote and stuns Sx |
| Hit and drop carried motes | `hit-loss-scenario.json`, `hit-loss.jsonl` | Pass: `player_hit`, flames 2, dropped 2 |
| Loss and win endings | `loss.jsonl`, `win.jsonl` | Pass: `game_over` events report `lost/no_flames` and `won/all_lit`; end rows report the matching terminal states |
| `--ticks` cap, snapshot interval and JSONL | `boundary.jsonl`, `zero-ticks.jsonl` | Pass: ticks 0 with cap 0; cap 5 ends at tick 5; interval 2 emits snapshots 0, 2, 4; each line parses as JSON |
| Exit code for bad input | `bad-input.json`, `bad-input-stderr.txt`, `commands-and-status.txt` | Pass: exit 2 and diagnostic on stderr |
| Identical repeated run | `determinism-a.jsonl`, `determinism-b.jsonl`, `determinism-compare.txt` | Pass: byte-identical with seed 909, same scenario/inputs |
| GUI gameplay, HUD and outcome | `gui-start.png`, `gui-win.png` (screenshots supplied by the player) | Pass by player-provided evidence: start HUD shows 0/5 lanterns at 04:58; win screen shows 5/5 and “ĐẢO ĐÃ SÁNG!” at 03:35. The player reports playing continuously from start to win. |
| GUI loss | `gui-loss.png` (screenshot supplied by the player) | Pass by player-provided evidence: HUD shows 0 flames and “ĐÊM TỐI THẮNG THẾ” at 04:50; player reports a shade stayed in contact until all flames were lost. |

All `.jsonl` files are direct program output. Empty `*-stderr.txt` means the successful process emitted no stderr. `bad-input.jsonl` is not expected because input validation fails before writing output.

## AI usage and review notes

- This verification pass used Codex to inspect the repository, run the existing harness, add a repeatable evidence-capture script and review its outputs. No external asset or service was used.
- For the request “Ghi giả định, nhật ký AI, ước tính token/chi phí và lỗi AI đã phát hiện,” the player estimates spending **about 10% of quota** while using **GPT-6 Luna Medium**. This is the player's quota estimate, not measured token usage; no token count or currency cost can be derived from available telemetry. Earlier project AI usage is not reconstructable from these files.
- Review caught three evidence-script defects before final capture: the original walk duration stopped short of the lantern; the expected loss reason was written as `flames` while the game emits `no_flames`; and the zero-tick check assumed the first JSONL row was a snapshot, despite startup events preceding it. The scenario duration and assertions were corrected, and the capture script now finds the tick-0 snapshot by type and asserts that pickup/deposit and terminal events appear in raw JSONL.
- Player observation: standing still can lead to a loss as shades continue chasing and attacking; the game grants 2 seconds of invulnerability after each hit. The player also observed shades gathering at the first lit lantern and stopping. This matches the current code: a lit lantern creates a 3 m safe radius and the shade update skips movement whenever a shade is inside that radius. This is intentional protection, but shades already in the radius can remain frozen there indefinitely, so the implementation can look like they are stuck. This behavior should be reviewed as a gameplay issue.
- The user-provided screenshots now cover GUI start, win and loss states. No continuous video clip was supplied; loss is also covered by the headless `loss.jsonl` scenario.
