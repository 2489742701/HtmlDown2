# Playwright 网页保存器实现计划

## 目标
使用 Playwright 替代 SingleFile，实现完整的网页保存功能，解决知乎等网站的反爬问题。

## 核心优势
1. 可连接已打开的 Chrome/Edge 浏览器，复用登录态
2. 完全绕过无头检测
3. 支持真实浏览器操作

## 需要创建/修改的文件
- 新建：`playwright_downloader.py`
- 修改：`gui.py`（集成 Playwright 下载器）

## 实现步骤

### 步骤1：安装依赖
```bash
pip install playwright
playwright install chromium
```

### 步骤2：创建 playwright_downloader.py
完整代码如下：

```python
import os
import time
import random
import subprocess
from urllib.parse import urlparse

class PlaywrightDownloader:
    def __init__(self, gui=None, log_callback=None):
        self.gui = gui
        self.log_callback = log_callback
        self.browser = None
        self.context = None
        self.connected = False
        self.debug_port = 9222
    
    def log(self, msg, tag="info"):
        if self.log_callback:
            self.log_callback(msg, tag)
        elif self.gui and hasattr(self.gui, 'literature_log'):
            self.gui.root.after(0, lambda: self.gui.literature_log(msg, tag))
        elif self.gui:
            self.gui.root.after(0, lambda: self.gui.log(msg, tag))
        else:
            print(f"[{tag}] {msg}")
    
    def get_domain(self, url):
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    
    def get_page_title(self, page):
        try:
            title = page.title()
            if title and len(title) > 3:
                title = title.replace('\\', '_').replace('/', '_')
                title = title.replace('*', '_').replace('?', '_')
                title = title.replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                title = title.replace(':', '_')
                return title[:100]
        except:
            pass
        return f"page_{int(time.time())}"
    
    def close_login_modal(self, page):
        close_script = """
        (function() {
            var selectors = [
                '.Modal-wrapper', '.Modal-inner', '.SignFlow', '.LoginContainer',
                '[class*="Modal"]', '[class*="modal"]', '[class*="sign-flow"]',
                '[class*="login-modal"]', '[class*="Login"]', '[class*="login"]',
                '[class*="popup"]', '[class*="Popup"]', '[class*="overlay"]',
                '[class*="backdrop"]', '[class*="mask"]'
            ];
            
            var closed = 0;
            for (var i = 0; i < selectors.length; i++) {
                var elements = document.querySelectorAll(selectors[i]);
                for (var j = 0; j < elements.length; j++) {
                    try {
                        elements[j].click();
                        elements[j].remove();
                        closed++;
                    } catch(e) {}
                }
            }
            
            document.body.style.overflow = 'auto';
            return closed;
        })();
        """
        try:
            result = page.evaluate(close_script)
            return result if result else 0
        except:
            return 0
    
    def trigger_lazy_load(self, page):
        lazy_script = """
        document.querySelectorAll('img[data-src]').forEach(img => {
            img.src = img.dataset.src;
        });
        document.querySelectorAll('img[data-original]').forEach(img => {
            img.src = img.dataset.original;
        });
        """
        try:
            page.evaluate(lazy_script)
        except:
            pass
    
    def scroll_page(self, page, times=3):
        for _ in range(times):
            page.evaluate('window.scrollBy(0, 800)')
            time.sleep(random.uniform(0.5, 1.5))
        page.evaluate('window.scrollTo(0, 0)')
    
    def connect_to_browser(self):
        """连接到已打开的浏览器"""
        try:
            from playwright.sync_api import sync_playwright
            
            p = sync_playwright().start()
            self.browser = p.chromium.connect_over_cdp(f"http://localhost:{self.debug_port}")
            
            if self.browser.contexts:
                self.context = self.browser.contexts[0]
            else:
                self.context = self.browser.new_context()
            
            self.connected = True
            self.log(f"[Playwright] 已连接到浏览器 (端口 {self.debug_port})", "success")
            return True
        except Exception as e:
            self.log(f"[Playwright] 连接失败: {e}", "error")
            self.log("[Playwright] 请确保浏览器以调试模式启动", "warning")
            return False
    
    def launch_browser(self, headless=False):
        """启动新浏览器"""
        try:
            from playwright.sync_api import sync_playwright
            
            self.p = sync_playwright().start()
            self.browser = self.p.chromium.launch(
                headless=headless,
                args=['--disable-blink-features=AutomationControlled']
            )
            self.context = self.browser.new_context(
                viewport={'width': 1400, 'height': 900},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            self.connected = True
            self.log("[Playwright] 浏览器已启动", "success")
            return True
        except Exception as e:
            self.log(f"[Playwright] 启动失败: {e}", "error")
            return False
    
    def download(self, url, output_dir, filename=None):
        if not self.connected:
            if not self.launch_browser(headless=False):
                return None
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        try:
            self.log(f"[Playwright] 正在下载: {url}", "info")
            
            page = self.context.new_page()
            page.goto(url, timeout=60000, wait_until='networkidle')
            
            time.sleep(2)
            
            for _ in range(5):
                closed = self.close_login_modal(page)
                if closed > 0:
                    self.log(f"[Playwright] 关闭了 {closed} 个弹窗", "info")
                time.sleep(0.5)
            
            self.trigger_lazy_load(page)
            self.scroll_page(page, times=3)
            
            time.sleep(1)
            
            title = self.get_page_title(page)
            html = page.content()
            
            if not filename:
                filename = f"{title}.html"
            elif not filename.endswith('.html'):
                filename = f"{filename}.html"
            
            output_path = os.path.join(output_dir, filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            self.log(f"[Playwright] 已保存: {output_path} ({len(html):,} bytes)", "success")
            
            page.close()
            
            return output_path
            
        except Exception as e:
            self.log(f"[Playwright] 下载失败: {e}", "error")
            return None
    
    def download_multiple(self, urls, output_dir, callback=None):
        results = []
        
        for i, url in enumerate(urls):
            url = url.strip()
            if not url:
                continue
            
            self.log(f"[Playwright] [{i+1}/{len(urls)}] {url[:50]}...", "info")
            
            result = self.download(url, output_dir)
            results.append({'url': url, 'result': result, 'success': result is not None})
            
            if callback:
                callback(i + 1, len(urls), result)
            
            time.sleep(random.uniform(1, 3))
        
        return results
    
    def close(self):
        if self.browser:
            try:
                self.browser.close()
            except:
                pass
        self.connected = False
        self.log("[Playwright] 浏览器已关闭", "info")
```

