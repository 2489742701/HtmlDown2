"""
现代化 Tkinter 主题样式
使用标准库实现，无需额外依赖
"""

import tkinter as tk
from tkinter import ttk


class ModernTheme:
    """现代化深色主题"""
    
    COLORS = {
        'bg_dark': '#1a1a2e',
        'bg_medium': '#16213e',
        'bg_light': '#0f3460',
        'accent': '#e94560',
        'accent_hover': '#ff6b6b',
        'success': '#00d9a5',
        'warning': '#ffc107',
        'error': '#ff4757',
        'text_primary': '#ffffff',
        'text_secondary': '#a0a0a0',
        'text_hint': '#6c6c6c',
        'border': '#2d2d44',
        'card_bg': '#1f1f38',
    }
    
    FONTS = {
        'title': ('Segoe UI', 18, 'bold'),
        'subtitle': ('Segoe UI', 12, 'bold'),
        'body': ('Segoe UI', 10),
        'small': ('Segoe UI', 9),
        'code': ('Consolas', 9),
    }
    
    @classmethod
    def apply(cls, root):
        """应用主题到根窗口"""
        style = ttk.Style()
        
        style.theme_use('clam')
        
        root.configure(bg=cls.COLORS['bg_dark'])
        
        style.configure('.',
            background=cls.COLORS['bg_dark'],
            foreground=cls.COLORS['text_primary'],
            fieldbackground=cls.COLORS['bg_medium'],
            bordercolor=cls.COLORS['border'],
            lightcolor=cls.COLORS['bg_light'],
            darkcolor=cls.COLORS['bg_dark'],
        )
        
        style.configure('TFrame',
            background=cls.COLORS['bg_dark'],
        )
        
        style.configure('Card.TFrame',
            background=cls.COLORS['card_bg'],
            bordercolor=cls.COLORS['border'],
            relief='flat',
        )
        
        style.configure('TLabel',
            background=cls.COLORS['bg_dark'],
            foreground=cls.COLORS['text_primary'],
            font=cls.FONTS['body'],
        )
        
        style.configure('Title.TLabel',
            font=cls.FONTS['title'],
            foreground=cls.COLORS['text_primary'],
        )
        
        style.configure('Subtitle.TLabel',
            font=cls.FONTS['subtitle'],
            foreground=cls.COLORS['text_secondary'],
        )
        
        style.configure('Hint.TLabel',
            font=cls.FONTS['small'],
            foreground=cls.COLORS['text_hint'],
        )
        
        style.configure('Success.TLabel',
            foreground=cls.COLORS['success'],
        )
        
        style.configure('Warning.TLabel',
            foreground=cls.COLORS['warning'],
        )
        
        style.configure('Error.TLabel',
            foreground=cls.COLORS['error'],
        )
        
        style.configure('Accent.TLabel',
            foreground=cls.COLORS['accent'],
        )
        
        style.configure('TButton',
            background=cls.COLORS['bg_light'],
            foreground=cls.COLORS['text_primary'],
            font=cls.FONTS['body'],
            padding=(16, 8),
            bordercolor=cls.COLORS['border'],
            focuscolor=cls.COLORS['accent'],
        )
        
        style.map('TButton',
            background=[
                ('active', cls.COLORS['accent']),
                ('pressed', cls.COLORS['accent_hover']),
                ('!active', cls.COLORS['bg_light']),
            ],
            foreground=[
                ('active', cls.COLORS['text_primary']),
                ('pressed', cls.COLORS['text_primary']),
            ],
        )
        
        style.configure('Accent.TButton',
            background=cls.COLORS['accent'],
            foreground=cls.COLORS['text_primary'],
            font=cls.FONTS['subtitle'],
            padding=(20, 10),
        )
        
        style.map('Accent.TButton',
            background=[
                ('active', cls.COLORS['accent_hover']),
                ('pressed', cls.COLORS['bg_light']),
            ],
        )
        
        style.configure('Success.TButton',
            background=cls.COLORS['success'],
            foreground=cls.COLORS['bg_dark'],
        )
        
        style.map('Success.TButton',
            background=[
                ('active', '#00ffbb'),
            ],
        )
        
        style.configure('TEntry',
            fieldbackground=cls.COLORS['bg_medium'],
            foreground=cls.COLORS['text_primary'],
            insertcolor=cls.COLORS['accent'],
            bordercolor=cls.COLORS['border'],
            lightcolor=cls.COLORS['bg_light'],
            darkcolor=cls.COLORS['bg_dark'],
            padding=8,
        )
        
        style.configure('TCombobox',
            fieldbackground=cls.COLORS['bg_medium'],
            foreground=cls.COLORS['text_primary'],
            arrowcolor=cls.COLORS['accent'],
            bordercolor=cls.COLORS['border'],
        )
        
        style.configure('TSpinbox',
            fieldbackground=cls.COLORS['bg_medium'],
            foreground=cls.COLORS['text_primary'],
            arrowcolor=cls.COLORS['accent'],
            bordercolor=cls.COLORS['border'],
        )
        
        style.configure('TCheckbutton',
            background=cls.COLORS['bg_dark'],
            foreground=cls.COLORS['text_primary'],
            font=cls.FONTS['body'],
        )
        
        style.map('TCheckbutton',
            background=[('active', cls.COLORS['bg_dark'])],
        )
        
        style.configure('TRadiobutton',
            background=cls.COLORS['bg_dark'],
            foreground=cls.COLORS['text_primary'],
            font=cls.FONTS['body'],
        )
        
        style.map('TRadiobutton',
            background=[('active', cls.COLORS['bg_dark'])],
        )
        
        style.configure('TLabelframe',
            background=cls.COLORS['card_bg'],
            foreground=cls.COLORS['accent'],
            bordercolor=cls.COLORS['border'],
            relief='flat',
        )
        
        style.configure('TLabelframe.Label',
            background=cls.COLORS['card_bg'],
            foreground=cls.COLORS['accent'],
            font=cls.FONTS['subtitle'],
        )
        
        style.configure('Card.TLabelframe',
            background=cls.COLORS['card_bg'],
            bordercolor=cls.COLORS['border'],
        )
        
        style.configure('Card.TLabelframe.Label',
            background=cls.COLORS['card_bg'],
            foreground=cls.COLORS['success'],
            font=cls.FONTS['subtitle'],
        )
        
        style.configure('TNotebook',
            background=cls.COLORS['bg_dark'],
            bordercolor=cls.COLORS['border'],
        )
        
        style.configure('TNotebook.Tab',
            background=cls.COLORS['bg_medium'],
            foreground=cls.COLORS['text_secondary'],
            padding=(20, 10),
            font=cls.FONTS['body'],
        )
        
        style.map('TNotebook.Tab',
            background=[
                ('selected', cls.COLORS['bg_light']),
                ('active', cls.COLORS['bg_light']),
            ],
            foreground=[
                ('selected', cls.COLORS['text_primary']),
                ('active', cls.COLORS['accent']),
            ],
        )
        
        style.configure('TProgressbar',
            background=cls.COLORS['accent'],
            troughcolor=cls.COLORS['bg_medium'],
            bordercolor=cls.COLORS['border'],
            lightcolor=cls.COLORS['accent'],
            darkcolor=cls.COLORS['accent'],
        )
        
        style.configure('Success.Horizontal.TProgressbar',
            background=cls.COLORS['success'],
            troughcolor=cls.COLORS['bg_medium'],
        )
        
        style.configure('Treeview',
            background=cls.COLORS['bg_medium'],
            foreground=cls.COLORS['text_primary'],
            fieldbackground=cls.COLORS['bg_medium'],
            bordercolor=cls.COLORS['border'],
            font=cls.FONTS['body'],
        )
        
        style.configure('Treeview.Heading',
            background=cls.COLORS['bg_light'],
            foreground=cls.COLORS['text_primary'],
            font=cls.FONTS['subtitle'],
        )
        
        style.map('Treeview',
            background=[('selected', cls.COLORS['accent'])],
            foreground=[('selected', cls.COLORS['text_primary'])],
        )
        
        style.configure('TScrollbar',
            background=cls.COLORS['bg_medium'],
            troughcolor=cls.COLORS['bg_dark'],
            bordercolor=cls.COLORS['border'],
            arrowcolor=cls.COLORS['accent'],
        )
        
        style.configure('Horizontal.TScrollbar',
            background=cls.COLORS['bg_medium'],
            troughcolor=cls.COLORS['bg_dark'],
        )
        
        style.configure('TScale',
            background=cls.COLORS['bg_dark'],
            troughcolor=cls.COLORS['bg_medium'],
            bordercolor=cls.COLORS['border'],
        )
        
        style.configure('TSeparator',
            background=cls.COLORS['border'],
        )
        
        return style


