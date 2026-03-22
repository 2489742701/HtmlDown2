import tkinter as tk
from tkinter import ttk

class UIStyles:
    """UI 样式配置"""
    
    COLORS = {
        'primary': '#10b981',
        'primary_light': '#34d399',
        'primary_dark': '#059669',
        'secondary': '#14b8a6',
        'bg_main': '#050505',
        'bg_card': '#0a0a0a',
        'bg_glass': '#0a0a0a',
        'text_primary': '#e0e0e0',
        'text_secondary': '#a1a1aa',
        'border': '#1a1a1a',
        'shadow': '#10b98120',
        'success': '#22c55e',
        'warning': '#f59e0b',
        'error': '#ef4444',
        'info': '#3b82f6',
    }
    
    FONTS = {
        'title': ('Microsoft YaHei UI', 16, 'bold'),
        'heading': ('Microsoft YaHei UI', 14, 'bold'),
        'body': ('Microsoft YaHei UI', 10, 'normal'),
        'small': ('Microsoft YaHei UI', 9, 'normal'),
        'mono': ('Consolas', 10, 'normal'),
    }
    
    SHADOWS = {
        'card': '0 0 30px rgba(16, 185, 129, 0.1)',
        'button': '0 0 15px rgba(16, 185, 129, 0.3)',
        'glow': '0 0 20px rgba(16, 185, 129, 0.5)',
    }
    
    @staticmethod
    def configure_style(style):
        """配置 ttk 样式"""
        try:
            style.theme_use('clam')
        except:
            pass
        
        style.configure(
            'Modern.TButton',
            font=UIStyles.FONTS['body'],
            background=UIStyles.COLORS['primary'],
            foreground='white',
            borderwidth=0,
            focuscolor=UIStyles.COLORS['primary_light'],
            relief='flat',
            padding=(25, 12)
        )
        
        style.map(
            'Modern.TButton',
            background=[
                ('active', UIStyles.COLORS['primary_dark']),
                ('pressed', UIStyles.COLORS['primary_dark'])
            ]
        )
        
        style.configure(
            'Glass.TFrame',
            background=UIStyles.COLORS['bg_glass'],
            borderwidth=1,
            relief='solid'
        )
        
        style.configure(
            'Modern.TLabel',
            font=UIStyles.FONTS['body'],
            background=UIStyles.COLORS['bg_main'],
            foreground=UIStyles.COLORS['text_primary']
        )
        
        style.configure(
            'Heading.TLabel',
            font=UIStyles.FONTS['heading'],
            background=UIStyles.COLORS['bg_main'],
            foreground=UIStyles.COLORS['primary_light']
        )
        
        style.configure(
            'Modern.TEntry',
            font=UIStyles.FONTS['body'],
            fieldbackground=UIStyles.COLORS['bg_card'],
            foreground=UIStyles.COLORS['text_primary'],
            borderwidth=1,
            relief='solid',
            insertcolor=UIStyles.COLORS['primary'],
            selectbackground=UIStyles.COLORS['primary'],
            selectforeground='white'
        )
        
        style.map(
            'Modern.TEntry',
            focuscolor=[('focus', UIStyles.COLORS['primary'])]
        )
        
        style.configure(
            'Card.TFrame',
            background=UIStyles.COLORS['bg_card'],
            borderwidth=1,
            relief='solid'
        )
        
        style.configure(
            'Nav.TButton',
            font=UIStyles.FONTS['body'],
            background=UIStyles.COLORS['bg_main'],
            foreground=UIStyles.COLORS['text_secondary'],
            borderwidth=0,
            relief='flat',
            anchor='w',
            padding=(15, 12)
        )
        
        style.map(
            'Nav.TButton',
            background=[
                ('active', UIStyles.COLORS['bg_card']),
                ('pressed', UIStyles.COLORS['bg_card'])
            ],
            foreground=[
                ('active', UIStyles.COLORS['primary_light']),
                ('pressed', UIStyles.COLORS['primary_light'])
            ]
        )
        
        style.configure(
            'Modern.TNotebook',
            background=UIStyles.COLORS['bg_main'],
            borderwidth=0,
            tabposition='n'
        )
        
        style.configure(
            'Modern.TNotebook.Tab',
            background=UIStyles.COLORS['bg_main'],
            foreground=UIStyles.COLORS['text_secondary'],
            padding=[20, 10],
            borderwidth=0
        )
        
        style.map(
            'Modern.TNotebook.Tab',
            background=[
                ('selected', UIStyles.COLORS['bg_card']),
                ('active', UIStyles.COLORS['bg_card'])
            ],
            foreground=[
                ('selected', UIStyles.COLORS['primary_light']),
                ('active', UIStyles.COLORS['primary'])
            ]
        )
        
        style.configure(
            'Modern.TProgressbar',
            thickness=8,
            troughcolor=UIStyles.COLORS['bg_card'],
            background=UIStyles.COLORS['primary'],
            borderwidth=0,
            relief='flat'
        )
        
        style.configure(
            'Horizontal.TProgressbar',
            thickness=8,
            troughcolor=UIStyles.COLORS['bg_card'],
            background=UIStyles.COLORS['primary'],
            borderwidth=0,
            relief='flat'
        )
    
    @staticmethod
    def get_color(name):
        """获取颜色"""
        return UIStyles.COLORS.get(name, '#000000')
    
    @staticmethod
    def get_font(name):
        """获取字体"""
        return UIStyles.FONTS.get(name, ('Microsoft YaHei UI', 10, 'normal'))
