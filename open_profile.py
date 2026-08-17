import asyncio
import os
import sys
import subprocess
import webbrowser
from playwright.async_api import async_playwright
from config import CHROME_PATH, USER_DATA_DIR, PROFILE_NAME, CDP_URL, TARGET_URL, POE_EMAIL, POE_PASSWORD

async def handle_cloudflare(page):
    """
    Tự động phát hiện và hỗ trợ xử lý màn hình Cloudflare Verify ('Just a moment...')
    """
    try:
        title = await page.title()
        if "Just a moment" in title or "cf_chl_rt_tk" in page.url:
            print("\n[!] PHÁT HIỆN MÀN HÌNH VERIFY CLOUDFLARE ('Verify you are human')!")
            print("[*] Đang thử tự động click ô xác minh Turnstile...")
            
            for check_attempt in range(1, 8):
                # Duyệt qua các frame tìm checkbox Turnstile
                for frame in page.frames:
                    if "cloudflare" in frame.url or "challenges" in frame.url or "turnstile" in frame.url:
                        try:
                            cb = frame.locator("input[type='checkbox'], .mark, #challenge-stage, span.mark").first
                            if await cb.is_visible(timeout=2000):
                                print("[+] Đã tìm thấy ô checkbox Verify! Đang click...")
                                await cb.click(force=True)
                                await asyncio.sleep(3)
                                break
                        except Exception:
                            pass
                
                await asyncio.sleep(2)
                title_now = await page.title()
                if "Just a moment" not in title_now:
                    print("[+] VƯỢT QUA CLOUDFLARE THÀNH CÔNG!")
                    return True
            
            # Nếu Cloudflare yêu cầu tương tác thủ công
            print("[!] LƯU Ý: Vui lòng tích vào ô 'Verify you are human' trên cửa sổ Chrome...")
            print("[*] Script đang chờ bạn vượt qua Cloudflare...")
            try:
                await page.wait_for_url(lambda u: "cf_chl_rt_tk" not in u and "Just a moment" not in page.url, timeout=120000)
                print("[+] Đã nhận diện vượt qua Cloudflare!")
            except Exception:
                pass
    except Exception as cf_err:
        print(f"[*] Kiểm tra Cloudflare hoàn tất ({cf_err}).")

