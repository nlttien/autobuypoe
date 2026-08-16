import asyncio
import os
import sys
import subprocess
import webbrowser
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
        
        # 1. Thử kết nối tới Chrome CDP đã mở sẵn (Port 9222)
        try:
            print(f"[*] Thử kết nối vào Chrome CDP tại {CDP_URL}...")
            browser = await p.chromium.connect_over_cdp(CDP_URL, timeout=3000)
            context = browser.contexts[0]
            print("[+] THÀNH CÔNG: Đã kết nối vào trình duyệt Chrome đang chạy qua CDP!")
        except Exception as e:
            print(f"[-] Chưa thể kết nối CDP trực tiếp ({e}).")
            print(f"[*] Tiến hành tự khởi chạy Chrome với URL mục tiêu...")
            
            # Tự mở Chrome với TARGET_URL được truyền thẳng vào arguments
            try:
                if os.name == 'nt' and os.path.exists(CHROME_PATH):
                    cmd = [
                        CHROME_PATH,
                        "--remote-debugging-port=9222",
                        f"--user-data-dir={USER_DATA_DIR}",
                        f"--profile-directory={PROFILE_NAME}",
                        "--remote-allow-origins=*",
                        TARGET_URL
                    ]
                    subprocess.Popen(cmd)
                    print("[+] Đã gọi Chrome hệ thống mở trực tiếp URL!")
                else:
                    webbrowser.open(TARGET_URL)
                    print("[+] Đã gọi trình duyệt mở URL hệ thống!")
                
                await asyncio.sleep(3)
                
                # Thử kết nối lại CDP sau khi Chrome khởi chạy
                try:
                    browser = await p.chromium.connect_over_cdp(CDP_URL, timeout=5000)
                    context = browser.contexts[0]
                except Exception:
                    pass
            except Exception as launch_err:
                print(f"[!] Lỗi khi mở Chrome: {launch_err}")

        # Lấy page hiện tại nếu có context
        if context:
            if context.pages:
                page = context.pages[-1]
            else:
                page = await context.new_page()
            
            try:
                await page.bring_to_front()
            except Exception:
                pass

            # Thực hiện chuyển hướng đến TARGET_URL nếu trang hiện tại chưa phải PoE Trade
            if "pathofexile.com" not in page.url:
                print(f"\n[*] Đang chuyển hướng đến trang web: {TARGET_URL}")
                try:
                    await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=15000)
                except Exception as goto_err:
                    print(f"[!] goto() không hoàn tất nhanh ({goto_err}), đang thử ép chuyển hướng qua JS...")

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
        if page:
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
