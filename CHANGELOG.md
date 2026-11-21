# Changelog

## Bản vá — v1.0.1

### Fixed

- Web zip tự chạy: kèm `serve_web.py` và `RUN.md`; giải nén là chạy được, không cần clone repo.
- `Dockerfile` dùng zip trong `dist/` thay vì `build/web` bị ignore, nên `docker build` chạy từ clone sạch.
- `tools/serve_web.py` tự chọn thư mục chứa nó khi không có `build/web`.
- `bench.json` ghi thêm `cpu`, `gpu`, `ram_mb`, `resolution`, `python`; thêm `machine.txt`.
- Harness `.agents/skills` được đưa vào repo và lịch sử git.
- Thêm `clean-clone.log`; đồng bộ lại `CHECKPOINTS.md` và các tài liệu Phase 1 lịch sử.

## Phase 4 — v1.0.0

### Added

- Contract `1.3` với `bench_cmd`, `soak_cmd`, `leaderboard_cmd`, `leaderboard`,
  `accessibility`, `input`; giữ nguyên contract gameplay.
- CLI `--bench`, `--soak`, `--export-leaderboard`, `--leaderboard-file`.
- `leaderboard.py` và bảng điểm GUI top 10, lưu `user://leaderboard.json`.
- Audio unlock sau thao tác người dùng; bỏ autoplay khi mở game.
- Admin cheat có checkbox và hotkey; admin không ghi bảng điểm.
- InputMap đổi phím, phát hiện trùng phím, khôi phục mặc định.
- Accessibility: chữ tối thiểu 18 px, cỡ 125%, giảm chuyển động, hướng nhân vật.
- Cảnh báo 10 giây cuối, shade gần, gió mạnh và dầu thấp.
- `LICENSE` MIT, `CREDITS.md`, `Dockerfile`, ghi chú Phase 4 và video demo.

### Fixed

- `_build_leaderboard` không còn dùng `String.strip()` (Godot 4 dùng `strip_edges()`).
- Soak đọc RSS đúng trên Windows bằng `GetProcessMemoryInfo`.

### Known limitations

- Benchmark là mô phỏng headless, không phải FPS 3D trên GPU.
- Chưa có bằng chứng chạy GUI thật trên macOS/Linux.

## Phase 3 — v1.2

### Breaking changes

- `lantern_cost` bị thay bằng `new_light_cost=10` và `relight_cost=5`.
- `deposited` trở thành alias của `fuel`; fuel là nguồn sự thật duy nhất.
- `lit` là dẫn xuất `fuel > 0`; đèn có thể tắt khi hết dầu.
- Thắng không còn xảy ra khi thắp hết đèn; chỉ xét tại bình minh với ngưỡng 60% số đèn.
- Bỏ điều kiện thắng bằng tháp chuông.
- Bỏ `score.per_second_left`; thêm `per_relight`, `per_flame_left`, `dawn_bonus`.
- Event `deposit` giờ là nạp dầu; `lantern_lit` có `mode: new|relight`.
- Snapshot thêm `color_mode`, `dawn_threshold`, `lit_lanterns`, `player.capacity`,
  `player.successful_lights`, lantern `fuel/deposited/ever_lit/relit_count`, shade
  `state/drain`.

### Added

- Fuel 0..100 với ambient drain 1/s và shade drain 5/s.
- Nạp dầu theo đóm, chọn đèn gần nhất, hòa chọn `id` nhỏ hơn.
- Thắp mới/thắp lại, `successful_lights`, `relit_count`, capacity tối đa 20.
- AI shade với state `stunned/chase/drain/wander` và pushback khi nạp vượt 30.
- Luật thắng bình minh, thua `not_enough_lanterns`, ưu tiên `no_flames`.
- Setting `color_mode` (`default|colorblind`) và HUD thanh dầu/capacity/cảnh báo.
- Test Phase 3 và bằng chứng `docs/proof/phase-3/`.

### Balance sau playtest

- `player_speed` tăng `5.0` → `6.5` m/s.
- `shade_chase_radius_m` tăng `6.0` → `10.0` m.
