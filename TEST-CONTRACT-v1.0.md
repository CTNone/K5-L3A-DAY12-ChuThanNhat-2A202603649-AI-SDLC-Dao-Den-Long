# Test Contract v1.0 — Đảo Đèn Lồng

Contract này bắt buộc cho Phase 1. File máy đọc được `game.contract.json` phải nằm ở gốc repo. Các giá trị tuning trong đó phải khớp với hành vi game.

## A. `game.contract.json`

Tệp gốc repo phải có cấu trúc tương đương sau; điền lệnh và thông số thật của game:

```json
{
  "contract_version": "1.0",
  "team": "mssv-ho-ten",
  "build_cmd": "lệnh cài đặt/biên dịch",
  "run_cmd": "lệnh mở game có giao diện",
  "headless_cmd": "lệnh chạy headless",
  "tuning": {
    "player_speed": 0,
    "carry_capacity": 0,
    "lantern_cost": 0,
    "lantern_count_night1": 5,
    "pickup_radius": 0,
    "interact_radius": 0,
    "pulse_cost": 0,
    "pulse_radius": 0,
    "night1_duration_s": 0,
    "flames": 0,
    "invuln_s": 0,
    "hit_drop_ratio": 0,
    "pulse_stun_s": 0,
    "pulse_push_m": 0,
    "pulse_cooldown_s": 0,
    "safe_radius": 0,
    "shade_speed": 0,
    "shade_hit_radius": 0,
    "fall_enabled": false,
    "score": {
      "per_mote": 0,
      "per_lantern": 0,
      "per_stun": 0,
      "per_second_left": 0,
      "per_flame_left": 0
    }
  }
}
```

Điền đúng các giá trị game sử dụng. Nếu game không có khái niệm tương ứng, điền `null` (hoặc `false`) và giải thích trong README. Test Phase 1 sinh tình huống từ các giá trị này; khai sai có thể làm trượt test.

Ý nghĩa đặc biệt:

- `hit_drop_ratio`: tỷ lệ đom đóm rơi khi bị chạm; `0` nếu không rơi.
- `safe_radius`: bán kính quanh đèn mà Bóng Mực không thể vào.
- `fall_enabled`: có áp dụng hình phạt khi rơi khỏi đảo không.
- `score.*`: số điểm cho sự kiện tương ứng.

Các lệnh phải chạy được trên macOS/Linux sau `build_cmd`. Docker được phép.

## B. Chạy headless và mô hình tick

Giao diện lệnh:

```text
<headless_cmd> --seed <int> --night 1 [--scenario <file.json>] [--inputs <file.json>] \\
  --ticks <int> --out <file.jsonl> [--snapshot-every <int>]
```

`--snapshot-every` mặc định là `10`. Logic chạy cố định ở 60 tick/giây (1 tick = 1/60 giây), không cần cửa sổ hay GPU và chạy nhanh nhất có thể.

- Dừng sau `--ticks` bước hoặc khi game kết thúc (thắng/thua).
- Thành công thoát mã `0`.
- Lỗi thoát mã khác `0` và ghi thông báo ra stderr.
- File inputs/scenario sai định dạng thoát mã `2`.
- Đơn vị độ dài là mét; trục Y hướng lên; mặt đất đảo ở `Y = 0`; người chơi xuất phát `(0, 0, 0)`.
- Snapshot tick 0 là trạng thái sau khi dựng scenario, trước khi áp dụng input.
- Bước `k` (từ `0` đến `N−1`) đọc input của tick `k` và tạo trạng thái `k+1`. Event của bước đó ghi `tick = k+1`.
- `--ticks N` thực hiện đúng N bước, trừ khi game kết thúc sớm.
- `time_left_s = thời lượng Đêm − số bước đã chạy / 60`.

Quy ước vị trí và khoảng cách:

- `player.pos`: chân nhân vật.
- `shade.pos`: tâm Bóng Mực.
- `lantern.pos`: chân cột đèn.
- Vị trí đom đóm: điểm trên mặt đất; độ cao lơ lửng chỉ dùng hiển thị.
- Mọi khoảng cách tuning đo trên mặt phẳng ngang XZ giữa các điểm trên, không cộng kích thước nhân vật.
- “Trong bán kính `r`” nghĩa là khoảng cách `≤ r`.

## C. File inputs

Ví dụ:

```json
{
  "frames": [
    { "tick": 0, "move": [0, 1], "cam_yaw_deg": 0 },
    { "tick": 120, "move": [0, 0], "interact": true },
    { "tick": 121, "interact": false },
    { "tick": 200, "pulse": true },
    { "tick": 201, "pulse": false }
  ]
}
```