class ModernWidgets:
    """现代化组件工厂"""
    
    @staticmethod
    def create_card(parent, title=None, **kwargs):
        """创建卡片容器"""
        frame = ttk.Frame(parent, style='Card.TFrame', **kwargs)
        frame.configure(padding=16)
        
        if title:
            title_label = ttk.Label(frame, text=title, style='Subtitle.TLabel')
            title_label.pack(anchor='w', pady=(0, 12))
        
        return frame
    
    @staticmethod
    def create_button(parent, text, command=None, style='TButton', **kwargs):
        """创建按钮"""
        btn = ttk.Button(parent, text=text, command=command, style=style, **kwargs)
        return btn
    
    @staticmethod
    def create_icon_button(parent, icon, text, command=None, **kwargs):
        """创建带图标的按钮"""
        btn_text = f"{icon} {text}"
        btn = ttk.Button(parent, text=btn_text, command=command, **kwargs)
        return btn
    
    @staticmethod
    def create_entry(parent, placeholder=None, **kwargs):
        """创建输入框"""
        entry = ttk.Entry(parent, **kwargs)
        
        if placeholder:
            entry.insert(0, placeholder)
            entry.configure(foreground=ModernTheme.COLORS['text_hint'])
            
            def on_focus_in(event):
                if entry.get() == placeholder:
                    entry.delete(0, tk.END)
                    entry.configure(foreground=ModernTheme.COLORS['text_primary'])
            
            def on_focus_out(event):
                if not entry.get():
                    entry.insert(0, placeholder)
                    entry.configure(foreground=ModernTheme.COLORS['text_hint'])
            
            entry.bind('<FocusIn>', on_focus_in)
            entry.bind('<FocusOut>', on_focus_out)
        
        return entry
    
    @staticmethod
    def create_status_label(parent, text, status='info'):
        """创建状态标签"""
        style_map = {
            'success': 'Success.TLabel',
            'warning': 'Warning.TLabel',
            'error': 'Error.TLabel',
            'accent': 'Accent.TLabel',
        }
        style = style_map.get(status, 'TLabel')
        return ttk.Label(parent, text=text, style=style)


def apply_rounded_corners(widget, radius=8):
    """为控件应用圆角效果（Windows 11风格）"""
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetParent(widget.winfo_id())
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        DWMWCP_ROUND = 2
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, 
            ctypes.byref(ctypes.c_int(DWMWCP_ROUND)), 
            ctypes.sizeof(ctypes.c_int)
        )
    except:
        pass


def create_tooltip(widget, text):
    """创建工具提示"""
    def show_tooltip(event):
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
        
        label = tk.Label(
            tooltip, text=text,
            background=ModernTheme.COLORS['bg_light'],
            foreground=ModernTheme.COLORS['text_primary'],
            relief='flat',
            padx=8, pady=4,
            font=('Segoe UI', 9)
        )
        label.pack()
        
        widget._tooltip = tooltip
        
        def hide_tooltip(event):
            if hasattr(widget, '_tooltip'):
                widget._tooltip.destroy()
                del widget._tooltip
        
        widget.bind('<Leave>', hide_tooltip)
    
    widget.bind('<Enter>', show_tooltip)
