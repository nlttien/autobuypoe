import asyncio
import sys
from playwright.async_api import async_playwright
from config import CHROME_PATH, USER_DATA_DIR, PROFILE_NAME, CDP_URL

async def main():
    async with async_playwright() as p:
        print("==================================================")
        print("   KẾT NỐI & ĐIỀU KHIỂN CHROME PROFILE WINDOWS    ")
        print("==================================================")
        
        browser = None
        context = None
        page = None
        
        # Phương án 1: Thử kết nối tới Chrome đã mở sẵn với Port 9222 (CDP)
        try:
            print(f"[*] Thử kết nối vào Chrome CDP tại {CDP_URL}...")
            browser = await p.chromium.connect_over_cdp(CDP_URL)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            print("[+] THÀNH CÔNG: Đã kết nối vào trình duyệt Chrome đang chạy!")
        except Exception as e:
            print(f"[-] Không thể kết nối CDP ({e}).")
            print(f"[*] Tiến hành tự khởi chạy Chrome Profile trực tiếp...")
            
            try:
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=USER_DATA_DIR,
                    executable_path=CHROME_PATH,
                    headless=False,
                    channel="chrome",
                    args=[
                        f"--profile-directory={PROFILE_NAME}",
                        "--remote-allow-origins=*"
                    ]
                )
                page = context.pages[0] if context.pages else await context.new_page()
                print("[+] THÀNH CÔNG: Đã khởi chạy Chrome với Profile cá nhân!")
            except Exception as launch_err:
                print(f"[!] LỖI khi khởi chạy Chrome: {launch_err}")
                print(">>> LƯU Ý: Nếu Chrome đang mở bình thường, hãy đóng Chrome hoặc chạy file launch_chrome.bat trước!")
                return

        # Thử điều khiển trình duyệt
        print("\n[*] Đang điều hướng đến trang Path of Exile...")
        await page.goto("https://www.pathofexile.com", timeout=60000)
        
        title = await page.title()
        url = page.url
        print(f"[+] Tiêu đề trang: {title}")
        print(f"[+] URL hiện tại  : {url}")
        
        print("\n[i] Nhấn Ctrl+C để kết thúc script (Trình duyệt sẽ giữ nguyên trạng thái).")
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n[*] Đã kết thúc script.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
