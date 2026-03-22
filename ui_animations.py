"""
UI 动画效果模块
提供窗口淡入淡出、输入框动画、弹窗动画等效果
"""

import tkinter as tk
from tkinter import ttk
import threading
import time


class WindowAnimation:
    """窗口动画效果类"""
    
    @staticmethod
    def fade_in(window, duration=300, steps=20, on_complete=None):
        """
        窗口淡入效果
        
        Args:
            window: tkinter窗口对象
            duration: 动画持续时间(毫秒)
            steps: 动画步数
            on_complete: 动画完成后的回调函数
        """
        try:
            # 确保窗口已创建
            window.update_idletasks()
            
            # 设置初始透明度为0
            window.attributes('-alpha', 0.0)
            window.deiconify()
            
            step_duration = duration // steps
            alpha_step = 1.0 / steps
            current_alpha = 0.0
            
            def _fade_step(step=0):
                if step >= steps:
                    window.attributes('-alpha', 1.0)
                    if on_complete:
                        on_complete()
                    return
                
                current_alpha = (step + 1) * alpha_step
                window.attributes('-alpha', current_alpha)
                window.after(step_duration, lambda: _fade_step(step + 1))
            
            _fade_step()
        except Exception as e:
            # 如果动画失败，直接显示窗口
            try:
                window.attributes('-alpha', 1.0)
                window.deiconify()
            except:
                pass
            if on_complete:
                on_complete()
    
    @staticmethod
    def fade_out(window, duration=200, steps=15, on_complete=None):
        """
        窗口淡出效果
        
        Args:
            window: tkinter窗口对象
            duration: 动画持续时间(毫秒)
            steps: 动画步数
            on_complete: 动画完成后的回调函数
        """
        try:
            if not window.winfo_exists():
                if on_complete:
                    on_complete()
                return
            
            step_duration = duration // steps
            alpha_step = 1.0 / steps
            
            def _fade_step(step=0):
                try:
                    if not window.winfo_exists():
                        if on_complete:
                            on_complete()
                        return
                    
                    if step >= steps:
                        # 动画完成，设置透明度为0
                        try:
                            window.attributes('-alpha', 0.0)
                        except:
                            pass
                        # 延迟执行回调，确保动画完全结束
                        if on_complete:
                            window.after(10, on_complete)
                        return
                    
                    current_alpha = 1.0 - (step + 1) * alpha_step
                    window.attributes('-alpha', max(0.0, current_alpha))
                    window.after(step_duration, lambda: _fade_step(step + 1))
                except Exception as e:
                    # 动画出错，直接执行回调
                    if on_complete:
                        on_complete()
            
            _fade_step()
        except Exception as e:
            # 如果动画失败，直接执行回调
            if on_complete:
                on_complete()
    
    @staticmethod
    def slide_in(window, direction='top', duration=300, distance=None, on_complete=None):
        """
        窗口滑入效果
        
        Args:
            window: tkinter窗口对象
            direction: 滑入方向 ('top', 'bottom', 'left', 'right')
            duration: 动画持续时间(毫秒)
            distance: 滑动距离(像素)，None则使用窗口大小
            on_complete: 动画完成后的回调函数
        """
        try:
            window.update_idletasks()
            
            # 获取窗口最终位置
            final_x = window.winfo_x()
            final_y = window.winfo_y()
            width = window.winfo_width()
            height = window.winfo_height()
            
            # 计算滑动距离
            if distance is None:
                if direction in ['top', 'bottom']:
                    distance = height
                else:
                    distance = width
            
            # 设置初始位置
            if direction == 'top':
                start_x, start_y = final_x, final_y - distance
            elif direction == 'bottom':
                start_x, start_y = final_x, final_y + distance
            elif direction == 'left':
                start_x, start_y = final_x - distance, final_y
            else:  # right
                start_x, start_y = final_x + distance, final_y
            
            window.geometry(f"+{start_x}+{start_y}")
            window.deiconify()
            
            steps = 20
            step_duration = duration // steps
            x_step = (final_x - start_x) / steps
            y_step = (final_y - start_y) / steps
            
            def _slide_step(step=0):
                if step >= steps:
                    window.geometry(f"+{final_x}+{final_y}")
                    if on_complete:
                        on_complete()
                    return
                
                current_x = int(start_x + x_step * (step + 1))
                current_y = int(start_y + y_step * (step + 1))
                window.geometry(f"+{current_x}+{current_y}")
                window.after(step_duration, lambda: _slide_step(step + 1))
            
            _slide_step()
        except Exception as e:
            if on_complete:
                on_complete()
    
    @staticmethod
    def scale_in(window, duration=300, on_complete=None):
        """
        窗口缩放进入效果
        
        Args:
            window: tkinter窗口对象
            duration: 动画持续时间(毫秒)
            on_complete: 动画完成后的回调函数
        """
        try:
            window.update_idletasks()
            
            final_width = window.winfo_width()
            final_height = window.winfo_height()
            x = window.winfo_x()
            y = window.winfo_y()
            
            steps = 15
            step_duration = duration // steps
            
            def _scale_step(step=0):
                if step >= steps:
                    window.geometry(f"{final_width}x{final_height}+{x}+{y}")
                    if on_complete:
                        on_complete()
                    return
                
                scale = (step + 1) / steps
                current_width = int(final_width * scale)
                current_height = int(final_height * scale)
                offset_x = (final_width - current_width) // 2
                offset_y = (final_height - current_height) // 2
                window.geometry(f"{current_width}x{current_height}+{x + offset_x}+{y + offset_y}")
                window.after(step_duration, lambda: _scale_step(step + 1))
            
            _scale_step()
        except Exception as e:
            if on_complete:
                on_complete()


