import os
from dotenv import load_dotenv

load_dotenv()

# Cấu hình đường dẫn Chrome và User Data trên Windows
WIN_USER = os.getenv("USERNAME", "tien")

# Đường dẫn file thực thi Chrome trên Windows
CHROME_PATH = os.getenv(
    "CHROME_PATH",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe"
)

# Đường dẫn thư mục User Data của Chrome trên Windows
USER_DATA_DIR = os.getenv(
    "USER_DATA_DIR",
    rf"C:\Users\{WIN_USER}\AppData\Local\Google\Chrome\User Data"
)

# Tên Profile muốn sử dụng ("Default", "Profile 1", "Profile 2", ...)
PROFILE_NAME = os.getenv("PROFILE_NAME", "Default")

# URL Remote Debugging CDP
CDP_URL = os.getenv("CDP_URL", "http://127.0.0.1:9222")

# URL mục tiêu cần mở và thao tác
TARGET_URL = os.getenv(
    "TARGET_URL",
    "https://www.pathofexile.com/trade/search/Allflame/rPaWLegmCQ"
)

# Cấu hình tài khoản đăng nhập PoE (nếu muốn tự động điền)
POE_EMAIL = os.getenv("POE_EMAIL", "brendagruener42190@hotmail.com")
POE_PASSWORD = os.getenv("POE_PASSWORD", "Gege@999")


