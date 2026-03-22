"""
用户手册模块
功能：提供用户手册界面，支持搜索和内容展示
作者：WebEXEBuilder Team
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, font as tkfont
import re


class UserManual:
    """
    用户手册类（单例模式）
    
    功能：
    - 显示用户手册窗口
    - 支持搜索功能
    - 按照匹配度排序
    - 显示大标题和小内容
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """
        单例模式实现
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, root=None, manual_data=None):
        """
        初始化用户手册
        
        参数:
            root: Tkinter根窗口对象
            manual_data: 手册数据列表，格式为 [{"title": "大标题", "content": "内容"}, ...]
        """
        if self._initialized:
            # 单例模式：更新 root 和 manual_data
            if root is not None:
                self.root = root
            if manual_data is not None:
                self.manual_data = manual_data
            return
        
        self.root = root
        self.manual_data = manual_data or []
        self.manual_window = None
        self.search_var = tk.StringVar()
        self.content_canvas = None
        self.content_frame = None
        self._initialized = True
        
        # 主题配置
        self.themes = {
            'light': {
                'bg': '#f5f5f5',
                'fg': '#333333',
                'secondary_fg': '#666666',
                'search_bg': '#4CAF50',
                'search_fg': 'white',
                'input_bg': 'white',
                'input_fg': '#333333',
                'button_bg': '#2196F3',
                'button_fg': 'white',
                'content_bg': 'white',
                'content_fg': '#666666',
                'border': '#e0e0e0'
            },
            'dark': {
                'bg': '#2b2b2b',
                'fg': '#e0e0e0',
                'secondary_fg': '#a0a0a0',
                'search_bg': '#1e5e3e',
                'search_fg': 'white',
                'input_bg': '#3a3a3a',
                'input_fg': '#e0e0e0',
                'button_bg': '#0d47a1',
                'button_fg': 'white',
                'content_bg': '#3a3a3a',
                'content_fg': '#b0b0b0',
                'border': '#4a4a4a'
            }
        }
        self.current_theme = 'dark'
        
    def set_manual_data(self, manual_data):
        """
        设置手册数据
        
        参数:
            manual_data: 手册数据列表
        """
        self.manual_data = manual_data
        if self.manual_window is not None and self.content_frame is not None:
            self.display_content(self.manual_data)
        
    def show_manual(self):
        """
        显示用户手册
        """
        if self.manual_window is not None:
            try:
                self.manual_window.lift()
                self.manual_window.focus()
                return
            except:
                self.manual_window = None
        
        colors = self.themes[self.current_theme]
        
        self.manual_window = tk.Toplevel(self.root)
        self.manual_window.title("用户手册")
        self.manual_window.geometry("900x700")
        
        # 设置窗口位置在屏幕右侧
        screen_width = self.manual_window.winfo_screenwidth()
        screen_height = self.manual_window.winfo_screenheight()
        window_width = 900
        window_height = 700
        x = screen_width - window_width - 50
        y = (screen_height - window_height) // 2
        self.manual_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 顶部搜索栏
        search_frame = tk.Frame(self.manual_window, bg=colors['search_bg'], padx=15, pady=15)
        search_frame.pack(fill=tk.X)
        
        tk.Label(
            search_frame,
            text="📚 用户手册",
            font=("Microsoft YaHei UI", 16, "bold"),
            bg=colors['search_bg'],
            fg=colors['search_fg']
        ).pack(anchor="w", pady=(0, 10))
        
        search_entry_frame = tk.Frame(search_frame, bg=colors['search_bg'])
        search_entry_frame.pack(fill=tk.X)
        
        search_entry = tk.Entry(
            search_entry_frame,
            textvariable=self.search_var,
            font=("Microsoft YaHei UI", 12),
            bg=colors['input_bg'],
            fg=colors['input_fg'],
            relief=tk.FLAT
        )
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=5)
        
        search_entry.bind("<KeyRelease>", self.on_search)
        
        search_btn = tk.Button(
            search_entry_frame,
            text="🔍",
            font=("Microsoft YaHei UI", 12),
            bg=colors['button_bg'],
            fg=colors['button_fg'],
            cursor="hand2",
            command=self.on_search,
            relief=tk.FLAT,
            padx=10
        )
        search_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # 创建滚动容器
        scroll_container = tk.Frame(self.manual_window, bg=colors['bg'])
        scroll_container.pack(fill=tk.BOTH, expand=True)
        
        # 创建Canvas（不使用滚动条）
        canvas = tk.Canvas(scroll_container, bg=colors['bg'], highlightthickness=0)
        
        # 内容区域
        self.content_frame = tk.Frame(canvas, bg=colors['bg'], padx=20, pady=20)
        
        # 配置滚动
        self.content_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # 创建窗口
        canvas_window = canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        
        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except tk.TclError:
                pass
        
        def _on_mousewheel_linux(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta)), "units")
            except tk.TclError:
                pass
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: _on_mousewheel_linux(e) or canvas.yview_scroll(-1, "units") if canvas.winfo_exists() else None)
        canvas.bind_all("<Button-5>", lambda e: _on_mousewheel_linux(e) or canvas.yview_scroll(1, "units") if canvas.winfo_exists() else None)
        
        # 布局
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # 显示内容
        self.display_content(self.manual_data)
        
        # 设置固定窗口大小
        screen_height = self.manual_window.winfo_screenheight()
        window_height = min(600, screen_height - 100)
        current_width = self.manual_window.winfo_width()
        self.manual_window.geometry(f"{current_width}x{window_height}")
        
        # 底部关闭按钮
        close_frame = tk.Frame(self.manual_window, bg=colors['bg'], padx=15, pady=15)
        close_frame.pack(fill=tk.X)
        
        tk.Button(
            close_frame,
            text="关闭",
            font=("Microsoft YaHei UI", 12),
            bg="#9E9E9E",
            fg="white",
            cursor="hand2",
            command=self.close_manual,
            relief=tk.FLAT,
            padx=30,
            pady=8
        ).pack(side=tk.RIGHT)
        
        # 窗口关闭事件
        self.manual_window.protocol("WM_DELETE_WINDOW", self.close_manual)
    
    def on_search(self, event=None):
        """
        搜索功能
        
        参数:
            event: 键盘事件（可选）
        """
        search_text = self.search_var.get().strip()
        
        print(f"[DEBUG] 搜索文本: '{search_text}'")
        
        if not search_text:
            self.display_content(self.manual_data, search_text="")
            return
        
        # 搜索并计算匹配度
        results = []
        for item in self.manual_data:
            title = item.get("title", "")
            content = item.get("content", "")
            
            # 计算标题匹配度
            title_match_score = self.calculate_match_score(search_text, title)
            
            # 计算内容匹配度
            content_match_score = self.calculate_match_score(search_text, content)
            
            # 综合匹配度（标题权重更高）
            total_score = title_match_score * 2 + content_match_score
            
            print(f"[DEBUG] 标题: '{title}', 分数: {total_score} (标题: {title_match_score}, 内容: {content_match_score})")
            
            if total_score > 0:
                results.append({
                    "title": title,
                    "content": content,
                    "score": total_score
                })
        
        print(f"[DEBUG] 找到 {len(results)} 个结果")
        
        # 按匹配度排序
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # 显示搜索结果
        self.display_content(results, search_text)
    
    def calculate_match_score(self, search_text, text):
        """
        计算匹配度分数（支持中文）
        
        参数:
            search_text: 搜索文本
            text: 要匹配的文本
        
        返回:
            int: 匹配度分数
        """
        if not search_text or not text:
            return 0
        
        search_text_lower = search_text.lower()
        text_lower = text.lower()
        
        score = 0
        
        if search_text_lower == text_lower:
            score += 100
        
        if search_text_lower in text_lower:
            score += 50
            score += text_lower.count(search_text_lower) * 10
        
        def contains_chinese(s):
            for char in s:
                if '\u4e00' <= char <= '\u9fff':
                    return True
            return False
        
        if contains_chinese(search_text):
            for i in range(len(search_text_lower)):
                for j in range(i + 1, len(search_text_lower) + 1):
                    substring = search_text_lower[i:j]
                    if len(substring) >= 2 and substring in text_lower:
                        score += 3
        else:
            search_words = search_text_lower.split()
            text_words = text_lower.split()
            
            for search_word in search_words:
                for text_word in text_words:
                    if search_word == text_word:
                        score += 10
                    elif search_word in text_word:
                        score += 5
        
        return score
    
    def display_content(self, data, search_text=""):
        """
        [修改] 显示内容（支持动态自适应宽度）
        
        参数:
            data: 要显示的数据列表
            search_text: 搜索文本（用于高亮）
        """
        colors = self.themes[self.current_theme]
        
        # 1. 清空现有内容
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # [关键] 绑定大小变化事件
        # 当 content_frame 宽度变化时，触发 self.on_frame_configure
        self.content_frame.bind("<Configure>", self.on_frame_configure)
        
        if not data:
            tk.Label(
                self.content_frame,
                text="未找到相关内容",
                font=("Microsoft YaHei UI", 12),
                bg=colors['bg'],
                fg=colors['secondary_fg']
            ).pack(pady=50)
            return
        
        self.content_font = tkfont.Font(family="Microsoft YaHei UI", size=10)
        
        for i, item in enumerate(data):
            title = item.get("title", "")
            content = item.get("content", "")
            
            # --- 条目容器 ---
            frame = tk.Frame(self.content_frame, bg=colors['content_bg'], pady=10, padx=15)
            frame.pack(pady=5, padx=5)
            
            # --- 标题 ---
            # --- 标题（改用 Text 组件以实现搜索高亮）---
            title_text = tk.Text(
                frame,
                font=("Microsoft YaHei UI", 12, "bold"),
                bg=colors['content_bg'],
                fg=colors['fg'],
                relief="flat",
                wrap="word",
                height=1,        # 初始行高，会自动适应
                bd=0,
                padx=0,
                pady=0
            )
            title_text.insert("1.0", title)
            title_text.config(state=tk.DISABLED)   # 设置为只读，防止用户修改
            title_text.pack(pady=(0, 5))
            
            # 存储原始文本，供后续动态调整高度使用（与内容共用同一机制）
            title_text.custom_text_content = title
            
            # 如果正在进行搜索，对标题也进行高亮
            if search_text:
                title_text.config(state=tk.NORMAL)
                self.highlight_text(title_text, search_text)
                title_text.config(state=tk.DISABLED)
            
            # --- 内容 (Text组件) ---
            content_text = tk.Text(
                frame,
                font=self.content_font,
                bg=colors['content_bg'],
                fg=colors['content_fg'],
                relief="flat",
                wrap="word",
                height=1,  # 初始高度设为1，稍后会自动拉伸
                bd=0,
                padx=0,
                pady=0
            )
            content_text.insert("1.0", content)
            content_text.config(state="disabled")
            content_text.pack()
            
            # [关键技巧] 将原始内容存储在组件对象的一个自定义属性中
            # 这样在 resize 事件发生时，我们能找回这段文字重新计算高度
            content_text.custom_text_content = content
            
            # --- 搜索高亮 ---
            if search_text:
                content_text.config(state=tk.NORMAL)
                self.highlight_text(content_text, search_text)
                content_text.config(state=tk.DISABLED)
            
            # --- 分隔线 ---
            if i < len(data) - 1:
                separator = tk.Frame(self.content_frame, bg=colors['border'], height=1)
                separator.pack(fill=tk.X, pady=(5, 5))
        
        # 更新窗口大小以适应内容
        self.manual_window.update_idletasks()
        content_height = self.content_frame.winfo_reqheight()
        search_height = 90
        close_height = 80
        total_height = content_height + search_height + close_height
        
        # 限制最大高度，不超过屏幕高度
        screen_height = self.manual_window.winfo_screenheight()
        max_height = screen_height - 100
        if total_height > max_height:
            total_height = max_height
        
        # 限制最小高度
        min_height = 400
        if total_height < min_height:
            total_height = min_height
        
        # 保持当前窗口宽度，只更新高度
        current_width = self.manual_window.winfo_width()
        self.manual_window.geometry(f"{current_width}x{total_height}")
        
        # 强制刷新一次布局
        self.manual_window.after(10, lambda: self.on_frame_configure(None))
    
    def on_frame_configure(self, event):
        """
        [新增] 窗口大小改变时的回调函数
        实时重新计算所有文本框的高度
        """
        # 获取窗口实际宽度
        window_width = self.manual_window.winfo_width()
        
        # 估算文本可用宽度（窗口宽度减去所有固定边距）
        # 根据布局，content_frame 左右边距20，frame 左右边距5+15，Text内部边距约4
        # 总共约 (20+5+15+4)*2 = 88，取整为100
        text_area_width = window_width - 100
        
        if text_area_width < 100:
            text_area_width = 100
        
        # 遍历所有子控件，找到所有的 Text 组件并更新高度
        # 注意：content_frame 的子控件是 frame，frame 的子控件才是 Text
        for outer_frame in self.content_frame.winfo_children():
            # 跳过 label (如果 "未找到相关内容" 存在)
            if not isinstance(outer_frame, tk.Frame):
                continue
                
            for widget in outer_frame.winfo_children():
                if isinstance(widget, tk.Text) and hasattr(widget, 'custom_text_content'):
                    # 取出之前存好的文字
                    text_content = widget.custom_text_content
                    
                    # 重新计算行数
                    new_lines = self.calculate_text_height(
                        text_content,
                        self.content_font,
                        text_area_width
                    )
                    
                    # 只有当高度确实变化时才更新，减少闪烁
                    if widget.cget("height") != new_lines:
                        widget.config(height=new_lines)
    
    def calculate_text_height(self, text, font, width_px):
        """
        计算文本在指定宽度下的高度（行数）
        
        参数:
            text: 文本内容
            font: 字体对象
            width_px: 宽度（像素）
        
        返回:
            int: 行数
        """
        lines = 0
        for paragraph in text.split('\n'):
            if not paragraph:
                lines += 1
                continue
            pixel_length = font.measure(paragraph)
            lines += int(pixel_length / width_px) + 1
        return lines
    
    def highlight_text(self, text_widget, search_text):
        """
        高亮搜索文本
        
        参数:
            text_widget: Text 组件
            search_text: 要高亮的文本
        """
        if not search_text:
            return
        
        print(f"[DEBUG] ========== 开始高亮搜索 ==========")
        print(f"[DEBUG] 搜索文本: '{search_text}'")
        print(f"[DEBUG] 搜索文本类型: {type(search_text)}")
        print(f"[DEBUG] 搜索文本长度: {len(search_text)}")
        
        # 移除旧的高亮
        text_widget.tag_remove("highlight", "1.0", tk.END)
        
        # 根据主题设置高亮样式
        if self.current_theme == 'dark':
            # 暗色主题使用黄色高亮
            text_widget.tag_config("highlight", background="#FFD700", foreground="black")
        else:
            # 亮色主题使用绿色高亮
            text_widget.tag_config("highlight", background="#C8E6C9", foreground="black")
        
        # 使用 Tkinter Text 组件自带的 search 方法直接搜索
        # 这样可以避免获取文本时的编码和索引问题
        search_pos = "1.0"
        match_count = 0
        
        while True:
            # 在 Text 组件中搜索（不区分大小写）
            match_pos = text_widget.search(search_text, search_pos, stopindex=tk.END, nocase=True)
            
            if not match_pos:
                break
            
            print(f"[DEBUG] --- 匹配 {match_count} ---")
            print(f"[DEBUG] 找到位置: {match_pos}")
            
            # 计算结束位置（使用 +N chars）
            end_pos = text_widget.index(f"{match_pos}+{len(search_text)} chars")
            
            print(f"[DEBUG] 结束位置: {end_pos}")
            
            # 验证匹配的文本
            matched_text = text_widget.get(match_pos, end_pos)
            print(f"[DEBUG] 匹配文本: '{matched_text}'")
            
            # 添加高亮标签
            text_widget.tag_add("highlight", match_pos, end_pos)
            
            # 更新搜索起始位置（从结束位置继续搜索）
            search_pos = end_pos
            match_count += 1
        
        print(f"[DEBUG] 总共高亮了 {match_count} 处")
        print(f"[DEBUG] ========== 高亮搜索结束 ==========")
        print()
    
    def set_theme(self, theme):
        """
        设置主题
        
        参数:
            theme: 主题名称 ('light' 或 'dark')
        """
        self.current_theme = theme
        if self.manual_window is not None:
            self.display_content(self.manual_data)
    
    def close_manual(self):
        """
        关闭用户手册窗口
        """
        if self.manual_window is not None:
            try:
                self.manual_window.destroy()
            except:
                pass
            self.manual_window = None
            self.content_canvas = None
            self.content_frame = None


def create_manual_button(parent, manual_data, root):
    """
    创建手册按钮（使用单例模式）
    
    参数:
        parent: 父容器
        manual_data: 手册数据
        root: 根窗口对象
    
    返回:
        tuple: (UserManual实例, 按钮对象)
    """
    manual = UserManual(root)
    manual.set_manual_data(manual_data)
    
    manual_btn = tk.Button(
        parent,
        text="📖 用户手册",
        font=("Microsoft YaHei UI", 10),
        bg="#2196F3",
        fg="white",
        cursor="hand2",
        command=manual.show_manual,
        relief=tk.FLAT,
        padx=15,
        pady=5
    )
    
    return manual, manual_btn
