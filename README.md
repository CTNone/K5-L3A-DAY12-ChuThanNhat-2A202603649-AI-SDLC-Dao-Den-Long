# Day 12 — AI SDLC: Đảo Đèn Lồng

## Demo v1.0.1

- Video: [docs/demo/demo.mp4](docs/demo/demo.mp4)
- Web build tự chạy: tải `dao-den-long-web-v1.0.1.zip` trong Release `v1.0.1`, giải nén,
  chạy `python serve_web.py` rồi mở URL in ra. Bản `v1.0.0` vẫn giữ trong Release để đối chiếu.
- Chạy từ mã nguồn: `python game.py --no-browser` nếu đã có `build/web` (hoặc `python game.py --build`).
- Docker: `docker build -t dao-den-long .` rồi `docker run --rm -p 8000:8000 dao-den-long`.
- Contract: `1.3`; headless, benchmark và soak đều chạy bằng Python chuẩn.

```bash
python3 tools/sync_shared.py --check
python3 tools/verify_phase1.py && python3 tools/verify_phase2.py && python3 tools/verify_phase3.py
python3 game.py --bench --bench-out bench.json
python3 game.py --soak --soak-out soak.json
python3 game.py
```

## Bản game Phase 4

Game dùng Python 3.10+ cho phần mô phỏng/headless và **Godot 4.7.2** cho GUI 3D thật. Trên Windows chạy bằng `python`; trên Linux/macOS dùng `python3`. Không cần Tkinter.

```bash
python3 tools/sync_shared.py
python3 tools/build_web.py
python3 game.py
```

Trên Windows thay `python3` bằng `python`. Lần đầu cần cài Godot 4.7.2 và export templates Web. `python game.py` tự phục vụ `build/web` và mở trình duyệt; thêm `--build` để build lại trước khi chạy. Điều khiển: WASD di chuyển, chuột xoay camera, Space nhảy/giữ để liệng, Shift lướt, E nhặt đóm/nạp dầu/thắp đèn, F xung sáng, Esc tạm dừng. Đèn mới tốn 10 đóm, thắp lại tốn 5, mỗi đóm nạp 10 dầu. Giữ đèn ít nhất 30 dầu để duy trì vùng an toàn; thắng khi bình minh đến và còn ít nhất 60% số đèn sáng.

Chạy contract headless (không cần Godot, cửa sổ hay GPU):

```bash
python3 game.py --headless --seed 7 --night 1 --ticks 600 --out out.jsonl
```

`game.contract.json` ghi lệnh và tuning. Chạy `python3 tools/verify_phase1.py`, `python3 tools/verify_phase2.py` và `python3 tools/verify_phase3.py` để tái lập các scenario kiểm tra; bảng bằng chứng Phase 1 ở [docs/proof/phase-1/README.md](docs/proof/phase-1/README.md), Phase 2 ở [docs/proof/phase-2](docs/proof/phase-2), Phase 3 ở [docs/proof/phase-3](docs/proof/phase-3). Ghi chú giả định và luật điểm: [docs/notes/phase-1-assumptions.md](docs/notes/phase-1-assumptions.md), [docs/notes/phase-2-assumptions.md](docs/notes/phase-2-assumptions.md), [docs/notes/phase-3-assumptions.md](docs/notes/phase-3-assumptions.md).

### Sáng tạo của tôi

GUI 3D có thêm đảo, đèn, đom đóm, bóng tối, tháp chuông, thanh dầu, cảnh báo dầu thấp và chế độ bảng màu dễ phân biệt. Đây chỉ là lớp trình bày, không thêm thực thể gameplay và không đổi contract output; bộ scenario headless vẫn đạt sau khi thêm hiệu ứng.

