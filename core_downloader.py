import os
import re
import time
import traceback
from urllib.parse import urljoin, urlparse, unquote
from io import BytesIO
import requests
from bs4 import BeautifulSoup
from PIL import Image
import concurrent.futures
from error_dialog import ErrorDialog

try:
    from fake_useragent import UserAgent
    _ua_available = True
except Exception:
    _ua_available = False
    UserAgent = None

def save_crash_log(module_name, error_info, context=None):
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

class CoreDownloader:
    def __init__(self, gui, params):
        self.gui = gui
        self.start_url = params['url']
        self.output_dir = params['output_dir']
        self.max_depth = params['depth']
        self.mode = params['mode']
        self.convert_images = params['convert_img']
        self.target_img_fmt = params['target_fmt']
        self.allow_img = params['filter_img']
        self.allow_video = params['filter_video']
        self.max_pages = params.get('max_pages', -1)
        self.pages_downloaded = 0
        self.is_first_page = True
        self.should_stop = False
        self.has_content = True
        self.is_single_page = params.get('is_single_page', False)
        
        if _ua_available and UserAgent:
            try:
                self.ua = UserAgent()
            except:
                self.ua = None
        else:
            self.ua = None
        self.visited_urls = set()
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        self.pages_dir = os.path.join(self.output_dir, 'pages')
        if not os.path.exists(self.pages_dir):
            os.makedirs(self.pages_dir)

        self.media_exts = {
            'img': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'],
            'video': ['.mp4', '.webm', '.mkv', '.avi', '.mov']
        }

    def log(self, msg, tag="info"):
        self.gui.root.after(0, lambda: self.gui.log(msg, tag))

    def get_headers(self, url=None):
        user_agent = self.ua.random if self.ua else 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }
        if url:
            parsed = urlparse(url)
            if parsed.netloc:
                headers['Host'] = parsed.netloc
        if self.start_url:
            headers['Referer'] = self.start_url
        return headers

    def safe_filename(self, url):
        path = urlparse(url).path
        filename = unquote(os.path.basename(path))
        if not filename or '.' not in filename:
            filename = f"file_{int(time.time())}.dat"
        filename = re.sub(r'[\\/*?:"<>|]', "", filename)
        if len(filename) > 100:
            filename = filename[-50:]
        return filename

    def download_resource(self, url, sub_folder):
        if self.should_stop:
            return None
        try:
            is_video = any(url.lower().endswith(ext) for ext in self.media_exts['video'])
            is_img = any(url.lower().endswith(ext) for ext in self.media_exts['img'])
            
            if is_video and not self.allow_video:
                return None
            if is_img and not self.allow_img:
                return None
            if not is_video and not is_img and self.mode == 'media_only':
                return None

            folder_path = os.path.join(self.output_dir, sub_folder)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            
            filename = self.safe_filename(url)
            local_path = os.path.join(folder_path, filename)
            relative_path = f"{sub_folder}/{filename}"

            if os.path.exists(local_path):
                return relative_path

            self.log(f"   ⬇️ {filename}", "info")
            resp = requests.get(url, headers=self.get_headers(url), stream=True, timeout=15, verify=False)
            
            if resp.status_code == 200:
                if is_img and self.convert_images:
                    try:
                        img = Image.open(BytesIO(resp.content))
                        fname_no_ext = os.path.splitext(filename)[0]
                        new_fname = f"{fname_no_ext}.{self.target_img_fmt.lower()}"
                        local_path = os.path.join(folder_path, new_fname)
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")
                        img.save(local_path, self.target_img_fmt)
                        return f"{sub_folder}/{new_fname}"
                    except Exception as img_error:
                        self.log(f"   ⚠️ 图片转换失败: {img_error}", "warning")

                with open(local_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                return relative_path
            else:
                self.log(f"   ⚠️ 下载失败: HTTP {resp.status_code}", "warning")
        except requests.exceptions.ConnectionError as e:
            self.log(f"   ⚠️ 连接错误: {url}", "warning")
        except requests.exceptions.Timeout as e:
            self.log(f"   ⚠️ 超时: {url}", "warning")
        except Exception as e:
            self.log(f"   ⚠️ 下载错误: {str(e)}", "warning")
        return None

    def _enable_user_select(self, soup):
        try:
            for style in soup.find_all('style'):
                if style.string:
                    content = style.string
                    content = re.sub(r'user-select\s*:\s*none\s*;?', 'user-select: text;', content, flags=re.IGNORECASE)
                    content = re.sub(r'-webkit-user-select\s*:\s*none\s*;?', '-webkit-user-select: text;', content, flags=re.IGNORECASE)
                    content = re.sub(r'-moz-user-select\s*:\s*none\s*;?', '-moz-user-select: text;', content, flags=re.IGNORECASE)
                    content = re.sub(r'-ms-user-select\s*:\s*none\s*;?', '-ms-user-select: text;', content, flags=re.IGNORECASE)
                    content = re.sub(r'-khtml-user-select\s*:\s*none\s*;?', '-khtml-user-select: text;', content, flags=re.IGNORECASE)
                    style.string = content
            
            for element in soup.find_all(style=True):
                style = element.get('style', '')
                if 'user-select' in style.lower():
                    style = re.sub(r'user-select\s*:\s*none\s*;?', 'user-select: text;', style, flags=re.IGNORECASE)
                    style = re.sub(r'-webkit-user-select\s*:\s*none\s*;?', '-webkit-user-select: text;', style, flags=re.IGNORECASE)
                    style = re.sub(r'-moz-user-select\s*:\s*none\s*;?', '-moz-user-select: text;', style, flags=re.IGNORECASE)
                    style = re.sub(r'-ms-user-select\s*:\s*none\s*;?', '-ms-user-select: text;', style, flags=re.IGNORECASE)
                    element['style'] = style
            
            enable_style = soup.new_tag('style')
            enable_style.string = '''
html, body, div, p, span, h1, h2, h3, h4, h5, h6, article, section, main, pre, code {
    -webkit-user-select: text !important;
    -moz-user-select: text !important;
    -ms-user-select: text !important;
    user-select: text !important;
}
'''
            if soup.head:
                soup.head.append(enable_style)
            elif soup.html:
                soup.html.insert(0, enable_style)
            
            self.log("   ✅ 已启用文本选择功能", "info")
        except Exception as e:
            self.log(f"   ⚠️ 启用文本选择失败: {e}", "warning")

    def _hide_ads(self, soup):
        try:
            ad_selectors = [
                '.container-download', '.container-fluid-flex',
                '[class*="ad-"]', '[class*="ads-"]', '[class*="advert"]',
                '[class*="banner"]', '[id*="ad-"]', '[id*="ads-"]',
                '.recommend-box', '.recommend-list',
                '.comment-box', '.comment-list',
                '.tool-box', '.toolbox',
                '.article-bar-bottom', '.right-side',
                '.csdn-side-toolbar', '.side-toolbar',
                '[data-report-view*="popu_36"]',
                '[data-report-click*="popu_36"]',
                '.passport-login-container', '.passport-login-mark',
                '.login-mark', '.login-box'
            ]
            
            hidden_count = 0
            for selector in ad_selectors:
                try:
                    for element in soup.select(selector):
                        if element.name:
                            element['style'] = element.get('style', '') + 'display: none !important;'
                            hidden_count += 1
                except:
                    pass
            
            hide_style = soup.new_tag('style')
            hide_style.string = '''
.container-download, .container-fluid-flex,
[class*="ad-"], [class*="ads-"], [class*="advert"],
[class*="banner"], [id*="ad-"], [id*="ads-"],
.recommend-box, .recommend-list,
.comment-box, .comment-list,
.tool-box, .toolbox,
.article-bar-bottom, .right-side,
.csdn-side-toolbar, .side-toolbar,
.passport-login-container, .passport-login-mark,
.login-mark, .login-box {
    display: none !important;
}
'''
            if soup.head:
                soup.head.append(hide_style)
            
            if hidden_count > 0:
                self.log(f"   🙈 已隐藏 {hidden_count} 个广告/干扰元素", "info")
        except Exception as e:
            self.log(f"   ⚠️ 隐藏广告失败: {e}", "warning")

    def post_process_html(self, html_content, base_url, is_subpage=False):
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            self._enable_user_select(soup)
            self._hide_ads(soup)
            
            if is_subpage:
                path_prefix = '../'
            else:
                path_prefix = ''
            
            for script in soup.find_all('script'):
                src = script.get('src')
                if src and not src.startswith('data:'):
                    abs_url = urljoin(base_url, src)
                    script_filename = self.safe_filename(abs_url)
                    script_path = os.path.join(self.output_dir, 'js', script_filename)
                    
                    if os.path.exists(script_path):
                        script['src'] = f"{path_prefix}js/{script_filename}"
                        self.log(f"   🔧 修复脚本引用: {script_filename}", "info")
                    else:
                        rel_path = self.download_resource(abs_url, 'js')
                        if rel_path:
                            script['src'] = f"{path_prefix}{rel_path}"
                            self.log(f"   ⬇️ 补充下载脚本: {script_filename}", "info")
            
            for link in soup.find_all('link'):
                href = link.get('href')
                rel = link.get('rel', [])
                if href and not href.startswith('data:') and 'stylesheet' in (rel if isinstance(rel, list) else [rel]):
                    abs_url = urljoin(base_url, href)
                    link_filename = self.safe_filename(abs_url)
                    link_path = os.path.join(self.output_dir, 'css', link_filename)
                    
                    if os.path.exists(link_path):
                        link['href'] = f"{path_prefix}css/{link_filename}"
                        self.log(f"   🔧 修复样式引用: {link_filename}", "info")
                    else:
                        rel_path = self.download_resource(abs_url, 'css')
                        if rel_path:
                            link['href'] = f"{path_prefix}{rel_path}"
                            self.log(f"   ⬇️ 补充下载样式: {link_filename}", "info")
            
            for style in soup.find_all('style'):
                if style.string:
                    style_content = style.string
                    import re
                    def replace_url(match):
                        url = match.group(1)
                        if url.startswith('data:'):
                            return match.group(0)
                        abs_url = urljoin(base_url, url)
                        filename = self.safe_filename(abs_url)
                        rel_path = self.download_resource(abs_url, 'images')
                        if rel_path:
                            return f'url({path_prefix}{rel_path})'
                        return match.group(0)
                    
                    style_content = re.sub(r'url\(["\']?([^)"\']+)["\']?\)', replace_url, style_content)
                    style.string = style_content
            
            for img in soup.find_all('img'):
                src = img.get('src')
                if src and not src.startswith('data:'):
                    abs_url = urljoin(base_url, src)
                    img_filename = self.safe_filename(abs_url)
                    img_path = os.path.join(self.output_dir, 'images', img_filename)
                    
                    if os.path.exists(img_path):
                        img['src'] = f"{path_prefix}images/{img_filename}"
                        self.log(f"   🔧 修复图片引用: {img_filename}", "info")
                    else:
                        rel_path = self.download_resource(abs_url, 'images')
                        if rel_path:
                            img['src'] = f"{path_prefix}{rel_path}"
                            self.log(f"   ⬇️ 补充下载图片: {img_filename}", "info")
            
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('#'):
                    continue
                
                abs_url = urljoin(base_url, href)
                
                if urlparse(abs_url).netloc == urlparse(self.start_url).netloc:
                    page_filename = self.safe_filename(abs_url)
                    if not page_filename.endswith('.html'):
                        page_filename += '.html'
                    
                    if abs_url == self.start_url:
                        if is_subpage:
                            a['href'] = "../index.html"
                        else:
                            a['href'] = "index.html"
                        self.log(f"   🔧 修复主页链接: {'../index.html' if is_subpage else 'index.html'}", "info")
                    else:
                        if is_subpage:
                            a['href'] = page_filename
                        else:
                            a['href'] = f"pages/{page_filename}"
                        self.log(f"   🔧 修复页面链接: {page_filename if is_subpage else 'pages/' + page_filename}", "info")
                else:
                    a['target'] = '_blank'
                    self.log(f"   🔗 外域链接: {href}", "info")
            
            return str(soup)
        except Exception as e:
            self.log(f"   ⚠️ HTML后处理失败: {e}", "warning")
            return html_content

    def process_page(self, url, depth):
        if self.should_stop:
            self.log("⏹️ 下载任务已终止", "warning")
            return
        
        if url in self.visited_urls or depth > self.max_depth:
            if url in self.visited_urls:
                self.log(f"⏭️ 跳过已访问: {url}", "info")
            if depth > self.max_depth:
                self.log(f"⏭️ 跳过超深度: {url} (深度{depth} > {self.max_depth})", "info")
            return
        
        if self.max_pages != -1 and self.pages_downloaded >= self.max_pages:
            self.log(f"⚠️ 已达到最大页数限制: {self.max_pages}页", "warning")
            return
        
        self.visited_urls.add(url)
        self.pages_downloaded += 1
        
        self.log(f"🌍 分析页面 [深度{depth}][第{self.pages_downloaded}页]: {url}", "info")
        requests.packages.urllib3.disable_warnings()
        
        max_retries = 3
        last_error = None
        for attempt in range(max_retries):
            try:
                time.sleep(1 + attempt * 2)
                resp = requests.get(url, headers=self.get_headers(url), verify=False, timeout=15)
                if resp.status_code != 200:
                    return
                
                soup = BeautifulSoup(resp.text, 'lxml')
                
                tags_to_find = [
                    ('img', 'src', 'images'),
                    ('video', 'src', 'videos'),
                    ('source', 'src', 'videos')
                ]
                if self.mode == 'full':
                    tags_to_find.extend([('script', 'src', 'js'), ('link', 'href', 'css')])

                futures = []
                with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                    for tag_name, attr, folder in tags_to_find:
                        for tag in soup.find_all(tag_name):
                            if self.should_stop:
                                break
                            if tag_name == 'link':
                                rel = tag.get('rel', [])
                                if 'stylesheet' not in (rel if isinstance(rel, list) else [rel]):
                                    continue
                            val = tag.get(attr)
                            if val and not val.startswith('data:'):
                                abs_url = urljoin(url, val)
                                f = executor.submit(self.download_resource, abs_url, folder)
                                futures.append((tag, attr, f))

                    if self.mode == 'full' and not self.should_stop:
                        for tag, attr, f in futures:
                            if self.should_stop:
                                break
                            rel_path = f.result()
                            if rel_path:
                                tag[attr] = rel_path
                        
                        if self.should_stop:
                            return
                        
                        if self.is_first_page:
                            page_name = 'index.html'
                            page_path = os.path.join(self.output_dir, page_name)
                            is_subpage = False
                            self.is_first_page = False
                            self.log(f"✅ 保存主页: {page_name}", "success")
                        else:
                            page_name = self.safe_filename(url)
                            if not page_name.endswith('.html'):
                                page_name += '.html'
                            page_path = os.path.join(self.pages_dir, page_name)
                            is_subpage = True
                            self.log(f"✅ 保存二级页面: pages/{page_name}", "success")
                        
                        processed_html = self.post_process_html(str(soup), url, is_subpage)
                        
                        text_content = soup.get_text(strip=True)
                        if len(text_content) < 100:
                            self.has_content = False
                            self.log(f"⚠️ 页面内容过少 ({len(text_content)}字符)，可能存在反爬虫机制", "warning")
                        
                        with open(page_path, 'w', encoding='utf-8') as f:
                            f.write(processed_html)

                if depth < self.max_depth and not self.is_single_page:
                    links = soup.find_all('a', href=True)
                    self.log(f"🔗 找到 {len(links)} 个链接", "info")
                    for link in links:
                        if self.should_stop:
                            self.log("⏹️ 下载任务已终止", "warning")
                            break
                        next_url = urljoin(url, link['href'])
                        if urlparse(next_url).netloc == urlparse(self.start_url).netloc:
                            self.log(f"📌 发现同域链接: {next_url}", "info")
                            self.process_page(next_url, depth + 1)
                        else:
                            self.log(f"⏭️ 跳过外域链接: {next_url}", "info")
                
                break
                
            except requests.exceptions.SSLError as e:
                last_error = e
                self.log(f"⚠️ SSL错误，重试 {attempt + 1}/{max_retries}: {url}", "warning")
                continue
            except requests.exceptions.ConnectionError as e:
                last_error = e
                self.log(f"⚠️ 连接错误，重试 {attempt + 1}/{max_retries}: {url}", "warning")
                continue
            except requests.exceptions.Timeout as e:
                last_error = e
                self.log(f"⚠️ 超时错误，重试 {attempt + 1}/{max_retries}: {url}", "warning")
                continue
            except Exception as e:
                error_msg = f"页面处理错误: {str(e)}"
                error_details = traceback.format_exc()
                self.log(f"❌ 页面错误: {e}", "error")
                self.log(f"❌ 错误详情: {error_details}", "error")
                
                context = f"URL: {url}\nDepth: {depth}\nPages downloaded: {self.pages_downloaded}"
                save_crash_log("core_downloader", error_details, context)
                
                if "FakeUserAgentError" in str(e):
                    self.log(f"⚠️ User-Agent错误，使用默认UA", "warning")
                    self.ua = None
                else:
                    self.gui.root.after(0, lambda: ErrorDialog(self.gui.root, "处理错误", error_msg, error_details))
                return
        
        if last_error and attempt == max_retries - 1:
            error_msg = f"重试{max_retries}次后仍失败: {str(last_error)}"
            error_details = traceback.format_exc()
            self.log(f"❌ {error_msg}", "error")
            self.gui.root.after(0, lambda: ErrorDialog(self.gui.root, "网络错误", error_msg, error_details))

    def start(self):
        self.process_page(self.start_url, 0)
        return self.has_content
    
    def stop(self):
        self.should_stop = True
