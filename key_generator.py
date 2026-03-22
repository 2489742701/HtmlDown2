import tkinter as tk
from tkinter import ttk, messagebox
import hashlib
import secrets
import string
import pyperclip

class KeyGenerator:
    SECRET_KEY = "WXxK9mP2vQ8nL3jH5tR7yF1cB4dS6aE0"
    
    def generate_key(self, machine_id):
        clean_id = machine_id.replace("-", "").upper()
        if len(clean_id) < 16:
            clean_id = clean_id.ljust(16, "0")
        
        combined = f"{clean_id[:16]}-{self.SECRET_KEY}"
        hash_part = hashlib.sha256(combined.encode()).hexdigest()[:8].upper()
        
        random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
        
        card_key = f"WX-{hash_part}-{random_part}"
        return card_key
    
    def verify_key(self, machine_id, card_key):
        if not card_key.startswith("WX-") or len(card_key) < 12:
            return False
        return True


class KeyGeneratorApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("卡密生成器")
        self.root.geometry("450x320")
        self.root.resizable(False, False)
        self.root.configure(bg="#f5f5f5")
        
        self._center_window()
        self._create_widgets()
        
        self.generator = KeyGenerator()
    
    def _center_window(self):
        self.root.update_idletasks()
        width = 450
        height = 320
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        title_label = tk.Label(
            main_frame,
            text="🔑 卡密生成器",
            font=("Microsoft YaHei", 16, "bold"),
            bg="#f5f5f5",
            fg="#333"
        )
        title_label.pack(pady=(0, 15))
        
        input_frame = ttk.LabelFrame(main_frame, text="机器码", padding="10")
        input_frame.pack(fill="x", pady=(0, 10))
        
        self.machine_id_var = tk.StringVar()
        self.machine_entry = ttk.Entry(
            input_frame,
            textvariable=self.machine_id_var,
            font=("Consolas", 11),
            width=45
        )
        self.machine_entry.pack(fill="x")
        
        btn_frame1 = ttk.Frame(input_frame)
        btn_frame1.pack(fill="x", pady=(5, 0))
        
        ttk.Button(btn_frame1, text="粘贴", command=self._paste_machine_id, width=10).pack(side="left")
        ttk.Button(btn_frame1, text="生成卡密", command=self._generate_key, width=15).pack(side="right")
        
        output_frame = ttk.LabelFrame(main_frame, text="生成的卡密", padding="10")
        output_frame.pack(fill="x", pady=(0, 10))
        
        self.key_var = tk.StringVar()
        self.key_entry = ttk.Entry(
            output_frame,
            textvariable=self.key_var,
            font=("Consolas", 12),
            width=45,
            state="readonly"
        )
        self.key_entry.pack(fill="x")
        
        btn_frame2 = ttk.Frame(output_frame)
        btn_frame2.pack(fill="x", pady=(5, 0))
        
        ttk.Button(btn_frame2, text="复制卡密", command=self._copy_key, width=15).pack(side="right")
        
        self.status_label = tk.Label(
            main_frame,
            text="",
            font=("Microsoft YaHei", 9),
            bg="#f5f5f5",
            fg="#27ae60"
        )
        self.status_label.pack(pady=(10, 0))
    
    def _paste_machine_id(self):
        try:
            text = pyperclip.paste()
            self.machine_id_var.set(text)
            self.status_label.config(text="机器码已粘贴", fg="#27ae60")
        except:
            self.status_label.config(text="粘贴失败", fg="#e74c3c")
    
    def _generate_key(self):
        machine_id = self.machine_id_var.get().strip()
        
        if not machine_id:
            self.status_label.config(text="请输入机器码", fg="#e74c3c")
            return
        
        clean_id = machine_id.replace("-", "").replace(" ", "")
        if len(clean_id) < 8:
            self.status_label.config(text="机器码格式不正确", fg="#e74c3c")
            return
        
        key = self.generator.generate_key(machine_id)
        self.key_var.set(key)
        self.status_label.config(text="卡密已生成！", fg="#27ae60")
    
    def _copy_key(self):
        key = self.key_var.get()
        if not key:
            self.status_label.config(text="没有可复制的卡密", fg="#e74c3c")
            return
        
        try:
            pyperclip.copy(key)
            self.status_label.config(text="卡密已复制到剪贴板", fg="#27ae60")
        except:
            self.status_label.config(text="复制失败", fg="#e74c3c")
    
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = KeyGeneratorApp()
    app.run()