class InputAnimation:
    """输入框动画效果类"""
    
    @staticmethod
    def focus_blink(entry, color='#2196f3', duration=300):
        """
        输入框聚焦闪烁效果
        
        Args:
            entry: Entry或Text对象
            color: 闪烁颜色
            duration: 动画持续时间(毫秒)
        """
        try:
            original_bg = entry.cget('bg')
            original_highlight = entry.cget('highlightbackground')
            
            steps = 6
            step_duration = duration // steps
            
            def _blink_step(step=0):
                if step >= steps:
                    entry.config(bg=original_bg, highlightbackground=original_highlight)
                    return
                
                if step % 2 == 0:
                    entry.config(bg=color, highlightbackground=color)
                else:
                    entry.config(bg=original_bg, highlightbackground=original_highlight)
                
                entry.after(step_duration, lambda: _blink_step(step + 1))
            
            _blink_step()
        except:
            pass
    
    @staticmethod
    def shake(entry, duration=300, intensity=5):
        """
        输入框抖动效果（用于验证错误）
        
        Args:
            entry: Entry对象
            duration: 动画持续时间(毫秒)
            intensity: 抖动强度(像素)
        """
        try:
            original_x = entry.winfo_x()
            steps = 10
            step_duration = duration // steps
            
            def _shake_step(step=0):
                if step >= steps:
                    entry.place(x=original_x)
                    return
                
                offset = intensity if step % 2 == 0 else -intensity
                if step % 4 >= 2:
                    offset = -offset
                
                entry.place(x=original_x + offset)
                entry.after(step_duration, lambda: _shake_step(step + 1))
            
            _shake_step()
        except:
            pass
    
    @staticmethod
    def typing_effect(entry, text, speed=50, on_complete=None):
        """
        打字机效果
        
        Args:
            entry: Entry或Text对象
            text: 要显示的文本
            speed: 打字速度(毫秒/字符)
            on_complete: 动画完成后的回调函数
        """
        try:
            entry.delete(0, 'end') if hasattr(entry, 'delete') else entry.delete('1.0', 'end')
            
            def _type_char(index=0):
                if index >= len(text):
                    if on_complete:
                        on_complete()
                    return
                
                char = text[index]
                if hasattr(entry, 'insert'):
                    if hasattr(entry, 'get'):  # Entry
                        entry.insert('end', char)
                    else:  # Text
                        entry.insert('end', char)
                
                entry.after(speed, lambda: _type_char(index + 1))
            
            _type_char()
        except:
            if on_complete:
                on_complete()


class DialogAnimation:
    """弹窗动画效果类"""
    
    @staticmethod
    def show_dialog(dialog, parent=None, animation_type='fade', duration=300):
        """
        显示弹窗并应用动画效果
        
        Args:
            dialog: 弹窗窗口对象
            parent: 父窗口
            animation_type: 动画类型 ('fade', 'slide', 'scale')
            duration: 动画持续时间(毫秒)
        """
        try:
            if animation_type == 'fade':
                WindowAnimation.fade_in(dialog, duration)
            elif animation_type == 'slide':
                WindowAnimation.slide_in(dialog, 'top', duration)
            elif animation_type == 'scale':
                WindowAnimation.scale_in(dialog, duration)
            else:
                dialog.deiconify()
        except:
            dialog.deiconify()
    
    @staticmethod
    def close_dialog(dialog, animation_type='fade', duration=200, on_complete=None):
        """
        关闭弹窗并应用动画效果
        
        Args:
            dialog: 弹窗窗口对象
            animation_type: 动画类型 ('fade', 'slide', 'scale')
            duration: 动画持续时间(毫秒)
            on_complete: 动画完成后的回调函数
        """
        def _do_close():
            try:
                dialog.destroy()
            except:
                pass
            if on_complete:
                on_complete()
        
        try:
            if animation_type == 'fade':
                WindowAnimation.fade_out(dialog, duration, on_complete=_do_close)
            else:
                _do_close()
        except:
            _do_close()


