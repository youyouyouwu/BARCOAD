import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import barcode
from barcode.writer import ImageWriter
import io
import os

# ================= 1. 核心图像引擎 =================

# 💡 核心变动：增加 remark 参数接收备注文本
def make_label_50x30(sku, title, spec, remark):
    """
    生成 LxU 专属 50x30mm 高清标签 (带仓库备注版)
    - 左下角新增中文备注区域，字体风格与 MADE IN CHINA 保持一致
    - 整体沿用极细体+粗体组合
    """
    width, height = 1000, 600 
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)

    def load_font(size, is_bold=False):
        # 字体加载逻辑保持不变 (优先 Light 细体)
        font_paths = [
            "C:/Windows/Fonts/msyhl.ttc", 
            "C:/Windows/Fonts/msyhbd.ttc" if is_bold else "C:/Windows/Fonts/msyh.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Light.ttc",
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf", 
            "C:/Windows/Fonts/malgun.ttf",
            "Arial.ttf"
        ]
        if is_bold:
            bold_paths = [p for p in font_paths if "bd" in p or "Bold" in p or "msyh.ttc" in p]
            for p in bold_paths:
                if os.path.exists(p): return ImageFont.truetype(p, size)
        for p in font_paths:
            if os.path.exists(p): return ImageFont.truetype(p, size)
        return ImageFont.load_default()

    # --- 1. 扫码区 ---
    try:
        code_factory = barcode.get_barcode_class('code128')
        c128 = code_factory(sku, writer=ImageWriter())
        buf = io.BytesIO()
        c128.write(buf, options={"module_height": 20.0, "module_width": 0.4, "font_size": 0, "quiet_zone": 1})
        b_img = Image.open(buf).resize((900, 220)) 
        img.paste(b_img, (50, 20)) 
    except: pass

    f_sku = load_font(68, is_bold=False)
    draw.text((500, 270), sku, fill='black', font=f_sku, anchor="mm")

    # --- 2. 底部声明与备注区 ---
    # 加载统一的底部字体：32号，非粗体 (极细)
    f_bottom = load_font(32, is_bold=False)
    
    # A. 居中的产地标识
    draw.text((500, 575), "MADE IN CHINA", fill='black', font=f_bottom, anchor="mm")

    # B. 💡 新增：左下角仓库备注
    if remark.strip():
        # 位置设定：X=50(左侧边距), Y=575(与产地标同一水平线)
        # anchor="lm" 表示左对齐垂直居中
        draw.text((50, 575), remark, fill='black', font=f_bottom, anchor="lm")

    # --- 3. 核心信息区 (自适应排版，保持不变) ---
    display_text = title
    if spec.strip():
        display_text = f"{title} / {spec.strip()}"
    
    max_text_width = 920 
    font_size = 78 
    wrapped_lines = []
    final_font_light = None
    final_font_bold = None

    while font_size > 20:
        f_light = load_font(font_size, is_bold=False)
        f_bold = load_font(font_size, is_bold=True)
        def get_w(t): return draw.textbbox((0,0), t, font=f_bold)[2]
        words = display_text.split()
        
        if get_w(display_text) <= max_text_width:
            wrapped_lines = [display_text]
            final_font_light = f_light; final_font_bold = f_bold
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
            final_font_light = f_light; final_font_bold = f_bold
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
            final_font_light = f_light; final_font_bold = f_bold
            break
        font_size -= 2 

    multiplier = 1.01 if len(wrapped_lines) >= 3 else 1.10
    line_height = int(font_size * multiplier)
    current_y = 422 - ((len(wrapped_lines) * line_height) / 2) + (line_height / 2)

    for line in wrapped_lines:
        if " / " in line:
            parts = line.split(" / ", 1)
            total_w = draw.textbbox((0,0), line, font=final_font_bold)[2]
            start_x = 500 - (total_w / 2)
            draw.text((start_x, current_y), parts[0], fill='black', font=final_font_light, anchor="lm")
            slash_w = draw.textbbox((0,0), parts[0], font=final_font_light)[2]
            spec_text = " / " + parts[1]
            sp_pos = (start_x + slash_w, current_y)
            for dx, dy in [(0,0), (1,0), (0,1), (1,1)]:
                draw.text((sp_pos[0]+dx, sp_pos[1]+dy), spec_text, fill='black', font=final_font_bold, anchor="lm")
        else:
            draw.text((500, current_y), line, fill='black', font=final_font_light, anchor="mm")
        current_y += line_height
        
    return img

# ================= 2. 界面展示逻辑 =================

st.set_page_config(page_title="LxU 标签生成器", page_icon="🏷️", layout="centered")

st.title("🏷️ LxU 50x30 高清标签生成器")
st.info("💡 **功能更新**：左下角已增加仓库备注区域，字体样式与底部声明保持一致。")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 📝 输入商品信息")
    v_sku = st.text_input("入库码", "S0033507379541")
    v_title = st.text_input("韩文品名", "[LxU] 용접돋보기 고글형 확대경")
    v_spec = st.text_input("规格参数 (Option)", "1.00배율 2개입")
    # 💡 新增备注输入框
    v_remark = st.text_input("仓库备注 (中文可选)", "")
    
    st.markdown("<br>", unsafe_allow_html=True)
    generate_btn = st.button("🚀 生成高清标签预览", use_container_width=True, type="primary")

with col2:
    st.markdown("### 🖨️ 预览与下载")
    if generate_btn or 'l_img' not in st.session_state:
        if v_sku and v_title:
            with st.spinner("正在生成包含备注的标签..."):
                # 💡 调用时传入备注参数
                st.session_state.l_img = make_label_50x30(v_sku, v_title, v_spec, v_remark)
        else:
            st.warning("请填写完整的入库码和品名！")

    if 'l_img' in st.session_state:
        st.image(st.session_state.l_img, caption="1000x600 px (300 DPI)", use_column_width=True)
        
        # 下载按钮
        png_buf = io.BytesIO(); st.session_state.l_img.save(png_buf, format="PNG", dpi=(300, 300))
        st.download_button("📥 下载标签 (PNG)", png_buf.getvalue(), f"LxU_Label_{v_sku}.png", use_container_width=True)
        pdf_buf = io.BytesIO(); st.session_state.l_img.save(pdf_buf, format="PDF", resolution=300.0)
        st.download_button("📥 下载标签 (PDF)", pdf_buf.getvalue(), f"LxU_Label_{v_sku}.pdf", use_container_width=True)
