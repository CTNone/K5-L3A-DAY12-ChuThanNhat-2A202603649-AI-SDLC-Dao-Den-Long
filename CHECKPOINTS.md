# Lộ trình Checkpoints: Day 12 AI SDLC

> **Cá nhân.** Làm lần lượt Checkpoint 0 đến 5. Mỗi checkpoint là một mốc tự kiểm tra, không phải bài nộp riêng.
> Yêu cầu của từng phase nằm trên **[lab board](https://claude.ai/artifact/Q1RYyv1dxjUczzCbd2ZnoW)**. Tài liệu này không lặp lại và không tiết lộ yêu cầu phase sau.
> Cách làm: [GUIDE.md](GUIDE.md). Nộp bài: [SUBMISSION.md](SUBMISSION.md).
> Cách trình bày bằng chứng, tên file và cấu trúc thư mục do bạn chọn. Các gợi ý dưới đây chỉ là ví dụ.

## Trạng thái hiện tại (cập nhật 2026-11-21)

| Checkpoint | Trạng thái | Ghi chú |
|---|---|---|
| CP0 | Một phần | Repo public, môi trường và nơi ghi chép đã có; còn xác nhận lab board/hạn nộp và clone sạch. |
| CP1 | Xong | Tag `phase-1` đã có cả local và remote; evidence Phase 1 đầy đủ. |
| CP2 | Code/evidence xong | Tag `phase-2` mới có ở local, **chưa push remote**. |
| CP3 | Code/evidence xong | Tag `phase-3` mới có ở local, **chưa push remote**. |
| CP4 | Đã xong phần chạy được | Contract `1.3`; `bench.json`, `soak.json`, leaderboard, web zip, tag `phase-4`/Release `v1.0.0`; xem `docs/proof/phase-4/`. |
| CP5 | Đang hoàn tất | Video `docs/demo/demo.mp4`, spec/giả định/retro/AI log đã có; còn xác nhận link nộp LMS. |

Đã kiểm tra ngày 2026-11-21: `origin` là `https://github.com/CTNone/K5-L3A-DAY12-ChuThanNhat-2A202603649-AI-SDLC-Dao-Den-Long.git`; GitHub API trả về `visibility=public`; `git ls-remote --tags origin` chỉ thấy `phase-1`.

## Lịch 4 giờ

| Checkpoint | Mốc | Thời lượng |
|---|---|---|
| CP0 Chuẩn bị | 0h (trong giờ Phase 1) | khoảng 10 phút |
| CP1 Phase 1 | 0h đến 1h | 60 phút (gồm CP0) |
| CP2 Phase 2 | 1h đến 2h | 60 phút |
| CP3 Phase 3 | 2h đến 2h30 | 30 phút |
| CP4 Phase 4 và phát hành | 2h30 đến 4h | 90 phút |
| CP5 Video và nộp | trong 15 phút cuối của giờ thứ tư | 10 đến 15 phút |

Hết giờ mỗi phase: gắn tag, push, rồi đi tiếp.

## Big picture

```
CP0 Chuẩn bị  ->  CP1 Phase 1  ->  CP2 Phase 2  ->  CP3 Phase 3  ->  CP4 Phase 4 + Release  ->  CP5 Nộp bài
```

Mỗi checkpoint phase (CP1 đến CP4) có cùng một khung, nhưng nội dung yêu cầu do ticket của phase đó quyết định:

| Bước | Câu hỏi tự kiểm tra |
|---|---|
| Hiểu | Mình đã tách được yêu cầu bắt buộc khỏi chỗ mơ hồ chưa? Giả định đã ghi chưa? |
| Kế hoạch kiểm chứng | Với mỗi yêu cầu chính, mình biết cách chứng minh nó chạy đúng chưa? |
| Xây dựng | Agent làm theo kế hoạch đã duyệt chưa? Commit có nhỏ và rõ không? |
| Kiểm chứng | Mọi yêu cầu chính đã có bằng chứng thật chưa? Cái nào chưa đạt đã ghi trung thực chưa? |
| Hồi quy | Những gì đúng ở phase trước còn đúng không? Test nào bị yêu cầu mới làm sai đã được sửa hoặc bỏ kèm lý do chưa? |
| Đánh giá | AI đã sai ở đâu? Mình chỉnh harness gì? Mình đã dùng bao nhiêu token? |
| Phát hành | Đã gắn tag `phase-N` và push chưa? |

---

## Checkpoint 0: Chuẩn bị (khoảng 10 phút)

**Mục tiêu:** có môi trường làm việc và repo sẵn sàng. Nên chuẩn bị **trước** buổi lab nếu có thể. Nếu không, làm ngay đầu giờ Phase 1.

Việc cần làm:
- [x] Tạo **repo cá nhân, public** trên GitHub, đặt tên theo [SUBMISSION.md](SUBMISSION.md). *(Đã xác minh public qua GitHub API.)*
- [x] Chọn công cụ AI, engine và ngôn ngữ. Cài và chạy thử một chương trình "hello" 3D hoặc headless để chắc môi trường ổn. *(Python 3.11 + Godot 4.7.2; headless và web build đã chạy.)*
- [ ] Đăng nhập claude.ai, mở lab board, thử mở tab Phase 1 và hỏi trợ giảng một câu bất kỳ để chắc trợ giảng hoạt động. *(Chưa có bằng chứng trong repo.)*
- [x] Tạo sẵn nơi ghi chép (một file hoặc một thư mục tùy bạn) cho giả định, nhật ký dùng AI và bằng chứng. *(Đã có `docs/notes/` và `docs/proof/`; nhật ký AI nằm trong `docs/proof/phase-1/README.md`, chưa có file riêng.)*
- [ ] Kiểm tra hạn nộp từng phase theo thông báo của Coach. *(Thông tin cá nhân, không kiểm chứng từ repo.)*

Tự kiểm: clone repo sang thư mục khác và chạy được chương trình thử. *(Chưa có log clone sạch; sẽ thực hiện ở CP4.)*

---

## Checkpoint 1: Phase 1 (PRD-0), 0h đến 1h

**Mục tiêu:** từ một mô tả tổng quát và mơ hồ, làm ra một bản chơi được của màn đầu tiên, kèm chế độ headless theo Test Contract, và chứng minh nó đúng.

Gợi ý:
- [x] Đọc PRD-0 hai lần. Lần một đọc để hiểu game. Lần hai gạch chân những chỗ mơ hồ và những chỗ **bắt buộc chính xác** (Test Contract). *(Đã có `docs/notes/phase-1-assumptions.md`; không có log riêng việc đọc hai lần.)*
- [x] Viết giả định cho từng chỗ mơ hồ, và các con số bạn tự chọn. Những con số này sẽ cần khai báo theo yêu cầu của contract. *(Xem `docs/notes/phase-1-assumptions.md` và `game.contract.json`.)*
- [x] Tách logic game khỏi phần hiển thị để chạy được headless. *(`game.py` cho mô phỏng/headless; `godot/` cho GUI.)*
- [x] Tự viết vài scenario nhỏ và kiểm tra đầu ra đúng định dạng. *(`docs/proof/phase-1/` có scenario, input, JSONL và log.)*
- [x] Chạy hai lần cùng đầu vào và so sánh, nếu contract yêu cầu tính tất định. *(`determinism-a.jsonl`, `determinism-b.jsonl`, `determinism-compare.txt`.)*
- [x] Làm đúng các bàn giao liệt kê trong PRD-0. *(Contract, README, verify/capture tools và evidence Phase 1.)*

Tự kiểm:
- [ ] Clone sạch, làm theo README của bạn, chạy được game. *(Chưa có log clone sạch; sẽ thực hiện ở CP4.)*
- [x] Mỗi yêu cầu chính có bằng chứng; chỗ chưa đạt đã ghi. *(Bảng evidence Phase 1 và ghi chú review.)*
- [x] Đã gắn tag `phase-1` và push. *(Tag local `phase-1`; remote có `refs/tags/phase-1`.)*

---

## Checkpoint 2: Phase 2 (Ticket-02), 1h đến 2h

**Mục tiêu:** tiếp nhận yêu cầu mới, mở rộng sản phẩm mà không làm hỏng những gì đã đúng.

Gợi ý:
- [x] Đọc ticket, so với những giả định ở Phase 1. Chỗ nào ticket đã làm rõ hoặc đổi, cập nhật giả định. *(`docs/notes/phase-2-spec.md`, `phase-2-assumptions.md`.)*
- [x] Viết kế hoạch kiểm chứng cho phần mới **trước** khi code. *(`docs/notes/phase-2-spec.md`.)*
- [x] Chạy lại toàn bộ kiểm chứng của Phase 1 sau khi tích hợp. *(`docs/proof/phase-2/verify-phase1.log`: 11/11 check.)*
- [x] Rà soát harness: agent có sai lặp lại không? Đã đến lúc thêm một dòng vào hướng dẫn, một skill hay một hook chưa? *(Ghi chú trong spec/assumptions; chưa có log review riêng.)*

Tự kiểm:
- [x] Phần mới có bằng chứng; phần cũ không bị hỏng (hoặc có lý do rõ ràng nếu đổi). *(`docs/proof/phase-2/verify-phase2.log`: 15 check; Phase 1 vẫn đạt.)*
- [ ] Đã gắn tag `phase-2` và push. *(Tag local `phase-2` đã có; remote **chưa có** tag này.)*

---

## Checkpoint 3: Phase 3 (Ticket-03), 2h đến 2h30

**Mục tiêu:** xử lý một thay đổi yêu cầu có thể **thay thế** những luật đã có.

Gợi ý:
- [x] Đọc kỹ những chỗ ticket nói luật cũ bị thay. Liệt kê những test, tài liệu và giả định cũ bị ảnh hưởng. *(`docs/notes/phase-3-adr.md`, `phase-3-test-changes.md`.)*
- [x] Ghi lại ngắn gọn bạn thay đổi thiết kế thế nào và vì sao (một đoạn ngắn là đủ). *(`docs/notes/phase-3-adr.md`.)*
- [x] Test cũ bị luật mới làm sai: **sửa hoặc bỏ kèm lý do**, không bỏ qua âm thầm. *(`docs/notes/phase-3-test-changes.md`.)*
- [x] Chạy lại tất cả kiểm chứng còn hiệu lực. *(`docs/proof/phase-3/verify-phase1..3.log`: 11/17/23 check.)*

Tự kiểm:
- [x] Người khác đọc ghi chú của bạn hiểu được vì sao đổi hướng. *(ADR, assumptions, test-changes.)*
- [x] Không còn test bị tắt mà không có lý do. *(Đã ghi thay đổi test trong `phase-3-test-changes.md`.)*
- [ ] Đã gắn tag `phase-3` và push. *(Tag local `phase-3` đã có; remote **chưa có** tag này.)*

---

## Checkpoint 4: Phase 4 và phát hành (Ticket-04), 2h30 đến 4h

**Mục tiêu:** đưa sản phẩm đến mức phát hành được, đo được, cài đặt dễ.

Gợi ý:
- [ ] Đọc các yêu cầu có **số đo cụ thể** trong ticket. Với mỗi yêu cầu đo, chạy thật và lưu kết quả cùng cấu hình máy.
- [ ] Làm sạch README: người khác clone sạch, làm theo, chạy được trong tối đa 3 lệnh.
- [ ] Đảm bảo file bản quyền, ghi nguồn asset, giấy phép.
- [ ] Tạo bản phát hành chạy được (file thực thi, thư mục web tĩnh hoặc Docker) và GitHub Release `v1.0.0`.

Tự kiểm:
- [ ] Thử trên một thư mục sạch hoặc máy khác, không dùng cấu hình sẵn của bạn.
- [ ] Đã gắn tag `phase-4` và tạo Release `v1.0.0`.

---

## Checkpoint 5: Video demo và nộp bài (10 đến 15 phút cuối)

**Mục tiêu:** hoàn tất ghi chép, quay video, kiểm tra lần cuối, nộp.

- [ ] **Retro ngắn:** điều gì hiệu quả hoặc không khi làm với AI; những lần AI sai và cách bạn phát hiện; harness nào giúp nhiều nhất; token/chi phí ước tính và cách bạn tiết kiệm; nếu làm lại thì đổi gì.
- [ ] **Video demo `.mp4` dưới 5 phút**: chơi thử và cho thấy bằng chứng game chạy đúng. Đính kèm Release `v1.0.0` hoặc commit vào `docs/demo/demo.mp4` (dưới 100 MB). Đặt link ở đầu README.
- [ ] Rà soát repo: không có `.env`, API key, token. Lịch sử git còn đủ file harness.
- [ ] Rà soát bằng danh sách ở [SUBMISSION.md](SUBMISSION.md) mục "Checklist trước khi nộp".
- [ ] Nộp link repo public theo hướng dẫn của Coach.
