# AutoBuyPoE - Mở và Điều Khiển Chrome Profile trên Windows

Dự án Python giúp khởi tạo và kết nối tự động tới trình duyệt Google Chrome sử dụng chính Profile cá nhân trên Windows (giữ nguyên thông tin đăng nhập, cookie, session).

---

## 🚀 Hướng Dẫn Cài Đặt (trên Windows)

Mở **Command Prompt (cmd)** hoặc **PowerShell** tại thư mục dự án và chạy:

```cmd
pip install -r requirements.txt
python -m playwright install chromium
```

---

## 📖 Hướng Dẫn Sử Dụng

Có 2 cách để chạy dự án:

### Cách 1: Sử dụng `launch_chrome.bat` (Khuyên dùng)
Cách này giúp tránh lỗi "Profile in use" khi bạn đang mở sẵn Chrome.

1. Bấm đúp vào file **`launch_chrome.bat`** trên Windows.
   - File này sẽ mở Google Chrome với Profile mặc định của bạn và kích hoạt cổng Remote Debugging `9222`.
2. Chạy script Python để kết nối điều khiển:
   ```cmd
   python open_profile.py
   ```

---

### Cách 2: Tự động khởi chạy Chrome từ Python
Đảm bảo bạn đã đóng tất cả cửa sổ Chrome trên Windows trước khi chạy:

```cmd
python open_profile.py
```
*Script sẽ tự tìm Chrome và mở Profile của bạn.*

---

## ⚙️ Cấu Hình Nâng Cao (`config.py`)

Nếu Profile của bạn nằm ở vị trí khác hoặc bạn dùng Profile khác (`Profile 1`, `Profile 2`...):
- Mở file [config.py](file:///home/tien/code/autobuypoe/config.py) và chỉnh sửa các biến `PROFILE_NAME`, `USER_DATA_DIR` tương ứng.
