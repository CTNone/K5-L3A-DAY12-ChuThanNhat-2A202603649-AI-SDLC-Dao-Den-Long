# Retro — Phase 4 / v1.0.0

## Kết quả

- Giữ được toàn bộ kiểm chứng Phase 1–3 sau khi nâng contract lên v1.3.
- Thêm CLI soak/bench/export leaderboard, leaderboard GUI, admin cheat, audio unlock,
  hướng nhân vật theo camera, InputMap và các tùy chọn accessibility.
- Đóng gói web zip và Dockerfile; video demo đặt trong `docs/demo/demo.mp4`.

## Bài học

- Thời gian cuối kỳ rất hẹp: ưu tiên tag/Release và bằng chứng thật trước, không chạy
  theo tính năng đẹp.
- Không nên để benchmark giả lập mang nhãn FPS 3D. Ghi rõ `headless-simulation` để
  người chấm biết giới hạn.
- Test cũ kiểm tra cứng contract v1.2; khi nâng v1.3 phải sửa test có lý do thay vì
  bỏ qua. Đã ghi thay đổi trong `docs/notes/phase-3-test-changes.md` và spec này.
- GUI web cần `audio.unlock()` từ thao tác người dùng; autoplay trong `_ready` bị chặn.

## Nếu làm lại

- Dành 15 phút đầu Phase 4 để chốt release artifact và video trước khi thêm tính năng.
- Đo FPS 3D bằng một cảnh Godot riêng, chạy trên máy có GPU, và lưu log thô.
- Viết test Phase 4 trước khi sửa GUI để tránh hồi quy.
