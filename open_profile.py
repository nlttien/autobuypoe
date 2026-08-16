import asyncio
import sys
from playwright.async_api import async_playwright
from config import CHROME_PATH, USER_DATA_DIR, PROFILE_NAME, CDP_URL, TARGET_URL

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
        print(f"\n[*] Đang điều hướng đến trang: {TARGET_URL}")
        await page.goto(TARGET_URL, timeout=60000)
        
        title = await page.title()
        url = page.url
        print(f"[+] Tiêu đề trang: {title}")
        print(f"[+] URL hiện tại  : {url}")
        
        # Đợi danh sách kết quả hoặc nút "Travel to Hideout" tải xong
        print("\n[*] Đang tìm kiếm nút 'Travel to Hideout' (<button class=\"btn btn-xs btn-default direct-btn\">)...")
        try:
            # Selector nhắm chính xác nút Direct Buy / Travel to Hideout
            selector = "button.direct-btn"
            
            # Chờ ít nhất 1 nút xuất hiện (timeout 15 giây)
            await page.wait_for_selector(selector, timeout=15000)
            
            buttons = page.locator(selector)
            count = await buttons.count()
            print(f"[+] ĐÃ TÌM THẤY {count} nút 'Travel to Hideout' trên trang!")
            
            for i in range(count):
                btn = buttons.nth(i)
                btn_text = await btn.inner_text()
                is_visible = await btn.is_visible()
                print(f"    - Nút #{i + 1}: Text='{btn_text.strip()}', Hiển thị={is_visible}")
                
        except Exception as err:
            print(f"[-] Không tìm thấy nút 'Travel to Hideout' trong 15s ({err}).")
            print("[!] Mẹo: Hãy kiểm tra xem trang có đang bắt xác minh Cloudflare, cần đăng nhập hoặc kết quả chưa tải hết.")
        
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
