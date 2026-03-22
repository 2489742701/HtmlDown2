"""
离线网页下载器 - 主程序入口

工作日志：
==========
[2026-02-17] 调试说明
- 如果打包后的程序无法启动或闪退，请尝试用源代码运行来查看详细错误：
  cd "项目目录"
  python main.py
- 源代码运行可以看到完整的错误堆栈和调试信息
- 常见问题：
  1. 模块缺失：检查spec文件中的hiddenimports是否完整
  2. 资源文件缺失：检查spec文件中的datas是否包含必要文件
  3. 激活问题：检查license_manager和secure_strings是否正确打包
  4. TCL/TK缺失：检查spec文件中是否包含tcl和tk目录
"""

import multiprocessing
import sys
import os

import tkinter as tk
import json
import traceback
import tempfile
import glob as glob_module
from gui import WebDownloaderGUI

def cleanup_pyinstaller_temp():
    if not (getattr(sys, 'frozen', False) or globals().get('__compiled__')):
        return
    try:
        temp_base = tempfile.gettempdir()
        patterns = ['_MEI*', '_MEIPASS*']
        for pattern in patterns:
            for temp_dir in glob_module.glob(os.path.join(temp_base, pattern)):
                try:
                    if os.path.isdir(temp_dir):
                        import shutil
                        shutil.rmtree(temp_dir, ignore_errors=True)
                except:
                    pass
    except:
        pass

def save_crash_log_main(module_name, error_info, context=None):
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
        print(f"Crash log saved: {crash_file}")
        return crash_file
    except:
        return None

def global_exception_handler(exc_type, exc_value, exc_tb):
    error_info = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(f"=== UNHANDLED EXCEPTION ===\n{error_info}")
    save_crash_log_main("main", error_info)
    sys.__excepthook__(exc_type, exc_value, exc_tb)

sys.excepthook = global_exception_handler

def check_activation():
    from license_manager import LicenseManager
    lm = LicenseManager()
    
    is_activated, msg = lm.check_activation()
    if is_activated:
        return True
    
    is_trial, remaining, trial_msg = lm.check_trial()
    
    if is_trial:
        trial_expired = False
        trial_remaining = remaining
        
        total = 200
        try:
            is_trial2, remaining2, total2 = lm.get_trial_status()
            if total2:
                total = total2
        except:
            pass
        
        used_count = total - remaining
        show_dialog = False
        
        if used_count > 0 and used_count % 5 == 0:
            show_dialog = True
        
        if not lm.should_show_activation_dialog() and not show_dialog:
            return True
        
        lm.mark_dialog_shown_today()
    else:
        trial_expired = True
        trial_remaining = 0
    
    from activation_dialog import ActivationDialog
    dialog = ActivationDialog(trial_expired=trial_expired, trial_remaining=trial_remaining)
    return dialog.show()

def run_preview_mode(config_file):
    """
    预览模式：直接运行预览窗口
    """
    from preview_helper import run_webview_preview
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        run_webview_preview(config)
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        import traceback
        traceback.print_exc()
        try:
            input("按任意键退出...")
        except:
            pass
    finally:
        try:
            if os.path.exists(config_file):
                os.remove(config_file)
        except:
            pass

if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    cleanup_pyinstaller_temp()
    
    if len(sys.argv) > 1 and sys.argv[1].endswith('.json'):
        try:
            run_preview_mode(sys.argv[1])
        finally:
            cleanup_pyinstaller_temp()
    else:
        if not check_activation():
            cleanup_pyinstaller_temp()
            sys.exit(0)
        
        root = tk.Tk()
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
        
        app = WebDownloaderGUI(root)
        
        # 导入动画模块
        from ui_animations import WindowAnimation
        
        # 标记是否正在关闭
        _is_closing = False
        
        def on_closing():
            global _is_closing
            if _is_closing:
                return
            _is_closing = True
            
            def do_close():
                try:
                    # 保存剪贴板内容
                    clipboard_content = None
                    try:
                        import pyperclip
                        clipboard_content = pyperclip.paste()
                    except:
                        pass
                    
                    # 销毁窗口并退出主循环
                    root.quit()  # 先退出mainloop
                    root.destroy()  # 再销毁窗口
                    
                    # 恢复剪贴板
                    if clipboard_content:
                        try:
                            import pyperclip
                            pyperclip.copy(clipboard_content)
                        except:
                            pass
                except Exception as e:
                    pass
                finally:
                    cleanup_pyinstaller_temp()
                    # 强制退出程序
                    import os
                    os._exit(0)
            
            # 使用淡出动画关闭窗口
            try:
                WindowAnimation.fade_out(root, duration=200, on_complete=do_close)
            except:
                # 如果动画失败，直接关闭
                do_close()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # 窗口淡入动画
        root.after(100, lambda: WindowAnimation.fade_in(root, duration=300))
        
        root.mainloop()
