import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import barcode
from barcode.writer import ImageWriter
import io
import os


APP_DIR = os.path.dirname(os.path.abspath(__file__))
BUNDLED_FONT_PATH = os.path.join(
    APP_DIR,
    "assets",
    "fonts",
    "NanumGothic-Regular.ttf",
)


# ================= 1. 核心图像引擎 =================

def make_label_50x30(sku, title, spec, remark):
    """
    生成 LxU 专属 50x30mm 高清标签
    - 分辨率：1000 x 600 px
    - 目标打印：300 DPI
    - 备注逻辑：内容两侧自动添加横杠，靠右对齐
    """

    width, height = 1000, 600

    img = Image.new(
        "RGB",
        (width, height),
        "white"
    )

    draw = ImageDraw.Draw(img)

    # ================= 字体加载 =================

    def load_font(size, is_bold=False):

        font_candidates = [
            {
                # Keep the app independent from Streamlit Cloud's apt installer.
                "path": BUNDLED_FONT_PATH,
                "index": 0
            },
            {
                "path": "/usr/share/fonts/opentype/noto/NotoSansCJK-Light.ttc",
                "index": 0
            },
            {
                "path": "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "index": 0
            },
            {
                "path": "C:/Windows/Fonts/msyhl.ttc",
                "index": 0
            },
            {
                "path": "C:/Windows/Fonts/msyh.ttc",
                "index": 0
            },
            {
                "path": "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
                "index": 0
            },
            {
                "path": "Arial.ttf",
                "index": 0
            }
        ]

        for cfg in font_candidates:

            if os.path.exists(cfg["path"]):

                try:
                    return ImageFont.truetype(
                        cfg["path"],
                        size,
                        index=cfg["index"]
                    )

                except Exception:
                    continue

        return ImageFont.load_default()


    # ================= 1. 条形码区域 =================

    try:

        code_factory = barcode.get_barcode_class("code128")

        c128 = code_factory(
            sku,
            writer=ImageWriter()
        )

        barcode_buf = io.BytesIO()

        c128.write(
            barcode_buf,
            options={
                "module_height": 20.0,
                "module_width": 0.4,
                "font_size": 0,
                "quiet_zone": 1
            }
        )

        barcode_buf.seek(0)

        with Image.open(barcode_buf) as temp_barcode:

            # 转 RGB，避免某些 Pillow 版本出现模式兼容问题
            b_img = temp_barcode.convert("RGB")

            b_img = b_img.resize(
                (900, 220),
                Image.Resampling.LANCZOS
            )

            img.paste(
                b_img,
                (50, 20)
            )

    except Exception as e:

        # 不再直接 except: pass
        # 这样 Streamlit Cloud Logs 可以看到真正错误
        raise RuntimeError(
            f"条形码生成失败：{e}"
        ) from e


    # ================= 入库码 =================

    f_sku = load_font(
        68,
        is_bold=False
    )

    draw.text(
        (500, 270),
        sku,
        fill="black",
        font=f_sku,
        anchor="mm"
    )


    # ================= 2. 底部功能区 =================

    f_bottom = load_font(
        32,
        is_bold=False
    )

    draw.text(
        (500, 575),
        "MADE IN CHINA",
        fill="black",
        font=f_bottom,
        anchor="mm"
    )


    # 仓库备注
    if remark.strip():

        display_remark = f"-{remark.strip()}-"

        draw.text(
            (950, 575),
            display_remark,
            fill="black",
            font=f_bottom,
            anchor="rm"
        )


    # ================= 3. 商品信息 =================

    display_text = title.strip()

    if spec.strip():

        display_text = (
            f"{title.strip()} / {spec.strip()}"
        )


    max_text_width = 920

    font_size = 78

    wrapped_lines = []

    final_font_light = None


    # ================= 自动字号 =================

    while font_size > 20:

        f_l = load_font(
            font_size,
            is_bold=False
        )

        def get_w(text):

            bbox = draw.textbbox(
                (0, 0),
                text,
                font=f_l
            )

            return bbox[2] - bbox[0]


        words = display_text.split()


        # ---------- 单行 ----------

        if get_w(display_text) <= max_text_width:

            wrapped_lines = [
                display_text
            ]

            final_font_light = f_l

            break


        # ---------- 两行 ----------

        best_2 = None

        for i in range(
            1,
            len(words)
        ):

            l1 = " ".join(
                words[:i]
            )

            l2 = " ".join(
                words[i:]
            )

            if (
                get_w(l1) <= max_text_width
                and
                get_w(l2) <= max_text_width
            ):

                diff = abs(
                    get_w(l1) -
                    get_w(l2)
                )

                if (
                    best_2 is None
                    or
                    diff < best_2[0]
                ):

                    best_2 = (
                        diff,
                        [l1, l2]
                    )


        if best_2:

            wrapped_lines = best_2[1]

            final_font_light = f_l

            break


        # ---------- 三行 ----------

        best_3 = None

        n = len(words)


        for i in range(
            1,
            n - 1
        ):

            for j in range(
                i + 1,
                n
            ):

                l1 = " ".join(
                    words[:i]
                )

                l2 = " ".join(
                    words[i:j]
                )

                l3 = " ".join(
                    words[j:]
                )


                if (
                    get_w(l1) <= max_text_width
                    and
                    get_w(l2) <= max_text_width
                    and
                    get_w(l3) <= max_text_width
                ):

                    widths = [
                        get_w(l1),
                        get_w(l2),
                        get_w(l3)
                    ]

                    w_diff = (
                        max(widths)
                        -
                        min(widths)
                    )


                    if (
                        best_3 is None
                        or
                        w_diff < best_3[0]
                    ):

                        best_3 = (
                            w_diff,
                            [l1, l2, l3]
                        )


        if best_3:

            wrapped_lines = best_3[1]

            final_font_light = f_l

            break


        font_size -= 2


    # ================= 防止极端长文本 =================

    if not wrapped_lines:

        final_font_light = load_font(
            20,
            is_bold=False
        )

        wrapped_lines = [
            display_text
        ]

        font_size = 20


    # ================= 行距 =================

    if len(wrapped_lines) >= 3:

        multiplier = 1.01

    else:

        multiplier = 1.10


    line_height = int(
        font_size *
        multiplier
    )


    current_y = (
        422
        -
        (
            len(wrapped_lines)
            *
            line_height
        ) / 2
        +
        (
            line_height / 2
        )
    )


    # ================= 绘制商品信息 =================

    for line in wrapped_lines:

        if " / " in line:

            parts = line.split(
                " / ",
                1
            )


            bbox = draw.textbbox(
                (0, 0),
                line,
                font=final_font_light
            )

            tw = (
                bbox[2] -
                bbox[0]
            )


            sx = (
                500 -
                tw / 2
            )


            # 商品名
            draw.text(
                (
                    sx,
                    current_y
                ),
                parts[0],
                fill="black",
                font=final_font_light,
                anchor="lm"
            )


            bbox_name = draw.textbbox(
                (0, 0),
                parts[0],
                font=final_font_light
            )

            sw = (
                bbox_name[2]
                -
                bbox_name[0]
            )


            # 规格
            spec_t = (
                " / "
                +
                parts[1]
            )


            # 轻微加粗
            for dx, dy in [
                (0, 0),
                (1, 0),
                (0, 1),
                (1, 1)
            ]:

                draw.text(
                    (
                        sx + sw + dx,
                        current_y + dy
                    ),
                    spec_t,
                    fill="black",
                    font=final_font_light,
                    anchor="lm"
                )


        else:

            draw.text(
                (
                    500,
                    current_y
                ),
                line,
                fill="black",
                font=final_font_light,
                anchor="mm"
            )


        current_y += line_height


    return img


