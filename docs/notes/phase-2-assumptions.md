# Phase 2 — giả định và điểm mơ hồ

Checklist Phase 2 không kèm bản Ticket-02 đầy đủ trong repo. Các mục dưới đây
là giả định triển khai, được ghi lại để chủ dự án duyệt/sửa. Không coi là số
liệu chính thức của khách hàng cho đến khi có xác nhận.

## 1. Contract và tick

- `contract_version` = `"1.1"`.
- `tick` là số vòng lặp đã chạy, tăng cả khi pause.
- `sim_tick` là số bước gameplay, chỉ tăng khi không pause.
- `time_left_s = duration_s - sim_tick/60`, kẹp tại 0.
- Event giữ trường `tick` như v1.0; snapshot thêm `sim_tick`, `paused`, `night`.
- Dòng `end` giữ `ticks` = `tick` và thêm `sim_ticks` = `sim_tick`.
- `pause` trong inputs là **trạng thái** boolean, không phải edge-trigger.
- `--ticks N` chạy N vòng lặp, trừ khi game kết thúc sớm.

## 2. Tuning v1.1

Giữ các giá trị Phase 1 trừ các mục dưới đây:

| Khóa | Giá trị | Ghi chú |
|---|---:|---|
| `carry_capacity` | 10 | HUD 10 ô đom đóm theo checklist Phase 2 |
| `lantern_cost` | 5 | Giữ Phase 1 để regression nhặt/nạp vẫn hợp lệ |
| `island_radius_m` | 40.0 | Night 1 theo checklist Phase 2 |
| `lantern_ring_radius_m` | 25.0 | Vành đèn Night 1 |
| `initial_mote_count` | 40 | Night 1 |
| `initial_mote_spawn_radius_m` | 36.0 | Night 1 |
| `initial_shade_count` | 3 | Night 1 |
| `initial_shade_spawn_radius_m` | 32.0 | Night 1 |
| `dash_speed_m_s` | 12.0 | Dash |
| `dash_duration_s` | 0.2 | Dash |
| `dash_cooldown_s` | 1.5 | Dash |
| `glide_fall_speed_m_s` | 2.0 | Glide |
| `lost_wisp_speed_m_s` | 2.0 | Gió Lạc |
| `lost_wisp_radius_m` | 2.0 | Gió Lạc đẩy |
| `lost_wisp_push_m_s` | 3.0 | Gió Lạc đẩy |
| `wind_charm_radius_m` | 1.2 | Bán kính nhặt bùa |
| `wind_charm_duration_s` | 8.0 | Thời gian miễn gió |
| `strong_wind_speed_m_s` | 2.5 | Gió mạnh Night 3 |
| `bell_tower_radius_m` | 3.0 | Điều kiện thắng Night 3 |
| `step_height_m` | 0.8 | Bước lên bề mặt |
| `fall_y_m` | -8.0 | Ngưỡng rơi |
| `night2_duration_s` | 360 | Night 2 |
| `night3_duration_s` | 420 | Night 3 |
| `night2_shade_speed` | 2.8 | Override Night 2 |
| `night3_shade_speed` | 3.1 | Override Night 3 |
| `night2_lost_wisp_speed_m_s` | 2.0 | Override Night 2 |
| `night3_lost_wisp_speed_m_s` | 2.6 | Override Night 3 |

Các giá trị còn lại giữ nguyên Phase 1. Score giữ nguyên 5 khóa v1.0; Phase 2
không thêm điểm cho charm/wisp.

## 3. Ba bản đồ

### Night 1 — Đảo Bến

- Một đảo tròn tâm `(0,0)`, bán kính 40 m, cao 0.
- 5 đèn vành bán kính 25 m: `L1..L5`.
- Player spawn `(0,0,0)`.
- 40 đom đóm ngẫu nhiên trong bán kính 36 m, chỉ trên bề mặt.
- 3 Bóng Mực vành bán kính 32 m, tốc độ 2,5 m/s.
- Mang tối đa 10 đom đóm.
- Không Gió Lạc, không bùa, không gió mạnh, không tháp chuông.

### Night 2 — Hai đảo và cầu

- Đảo A: tâm `(-20,0)`, bán kính 18 m, cao 0.
- Đảo B: tâm `(20,0)`, bán kính 16 m, cao 0.
- Cầu: hình chữ nhật `x ∈ [-2,4]`, `z ∈ [-3,3]`, cao 0.
- 6 đèn: 3 trên A, 3 trên B.
- Player spawn `(0,0,0)` trên cầu.
- 45 đom đóm ngẫu nhiên trên bề mặt; 4 Bóng Mực; 2 Gió Lạc; 2 bùa gió.
- Mang tối đa 10; Bóng Mực tốc độ 2,8 m/s; Gió Lạc tốc độ 2,0 m/s.
- Không gió mạnh, không tháp chuông.

### Night 3 — Ba tầng, dốc, bục nhảy, tháp chuông