> **Cá nhân** (1 người / 1 MSSV) · Áp dụng SDLC cùng AI để xây một **game 3D** qua **4 phase**, từ yêu cầu ban đầu tới bản phát hành.
> **Lab board + trợ giảng:** **[Đảo Đèn Lồng Lab](https://claude.ai/artifact/Q1RYyv1dxjUczzCbd2ZnoW)**

---

## Tài liệu của lab

| File | Nội dung |
|---|---|
| [GUIDE.md](GUIDE.md) | Hướng dẫn làm lab: vòng làm việc mỗi phase, harness, kiểm chứng, token |
| [CHECKPOINTS.md](CHECKPOINTS.md) | Các mốc tự kiểm tra từ chuẩn bị đến nộp bài |
| [SUBMISSION.md](SUBMISSION.md) | Đặt tên repo, hạn nộp, tag, Release, video, checklist |
| [RULES.md](RULES.md) | Quy định: AI, trung thực về bằng chứng, bản quyền, bảo mật |
| [RUBRIC.md](RUBRIC.md) | Thang điểm chi tiết |

## Lab board

Yêu cầu dự án được phát hành tại **[Đảo Đèn Lồng Lab](https://claude.ai/artifact/Q1RYyv1dxjUczzCbd2ZnoW)**. Mỗi phase là một tab (tab chưa phát hành bị khóa), mỗi tab có trợ giảng AI riêng chỉ trả lời trong phạm vi phase đó. Trợ giảng cần đăng nhập claude.ai và dùng lượt Claude của bạn.

## Dự án

**Đảo Đèn Lồng**: game 3D góc nhìn thứ ba. Mây, người giữ đèn nhỏ tuổi, gom đom đóm để thắp lại các Đèn Lồng Lớn và né Bóng Mực trong sương đen.

- Không ràng buộc công nghệ; chạy được trên macOS hoặc Linux.
- Tuân theo **Test Contract** (chế độ headless) để được chấm tự động và so sánh với nhau.

| Phase | Bạn nhận | Nộp |
|---|---|---|
| 1 | **PRD-0** (mô tả tổng quát) + Test Contract | tag `phase-1` |
| 2 | **Ticket-02**, phát hành khi Phase 1 kết thúc | tag `phase-2` |
| 3 | **Ticket-03**, phát hành khi Phase 2 kết thúc | tag `phase-3` |
| 4 | **Ticket-04**, phát hành khi Phase 3 kết thúc | tag `phase-4` + Release `v1.0.0` |

Yêu cầu sẽ được bổ sung và có thể thay đổi giữa các phase, giống dự án thật.

### Lịch 4 giờ

Bài lab kéo dài **4 giờ**. Phase 1 và 2 khoảng **1 giờ**, Phase 3 khoảng **30 phút**, Phase 4 khoảng **1 giờ 30 phút**. Mỗi phase phát hành đúng mốc giờ. Phase mới xuất hiện trên lab board khi tới mốc.

| Mốc | Sự kiện | Hạn tag |
|---|---|---|
| 0h | Phát hành **Phase 1** (PRD-0), gồm cả phần chuẩn bị | `phase-1` trước mốc 1h |
| 1h | Phát hành **Phase 2** | `phase-2` trước mốc 2h |
| 2h | Phát hành **Phase 3** | `phase-3` trước mốc 2h30 |
| 2h30 | Phát hành **Phase 4** | `phase-4`, Release `v1.0.0` và video trước mốc 4h |
| 4h | Hết giờ lab, chốt bài | |

Hết giờ mỗi phase thì tag và chuyển sang phase tiếp theo, dù phase chưa hoàn hảo. Chỗ chưa xong ghi trung thực trong bằng chứng.

---

## Gợi ý SDLC (cách làm là của bạn)

Mỗi phase là một vòng nhỏ. Công cụ, thứ tự, định dạng tài liệu đều tự do; đây chỉ là gợi ý:

1. **Requirements:** biến yêu cầu thành tiêu chí nghiệm thu kiểm chứng được. Chỗ mơ hồ thì tự giả định và ghi lại.
2. **Plan:** nghĩ cách kiểm chứng **trước** khi để agent viết code.
3. **Build:** để agent viết, bạn điều phối và review.
4. **Verify:** chạy thật, kiểm tra hành vi thật. *Không có bằng chứng thì chưa xong*: "agent bảo chạy rồi" không phải bằng chứng.
5. **Evaluate:** cái gì đạt, AI sai ở đâu, harness (AGENTS.md, skill, hook) cần chỉnh gì.
6. **Release:** gắn tag.

## Ba điều cần nhớ

> Bạn được **tự do sáng tạo thêm** quanh phần lõi (nhân vật, cơ chế nhỏ, câu chuyện, hiệu ứng, âm thanh…). Sáng tạo gọn và không phá yêu cầu được tính điểm trong hạng mục F của [RUBRIC](RUBRIC.md); ghi mục "Sáng tạo của tôi" trong README của bạn.

- **Game tốt là game đúng yêu cầu của khách hàng**, không phải game phức tạp hay đẹp nhất. Làm đúng và chứng minh được là đúng trước, trau chuốt sau.
- **Cân nhắc kỹ quota token của bạn.** Đốt nhiều token không làm bài tốt hơn. Ngữ cảnh gọn, kế hoạch rõ, kiểm chứng sớm thường vừa rẻ vừa đúng hơn chạy agent liên tục.
- **Kiểm chứng là phần quan trọng nhất.** Bằng chứng (test, output headless, ảnh, số đo) đáng giá hơn lời mô tả.

---

## Phase 4 / v1.0.0 và bản vá v1.0.1

- **Artifact**: `v1.0.0` giữ nguyên bản đã nộp; `v1.0.1` là web zip tự chạy (kèm
  `serve_web.py` và `RUN.md`), Dockerfile dùng zip này.
- **Leaderboard**: lưu top 10 theo tên 3–12 ký tự, điểm rồi thời điểm; nhập tên sau khi
  thua hoặc thắng Đêm 3; admin không ghi điểm. CLI: `python3 game.py --export-leaderboard out.json`.
- **Benchmark/soak**: `bench.json` là 60 giây mô phỏng headless (200 shade, 100 mote);
  `soak.json` là 10 đêm trong một tiến trình, không input. Không có số đo GPU 3D.
- **Accessibility**: chữ tối thiểu 18 px, cỡ 125%, giảm chuyển động, đổi phím qua
  InputMap có phát hiện trùng phím, hướng nhân vật theo camera hoặc hướng di chuyển.
- **Audio**: audio chỉ phát sau thao tác người dùng (`audio.unlock()`), phù hợp chính
  sách autoplay của trình duyệt.
- **Admin**: checkbox luôn hiện; `Ctrl+Shift+1..6` bật/tắt cheat dev. Không phải bảo mật.
- Ghi chú: [spec](docs/notes/phase-4-spec.md), [giả định](docs/notes/phase-4-assumptions.md),
  [retro](docs/notes/phase-4-retro.md), [nhật ký AI](docs/notes/ai-usage-log.md).
- Bằng chứng: [phase-4](docs/proof/phase-4/README.md), [cấu hình máy](docs/proof/phase-4/machine.txt),
  [clone sạch](docs/proof/phase-4/clean-clone.log).

---

## Bàn giao cuối cùng

Một **repo GitHub cá nhân, public**, gồm:

1. **Toàn bộ mã nguồn** của game qua 4 phase, tag `phase-1` … `phase-4`, Release `v1.0.0` (bản vá `v1.0.1`).
2. **Video demo `.mp4` dưới 5 phút** (đính kèm Release `v1.0.0` hoặc `docs/demo/demo.mp4`, link ở đầu README): chơi thử và cho thấy bằng chứng game chạy đúng.
3. **Bằng chứng kiểm chứng** của từng phase (định dạng tự chọn).
4. **Harness AI đã dùng** (AGENTS.md / CLAUDE.md, skills, hooks, plugins…), giữ nguyên trong repo và lịch sử git.
5. **Ghi chép ngắn:** spec/giả định mỗi phase, nhật ký dùng AI (gồm token/chi phí ước tính), retro.

Không commit API key, token hay `.env`. Gửi link repo theo hướng dẫn của Coach.

## Đánh giá (100 điểm)

| Hạng mục | Điểm |
|---|---|
| Test tự động ẩn (headless, gồm kiểm tra lại phase trước) | 30 |
| Kiểm chứng & bằng chứng của bạn | 20 |
| Quy trình SDLC & harness AI | 15 |
| Evaluation & retro (gồm cách bạn dùng token) | 10 |
| Hiệu năng & ổn định | 10 |
| Chất lượng sản phẩm (đúng yêu cầu, chơi được) | 10 |
| Video demo | 5 |

## Quy định

- Dùng AI thoải mái; không sao chép repo của người khác.
- Bằng chứng phải thật: test luôn đạt hay output sửa tay là vi phạm.
- Nhân vật, bối cảnh là bản gốc của lab; asset bên ngoài chỉ dùng loại CC0/CC-BY/MIT hoặc tự tạo, ghi nguồn trong `CREDITS.md`.
