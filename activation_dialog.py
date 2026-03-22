import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

def get_resource_path(relative_path):
    """获取资源文件的绝对路径，兼容开发环境和打包环境"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包后的临时目录
        return os.path.join(sys._MEIPASS, relative_path)
    elif hasattr(sys, 'frozen'):
        # Nuitka 打包模式（单文件或文件夹模式）
        exe_dir = os.path.dirname(sys.executable)
        # 首先检查 _internal 目录（Nuitka 文件夹模式）
        internal_path = os.path.join(exe_dir, '_internal', relative_path)
        if os.path.exists(internal_path):
            return internal_path
        # 然后检查直接路径
        direct_path = os.path.join(exe_dir, relative_path)
        if os.path.exists(direct_path):
            return direct_path
        return internal_path
    else:
        # 开发环境
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

class ActivationDialog:
    def __init__(self, parent=None, trial_expired=False, trial_remaining=0):
        self.result = False
        self.trial_expired = trial_expired
        self.trial_remaining = trial_remaining
        self.root = tk.Tk() if parent is None else tk.Toplevel(parent)
        
        if parent is None:
            self.root.title("离线网页下载器 - 激活")
        else:
            self.root.title("激活程序")
        
        self.root.geometry("600x320")
        self.root.resizable(False, False)
        self.root.configure(bg="#f5f5f5")
        
        # 初始隐藏，等待动画
        if parent:
            self.root.withdraw()
        
        self._center_window()
        self._create_widgets()
        
        if parent:
            self.root.transient(parent)
            self.root.grab_set()
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # 淡入动画
        if parent:
            self.root.after(50, self._fade_in)
    
    def _center_window(self):
        self.root.update_idletasks()
        width = 600
        height = 320
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def _fade_in(self):
        """淡入动画"""
        try:
            from ui_animations import WindowAnimation
            WindowAnimation.fade_in(self.root, duration=300)
        except:
            self.root.deiconify()
    
    def _fade_out_and_close(self):
        """淡出并关闭"""
        try:
            from ui_animations import WindowAnimation
            def do_close():
                self.result = False
                try:
                    self.root.destroy()
                except:
                    pass
            WindowAnimation.fade_out(self.root, duration=200, on_complete=do_close)
        except:
            self.result = False
            try:
                self.root.destroy()
            except:
                pass
    
    def _create_widgets(self):
        main_frame = tk.Frame(self.root, bg="#f5f5f5", padx=30, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        title_label = tk.Label(
            main_frame,
            text="🔐 程序激活",
            font=("Microsoft YaHei", 18, "bold"),
            bg="#f5f5f5",
            fg="#333"
        )
        title_label.pack(pady=(0, 5))
        
        if self.trial_expired:
            subtitle_text = "试用次数已用完，请输入卡密激活"
            subtitle_color = "#e74c3c"
        elif self.trial_remaining > 0:
            subtitle_text = f"剩余 {self.trial_remaining} 次启动，输入卡密可永久激活"
            subtitle_color = "#f39c12"
        else:
            subtitle_text = "请输入卡密以激活程序"
            subtitle_color = "#666"
        
        subtitle_label = tk.Label(
            main_frame,
            text=subtitle_text,
            font=("Microsoft YaHei", 11),
            bg="#f5f5f5",
            fg=subtitle_color
        )
        subtitle_label.pack(pady=(0, 15))
        
        content_frame = tk.Frame(main_frame, bg="#f5f5f5")
        content_frame.pack(fill="x", expand=True)
        
        machine_frame = tk.LabelFrame(content_frame, text="机器码", font=("Microsoft YaHei", 10), bg="#f5f5f5", padx=15, pady=8)
        machine_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        from license_manager import LicenseManager
        lm = LicenseManager()
        machine_id = lm.get_machine_id_display()
        
        machine_label = tk.Label(
            machine_frame,
            text=machine_id,
            font=("Consolas", 12),
            bg="#e8e8e8",
            fg="#333",
            padx=10,
            pady=5
        )
        machine_label.pack(fill="x")
        
        copy_btn = ttk.Button(
            machine_frame,
            text="复制机器码",
            command=lambda: self._copy_machine_id(machine_id),
            width=12
        )
        copy_btn.pack(pady=(8, 0))
        
        key_frame = tk.LabelFrame(content_frame, text="卡密", font=("Microsoft YaHei", 10), bg="#f5f5f5", padx=15, pady=8)
        key_frame.pack(side="right", fill="both", expand=True)
        
        self.key_var = tk.StringVar()
        self.key_entry = ttk.Entry(
            key_frame,
            textvariable=self.key_var,
            font=("Consolas", 14),
            width=30,
            justify="center"
        )
        self.key_entry.pack(fill="x", pady=(0, 8))
        self.key_entry.focus_set()
        
        self.key_entry.bind("<Return>", lambda e: self._activate())
        
        activate_btn = ttk.Button(
            key_frame,
            text="激活",
            command=self._activate,
            width=12
        )
        activate_btn.pack()
        
        btn_frame = tk.Frame(main_frame, bg="#f5f5f5")
        btn_frame.pack(fill="x", pady=(15, 0))
        
        if not self.trial_expired and self.trial_remaining > 0:
            trial_btn = ttk.Button(
                btn_frame,
                text=f"试用（剩余 {self.trial_remaining} 次）",
                command=self._use_trial,
                width=20
            )
            trial_btn.pack(side="left")
        
        forget_btn = ttk.Button(
            btn_frame,
            text="忘记密码",
            command=self._show_forget_password,
            width=12
        )
        forget_btn.pack(side="left", padx=10)
        
        exit_btn = ttk.Button(
            btn_frame,
            text="退出",
            command=self._on_close,
            width=12
        )
        exit_btn.pack(side="right")
        
        self.status_label = tk.Label(
            main_frame,
            text="",
            font=("Microsoft YaHei", 10),
            bg="#f5f5f5",
            fg="#e74c3c"
        )
        self.status_label.pack(pady=(10, 0))
    
    def _use_trial(self):
        self.result = True
        self.root.destroy()
    
    def _show_forget_password(self):
        forget_window = tk.Toplevel(self.root)
        forget_window.title("忘记密码")
        forget_window.geometry("500x450")
        forget_window.resizable(False, False)
        forget_window.configure(bg="#f5f5f5")
        
        icon_path = get_resource_path('assets/icon.ico')
        if os.path.exists(icon_path):
            try:
                forget_window.iconbitmap(icon_path)
            except Exception as e:
                print(f"[Error] Cannot load forget password window icon: {e}")
        
        forget_window.transient(self.root)
        forget_window.grab_set()
        
        x = (forget_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (forget_window.winfo_screenheight() // 2) - (450 // 2)
        forget_window.geometry(f"500x450+{x}+{y}")
        
        title_label = tk.Label(
            forget_window,
            text="🔑 忘记密码",
            font=("Microsoft YaHei", 16, "bold"),
            bg="#f5f5f5",
            fg="#333"
        )
        title_label.pack(pady=(20, 15))
        
        info_frame = tk.Frame(forget_window, bg="#fff3cd", padx=20, pady=15)
        info_frame.pack(fill="x", padx=20, pady=10)
        
        info_text = tk.Label(
            info_frame,
            text="如果您忘记了激活密码，请在此输入您的留言：",
            font=("Microsoft YaHei", 11),
            bg="#fff3cd",
            fg="#856404",
            justify="left",
            wraplength=440
        )
        info_text.pack(anchor="w")
        
        text_frame = tk.Frame(forget_window, bg="#f5f5f5")
        text_frame.pack(fill="x", padx=20, pady=10)
        
        text_label = tk.Label(
            text_frame,
            text="留言内容：",
            font=("Microsoft YaHei", 10),
            bg="#f5f5f5",
            fg="#666"
        )
        text_label.pack(anchor="w")
        
        text_content = tk.Text(
            text_frame,
            height=10,
            width=50,
            font=("Microsoft YaHei", 10),
            relief="solid",
            bd=1,
            bg="white",
            fg="#333"
        )
        text_content.pack(pady=5)
        
        text_content.insert("1.0", "")
        
        close_btn = ttk.Button(
            forget_window,
            text="关闭",
            command=forget_window.destroy,
            width=12
        )
        close_btn.pack(pady=15)
    
    def _copy_machine_id(self, machine_id):
        self.root.clipboard_clear()
        self.root.clipboard_append(machine_id)
        self.status_label.config(text="机器码已复制到剪贴板", fg="#27ae60")
    
    def _activate(self):
        key = self.key_var.get().strip()
        
        if not key:
            self.status_label.config(text="请输入卡密", fg="#e74c3c")
            return
        
        from license_manager import LicenseManager
        lm = LicenseManager()
        
        if not lm.validate_card_key(key):
            self.status_label.config(text="卡密无效，请检查后重试", fg="#e74c3c")
            return
        
        if lm.save_activation(key):
            self.result = True
            messagebox.showinfo("激活成功", "程序已成功激活！\n\n感谢您的使用。")
            self.root.destroy()
        else:
            self.status_label.config(text="激活失败，请重试", fg="#e74c3c")
    
    def _on_close(self):
        self._fade_out_and_close()
    
    def show(self):
        if isinstance(self.root, tk.Tk):
            self.root.mainloop()
        else:
            self.root.wait_window()
        return self.result


def check_and_activate(parent=None):
    from license_manager import LicenseManager
    lm = LicenseManager()
    
    is_activated, message = lm.check_activation()
    
    if is_activated:
        return True
    
    dialog = ActivationDialog(parent)
    return dialog.show()


if __name__ == "__main__":
    if check_and_activate():
        print("程序已激活，可以运行主程序")
    else:
        print("程序未激活，退出")
