import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import barcode
from barcode.writer import ImageWriter
import io
import os

# ================= 1. 核心图像引擎 =================

def make_label_50x30(sku, title, spec):
    """
    生成 LxU 专属 50x30mm 高清标签 (智能三行版)
    - 支持 1-3 行自适应切换，防止长标题字体过小
    - 维持 SKU(中等)、品名(粗体)、规格(超粗)的权重层级
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

    # 入库码数字：常规体双层叠加 (保持清秀但清晰)
    f_sku = load_font(68, is_bold=False)
    sku_pos = (500, 270)
    draw.text(sku_pos, sku, fill='black', font=f_sku, anchor="mm")
    draw.text((sku_pos[0] + 1, sku_pos[1]), sku, fill='black', font=f_sku, anchor="mm")

    # --- 2. 底部声明区 ---
    # MADE IN CHINA 保持底部中心，字号 32
    f_bottom = load_font(32, is_bold=False)
    draw.text((500, 575), "MADE IN CHINA", fill='black', font=f_bottom, anchor="mm")

    # --- 3. 核心信息区 (智能 1-3 行排版) ---
    display_text = title
    if spec.strip():
        display_text = f"{title} / {spec.strip()}"
    
    max_text_width = 900 # 稍微放宽一点边距
    font_size = 78 # 起步大字号
    wrapped_lines = []
    final_font_bold = None

    while font_size > 20:
        f_test_bold = load_font(font_size, is_bold=True)
        def get_w(t): return draw.textbbox((0,0), t, font=f_test_bold)[2]
        words = display_text.split()
        
        # 尝试 1: 单行直接装下
        if get_w(display_text) <= max_text_width:
            wrapped_lines = [display_text]
            final_font_bold = f_test_bold
            break
            
        # 尝试 2: 智能切分两行
        best_2_split = None
        for i in range(1, len(words)):
            l1, l2 = " ".join(words[:i]), " ".join(words[i:])
            if get_w(l1) <= max_text_width and get_w(l2) <= max_text_width:
                diff = abs(get_w(l1) - get_w(l2))
                if best_2_split is None or diff < best_2_split[0]:
                    best_2_split = (diff, [l1, l2])
        if best_2_split:
            wrapped_lines = best_2_split[1]
            final_font_bold = f_test_bold
            break

        # 尝试 3: 💡 新增：智能切分三行 (保持大字号的关键)
        best_3_split = None
        n = len(words)
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                l1, l2, l3 = " ".join(words[:i]), " ".join(words[i:j]), " ".join(words[j:])
                if get_w(l1) <= max_text_width and get_w(l2) <= max_text_width and get_w(l3) <= max_text_width:
                    # 寻找视觉上最均衡的切分点
                    w1, w2, w3 = get_w(l1), get_w(l2), get_w(l3)
                    diff = max(w1, w2, w3) - min(w1, w2, w3)
                    if best_3_split is None or diff < best_3_split[0]:
                        best_3_split = (diff, [l1, l2, l3])
        if best_3_split:
            wrapped_lines = best_3_split[1]
            final_font_bold = f_test_bold
            break
            
        # 若三行在大字号下都装不下，则缩小字号循环
        font_size -= 2 

    if not wrapped_lines: # 极端保底
        final_font_bold = load_font(30, is_bold=True)
        wrapped_lines = [display_text]

    # --- 渲染逻辑 ---
    # 调整行间距为 1.10，确保三行也能在中心区域完美展示
    line_height = int(font_size * 1.10)
    center_y_area = 422 # 理论视觉中心
    start_y = center_y_area - ((len(wrapped_lines) * line_height) / 2) + (line_height / 2)

    current_y = start_y
    for line in wrapped_lines:
        if " / " in line:
            # 规格增强处理：四重暴力加粗
            parts = line.split(" / ", 1)
            total_w = draw.textbbox((0,0), line, font=final_font_bold)[2]
            start_x = 500 - (total_w / 2)
            name_text = parts[0]
            draw.text((start_x, current_y), name_text, fill='black', font=final_font_bold, anchor="lm")
            slash_w = draw.textbbox((0,0), name_text, font=final_font_bold)[2]
            spec_text = " / " + parts[1]
            sp_pos = (start_x + slash_w, current_y)
            # 渲染四次实现超粗体
            for dx, dy in [(0,0), (1,0), (0,1), (1,1)]:
                draw.text((sp_pos[0]+dx, sp_pos[1]+dy), spec_text, fill='black', font=final_font_bold, anchor="lm")
        else:
            draw.text((500, current_y), line, fill='black', font=final_font_bold, anchor="mm")
        current_y += line_height
        
    return img

# ================= 2. 界面展示逻辑 =================

st.set_page_config(page_title="LxU 标签生成器", page_icon="🏷️", layout="centered")

st.title("🏷️ LxU 50x30 高清标签生成器")
st.info("💡 **深度排版优化**：自动支持三行自适应，长商品名也能保持大字号清晰打印。")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 📝 输入商品信息")
    v_sku = st.text_input("入库码", "S0033507379541")
    v_title = st.text_input("韩文品名", "[LxU] 용접돋보기 고글형 확대경")
    v_spec = st.text_input("规格参数 (Option)", "1.00배율 2개입")
    
    st.markdown("<br>", unsafe_allow_html=True)
    generate_btn = st.button("🚀 生成高清标签预览", use_container_width=True, type="primary")

with col2:
    st.markdown("### 🖨️ 预览与下载")
    if generate_btn or 'l_img' not in st.session_state:
        if v_sku and v_title:
            with st.spinner("智能排版中..."):
                st.session_state.l_img = make_label_50x30(v_sku, v_title, v_spec)
        else:
            st.warning("请填写完整的入库码和品名！")

    if 'l_img' in st.session_state:
        st.image(st.session_state.l_img, caption="1000x600 px (300 DPI 智能自适应版)", use_column_width=True)
        
        # PNG 下载
        png_buf = io.BytesIO()
        st.session_state.l_img.save(png_buf, format="PNG", dpi=(300, 300))
        st.download_button("📥 下载标签 (PNG)", png_buf.getvalue(), f"LxU_Label_{v_sku}.png", use_container_width=True)
        
        # PDF 下载
        pdf_buf = io.BytesIO()
        st.session_state.l_img.save(pdf_buf, format="PDF", resolution=300.0)
        st.download_button("📥 下载标签 (PDF)", pdf_buf.getvalue(), f"LxU_Label_{v_sku}.pdf", use_container_width=True)
