# Phase 4 — Giả định

- `bench.json` và `soak.json` trong repo là số đo thật của máy dev, không phải ngưỡng
  máy chấm. Seed mặc định của CLI là 1; ticket gợi ý 20261121 nhưng lần đo đã dùng 1
  và ghi rõ trong file.
- Cấu hình máy đo được lưu ở `docs/proof/phase-4/machine.txt` (CPU/GPU/RAM/OS/Python);
  `bench.json` cũng ghi các trường `cpu`, `gpu`, `ram_mb`, `resolution`, `python`.
- Benchmark dùng mô phỏng headless vì môi trường dev dùng Intel HD 4600 và không có
  phép đo GPU ổn định. Không sửa số đo để đạt ngưỡng.
- Bảng điểm GUI lưu ở `user://leaderboard.json` (thư mục dữ liệu Godot); CLI export
  đọc `leaderboard.json` ở repo hoặc `--leaderboard-file`.
- Tên 3–12 ký tự, giữ một entry tốt nhất cho mỗi tên; nếu trùng điểm, người đạt sớm hơn
  đứng trước.
- Admin là công cụ dev, không phải bảo mật. Bật admin sẽ tắt ghi bảng điểm.
- Cỡ chữ 125% được lưu và áp dụng sau khi mở lại cửa sổ; không rebuild toàn bộ UI
  trong cùng phiên để tránh mất trạng thái.
