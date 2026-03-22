import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import traceback

class ErrorDialog:
    def __init__(self, parent, title, message, details=None):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("550x400")
        self.dialog.configure(bg="#f5f5f5")
        self.dialog.resizable(True, True)
        
        # 初始设置为透明，等待动画
        self.dialog.withdraw()
        
        icon_path = self._get_icon_path()
        if icon_path:
            try:
                self.dialog.iconbitmap(icon_path)
            except:
                pass
        
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 10))
        
        error_icon = ttk.Label(header_frame, text="❌", 
                              font=("Microsoft YaHei", 20))
        error_icon.pack(side="left", padx=(0, 10))
        
        title_label = ttk.Label(header_frame, text=title,
                               font=("Microsoft YaHei", 12, "bold"),
                               foreground="#e74c3c")
        title_label.pack(side="left")
        
        message_frame = ttk.LabelFrame(main_frame, text=" 错误信息 ", padding=10)
        message_frame.pack(fill="x", pady=(0, 10))
        
        message_label = ttk.Label(message_frame, text=message,
                                 font=("Microsoft YaHei", 10),
                                 foreground="#34495e",
                                 wraplength=480)
        message_label.pack(anchor="w")
        
        if details:
            details_frame = ttk.LabelFrame(main_frame, text=" 详细信息 ", padding=10)
            details_frame.pack(fill="both", expand=True, pady=(0, 10))
            
            details_text = scrolledtext.ScrolledText(details_frame,
                                                     height=10,
                                                     font=("Consolas", 9),
                                                     bg="#f8f9fa",
                                                     wrap="word")
            details_text.pack(fill="both", expand=True)
            details_text.insert("1.0", details)
            details_text.config(state="disabled")
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x")
        
        copy_btn = ttk.Button(button_frame, text="📋 复制错误信息",
                             command=lambda: self._copy_to_clipboard(message, details),
                             width=15)
        copy_btn.pack(side="left", padx=(0, 10))
        
        # 使用动画关闭
        close_btn = ttk.Button(button_frame, text="关闭",
                              command=self._close_with_animation,
                              width=10)
        close_btn.pack(side="right")
        
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.focus_set()
        
        close_btn.focus_set()
        
        self.dialog.bind("<Escape>", lambda e: self._close_with_animation())
        self.dialog.bind("<Return>", lambda e: self._close_with_animation())
        
        # 淡入动画
        self._fade_in()
    
    def _fade_in(self):
        """淡入动画"""
        try:
            from ui_animations import WindowAnimation
            WindowAnimation.fade_in(self.dialog, duration=250)
        except:
            self.dialog.deiconify()
    
    def _close_with_animation(self):
        """带动画的关闭"""
        try:
            from ui_animations import WindowAnimation
            def do_close():
                try:
                    self.dialog.destroy()
                except:
                    pass
            WindowAnimation.fade_out(self.dialog, duration=150, on_complete=do_close)
        except:
            self.dialog.destroy()
    
    def _get_icon_path(self):
        import os
        import sys
        try:
            if getattr(sys, 'frozen', False) or globals().get('__compiled__'):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(__file__)
            return os.path.join(base_path, 'assets', 'icon.ico')
        except:
            return None
    
    def _copy_to_clipboard(self, message, details):
        try:
            full_text = f"错误信息: {message}\n\n"
            if details:
                full_text += f"详细信息:\n{details}"
            
            self.dialog.clipboard_clear()
            self.dialog.clipboard_append(full_text)
            self.dialog.update()
            
            messagebox.showinfo("提示", "错误信息已复制到剪贴板")
        except Exception as e:
            messagebox.showerror("错误", f"复制失败: {str(e)}")


def show_error(parent, title, message, details=None):
    return ErrorDialog(parent, title, message, details)


def show_exception(parent, title, exception):
    message = str(exception)
    details = traceback.format_exc()
    return ErrorDialog(parent, title, message, details)
