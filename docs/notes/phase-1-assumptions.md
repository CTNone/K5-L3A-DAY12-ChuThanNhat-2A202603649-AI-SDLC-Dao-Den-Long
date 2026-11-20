# Phase 1 — giả định và lựa chọn

## Công nghệ và cách chạy

- Python 3.10+ và thư viện chuẩn; chạy trên Windows/Linux/macOS bằng `python game.py` (GUI) hoặc `python game.py --headless` (không cửa sổ, không GPU, không phụ thuộc ngoài).
- Logic mô phỏng độc lập giao diện, bước cố định 60 Hz. GUI vẽ cảnh phối cảnh 3D cách điệu bằng Tkinter Canvas; trục gameplay vẫn là XZ, Y là độ cao. Camera theo sau Mây và xoay theo hướng camera.
- Đảo là đĩa tròn bán kính 35 m ở Y=0. Đi khỏi vành đảo gây sát thương rơi; điểm/va chạm đo trên XZ theo contract. Nhảy là chuyển động Y trang trí/gameplay, không thay đổi kiểm tra pickup hoặc va chạm ngang.
- Đom đóm và địch ban đầu: 30 đom đóm, 3 Bóng Mực; vị trí khởi tạo cố định theo seed. Scenario có thể thay thế hai danh sách này.
- Mỗi đèn cần 5 đom đóm; mang tối đa 5. Nhấn tương tác cạnh đèn chuyển toàn bộ số đang mang vào đèn (không vượt quá chi phí); nhấn cạnh đom đóm tự nhặt khi còn chỗ.
- Mây có 3 ngọn lửa (máu). Bóng Mực gây sát thương khi khoảng cách XZ ≤ 1 m; mỗi lần trúng mất 1 lửa và rơi một nửa số đom đóm đang mang (làm tròn xuống). Bất tử sau đòn đánh 2 giây.
- Xung sáng tiêu hao 1 đom đóm đang mang (tuning `pulse_cost`); nếu túi rỗng thì lệnh bị bỏ qua. Phạm vi 7 m, làm choáng 2 giây, đẩy lùi 2 m; hồi chiêu 3 giây. Mỗi đèn đã thắp tạo vùng an toàn bán kính 3 m mà Bóng Mực không thể đi vào.
- Bóng Mực chạy 2.5 m/s. Trời sáng sau 300 giây. Thắng khi cả 5 đèn sáng; thua khi hết lửa hoặc hết giờ.
- Điểm: +10 mỗi đom đóm nhặt, +100 mỗi đèn thắp, +25 mỗi Bóng Mực bị choáng, +1 mỗi giây còn lại khi thắng, +50 mỗi lửa còn khi thắng. Chỉ cộng điểm thời gian/lửa lúc thắng.
- Tạo hình không dùng asset ngoài: Mây đội nón lá, đèn lồng vàng cam; đảo xanh đêm và đom đóm phát sáng. Bóng Mực tím đen, không có máu me.

## Kiểm chứng và sáng tạo

- `game.contract.json` là nguồn thông số công khai cho test harness; các giá trị trên phải khớp logic thực tế.
- Kiểm tra headless nên bao gồm nhặt, nạp đèn, pulse, va chạm, kết thúc thắng/thua, scenario và tính tất định; mọi tọa độ snapshot làm tròn 3 chữ số.
- Ý sáng tạo nhỏ: ba đom đóm trang trí bay quanh mỗi đèn đã thắp. Đây chỉ là hiệu ứng vẽ, không thêm thực thể gameplay và không đổi headless output; bộ kiểm chứng lõi được chạy lại sau khi thêm.
