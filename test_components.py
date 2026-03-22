"""
视图组件测试脚本
逐个测试所有UI组件，找出问题所在
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import traceback

class ComponentTester:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("视图组件测试")
        self.root.geometry("800x600")
        self.root.configure(bg='#050505')
        
        self.test_results = []
        self.current_test = 0
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置测试界面"""
        main_frame = tk.Frame(self.root, bg='#050505')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        title_label = tk.Label(
            main_frame,
            text="视图组件测试",
            font=('Microsoft YaHei UI', 16, 'bold'),
            bg='#050505',
            fg='#34d399'
        )
        title_label.pack(pady=(0, 20))
        
        button_frame = tk.Frame(main_frame, bg='#050505')
        button_frame.pack(fill='x', pady=10)
        
        tests = [
            ("测试 ModernButton", self.test_modern_button),
            ("测试 GlassCard", self.test_glass_card),
            ("测试 ModernInput", self.test_modern_input),
            ("测试 ModernProgressBar", self.test_modern_progressbar),
            ("测试 ModernLabel", self.test_modern_label),
            ("测试 ModernCheckbox", self.test_modern_checkbox),
            ("测试 ModernDropdown", self.test_modern_dropdown),
            ("测试 ModernTextArea", self.test_modern_textarea),
            ("运行所有测试", self.run_all_tests),
            ("显示测试结果", self.show_results)
        ]
        
        for text, command in tests:
            btn = tk.Button(
                button_frame,
                text=text,
                command=command,
                font=('Microsoft YaHei UI', 10),
                bg='#10b981',
                fg='white',
                relief='flat',
                padx=15,
                pady=8,
                cursor='hand2'
            )
            btn.pack(side='left', padx=5, pady=5)
        
        self.result_text = tk.Text(
            main_frame,
            height=20,
            bg='#0a0a0a',
            fg='#e0e0e0',
            font=('Consolas', 9),
            relief='flat',
            bd=1,
            highlightthickness=1,
            highlightbackground='#1a1a1a'
        )
        self.result_text.pack(fill='both', expand=True, pady=20)
        
        self.log("=== 视图组件测试开始 ===\n")
        
    def log(self, message):
        """记录日志"""
        self.result_text.insert('end', message + '\n')
        self.result_text.see('end')
        self.root.update()
        
    def test_component(self, test_name, test_func):
        """测试单个组件"""
        self.log(f"\n{'='*50}")
        self.log(f"测试: {test_name}")
        self.log(f"{'='*50}")
        
        try:
            test_func()
            self.log(f"✓ {test_name} 测试通过")
            self.test_results.append((test_name, "通过", None))
            return True
        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()
            self.log(f"✗ {test_name} 测试失败")
            self.log(f"错误: {error_msg}")
            self.log(f"堆栈:\n{error_trace}")
            self.test_results.append((test_name, "失败", error_msg))
            return False
        
    def test_modern_button(self):
        """测试 ModernButton 组件"""
        from ui_components import ModernButton
        
        test_window = tk.Toplevel(self.root)
        test_window.title("ModernButton 测试")
        test_window.geometry("400x300")
        test_window.configure(bg='#050505')
        
        frame = tk.Frame(test_window, bg='#050505')
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        def on_click():
            messagebox.showinfo("按钮测试", "按钮点击成功！")
        
        btn1 = ModernButton(frame, "主要按钮", on_click, style='primary')
        btn1.pack(pady=10)
        
        btn2 = ModernButton(frame, "次要按钮", on_click, style='secondary')
        btn2.pack(pady=10)
        
        btn3 = ModernButton(frame, "成功按钮", on_click, style='success')
        btn3.pack(pady=10)
        
        btn4 = ModernButton(frame, "危险按钮", on_click, style='danger')
        btn4.pack(pady=10)
        
        self.log("✓ ModernButton 创建成功")
        
    def test_glass_card(self):
        """测试 GlassCard 组件"""
        from ui_components import GlassCard, ModernButton, ModernLabel
        
        test_window = tk.Toplevel(self.root)
        test_window.title("GlassCard 测试")
        test_window.geometry("500x400")
        test_window.configure(bg='#050505')
        
        frame = tk.Frame(test_window, bg='#050505')
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        card1 = GlassCard(frame, title="卡片标题1")
        card1.pack(fill='x', pady=10)
        
        label1 = ModernLabel(card1.content_frame, "这是卡片内容1")
        label1.pack(pady=5)
        
        card2 = GlassCard(frame, title="卡片标题2")
        card2.pack(fill='x', pady=10)
        
        label2 = ModernLabel(card2.content_frame, "这是卡片内容2")
        label2.pack(pady=5)
        
        self.log("✓ GlassCard 创建成功")
        
    def test_modern_input(self):
        """测试 ModernInput 组件"""
        from ui_components import ModernInput
        
        test_window = tk.Toplevel(self.root)
        test_window.title("ModernInput 测试")
        test_window.geometry("500x300")
        test_window.configure(bg='#050505')
        
        frame = tk.Frame(test_window, bg='#050505')
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        input1 = ModernInput(frame, placeholder="请输入URL", width=40)
        input1.pack(pady=10)
        
        input2 = ModernInput(frame, placeholder="请输入密码", width=40, show='*')
        input2.pack(pady=10)
        
        test_btn = tk.Button(
            frame,
            text="获取输入值",
            command=lambda: self.log(f"输入1: {input1.get()}, 输入2: {input2.get()}"),
            bg='#10b981',
            fg='white',
            relief='flat'
        )
        test_btn.pack(pady=10)
        
        self.log("✓ ModernInput 创建成功")
        
    def test_modern_progressbar(self):
        """测试 ModernProgressBar 组件"""
        from ui_components import ModernProgressBar
        
        test_window = tk.Toplevel(self.root)
        test_window.title("ModernProgressBar 测试")
        test_window.geometry("500x300")
        test_window.configure(bg='#050505')
        
        frame = tk.Frame(test_window, bg='#050505')
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        progress = ModernProgressBar(frame, length=400)
        progress.pack(pady=20)
        
        def animate_progress():
            for i in range(0, 101, 10):
                progress.set_value(i)
                test_window.update()
                test_window.after(100)
        
        btn = tk.Button(
            frame,
            text="开始动画",
            command=animate_progress,
            bg='#10b981',
            fg='white',
            relief='flat'
        )
        btn.pack(pady=10)
        
        self.log("✓ ModernProgressBar 创建成功")
        
    def test_modern_label(self):
        """测试 ModernLabel 组件"""
        from ui_components import ModernLabel
        
        test_window = tk.Toplevel(self.root)
        test_window.title("ModernLabel 测试")
        test_window.geometry("400x300")
        test_window.configure(bg='#050505')
        
        frame = tk.Frame(test_window, bg='#050505')
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        label1 = ModernLabel(frame, "标题样式", style='title')
        label1.pack(pady=5)
        
        label2 = ModernLabel(frame, "标题样式", style='heading')
        label2.pack(pady=5)
        
        label3 = ModernLabel(frame, "正文样式", style='body')
        label3.pack(pady=5)
        
        label4 = ModernLabel(frame, "小字样式", style='small')
        label4.pack(pady=5)
        
        self.log("✓ ModernLabel 创建成功")
        
    def test_modern_checkbox(self):
        """测试 ModernCheckbox 组件"""
        from ui_components import ModernCheckbox
        
        test_window = tk.Toplevel(self.root)
        test_window.title("ModernCheckbox 测试")
        test_window.geometry("400x300")
        test_window.configure(bg='#050505')
        
        frame = tk.Frame(test_window, bg='#050505')
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        checkbox1 = ModernCheckbox(frame, "选项1")
        checkbox1.pack(pady=5)
        
        checkbox2 = ModernCheckbox(frame, "选项2")
        checkbox2.pack(pady=5)
        
        checkbox3 = ModernCheckbox(frame, "选项3")
        checkbox3.pack(pady=5)
        
        test_btn = tk.Button(
            frame,
            text="获取选中状态",
            command=lambda: self.log(f"选项1: {checkbox1.get()}, 选项2: {checkbox2.get()}, 选项3: {checkbox3.get()}"),
            bg='#10b981',
            fg='white',
            relief='flat'
        )
        test_btn.pack(pady=10)
        
        self.log("✓ ModernCheckbox 创建成功")
        
    def test_modern_dropdown(self):
        """测试 ModernDropdown 组件"""
        from ui_components import ModernDropdown
        
        test_window = tk.Toplevel(self.root)
        test_window.title("ModernDropdown 测试")
        test_window.geometry("400x300")
        test_window.configure(bg='#050505')
        
        frame = tk.Frame(test_window, bg='#050505')
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        options = ["选项1", "选项2", "选项3", "选项4"]
        dropdown = ModernDropdown(frame, options, default="选项1")
        dropdown.pack(pady=10)
        
        test_btn = tk.Button(
            frame,
            text="获取选中值",
            command=lambda: self.log(f"选中值: {dropdown.get()}"),
            bg='#10b981',
            fg='white',
            relief='flat'
        )
        test_btn.pack(pady=10)
        
        self.log("✓ ModernDropdown 创建成功")
        
    def test_modern_textarea(self):
        """测试 ModernTextArea 组件"""
        from ui_components import ModernTextArea
        
        test_window = tk.Toplevel(self.root)
        test_window.title("ModernTextArea 测试")
        test_window.geometry("500x400")
        test_window.configure(bg='#050505')
        
        frame = tk.Frame(test_window, bg='#050505')
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        textarea = ModernTextArea(frame, width=40, height=10, placeholder="请输入多行文本...")
        textarea.pack(pady=10)
        
        test_btn = tk.Button(
            frame,
            text="获取文本内容",
            command=lambda: self.log(f"文本内容: {textarea.get()}"),
            bg='#10b981',
            fg='white',
            relief='flat'
        )
        test_btn.pack(pady=10)
        
        self.log("✓ ModernTextArea 创建成功")
        
    def run_all_tests(self):
        """运行所有测试"""
        self.test_results = []
        self.result_text.delete('1.0', 'end')
        self.log("=== 开始运行所有测试 ===\n")
        
        tests = [
            ("ModernButton", self.test_modern_button),
            ("GlassCard", self.test_glass_card),
            ("ModernInput", self.test_modern_input),
            ("ModernProgressBar", self.test_modern_progressbar),
            ("ModernLabel", self.test_modern_label),
            ("ModernCheckbox", self.test_modern_checkbox),
            ("ModernDropdown", self.test_modern_dropdown),
            ("ModernTextArea", self.test_modern_textarea),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            if self.test_component(test_name, test_func):
                passed += 1
            else:
                failed += 1
        
        self.log(f"\n{'='*50}")
        self.log(f"测试完成！")
        self.log(f"通过: {passed}, 失败: {failed}")
        self.log(f"{'='*50}")
        
    def show_results(self):
        """显示测试结果"""
        if not self.test_results:
            messagebox.showinfo("测试结果", "还没有运行任何测试")
            return
        
        result_window = tk.Toplevel(self.root)
        result_window.title("测试结果汇总")
        result_window.geometry("600x400")
        result_window.configure(bg='#050505')
        
        frame = tk.Frame(result_window, bg='#050505')
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        title_label = tk.Label(
            frame,
            text="测试结果汇总",
            font=('Microsoft YaHei UI', 14, 'bold'),
            bg='#050505',
            fg='#34d399'
        )
        title_label.pack(pady=(0, 20))
        
        result_text = tk.Text(
            frame,
            height=15,
            bg='#0a0a0a',
            fg='#e0e0e0',
            font=('Consolas', 9),
            relief='flat',
            bd=1,
            highlightthickness=1,
            highlightbackground='#1a1a1a'
        )
        result_text.pack(fill='both', expand=True)
        
        for test_name, status, error in self.test_results:
            status_symbol = "✓" if status == "通过" else "✗"
            result_text.insert('end', f"{status_symbol} {test_name}: {status}\n")
            if error:
                result_text.insert('end', f"  错误: {error}\n")
        
        passed = sum(1 for _, status, _ in self.test_results if status == "通过")
        failed = len(self.test_results) - passed
        
        result_text.insert('end', f"\n总计: {len(self.test_results)} 个测试\n")
        result_text.insert('end', f"通过: {passed}, 失败: {failed}\n")
        
    def run(self):
        """运行测试器"""
        self.root.mainloop()

if __name__ == "__main__":
    try:
        tester = ComponentTester()
        tester.run()
    except Exception as e:
        print(f"启动测试器失败: {e}")
        traceback.print_exc()
        input("按任意键退出...")
