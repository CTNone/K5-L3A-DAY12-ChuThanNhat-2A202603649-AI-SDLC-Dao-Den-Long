# Checklist kế hoạch — Phase 1

Checklist này dựa trên PRD-0 và Test Contract v1.0. Các giá trị gameplay chưa được PRD quy định cần được chọn, ghi lại trong giả định và khai báo nhất quán trong `game.contract.json`.

## Trạng thái rà soát

| Hạng mục | Tình trạng | Căn cứ / việc còn lại |
|---|---|---|
| Quyết định công nghệ và giả định gameplay | Đã ghi | Python 3.10+, Tkinter; chi tiết trong `docs/notes/phase-1-assumptions.md` |
| Contract, tuning và headless 60 Hz | Đã kiểm chứng | `game.contract.json`; `tools/verify_phase1.py` |
| Lõi gameplay, thắng/thua, điểm, HUD và chơi lại | Có triển khai; có bằng chứng GUI | Ảnh start/win/loss trong `docs/proof/phase-1/`; người chơi cần tự xác nhận cảm giác điều khiển và chơi hết ván |
| Inputs, scenario, JSONL, mã lỗi, tính tất định | Đã kiểm chứng | Bằng chứng và kịch bản trong `docs/proof/phase-1/` |
| README, ghi chú giả định, nhật ký AI và harness | Đã có | `README.md`, `docs/notes/phase-1-assumptions.md`, `AGENTS.md`, các script verify/capture |
| Tag và phát hành lên remote | Cần hoàn tất | Tag `phase-1` hiện có cục bộ; phải cập nhật để chứa toàn bộ thay đổi phase 1 rồi push tag và commit |
| Chạy trên macOS/Linux | Chưa xác minh trực tiếp | README có lệnh tương thích; Tkinter cần có trên máy Linux/macOS |

**Kiểm tra gần nhất:** `py_compile` và `python tools/verify_phase1.py` chạy đạt trên Windows/Python 3.11.9. Ảnh GUI hiện có là bằng chứng do người chơi cung cấp; lần rà soát này không tự chơi lại GUI.

## 1. Chuẩn bị và quyết định

- [ ] Chọn engine/ngôn ngữ và cách chạy được trên macOS hoặc Linux.
- [ ] Chọn cách biểu diễn đảo tròn, va chạm, nhảy, camera, ánh sáng và giao diện.
- [ ] Quyết định các luật PRD chưa quy định: tính điểm, số đom đóm/địch ban đầu, cách nạp đèn, tác dụng/giới hạn pulse, điều kiện gây sát thương và điều kiện hết giờ.
- [ ] Ghi các giả định cùng thông số gameplay vào tài liệu ghi chép.
- [ ] Chọn một ý sáng tạo nhỏ, chỉ triển khai sau khi lõi đã chạy và được kiểm chứng.

## 2. Contract và nền tảng headless

- [ ] Tạo `game.contract.json` ở gốc repo với `contract_version`, `team`, `build_cmd`, `run_cmd`, `headless_cmd` và `tuning`.
- [ ] Đặt `contract_version` là `"1.0"` và `lantern_count_night1` là `5`.
- [ ] Khai báo đúng mọi giá trị tuning đang dùng; dùng `null` hoặc `false` nếu game không có khái niệm đó và giải thích trong README.
- [ ] Tách logic mô phỏng khỏi đồ họa để headless chạy không cửa sổ, không GPU.
- [ ] Chạy mô phỏng cố định 60 tick/giây; `--ticks N` chạy đúng N bước, trừ khi game kết thúc sớm.
- [ ] Đúng thứ tự tick: snapshot tick 0 sau khi dựng scenario và trước input; input tick `k` tạo trạng thái `k+1`; event ghi tick `k+1`.
- [ ] Tính `time_left_s` từ số bước đã chạy, không từ đồng hồ thực.
- [ ] Hỗ trợ `--seed`, `--night`, `--scenario`, `--inputs`, `--ticks`, `--out`, `--snapshot-every`.
- [ ] Chạy hợp lệ thoát mã 0; file inputs/scenario sai định dạng thoát mã 2; lỗi khác thoát mã khác 0 và ghi stderr.

## 3. Game chơi được

