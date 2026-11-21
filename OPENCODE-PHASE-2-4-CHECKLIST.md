# OpenCode — Checklist Phase 2, 3 và 4

> **Kế hoạch đã thực thi.** Trạng thái hiện tại xem `CHECKPOINTS.md`; kiến trúc là Godot 4.7.2 (GUI) + Python headless.

## Chỉ dẫn chung

- Làm tuần tự **Phase 2 → Phase 3 → Phase 4**. Không gộp nhiều phase trong một lượt.
- Mỗi phase có checklist và prompt riêng bên dưới. Chỉ bắt đầu phase kế tiếp khi tôi xác nhận hoặc gửi yêu cầu tiếp theo.
- Yêu cầu sản phẩm xuyên suốt: đây phải là **game 3D thực sự có camera 3D và giao diện game hoàn chỉnh**, chạy được trên macOS/Linux. Không coi hình vẽ giả 3D hoặc cửa sổ Tkinter là đã đạt mục tiêu 3D.
- Trước khi code, kiểm tra game hiện tại đang render bằng gì. Nếu chưa phải 3D thực sự, hãy đề xuất lộ trình chuyển sang engine phù hợp và nêu rõ ảnh hưởng tới GUI, headless, build và Test Contract. Ưu tiên Godot nếu dự án cần engine 3D nhưng chưa có engine phù hợp; không tự ý chuyển trước khi trình bày kế hoạch, cách giữ contract và migration có thể kiểm chứng.
- Dùng router Awesome Gamedev Agent Skills. Khi dự án là Godot, dự kiến chọn `godot-gdscript` + `godot-3d-essentials` cho nền 3D; ghép `game-ui-ux`/`godot-ui-control` cho HUD/menu; `camera-systems` cho camera; `godot-gdscript-headless-testing` cho kiểm thử. Chỉ nạp skill liên quan đúng việc đang làm và báo tên/lý do. Không nạp Godot skill nếu dự án chưa chuyển Godot.
- Test Contract là chuẩn bắt buộc. Không làm thay đổi kết quả headless để thêm hiệu ứng/trang trí. Nội dung sáng tạo phải tắt hoặc không ảnh hưởng đầu ra kiểm thử theo yêu cầu từng phase.
- Trước mỗi phase: đọc `AGENTS.md`, PRD, contract, README, checklist và lịch sử Git. Ghi các giả định/điểm mơ hồ; không tự bịa số liệu khi contract chưa quy định.
- Sau mỗi phase: chạy kiểm chứng cần thiết, lưu bằng chứng, cập nhật tài liệu và checklist, báo cáo lệnh/kết quả thật. Không tạo tag nộp cho đến khi các việc cần chủ dự án xác nhận đã xong.

---

## Phase 2 — Ticket-02, Contract v1.1, tag `phase-2`

### Checklist thực hiện cho OpenCode

