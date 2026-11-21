# Changelog

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
