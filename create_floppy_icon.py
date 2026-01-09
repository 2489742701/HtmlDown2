from PIL import Image, ImageDraw, ImageFont
import os

def create_floppy_download_icon():
    """创建软盘+下载图标"""
    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    
    for size in sizes:
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 颜色定义
        dark_gray = (60, 60, 60)
        medium_gray = (100, 100, 100)
        light_gray = (180, 180, 180)
        blue = (70, 130, 180)
        white = (255, 255, 255)
        shadow = (40, 40, 40)
        
        # 计算比例
        scale = size / 256.0
        
        # 软盘主体
        floppy_width = int(180 * scale)
        floppy_height = int(200 * scale)
        floppy_x = (size - floppy_width) // 2
        floppy_y = int(30 * scale)
        
        # 软盘阴影
        shadow_offset = int(4 * scale)
        draw.rectangle(
            [floppy_x + shadow_offset, floppy_y + shadow_offset, 
             floppy_x + floppy_width + shadow_offset, floppy_y + floppy_height + shadow_offset],
            fill=shadow
        )
        
        # 软盘主体
        draw.rectangle(
            [floppy_x, floppy_y, floppy_x + floppy_width, floppy_y + floppy_height],
            fill=medium_gray, outline=dark_gray, width=int(2 * scale)
        )
        
        # 软盘标签区域（上部）
        label_height = int(60 * scale)
        draw.rectangle(
            [floppy_x + int(10 * scale), floppy_y + int(10 * scale),
             floppy_x + floppy_width - int(10 * scale), floppy_y + label_height],
            fill=light_gray, outline=dark_gray, width=int(1 * scale)
        )
        
        # 软盘金属滑块（左上角）
        slider_width = int(50 * scale)
        slider_height = int(35 * scale)
        draw.rectangle(
            [floppy_x + int(20 * scale), floppy_y + int(20 * scale),
             floppy_x + int(20 * scale) + slider_width, floppy_y + int(20 * scale) + slider_height],
            fill=(200, 200, 220), outline=dark_gray, width=int(1 * scale)
        )
        
        # 软盘中心圆孔
        center_x = floppy_x + floppy_width // 2
        center_y = floppy_y + int(120 * scale)
        hole_radius = int(30 * scale)
        draw.ellipse(
            [center_x - hole_radius, center_y - hole_radius,
             center_x + hole_radius, center_y + hole_radius],
            fill=(30, 30, 30), outline=dark_gray, width=int(2 * scale)
        )
        
        # 软盘底部保护罩
        cover_height = int(50 * scale)
        draw.rectangle(
            [floppy_x + int(20 * scale), floppy_y + floppy_height - cover_height - int(10 * scale),
             floppy_x + floppy_width - int(20 * scale), floppy_y + floppy_height - int(10 * scale)],
            fill=(80, 80, 80), outline=dark_gray, width=int(1 * scale)
        )
        
        # 下载箭头（在软盘下方）
        arrow_size = int(60 * scale)
        arrow_x = size // 2
        arrow_y = floppy_y + floppy_height + int(30 * scale)
        
        # 下载箭头阴影
        draw.polygon([
            (arrow_x + shadow_offset, arrow_y + shadow_offset),
            (arrow_x - arrow_size//2 + shadow_offset, arrow_y - arrow_size//2 + shadow_offset),
            (arrow_x + arrow_size//2 + shadow_offset, arrow_y - arrow_size//2 + shadow_offset)
        ], fill=shadow)
        
        # 下载箭头主体
        draw.polygon([
            (arrow_x, arrow_y),
            (arrow_x - arrow_size//2, arrow_y - arrow_size//2),
            (arrow_x + arrow_size//2, arrow_y - arrow_size//2)
        ], fill=blue, outline=dark_gray, width=int(2 * scale))
        
        # 箭头杆
        line_width = int(8 * scale)
        draw.rectangle(
            [arrow_x - line_width//2, arrow_y - arrow_size//2 - int(20 * scale),
             arrow_x + line_width//2, arrow_y - arrow_size//2],
            fill=blue, outline=dark_gray, width=int(1 * scale)
        )
        
        # 箭头杆顶部的横线
        draw.rectangle(
            [arrow_x - arrow_size//2, arrow_y - arrow_size//2 - int(20 * scale) - int(5 * scale),
             arrow_x + arrow_size//2, arrow_y - arrow_size//2 - int(20 * scale)],
            fill=blue, outline=dark_gray, width=int(1 * scale)
        )
        
        images.append(img)
    
    # 保存为ICO文件
    images[0].save('icon.ico', format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("✅ 软盘+下载图标已创建: icon.ico")

if __name__ == "__main__":
    create_floppy_download_icon()
