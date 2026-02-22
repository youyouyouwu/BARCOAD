import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import barcode
from barcode.writer import ImageWriter
import io
import os

# ================= 1. 核心图像引擎 =================

def make_label_50x30(sku, title, spec):
    """
    生成 LxU 专属 50x30mm 高清标签 (视觉进化版)
    - 二维码与数字紧贴
    - 商品名行间距收缩
    - 底部标识微型化
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

    # --- 💡 板块一：扫码区 (Barcode + SKU 紧贴版) ---
    try:
        code_factory = barcode.get_barcode_class('code128')
        c128 = code_factory(sku, writer=ImageWriter())
        buf = io.BytesIO()
        c128.write(buf, options={"module_height": 20.0, "module_width": 0.4, "font_size": 0, "quiet_zone": 1})
        b_img = Image.open(buf).resize((900, 220))
        # 条形码位置稍微下移一点点，给顶部留白
        img.paste(b_img, (50, 20))
    except: pass

    # SKU：使用 Bold 字体，Y轴下移至 270，实现“紧贴”效果，解决重叠问题
    f_sku = load_font(68, is_bold=True)
    draw.text((500, 270), sku, fill='black', font=f_sku, anchor="mm")

    # --- 💡 板块二：核心信息区 (Title / Spec) ---
    display_text = title
    if spec.strip():
        display_text = f"{title} / {spec.strip()}"

    max_text_width = 880
    font_size = 78
    wrapped_lines = []
    final_font = None

    while font_size > 22:
        f_test = load_font(font_size, is_bold=True)
        def get_w(t): return draw.textbbox((0,0), t, font=f_test)[2]

        if get_w(display_text) <= max_text_width:
            wrapped_lines = [display_text]
            final_font = f_test
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
            final_font = f_test
            break
        font_size -= 2

    if not wrapped_lines:
        final_font = load_font(30, is_bold=True)
        wrapped_lines = [display_text]

    # 💡 关键：行间距倍率从 1.35 降低到 1.12，缩小两行间距
    line_height = int(font_size * 1.12)
    # 因为顶部 SKU 上移了，中心区域也随之略微上移
    center_y_area = 410
    start_y = center_y_area - ((len(wrapped_lines) * line_height) / 2) + (line_height / 2)

    current_y = start_y
    for line in wrapped_lines:
        if " / " in line:
            parts = line.split(" / ", 1)
            total_w = draw.textbbox((0,0), line, font=final_font)[2]
            start_x = 500 - (total_w / 2)

            # 产品品名：中等粗细渲染
            name_text = parts[0]
            draw.text((start_x, current_y), name_text, fill='black', font=final_font, anchor="lm")

            slash_w = draw.textbbox((0,0), name_text, font=final_font)[2]

            # 规格参数：最厚渲染 (Bold + 多重位移)
            spec_text = " / " + parts[1]
            spec_pos = (start_x + slash_w, current_y)
            draw.text(spec_pos, spec_text, fill='black', font=final_font, anchor="lm")
            draw.text((spec_pos[0]+1, spec_pos[1]), spec_text, fill='black', font=final_font, anchor="lm")
            draw.text((spec_pos[0], spec_pos[1]+0.5), spec_text, fill='black', font=final_font, anchor="lm")
        else:
            draw.text((500, current_y), line, fill='black', font=final_font, anchor="mm")

        current_y += line_height

    return img

# ================= 2. 界面配置与布局 =================

st.set_page_config(page_title="LxU 标签生成器", page_icon="🏷️", layout="centered")

st.title("🏷️ LxU 50x30 高清标签生成器")
st.info("💡 **布局终极版**：数字与二维码紧贴，商品名行距收紧，视觉重心更聚焦。")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 📝 输入商品信息")
    v_sku = st.text_input("货号 (SKU)", "S0033507379541")
    v_title = st.text_input("韩文品名", "[LxU] 용접돋보기 고글형 확대경")
    v_spec = st.text_input("规格参数 (Option)", "1.00배율 2개입")

    st.markdown("<br>", unsafe_allow_html=True)
    generate_btn = st.button("🚀 生成高清标签", use_container_width=True, type="primary")

with col2:
    st.markdown("### 🖨️ 预览与下载")
    if generate_btn or 'l_img' not in st.session_state:
        if v_sku and v_title:
            with st.spinner("视觉调优中..."):
                st.session_state.l_img = make_label_50x30(v_sku, v_title, v_spec)
        else:
            st.warning("请填写完整的 SKU 和品名！")

    if 'l_img' in st.session_state:
        st.image(st.session_state.l_img, caption="1000x600 px (视觉终极进化版)", use_column_width=True)
        b = io.BytesIO()
        st.session_state.l_img.save(b, format="PNG", dpi=(300, 300))
        st.download_button(
            label="📥 一键下载标签 (PNG)",
            data=b.getvalue(),
            file_name=f"LxU_Label_{v_sku}.png",
            mime="image/png",
            use_container_width=True
        )