- Trước frame đầu tiên: `move = [0,0]`, `cam_yaw_deg = 0`, mọi nút false.
- Mỗi frame chỉ đổi trường được nêu; trường vắng mặt giữ giá trị trước.
- Tick các frame phải tăng nghiêm ngặt, không trùng và không giảm.
- `move = [x,z]`, mỗi thành phần thuộc `[-1,1]`.
- Với `θ = cam_yaw_deg` đổi sang radian: `x' = x·cosθ + z·sinθ`, `z' = −x·sinθ + z·cosθ`. Khi `θ = 0`, x là `+X`, z là `+Z`.
- Vector move có độ dài lớn hơn 1 phải được chuẩn hóa về độ dài 1.
- `jump`, `interact`, `pulse` (và `dash` nếu có) là boolean; hành động kích hoạt khi giá trị chuyển false → true.
- Không có file inputs nghĩa là người chơi đứng yên.

## D. File scenario

Ví dụ:

```json
{
  "player": { "pos": [0, 0, 0], "carried": 0, "flames": 3 },
  "random_motes": false,
  "random_shades": false,
  "motes": [[0, 0, 5]],
  "shades": [{ "pos": [10, 0, 0] }],
  "lanterns": [{ "id": "L1", "pos": [0, 0, 25], "deposited": 0 }],
  "time_left_s": 300
}
```

- `random_motes: false`: không tự sinh đom đóm, chỉ dùng danh sách được liệt kê.
- `random_shades: false`: không tự sinh Bóng Mực, chỉ dùng danh sách được liệt kê; chúng hoạt động bình thường ngay lập tức.
- `lanterns`: cập nhật theo ID đèn của màn (`L1`…`L5`). Đèn không được nhắc đến giữ nguyên; có `pos` thì đổi vị trí; có thể đặt `lit: true`.
- `motes` và `shades`: thay thế danh sách ban đầu tương ứng; mảng rỗng nghĩa là không có phần tử. Shade có thể kèm `id` để test tham chiếu.
- Trường không có dùng mặc định của game.
- Dựng scenario không phát event và không cộng điểm; ví dụ đèn được đặt `lit: true` không cộng điểm thắp.

## E. Output JSONL

Mỗi dòng là một đối tượng JSON. Có ba loại dòng: snapshot, event và end.

### Snapshot

Ghi mỗi `--snapshot-every` tick, bắt đầu từ tick 0. Ví dụ:

```json
{"type":"snapshot","tick":120,"sim_tick":120,"state":"playing","time_left_s":298.0,"score":20,"player":{"pos":[0.0,0.0,12.0],"flames":3,"carried":2},"lanterns":[{"id":"L1","pos":[0,0,25],"lit":false,"deposited":0}],"shades":[{"id":"S1","pos":[30.1,1.0,2.0],"state":"chase"}],"motes_active":19}
```

### Event

Ghi ngay khi event xảy ra. Ví dụ:

```json
{"type":"event","tick":131,"name":"mote_picked","data":{"carried":3}}
```

Các event và dữ liệu:

| `name` | `data` |
|---|---|
| `mote_picked` | `{"carried": n}` |
| `deposit` | `{"lantern_id":"L1","amount":n,"deposited":n}` |
| `lantern_lit` | `{"lantern_id":"L1"}` |
| `pulse` | `{"stunned_ids":["S1"]}` |
| `player_hit` | `{"by":"shade" hoặc "fall","flames":n,"dropped":n}` |
| `shade_spawned` | `{"id":"S3"}` |
| `game_over` | `{"result":"won" hoặc "lost","reason":"all_lit" hoặc "dawn" hoặc "no_flames"}` |

Dòng cuối cùng và bắt buộc:

```json
{"type":"end","ticks":4800,"state":"won","score":1730}
```

- `state` là `playing`, `won` hoặc `lost`.
- Bóng Mực phải có tối thiểu trạng thái `stunned`; trạng thái khác tùy game.
- Tọa độ làm tròn đến 3 chữ số thập phân.
- Nếu game không có một event nào đó (ví dụ không có rơi khỏi đảo), không ghi event đó.
- `sim_tick` là số bước gameplay đã chạy; Phase 1 bằng tick.
- Mảng `motes` trong snapshot, mỗi phần tử có `id` và `pos`, là khuyến nghị trong v1.0.

## F. Tính tất định

Cùng `--seed`, cùng scenario và cùng inputs phải tạo output giống hệt giữa hai lần chạy, bao gồm cả ID tự sinh. Các bài không cần dùng cùng chuỗi ngẫu nhiên với nhau.

