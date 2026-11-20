# Checklist bàn giao dự án cho OpenCode

## Mục tiêu

Cho OpenCode đọc và nắm dự án Đảo Đèn Lồng sau Phase 1. Chỉ kiểm tra, chưa triển khai Phase 2 cho đến khi chủ dự án gửi Ticket-02.

## Trước khi mở OpenCode

- [ ] Mở PowerShell tại thư mục dự án:
  `C:\Users\CTN_Number_ONE\Desktop\K5-L3A-DAY12-ChuThanNhat-2A202603649-AI-SDLC-Dao-Den-Long`
- [ ] Kiểm tra `opencode --version` chạy được.
- [ ] Mở OpenCode từ đúng thư mục dự án bằng lệnh `opencode`.
- [ ] Xác nhận OpenCode nhìn thấy bộ skill Awesome Gamedev Agent Skills đã cài.

## Prompt bàn giao để dán vào OpenCode

```text
Hãy tiếp quản dự án Đảo Đèn Lồng trong thư mục hiện tại ở chế độ kiểm tra, chưa sửa code.

1. Đọc lần lượt:
   - AGENTS.md
   - GUIDE.md
   - README.md
   - PRD-0.md
   - TEST-CONTRACT-v1.0.md
   - game.contract.json
   - checklist.md
   - SUBMISSION.md và các bằng chứng trong docs/proof/phase-1/

2. Kiểm tra trạng thái Git:
   - nhánh và commit hiện tại
   - tag phase-1 có tồn tại và trỏ tới commit nào
   - file đã sửa/chưa commit và file chưa được theo dõi
   Không xóa hoặc ghi đè file nào.

3. Dùng router của Awesome Gamedev Agent Skills để phân loại dự án và báo rõ:
   - Dự án này là Python/Tkinter, không phải Godot/Unity/pygame.
   - Hãy kiểm tra entry point và dependency trước khi gán engine.
   - Nếu router phân loại là custom/unsupported engine, hãy làm theo nhánh custom engine trong router; không giả vờ rằng có skill Python/Tkinter chuyên biệt và không nạp skill engine không liên quan.
   - Chỉ nạp tối đa 2–3 skill phù hợp với tác vụ kiểm tra hiện tại. Nêu tên skill và lý do trước khi dùng.
   - Với yêu cầu chỉ rà soát tài liệu/trạng thái, không cần nạp skill gameplay chỉ để cho đủ bộ. Nếu cần đánh giá gameplay tổng quát, cân nhắc game-ai, game-ui-ux hoặc platformer tùy phần việc; không mặc định nạp tất cả.

4. Đối chiếu checklist Phase 1 với code, contract và bằng chứng hiện có. Chia kết quả thành:
   - Đã hoàn thành và có bằng chứng trong repo.
   - Còn tôi cần tự làm (ví dụ tự chơi GUI hoặc kiểm tra máy macOS/Linux).
   - Còn thiếu hoặc chưa đủ bằng chứng.
   Không đánh dấu việc chỉ có ảnh hoặc lời mô tả là đã được bạn tự xác minh nếu chưa chạy/thấy trực tiếp.

5. Kiểm tra lệnh chạy GUI và headless trong README/contract, cùng các kiểm chứng Phase 1 đã có. Không cần chạy lại test nếu không cần để trả lời; nếu chạy lệnh nào thì ghi nguyên lệnh và kết quả thực tế.

6. Trả lời bằng báo cáo ngắn:
   - Kiến trúc và cách chạy.
   - Router phát hiện loại engine gì, skill nào đã nạp (nếu có).
   - Tình trạng Phase 1 theo ba nhóm ở mục 4.
   - Git/tag và các file còn dang dở.
   - Việc cụ thể tôi cần tự làm tiếp theo.

Không triển khai Phase 2, không thay đổi tuning hoặc đầu ra headless của Test Contract v1.0. Chờ tôi gửi Ticket-02 rồi mới bắt đầu sửa tính năng.
```

## Việc tôi cần làm sau khi OpenCode rà soát

- [ ] Đọc báo cáo, đối chiếu các lệnh và bằng chứng thay vì chỉ dựa vào kết luận của agent.
- [ ] Tự mở game GUI, thử điều khiển, nhặt đom đóm, nạp đèn, thắng/thua và chơi lại.
- [ ] Nếu có môi trường phù hợp, thử GUI trên macOS hoặc Linux.
- [ ] Gửi Ticket-02 khi sẵn sàng bắt đầu Phase 2.

## Ghi chú định tuyến skill

Dự án hiện dùng Python/Tkinter và có chế độ headless riêng. Danh mục skill có pygame, nhưng điều đó không có nghĩa dự án này dùng pygame. Router cần căn cứ entry point/dependency; khi engine không thuộc danh mục, dùng hướng dẫn custom/unsupported engine và chỉ ghép skill discipline liên quan đến đúng yêu cầu.
