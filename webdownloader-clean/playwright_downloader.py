import os
import re
import sys
import time
import random
import base64
import mimetypes
import warnings
import requests
import traceback
import ctypes
from urllib.parse import urljoin

warnings.filterwarnings('ignore', message='Unverified HTTPS request')

mimetypes.init()

def set_window_bottom(hwnd):
    try:
        HWND_BOTTOM = 1
        SWP_NOSIZE = 0x0001
        SWP_NOMOVE = 0x0002
        SWP_NOACTIVATE = 0x0010
        ctypes.windll.user32.SetWindowPos(hwnd, HWND_BOTTOM, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE)
    except:
        pass

def set_window_top(hwnd):
    try:
        HWND_TOP = 0
        SWP_NOSIZE = 0x0001
        SWP_NOMOVE = 0x0002
        SWP_SHOWWINDOW = 0x0040
        ctypes.windll.user32.SetWindowPos(hwnd, HWND_TOP, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE | SWP_SHOWWINDOW)
        ctypes.windll.user32.SetForegroundWindow(hwnd)
    except:
        pass

def get_browser_hwnd():
    try:
        import subprocess
        result = subprocess.run(['powershell', '-Command', 
            f'Get-Process | Where-Object {{$_.MainWindowTitle -ne "" -and ($_.ProcessName -like "*chrome*" -or $_.ProcessName -like "*msedge*" -or $_.ProcessName -like "*chromium*")}} | Select-Object -First 1 -ExpandProperty MainWindowHandle'],
            capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.strip())
    except:
        pass
    return None

