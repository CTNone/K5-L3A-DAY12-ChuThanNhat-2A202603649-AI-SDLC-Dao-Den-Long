# PRD-0 — Đảo Đèn Lồng

**Phase:** 1  
**Tag bàn giao:** `phase-1`  
**Thời lượng dự kiến:** khoảng 60 phút

Đây là mô tả đầu tiên từ khách hàng. Phần yêu cầu gameplay có chủ ý ở mức tổng quát; người thực hiện tự chọn công nghệ và ghi lại các giả định hợp lý. **Test Contract v1.0 là bắt buộc và chính xác**, nằm riêng trong [TEST-CONTRACT-v1.0.md](TEST-CONTRACT-v1.0.md).

## 1. Mục tiêu

Xây dựng game 3D tên **Đảo Đèn Lồng**. Người chơi điều khiển Mây, người giữ đèn nhỏ tuổi trên hòn đảo giữa biển mây. Đêm nay sương đen đã nuốt hết ánh sáng. Mây thu thập đom đóm, mang về thắp các Đèn Lồng Lớn và tránh Bóng Mực sống trong sương.

Bóng Mực đuổi theo Mây; khi chạm vào, chúng làm Mây mất lửa/máu. Mây có thể tỏa sáng để xua chúng nhưng hành động này tốn ánh sáng. Bóng Mực sợ những chiếc đèn. Thắp hết đèn thì thắng; mất hết lửa/máu thì thua. Game có điểm số.

## 2. Phạm vi Phase 1

- Một màn chơi: **Đêm 1 – Đảo Bến**, đảo tròn với 5 Đèn Lồng Lớn.
- Nhân vật có thể đi lại, nhảy; có camera 3D.
- Đom đóm xuất hiện rải rác trên đảo và có thể nhặt.
- Người chơi nạp ánh sáng vào đèn để thắp chúng.
- Bóng Mực xuất hiện và đuổi theo người chơi.
- Người chơi tỏa sáng để xua Bóng Mực.
- Có điều kiện thắng, thua, điểm số và HUD hiển thị thông tin cần thiết.
- Có thể chơi lại sau khi thắng hoặc thua.
- Có chế độ headless theo Test Contract v1.0.

## 3. Cảm giác và phong cách

- Không khí đêm, ấm áp, cổ tích.
- Đảo sáng dần lên khi các đèn được thắp.
- Ánh sáng vàng cam biểu thị điều tốt; tím đen biểu thị nguy hiểm.
- Đồ họa đơn giản nhưng đẹp; không cần chân thực.
- Mây đội nón lá và mang một chiếc đèn lồng nhỏ.
- Không bạo lực, không máu me.

## 4. Sáng tạo thêm

Có thể thêm nhân vật, loại Bóng Mực/đom đóm, cơ chế nhỏ, sự kiện, câu chuyện, hiệu ứng, âm thanh hoặc chi tiết đảo. Phần thêm không được phá yêu cầu PRD hay làm đổi output headless theo contract. Thực thể bổ sung có thể được tắt trong headless.

README cần có mục ngắn **“Sáng tạo của tôi”** nêu phần đã thêm và bằng chứng ngắn cho thấy phần lõi vẫn đúng. Ưu tiên hoàn tất và kiểm chứng phần lõi trước.

## 5. Công nghệ và nền tảng

Không bắt buộc engine, ngôn ngữ hay framework. Game phải chạy được trên macOS hoặc Linux. Nếu phát triển trên Windows, cần cung cấp cách chạy phù hợp cho người chấm, chẳng hạn Docker hoặc bản web.

## 6. Bàn giao Phase 1

- [ ] Repo GitHub cá nhân, public; có tag `phase-1`.
- [ ] Game chơi được Đêm 1 từ đầu đến thắng hoặc thua.
- [ ] `README.md` có cách cài đặt/chạy trong tối đa 3 lệnh, điều khiển và cách tính điểm.
- [ ] `game.contract.json` ở gốc repo và chế độ headless tuân theo [Test Contract v1.0](TEST-CONTRACT-v1.0.md).
- [ ] Có bằng chứng game chạy đúng yêu cầu.
- [ ] Có ghi chép ngắn về giả định và nhật ký sử dụng AI.
- [ ] Harness AI đã dùng (AGENTS.md hoặc tương đương, skills, hooks...) còn trong repo.

## 7. Nguyên tắc

- Đúng yêu cầu khách hàng quan trọng hơn độ phức tạp.
- Bằng chứng phải là kết quả chạy thật và khớp với mã ở tag tương ứng.
- Chỗ PRD chưa quy định thì tự chọn giả định hợp lý và ghi lại.
- Làm lõi đúng trước; sáng tạo thêm nhưng không làm hỏng gameplay hoặc Test Contract.
- Cân nhắc quota token; ghi ước tính token/chi phí và cách tiết kiệm.