- [ ] Đọc ticket Phase 2 đầy đủ và chuyển thành spec có acceptance criteria theo từng yêu cầu.
- [ ] Kiểm tra trạng thái Phase 1, contract v1.0, tag/commit và test/evidence hiện có.
- [ ] Kiểm tra yêu cầu 3D/UI xuyên suốt; báo cáo đề xuất engine/migration trước khi sửa kiến trúc nếu hiện tại chưa phải 3D thật.
- [ ] Cập nhật harness `AGENTS.md`, cấu hình skill/ghi chú router và quy trình kiểm thử cho phạm vi Phase 2; để lịch sử Git thể hiện thay đổi.
- [ ] Nâng headless contract lên v1.1, hỗ trợ `--night 1|2|3`, tick cố định 60 Hz, pause/tick/sim_tick đúng quy tắc.
- [ ] Chuẩn hóa số liệu chung theo ticket: tốc độ, sức chứa, khoảng cách, pulse, dash, máu, bất tử, rơi, shade, score và thời lượng từng đêm. Điền đúng `game.contract.json`.
- [ ] Dựng đủ ba bản đồ chuẩn theo ticket: Đêm 1 đảo tròn bán kính 40 m; Đêm 2 hai đảo và cầu; Đêm 3 đảo ba tầng, dốc, bục nhảy và tháp chuông. Kiểm tra tọa độ, tầng cao, điểm spawn và đèn.
- [ ] Làm đủ luật gameplay từng đêm: đom đóm, Bóng Mực, Gió Lạc ở Đêm 2/3, bùa gió, gió mạnh Đêm 3, nhảy/lướt, tương tác đèn, tỏa sáng, vùng an toàn, rơi và luật thắng/thua Phase 2.
- [ ] Làm chuỗi menu → giới thiệu đêm → chơi → kết quả → đêm kế tiếp; thắng Đêm 3 có màn Bình Minh, thua cho chơi lại đúng đêm.
- [ ] Làm pause/resume/retry/settings; lưu âm lượng và độ nhạy chuột.
- [ ] Làm HUD theo ticket: Ngọn Lửa, đồng hồ, đèn/điểm, 10 ô đom đóm, cooldown, nhắc tương tác, chỉ hướng đèn chưa sáng, cảnh báo cần thiết.
- [ ] Thêm âm nhạc và các hiệu ứng âm thanh liệt kê; có điều khiển âm lượng.
- [ ] Đảm bảo bản GUI là 3D thật, camera 3D hoạt động, giao diện rõ ở 1280×720, bản thường trung bình đạt ít nhất 30 FPS trên máy đo phù hợp.
- [ ] Tạo ít nhất một scenario headless cho từng tính năng mới; giữ regression Phase 1.
- [ ] Đo headless một đêm tối đa 21.600 tick và xác nhận hoàn tất trong ≤30 giây.
- [ ] Ghi bằng chứng, cập nhật README (tối đa 3 lệnh cài/chạy), spec, checklist, assumptions và nhật ký AI.
- [ ] Kiểm tra clone sạch/build trên macOS/Linux hoặc cung cấp cách chạy được cho giảng viên.
- [ ] Báo cáo các bước cần tôi tự chơi/kiểm tra. Chờ tôi xác nhận trước Phase 3.

### Prompt bắt đầu Phase 2

```text
Bắt đầu riêng Phase 2 theo file OPENCODE-PHASE-2-4-CHECKLIST.md và Ticket-02 tôi đã cung cấp. Trước tiên kiểm tra 3D hiện trạng, repo/contract/tag/test; nếu cần đổi engine hoặc migration thì trình bày kế hoạch nhỏ, các rủi ro và cách giữ headless contract trước khi sửa kiến trúc. Game đích phải là 3D thật có UI đầy đủ.

Sau khi chốt cách triển khai, làm lần lượt các checklist Phase 2. Giữ nguyên số liệu và thứ tự tick của Ticket-02, xây tests/scenarios cho từng tính năng, giữ regression Phase 1, cập nhật tài liệu và lưu bằng chứng. Không làm Phase 3/4, không tạo tag phase-2 cho tới khi Phase 2 được kiểm chứng và tôi xác nhận các việc cần người dùng đã hoàn thành. Báo cáo skill đã nạp, file đổi, lệnh kiểm chứng và kết quả thực tế.
```

---

## Phase 3 — Ticket-03 “Đèn cạn dầu”, Contract v1.2, tag `phase-3`

### Checklist thực hiện cho OpenCode