def save_crash_log_pw(module_name, error_info, context=None):
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logs_dir = os.path.join(base_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        import datetime
        current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        crash_file = os.path.join(logs_dir, f"crash_{current_time}.log")
        
        with open(crash_file, "w", encoding="utf-8") as f:
            f.write(f"=== CRASH LOG ===\n")
            f.write(f"时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"模块: {module_name}\n")
            f.write(f"\n=== 错误信息 ===\n")
            f.write(str(error_info))
            f.write(f"\n\n=== 上下文 ===\n")
            if context:
                f.write(str(context))
            else:
                f.write("无")
        return crash_file
    except:
        return None

class PlaywrightDownloader:
    POPUP_SELECTORS = [
        '.Modal-wrapper', '.Modal-inner', '.SignFlow', '.LoginContainer',
        '.passport-login-container', '.passport-login-mark',
        '[class*="passport-login"]', '[class*="login-modal"]',
        '[class*="sign-flow"]', '[class*="Login"]',
        '[class*="popup"]', '[class*="Popup"]', '[class*="overlay"]',
        '[class*="backdrop"]', '[class*="mask"]',
        '.css-1ynzxqw', '.SignFlowHomepage',
        '.Modal-backdrop', '.Login-modal',
        '.css-1f2yvkb', '.css-1v0td5a',
        '[class*="Modal"]', '[class*="modal"]',
        '.zopim', '.linkechat'
    ]
    
    GDPR_BUTTON_SELECTORS = [
        'button:has-text("Consent")',
        'button:has-text("Accept")',
        'button:has-text("Accept All")',
        'button:has-text("I Accept")',
        'button:has-text("同意")',
        'button:has-text("接受")',
        'button:has-text("Agree")',
        'button:has-text("OK")',
        'button:has-text("Allow All")',
        'button:has-text("登录")',
        'button:has-text("立即登录")',
        '[class*="consent"] button',
        '[class*="Consent"] button',
        '[class*="gdpr"] button',
        '[class*="GDPR"] button',
        '[id*="consent"] button',
        '[id*="gdpr"] button',
        '.cc-btn', '.cc-allow',
        '#onetrust-accept-btn-handler',
        '.accept-cookies',
        '[data-testid="accept-cookies"]',
        '[aria-label*="accept"]',
        '[aria-label*="Accept"]',
        '.Modal-closeButton',
        'button[aria-label="关闭"]',
        '.css-1f2yvkb'
    ]
    
    REMOVE_SELECTORS = [
        '.Modal-wrapper', '.Modal-inner', '.SignFlow', '.LoginContainer',
        '.passport-login-container', '.passport-login-mark',
        '[class*="passport-login"]', '[class*="login-modal"]',
        'noscript',
        '[class*="gdpr"]', '[class*="GDPR"]', '[class*="consent"]',
        '[class*="Consent"]', '[class*="cookie-consent"]',
        '[class*="privacy"]', '[class*="Privacy"]',
        '[id*="gdpr"]', '[id*="GDPR"]', '[id*="consent"]',
        '[id*="cookie"]', '[id*="privacy"]',
        '.cc-banner', '.cc-window', '.cc-revoke',
        '.css-1ynzxqw', '.SignFlowHomepage', '.css-1f2yvkb',
        '.Modal-backdrop', '.Login-modal',
        '[class*="Modal"]', '[class*="modal"]',
        '[class*="sign-flow"]', '[class*="SignFlow"]',
        '[class*="Login"]', '[class*="login"]',
        '.Pc-card', '.Pc-word-card', '.GlobalSideBar', '.Sticky',
        '.Question-sideColumn', '.QuestionHeader-Comment',
        '.CornerButton', '.CornerAnimayedFlex',
        '[class*="ad-"]', '[class*="ads-"]', '[class*="advert"]',
        '.zopim', '.linkechat',
        '#onetrust-banner-sdk', '.onetrust-pc-dark-filter',
        '[data-testid="cookie-policy"]', '[data-testid="gdpr"]',
        '.truste_box_overlay', '.truste_overlay',
        '#_evidon_banner', '#_evidon-option-button',
        '.qc-cmp-ui-container', '#qc-cmp2-ui',
        '[class*="trustarc"]', '[class*="TrustArc"]',
        'div[class*="overlay"][class*="modal"]',
        'div[role="dialog"][aria-label*="cookie"]',
        'div[role="dialog"][aria-label*="privacy"]',
        'div[role="dialog"][aria-label*="consent"]',
        '.ContentItem-actions', '.RichContent-actions'
    ]
    
    EVENT_ATTRS = [
        'onerror', 'onload', 'onclick', 'onmouseover', 'onmouseout',
        'onmouseenter', 'onmouseleave', 'onfocus', 'onblur', 'onchange',
        'onsubmit', 'onkeydown', 'onkeyup', 'onkeypress', 'ondblclick',
        'ontouchstart', 'ontouchend', 'ontouchmove', 'oncontextmenu'
    ]
    
    INJECT_CSS = '''
html, body {
    -webkit-user-select: text !important;
    -moz-user-select: text !important;
    -ms-user-select: text !important;
    user-select: text !important;
}
div, p, span, h1, h2, h3, h4, h5, h6, article, section, main, pre, code, td, th, li {
    -webkit-user-select: text !important;
    -moz-user-select: text !important;
    -ms-user-select: text !important;
    user-select: text !important;
}
.container-download, .container-fluid-flex,
[class*="ad-"], [class*="ads-"], [class*="advert"],
[class*="banner"], [id*="ad-"], [id*="ads-"],
.recommend-box, .recommend-list,
.comment-box, .comment-list,
.tool-box, .toolbox,
.article-bar-bottom, .right-side,
.csdn-side-toolbar, .side-toolbar,
.passport-login-container, .passport-login-mark,
.login-mark, .login-box, .tool-middle-box,
.recommend-right, .blog-aside, aside,
.csdn-toolbar, .toolbar-inside,
.blog-footer-bottom, .footer-box,
#csdn-toolbar, .passport-login-tip-container,
[class*="gdpr"], [class*="GDPR"], [class*="consent"],
[class*="Consent"], [class*="cookie-consent"],
[class*="privacy"], [class*="Privacy"],
[id*="gdpr"], [id*="GDPR"], [id*="consent"],
[id*="cookie"], [id*="privacy"],
.cc-banner, .cc-window, .cc-revoke,
#onetrust-banner-sdk, .onetrust-pc-dark-filter,
.truste_box_overlay, .truste_overlay,
.qc-cmp-ui-container, #qc-cmp2-ui,
[class*="trustarc"], [class*="TrustArc"],
.css-1ynzxqw, .SignFlowHomepage,
.SignFlow-content, .SignFlow-inner,
[class*="SignFlow"], [class*="sign-flow"],
.Login-content, [class*="Login-content"],
.css-1f2yvkb, .css-1v0td5a,
.css-1h4afuj, .css-1qyijqe,
.css-1a5y2hb, .css-1vqeg4f,
.Question-mainColumnLogin,
.Card.LoginCard,
.LoginPrompt,
[class*="LoginPrompt"],
[class*="login-prompt"],
.Button.SignFlow-submitButton {
    display: none !important;
}
'''

    BLOCK_SCRIPT = '''
(function() {
    try {
        window.open = function(){ return null; };
        window.location.__proto__.replace = function(){};
    } catch(e) {}
})();
'''

    def __init__(self, gui=None, log_callback=None, browser_type="auto"):
        self.gui = gui
        self.log_callback = log_callback
        self.browser = None
        self.context = None
        self.connected = False
        self.debug_port = 9222
        self.p = None
        self.browser_type = browser_type
        
        self.user_data_dir = os.path.join(os.path.dirname(__file__), 'browser_data')
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        })
        adapter = requests.adapters.HTTPAdapter(max_retries=3, pool_connections=10, pool_maxsize=20)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def log(self, msg, tag="info"):
        try:
            if self.log_callback:
                self.log_callback(msg, tag)
            elif self.gui and hasattr(self.gui, 'literature_log'):
                self.gui.root.after(0, lambda: self.gui.literature_log(msg, tag))
            else:
                print(f"[{tag}] {msg}")
        except:
            print(f"[{tag}] {msg}")
    
    def log_update(self, msg, tag="info"):
        try:
            if self.gui and hasattr(self.gui, 'literature_log_update'):
                self.gui.root.after(0, lambda: self.gui.literature_log_update(msg, tag))
            else:
                print(f"[{tag}] {msg}")
        except:
            print(f"[{tag}] {msg}")

    def _show_page_action_dialog(self, url, is_security_check=False):
        import tkinter as tk
        from tkinter import ttk
        
        result = {'choice': None}
        
        def on_skip():
            result['choice'] = 'skip'
            dialog.destroy()
        
        def on_done():
            result['choice'] = 'done'
            dialog.destroy()
        
        try:
            dialog = tk.Toplevel()
            dialog.title("需要您的操作")
            dialog.geometry("420x200")
            dialog.resizable(False, False)
            dialog.transient()
            dialog.grab_set()
            
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() - 420) // 2
            y = (dialog.winfo_screenheight() - 200) // 2
            dialog.geometry(f"+{x}+{y}")
            
            main_frame = ttk.Frame(dialog, padding=20)
            main_frame.pack(fill="both", expand=True)
            
            if is_security_check:
                title_text = "🔐 检测到安全验证"
                msg_text = "该页面需要完成安全验证。\n请在浏览器中手动完成验证后，点击「完成操作」继续下载。"
            else:
                title_text = "⏳ 页面加载超时"
                msg_text = "页面加载时间较长，可能需要您的操作。\n请在浏览器中检查页面状态后，选择继续或跳过。"
            
            ttk.Label(main_frame, text=title_text, font=("Microsoft YaHei", 12, "bold")).pack(pady=(0, 10))
            ttk.Label(main_frame, text=msg_text, font=("Microsoft YaHei", 10), justify="center").pack(pady=(0, 5))
            
            ttk.Label(main_frame, text=f"页面: {url[:50]}...", font=("Microsoft YaHei", 9), 
                     foreground="gray").pack(pady=(0, 15))
            
            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(fill="x")
            
            skip_btn = ttk.Button(btn_frame, text="⏭️ 跳过此页面", command=on_skip, width=15)
            skip_btn.pack(side="left", padx=10, expand=True)
            
            done_btn = ttk.Button(btn_frame, text="✅ 完成操作", command=on_done, width=15)
            done_btn.pack(side="right", padx=10, expand=True)
            
            dialog.protocol("WM_DELETE_WINDOW", on_skip)
            dialog.focus_set()
            
            while result['choice'] is None:
                dialog.update()
                time.sleep(0.05)
            
            return result['choice']
            
        except Exception as e:
            self.log(f"[Playwright] 对话框错误: {e}", "error")
            return 'skip'

    def _ensure_browser(self, headless=False):
        if self.connected and self.browser:
            try:
                if self.context.pages:
                    self.log("[Playwright] 复用现有浏览器实例", "info")
                    hwnd = get_browser_hwnd()
                    if hwnd:
                        set_window_top(hwnd)
                    return True
            except:
                self.connected = False
                self.browser = None
                self.context = None
        
        if self.browser_type not in ['chrome', 'msedge', 'firefox']:
            try:
                from browser_manager import setup_browser_env, is_browser_ready
                setup_browser_env()
                
                if not is_browser_ready():
                    self.log("[Playwright] 浏览器未安装", "warning")
                    return "need_download"
            except ImportError:
                pass
        
        try:
            from playwright.sync_api import sync_playwright
            self.p = sync_playwright().start()
        except Exception as e:
            self.log(f"[Playwright] 初始化失败: {e}", "error")
            return False
        
        ANTI_DETECT_ARGS = [
            '--disable-blink-features=AutomationControlled',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials',
            '--disable-web-security',
            '--no-sandbox',
            '--disable-infobars',
            '--disable-dev-shm-usage',
            '--disable-browser-side-navigation',
            '--disable-gpu'
        ]
        
        ANTI_DETECT_SCRIPT = """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en']
        });
        window.chrome = {
            runtime: {}
        };
        Object.defineProperty(navigator, 'platform', {
            get: () => 'Win32'
        });
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8
        });
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8
        });
        Object.defineProperty(screen, 'width', {
            get: () => 1920
        });
        Object.defineProperty(screen, 'height', {
            get: () => 1080
        });
        Object.defineProperty(screen, 'colorDepth', {
            get: () => 24
        });
        Object.defineProperty(navigator, 'permissions', {
            get: () => ({
                query: () => Promise.resolve({state: 'granted'})
            })
        });
        Object.defineProperty(navigator, 'connection', {
            get: () => ({
                effectiveType: '4g',
                downlink: 10,
                rtt: 50
            })
        });
        Object.defineProperty(navigator, 'maxTouchPoints', {
            get: () => 0
        });
        Object.defineProperty(navigator, 'vendor', {
            get: () => 'Google Inc.'
        });
        """
        
        os.makedirs(self.user_data_dir, exist_ok=True)
        
        args = ANTI_DETECT_ARGS + ['--window-position=100,100']
        
        browser_launched = False
        
        if self.browser_type == "internal":
            channels_to_try = [None]
        elif self.browser_type in ['chrome', 'msedge']:
            channels_to_try = [self.browser_type, None]
        else:
            channels_to_try = ['msedge', 'chrome', None]
        
        for channel in channels_to_try:
            try:
                launch_kwargs = {
                    'user_data_dir': self.user_data_dir,
                    'headless': False,
                    'args': args,
                    'viewport': {'width': 1200, 'height': 800},
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'locale': 'zh-CN',
                    'bypass_csp': True
                }
                if channel:
                    launch_kwargs['channel'] = channel
                    browser_name = 'Edge' if channel == 'msedge' else 'Chrome'
                else:
                    browser_name = '内置Chromium'
                
                self.context = self.p.chromium.launch_persistent_context(**launch_kwargs)
                self.browser = self.context
                self.log(f"[Playwright] {browser_name} 浏览器已启动（登录状态已保存）", "success")
                browser_launched = True
                break
            except Exception as e:
                if channel:
                    self.log(f"[Playwright] {browser_name} 启动失败: {e}", "warning")
                continue
        
        if not browser_launched:
            raise Exception("无法启动任何浏览器，请确保已安装 Edge 或 Chrome 或下载内置浏览器")
        
        self.connected = True
        return True

    def _center_window(self, page):
        try:
            client = page.context.new_cdp_session(page)
            window_id = client.send('Browser.getWindowForTarget')['windowId']
            screen_width = 1920
            screen_height = 1080
            window_width = 900
            window_height = 600
            x = max(0, (screen_width - window_width) // 2)
            y = max(0, (screen_height - window_height) // 2)
            client.send('Browser.setWindowBounds', {
                'windowId': window_id,
                'bounds': {'left': x, 'top': y, 'width': window_width, 'height': window_height, 'state': 'normal'}
            })
            
            try:
                import subprocess
                result = subprocess.run(['powershell', '-Command', 
                    f'Get-Process | Where-Object {{$_.MainWindowTitle -like "*Chrome*" -or $_.MainWindowTitle -like "*Edge*"}} | Select-Object -First 1 -ExpandProperty MainWindowHandle'],
                    capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and result.stdout.strip():
                    hwnd = int(result.stdout.strip())
                    set_window_bottom(hwnd)
            except:
                pass
        except Exception as e:
            self.log(f"[Playwright] 窗口居中失败: {e}", "warning")

    def _move_window_to_center(self):
        try:
            if not self.context or not self.context.pages:
                return
            
            page = self.context.pages[0]
            client = page.context.new_cdp_session(page)
            window_id = client.send('Browser.getWindowForTarget')['windowId']
            
            screen_width = 1920
            screen_height = 1080
            window_width = 900
            window_height = 600
            x = max(0, (screen_width - window_width) // 2)
            y = max(0, (screen_height - window_height) // 2)
            
            client.send('Browser.setWindowBounds', {
                'windowId': window_id,
                'bounds': {'left': x, 'top': y, 'width': window_width, 'height': window_height, 'state': 'normal'}
            })
            self.log("[Playwright] 浏览器窗口已移至屏幕中央", "info")
        except Exception as e:
            self.log(f"[Playwright] 移动窗口失败: {e}", "warning")

    def _url_to_b64(self, url, base_url):
        if url.startswith('//'):
            url = 'https:' + url
        elif not url.startswith('http'):
            url = urljoin(base_url, url)
        
        if not url.startswith('http') or len(url) > 2000:
            return None, None, None
        
        headers = {
            'Referer': base_url,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
        }
        
        last_error = None
        for attempt in range(3):
            try:
                resp = self.session.get(url, timeout=15, verify=False, headers=headers, allow_redirects=True)
                if resp.status_code == 200:
                    content = resp.content
                    break
            except Exception as e:
                last_error = e
                if attempt == 2:
                    self.log(f"图片下载失败: {url[:50]}... - {e}", "warning")
                    error_type = None
                    if 'SSL' in str(e) or 'TLSV1_ALERT' in str(e):
                        error_type = 'ssl'
                    elif 'Connection' in str(e) or 'timeout' in str(e).lower():
                        error_type = 'connection'
                    return None, None, error_type
                time.sleep(0.5)
        else:
            return None, None, None
        
        mime_type = resp.headers.get('Content-Type', '').split(';')[0].strip()
        if not mime_type or mime_type == 'application/octet-stream':
            mime_type, _ = mimetypes.guess_type(url)
        if not mime_type:
            if content[:4] == b'\x89PNG':
                mime_type = 'image/png'
            elif content[:2] == b'\xff\xd8':
                mime_type = 'image/jpeg'
            elif content[:6] in (b'GIF87a', b'GIF89a'):
                mime_type = 'image/gif'
            elif content[:4] == b'RIFF':
                mime_type = 'image/webp'
            elif b'<svg' in content[:500] or content.startswith(b'<?xml'):
                mime_type = 'image/svg+xml'
            else:
                mime_type = 'image/png'
        
        b64 = base64.b64encode(content).decode('utf-8')
        return f'data:{mime_type};base64,{b64}', content, None

    def _ask_ssl_skip_dialog(self, domain):
        import tkinter.messagebox as messagebox
        from tkinter import Tk
        root = self.gui.root if self.gui else Tk()
        result = messagebox.askyesno(
            "资源下载提示",
            f"检测到 {domain} 部分资源无法下载\n\n"
            f"可能原因：\n"
            f"• 需要登录才能访问\n"
            f"• 网站限制了自动化访问\n"
            f"• 网络连接问题\n\n"
            f"已为您处理其他可下载的资源。\n\n"
            f"是否跳过剩余图片下载？\n"
            f"• 点击「是」：跳过所有图片，继续处理其他资源\n"
            f"• 点击「否」：继续尝试下载图片",
            parent=root
        )
        self._ssl_skip_result = result

    def _get_page_title(self, page):
        try:
            title = page.title()
            if title and len(title) > 3:
                return re.sub(r'[\\/*?:"<>|]', '_', title)[:100]
        except:
            pass
        return f"page_{int(time.time())}"

    def _close_modals(self, page):
        selectors_js = ','.join(f'"{s}"' for s in self.POPUP_SELECTORS)
        close_script = f'''
        (function() {{
            var selectors = [{selectors_js}];
            var closed = 0;
            selectors.forEach(function(sel) {{
                document.querySelectorAll(sel).forEach(function(el) {{
                    if (el.offsetWidth > 0 || el.offsetHeight > 0) {{
                        el.click();
                        el.remove();
                        closed++;
                    }}
                }});
            }});
            document.body.style.overflow = 'auto';
            document.documentElement.style.overflow = 'auto';
            return closed;
        }})();
        '''
        try:
            closed = page.evaluate(close_script) or 0
        except:
            closed = 0
        
        for selector in self.GDPR_BUTTON_SELECTORS:
            try:
                btn = page.query_selector(selector)
                if btn and btn.is_visible():
                    btn.click(timeout=1000)
                    closed += 1
                    break
            except:
                pass
        
        return closed

    def _hide_ads(self, page):
        hide_script = '''
        (function() {
            var style = document.createElement('style');
            style.innerHTML = `
                .Pc-card, .Pc-word-card, .GlobalSideBar, .Sticky,
                .Question-sideColumn, .QuestionHeader-Comment,
                .CornerButton, .CornerAnimayedFlex,
                [class*="ad-"], [class*="ads-"], [class*="advert"],
                .Modal-wrapper, .Modal-inner, .SignFlow,
                .css-1ynzxqw, .SignFlowHomepage,
                .css-1h4afuj, .css-1qyijqe,
                .Question-mainColumnLogin, .LoginPrompt,
                [class*="LoginPrompt"], [class*="login-prompt"] {
                    display: none !important;
                }
                .RichContent-inner {
                    max-height: none !important;
                    overflow: visible !important;
                }
                html, body, .App-main, .Question-main, .QuestionAnswers-answer {
                    overflow: auto !important;
                    overflow-x: auto !important;
                    overflow-y: auto !important;
                    height: auto !important;
                    max-height: none !important;
                    position: static !important;
                }
                body {
                    overflow: auto !important;
                }
            `;
            document.head.appendChild(style);
            
            document.body.style.overflow = 'auto';
            document.documentElement.style.overflow = 'auto';
            
            var loginTexts = document.querySelectorAll('div, p, span, h1, h2, h3');
            loginTexts.forEach(function(el) {
                var text = el.innerText || '';
                if (text.includes('登录知乎，您可以享受以下权益') ||
                    text.includes('更懂你的优质内容') ||
                    text.includes('更专业的大咖答主') ||
                    text.includes('更深度的互动交流') ||
                    text.includes('更高效的创作环境') ||
                    text.includes('立即登录/注册')) {
                    if (el.parentElement && el.innerText.length < 200) {
                        el.style.display = 'none';
                    }
                }
            });
            
            return 'CSS injected';
        })();
        '''
        try:
            page.evaluate(hide_script)
        except:
            pass

    def _remove_elements(self, page):
        selectors_js = ','.join(f'"{s}"' for s in self.REMOVE_SELECTORS)
        remove_script = f'''
        (function() {{
            var selectors = [{selectors_js}];
            var removed = 0;
            selectors.forEach(function(sel) {{
                document.querySelectorAll(sel).forEach(function(el) {{
                    el.remove();
                    removed++;
                }});
            }});
            return removed;
        }})();
        '''
        try:
            removed = page.evaluate(remove_script) or 0
            self.log(f"[Playwright] 移除了 {removed} 个干扰元素", "info")
        except:
            pass

    def _trigger_lazy_load(self, page):
        try:
            page.evaluate('''
            document.querySelectorAll('img[data-src]').forEach(i => i.src = i.dataset.src);
            document.querySelectorAll('img[data-original]').forEach(i => i.src = i.dataset.original);
            document.querySelectorAll('[loading="lazy"]').forEach(i => i.loading = 'eager');
            ''')
        except:
            pass

    def _expand_content(self, page):
        try:
            expand_script = '''
            (function() {
                var expanded = 0;
                var loginRequired = false;
                
                document.querySelectorAll('button').forEach(function(btn) {
                    var text = btn.innerText || btn.textContent;
                    if (text.includes('展开') || text.includes('阅读全文') || 
                        text.includes('查看全部') || text.includes('显示更多') ||
                        text.includes('展开全文') || text.includes('查看更多') ||
                        text.includes('阅读全部') || text.includes('展开全部')) {
                        try {
                            btn.click();
                            expanded++;
                        } catch(e) {}
                    }
                });
                
                document.querySelectorAll('.ContentItem-expandButton, .RichContent-inner .ContentItem-expandButton').forEach(function(btn) {
                    try {
                        btn.click();
                        expanded++;
                    } catch(e) {}
                });
                
                document.querySelectorAll('[class*="expand"]').forEach(function(el) {
                    if (el.offsetWidth > 0 || el.offsetHeight > 0) {
                        try {
                            el.click();
                            expanded++;
                        } catch(e) {}
                    }
                });
                
                document.querySelectorAll('.RichContent-inner').forEach(function(el) {
                    el.style.maxHeight = 'none';
                    el.style.overflow = 'visible';
                });
                
                document.querySelectorAll('.RichText').forEach(function(el) {
                    el.style.maxHeight = 'none';
                });
                
                document.querySelectorAll('.RichContent').forEach(function(el) {
                    el.classList.add('RichContent-expanded');
                });
                
                document.querySelectorAll('[style*="max-height"]').forEach(function(el) {
                    if (el.classList.contains('RichContent-inner') || 
                        el.classList.contains('RichText') ||
                        el.classList.contains('ContentItem')) {
                        el.style.maxHeight = 'none';
                    }
                });
                
                var loginTexts = document.querySelectorAll('div, span, p, button');
                loginTexts.forEach(function(el) {
                    var text = el.innerText || '';
                    if (text.includes('登录后查看') || 
                        text.includes('登录查看') ||
                        text.includes('登录知乎') ||
                        text.includes('立即登录') ||
                        text.includes('登录/注册')) {
                        if (text.length < 50) {
                            loginRequired = true;
                        }
                    }
                });
                
                var answerItems = document.querySelectorAll('.List-item, .ContentItem, .AnswerItem');
                answerItems.forEach(function(item) {
                    var expandBtn = item.querySelector('.ContentItem-expandButton');
                    if (expandBtn) {
                        try {
                            expandBtn.click();
                            expanded++;
                        } catch(e) {}
                    }
                    
                    var contentInner = item.querySelector('.RichContent-inner');
                    if (contentInner) {
                        contentInner.style.maxHeight = 'none';
                        contentInner.style.overflow = 'visible';
                    }
                });
                
                return { expanded: expanded, loginRequired: loginRequired };
            })();
            '''
            result = page.evaluate(expand_script)
            if result:
                if result.get('expanded', 0) > 0:
                    self.log(f"[Playwright] 展开了 {result['expanded']} 处内容", "info")
                if result.get('loginRequired'):
                    self.log("[Playwright] ⚠️ 检测到需要登录才能查看完整内容", "warning")
                time.sleep(0.5)
            return result or {'expanded': 0, 'loginRequired': False}
        except:
            return {'expanded': 0, 'loginRequired': False}

    def _scroll_page(self, page, max_scrolls=50):
        try:
            self.log("[Playwright] 正在滚动页面加载图片...", "info")
            
            for i in range(max_scrolls):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                time.sleep(0.2)
                
                current_pos = page.evaluate('window.pageYOffset + window.innerHeight')
                total_height = page.evaluate('document.body.scrollHeight')
                
                if current_pos >= total_height - 100:
                    self.log(f"[Playwright] 已滚动到底部", "info")
                    break
            
            page.evaluate('window.scrollTo(0, 0)')
            time.sleep(0.3)
        except:
            pass

    def _embed_resources(self, soup, base_url):
        img_count = 0
        style_count = 0
        bg_count = 0
        total_imgs = len(soup.find_all('img'))
        processed_imgs = 0
        ssl_error_count = 0
        ssl_error_domain = None
        skip_all_images = False
        user_asked = False
        
        self.log("[Playwright] 正在处理资源... (可能需要较长时间，请耐心等待)", "info")
        
        for img in soup.find_all('img'):
            if skip_all_images:
                break
            for attr in ['src', 'data-src', 'data-original']:
                src = img.get(attr)
                if src and not src.startswith('data:') and not src.startswith('blob:'):
                    data_uri, _, error_type = self._url_to_b64(src, base_url)
                    if error_type == 'ssl':
                        ssl_error_count += 1
                        if ssl_error_domain is None:
                            from urllib.parse import urlparse
                            ssl_error_domain = urlparse(src).netloc
                        if ssl_error_count >= 3 and not user_asked:
                            user_asked = True
                            self.log(f"[Playwright] 检测到 {ssl_error_domain} 部分资源无法下载（可能需要登录）", "warning")
                            if self.gui:
                                import tkinter.messagebox as messagebox
                                result = self.gui.root.after(0, lambda: self._ask_ssl_skip_dialog(ssl_error_domain))
                                while not hasattr(self, '_ssl_skip_result'):
                                    time.sleep(0.1)
                                skip_all_images = self._ssl_skip_result
                                delattr(self, '_ssl_skip_result')
                            else:
                                skip_all_images = True
                        if not skip_all_images:
                            continue
                    if data_uri:
                        img['src'] = data_uri
                        if attr != 'src':
                            del img[attr]
                        img_count += 1
                        break
            
            processed_imgs += 1
            
            srcset = img.get('srcset')
            if srcset:
                new_parts = []
                for part in srcset.split(','):
                    part = part.strip()
                    if ' ' in part:
                        url, size = part.rsplit(' ', 1)
                    else:
                        url, size = part, '1x'
                    if not url.startswith('data:'):
                        data_uri, _, error_type = self._url_to_b64(url, base_url)
                        if error_type == 'ssl' and not user_asked:
                            ssl_error_count += 1
                            if ssl_error_domain is None:
                                from urllib.parse import urlparse
                                ssl_error_domain = urlparse(url).netloc
                            if ssl_error_count >= 3:
                                user_asked = True
                                if self.gui:
                                    self.gui.root.after(0, lambda: self._ask_ssl_skip_dialog(ssl_error_domain))
                                    while not hasattr(self, '_ssl_skip_result'):
                                        time.sleep(0.1)
                                    skip_all_images = self._ssl_skip_result
                                    delattr(self, '_ssl_skip_result')
                                else:
                                    skip_all_images = True
                        if data_uri:
                            new_parts.append(f'{data_uri} {size}')
                            img_count += 1
                if new_parts:
                    img['srcset'] = ', '.join(new_parts)
        
        for source in soup.find_all('source'):
            srcset = source.get('srcset')
            if srcset:
                new_parts = []
                for part in srcset.split(','):
                    part = part.strip()
                    if ' ' in part:
                        url, descriptor = part.rsplit(' ', 1)
                    else:
                        url, descriptor = part, '1x'
                    if not url.startswith('data:'):
                        data_uri, _, _ = self._url_to_b64(url, base_url)
                        if data_uri:
                            new_parts.append(f'{data_uri} {descriptor}')
                            img_count += 1
                if new_parts:
                    source['srcset'] = ', '.join(new_parts)
        
        for video in soup.find_all('video'):
            poster = video.get('poster')
            if poster and not poster.startswith('data:'):
                data_uri, _, _ = self._url_to_b64(poster, base_url)
                if data_uri:
                    video['poster'] = data_uri
                    img_count += 1
        
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href and not href.startswith('data:'):
                data_uri, content, _ = self._url_to_b64(href, base_url)
                if content:
                    style_tag = soup.new_tag('style')
                    style_tag.string = content.decode('utf-8', errors='ignore')
                    link.replace_with(style_tag)
                    style_count += 1
        
        url_pattern = re.compile(r'url\(["\']?([^)"\'\s]+)["\']?\)')
        bg_counter = [0]
        
        def replace_urls(text):
            def repl(m):
                url = m.group(1).strip('\'"')
                if url.startswith('data:') or url.startswith('blob:'):
                    return m.group(0)
                data_uri, _, _ = self._url_to_b64(url, base_url)
                if data_uri:
                    bg_counter[0] += 1
                    return f'url({data_uri})'
                return m.group(0)
            return url_pattern.sub(repl, text)
        
        for el in soup.find_all(style=True):
            el['style'] = replace_urls(el.get('style', ''))
        
        for style in soup.find_all('style'):
            if style.string:
                style.string = replace_urls(style.string)
        
        bg_count = bg_counter[0]
        return img_count, style_count, bg_count

    def _clean_html(self, soup):
        from bs4 import BeautifulSoup
        
        for selector in self.REMOVE_SELECTORS:
            for el in soup.select(selector):
                el.decompose()
        
        for tag in soup.find_all(['script', 'iframe']):
            tag.decompose()
        
        for tag in soup.find_all(True):
            for attr in self.EVENT_ATTRS:
                if tag.has_attr(attr):
                    del tag[attr]
            
            if tag.has_attr('href'):
                href = tag['href']
                if href.startswith('http') or href.startswith('//'):
                    tag['href'] = '未下载页面.html#' + href
        
        for meta in soup.find_all('meta'):
            if meta.get('http-equiv', '').lower() in ['refresh', 'location']:
                meta.decompose()
        
        for link in soup.find_all('link'):
            href = link.get('href', '')
            rel = link.get('rel', [])
            if href and not href.startswith('data:'):
                if 'stylesheet' not in (rel if isinstance(rel, list) else [rel]):
                    link.decompose()
        
        for style in soup.find_all('style'):
            if style.string:
                content = style.string
                content = re.sub(r'background-color\s*:\s*#0a0a0a', 'background-color: #f5f6f7', content, flags=re.IGNORECASE)
                content = re.sub(r'user-select\s*:\s*none', 'user-select: text', content, flags=re.IGNORECASE)
                content = re.sub(r'-webkit-user-select\s*:\s*none', '-webkit-user-select: text', content, flags=re.IGNORECASE)
                content = re.sub(r'-moz-user-select\s*:\s*none', '-moz-user-select: text', content, flags=re.IGNORECASE)
                content = re.sub(r'-ms-user-select\s*:\s*none', '-ms-user-select: text', content, flags=re.IGNORECASE)
                style.string = content
        
        inject_style = soup.new_tag('style')
        inject_style.string = self.INJECT_CSS
        if soup.head:
            soup.head.append(inject_style)
        
        block_script = soup.new_tag('script')
        block_script.string = self.BLOCK_SCRIPT
        if soup.body:
            soup.body.insert(0, block_script)
    
    def _inject_floating_toc(self, soup, url):
        from bs4 import BeautifulSoup
        from urllib.parse import urlparse
        
        title = soup.title.string if soup.title else '未命名页面'
        
        parsed = urlparse(url)
        domain = parsed.netloc
        
        site_names = {
            'zhihu.com': '知乎',
            'csdn.net': 'CSDN',
            'juejin.cn': '掘金',
            'jianshu.com': '简书',
            'bilibili.com': '哔哩哔哩',
            'blog.csdn.net': 'CSDN博客',
            'zhuanlan.zhihu.com': '知乎专栏',
        }
        
        site_name = None
        for site_domain, name in site_names.items():
            if site_domain in domain:
                site_name = name
                break
        
        if not site_name:
            site_name = domain
        
        toc_css = '''
        #floatingTocPanel {
            position: fixed !important;
            top: 50% !important;
            left: 20px !important;
            transform: translateY(-50%) !important;
            width: 350px !important;
            max-height: 80vh !important;
            background: rgba(255, 255, 255, 0.98) !important;
            border-radius: 12px !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
            z-index: 999999 !important;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
            overflow: hidden !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            box-sizing: border-box !important;
            line-height: 1.5 !important;
        }
        
        #floatingTocPanel.collapsed {
            display: none !important;
        }
        
        #floatingTocPanel.expanded {
            display: block !important;
        }
        
        #floatingTocPanel * {
            box-sizing: border-box !important;
        }
        
        #floatingTocHeader {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            padding: 15px 20px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
            cursor: move !important;
            user-select: none !important;
        }
        
        #floatingTocPanel .floating-toc-title {
            font-size: 16px !important;
            font-weight: bold !important;
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
            color: white !important;
        }
        
        #floatingTocPanel .floating-toc-toggle-btn {
            background: rgba(255, 255, 255, 0.2) !important;
            border: none !important;
            color: white !important;
            width: 32px !important;
            height: 32px !important;
            border-radius: 50% !important;
            cursor: pointer !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            transition: all 0.3s ease !important;
            font-size: 18px !important;
        }
        
        #floatingTocPanel .floating-toc-toggle-btn:hover {
            background: rgba(255, 255, 255, 0.3) !important;
            transform: scale(1.1) !important;
        }
        
        #floatingTocPanel .floating-toc-content {
            padding: 15px !important;
            max-height: calc(80vh - 60px) !important;
            overflow-y: auto !important;
        }
        
        #floatingTocPanel .floating-toc-content::-webkit-scrollbar {
            width: 6px !important;
        }
        
        #floatingTocPanel .floating-toc-content::-webkit-scrollbar-track {
            background: #f1f1f1 !important;
            border-radius: 3px !important;
        }
        
        #floatingTocPanel .floating-toc-content::-webkit-scrollbar-thumb {
            background: #c1c1c1 !important;
            border-radius: 3px !important;
        }
        
        #floatingTocPanel .floating-toc-item {
            padding: 12px 15px !important;
            margin: 8px 0 !important;
            background: #f8f9fa !important;
            border-radius: 8px !important;
            cursor: pointer !important;
            transition: all 0.3s ease !important;
            border-left: 3px solid transparent !important;
        }
        
        #floatingTocPanel .floating-toc-item:hover {
            background: #e3f2fd !important;
            border-left-color: #2196f3 !important;
            transform: translateX(3px) !important;
        }
        
        #floatingTocPanel .floating-toc-item-title {
            color: #333 !important;
            font-size: 14px !important;
            line-height: 1.4 !important;
        }
        
        #floatingTocPanel .floating-toc-source {
            color: #7f8c8d !important;
            font-size: 11px !important;
            margin-top: 3px !important;
        }
        
        #floatingTocFloatBtn {
            position: fixed !important;
            top: 50% !important;
            left: 0 !important;
            transform: translateY(-50%) !important;
            width: 40px !important;
            height: 80px !important;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            border-radius: 0 12px 12px 0 !important;
            cursor: pointer !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            color: white !important;
            font-size: 20px !important;
            z-index: 999998 !important;
            transition: all 0.3s ease !important;
            box-shadow: 2px 0 10px rgba(0, 0, 0, 0.2) !important;
        }
        
        #floatingTocFloatBtn:hover {
            width: 50px !important;
            box-shadow: 4px 0 15px rgba(0, 0, 0, 0.3) !important;
        }
        
        #floatingTocFloatBtn.hidden {
            left: -50px !important;
        }
        '''
        
        toc_html = f'''
        <div class="floating-toc-panel" id="floatingTocPanel">
            <div class="floating-toc-header" id="floatingTocHeader">
                <div class="floating-toc-title">
                    <span>📑</span>
                    <span>文章目录</span>
                </div>
                <button class="floating-toc-toggle-btn" onclick="toggleFloatingTOC()" title="折叠/展开">
                    ◀
                </button>
            </div>
            <div class="floating-toc-content">
                <div class="floating-toc-item">
                    <div class="floating-toc-item-title">标题</div>
                    <div class="floating-toc-source">{title}</div>
                </div>
                <div class="floating-toc-item">
                    <div class="floating-toc-item-title">来源</div>
                    <div class="floating-toc-source">{site_name}</div>
                </div>
                <div class="floating-toc-item">
                    <div class="floating-toc-item-title">原始网址</div>
                    <div class="floating-toc-source" style="word-break: break-all;">{url}</div>
                </div>
            </div>
        </div>
        
        <div class="floating-toc-float-btn" id="floatingTocFloatBtn" onclick="toggleFloatingTOC()" title="展开目录">
            ◀
        </div>
        '''
        
        toc_script = '''
        var floatingTocPanel = document.getElementById('floatingTocPanel');
        var floatingTocFloatBtn = document.getElementById('floatingTocFloatBtn');
        var isFloatingCollapsed = false;
        var floatingXOffset = 0;
        var floatingYOffset = 0;
        
        function toggleFloatingTOC() {
            isFloatingCollapsed = !isFloatingCollapsed;
            
            if (isFloatingCollapsed) {
                floatingTocPanel.classList.add('collapsed');
                floatingTocPanel.classList.remove('expanded');
                floatingTocFloatBtn.classList.remove('hidden');
                floatingTocFloatBtn.innerHTML = '▶';
                floatingTocPanel.style.transform = 'translateY(-50%)';
                floatingXOffset = 0;
                floatingYOffset = 0;
            } else {
                floatingTocPanel.classList.remove('collapsed');
                floatingTocPanel.classList.add('expanded');
                floatingTocFloatBtn.classList.add('hidden');
                floatingTocPanel.style.transform = 'translateY(-50%)';
            }
        }
        
        var floatingTocHeader = document.getElementById('floatingTocHeader');
        var isFloatingDragging = false;
        var floatingCurrentX;
        var floatingCurrentY;
        var floatingInitialX;
        var floatingInitialY;
        
        floatingTocHeader.addEventListener('mousedown', floatingDragStart);
        document.addEventListener('mouseup', floatingDragEnd);
        document.addEventListener('mousemove', floatingDrag);
        
        function floatingDragStart(e) {
            floatingInitialX = e.clientX - floatingXOffset;
            floatingInitialY = e.clientY - floatingYOffset;
            
            if (e.target === floatingTocHeader || floatingTocHeader.contains(e.target)) {
                isFloatingDragging = true;
            }
        }
        
        function floatingDragEnd(e) {
            floatingInitialX = floatingCurrentX;
            floatingInitialY = floatingCurrentY;
            isFloatingDragging = false;
        }
        
        function floatingDrag(e) {
            if (isFloatingDragging) {
                e.preventDefault();
                floatingCurrentX = e.clientX - floatingInitialX;
                floatingCurrentY = e.clientY - floatingInitialY;
                floatingXOffset = floatingCurrentX;
                floatingYOffset = floatingCurrentY;
                
                floatingTocPanel.style.transform = 'translate(' + floatingCurrentX + 'px, ' + floatingCurrentY + 'px)';
            }
        }
        
        // 初始化：默认展开
        if (floatingTocPanel) {
            floatingTocPanel.classList.add('expanded');
            if (floatingTocFloatBtn) {
                floatingTocFloatBtn.classList.add('hidden');
            }
        }
        '''
        
        if soup.find(id='floatingTocPanel'):
            return
        
        style_tag = soup.new_tag('style')
        style_tag.string = toc_css
        if soup.head:
            soup.head.append(style_tag)
        
        from bs4 import BeautifulSoup
        toc_div = BeautifulSoup(toc_html, 'html.parser')
        if soup.body:
            soup.body.append(toc_div)
        
        script_tag = soup.new_tag('script')
        script_tag.string = toc_script
        if soup.body:
            soup.body.append(script_tag)

    def download_page(self, url, save_dir, filename=None, headless=True, process_resources=True):
        try:
            from bs4 import BeautifulSoup
            
            if not self._ensure_browser(headless):
                return None
            
            page = self.context.new_page()
            
            try:
                self.log(f"[Playwright] 正在访问: {url}", "info")
                page.goto(url, wait_until='networkidle', timeout=60000)
                
                self.log("[Playwright] 等待页面加载...", "info")
                time.sleep(3)
                
                self._close_modals(page)
                
                expand_result = self._expand_content(page)
                if expand_result.get('expanded', 0) > 0:
                    self.log(f"[Playwright] 展开了 {expand_result['expanded']} 处内容", "info")
                if expand_result.get('loginRequired'):
                    self.log("[Playwright] ⚠️ 检测到需要登录才能查看完整内容", "warning")
                
                self._scroll_page(page)
                
                self._trigger_lazy_load(page)
                
                self._hide_ads(page)
                
                time.sleep(2)
                
                self._close_modals(page)
                self._remove_elements(page)
                
                if not filename:
                    filename = self._get_page_title(page)
                
                html_content = page.content()
                
                if '"code":40362' in html_content or '请求存在异常' in html_content or '暂时限制本次访问' in html_content:
                    self.log("[Playwright] ⚠️ 访问过于频繁，请稍后再试", "warning")
                    return "rate_limited"
                
                soup = BeautifulSoup(html_content, 'lxml')
                
                os.makedirs(save_dir, exist_ok=True)
                safe_filename = re.sub(r'[\\/*?:"<>|]', '_', filename)
                filepath = os.path.join(save_dir, f"{safe_filename}.html")
                
                if process_resources:
                    self.log("[Playwright] 正在处理资源...", "info")
                    img_count, style_count, bg_count = self._embed_resources(soup, url)
                    self.log(f"[Playwright] 内嵌: 图片 {img_count}, 样式 {style_count}, 背景图 {bg_count}", "info")
                
                self._clean_html(soup)
                self.log("[Playwright] HTML清理完成", "info")
                
                self._inject_floating_toc(soup, url)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                
                self.log(f"[Playwright] 保存成功: {filepath}", "success")
                return filepath
                
            finally:
                page.close()
                
        except Exception as e:
            error_details = traceback.format_exc()
            self.log(f"[Playwright] 下载失败: {e}", "error")
            save_crash_log_pw("playwright_downloader", error_details, f"URL: {url}")
            return None

    def download_batch(self, urls, save_dir, headless=True, progress_callback=None, stop_check=None, download_mode="html"):
        results = []
        total = len(urls)
        downloaded_files = []
        
        if not self._ensure_browser(headless):
            return results
        
        self.log(f"[Playwright] ========== 第一阶段：下载所有网页 (模式: {download_mode.upper()}) ==========", "info")
        self.log("[Playwright] 💡 浏览器将在前台显示，请勿操作浏览器窗口", "info")
        
        reuse_page = None
        try:
            reuse_page = self.context.new_page()
            
            for i, url in enumerate(urls):
                if stop_check and stop_check():
                    self.log("[Playwright] 下载已终止", "warning")
                    break
                
                hwnd = get_browser_hwnd()
                if hwnd:
                    set_window_top(hwnd)
                
                self.log(f"[Playwright] 正在下载 [{i+1}/{total}]: {url[:50]}...", "info")
                
                result = None
                
                try:
                    page_loaded = False
                    try:
                        reuse_page.goto(url, wait_until='networkidle', timeout=30000)
                        time.sleep(2)
                        try:
                            reuse_page.evaluate(ANTI_DETECT_SCRIPT)
                        except:
                            pass
                        page_loaded = True
                    except Exception as timeout_e:
                        self.log(f"[Playwright] ⏳ 页面加载超时，请检查浏览器窗口", "warning")
                        hwnd = get_browser_hwnd()
                        if hwnd:
                            set_window_top(hwnd)
                        
                        user_choice = self._show_page_action_dialog(url)
                        
                        if user_choice == 'skip':
                            self.log("[Playwright] ⏭️ 用户选择跳过此页面", "info")
                            result = "user_skipped"
                        elif user_choice == 'done':
                            self.log("[Playwright] ✅ 用户确认页面已准备好", "info")
                            page_loaded = True
                        else:
                            result = None
                    
                    if page_loaded:
                        html_content = reuse_page.content()
                        if '安全验证' in html_content or 'Security Verification' in html_content or '请完成"安全验证"' in html_content:
                            self.log("[Playwright] ⚠️ 检测到安全验证页面，请手动完成验证", "warning")
                            hwnd = get_browser_hwnd()
                            if hwnd:
                                set_window_top(hwnd)
                            
                            user_choice = self._show_page_action_dialog(url, is_security_check=True)
                            
                            if user_choice == 'skip':
                                self.log("[Playwright] ⏭️ 用户选择跳过此页面", "info")
                                result = "user_skipped"
                            elif user_choice == 'done':
                                self.log("[Playwright] ✅ 用户确认验证已完成", "info")
                                hwnd = get_browser_hwnd()
                                if hwnd:
                                    set_window_top(hwnd)
                            else:
                                result = "security_check"
                        
                        if not result or result not in ["user_skipped", "security_check"]:
                            self._close_modals(reuse_page)
                            
                            expand_result = self._expand_content(reuse_page)
                            if expand_result.get('expanded', 0) > 0:
                                self.log(f"[Playwright] 展开了 {expand_result['expanded']} 处内容", "info")
                            if expand_result.get('loginRequired'):
                                self.log("[Playwright] ⚠️ 检测到需要登录才能查看完整内容", "warning")
                            
                            self._scroll_page(reuse_page)
                            self._trigger_lazy_load(reuse_page)
                            self._hide_ads(reuse_page)
                            
                            time.sleep(1)
                            
                            self._close_modals(reuse_page)
                            self._remove_elements(reuse_page)
                            
                            filename = self._get_page_title(reuse_page)
                            html_content = reuse_page.content()
                            
                            if '"code":40362' in html_content or '请求存在异常' in html_content or '暂时限制本次访问' in html_content:
                                self.log("[Playwright] ⚠️ 访问过于频繁，请稍后再试", "warning")
                                result = "rate_limited"
                            else:
                                from bs4 import BeautifulSoup
                                soup = BeautifulSoup(html_content, 'lxml')
                                
                                os.makedirs(save_dir, exist_ok=True)
                                safe_filename = re.sub(r'[\\/*?:"<>|]', '_', filename)
                                
                                saved_files = []
                                
                                if download_mode in ["html", "both"]:
                                    filepath = os.path.join(save_dir, f"{safe_filename}.html")
                                    with open(filepath, 'w', encoding='utf-8') as f:
                                        f.write(str(soup))
                                    saved_files.append(filepath)
                                    self.log(f"[Playwright] HTML保存成功: {filepath}", "success")
                                
                                if download_mode in ["pdf", "both"]:
                                    pdf_filepath = os.path.join(save_dir, f"{safe_filename}.pdf")
                                    try:
                                        reuse_page.pdf(path=pdf_filepath, format='A4', print_background=True, margin={
                                            'top': '20px',
                                            'bottom': '20px',
                                            'left': '20px',
                                            'right': '20px'
                                        })
                                        saved_files.append(pdf_filepath)
                                        self.log(f"[Playwright] PDF保存成功: {pdf_filepath}", "success")
                                    except Exception as pdf_e:
                                        self.log(f"[Playwright] PDF保存失败: {pdf_e}", "warning")
                                
                                result = saved_files[0] if saved_files else None
                    
                except Exception as e:
                    self.log(f"[Playwright] 页面访问失败: {e}", "error")
                    result = None
                
                success = bool(result) and result != "rate_limited"
                results.append({'url': url, 'success': success, 'filepath': result if success else None})
                
                if success and result:
                    downloaded_files.append({'url': url, 'filepath': result})
                
                if progress_callback:
                    progress_callback(i + 1, total, result, "download", url)
        
        finally:
            if reuse_page:
                try:
                    reuse_page.close()
                except:
                    pass
        
        if downloaded_files:
            self.log(f"[Playwright] ========== 第二阶段：处理资源（共 {len(downloaded_files)} 个文件）==========", "info")
            
            for i, file_info in enumerate(downloaded_files):
                if stop_check and stop_check():
                    self.log("[Playwright] 资源处理已终止", "warning")
                    break
                
                filepath = file_info['filepath']
                url = file_info['url']
                
                try:
                    self.log(f"[Playwright] 处理资源 [{i+1}/{len(downloaded_files)}]: {os.path.basename(filepath)}", "info")
                    
                    if progress_callback:
                        progress_callback(i + 1, len(downloaded_files), filepath, "process", url)
                    
                    with open(filepath, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html_content, 'lxml')
                    
                    img_count, style_count, bg_count = self._embed_resources(soup, url)
                    self.log(f"[Playwright] 内嵌: 图片 {img_count}, 样式 {style_count}, 背景图 {bg_count}", "info")
                    
                    self._clean_html(soup)
                    
                    self._inject_floating_toc(soup, url)
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(str(soup))
                    
                except Exception as e:
                    self.log(f"[Playwright] 资源处理失败 {filepath}: {e}", "warning")
        
        self.log("[Playwright] ========== 下载完成 ==========", "success")
        return results

    def connect_to_browser(self):
        return self._ensure_browser(headless=False)

    def launch_browser(self, headless=False):
        return self._ensure_browser(headless=headless)

    def open_login_page(self, site='zhihu'):
        sites = {
            'zhihu': 'https://www.zhihu.com/signin',
            'csdn': 'https://passport.csdn.net/login',
            'juejin': 'https://juejin.cn/passport/login',
            'jianshu': 'https://www.jianshu.com/sign_in'
        }
        
        url = sites.get(site, sites['zhihu'])
        
        if not self._ensure_browser(headless=False):
            return False
        
        self._move_window_to_center()
        
        hwnd = get_browser_hwnd()
        if hwnd:
            set_window_top(hwnd)
        
        try:
            if self.context.pages:
                page = self.context.pages[0]
                self.log(f"[Playwright] 复用现有页面打开登录页", "info")
            else:
                page = self.context.new_page()
                self.log(f"[Playwright] 创建新页面打开登录页", "info")
            self._center_window(page)
            page.goto(url, wait_until='networkidle')
            self.log(f"[Playwright] 已打开 {site} 登录页面，请在浏览器中完成登录", "info")
            self.log("[Playwright] 登录状态将自动保存到本地", "info")
            return True
        except Exception as e:
            self.log(f"[Playwright] 打开登录页面失败: {e}", "error")
            return False

    def download_multiple(self, urls, save_dir, progress_callback=None, headless=True, stop_check=None, download_mode="html"):
        return self.download_batch(urls, save_dir, headless, progress_callback, stop_check, download_mode)

    def close(self, minimize_only=False):
        if minimize_only:
            hwnd = get_browser_hwnd()
            if hwnd:
                try:
                    ctypes.windll.user32.ShowWindow(hwnd, 6)
                except:
                    pass
            self.log("[Playwright] 浏览器已最小化", "info")
            return
        
        self.log("[Playwright] 正在关闭浏览器...", "info")
        
        try:
            if self.context:
                try:
                    for page in self.context.pages[:]:
                        try:
                            page.close()
                        except:
                            pass
                except:
                    pass
        except:
            pass
        
        try:
            if self.browser:
                try:
                    self.browser.close()
                except:
                    pass
        except:
            pass
        
        try:
            if self.p:
                try:
                    self.p.stop()
                except:
                    pass
        except:
            pass
        
        self.browser = None
        self.context = None
        self.p = None
        self.connected = False
        self.log("[Playwright] 浏览器已安全关闭", "info")
    
    @staticmethod
    def generate_not_downloaded_page(original_url=""):
        return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>页面未下载</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 60px 40px;
            max-width: 500px;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }
        .icon {
            font-size: 80px;
            margin-bottom: 30px;
        }
        h1 {
            color: #2c3e50;
            font-size: 28px;
            margin-bottom: 20px;
        }
        .message {
            color: #7f8c8d;
            font-size: 16px;
            line-height: 1.8;
            margin-bottom: 30px;
        }
        .url-box {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 30px;
            word-break: break-all;
            font-size: 13px;
            color: #555;
            border: 1px solid #e0e0e0;
        }
        .btn-group {
            display: flex;
            gap: 15px;
            justify-content: center;
            flex-wrap: wrap;
        }
        .back-btn {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            padding: 15px 40px;
            border-radius: 30px;
            font-size: 16px;
            font-weight: bold;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        .back-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }
        .toc-btn {
            display: inline-block;
            background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
            color: white;
            text-decoration: none;
            padding: 15px 40px;
            border-radius: 30px;
            font-size: 16px;
            font-weight: bold;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(39, 174, 96, 0.4);
        }
        .toc-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(39, 174, 96, 0.6);
        }
        .tips {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #95a5a6;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">📄</div>
        <h1>当前页面未下载</h1>
        <div class="message">
            您点击的链接指向外部页面，<br>
            该页面未被下载到本地。
        </div>
        <div class="url-box">
            <strong>原始地址：</strong><br>
            <span id="originalUrl"></span>
        </div>
        <div class="btn-group">
            <a href="javascript:history.back()" class="back-btn">← 返回上一页</a>
            <a href="../文献合集.html" class="toc-btn">📑 返回目录</a>
        </div>
        <div class="tips">
            💡 提示：如需查看此页面，请将链接添加到下载列表中重新下载
        </div>
    </div>
    <script>
        var url = document.referrer || window.location.hash.slice(1) || '';
        if (url) {
            document.getElementById('originalUrl').textContent = decodeURIComponent(url);
        } else {
            document.getElementById('originalUrl').textContent = '未知来源';
        }
    </script>
</body>
</html>'''
