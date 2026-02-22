import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import barcode
from barcode.writer import ImageWriter
import io
import os

# ================= 1. 核心图像引擎 =================

def make_label_50x30(sku, title, spec):
    """
    生成 LxU 专属 50x30mm 高清标签 (视觉权重完美版)
    - 入库码：中等粗度 (Medium)
    - 商品名称：原生粗体 (Standard Bold)
    - 规格参数：四重叠加 (Super Bold)
    - 产地声明：极简常规 (Regular)
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

    # --- 💡 板块一：扫码区 (Barcode + SKU) ---
    try:
        code_factory = barcode.get_barcode_class('code128')
        c128 = code_factory(sku, writer=ImageWriter())
        buf = io.BytesIO()
        c128.write(buf, options={"module_height": 20.0, "module_width": 0.4, "font_size": 0, "quiet_zone": 1})
        b_img = Image.open(buf).resize((900, 220)) 
        img.paste(b_img, (50, 20)) 
    except: pass

    # 入库码数字：使用常规体 + 双层叠加渲染 (比标题细一点点)
    f_sku = load_font(68, is_bold=False)
    sku_pos = (500, 270)
    draw.text(sku_pos, sku, fill='black', font=f_sku, anchor="mm")
    draw.text((sku_pos[0] + 1, sku_pos[1]), sku, fill='black', font=f_sku, anchor="mm")

    # --- 💡 板块三：底部声明区 (居中细体) ---
    f_bottom = load_font(32, is_bold=False)
    draw.text((500, 575), "MADE IN CHINA", fill='black', font=f_bottom, anchor="mm")

    # --- 💡 板块二：核心信息区 (Title / Spec) ---
    display_text = title
    if spec.strip():
        display_text = f"{title} / {spec.strip()}"
    
    max_text_width = 880 
    font_size = 78 
    wrapped_lines = []
    final_font_bold = None

    while font_size > 22:
        f_test_bold = load_font(font_size, is_bold=True)
        def get_w(t): return draw.textbbox((0,0), t, font=f_test_bold)[2]
        
        if get_w(display_text) <= max_text_width:
            wrapped_lines = [display_text]
            final_font_bold = f_test_bold
            break
            
        words = display_text.split()
        best_split = None
        for i in range(1, len(words)):
            l1, l2 = " ".join(words[:i]), " ".join(words[i:])
            if get_w(l1) <= max_text_width and get_w(l2) <= max_text_width:
                diff = abs(get_w(l1) - get_w(l2))
                if best_split is None or diff < best_split[0]:
                    best_split = (diff, [l1, l2])
        
        if best_split:
            wrapped_lines = best_split[1]
            final_font_bold = f_test_bold
            break
        font_size -= 2 

    line_height = int(font_size * 1.12)
    center_y_area = 420 
    start_y = center_y_area - ((len(wrapped_lines) * line_height) / 2) + (line_height / 2)

    current_y = start_y
    for line in wrapped_lines:
        if " / " in line:
            parts = line.split(" / ", 1)
            total_w = draw.textbbox((0,0), line, font=final_font_bold)[2]
            start_x = 500 - (total_w / 2)
            
            # 产品品名：标准粗体单层绘制
            name_text = parts[0]
            draw.text((start_x, current_y), name_text, fill='black', font=final_font_bold, anchor="lm")
            
            slash_w = draw.textbbox((0,0), name_text, font=final_font_bold)[2]
            
            # 规格参数：四重暴力加粗渲染
            spec_text = " / " + parts[1]
            spec_x = start_x + slash_w
            draw.text((spec_x, current_y), spec_text, fill='black', font=final_font_bold, anchor="lm")
            draw.text((spec_x + 1, current_y), spec_text, fill='black', font=final_font_bold, anchor="lm")
            draw.text((spec_x, current_y + 1), spec_text, fill='black', font=final_font_bold, anchor="lm")
            draw.text((spec_x + 1, current_y + 1), spec_text, fill='black', font=final_font_bold, anchor="lm")
        else:
            draw.text((500, current_y), line, fill='black', font=final_font_bold, anchor="mm")
        
        current_y += line_height
        
    return img

# ================= 2. 界面配置与布局 =================

st.set_page_config(page_title="LxU 标签生成器", page_icon="🏷️", layout="centered")

st.title("🏷️ LxU 50x30 高清标签生成器")
st.info("💡 **生产版更新**：支持 PNG 和 PDF 双格式下载。入库码数字已精细调细。")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 📝 输入商品信息")
    # 💡 核心修改：文案改为“入库码”
    v_sku = st.text_input("入库码", "S0033507379541")
    v_title = st.text_input("韩文品名", "[LxU] 용접돋보기 고글형 확대경")
    v_spec = st.text_input("规格参数 (Option)", "1.00배율 2개입")
    
    st.markdown("<br>", unsafe_allow_html=True)
    generate_btn = st.button("🚀 生成高清标签预览", use_container_width=True, type="primary")

with col2:
    st.markdown("### 🖨️ 预览与下载")
    if generate_btn or 'l_img' not in st.session_state:
        if v_sku and v_title:
            with st.spinner("视觉校准中..."):
                st.session_state.l_img = make_label_50x30(v_sku, v_title, v_spec)
        else:
            st.warning("请填写完整的入库码和品名！")

    if 'l_img' in st.session_state:
        st.image(st.session_state.l_img, caption="1000x600 px (300 DPI)", use_column_width=True)
        
        # --- 下载按钮区域 ---
        # 1. 保存为 PNG 字节流
        png_buf = io.BytesIO()
        st.session_state.l_img.save(png_buf, format="PNG", dpi=(300, 300))
        
        # 2. 保存为 PDF 字节流
        pdf_buf = io.BytesIO()
        # PIL 支持直接将 RGB 图像保存为 PDF
        st.session_state.l_img.save(pdf_buf, format="PDF", resolution=300.0)
        
        # 渲染双按钮
        st.download_button(
            label="📥 下载标签 (PNG 图片)", 
            data=png_buf.getvalue(), 
            file_name=f"LxU_Label_{v_sku}.png", 
            mime="image/png",
            use_container_width=True
        )
        
        st.download_button(
            label="📥 下载标签 (PDF 文档)", 
            data=pdf_buf.getvalue(), 
            file_name=f"LxU_Label_{v_sku}.pdf", 
            mime="application/pdf",
            use_container_width=True
        )
