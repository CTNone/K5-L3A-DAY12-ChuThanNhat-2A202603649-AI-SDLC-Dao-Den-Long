# Phase 2 — Ticket-02 spec và acceptance criteria

**Nguồn yêu cầu:** checklist Phase 2 do chủ dự án cung cấp trong
`OPENCODE-PHASE-2-4-CHECKLIST.md`. Bản Ticket-02 đầy đủ (nếu có) chưa nằm trong
repo; các số liệu không được checklist quy định được ghi thành giả định trong
`docs/notes/phase-2-assumptions.md` và phải được chủ dự án xác nhận trước khi
coi là số liệu cuối.

## 1. Phạm vi

- Giữ Test Contract v1.0 làm nền; nâng lên v1.1 với `--night 1|2|3`, pause,
  `tick`/`sim_tick`, map mới và cơ chế Phase 2.
- Headless vẫn là Python zero-dependency, 60 Hz cố định, JSONL tất định.
- GUI là Godot 4.7 3D thật, xuất web (local trước), có camera 3D, HUD, menu,
  pause, settings, audio.
- Không làm Phase 3/4; không tạo tag `phase-2` trước khi chủ dự án xác nhận.

## 2. Acceptance criteria

### AC-2.1 Contract v1.1

- `game.contract.json` có `contract_version: "1.1"`.
- `headless_cmd` vẫn chạy `python3 game.py --headless` trên macOS/Linux.
- Hỗ trợ `--night 1|2|3`; night khác trả mã 2 và thông báo stderr.
- `tick` tăng mỗi vòng lặp; `sim_tick` chỉ tăng khi không pause.
- `time_left_s = duration_s - sim_tick/60`, kẹp tại 0.
- Snapshot có `tick`, `sim_tick`, `paused`, `night`; event giữ `tick` như v1.0.
- `--ticks N` chạy đúng N vòng lặp trừ khi game kết thúc sớm.

### AC-2.2 Tuning và dữ liệu chung

- Tuning nằm trong `game.contract.json`; map nằm trong `shared/maps/night1..3.json`.
- `godot/shared/` là bản sao được sinh bởi `tools/sync_shared.py`; có kiểm tra
  đồng bộ, không sửa tay bản sao.
- Các giá trị mới: dash, glide, Gió Lạc, bùa gió, gió mạnh, tháp chuông, thời
  lượng từng đêm. Night 2/3 dùng override `shade_speed` 2.8/3.1 và
  `lost_wisp_speed_m_s` 2.0/2.6. Giá trị cụ thể nằm trong assumptions.

### AC-2.3 Ba bản đồ

- Night 1: đảo tròn bán kính 40 m, 5 đèn vành 25 m, spawn người chơi tại
  `(0,0,0)`; 40 đom đóm, 3 Bóng Mực vành 32 m.
- Night 2: hai đảo tròn nối bằng cầu, 6 đèn, có Gió Lạc và bùa gió.
- Night 3: ba tầng (0 m/4 m/8 m), dốc, bục nhảy, tháp chuông, 7 đèn, gió mạnh,
  Gió Lạc và bùa gió.
- Mỗi map có toạ độ đèn, spawn người chơi, spawn shade/wisp/charm, bề mặt đi
  được và vùng gió; kiểm tra bằng test đọc JSON và snapshot headless.

### AC-2.4 Gameplay Phase 2

- Đom đóm nhặt bằng tương tác; nạp đèn; thắp đèn; vùng an toàn quanh đèn sáng.
- Bóng Mực đuổi, gây sát thương, bị pulse làm choáng/đẩy.
- Dash có cooldown; glide giới hạn tốc độ rơi khi giữ phím.
- Gió Lạc xuất hiện ở Night 2/3, đẩy người chơi khi lại gần.
- Bùa gió nhặt được, miễn đẩy từ Gió Lạc/gió mạnh trong thời gian hiệu lực.
- Gió mạnh ở Night 3 đẩy người chơi theo vùng; bùa gió chặn đẩy.
- Rơi khỏi bề mặt: mất 1 lửa, rơi đom đóm, hồi sinh tại điểm an toàn gần nhất.
- Night 1/2 thắng khi thắp hết đèn. Night 3 thắng khi thắp hết đèn và đứng
  trong bán kính tháp chuông.