- [ ] Đọc Ticket-03 như change request thay đổi luật lõi; ghi ADR ngắn về mô hình nhiên liệu/ever_lit và luật thắng mới trước hoặc cùng lúc triển khai.
- [ ] Cập nhật spec và contract lên v1.2; giữ toàn bộ phần v1.1 không bị ticket thay thế.
- [ ] Thêm fuel nguyên theo tick 1/60; ánh sáng tự hao 1/s, Bóng Mực drain hút 5/s; xử lý hết dầu đúng thứ tự tick, phát `lantern_out`, đặt deposited=0 và giữ `ever_lit`.
- [ ] Cài đặt nạp dầu: `used=min(carried, ceil((100-fuel)/10))`; chỉ chọn đèn nhận được gần nhất, hòa thì id nhỏ hơn; đèn đầy không phát event/điểm.
- [ ] Thắp mới cần 10 đom đóm; thắp lại cần 5; dầu được đặt 100. Theo dõi `successful_lights`, tăng capacity `min(20,10+2*successful_lights)` và reset đầu mỗi đêm.
- [ ] Cập nhật AI shade: wander ưu tiên đèn sáng yếu nhất theo quy tắc gần nhất; drain trong ≤2 m; chase khi người chơi ≤6 m; xử lý stunned/wander và đẩy shade khi dầu được châm lên ≥30.
- [ ] Mất safe radius khi fuel<30; đúng 30 vẫn an toàn. Thêm hiệu ứng/hiển thị thanh dầu và nhấp nháy 1 Hz khi dưới ngưỡng.
- [ ] Thay luật thắng bằng sống tới bình minh và đạt ngưỡng 60% số đèn; xử lý `no_flames` trước kết quả bình minh, không còn thắng sớm khi tất cả đèn sáng.
- [ ] Thay toàn bộ scoring theo Ticket-03; bỏ thưởng thời gian, tính dawn bonus chỉ khi thắng.
- [ ] Thêm setting bảng màu dễ phân biệt có lưu; đảm bảo phân biệt đèn sáng/tắt không phụ thuộc màu, cảnh báo có biểu tượng.
- [ ] Cập nhật schema `game.contract.json` v1.2, snapshot/scenario/event, gồm fuel, ever_lit, relit_count, capacity, drain và các trường mới.
- [ ] Sửa test Phase 1/2 bị thay đổi; xóa test chỉ khi ghi rõ lý do; tuyệt đối không skip âm thầm. Thêm scenario cho refuel, depletion, relight, drain, pushback, ngưỡng dawn, scoring và color mode.
- [ ] Thêm changelog về breaking changes Phase 3; giữ bản game GUI 3D và giao diện HUD cỡ dầu/capacity/cảnh báo.
- [ ] Chạy test regression Phase 1–2 còn hiệu lực; lưu bằng chứng và cập nhật README/spec/assumptions.
- [ ] Báo cáo việc cần tôi tự kiểm tra và chờ tôi xác nhận trước Phase 4.

### Prompt bắt đầu Phase 3

```text
Bắt đầu riêng Ticket-03 Phase 3 sau khi Phase 2 đã được tôi xác nhận. Đọc checklist và contract hiện hành. Đây là breaking change: lập ADR ngắn trước khi sửa luật, cập nhật tests cũ bị ảnh hưởng có ghi lý do, không skip âm thầm. Thực hiện nhiên liệu, drain, luật thắng bình minh, capacity, scoring, color mode và contract v1.2 đúng nguyên văn Ticket-03.

Giữ nguyên game 3D và UI; cập nhật HUD/đèn để thể hiện fuel, capacity, cảnh báo dưới 30 và chế độ màu dễ phân biệt. Giữ output headless tất định và regression các test v1.0/v1.1 còn hiệu lực. Không làm Phase 4, không tạo tag phase-3 trước khi test/evidence/tài liệu hoàn tất. Báo cáo thay đổi tương thích, test và kết quả thực tế; chờ tôi xác nhận trước phase sau.
```

---

## Phase 4 — Ticket-04 “Bình minh: phát hành v1.0.0”, Contract v1.3, tag `phase-4`

### Checklist thực hiện cho OpenCode

