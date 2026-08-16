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
            
            # Chọn tab đang mở sẵn thay vì tạo thêm tab about:blank mới
            if context.pages:
                page = context.pages[-1]
            else:
                page = await context.new_page()
                
            await page.bring_to_front()
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
                await page.bring_to_front()
                print("[+] THÀNH CÔNG: Đã khởi chạy Chrome với Profile cá nhân!")
            except Exception as launch_err:
                print(f"[!] LỖI khi khởi chạy Chrome: {launch_err}")
                print(">>> LƯU Ý: Nếu Chrome đang mở bình thường, hãy đóng Chrome hoặc chạy file launch_chrome.bat trước!")
                return

        # Thực hiện chuyển hướng đến TARGET_URL (với fallback JS location.href)
        print(f"\n[*] Đang chuyển hướng đến trang web: {TARGET_URL}")
        try:
            await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=15000)
        except Exception as goto_err:
            print(f"[!] goto() không hoàn tất nhanh ({goto_err}), đang thử ép chuyển hướng qua JS...")

        # Ép chuyển hướng qua JavaScript nếu trang vẫn ở about:blank hoặc chrome://newtab/
        try:
            current_url = page.url
            if "pathofexile.com" not in current_url:
                print("[*] Thực thi JavaScript window.location.href để ép Chrome chuyển hướng...")
                await page.evaluate(f"window.location.href = '{TARGET_URL}'")
                await asyncio.sleep(2)
        except Exception as eval_err:
            print(f"[!] Cảnh báo JS redirect: {eval_err}")

        try:
            title = await page.title()
            url = page.url
            print(f"[+] Tiêu đề trang: {title}")
            print(f"[+] URL hiện tại  : {url}")
        except Exception:
            pass

        # Tìm kiếm nút "Travel to Hideout"
        print("\n[*] Đang tìm kiếm nút 'Travel to Hideout' (<button class=\"btn btn-xs btn-default direct-btn\">)...")
        selectors = [
            "button.direct-btn",
            "button:has-text('Travel to Hideout')",
            ".direct-btn"
        ]
        
        found = False
        for sel in selectors:
            try:
                await page.wait_for_selector(sel, timeout=10000)
                buttons = page.locator(sel)
                count = await buttons.count()
                if count > 0:
                    print(f"[+] ĐÃ TÌM THẤY {count} nút với selector '{sel}':")
                    for i in range(count):
                        btn = buttons.nth(i)
                        txt = await btn.inner_text()
                        visible = await btn.is_visible()
                        print(f"    - Nút #{i+1}: Text='{txt.strip()}', Hiển thị={visible}")
                    found = True
                    break
            except Exception:
                continue

        if not found:
            print("[-] Chưa tìm thấy nút 'Travel to Hideout' trong 10s (Có thể trang đang load danh sách kết quả, cần xác minh Cloudflare hoặc chưa có kết quả nào).")
        
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
