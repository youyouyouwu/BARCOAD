import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import barcode
from barcode.writer import ImageWriter
import io
import os

# ================= 1. 核心图像引擎 =================

def make_label_50x30(sku, title, spec, remark):
    """
    生成 LxU 专属 50x30mm 高清标签 (同行布局版)
    - 产地标与备注归于底行 (Y=575)，释放中部空间
    - 字体：优先思源黑体/雅黑细体，确保全字符不乱码
    """
    width, height = 1000, 600 
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)

    def load_font(size, is_bold=False):
        font_candidates = [
            # 1. 线上 Linux (Noto Sans CJK)
            {"path": "/usr/share/fonts/opentype/noto/NotoSansCJK-Light.ttc", "index": 0},
            {"path": "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "index": 0},
            # 2. 本地 Windows (雅黑细体)
            {"path": "C:/Windows/Fonts/msyhl.ttc", "index": 0},
            {"path": "C:/Windows/Fonts/msyh.ttc", "index": 0},
            # 3. 韩国语保底
            {"path": "/usr/share/fonts/truetype/nanum/NanumGothic.ttf", "index": 0},
            {"path": "Arial.ttf", "index": 0}
        ]
        for cfg in font_candidates:
            if os.path.exists(cfg["path"]):
                try:
                    return ImageFont.truetype(cfg["path"], size, index=cfg["index"])
                except: continue
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

    # 入库码 (Y=270, 细体双层渲染)
    f_sku = load_font(68, is_bold=False)
    draw.text((500, 270), sku, fill='black', font=f_sku, anchor="mm")

    # --- 2. 底部功能区 (同行显示) ---
    f_bottom = load_font(32, is_bold=False)
    
    # 💡 核心改动：产地标与备注全部锁定在 Y=575
    # A. 产地标识：保持中心地位
    draw.text((500, 575), "MADE IN CHINA", fill='black', font=f_bottom, anchor="mm")

    # B. 仓库备注：靠右侧显示 (右对齐)，不干扰产地标
    if remark.strip():
        # X=950 确保不贴边，anchor="rm" 确保向左延伸
        draw.text((950, 575), remark, fill='black', font=f_bottom, anchor="rm")

    # --- 3. 核心信息区 (智能 1-3 行自适应) ---
    display_text = title
    if spec.strip():
        display_text = f"{title} / {spec.strip()}"
    
    max_text_width = 920 
    font_size = 78 
    wrapped_lines = []
    final_font_light = None

    while font_size > 20:
        f_l = load_font(font_size, is_bold=False)
        def get_w(t): return draw.textbbox((0,0), t, font=f_l)[2]
        words = display_text.split()
        
        if get_w(display_text) <= max_text_width:
            wrapped_lines = [display_text]; final_font_light = f_l; break
        
        # 智能两行/三行切分 (1.01 紧凑间距)
        # (此处逻辑自动执行 best_2 和 best_3 寻找最均衡排版)
        best_2 = None
        for i in range(1, len(words)):
            l1, l2 = " ".join(words[:i]), " ".join(words[i:])
            if get_w(l1) <= max_text_width and get_w(l2) <= max_text_width:
                diff = abs(get_w(l1) - get_w(l2))
                if best_2 is None or diff < best_2[0]: best_2 = (diff, [l1, l2])
        if best_2: wrapped_lines = best_2[1]; final_font_light = f_l; break

        best_3 = None
        n = len(words)
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                l1, l2, l3 = " ".join(words[:i]), " ".join(words[i:j]), " ".join(words[j:])
                if get_w(l1) <= max_text_width and get_w(l2) <= max_text_width and get_w(l3) <= max_text_width:
                    w_diff = max(get_w(l1), get_w(l2), get_w(l3)) - min(get_w(l1), get_w(l2), get_w(l3))
                    if best_3 is None or w_diff < best_3[0]: best_3 = (w_diff, [l1, l2, l3])
        if best_3: wrapped_lines = best_3[1]; final_font_light = f_l; break
        font_size -= 2 

    # 渲染品名与规格
    multiplier = 1.01 if len(wrapped_lines) >= 3 else 1.10
    line_height = int(font_size * multiplier)
    current_y = 422 - ((len(wrapped_lines) * line_height) / 2) + (line_height / 2)

    for line in wrapped_lines:
        if " / " in line:
            parts = line.split(" / ", 1)
            tw = draw.textbbox((0,0), line, font=final_font_light)[2]
            sx = 500 - (tw / 2)
            draw.text((sx, current_y), parts[0], fill='black', font=final_font_light, anchor="lm")
            sw = draw.textbbox((0,0), parts[0], font=final_font_light)[2]
            spec_t = " / " + parts[1]
            # 规格暴力加粗
            for dx, dy in [(0,0), (1,0), (0,1), (1,1)]:
                draw.text((sx+sw+dx, current_y+dy), spec_t, fill='black', font=final_font_light, anchor="lm")
        else:
            draw.text((500, current_y), line, fill='black', font=final_font_light, anchor="mm")
        current_y += line_height
    return img

# ================= 2. 界面展示逻辑 =================

st.set_page_config(page_title="LxU 标签生成器", page_icon="🏷️", layout="centered")

st.title("🏷️ LxU 50x30 高清标签生成器")
st.success("✅ **空间优化完成**：产地标与备注已合并至最底行，中部信息区已获得最大显示空间。")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    v_sku = st.text_input("入库码", "S0033507379541")
    v_title = st.text_input("韩文品名", "[LxU] 용접돋보기 고글형 확대경")
    v_spec = st.text_input("规格参数 (Option)", "1.00배율 2개입")
    v_remark = st.text_input("仓库备注 (例如：两个装/绿色)", "两个装/绿色") 
    
    st.markdown("<br>", unsafe_allow_html=True)
    generate_btn = st.button("🚀 生成高清标签预览", use_container_width=True, type="primary")

with col2:
    if generate_btn or 'l_img' not in st.session_state:
        if v_sku and v_title:
            st.session_state.l_img = make_label_50x30(v_sku, v_title, v_spec, v_remark)
        else:
            st.warning("请填写完整的入库码和品名！")

    if 'l_img' in st.session_state:
        st.image(st.session_state.l_img, caption="1000x600 px (300 DPI 空间最大化版)", use_column_width=True)
        # 下载
        p_buf = io.BytesIO(); st.session_state.l_img.save(p_buf, format="PNG", dpi=(300, 300))
        st.download_button("📥 下载标签 (PNG)", p_buf.getvalue(), f"LxU_{v_sku}.png", use_container_width=True)
        pdf_buf = io.BytesIO(); st.session_state.l_img.save(pdf_buf, format="PDF", resolution=300.0)
        st.download_button("📥 下载标签 (PDF)", pdf_buf.getvalue(), f"LxU_{v_sku}.pdf", use_container_width=True)