- [ ] Dựng màn “Đêm 1 – Đảo Bến”: đảo tròn và 5 Đèn Lồng Lớn.
- [ ] Mây đi lại, nhảy và điều khiển được camera 3D.
- [ ] Đom đóm xuất hiện trên đảo, nhặt được và có thông tin số lượng đang mang.
- [ ] Người chơi nạp đom đóm vào đèn; HUD thể hiện tiến độ thắp.
- [ ] Bóng Mực đuổi theo người chơi; chạm vào gây mất lửa/máu theo tuning.
- [ ] Pulse tốn ánh sáng và xua đuổi/làm choáng Bóng Mực theo tuning.
- [ ] Thắng khi thắp hết đèn; thua khi hết lửa hoặc theo điều kiện kết thúc đã chọn.
- [ ] Có điểm số và HUD hiển thị thông tin cần thiết để chơi.
- [ ] Có thể chơi lại sau khi thắng hoặc thua.
- [ ] Không khí đêm ấm áp, cổ tích; vàng cam là ánh sáng tốt, tím đen là nguy hiểm; không máu me.

## 4. Inputs và scenario

- [ ] Scenario cho phép đặt người chơi, đom đóm, Bóng Mực, đèn và thời gian còn lại.
- [ ] `random_motes: false` và `random_shades: false` nghĩa là chỉ dùng danh sách được liệt kê.
- [ ] Đèn cập nhật theo ID `L1`–`L5`; đèn không được nhắc tới giữ mặc định.
- [ ] Scenario không phát event và không cộng điểm.
- [ ] Inputs có tick tăng nghiêm ngặt; từ chối tick trùng/giảm và move ngoài `[-1, 1]`.
- [ ] Trường vắng mặt giữ giá trị trước đó; mặc định ban đầu move `[0,0]`, yaw `0`, mọi nút false.
- [ ] `jump`, `interact`, `pulse` (và dash nếu có) chỉ kích hoạt khi chuyển false sang true.
- [ ] Chuyển hướng move theo `cam_yaw_deg` đúng công thức contract; chuẩn hóa vector dài hơn 1.
- [ ] Dùng khoảng cách XZ giữa các điểm quy ước; “trong bán kính r” nghĩa là khoảng cách `≤ r`.

## 5. Output và tính tất định

- [ ] Ghi JSONL gồm snapshot, event và đúng một dòng `end` cuối cùng.
- [ ] Snapshot có các trường tối thiểu theo contract: tick/sim tick, state, thời gian, điểm, player, lanterns, shades, `motes_active`.
- [ ] Tọa độ làm tròn 3 chữ số thập phân.
- [ ] Phát event đúng khi nhặt mote, nạp/thắp đèn, pulse, player bị hit, shade xuất hiện và game kết thúc.
- [ ] Event `game_over` dùng result/reason hợp lệ; dòng `end` có ticks/state/score.
- [ ] Seed điều khiển mọi yếu tố ngẫu nhiên và ID tự sinh; cùng seed, scenario, inputs cho output giống hệt giữa hai lần chạy.
- [ ] Chế độ headless không tạo thực thể/hiệu ứng bổ sung làm đổi output contract.

## 6. Kiểm chứng và bằng chứng

- [x] Build và mở game có giao diện; chơi từ đầu đến thắng hoặc thua. Ảnh người chơi cung cấp: `docs/proof/phase-1/gui-start.png`, `gui-win.png`.
- [x] Tạo scenario kiểm tra nhặt mote, nạp/thắp đèn, pulse, bị đánh và kết thúc.
- [x] Kiểm tra tick 0, input tick, giới hạn ticks, snapshot interval, JSONL và mã thoát.
- [x] Chạy hai lần cùng seed/scenario/inputs và so sánh output nguyên vẹn.
- [ ] Lưu bằng chứng thật: lệnh, input/scenario, output và ảnh/clip cho đồ họa, HUD, điều khiển. Đã có ảnh bắt đầu/thắng/thua; chưa có clip liên tục.
- [x] Gắn từng bằng chứng với yêu cầu được kiểm tra; ghi “chưa đạt” và lý do cho phần còn thiếu.
- [x] Ghi giả định, nhật ký AI, ước tính token/chi phí và lỗi AI đã phát hiện.

Chi tiết: [docs/proof/phase-1/README.md](docs/proof/phase-1/README.md). Ảnh người chơi cung cấp xác nhận trạng thái bắt đầu, thắng và thua; headless cũng xác nhận kết thúc thua. Scenario headless nạp/thắp đèn, pulse, hit và cả hai kết thúc đã được lưu thành artifact. Chưa có clip liên tục.

## 7. Bàn giao Phase 1

- [ ] README có cài đặt/chạy tối đa 3 lệnh, điều khiển, tính điểm và lệnh headless.
- [ ] README có mục “Sáng tạo của tôi” nếu có phần sáng tạo thêm.
- [ ] Repo có harness AI đã dùng, ghi chép và bằng chứng kiểm chứng.
- [ ] `game.contract.json` khớp với code và hành vi thực tế.
- [ ] Commit nhỏ, rõ; gắn tag `phase-1` và push trước hạn 1 giờ.