# ================= 2. 图片转换工具 =================

def image_to_png_bytes(img):

    buf = io.BytesIO()

    img.save(
        buf,
        format="PNG",
        dpi=(300, 300)
    )

    buf.seek(0)

    return buf.getvalue()


def image_to_pdf_bytes(img):

    buf = io.BytesIO()

    # PDF 最稳妥使用 RGB
    pdf_img = img.convert("RGB")

    pdf_img.save(
        buf,
        format="PDF",
        resolution=300.0
    )

    buf.seek(0)

    return buf.getvalue()


# ================= 3. Streamlit 页面 =================

st.set_page_config(
    page_title="LxU 标签生成器",
    page_icon="🏷️",
    layout="centered"
)


st.title(
    "🏷️ LxU 50x30 高清标签生成器"
)


# 显示当前 Streamlit 版本
st.caption(
    f"Streamlit {st.__version__}"
)


col1, col2 = st.columns(
    [1, 1],
    gap="large"
)


# ================= 左侧输入区 =================

with col1:

    st.markdown(
        "### 📝 输入商品信息"
    )


    v_sku = st.text_input(
        "入库码",
        "S0033507379541"
    )


    v_title = st.text_input(
        "韩文品名",
        "[LxU] 용접돋보기 고글형 확대경"
    )


    v_spec = st.text_input(
        "规格参数 (Option)",
        "1.00배율 2개입"
    )


    v_remark = st.text_input(
        "仓库备注 (选填 | 尽量拼音标注，避免显示中文)",
        ""
    )


    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )


    # 新版 Streamlit：
    # use_container_width=True
    # 改成 width="stretch"
    generate_btn = st.button(
        "🚀 生成高清标签预览",
        width="stretch",
        type="primary"
    )


# ================= 右侧预览区 =================

with col2:

    # 第一次打开页面时自动生成
    # 点击按钮后重新生成
    if (
        generate_btn
        or
        "l_img" not in st.session_state
    ):

        if (
            v_sku.strip()
            and
            v_title.strip()
        ):

            try:

                st.session_state.l_img = (
                    make_label_50x30(
                        v_sku.strip(),
                        v_title.strip(),
                        v_spec,
                        v_remark
                    )
                )

            except Exception as e:

                st.error(
                    f"标签生成失败：{e}"
                )

                st.stop()


    # ================= 显示预览 =================

    if "l_img" in st.session_state:

        current_img = (
            st.session_state.l_img
        )


        # 先转换成 PNG bytes
        # 不再直接把 PIL.Image 传入 st.image
        png_bytes = image_to_png_bytes(
            current_img
        )


        # 关键修复：
        # 删除 use_column_width=True
        st.image(
            png_bytes,
            caption="1000x600 px (300 DPI)",
            width="stretch"
        )


        # ================= PNG 下载 =================

        st.download_button(
            "📥 下载标签 (PNG)",
            data=png_bytes,
            file_name=f"LxU_{v_sku}.png",
            mime="image/png",
            width="stretch"
        )


        # ================= PDF 下载 =================

        pdf_bytes = image_to_pdf_bytes(
            current_img
        )


        st.download_button(
            "📥 下载标签 (PDF)",
            data=pdf_bytes,
            file_name=f"LxU_{v_sku}.pdf",
            mime="application/pdf",
            width="stretch"
        )
