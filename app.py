import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import barcode
from barcode.writer import ImageWriter
import io
import os

# ================= 1. 核心图像引擎 =================

def wrap_text_pil(text, font, max_width, draw_surface):
    """辅助函数：计算文本宽度并实现自动折行"""
    lines = []
    paragraphs = text.split('\n')
    for paragraph in paragraphs:
        words = paragraph.split(' ')
        current_line = words[0]
        for word in words[1:]:
            test_line = current_line + " " + word
            if draw_surface.textlength(test_line, font=font) <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)
    return lines

def make_label_50x30(sku, title, spec):
    """
    生成 LxU 专属 50x30mm 高清标签
    BarCode 格式：Code 128 (Coupang 标准)
    布局：样本 1:1 复刻，中间标题自适应折行居中
    """
    width, height = 1000, 600 
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)

    def load_font(size, is_bold=False):
        # 兼容本地 Windows 测试和 Streamlit Cloud 线上环境的韩文字体
        font_paths = [
            "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf", 
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf", 
            "NanumGothic.ttf", 
            "C:/Windows/Fonts/malgunbd.ttf", 
            "C:/Windows/Fonts/malgun.ttf",
            "Arial.ttf"
        ]
        if not is_bold: font_paths.reverse()
        for p in font_paths:
            if os.path.exists(p): return ImageFont.truetype(p, size)
        return ImageFont.load_default()

    # --- 1. 顶部条形码 (固定位置) ---
    try:
        code_factory = barcode.get_barcode_class('code128')
        c128 = code_factory(sku, writer=ImageWriter())
        buf = io.BytesIO()
        c128.write(buf, options={"module_height": 22.0, "module_width": 0.4, "font_size": 0, "quiet_zone": 1})
        b_img = Image.open(buf).resize((900, 240))
        img.paste(b_img, (50, 25)) 
    except Exception as e: 
        st.error(f"条形码生成失败: {e}")

    # --- 2. 绘制内容 (字体大小已优化，防止打印溢出) ---
    f_sku = load_font(68, is_bold=True)
    f_title = load_font(52, is_bold=True)
    f_bottom = load_font(42)

    # 绘制 SKU
    draw.text((500, 315), sku, fill='black', font=f_sku, anchor="mm")

    # 绘制底部 MADE IN CHINA (固定位置)
    draw.text((500, 560), "MADE IN CHINA", fill='black', font=f_bottom, anchor="mm")

    # --- 3. 绘制中间标题 (安全边距折行 + 垂直居中) ---
    full_title = f"{title} {spec}".strip()
    max_text_width = 800 # 留出侧边边距
    line_padding = 6 
    
    # 获取字体高度
    bbox = f_title.getbbox("A")
    line_height = (bbox[3] - bbox[1]) + line_padding if bbox else 60
    
    wrapped_lines = wrap_text_pil(full_title, f_title, max_text_width, draw)
    
    center_y_area = 450
    start_y = center_y_area - ((len(wrapped_lines) * line_height) / 2) + (line_height / 2)

    current_y = start_y
    for line in wrapped_lines:
        draw.text((500, current_y), line, fill='black', font=f_title, anchor="mm")
        current_y += line_height
        
    return img

# ================= 2. 界面配置与布局 =================

st.set_page_config(page_title="LxU 标签生成器", page_icon="🏷️", layout="centered")

st.title("🏷️ LxU 50x30 高清标签生成器")
st.info("💡 **纯本地运算工具**：无需网络请求，生成速度极快，且不消耗任何 API 费用。")

# 采用双栏布局提升操作体验
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 📝 输入商品信息")
    v_sku = st.text_input("货号 (SKU)", "S0033507379541")
    v_title = st.text_input("韩文品名", "[LxU] 용접돋보기 고글형 확대경")
    v_spec = st.text_input("规格参数", "1.00배율 2개입")
    
    st.markdown("<br>", unsafe_allow_html=True)
    generate_btn = st.button("🚀 生成高清标签", use_container_width=True, type="primary")

with col2:
    st.markdown("### 🖨️ 预览与下载")
    # 首次加载或点击按钮时生成
    if generate_btn or 'l_img' not in st.session_state:
        if v_sku and v_title:
            with st.spinner("生成中..."):
                st.session_state.l_img = make_label_50x30(v_sku, v_title, v_spec)
        else:
            st.warning("请填写完整的 SKU 和品名！")

    if 'l_img' in st.session_state:
        # 显示图片预览，加上边框更显正式
        st.image(st.session_state.l_img, caption="1000x600 px (300 DPI)", use_column_width=True)
        
        # 准备下载数据
        b = io.BytesIO()
        st.session_state.l_img.save(b, format="PNG", dpi=(300, 300))
        
        st.download_button(
            label="📥 一键下载标签 (PNG)", 
            data=b.getvalue(), 
            file_name=f"LxU_Label_{v_sku}.png", 
            mime="image/png",
            use_container_width=True
        )