- [ ] Đọc Ticket-04 và rà soát hợp đồng v1.0–v1.2; nâng `game.contract.json` lên v1.3 mà không xóa yêu cầu còn hiệu lực.
- [ ] Thêm `bench_cmd` và `soak_cmd`; benchmark đúng cảnh chuẩn 1280×720, 200 shade, 100 mote, 3 lantern, camera bay vòng; khởi động 3 giây rồi đo đúng thời lượng.
- [ ] Tính chính xác `avg_fps`, `p1_low_fps`, `frame_ms_p95`, `frames`, `load_ms`, `peak_mem_mb`; ghi renderer/OS/vsync và không để hiệu ứng sáng tạo tác động phép đo.
- [ ] Tạo soak test 10 đêm trong cùng tiến trình, seed/input theo ticket; báo crashes, kết quả từng đêm, RSS đầu/cuối và thời gian.
- [ ] Lưu `bench.json` và `soak.json` do chạy thực tế vào repo; phân biệt phép đo của máy phát triển với ngưỡng chấm trên máy giảng viên.
- [ ] Làm bảng xếp hạng top 10 lưu bền; xác thực tên 3–12 ký tự; tie-break người đạt trước; score/nights_won/ISO8601 timezone/seed đúng schema.
- [ ] Thêm màn bảng xếp hạng, nhập tên sau thua hoặc sau thắng Đêm 3, và `--export-leaderboard out.json` đúng thứ tự.
- [ ] Làm đổi phím mọi hành động, phát hiện xung đột, khôi phục mặc định, lưu thiết lập; chỉ báo hình ảnh cho shade/gió/10 giây cuối/fuel thấp; giảm chuyển động; chữ UI ≥18 px ở 1280×720 và tùy chọn ×1.25.
- [ ] Đảm bảo tất cả menu/HUD/cài đặt/hạng được kiểm tra bằng bàn phím và dễ đọc; giữ game 3D và tương thích macOS/Linux.
- [ ] Kiểm tra clone sạch: README tối đa 3 lệnh để cài và chơi; bổ sung ảnh/GIF, yêu cầu hệ thống, điều khiển, test, headless, bench, soak.
- [ ] Tạo `CHANGELOG.md` đủ 4 phase, `CREDITS.md` đầy đủ tài sản/âm thanh/công cụ AI, `LICENSE`, retro 1–2 trang.
- [ ] Chạy mọi test Phase 1–3 còn hiệu lực, benchmark, soak, kiểm tra export leaderboard và build/release sạch.
- [ ] Chuẩn bị artifact phát hành phù hợp (binary/web/Docker) và hướng dẫn cài/chạy.
- [ ] Chỉ sau khi bằng chứng và mọi việc người dùng hoàn tất: tạo/push tag `phase-4` và GitHub Release `v1.0.0`; không phát hành trước khi có xác nhận của tôi.

### Prompt bắt đầu Phase 4

```text
Bắt đầu riêng Ticket-04 Phase 4 sau khi tôi đã xác nhận Phase 3. Tuân theo checklist trong OPENCODE-PHASE-2-4-CHECKLIST.md và toàn bộ contract v1.0–v1.3 còn hiệu lực. Trước hết lập thứ tự triển khai có checkpoint cho benchmark/soak, leaderboard, accessibility, đóng gói và tài liệu.

Làm benchmark và soak theo đúng cảnh/số liệu/seed/thời lượng, không để nội dung sáng tạo ảnh hưởng kết quả. Triển khai bảng xếp hạng bền vững, export JSON, accessibility, tài liệu, LICENSE, credits và retro. Chạy kiểm chứng và commit bằng chứng thật. Giữ game 3D/UI và khả năng chạy macOS/Linux.

Không tạo/push tag phase-4 hoặc GitHub Release v1.0.0 cho đến khi tôi xem báo cáo cuối và xác nhận phát hành. Báo rõ số đo trên máy hiện tại, lệnh và kết quả, các ngưỡng chưa thể xác minh trên máy chấm, cùng mọi việc tôi cần tự làm.
```

## Điểm cần làm rõ trước khi OpenCode triển khai

- [ ] **Engine 3D hiện tại:** Tkinter không tự tạo game 3D thực. OpenCode phải xác minh trạng thái code thật rồi trình bày đề xuất engine/migration và cách duy trì headless trước khi thay kiến trúc.
- [ ] **Đầu ra OpenCode:** yêu cầu nó tạo kế hoạch và checkpoint trước; bạn duyệt từng phase riêng, không đưa cả ba prompt để nó chạy nối tiếp tự động.
- [ ] **Phát hành GitHub:** GitHub Release cần repo public/quyền ghi và artifact. OpenCode phải chuẩn bị artifact trước; thao tác release chỉ sau khi bạn duyệt.
