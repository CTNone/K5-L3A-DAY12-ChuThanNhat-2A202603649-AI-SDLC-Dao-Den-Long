# Phase 3 — Ticket-03 spec v1.2 acceptance criteria

**Nguồn yêu cầu:** checklist Phase 3 do chủ dự án cung cấp trong
`OPENCODE-PHASE-2-4-CHECKLIST.md`. Bản Ticket-03 đầy đủ (nếu có) chưa nằm trong repo; các
giá trị không được checklist quy định được ghi thành giả định trong
`docs/notes/phase-3-assumptions.md` và cần chủ dự án xác nhận trước khi coi là số liệu cuối.

## 1. Phạm vi

- Giữ Test Contract v1.0 làm nền; nâng lên v1.2 với fuel, ever_lit, relit_count, capacity,
  drain, luật thắng bình minh, scoring mới và `color_mode`.
- Headless vẫn là Python zero-dependency, 60 Hz cố định, JSONL tất định.
- GUI vẫn là Godot 4.7 3D thật; thêm thanh dầu, capacity, cảnh báo dầu thấp và bảng màu
  dễ phân biệt.
- Không làm Phase 4; không tạo tag `phase-3` trước khi chủ dự án xác nhận.

## 2. Acceptance criteria

### AC-3.1 Contract v1.2

- `game.contract.json` có `contract_version: "1.2"`.
- Giữ toàn bộ phần v1.1 không bị ticket thay thế: `--night 1|2|3`, pause, `tick`/`sim_tick`,
  JSONL, tuning Phase 1/2, map Night 1–3.
- Tuning mới: `capacity_per_light`, `capacity_max`, `new_light_cost`, `relight_cost`,
  `lantern_fuel_max`, `refuel_fuel_per_mote`, `ambient_drain_per_s`, `shade_drain_per_s`,
  `shade_drain_radius_m`, `shade_chase_radius_m`, `safe_fuel_threshold`, `dawn_lantern_ratio`,
  `fuel_push_radius_m`, `fuel_push_m`.
- Bỏ `lantern_cost` và `score.per_second_left`; thêm `score.per_relight`, `score.per_flame_left`,
  `score.dawn_bonus`.
- `ui` có `color_modes`, `default_color_mode`, `fuel_warning_blink_hz`.

### AC-3.2 Fuel và drain

- Mỗi đèn có `fuel` 0..100; `lit = fuel > 0`; `deposited` là alias legacy của `fuel`.
- Drain cộng dồn theo tick 1/60: mỗi đèn sáng mất `ambient_drain_per_s`; mỗi shade trong
  `shade_drain_radius_m` của đèn sáng cộng thêm `shade_drain_per_s`.
- Khi fuel về 0 đúng tại tick: `lit=false`, `deposited=0`, `drain_acc=0`, phát `lantern_out`,
  giữ `ever_lit`.
- `drain_acc` là phần dầu lẻ còn lại theo đơn vị 1/60 để tránh sai số tích lũy.

### AC-3.3 Nạp dầu, thắp mới, thắp lại

- Nạp dầu: `used = min(carried, ceil((100 - fuel) / 10))`; mỗi đóm nạp 10 fuel.
- Chỉ chọn đèn nhận được gần nhất; hòa khoảng cách chọn `id` nhỏ hơn; đèn đầy không phát
  event/điểm.
- Thắp mới tốn 10 đóm; thắp lại tốn 5; đặt `fuel=deposited=100`.
- `successful_lights` tăng mỗi lần thắp mới hoặc thắp lại thành công; `relit_count` chỉ tăng
  khi thắp lại.
- `capacity = min(20, 10 + 2 * successful_lights)`, reset mỗi đêm.
- Đèn chưa từng sáng: thắp mới; đèn đã từng sáng và đang tắt: thắp lại.

### AC-3.4 AI shade và vùng an toàn

- Shade có state `stunned`, `chase`, `drain`, `wander`.
- Ưu tiên chase khi người chơi trong `shade_chase_radius_m` (10 m); nếu không, drain khi
  trong `shade_drain_radius_m` (2 m) của đèn sáng; nếu không, wander tới đèn sáng yếu nhất
  theo quy tắc gần nhất.
- Vùng an toàn quanh đèn chỉ tồn tại khi `fuel >= safe_fuel_threshold` (30). Đúng 30 vẫn
  an toàn; dưới 30 shade có thể drain đèn.
- Khi đèn được nạp vượt ngưỡng 30, shade trong `fuel_push_radius_m` (7 m) bị đẩy ra xa
  thêm `fuel_push_m` (2 m) theo hướng từ đèn, phát `shade_pushed`.

### AC-3.5 Luật thắng bình minh

- Không thắng sớm khi tắt cả đèn sáng; chỉ xét tại `time_left <= 0`.
- Thứ tự: `no_flames` trước; sau đó nếu `lit_count >= ceil(0.6 * N)` thì thắng `dawn`;
  ngược lại thua `not_enough_lanterns`.
- Bỏ điều kiện thắng bằng tháp chuông; giữ địa hình tháp chuông làm trang trí.

### AC-3.6 Scoring

- `per_mote=10`, `per_lantern=100`, `per_relight=50`, `per_stun=25`.
- Chỉ khi thắng: cộng `per_flame_left=50` cho mỗi lửa còn lại và `dawn_bonus=500`.
- Bỏ thưởng thời gian (`per_second_left`).

### AC-3.7 Snapshot, scenario, event

- Snapshot thêm `color_mode`, `dawn_threshold`, `lit_lanterns`, `player.capacity`,
  `player.successful_lights`, lantern `fuel/deposited/ever_lit/relit_count`, shade
  `state/drain`.
- Scenario nhận `successful_lights`, `color_mode`; lantern nhận `fuel/ever_lit/relit_count`.
- Event mới: `lantern_out`, `deposit` (nạp dầu), `lantern_lit` với `mode: new|relight`,
  `shade_pushed`.
- `game_over` thêm `lit_lanterns`, `dawn_threshold`, `score`.

### AC-3.8 GUI và accessibility

- HUD có thanh dầu, capacity, số đèn sáng/ngưỡng bình minh; thanh dầu nhấp nháy 1 Hz khi
  dưới ngưỡng an toàn.
- Cảnh báo dầu thấp có biểu tượng, không phụ thuộc màu.
- Setting `color_mode` gồm `default` và `colorblind`, lưu trong `user://settings.cfg`.
- Trạng thái đèn sáng/tắt có nhãn chữ, không chỉ dựa vào màu.

### AC-3.9 Test và bằng chứng

- Sửa test Phase 1/2 bị thay đổi hành vi; ghi rõ lý do, không skip.
- Thêm scenario refuel, depletion, relight, drain, pushback, ngưỡng dawn, scoring và
  color mode.
- Chạy lại toàn bộ test Phase 1–3, lưu bằng chứng trong `docs/proof/phase-3/`.
- Cập nhật README, spec, assumptions, changelog.
