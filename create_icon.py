from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    """创建网页下载器图标"""
    # 创建不同尺寸的图标
    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    
    for size in sizes:
        # 创建透明背景的图像
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 计算中心和半径
        center = size // 2
        radius = int(size * 0.4)
        
        # 绘制地球（蓝色圆形）
        draw.ellipse([center - radius, center - radius, center + radius, center + radius],
                    fill='#3498db', outline='#2980b9', width=max(1, size // 32))
        
        # 绘制下载箭头（白色）
        arrow_size = int(size * 0.15)
        arrow_x = center
        arrow_y = center
        
        # 箭头主体
        draw.polygon([
            (arrow_x, arrow_y - arrow_size),
            (arrow_x - arrow_size * 0.7, arrow_y),
            (arrow_x - arrow_size * 0.3, arrow_y),
            (arrow_x - arrow_size * 0.3, arrow_y + arrow_size),
            (arrow_x + arrow_size * 0.3, arrow_y + arrow_size),
            (arrow_x + arrow_size * 0.3, arrow_y),
            (arrow_x + arrow_size * 0.7, arrow_y)
        ], fill='white')
        
        # 添加一些装饰线条（经纬线效果）
        line_width = max(1, size // 64)
        draw.arc([center - radius * 0.7, center - radius * 0.7, center + radius * 0.7, center + radius * 0.7],
                0, 180, fill='#2980b9', width=line_width)
        draw.arc([center - radius * 0.5, center - radius * 0.5, center + radius * 0.5, center + radius * 0.5],
                180, 360, fill='#2980b9', width=line_width)
        
        images.append(img)
    
    # 保存为ICO文件
    icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
    images[0].save(icon_path, format='ICO', sizes=[(size, size) for size in sizes])
    print(f"图标已创建: {icon_path}")
    return icon_path

if __name__ == "__main__":
    create_icon()