### 步骤3：修改 gui.py 集成 Playwright

在 `gui.py` 顶部添加导入：
```python
from playwright_downloader import PlaywrightDownloader
```

在 `start_literature_download` 方法中，将：
```python
from singlefile_downloader import SingleFileDownloader
downloader = SingleFileDownloader(...)
```

改为：
```python
from playwright_downloader import PlaywrightDownloader
downloader = PlaywrightDownloader(...)
```

### 步骤4：添加浏览器连接功能（可选）

在 GUI 的文献下载区域添加按钮：

```python
ttk.Button(action_card, text="🔗 连接浏览器", 
          command=self.connect_browser).pack(fill="x", pady=5)
```

添加连接方法：
```python
def connect_browser(self):
    """连接到已打开的浏览器"""
    from playwright_downloader import PlaywrightDownloader
    downloader = PlaywrightDownloader(self)
    if downloader.connect_to_browser():
        self.literature_log("✅ 已连接到浏览器，现在可以下载了", "success")
    else:
        self.literature_log("❌ 连接失败，请先以调试模式启动浏览器", "error")
```

### 步骤5：启动调试模式浏览器（用户手动操作）

Chrome:
```bash
taskkill /F /IM chrome.exe
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\chrome_debug_profile"
```

Edge:
```bash
taskkill /F /IM msedge.exe
"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222 --user-data-dir="C:\edge_debug_profile"
```

## 测试验证
```python
from playwright_downloader import PlaywrightDownloader

downloader = PlaywrightDownloader()
downloader.launch_browser(headless=False)

result = downloader.download(
    'https://www.zhihu.com/question/1995071735683363267/answer/1997429833437814932',
    'test_output'
)
print(f"结果: {result}")

downloader.close()
```

## 注意事项
1. 首次使用需要运行 `playwright install chromium`
2. 连接已打开浏览器时，不要调用 `browser.close()`
3. 每次下载后可以关闭页面，但保持浏览器连接
4. 支持复用已登录的知乎账号