- Thua khi hết lửa (`no_flames`) hoặc hết giờ (`dawn`).
- Ưu tiên cùng tick: `no_flames` → thắng → `dawn` (giả định, xem assumptions).

### AC-2.5 Scenario/inputs mở rộng

- Scenario: `paused`, `wisps`, `charms`, `random_wisps`, `random_charms`.
- Inputs: `dash`, `glide`, `pause` boolean; `pause` là trạng thái, không phải
  edge-trigger.
- Giữ nguyên quy tắc tick tăng nghiêm ngặt, move `[-1,1]`, chuẩn hóa vector,
  edge-trigger cho `jump`/`interact`/`pulse`/`dash`.
- Dựng scenario không phát event, không cộng điểm.

### AC-2.6 GUI 3D và UI

- Godot 4.7, renderer compatibility, cửa sổ 1280×720.
- World 3D thật: `Node3D`, `Camera3D` + camera follow/orbit tự viết, player 3D, đèn, sương,
  ánh sáng; không dùng Tkinter cho GUI mới.
- Chuỗi màn: menu → giới thiệu đêm → chơi → kết quả → đêm kế; thắng Night 3
  có màn Bình Minh; thua cho chơi lại đúng đêm.
- Pause/resume/retry/settings; lưu âm lượng và độ nhạy chuột.
- HUD: lửa, đồng hồ, đèn/điểm, 10 ô đom đóm, cooldown pulse, nhắc tương tác,
  chỉ hướng đèn chưa sáng, cảnh báo.
- Âm nhạc + SFX; điều khiển âm lượng.
- Trung bình ≥30 FPS ở 1280×720 trên máy đo phù hợp; ghi cấu hình đo.

### AC-2.7 Web local

- `python3 tools/build_web.py` xuất Godot web vào `build/web/`.
- `python3 tools/serve_web.py` phục vụ local với COOP/COEP và MIME đúng.
- Đã kiểm tra Chrome 157 headless (SwiftShader) với WebGL 2.0; Edge/Firefox và macOS/Linux chưa kiểm tra.
- Không commit `build/web/`; có thể phát hành artifact ở Phase 4.

### AC-2.8 Kiểm chứng và bằng chứng

- `python3 -m py_compile ...` đạt.
- `python3 tools/verify_phase1.py` vẫn đạt sau khi cập nhật test theo v1.1.
- `python3 tools/verify_phase2.py` đạt: map, pause/tick/sim_tick, dash, glide,
  wisp, charm, wind, fall, win/lose Night 3, invalid night, determinism.
- Headless Night 3 21.600 tick ≤30 giây.
- `tools/capture_phase2_evidence.py` ghi JSONL/stderr/lệnh/so sánh vào
  `docs/proof/phase-2/`; không sửa tay output.
- Ảnh/video GUI do chạy thật; người dùng xác nhận cảm giác chơi và macOS/Linux.

## 3. Ngoài phạm vi Phase 2

- Fuel/ever_lit/relight, luật bình minh 60% đèn, scoring mới, color mode:
  Phase 3.
- Benchmark/soak chính thức, leaderboard, remap đầy đủ, accessibility nâng cao,
  release v1.0.0: Phase 4.
- Docker: sau Phase 2; WSL có thể dùng để kiểm tra Linux.

## 4. Định nghĩa hoàn thành Phase 2

- Tất cả AC trên có bằng chứng thật trong repo.
- Không có regression Phase 1 chưa được ghi lý do.
- README tối đa 3 lệnh cài/chạy; spec/assumptions/checklist/AI log cập nhật.
- Chủ dự án xác nhận các việc cần tự chơi/kiểm tra.
- Chỉ sau đó mới tạo tag `phase-2`.