- Tầng 0: tròn tâm `(0,0)`, bán kính 30 m, cao 0.
- Tầng 1: tròn tâm `(0,0)`, bán kính 20 m, cao 4 m.
- Tầng 2: tròn tâm `(0,0)`, bán kính 10 m, cao 8 m.
- Dốc 1: `x ∈ [-3,3]`, `z ∈ [20,26]`, cao 4 tại `z=20`, cao 0 tại `z=26`.
- Dốc 2: `x ∈ [-3,3]`, `z ∈ [10,14]`, cao 8 tại `z=10`, cao 4 tại `z=14`.
- Bục nhảy: `(15,0)` và `(-15,0)`, bán kính 2 m, lực phóng 14 m/s.
- Tháp chuông: tâm `(0,0)`, chân ở cao 8 m, bán kính điều kiện 3 m.
- 7 đèn: 4 ở vành tầng 0 bán kính 28 m, 2 ở vành tầng 1 bán kính 16 m,
  1 trên tầng 2.
- Player spawn `(0,0,28)` trên tầng 0.
- 60 đom đóm ngẫu nhiên trên bề mặt; 5 Bóng Mực; 3 Gió Lạc; 3 bùa gió.
- Mang tối đa 10; Bóng Mực tốc độ 3,1 m/s; Gió Lạc tốc độ 2,6 m/s.
- 2 vùng gió mạnh dọc hai dốc, đẩy theo `+Z` (xuống dốc).

## 4. Luật gameplay mới

- **Dash:** edge-trigger, chỉ khi đang đứng trên bề mặt; hướng theo move hiện
  tại, nếu move bằng 0 thì theo hướng camera (+Z đã xoay yaw); tốc độ 12 m/s
  trong 0,2 s; hồi 1,5 s. Không tốn đom đóm.
- **Glide:** khi đang bay và giữ `glide`, tốc độ rơi bị kẹp ở 2 m/s; không tốn
  tài nguyên.
- **Gió Lạc:** lang thang về phía đèn chưa sáng gần nhất; nếu cách player
  ≤2 m thì đẩy player ra xa 3 m/s. Không gây mất lửa.
- **Bùa gió:** tự nhặt khi cách ≤1,2 m; đặt `wind_shield_s = 8`; miễn đẩy từ
  Gió Lạc và gió mạnh; phát event `charm_picked`.
- **Gió mạnh:** trong vùng gió, đẩy player 2,5 m/s theo vector của vùng; bùa
  gió chặn hoàn toàn.
- **Rơi:** khi `y < -8` hoặc không còn bề mặt và rơi quá ngưỡng, mất 1 lửa,
  rơi đom đóm theo `hit_drop_ratio`, hồi sinh tại vị trí an toàn gần nhất,
  bất tử 2 s; event `player_hit` với `by: "fall"`.
- **Vị trí an toàn:** cập nhật mỗi khi đứng trên bề mặt và không trong vùng
  gió mạnh; mặc định là `player_spawn`.
- **Thắng Night 1/2:** tất cả đèn sáng.
- **Thắng Night 3:** tất cả đèn sáng **và** player trong bán kính 3 m của
  tháp chuông (khoảng cách XZ).
- **Thua:** hết lửa (`no_flames`) hoặc hết giờ (`dawn`).
- **Ưu tiên cùng tick:** `no_flames` → thắng → `dawn`.
- **An toàn quanh đèn:** giữ bán kính 3 m; Bóng Mực không vào.
- **Pulse:** giữ nguyên Phase 1; chỉ ảnh hưởng Bóng Mực.
- **Score:** giữ nguyên Phase 1; chỉ cộng thưởng thời gian/lửa khi thắng.

## 5. Scenario/inputs mở rộng

- Scenario thêm: `paused` (bool), `wisps` (mảng pos/id), `charms` (mảng pos/id),
  `random_wisps` (bool), `random_charms` (bool).
- Inputs thêm: `dash`, `glide`, `pause` (bool). `dash` edge-trigger; `glide` và
  `pause` là trạng thái.
- Giữ nguyên các quy tắc validate của v1.0.

## 6. GUI và web

- Godot 4.7.2, renderer `gl_compatibility`, 1280×720.
- Bản web local trước; export template web cần cài từ Godot.
- Server local set COOP/COEP và MIME cho `.wasm`/`.pck`.
- Bản web mặc định **không bật thread** để đơn giản host; nếu FPS thấp sẽ thử
  bản có thread và server COOP/COEP.
- Âm thanh tự sinh bằng Python (sine/noise) để tránh asset ngoài; ghi vào
  `CREDITS.md` ở Phase 4.
- Lưu settings bằng `ConfigFile` tại `user://settings.cfg` (web: IndexedDB).

## 7. Điểm cần chủ dự án xác nhận

- Night 1 theo checklist Phase 2: đảo R=40, vành đèn 25, 40 đom đóm,
  Bóng Mực vành 32, mang tối đa 10; regression fall Phase 1 sẽ được cập nhật
  biên bản theo bán kính mới.
- Các số tuning mới (dash/glide/wisp/charm/wind/thời lượng Night 2/3).
- Số đèn Night 2 (6) và Night 3 (7).
- Điều kiện thắng Night 3 cần tháp chuông.
- `pause` là trạng thái, không phải edge-trigger.
- Bùa gió tự nhặt, không cần phím tương tác.
- Bản web không thread mặc định.
