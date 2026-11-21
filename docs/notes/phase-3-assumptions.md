# Phase 3 — giả định và điểm mở

Checklist Phase 3 không kèm bản Ticket-03 đầy đủ trong repo. Các mục dưới đây là giả định
triển khai, được ghi lại để chủ dự án duyệt/sửa. Không coi là số liệu chính thức của khách
hàng cho đến khi có xác nhận.

> **Đã xác nhận trong phiên 2026-11-21:** giữ scoring hiện tại, safe zone ưu tiên hơn
> chase, pushback đẩy thêm 2 m và không stun, capacity tăng cho cả thắp lại, `deposited`
> tiếp tục là alias của `fuel`.

## 1. Contract và tick

- `contract_version` = `"1.2"`.
- Giữ nguyên `tick`/`sim_tick`, pause, JSONL và các quy tắc tick của v1.1.
- Fuel là số thực 0..100; `deposited` được giữ như alias của `fuel` để tương thích test cũ.
- `lit` là dẫn xuất `fuel > 0`; không lưu cờ `lit` độc lập trong mô phỏng.
- `ever_lit` bền qua các lần tắt/thắp lại; `relit_count` đếm số lần thắp lại thành công.

## 2. Tuning v1.2

Giữ các giá trị Phase 1/2 trừ các mục dưới đây:

| Khóa | Giá trị | Ghi chú |
|---|---:|---|
| `capacity_per_light` | 2 | Mỗi lần thắp mới/thắp lại tăng capacity |
| `capacity_max` | 20 | Trần capacity |
| `new_light_cost` | 10 | Đóm để thắp đèn mới |
| `relight_cost` | 5 | Đóm để thắp lại đèn đã từng sáng |
| `lantern_fuel_max` | 100 | Dầu tối đa mỗi đèn |
| `refuel_fuel_per_mote` | 10 | Dầu mỗi đóm khi nạp |
| `ambient_drain_per_s` | 1 | Hao dầu nền mỗi giây |
| `shade_drain_per_s` | 5 | Hao thêm mỗi shade trong bán kính |
| `shade_drain_radius_m` | 2.0 | Bán kính shade drain |
| `shade_chase_radius_m` | 6.0 | Bán kính chase |
| `safe_fuel_threshold` | 30 | Dưới ngưỡng này mất vùng an toàn |
| `dawn_lantern_ratio` | 0.6 | Tỷ lệ đèn sáng cần để thắng |
| `fuel_push_radius_m` | 7.0 | Bán kính đẩy shade khi nạp vượt ngưỡng |
| `fuel_push_m` | 2.0 | Khoảng cách đẩy shade ra |

Scoring v1.2:

| Khóa | Giá trị |
|---|---:|
| `per_mote` | 10 |
| `per_lantern` | 100 |
| `per_relight` | 50 |
| `per_stun` | 25 |
| `per_flame_left` | 50 (chỉ khi thắng) |
| `dawn_bonus` | 500 (chỉ khi thắng) |

Các giá trị `per_relight`, `per_flame_left`, `dawn_bonus`, `fuel_push_radius_m` và
`fuel_push_m` là giả định; cần xác nhận nếu Ticket-03 có bảng điểm/knockback chính thức.

## 3. Drain và làm tròn

- Drain được cộng dồn vào `drain_acc` theo đơn vị 1/60 mỗi tick.
- `drain_acc` đủ 1.0 thì trừ 1 fuel và giữ phần lẻ; tránh sai số float giữa các nền tảng.
- Khi fuel về 0 đúng tick, phát `lantern_out` một lần và reset `drain_acc`.
- Ambient drain chỉ áp dụng cho đèn đang sáng; shade drain chỉ áp dụng khi shade ở state
  `drain` và có `drain_target` hợp lệ.

## 4. Nạp dầu và chọn đèn

- `used = min(carried, ceil((100 - fuel) / 10))`; `carried` và `fuel` là số thực nhưng
  lượng đóm dùng là số nguyên.
