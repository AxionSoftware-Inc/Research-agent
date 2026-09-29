import os
from PIL import Image, ImageDraw

def create_app_icon():
    size = 1024
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Outer rounded rect (dark slate background with subtle border)
    radius = 220
    # Background
    bg_color = (15, 23, 42, 255) # Slate 900
    border_color = (56, 189, 248, 180) # Sky 400
    draw.rounded_rectangle([40, 40, size - 40, size - 40], radius=radius, fill=bg_color, outline=border_color, width=16)
    
    # Inner glowing elements - minimalist futuristic AI core
    center = size // 2
    
    # Draw central hexagon or diamond
    outer_diamond = [
        (center, center - 260),
        (center + 260, center),
        (center, center + 260),
        (center - 260, center),
    ]
    draw.polygon(outer_diamond, outline=(14, 165, 233, 220), width=18)
    
    inner_diamond = [
        (center, center - 160),
        (center + 160, center),
        (center, center + 160),
        (center - 160, center),
    ]
    draw.polygon(inner_diamond, fill=(2, 132, 199, 200), outline=(56, 189, 248, 255), width=12)
    
    # Core circle
    core_r = 70
    draw.ellipse([center - core_r, center - core_r, center + core_r, center + core_r], fill=(255, 255, 255, 255))
    
    # 4 satellite nodes
    node_r = 30
    nodes = [
        (center, center - 260),
        (center + 260, center),
        (center, center + 260),
        (center - 260, center),
    ]
    for nx, ny in nodes:
        draw.ellipse([nx - node_r, ny - node_r, nx + node_r, ny + node_r], fill=(56, 189, 248, 255), outline=(255, 255, 255, 255), width=6)
        
    out_dir = os.path.join("frontend", "public")
    os.makedirs(out_dir, exist_ok=True)
    out_png = os.path.join(out_dir, "app-icon.png")
    img.save(out_png, "PNG")
    print(f"Generated {out_png}")
    return out_png

if __name__ == "__main__":
    create_app_icon()
