import os
import sys
import subprocess
import shutil

def is_frozen():
    return getattr(sys, 'frozen', False) or globals().get('__compiled__') is not None

def get_base_path():
    if is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_browsers_path():
    base_dir = get_base_path()
    return os.path.join(base_dir, 'browsers')

def get_chromium_path():
    browsers_path = get_browsers_path()
    for item in os.listdir(browsers_path) if os.path.exists(browsers_path) else []:
        if item.startswith('chromium-'):
            chromium_dir = os.path.join(browsers_path, item, 'chrome-win64')
            if os.path.exists(os.path.join(chromium_dir, 'chrome.exe')):
                return chromium_dir
    return None

def check_browser_integrity():
    chromium_path = get_chromium_path()
    if not chromium_path:
        return False, "浏览器目录不存在"
    
    required_files = [
        'chrome.exe',
        'chrome.dll',
        'icudtl.dat',
        'resources.pak'
    ]
    
    missing_files = []
    for f in required_files:
        if not os.path.exists(os.path.join(chromium_path, f)):
            missing_files.append(f)
    
    if missing_files:
        return False, f"缺少文件: {', '.join(missing_files)}"
    
    return True, "浏览器完整"

def is_browser_ready():
    is_valid, _ = check_browser_integrity()
    return is_valid

def download_browser(progress_callback=None, use_mirror=True):
    browsers_path = get_browsers_path()
    os.makedirs(browsers_path, exist_ok=True)
    
    env = os.environ.copy()
    env['PLAYWRIGHT_BROWSERS_PATH'] = browsers_path
    
    if use_mirror:
        pass
    
    if is_frozen():
        try:
            from playwright._impl._driver import compute_driver_executable, get_driver_env
            from playwright._repo_version import version as pw_version
            
            driver_executable = compute_driver_executable()
            
            if isinstance(driver_executable, tuple):
                node_exe, cli_js = driver_executable
                if not os.path.exists(node_exe) or not os.path.exists(cli_js):
                    if progress_callback:
                        progress_callback("初始化 Playwright 驱动...")
                    return False
                driver_path = node_exe
                cli_path = cli_js
            elif hasattr(driver_executable, 'exists'):
                if not driver_executable.exists():
                    if progress_callback:
                        progress_callback("初始化 Playwright 驱动...")
                    return False
                driver_path = str(driver_executable)
                cli_path = None
            else:
                driver_path = str(driver_executable)
                cli_path = None
                if not os.path.exists(driver_path):
                    if progress_callback:
                        progress_callback("初始化 Playwright 驱动...")
                    return False
            
            env.update(get_driver_env())
            
            if progress_callback:
                progress_callback("正在下载浏览器...")
            
            if cli_path:
                cmd = [driver_path, cli_path, 'install', 'chromium']
            else:
                cmd = [driver_path, 'install', 'chromium']
            
            print(f"[browser_manager] 执行: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                encoding='utf-8',
                errors='replace'
            )
            
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    print(f"[playwright] {line.strip()}")
                    if progress_callback:
                        clean_line = line.replace('■', '🟦').replace('□', '⬜').strip()
                        if clean_line:
                            progress_callback(clean_line)
            
            print(f"[browser_manager] 返回码: {process.returncode}")
            
            if process.returncode == 0:
                if progress_callback:
                    progress_callback("下载完成")
                return True
            else:
                if progress_callback:
                    progress_callback("下载失败")
                return False
                
        except Exception as e:
            if progress_callback:
                progress_callback(f"下载失败: {e}")
            print(f"[browser_manager] 打包模式下载错误: {e}")
            return False
    else:
        cmd = [sys.executable, '-m', 'playwright', 'install', 'chromium']
        
        if progress_callback:
            progress_callback(f"执行: {' '.join(cmd)}")
            progress_callback(f"PLAYWRIGHT_BROWSERS_PATH: {browsers_path}")
        
        print(f"[browser_manager] 下载命令: {' '.join(cmd)}")
        print(f"[browser_manager] 浏览器路径: {browsers_path}")
        
        try:
            process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                encoding='utf-8',
                errors='replace'
            )
            
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    print(f"[playwright] {line.strip()}")
                    if progress_callback:
                        progress_callback(line.strip())
            
            print(f"[browser_manager] 下载返回码: {process.returncode}")
            
            if process.returncode == 0:
                if os.path.exists(browsers_path):
                    print(f"[browser_manager] 浏览器目录内容: {os.listdir(browsers_path)}")
            
            return process.returncode == 0
        except Exception as e:
            if progress_callback:
                progress_callback(f"下载失败: {e}")
            print(f"[browser_manager] 下载异常: {e}")
            return False

def setup_browser_env():
    browsers_path = get_browsers_path()
    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = browsers_path
    return browsers_path
