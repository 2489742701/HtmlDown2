import tkinter as tk
from tkinter import ttk
from ui_styles import UIStyles

class ModernButton:
    """现代化按钮"""
    
    def __init__(self, parent, text, command, icon=None, style='primary'):
        self.parent = parent
        self.text = text
        self.command = command
        self.icon = icon
        self.style = style
        
        self.button = self._create_button()
    
    def _create_button(self):
        """创建按钮"""
        if self.style == 'primary':
            bg_color = UIStyles.COLORS['primary']
            active_bg = UIStyles.COLORS['primary_dark']
            hover_bg = UIStyles.COLORS['primary_light']
        elif self.style == 'secondary':
            bg_color = UIStyles.COLORS['secondary']
            active_bg = '#0d9488'
            hover_bg = '#2dd4bf'
        elif self.style == 'success':
            bg_color = UIStyles.COLORS['success']
            active_bg = '#16a34a'
            hover_bg = '#4ade80'
        elif self.style == 'danger':
            bg_color = UIStyles.COLORS['error']
            active_bg = '#dc2626'
            hover_bg = '#f87171'
        else:
            bg_color = UIStyles.COLORS['primary']
            active_bg = UIStyles.COLORS['primary_dark']
            hover_bg = UIStyles.COLORS['primary_light']
        
        btn_text = f"{self.icon} {self.text}" if self.icon else self.text
        
        btn = tk.Button(
            self.parent,
            text=btn_text,
            command=self.command,
            font=UIStyles.FONTS['body'],
            relief='flat',
            bd=0,
            padx=25,
            pady=12,
            cursor='hand2',
            bg=bg_color,
            fg='white',
            activebackground=active_bg,
            activeforeground='white'
        )
        
        def on_enter(event):
            btn.config(bg=hover_bg)
        
        def on_leave(event):
            btn.config(bg=bg_color)
        
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        
        return btn
    
    def pack(self, **kwargs):
        """打包方法"""
        self.button.pack(**kwargs)
    
    def grid(self, **kwargs):
        """网格布局方法"""
        self.button.grid(**kwargs)
    
    def config(self, **kwargs):
        """配置方法"""
        self.button.config(**kwargs)
    
    def enable(self):
        """启用按钮"""
        self.button.config(state='normal')
    
    def disable(self):
        """禁用按钮"""
        self.button.config(state='disabled')