class ButtonAnimation:
    """按钮动画效果类"""
    
    @staticmethod
    def pulse(button, color='#2196f3', duration=600):
        """
        按钮脉冲效果
        
        Args:
            button: Button对象
            color: 脉冲颜色
            duration: 动画持续时间(毫秒)
        """
        try:
            original_bg = button.cget('bg')
            steps = 12
            step_duration = duration // steps
            
            def _pulse_step(step=0):
                if step >= steps:
                    button.config(bg=original_bg)
                    return
                
                # 模拟颜色渐变
                intensity = abs((step % 6) - 3) / 3.0
                button.config(bg=color if intensity > 0.5 else original_bg)
                
                button.after(step_duration, lambda: _pulse_step(step + 1))
            
            _pulse_step()
        except:
            pass
    
    @staticmethod
    def press_effect(button, duration=100):
        """
        按钮按下效果
        
        Args:
            button: Button对象
            duration: 动画持续时间(毫秒)
        """
        try:
            original_relief = button.cget('relief')
            button.config(relief='sunken')
            button.after(duration, lambda: button.config(relief=original_relief))
        except:
            pass


class LoadingAnimation:
    """加载动画效果类"""
    
    def __init__(self, parent, text="加载中..."):
        """
        初始化加载动画
        
        Args:
            parent: 父窗口
            text: 加载文本
        """
        self.parent = parent
        self.text = text
        self.window = None
        self._stop_flag = False
        self._animating = False
    
    def show(self, animation_type='fade'):
        """显示加载动画"""
        try:
            self.window = tk.Toplevel(self.parent)
            self.window.title("")
            self.window.geometry("200x100")
            self.window.resizable(False, False)
            self.window.overrideredirect(True)
            self.window.transient(self.parent)
            self.window.grab_set()
            
            # 居中显示
            self.window.update_idletasks()
            x = (self.window.winfo_screenwidth() // 2) - 100
            y = (self.window.winfo_screenheight() // 2) - 50
            self.window.geometry(f"+{x}+{y}")
            
            # 创建加载界面
            frame = tk.Frame(self.window, bg='#f5f5f5', padx=20, pady=20)
            frame.pack(fill='both', expand=True)
            
            self.label = tk.Label(
                frame,
                text=self.text,
                font=('Microsoft YaHei', 10),
                bg='#f5f5f5',
                fg='#333'
            )
            self.label.pack()
            
            self.dots_label = tk.Label(
                frame,
                text="",
                font=('Microsoft YaHei', 12),
                bg='#f5f5f5',
                fg='#2196f3'
            )
            self.dots_label.pack()
            
            # 应用淡入动画
            if animation_type == 'fade':
                WindowAnimation.fade_in(self.window, duration=200)
            else:
                self.window.deiconify()
            
            # 开始动画
            self._stop_flag = False
            self._animate_dots()
            
        except Exception as e:
            print(f"[Error] Failed to show loading animation: {e}")
    
    def _animate_dots(self):
        """动画点"""
        if self._stop_flag or not self.window or not self.window.winfo_exists():
            return
        
        try:
            dots = ["", ".", "..", "..."]
            current = getattr(self, '_dot_index', 0)
            self.dots_label.config(text=dots[current])
            self._dot_index = (current + 1) % len(dots)
            
            if not self._stop_flag:
                self.window.after(300, self._animate_dots)
        except:
            pass
    
    def hide(self, animation_type='fade'):
        """隐藏加载动画"""
        self._stop_flag = True
        
        def _destroy():
            try:
                if self.window and self.window.winfo_exists():
                    self.window.destroy()
            except:
                pass
            self.window = None
        
        try:
            if self.window and self.window.winfo_exists():
                if animation_type == 'fade':
                    WindowAnimation.fade_out(self.window, duration=150, on_complete=_destroy)
                else:
                    _destroy()
            else:
                _destroy()
        except:
            _destroy()
    
    def set_text(self, text):
        """设置加载文本"""
        self.text = text
        try:
            if self.label and self.label.winfo_exists():
                self.label.config(text=text)
        except:
            pass


# 便捷的动画函数
def animate_window_open(window, animation='fade', duration=300):
    """便捷函数：窗口打开动画"""
    if animation == 'fade':
        WindowAnimation.fade_in(window, duration)
    elif animation == 'slide':
        WindowAnimation.slide_in(window, 'top', duration)
    elif animation == 'scale':
        WindowAnimation.scale_in(window, duration)


def animate_window_close(window, animation='fade', duration=200, on_complete=None):
    """便捷函数：窗口关闭动画"""
    WindowAnimation.fade_out(window, duration, on_complete=on_complete)


def animate_dialog_show(dialog, animation='fade', duration=300):
    """便捷函数：弹窗显示动画"""
    DialogAnimation.show_dialog(dialog, animation_type=animation, duration=duration)


def animate_dialog_close(dialog, animation='fade', duration=200, on_complete=None):
    """便捷函数：弹窗关闭动画"""
    DialogAnimation.close_dialog(dialog, animation_type=animation, duration=duration, on_complete=on_complete)
