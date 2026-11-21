# Phase 4 — Spec và tiêu chí nghiệm thu

## Mục tiêu

Phát hành `v1.0.0`: contract v1.3, benchmark/soak, bảng điểm top 10, accessibility,
audio ổn định trên web, admin cheat có kiểm soát, đóng gói và tài liệu.

## Đã làm

- `game.contract.json` lên `1.3`, thêm `bench_cmd`, `soak_cmd`, `leaderboard_cmd`,
  `leaderboard`, `accessibility`, `input`; giữ nguyên `tuning` và `ui` cũ.
- `python game.py --bench --bench-out bench.json`: đo 60 giây mô phỏng với 200 shade,
  100 mote, seed 20261121 (mặc định CLI là 1; lần đo trong repo dùng seed 1 và ghi rõ
  `mode: headless-simulation`).
- `python game.py --soak --soak-out soak.json`: 10 đêm trong một tiến trình, không input,
  seed 1, ghi crashes/RSS/thời gian/kết quả từng đêm.
- `leaderboard.py`: top 10, tên 3–12 ký tự, sort theo score rồi thời điểm đạt sớm hơn,
  schema `score`, `nights_won`, `achieved_at` (ISO-8601 có timezone), `seed`.
- `python game.py --export-leaderboard out.json`: xuất mảng đã sort.
- GUI: nhập tên sau khi thua hoặc thắng Đêm 3; lưu `user://leaderboard.json`;
  admin không lưu bảng điểm.
- Audio: bỏ autoplay trong `_ready`, thêm `unlock()` và gọi từ input/`start_night`.
- Nhân vật mặc định quay theo camera; setting `Hướng nhân vật` đổi sang hướng di chuyển.
- Admin checkbox luôn hiện; cheat: bất tử, dầu vô hạn, thắng đêm hiện tại, tốc độ ×2,
  hiện đèn/đường; hotkey `Ctrl+Shift+1..6`.
- Accessibility: chữ UI tối thiểu 18 px, tùy chọn cỡ 125%, giảm chuyển động,
  InputMap cho phép đổi phím và lưu, phát hiện trùng phím, khôi phục mặc định.
- Tín hiệu hình ảnh: cảnh báo shade gần, gió mạnh, 10 giây cuối, dầu thấp.

## Chưa đạt / giới hạn đã biết

- Benchmark trong repo là đo mô phỏng headless, không phải FPS 3D trên GPU thật.
  Trường `renderer` ghi `headless-simulation` để không gây hiểu nhầm. Muốn đo 3D phải
  chạy GUI Godot trên máy có GPU; số đo này không dùng để thay thế ngưỡng máy chấm.
- Chưa có bằng chứng chạy GUI trên macOS/Linux thật; WSL chỉ dùng để kiểm tra tệp.
- Video demo nằm ở `docs/demo/demo.mp4`; link ở đầu README.