- Đèn nhận được là đèn trong bán kính tương tác và `fuel < 100`.
- Chọn đèn gần nhất; hòa khoảng cách chọn `id` nhỏ hơn.
- Nếu không có đèn nhận được, không phát event, không trừ đóm.
- `deposit` event chứa `used`, `fuel` sau nạp và `carried` còn lại.

## 5. Thắp đèn

- Đèn chưa `ever_lit`: thắp mới, tốn `new_light_cost`.
- Đèn đã `ever_lit` và đang tắt: thắp lại, tốn `relight_cost`.
- Thắp thành công đặt `fuel=deposited=100`, `lit=true`, `drain_acc=0`, phát `lantern_lit`
  với `mode`.
- `successful_lights` tăng cho cả hai trường hợp; `relit_count` chỉ tăng khi thắp lại.
- Capacity tăng ngay sau khi thắp thành công và không giảm khi đèn tắt.
- Capacity reset về 10 khi bắt đầu đêm mới.

## 6. AI shade

- Thứ tự ưu tiên mỗi tick: `stunned` > vùng an toàn (`wander`) > `chase` > `drain` > `wander`.
- Chase khi khoảng cách người chơi `<= shade_chase_radius_m`.
- Drain khi không chase và có đèn sáng trong `shade_drain_radius_m`.
- Wander tới đèn sáng yếu nhất; nếu nhiều đèn cùng fuel thấp, chọn gần nhất, hòa chọn `id`
  nhỏ hơn.
- Shade bị đẩy khi đèn được nạp từ dưới 30 lên `>= 30`; shade trong `fuel_push_radius_m`
  bị đẩy ra xa thêm `fuel_push_m` theo hướng từ đèn tới shade, phát `shade_pushed`.
- Đẩy shade không gây stun và không cộng điểm.

## 7. Vùng an toàn và thắng/thua

- Vùng an toàn chỉ tồn tại khi đèn sáng và `fuel >= 30`; đúng 30 vẫn an toàn.
- Không thắng sớm khi tất cả đèn sáng.
- Tại `time_left <= 0`: nếu `flames == 0` → thua `no_flames`; nếu không, nếu
  `lit_count >= ceil(0.6 * N)` → thắng `dawn`; ngược lại thua `not_enough_lanterns`.
- `dawn_threshold = ceil(0.6 * N)`; Night 1/2/3 lần lượt là 3/4/5 với 5/6/7 đèn.
- Bỏ tháp chuông khỏi điều kiện thắng; giữ mô hình tháp chuông trong GUI.

## 8. Scoring

- Điểm đom, đèn, thắp lại, stun cộng ngay khi xảy ra.
- Khi thắng: cộng `per_flame_left * flames` và `dawn_bonus`.
- Khi thua: không cộng thưởng lửa còn lại và dawn bonus.
- Bỏ hoàn toàn thưởng thời gian còn lại.

## 9. Color mode

- `color_mode` chỉ là metadata UI, không ảnh hưởng mô phỏng.
- Giá trị hợp lệ: `default`, `colorblind`; giá trị khác bị từ chối khi nạp scenario.
- `colorblind` dùng palette xanh/cyan cho đèn sáng và cam cho đèn tắt; nhãn `SÁNG/TẮT`
  luôn hiện để không phụ thuộc màu.
- Cảnh báo dầu thấp có biểu tượng `⚠` và nhấp nháy 1 Hz.

## 10. Điểm đã chốt

- Giữ bảng điểm hiện tại: `per_relight=50`, `per_flame_left=50`, `dawn_bonus=500`.
- Pushback dùng `fuel_push_radius_m=7`, `fuel_push_m=2`, đẩy shade ra xa thêm 2 m và không
  gây stun.
- Capacity tăng cho cả thắp mới và thắp lại.
- `deposited` tiếp tục là alias của `fuel`.
