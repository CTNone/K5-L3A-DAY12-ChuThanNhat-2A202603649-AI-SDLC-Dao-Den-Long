# Phase 3 — thay đổi test

Các test Phase 1/2 bị sửa vì hành vi v1.2 thay đổi có chủ đích. Không test nào bị skip.

## Phase 1 (`tools/verify_phase1.py`)

- Cập nhật contract kỳ vọng từ v1.0 lên v1.2.
- Thay kiểm tra `lantern_cost=5` bằng `new_light_cost=10`; thêm `relight_cost=5`.
- `deposited` được kiểm tra như alias của `fuel`, không còn là bộ đếm riêng.
- Kịch bản “thắp đủ đèn để thắng” được thay bằng kiểm tra đèn sáng nhưng chưa thắng trước
  bình minh; thắng chỉ xét tại `time_left <= 0`.
- Bỏ kỳ vọng thưởng thời gian còn lại; thêm `per_relight`, `per_flame_left`, `dawn_bonus`.
- Snapshot kỳ vọng thêm `color_mode`, `dawn_threshold`, `lit_lanterns`, `capacity`,
  `successful_lights`, lantern `fuel/ever_lit/relit_count`, shade `state/drain`.

## Phase 2 (`tools/verify_phase2.py`)

- Cập nhật contract kỳ vọng lên v1.2.
- Bỏ test thắng sớm khi thắp hết đèn và bỏ điều kiện tháp chuông.
- Thêm test “tất cả đèn sáng vẫn không thắng trước dawn”.
- Thêm test ngưỡng bình minh Night 3: cần 5/7 đèn sáng mới thắng.
- Giữ nguyên các test địa hình, dash, glide, gió, charm, pause và determinism.

## Phase 3 (`tools/verify_phase3.py`)

22 kiểm tra mới:

1. Contract v1.2 và `ui` đồng bộ với `godot/shared/`.
2. Snapshot có đầy đủ trường fuel/capacity/dawn/color mode.
3. Refuel chọn đèn gần nhất và hòa chọn `id` nhỏ hơn.
4. Refuel dùng `min(carried, ceil((100-fuel)/10))`.
5. Refuel đèn đầy không phát event/điểm.
6. Ambient depletion đúng 60 tick cho 1 fuel.
7. Shade drain 5 fuel/s trong bán kính 2 m.
8. Drain vẫn hoạt động khi fuel dưới 30.
9. Relight tốn 5 đóm, tăng `relit_count`, tăng capacity.
10. Thắp mới tốn 10 đóm, đặt fuel 100, tăng `successful_lights`.
11. Capacity đạt trần 20.
12. Capacity reset mỗi đêm.
13. Pushback khi nạp vượt 30.
14. Không pushback khi vẫn dưới 30.
15. Thắng dawn khi đủ ngưỡng.
16. Thua `not_enough_lanterns` khi thiếu đèn.
17. `no_flames` ưu tiên trước kết quả dawn.
18. Scoring không còn thưởng thời gian; có dawn bonus và flame bonus khi thắng.
19. `color_mode=colorblind` được phản chiếu trong snapshot.
20. Determinism với cùng seed/scenario.
21. Hiệu năng 21.600 tick trong ngân sách thời gian.
22. `godot/shared` đồng bộ với contract và map.

## Ghi chú

- Các kịch bản dùng `--scenario` và `--inputs` thật, không chỉnh output đã lưu.
- Bằng chứng được sinh lại bằng `python tools/capture_phase3_evidence.py`.
