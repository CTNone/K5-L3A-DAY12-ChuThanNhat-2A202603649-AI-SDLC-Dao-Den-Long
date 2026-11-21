# Phase 4 evidence

- `verify.log` — kết quả `python tools/verify_phase1.py`, `verify_phase2.py`,
  `verify_phase3.py`, `verify_phase4.py` và `py_compile`.
- `bench.json` — lần đo benchmark thật, ghi rõ `mode: headless-simulation` kèm CPU/GPU/RAM.
- `machine.txt` — cấu hình máy đo (OS, CPU, GPU, RAM, Python).
- `soak.json` — 10 đêm trong một tiến trình, không input.
- `clean-clone.log` — clone sạch từ remote và chạy lại toàn bộ kiểm chứng.
- `demo.mp4` — video demo (ở `docs/demo/demo.mp4`).
- `web-sha256.txt` — checksum của gói web `v1.0.0` trong Release.
- `web-sha256-v1.0.1.txt` — checksum của gói web tự chạy `v1.0.1`.

Số đo dev không phải ngưỡng máy chấm. Không sửa tay output.
