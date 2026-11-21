# ADR Phase 3 — Đèn cạn dầu, luật bình minh và Contract v1.2

- **Trạng thái:** Chấp nhận (triển khai Phase 3)
- **Ngày:** 2026-11-21
- **Bối cảnh:** Ticket-03 thay đổi luật lõi của Phase 1–2. Bản Ticket-03 đầy đủ
  không nằm trong repo; nguồn yêu cầu dùng để triển khai là checklist Phase 3
  trong `OPENCODE-PHASE-2-4-CHECKLIST.md`. Các số liệu checklist không quy định
  được ghi thành giả định trong `phase-3-assumptions.md`.

## 1. Quyết định

### 1.1 Nhiên liệu và `ever_lit`

Mỗi Đèn Lồng Lớn có:

- `fuel` nguyên `0..100` (đơn vị dầu), `lit = fuel > 0`.
- `deposited` giữ làm bí danh tương thích của `fuel` (0..100). Khi đèn tắt vì
  hết dầu, `deposited = 0` theo đúng checklist.
- `ever_lit` bền trong đêm: đã từng sáng thì giữ `true` kể cả khi `fuel = 0`.
- `relit_count` đếm số lần thắp lại sau khi đã từng sáng.

Hao dầu:

- Đèn đang sáng tự hao `1/s`.
- Mỗi Bóng Mực trong bán kính `2 m` của đèn đang sáng hút thêm `5/s`.
- Hai nguồn **cộng dồn**; một Bóng Mực + đèn sáng = `6/s`.
- Dùng bộ tích lũy nguyên theo `1/60` giây (`drain_acc`) để giữ tất định, không
  dùng số thực tích lũy cho `fuel`.
- Khi `fuel` về `0` trong tick hiện tại: đặt `lit = false`, `deposited = 0`,
  `drain_acc = 0`, phát `lantern_out`, **giữ** `ever_lit`.

### 1.2 Nạp dầu, thắp mới, thắp lại

- Nạp dầu đèn đang sáng: `used = min(carried, ceil((100 - fuel) / 10))`.
  Mỗi đom đóm nạp thêm `10` dầu, kẹp `fuel` tại `100`. Không cộng điểm.
- Đèn đầy (`fuel = 100`) không phát event, không cộng điểm.
- Chỉ chọn **đèn nhận được gần nhất** trong `interact_radius`; hòa khoảng cách
  chọn `id` nhỏ hơn (so sánh chuỗi). Đèn đầy hoặc không đủ đom đóm không phải
  ứng viên.
- Thắp mới đèn chưa từng sáng: tốn `10` đom đóm.
- Thắp lại đèn `ever_lit = true` đang tắt: tốn `5` đom đóm.
- Cả hai đặt `fuel = 100`, `deposited = 100`, `lit = true`, `ever_lit = true`,
  tăng `successful_lights`; thắp lại tăng thêm `relit_count`.

### 1.3 Sức chứa

`capacity = min(20, 10 + 2 * successful_lights)`, reset `successful_lights = 0`
đầu mỗi đêm. `successful_lights` tăng cho cả thắp mới và thắp lại.

### 1.4 AI Bóng Mực

- Trạng thái: `stunned`, `chase`, `drain`, `wander`.
- `stunned`: đếm lùi, không di chuyển/hút; hết choáng → `wander`.
- Vùng an toàn: đèn sáng có `fuel >= 30` tạo bán kính an toàn `3 m`. Đúng `30`
  vẫn an toàn; `< 30` mất vùng an toàn.
- Vùng an toàn (đèn sáng `fuel >= 30`) luôn đẩy shade sang `wander`; nếu không trong vùng an
  toàn: người chơi trong `<= 6 m` → `chase`; nếu không, trong `<= 2 m` của
  đèn sáng → `drain`; nếu không → `wander`.
