import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import barcode
from barcode.writer import ImageWriter
import io
import os

# ================= 1. 核心图像引擎 =================

def make_label_50x30(sku, title, spec):
    """
    生成 LxU 专属 50x30mm 高清标签 (自适应智能排版版)
    布局优化：SKU上移，标题强制最多两行且字体大小自动缩放，彻底解决重叠。
    """
    width, height = 1000, 600 
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)

    def load_font(size, is_bold=False):
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

    # --- 1. 顶部条形码 ---
    try:
        code_factory = barcode.get_barcode_class('code128')
        c128 = code_factory(sku, writer=ImageWriter())
        buf = io.BytesIO()
        c128.write(buf, options={"module_height": 20.0, "module_width": 0.4, "font_size": 0, "quiet_zone": 1})
        b_img = Image.open(buf).resize((900, 230)) 
        img.paste(b_img, (50, 20)) 
    except Exception as e: 
        st.error(f"条形码生成失败: {e}")

    f_sku = load_font(68, is_bold=True)
    f_bottom = load_font(42)

    # 绘制 SKU
    draw.text((500, 285), sku, fill='black', font=f_sku, anchor="mm")
    # 绘制底部 MADE IN CHINA
    draw.text((500, 570), "MADE IN CHINA", fill='black', font=f_bottom, anchor="mm")

    # --- 2. 智能排版引擎：动态字体缩放 + 最多两行 ---
    full_title = f"{title} {spec}".strip()
    max_text_width = 850 
    
    font_size = 80 # 从极大的字体开始尝试
    wrapped_lines = []
    final_font = None

    while font_size > 20:
        f_test = load_font(font_size, is_bold=True)
        words = full_title.split()
        
        # 辅助函数：获取文字真实宽度
        def get_w(t): return draw.textbbox((0,0), t, font=f_test)[2]
        
        # 尝试 1：如果一行就能装下
        if get_w(full_title) <= max_text_width:
            wrapped_lines = [full_title]
            final_font = f_test
            break
            
        # 尝试 2：尝试在空格处切分成两行
        best_split = None
        for i in range(1, len(words)):
            l1 = " ".join(words[:i])
            l2 = " ".join(words[i:])
            if get_w(l1) <= max_text_width and get_w(l2) <= max_text_width:
                # 寻找最均衡的切分点（上下两行宽度差异最小）
                diff = abs(get_w(l1) - get_w(l2))
                if best_split is None or diff < best_split[0]:
                    best_split = (diff, [l1, l2])
        
        if best_split:
            wrapped_lines = best_split[1]
            final_font = f_test
            break
            
        # 如果当前字体连两行都装不下，缩小字体继续循环
        font_size -= 2 

    # 兜底方案（极端情况，比如全是一个长词没有空格）
    if not wrapped_lines:
        final_font = load_font(40, is_bold=True)
        wrapped_lines = [full_title]

    # --- 3. 绘制居中标题 ---
    # 💡 核心修复：基于字体大小乘以 1.3 倍作为安全行高，绝不重叠！
    line_height = int(font_size * 1.3)
    
    center_y_area = 425 
    start_y = center_y_area - ((len(wrapped_lines) * line_height) / 2) + (line_height / 2)

    current_y = start_y
    for line in wrapped_lines:
        draw.text((500, current_y), line, fill='black', font=final_font, anchor="mm")
        current_y += line_height
        
    return img

# ================= 2. 界面配置与布局 =================

st.set_page_config(page_title="LxU 标签生成器", page_icon="🏷️", layout="centered")

st.title("🏷️ LxU 50x30 高清标签生成器")
st.info("💡 **自适应排版引擎已激活**：商品名称将自动寻找最佳折行点，并根据长短动态缩放字体，确保最多两行且绝不重叠。")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 📝 输入商品信息")
    v_sku = st.text_input("货号 (SKU)", "S0033507379541")
    v_title = st.text_input("韩文品名", "[LxU] 강력한 자석 현관문 도어벨 풍경")
    v_spec = st.text_input("规格参数", "황동/우드 마그네틱 부착형")
    
    st.markdown("<br>", unsafe_allow_html=True)
    generate_btn = st.button("🚀 生成高清标签", use_container_width=True, type="primary")

with col2:
    st.markdown("### 🖨️ 预览与下载")
    if generate_btn or 'l_img' not in st.session_state:
        if v_sku and v_title:
            with st.spinner("极速智能排版中..."):
                st.session_state.l_img = make_label_50x30(v_sku, v_title, v_spec)
        else:
            st.warning("请填写完整的 SKU 和品名！")

    if 'l_img' in st.session_state:
        st.image(st.session_state.l_img, caption="1000x600 px (50x30mm @ 300DPI)", use_column_width=True)
        
        b = io.BytesIO()
        st.session_state.l_img.save(b, format="PNG", dpi=(300, 300))
        
        st.download_button(
            label="📥 一键下载标签 (PNG)", 
            data=b.getvalue(), 
            file_name=f"LxU_Label_{v_sku}.png", 
            mime="image/png",
            use_container_width=True
        )