class GlassCard:
    """玻璃态卡片"""
    
    def __init__(self, parent, title=None):
        self.parent = parent
        self.title = title
        
        self.frame = self._create_frame()
        self.content_frame = self._create_content()
    
    def _create_frame(self):
        """创建卡片框架"""
        frame = tk.Frame(
            self.parent,
            bg=UIStyles.COLORS['bg_glass'],
            bd=1,
            relief='solid',
            highlightthickness=0
        )
        
        if self.title:
            title_label = tk.Label(
                frame,
                text=self.title,
                bg=UIStyles.COLORS['bg_glass'],
                fg=UIStyles.COLORS['primary_light'],
                font=UIStyles.FONTS['heading']
            )
            title_label.pack(anchor='w', padx=15, pady=10)
        
        return frame
    
    def _create_content(self):
        """创建内容区域"""
        content = tk.Frame(
            self.frame,
            bg=UIStyles.COLORS['bg_card']
        )
        content.pack(fill='both', expand=True, padx=15, pady=15)
        return content
    
    def pack(self, **kwargs):
        """打包方法"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """网格布局方法"""
        self.frame.grid(**kwargs)

class ModernInput:
    """现代化输入框"""
    
    def __init__(self, parent, placeholder='', width=400, show=None):
        self.parent = parent
        self.placeholder = placeholder
        self.width = width
        self.show = show
        
        self.frame = self._create_frame()
        self.entry = self._create_entry()
    
    def _create_frame(self):
        """创建输入框框架"""
        frame = tk.Frame(
            self.parent,
            bg=UIStyles.COLORS['bg_main']
        )
        return frame
    
    def _create_entry(self):
        """创建输入框"""
        entry = tk.Entry(
            self.frame,
            width=self.width,
            font=UIStyles.FONTS['body'],
            bg=UIStyles.COLORS['bg_card'],
            fg=UIStyles.COLORS['text_primary'],
            insertbackground=UIStyles.COLORS['primary'],
            selectbackground=UIStyles.COLORS['primary'],
            selectforeground='white',
            relief='flat',
            bd=1,
            highlightthickness=1,
            highlightbackground=UIStyles.COLORS['border'],
            highlightcolor=UIStyles.COLORS['primary'],
            show=self.show
        )
        
        if self.placeholder:
            self._set_placeholder(entry)
        
        return entry
    
    def _set_placeholder(self, entry):
        """设置占位符效果"""
        placeholder_text = self.placeholder
        
        def on_focus_in(event):
            if entry.get() == placeholder_text:
                entry.delete(0, 'end')
                entry.config(fg=UIStyles.COLORS['text_primary'])
        
        def on_focus_out(event):
            if not entry.get():
                entry.insert(0, placeholder_text)
                entry.config(fg=UIStyles.COLORS['text_secondary'])
        
        entry.bind('<FocusIn>', on_focus_in)
        entry.bind('<FocusOut>', on_focus_out)
        
        entry.insert(0, placeholder_text)
        entry.config(fg=UIStyles.COLORS['text_secondary'])
    
    def pack(self, **kwargs):
        """打包方法"""
        self.frame.pack(**kwargs)
        self.entry.pack(padx=10, pady=10)
    
    def grid(self, **kwargs):
        """网格布局方法"""
        self.frame.grid(**kwargs)
        self.entry.grid(padx=10, pady=10)
    
    def get(self):
        """获取值"""
        value = self.entry.get()
        if self.placeholder and value == self.placeholder:
            return ''
        return value
    
    def set(self, value):
        """设置值"""
        self.entry.delete(0, 'end')
        self.entry.insert(0, value)
        self.entry.config(fg=UIStyles.COLORS['text_primary'])
    
    def clear(self):
        """清空输入框"""
        self.entry.delete(0, 'end')
        if self.placeholder:
            self.entry.insert(0, self.placeholder)
            self.entry.config(fg=UIStyles.COLORS['text_secondary'])

class ModernProgressBar:
    """现代化进度条"""
    
    def __init__(self, parent, length=400, mode='determinate'):
        self.parent = parent
        self.length = length
        self.mode = mode
        
        self.frame = self._create_frame()
        self.progress = self._create_progress()
        self.label = self._create_label()
    
    def _create_frame(self):
        """创建进度条框架"""
        frame = tk.Frame(
            self.parent,
            bg=UIStyles.COLORS['bg_main']
        )
        return frame
    
    def _create_progress(self):
        """创建进度条"""
        progress = ttk.Progressbar(
            self.frame,
            length=self.length,
            mode=self.mode,
            style='Horizontal.TProgressbar'
        )
        return progress
    
    def _create_label(self):
        """创建标签"""
        label = tk.Label(
            self.frame,
            text='0%',
            bg=UIStyles.COLORS['bg_main'],
            fg=UIStyles.COLORS['text_secondary'],
            font=UIStyles.FONTS['small']
        )
        return label
    
    def pack(self, **kwargs):
        """打包方法"""
        self.frame.pack(**kwargs)
        self.progress.pack(padx=10, pady=5)
        self.label.pack(padx=10, pady=5)
    
    def grid(self, **kwargs):
        """网格布局方法"""
        self.frame.grid(**kwargs)
        self.progress.grid(padx=10, pady=5)
        self.label.grid(padx=10, pady=5)
    
    def set_value(self, value):
        """设置进度值 (0-100)"""
        self.progress['value'] = value
        self.label.config(text=f'{int(value)}%')
    
    def start(self):
        """开始进度条"""
        self.progress.start()
    
    def stop(self):
        """停止进度条"""
        self.progress.stop()
    
    def reset(self):
        """重置进度条"""
        self.progress['value'] = 0
        self.label.config(text='0%')

class ModernLabel:
    """现代化标签"""
    
    def __init__(self, parent, text, style='body'):
        self.parent = parent
        self.text = text
        self.style = style
        
        self.label = self._create_label()
    
    def _create_label(self):
        """创建标签"""
        if self.style == 'title':
            font = UIStyles.FONTS['title']
            fg = UIStyles.COLORS['primary_light']
        elif self.style == 'heading':
            font = UIStyles.FONTS['heading']
            fg = UIStyles.COLORS['primary_light']
        elif self.style == 'body':
            font = UIStyles.FONTS['body']
            fg = UIStyles.COLORS['text_primary']
        elif self.style == 'small':
            font = UIStyles.FONTS['small']
            fg = UIStyles.COLORS['text_secondary']
        else:
            font = UIStyles.FONTS['body']
            fg = UIStyles.COLORS['text_primary']
        
        label = tk.Label(
            self.parent,
            text=self.text,
            font=font,
            bg=UIStyles.COLORS['bg_main'],
            fg=fg
        )
        return label
    
    def pack(self, **kwargs):
        """打包方法"""
        self.label.pack(**kwargs)
    
    def grid(self, **kwargs):
        """网格布局方法"""
        self.label.grid(**kwargs)
    
    def config(self, **kwargs):
        """配置方法"""
        self.label.config(**kwargs)
    
    def set_text(self, text):
        """设置文本"""
        self.label.config(text=text)

class ModernCheckbox:
    """现代化复选框"""
    
    def __init__(self, parent, text, variable=None):
        self.parent = parent
        self.text = text
        self.variable = variable if variable else tk.BooleanVar()
        
        self.frame = self._create_frame()
        self.checkbox = self._create_checkbox()
    
    def _create_frame(self):
        """创建复选框框架"""
        frame = tk.Frame(
            self.parent,
            bg=UIStyles.COLORS['bg_main']
        )
        return frame
    
    def _create_checkbox(self):
        """创建复选框"""
        checkbox = tk.Checkbutton(
            self.frame,
            text=self.text,
            variable=self.variable,
            font=UIStyles.FONTS['body'],
            bg=UIStyles.COLORS['bg_main'],
            fg=UIStyles.COLORS['text_primary'],
            selectcolor=UIStyles.COLORS['bg_card'],
            activebackground=UIStyles.COLORS['bg_main'],
            activeforeground=UIStyles.COLORS['primary_light'],
            cursor='hand2'
        )
        return checkbox
    
    def pack(self, **kwargs):
        """打包方法"""
        self.frame.pack(**kwargs)
        self.checkbox.pack(anchor='w', padx=10, pady=5)
    
    def grid(self, **kwargs):
        """网格布局方法"""
        self.frame.grid(**kwargs)
        self.checkbox.grid(anchor='w', padx=10, pady=5)
    
    def get(self):
        """获取值"""
        return self.variable.get()
    
    def set(self, value):
        """设置值"""
        self.variable.set(value)

class ModernDropdown:
    """现代化下拉框"""
    
    def __init__(self, parent, options, default=None):
        self.parent = parent
        self.options = options
        self.variable = tk.StringVar(value=default if default else (options[0] if options else ''))
        
        self.frame = self._create_frame()
        self.dropdown = self._create_dropdown()
    
    def _create_frame(self):
        """创建下拉框框架"""
        frame = tk.Frame(
            self.parent,
            bg=UIStyles.COLORS['bg_main']
        )
        return frame
    
    def _create_dropdown(self):
        """创建下拉框"""
        dropdown = ttk.Combobox(
            self.frame,
            textvariable=self.variable,
            values=self.options,
            state='readonly',
            font=UIStyles.FONTS['body'],
            style='Modern.TEntry'
        )
        return dropdown
    
    def pack(self, **kwargs):
        """打包方法"""
        self.frame.pack(**kwargs)
        self.dropdown.pack(padx=10, pady=10)
    
    def grid(self, **kwargs):
        """网格布局方法"""
        self.frame.grid(**kwargs)
        self.dropdown.grid(padx=10, pady=10)
    
    def get(self):
        """获取值"""
        return self.variable.get()
    
    def set(self, value):
        """设置值"""
        self.variable.set(value)
    
    def bind(self, event, callback):
        """绑定事件"""
        self.dropdown.bind(event, callback)

class ModernTextArea:
    """现代化文本区域"""
    
    def __init__(self, parent, width=400, height=200, placeholder=''):
        self.parent = parent
        self.width = width
        self.height = height
        self.placeholder = placeholder
        
        self.frame = self._create_frame()
        self.text_area = self._create_text_area()
    
    def _create_frame(self):
        """创建文本区域框架"""
        frame = tk.Frame(
            self.parent,
            bg=UIStyles.COLORS['bg_main']
        )
        return frame
    
    def _create_text_area(self):
        """创建文本区域"""
        text_area = tk.Text(
            self.frame,
            width=self.width,
            height=self.height,
            font=UIStyles.FONTS['body'],
            bg=UIStyles.COLORS['bg_card'],
            fg=UIStyles.COLORS['text_primary'],
            insertbackground=UIStyles.COLORS['primary'],
            selectbackground=UIStyles.COLORS['primary'],
            selectforeground='white',
            relief='flat',
            bd=1,
            highlightthickness=1,
            highlightbackground=UIStyles.COLORS['border'],
            highlightcolor=UIStyles.COLORS['primary'],
            wrap='word'
        )
        
        if self.placeholder:
            self._set_placeholder(text_area)
        
        return text_area
    
    def _set_placeholder(self, text_area):
        """设置占位符效果"""
        placeholder_text = self.placeholder
        
        def on_focus_in(event):
            if text_area.get('1.0', 'end-1c') == placeholder_text:
                text_area.delete('1.0', 'end')
                text_area.config(fg=UIStyles.COLORS['text_primary'])
        
        def on_focus_out(event):
            if not text_area.get('1.0', 'end-1c'):
                text_area.insert('1.0', placeholder_text)
                text_area.config(fg=UIStyles.COLORS['text_secondary'])
        
        text_area.bind('<FocusIn>', on_focus_in)
        text_area.bind('<FocusOut>', on_focus_out)
        
        text_area.insert('1.0', placeholder_text)
        text_area.config(fg=UIStyles.COLORS['text_secondary'])
    
    def pack(self, **kwargs):
        """打包方法"""
        self.frame.pack(**kwargs)
        self.text_area.pack(padx=10, pady=10)
    
    def grid(self, **kwargs):
        """网格布局方法"""
        self.frame.grid(**kwargs)
        self.text_area.grid(padx=10, pady=10)
    
    def get(self):
        """获取值"""
        value = self.text_area.get('1.0', 'end-1c')
        if self.placeholder and value == self.placeholder:
            return ''
        return value
    
    def set(self, value):
        """设置值"""
        self.text_area.delete('1.0', 'end')
        self.text_area.insert('1.0', value)
        self.text_area.config(fg=UIStyles.COLORS['text_primary'])
    
    def clear(self):
        """清空文本区域"""
        self.text_area.delete('1.0', 'end')
        if self.placeholder:
            self.text_area.insert('1.0', self.placeholder)
            self.text_area.config(fg=UIStyles.COLORS['text_secondary'])
    
    def append(self, text):
        """追加文本"""
        if self.placeholder and self.text_area.get('1.0', 'end-1c') == self.placeholder:
            self.text_area.delete('1.0', 'end')
            self.text_area.config(fg=UIStyles.COLORS['text_primary'])
        self.text_area.insert('end', text)
        self.text_area.see('end')