async def handle_poe_login(page):
    """
    Xử lý kiểm tra màn hình Sign In và thực hiện các bước đăng nhập bằng JS DOM Native Click
    """
    try:
        # 0. Kiểm tra xem đã ở sẵn giao diện trang Trade (đã đăng nhập sẵn) chưa
        is_already_trade = await page.evaluate("""
            () => {
                const btns = document.querySelectorAll('button.direct-btn, .direct-btn');
                const results = document.querySelector('.results, .search-results');
                return (btns && btns.length > 0) || (results !== null);
            }
        """)
        if is_already_trade:
            print("\n[+] PHÁT HIỆN ĐÃ VÀO THẲNG TRANG TRADE! (Đã đăng nhập sẵn).")
            return

        # Chờ cho đến khi khung Sign In (.splash) hoặc kết quả tìm kiếm được render lên DOM
        print("\n[*] Đang chờ trang PoE Trade và khung Sign In tải xong toàn bộ DOM...")
        try:
            await page.wait_for_selector("a.splash__continue, .splash, button.direct-btn, .results", timeout=15000)
            await asyncio.sleep(1.5)
        except Exception:
            pass

        # 1. Kiểm tra màn hình Sign In (nút <a class="splash__continue">CONTINUE</a>)
        print("[*] Đang kiểm tra màn hình Sign In (nút CONTINUE)...")
        clicked_continue = False
        
        for attempt in range(1, 10):
            # Thử click bằng Native JavaScript DOM (Bỏ qua hoàn toàn Infobar/Overlay/Google Translate)
            js_click_result = await page.evaluate("""
                () => {
                    const btn = document.querySelector('a.splash__continue') || 
                                document.querySelector("a[href*='/login']") || 
                                Array.from(document.querySelectorAll('a')).find(el => el.textContent.trim().toUpperCase().includes('CONTINUE'));
                    if (btn) {
                        btn.click();
                        return true;
                    }
                    return false;
                }
            """)
            
            if js_click_result:
                print(f"[+] [Lần {attempt}] ĐÃ CLICK THÀNH CÔNG NÚT 'CONTINUE' qua Native JavaScript!")
                clicked_continue = True
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(3)
                break
            else:
                await asyncio.sleep(1.5)

        if not clicked_continue:
            print("[-] Không thấy nút 'CONTINUE' hoặc trang đã ở trạng thái khác.")

        # 2. Kiểm tra nếu đang ở trang Đăng nhập (/login)
        if "/login" in page.url or "redir=" in page.url:
            print("[*] Đang ở trang Đăng nhập (/login)...")
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(1.5)
            
            # 2a. Click nút tùy chọn Email nếu có (VD: nút 'Email', 'Sign in with Email', ...)
            print("[*] Kiểm tra nút chọn Đăng nhập bằng Email...")
            try:
                clicked_email_tab = await page.evaluate("""
                    () => {
                        const emailBtn = document.querySelector('a.btn-email') || 
                                         document.querySelector('button.btn-email') || 
                                         document.querySelector("a[href*='email']") || 
                                         Array.from(document.querySelectorAll('a, button, div, span')).find(el => {
                                             const txt = el.textContent ? el.textContent.trim().toLowerCase() : '';
                                             return txt === 'email' || txt.includes('sign in with email') || txt.includes('đăng nhập bằng email');
                                         });
                        if (emailBtn) {
                            emailBtn.click();
                            return true;
                        }
                        return false;
                    }
                """)
                if clicked_email_tab:
                    print("[+] ĐÃ CLICK NÚT TÙY CHỌN EMAIL!")
                    await asyncio.sleep(1.5)
            except Exception as e_btn:
                print(f"[*] Cảnh báo click nút Email: {e_btn}")

            # 2b. Chờ 2 ô nhập email và password hiển thị
            try:
                await page.wait_for_selector("input#login_email, input[name='login_email'], input[type='email'], input[name='email']", timeout=10000)
            except Exception:
                pass

            email_input = page.locator("input#login_email, input[name='login_email'], input[type='email'], input[name='email']").first
            password_input = page.locator("input#login_password, input[name='login_password'], input[type='password'], input[name='password']").first
            
            if await email_input.is_visible(timeout=5000) or await password_input.is_visible(timeout=5000):
                if POE_EMAIL and POE_PASSWORD:
                    print(f"[*] Tự động điền email '{POE_EMAIL}' và mật khẩu...")
                    try:
                        await email_input.fill(POE_EMAIL)
                        await password_input.fill(POE_PASSWORD)
                    except Exception:
                        await page.evaluate(f"""
                            () => {{
                                const email = document.querySelector('input#login_email, input[name="login_email"], input[type="email"], input[name="email"]');
                                const pass = document.querySelector('input#login_password, input[name="login_password"], input[type="password"], input[name="password"]');
                                if (email) email.value = "{POE_EMAIL}";
                                if (pass) pass.value = "{POE_PASSWORD}";
                            }}
                        """)
                    # 2c. Chờ Captcha Cloudflare Turnstile xác minh xong (dấu tích xanh / 'Success!')
                    print("[*] Đang chờ Captcha Cloudflare xác minh xong (tích xanh 'Success!')...")
                    captcha_passed = False
                    for captcha_attempt in range(1, 20):
                        # Kiểm tra token response trong DOM
                        token_ok = await page.evaluate("""
                            () => {
                                const resp = document.querySelector('input[name="cf-turnstile-response"], input[name="g-recaptcha-response"]');
                                if (resp && resp.value && resp.value.length > 5) return true;
                                return false;
                            }
                        """)
                        if token_ok:
                            captcha_passed = True
                            break
                        
                        # Kiểm tra trạng thái trong các iframe Turnstile
                        for frame in page.frames:
                            if "cloudflare" in frame.url or "challenges" in frame.url or "turnstile" in frame.url:
                                try:
                                    success_el = frame.locator("text='Success!', .success, #success, [data-state='success']").first
                                    if await success_el.is_visible(timeout=1000):
                                        captcha_passed = True
                                        break
                                except Exception:
                                    pass
                        if captcha_passed:
                            break
                        
                        # Hỗ trợ click ô checkbox nếu chưa tích
                        await handle_cloudflare(page)
                        await asyncio.sleep(1.5)

                    if captcha_passed:
                        print("[+] CAPTCHA ĐÃ XÁC MINH THÀNH CÔNG (TÍCH XANH 'Success!')!")
                    else:
                        print("[!] LƯU Ý: Vui lòng tích vào ô Captcha trên màn hình Chrome...")
                        await asyncio.sleep(3)
                    
                    # Bấm Sign In qua Native JavaScript
                    print("[*] Bấm nút 'Sign In'...")
                    await page.evaluate("""
                        () => {
                            const btn = document.querySelector('input#login_submit') || 
                                        document.querySelector('button#login_submit') || 
                                        document.querySelector("input[type='submit']") || 
                                        Array.from(document.querySelectorAll('button, input')).find(el => {
                                            const txt = (el.value || el.textContent || '').trim().toUpperCase();
                                            return txt.includes('SIGN IN') || txt.includes('DANG NHAP');
                                        });
                            if (btn) btn.click();
                        }
                    """)
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
        
        # Khởi chạy Chrome với AutomationProfile riêng biệt
        try:
            print(f"[*] Khởi chạy Chrome với Profile tự động hóa ({USER_DATA_DIR})...")
            context = await p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                executable_path=CHROME_PATH if (os.path.exists(CHROME_PATH)) else None,
                headless=False,
                channel="chrome",
                no_viewport=True,
                args=[
                    "--remote-allow-origins=*",
                    "--disable-session-crashed-bubble",
                    "--disable-infobars",
                    "--hide-crash-restore-bubble",
                    "--restore-last-session=false",
                    "--disable-blink-features=AutomationControlled"
                ]
            )
            print("[+] THÀNH CÔNG: Đã mở Chrome với Profile tự động hóa!")
        except Exception as launch_err:
            print(f"[-] Không thể gọi launch_persistent_context ({launch_err}). Thử kết nối CDP...")
            try:
                browser = await p.chromium.connect_over_cdp(CDP_URL, timeout=3000)
                context = browser.contexts[0]
                print("[+] THÀNH CÔNG: Đã kết nối vào Chrome CDP!")
            except Exception as cdp_err:
                print(f"[!] Kết nối CDP thất bại: {cdp_err}")

        # Stealth Mode: Ẩn navigator.webdriver
        if context:
            try:
                await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            except Exception:
                pass

        # Thực thi điều hướng và thao tác lập tức
        if context:
            # Ưu tiên chọn tab đang mở trang Path of Exile
            page = None
            for p_item in context.pages:
                if "pathofexile.com" in p_item.url:
                    page = p_item
                    break

            if not page:
                page = context.pages[-1] if context.pages else await context.new_page()
            
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

            # 0. Kiểm tra & xử lý Cloudflare Verify
            await handle_cloudflare(page)

            # 1. Xử lý màn hình Sign In & các bước đăng nhập
            await handle_poe_login(page)

            # Đảm bảo trang quay về TARGET_URL nếu cần
            if "trade/search" in TARGET_URL and "trade/search" not in page.url:
                print(f"[*] Chuyển lại về URL tìm kiếm: {TARGET_URL}")
                try:
                    await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)
                except Exception:
                    pass

            # 2. Tìm kiếm và click vào nút "Travel to Hideout" thứ 3
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
                        
                        # Click vào nút thứ 3 (Index 2)
                        target_index = 2
                        if count >= 3:
                            target_btn = buttons.nth(target_index)
                            txt_3 = await target_btn.inner_text()
                            print(f"\n[!] THỰC HIỆN CLICK NÚT 'Travel to Hideout' THỨ 3 (Nút #3: '{txt_3.strip()}')...")
                            try:
                                await target_btn.click(force=True)
                                print("[+] ĐÃ CLICK NÚT THỨ 3 THÀNH CÔNG qua Playwright!")
                            except Exception as click_err:
                                print(f"[*] Bấm Playwright báo: {click_err}, đang thử click qua Native JS...")
                                await page.evaluate(f"""
                                    (idx) => {{
                                        const btns = document.querySelectorAll('{sel}');
                                        if (btns && btns[idx]) {{
                                            btns[idx].click();
                                        }}
                                    }}
                                """, target_index)
                                print("[+] ĐÃ CLICK NÚT THỨ 3 THÀNH CÔNG qua Native JS!")
                        else:
                            print(f"\n[!] Trang chỉ tìm thấy {count} nút. Đang bấm nút có sẵn vị trí #{count}...")
                            target_btn = buttons.nth(count - 1)
                            await target_btn.click(force=True)
                            print(f"[+] Đã click nút vị trí #{count} thành công!")

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
