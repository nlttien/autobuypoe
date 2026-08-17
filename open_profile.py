import asyncio
import os
import sys
import subprocess
import webbrowser
from playwright.async_api import async_playwright
from config import CHROME_PATH, USER_DATA_DIR, PROFILE_NAME, CDP_URL, TARGET_URL, POE_EMAIL, POE_PASSWORD

async def handle_poe_login(page):
    """
    Xử lý kiểm tra màn hình Sign In và thực hiện các bước đăng nhập
    """
    try:
        # 1. Kiểm tra màn hình Sign In (nút <a class="splash__continue">CONTINUE</a>)
        continue_selector = "a.splash__continue, a[href*='/login'], a:has-text('Continue')"
        try:
            continue_btn = page.locator(continue_selector).first
            if await continue_btn.is_visible(timeout=5000):
                print("\n[!] PHÁT HIỆN MÀN HÌNH SIGN IN! Đang bấm nút 'CONTINUE'...")
                await continue_btn.click()
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(2)
        except Exception:
            pass
        
        # 2. Kiểm tra nếu đang ở trang Đăng nhập (/login)
        if "/login" in page.url:
            print("[*] Đang ở trang Đăng nhập (/login)...")
            
            email_input = page.locator("input#login_email, input[name='login_email'], input[type='email']").first
            password_input = page.locator("input#login_password, input[name='login_password'], input[type='password']").first
            submit_btn = page.locator("input#login_submit, button#login_submit, input[type='submit'][value*='Sign In'], button:has-text('Sign In')").first
            
            if await email_input.is_visible(timeout=5000) and await password_input.is_visible(timeout=5000):
                if POE_EMAIL and POE_PASSWORD:
                    print(f"[*] Tự động điền email '{POE_EMAIL}' và mật khẩu...")
                    await email_input.fill(POE_EMAIL)
                    await password_input.fill(POE_PASSWORD)
                    await asyncio.sleep(1)
                    
                    if await submit_btn.is_visible():
                        print("[*] Bấm nút 'Sign In'...")
                        await submit_btn.click()
                        print("[+] Đã gửi thông tin đăng nhập!")
                else:
                    print("[!] LƯU Ý: Chưa điền POE_EMAIL và POE_PASSWORD trong file config.py / .env.")
                    print("[*] Vui lòng tự nhập tài khoản và đăng nhập trên màn hình Chrome...")
                    
                # Chờ đăng nhập hoàn tất và quay về trang PoE Trade
                print("[*] Chờ hoàn tất đăng nhập...")
                try:
                    await page.wait_for_url(lambda u: "/login" not in u, timeout=60000)
                    print("[+] Đăng nhập thành công! Đã quay lại trang chính.")
                except Exception:
                    pass

    except Exception as err:
        print(f"[*] Kiểm tra đăng nhập kết thúc ({err}).")

async def main():
    async with async_playwright() as p:
        print("==================================================")
        print("   KẾT NỐI & ĐIỀU KHIỂN CHROME PROFILE WINDOWS    ")
        print("==================================================")
        
        browser = None
        context = None
        page = None
        
        # 1. Thử kết nối tới Chrome CDP đã mở sẵn (Port 9222)
        try:
            print(f"[*] Thử kết nối vào Chrome CDP tại {CDP_URL}...")
            browser = await p.chromium.connect_over_cdp(CDP_URL, timeout=2000)
            context = browser.contexts[0]
            print("[+] THÀNH CÔNG: Đã kết nối vào trình duyệt Chrome đang chạy qua CDP!")
        except Exception:
            print("[-] Chưa kết nối CDP trực tiếp. Tiến hành tự khởi chạy Chrome...")
            
            # Dọn dẹp các tiến trình Chrome cũ/treo nếu chạy trên Windows
            if os.name == 'nt':
                try:
                    subprocess.run(["taskkill", "/F", "/IM", "chrome.exe", "/T"], capture_output=True)
                    await asyncio.sleep(1)
                except Exception:
                    pass

            try:
                # Tự khởi chạy Chrome Profile trực tiếp qua Playwright
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=USER_DATA_DIR,
                    executable_path=CHROME_PATH if (os.path.exists(CHROME_PATH)) else None,
                    headless=False,
                    channel="chrome",
                    args=[
                        f"--profile-directory={PROFILE_NAME}",
                        "--remote-allow-origins=*",
                        "--disable-session-crashed-bubble",
                        "--disable-infobars",
                        "--hide-crash-restore-bubble",
                        "--restore-last-session=false"
                    ]
                )
                print("[+] THÀNH CÔNG: Đã khởi chạy Chrome với Profile cá nhân!")
            except Exception as launch_err:
                print(f"[!] Lỗi launch_persistent_context: {launch_err}")
                print("[*] Thử mở Chrome qua subprocess hệ thống...")
                try:
                    if os.name == 'nt' and os.path.exists(CHROME_PATH):
                        cmd = [
                            CHROME_PATH,
                            "--remote-debugging-port=9222",
                            f"--user-data-dir={USER_DATA_DIR}",
                            f"--profile-directory={PROFILE_NAME}",
                            "--remote-allow-origins=*",
                            "--disable-session-crashed-bubble",
                            "--disable-infobars",
                            "--hide-crash-restore-bubble",
                            "--restore-last-session=false",
                            TARGET_URL
                        ]
                        subprocess.Popen(cmd)
                    else:
                        webbrowser.open(TARGET_URL)
                    
                    await asyncio.sleep(3)
                    try:
                        browser = await p.chromium.connect_over_cdp(CDP_URL, timeout=8000)
                        context = browser.contexts[0]
                    except Exception:
                        pass
                except Exception:
                    pass

        # Thực thi điều hướng và thao tác lập tức
        if context:
            page = context.pages[0] if context.pages else await context.new_page()
            
            try:
                await page.bring_to_front()
            except Exception:
                pass

            # Chuyển hướng ngay lập tức đến TARGET_URL
            print(f"\n[*] Điều hướng đến trang web: {TARGET_URL}")
            try:
                await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)
            except Exception as goto_err:
                print(f"[!] Cảnh báo goto: {goto_err}")
                try:
                    await page.evaluate(f"window.location.href = '{TARGET_URL}'")
                except Exception:
                    pass

            try:
                print(f"[+] Tiêu đề trang: {await page.title()}")
                print(f"[+] URL hiện tại  : {page.url}")
            except Exception:
                pass

            # 1. Xử lý màn hình Sign In & các bước đăng nhập
            await handle_poe_login(page)

            # Đảm bảo trang quay về TARGET_URL nếu cần
            if "trade/search" in TARGET_URL and "trade/search" not in page.url:
                print(f"[*] Chuyển lại về URL tìm kiếm: {TARGET_URL}")
                try:
                    await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)
                except Exception:
                    pass

            # 2. Tìm kiếm nút "Travel to Hideout"
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
                print("[-] Chưa tìm thấy nút 'Travel to Hideout' (Vui lòng kiểm tra xem kết quả tìm kiếm đã hiển thị trên trang chưa).")
        
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