- `wander`: đi tới đèn sáng có `fuel` thấp nhất; hòa chọn đèn gần Bóng Mực hơn;
  hòa nữa chọn `id` nhỏ hơn. Không còn đèn sáng thì đứng yên.
- `drain`: hút đèn mục tiêu `5/s` (cộng với hao tự nhiên).
- Khi một đèn được châm lên `>= 30` từ mức `< 30`, đẩy mọi Bóng Mực trong `7 m`
  ra xa `2 m`, đặt về `wander`, phát `shade_pushed`.

### 1.5 Luật thắng/thua

- **Bỏ thắng sớm khi tất cả đèn sáng.** Không còn điều kiện tháp chuông trong
  luật thắng (tháp chuông vẫn là địa hình/trang trí).
- Chỉ xét kết quả khi `time_left_s <= 0` (bình minh):
  1. `flames == 0` → thua `no_flames` (ưu tiên trước bình minh).
  2. `lit_lanterns >= ceil(0.6 * lantern_count)` → thắng `dawn`.
  3. Ngược lại → thua `not_enough_lanterns`.
- Không còn thưởng theo thời gian còn lại.

### 1.6 Điểm

- `per_mote = 10`, `per_lantern = 100` (thắp mới), `per_relight = 50`,
  `per_stun = 25`.
- Khi thắng: cộng `dawn_bonus = 500` và `per_flame_left = 50` cho mỗi lửa còn
  lại. Khi thua: không cộng `dawn_bonus`/`per_flame_left`.
- Bỏ `per_second_left`.

### 1.7 Chế độ màu

- Thêm setting `color_mode` (`default` | `colorblind`), lưu bền trong
  `user://settings.cfg`.
- Đèn sáng/tắt được phân biệt bằng **chữ trạng thái** (`SÁNG`/`TẮT`) và độ
  sáng, không chỉ bằng màu. Cảnh báo HUD có biểu tượng `⚠`.
- `color_mode` là metadata UI, không ảnh hưởng mô phỏng. Headless nhận
  `color_mode` trong scenario và phản chiếu trong snapshot để kiểm thử tất
  định; không thêm hiệu ứng trang trí vào output.

### 1.8 Contract v1.2

- Giữ toàn bộ trường v1.1 còn hiệu lực; thêm `fuel`, `ever_lit`, `relit_count`,
  `capacity`, `successful_lights`, `drain`, `dawn_threshold`, `lit_lanterns`,
  `color_mode` và các event mới.
- `deposited` đổi ngữ nghĩa từ `0..5` (số đom đóm) sang `0..100` (dầu), là
  breaking change có chủ đích theo Ticket-03.

## 2. Hệ quả

- Test Phase 1/2 dựa trên `lantern_cost = 5`, thắng sớm `all_lit`, thua `dawn`
  và `deposited <= 5` phải sửa; lý do ghi trong
  `phase-3-test-changes.md`, không skip âm thầm.
- GUI 3D giữ nguyên; HUD thêm thanh dầu, sức chứa động, cảnh báo `< 30` nhấp
  nháy `1 Hz`, nhãn trạng thái đèn và setting bảng màu.
- Output headless vẫn tất định 60 Hz; không có yếu tố GUI nào thay đổi mô phỏng.

## 3. Phương án đã cân nhắc

- **Drain thay thế thay vì cộng dồn:** đơn giản hơn nhưng không đúng ý “tự hao
  1/s” và “Bóng Mực hút 5/s” là hai nguồn riêng. Chọn cộng dồn.
- **Giữ thắng sớm all-lit:** trái yêu cầu “sống tới bình minh”. Bỏ.
- **Giữ tháp chuông trong luật thắng:** Ticket-03 thay luật thắng; giữ lại sẽ
  mâu thuẫn. Bỏ khỏi điều kiện thắng, giữ địa hình.
- **Dùng số thực cho fuel:** dễ trôi giữa các lần chạy. Chọn tích lũy nguyên
  1/60.
