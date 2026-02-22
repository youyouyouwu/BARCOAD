import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import barcode
from barcode.writer import ImageWriter
import io
import os

# ================= 1. 核心图像引擎 =================

def make_label_50x30(sku, title, spec):
    """
    生成 LxU 专属 50x30mm 高清标签 (视觉精修版)
    - 三行模式行间距设为 1.01，平衡紧凑度与清晰度
    - 维持品牌视觉规范：入库码(中)、品名(粗)、规格(暴力加粗)
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

    # --- 1. 扫码区 (Barcode + 入库码) ---
    try:
        code_factory = barcode.get_barcode_class('code128')
        c128 = code_factory(sku, writer=ImageWriter())
        buf = io.BytesIO()
        c128.write(buf, options={"module_height": 20.0, "module_width": 0.4, "font_size": 0, "quiet_zone": 1})
        b_img = Image.open(buf).resize((900, 220)) 
        img.paste(b_img, (50, 20)) 
    except: pass

    # 入库码数字：位置 270 紧贴条形码
    f_sku = load_font(68, is_bold=False)
    sku_pos = (500, 270)
    draw.text(sku_pos, sku, fill='black', font=f_sku, anchor="mm")
    draw.text((sku_pos[0] + 1, sku_pos[1]), sku, fill='black', font=f_sku, anchor="mm")

    # --- 2. 底部声明区 ---
    # MADE IN CHINA 居中，字号 32
    f_bottom = load_font(32, is_bold=False)
    draw.text((500, 575), "MADE IN CHINA", fill='black', font=f_bottom, anchor="mm")

    # --- 3. 核心信息区 (自适应 1-3 行) ---
    display_text = title
    if spec.strip():
        display_text = f"{title} / {spec.strip()}"
    
    max_text_width = 900 
    font_size = 78 
    wrapped_lines = []
    final_font_bold = None

    while font_size > 20:
        f_test = load_font(font_size, is_bold=True)
        def get_w(t): return draw.textbbox((0,0), t, font=f_test)[2]
        words = display_text.split()
        
        if get_w(display_text) <= max_text_width:
            wrapped_lines = [display_text]
            final_font_bold = f_test
            break
            
        best_2_split = None
        for i in range(1, len(words)):
            l1, l2 = " ".join(words[:i]), " ".join(words[i:])
            if get_w(l1) <= max_text_width and get_w(l2) <= max_text_width:
                diff = abs(get_w(l1) - get_w(l2))
                if best_2_split is None or diff < best_2_split[0]:
                    best_2_split = (diff, [l1, l2])
        if best_2_split:
            wrapped_lines = best_2_split[1]
            final_font_bold = f_test
            break

        best_3_split = None
        n = len(words)
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                l1, l2, l3 = " ".join(words[:i]), " ".join(words[i:j]), " ".join(words[j:])
                if get_w(l1) <= max_text_width and get_w(l2) <= max_text_width and get_w(l3) <= max_text_width:
                    w1, w2, w3 = get_w(l1), get_w(l2), get_w(l3)
                    diff = max(w1, w2, w3) - min(w1, w2, w3)
                    if best_3_split is None or diff < best_3_split[0]:
                        best_3_split = (diff, [l1, l2, l3])
        if best_3_split:
            wrapped_lines = best_3_split[1]
            final_font_bold = f_test
            break
        font_size -= 2 

    # 💡 核心微调：三行模式行间距设为 1.01
    if len(wrapped_lines) >= 3:
        multiplier = 1.01
    else:
        multiplier = 1.10
        
    line_height = int(font_size * multiplier)
    center_y_area = 422 
    start_y = center_y_area - ((len(wrapped_lines) * line_height) / 2) + (line_height / 2)

    current_y = start_y
    for line in wrapped_lines:
        if " / " in line:
            # 规格参数四重暴力加粗
            parts = line.split(" / ", 1)
            total_w = draw.textbbox((0,0), line, font=final_font_bold)[2]
            start_x = 500 - (total_w / 2)
            name_text = parts[0]
            draw.text((start_x, current_y), name_text, fill='black', font=final_font_bold, anchor="lm")
            slash_w = draw.textbbox((0,0), name_text, font=final_font_bold)[2]
            spec_text = " / " + parts[1]
            sp_pos = (start_x + slash_w, current_y)
            for dx, dy in [(0,0), (1,0), (0,1), (1,1)]:
                draw.text((sp_pos[0]+dx, sp_pos[1]+dy), spec_text, fill='black', font=final_font_bold, anchor="lm")
        else:
            draw.text((500, current_y), line, fill='black', font=final_font_bold, anchor="mm")
        current_y += line_height
        
    return img

# ================= 2. 界面展示逻辑 =================

st.set_page_config(page_title="LxU 标签生成器", page_icon="🏷️", layout="centered")

st.title("🏷️ LxU 50x30 高清标签生成器")
st.info("💡 **精细调优版**：三行模式行间距已调至 1.01，确保长标题在极致紧凑下依然清晰。")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 📝 输入商品信息")
    # 字段名已更新为“入库码”
    v_sku = st.text_input("入库码", "S0033507379541")
    v_title = st.text_input("韩文品名", "[LxU] 용접돋보기 고글형 확대경")
    v_spec = st.text_input("规格参数 (Option)", "1.00배율 2개입")
    
    st.markdown("<br>", unsafe_allow_html=True)
    generate_btn = st.button("🚀 生成高清标签预览", use_container_width=True, type="primary")

with col2:
    st.markdown("### 🖨️ 预览与下载")
    if generate_btn or 'l_img' not in st.session_state:
        if v_sku and v_title:
            with st.spinner("智能排版微调中..."):
                st.session_state.l_img = make_label_50x30(v_sku, v_title, v_spec)
        else:
            st.warning("请填写完整的入库码和品名！")

    if 'l_img' in st.session_state:
        st.image(st.session_state.l_img, caption="1000x600 px (300 DPI 极致紧凑精修版)", use_column_width=True)
        
        # PNG 下载
        png_buf = io.BytesIO()
        st.session_state.l_img.save(png_buf, format="PNG", dpi=(300, 300))
        st.download_button("📥 下载标签 (PNG)", png_buf.getvalue(), f"LxU_Label_{v_sku}.png", use_container_width=True)
        
        # PDF 下载
        pdf_buf = io.BytesIO()
        st.session_state.l_img.save(pdf_buf, format="PDF", resolution=300.0)
        st.download_button("📥 下载标签 (PDF)", pdf_buf.getvalue(), f"LxU_Label_{v_sku}.pdf", use_container_width=True)
