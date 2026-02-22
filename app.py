import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import os

def load_font(size, is_bold=False):
    """
    思源黑体 (Source Han Sans / Noto Sans CJK) 专项优化版
    - 优先加载 ExtraLight/Light 权重，形如雅致版微软雅黑
    """
    font_configs = [
        # 1. Linux/Streamlit Cloud 环境 (Noto Sans CJK)
        {"path": "/usr/share/fonts/opentype/noto/NotoSansCJK-Light.ttc", "index": 0},
        {"path": "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "index": 0},
        
        # 2. 如果你本地下载了思源黑体放在代码目录，请改名并放这里
        {"path": "SourceHanSansCN-ExtraLight.otf", "index": 0},
        
        # 3. Windows 备选方案 (如果你本地安装了思源黑体)
        {"path": "C:/Windows/Fonts/SourceHanSansCN-Light.otf", "index": 0},
        
        # 4. 极致保底
        {"path": "C:/Windows/Fonts/msyhl.ttc", "index": 0}, 
        {"path": "/usr/share/fonts/truetype/nanum/NanumGothic.ttf", "index": 0}
    ]

    # 如果需要加粗（用于规格参数），优先找 Bold 或 Regular 路径
    if is_bold:
        # 这里逻辑简单化，直接寻找非 Light 的字体
        for cfg in reversed(font_configs): # 倒序寻找通常能找到更重的权重
            if os.path.exists(cfg["path"]):
                return ImageFont.truetype(cfg["path"], size, index=cfg["index"])

    # 默认加载极细体
    for cfg in font_configs:
        if os.path.exists(cfg["path"]):
            try:
                return ImageFont.truetype(cfg["path"], size, index=cfg["index"])
            except:
                continue
    return ImageFont.load_default()
