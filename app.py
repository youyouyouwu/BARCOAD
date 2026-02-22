import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
from PIL import Image
import io
import time
import json
import re

# ================= 1. 状态锁初始化 =================
if 'extractions' not in st.session_state:
    st.session_state.extractions = []

# ================= 2. 核心工具函数 =================

def render_copy_button(text, key):
    """带 ✅ 成功反馈的一键复制按钮"""
    html_code = f"""
    <!DOCTYPE html>
    <html><head><style>
        body {{ margin: 0; padding: 2px; font-family: sans-serif; }}
        .container {{ display: flex; align-items: center; }}
        .text-box {{ flex-grow: 1; padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; width: 100%; box-sizing: border-box; background: #fdfdfd; color: #333; }}
        .copy-btn {{ padding: 8px 15px; background: #fff; border: 1px solid #ddd; border-radius: 4px; margin-left: 8px; cursor: pointer; font-weight: bold; min-width: 80px; transition: 0.2s; color: #333; }}
    </style></head>
    <body><div class="container">
        <input type="text" value="{text}" id="q_{key}" class="text-box" readonly>
        <button onclick="c()" id="b_{key}" class="copy-btn">复制</button>
    </div>
    <script>
    function c() {{
        var i = document.getElementById("q_{key}"); i.select(); document.execCommand("copy");
        var b = document.getElementById("b_{key}"); b.innerText = "✅ 成功";
        b.style.background = "#dcfce7"; b.style.borderColor = "#86efac";
        setTimeout(()=>{{ b.innerText = "复制"; b.style.background = "#fff"; b.style.borderColor = "#ddd"; }}, 2000);
    }}
    </script></body></html>
    """
    components.html(html_code, height=45)

def process_lxu_file_bytes(file_bytes, filename, prompt):
    """兼容图片与 PDF 内存直传的引擎"""
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction="你是一个精通韩国 Coupang 选品和竞品分析的专家，品牌名为 LxU。"
        )
        if filename.lower().endswith(".pdf"):
            payload = [{"mime_type": "application/pdf", "data": file_bytes}, prompt]
        else:
            img = Image.open(io.BytesIO(file_bytes))
            payload = [img, prompt]
            
        response = model.generate_content(payload, generation_config={"response_mime_type": "application/json"})
        return response.text
    except Exception as e:
        return f'{{"error": "{str(e)}" }}'

# ================= 3. 界面配置与侧边栏 (隐藏 Key 逻辑) =================

st.set_page_config(page_title="品名识别生成工具", layout="wide", initial_sidebar_state="collapsed")

with st.sidebar:
    st.header("⚙️ 引擎配置")
    secret_key = st.secrets.get("GEMINI_API_KEY", "")
    manual_key = st.text_input("备用 API Key (可选)", value="", type="password", help="默认使用隐藏密钥")
    final_api_key = manual_key if manual_key else secret_key
    if not final_api_key:
        st.warning("👈 请在后台或此处配置 API Key")
        st.stop()
    genai.configure(api_key=final_api_key)
    st.success("✅ 极速引擎已就绪")

# ================= 4. 主界面 (测款识图) =================

st.title("🔎 品名识别生成工具")
st.info("💡 **效率提示**：支持拖拽上传图片或 PDF。标题已优化为【客观卖点+核心词】平衡比例，拒绝极端堆砌！")

files = st.file_uploader("📥 [全局上传/拖拽区]", type=["png", "jpg", "jpeg", "webp", "pdf"], accept_multiple_files=True)

if files:
    if st.button("🚀 开始极速精准提取", type="primary", use_container_width=True):
        new_exts = []
        for f in files:
            file_bytes = f.getvalue() 
            prompt_full = """
            任务：分析图片/文档，为该商品生成一套完整的Coupang上架信息。
            要求：
            1. keywords：5个精准查找同款的【实体名词】，严禁泛流量词。
            2. title_kr：符合Coupang真实卖家风格。核心名词 + 1~2个客观属性/卖点 + 1~2个热搜词。
               - 【拒绝极端】：不堆砌同义词，不用“安心、完美”等主观词，不带标点。
            输出 JSON 代码。
            """
            with st.spinner(f"⚡ 正在提取 {f.name} ..."):
                res_text = process_lxu_file_bytes(file_bytes, f.name, prompt_full)
            try:
                json_str = re.search(r"\{.*\}", res_text, re.DOTALL).group()
                data = json.loads(json_str)
                # 💡 新提取的结果堆叠在最上方
                new_exts.insert(0, {
                    "file": f.name, "bytes": file_bytes, "data": data,
                    "kw_history": [], "name_history": [], "title_history": []
                })
            except: st.error(f"{f.name} 解析失败")
        st.session_state.extractions = new_exts + st.session_state.extractions

# ================= 5. 渲染结果区 (带删除工具) =================

if st.session_state.extractions:
    # 💡 顶部大按钮：一键清空
    if st.button("🧨 清空所有提取结果", use_container_width=True):
        st.session_state.extractions = []
        st.rerun()

    for idx, item in enumerate(st.session_state.extractions):
        st.write("---")
        
        # 💡 每一条结果的操作头部
        h_col1, h_col2 = st.columns([8, 2])
        with h_col1:
            st.markdown("### 🔎 建议搜索关键词")
        with h_col2:
            # 🗑️ 删除此条记录的按钮
            if st.button("🗑️ 删除此条", key=f"del_{idx}", use_container_width=True):
                st.session_state.extractions.pop(idx)
                st.rerun()

        with st.expander(f"📁 查看源文件预览: {item['file']}", expanded=False):
            if item['file'].lower().endswith(".pdf"): st.success("📄 PDF 文档已成功解析")
            else: st.image(item['bytes'], use_column_width=True)

        # ---------------- A. 关键词 ----------------
        c_undo, c_refresh = st.columns([5, 5])
        with c_undo:
            if item.get('kw_history'):
                if st.button("⏪ 撤销返回", key=f"u_kw_{idx}", use_container_width=True):
                    item['data']['keywords'] = item['kw_history'].pop(); st.rerun()
        with c_refresh:
            if st.button("🔄 换一批词", key=f"r_kw_{idx}", use_container_width=True):
                # 此处省略刷新词的 API 请求逻辑（同之前版本）...
                pass

        for i, kw in enumerate(item['data'].get('keywords', [])):
            cx, cy, cz = st.columns([0.5, 6, 4])
            cx.write(f"**{i+1}**")
            with cy: render_copy_button(kw.get('kr', ''), f"kw_{idx}_{i}")
            cz.markdown(f"<div style='padding-top:10px; color:#666;'>{kw.get('cn', '')}</div>", unsafe_allow_html=True)

        # ---------------- B. 品名与标题 (略，结构同前) ----------------
        st.markdown("<br>##### 🏷️ 内部实体管理品名 / 🛒 Coupang SEO 标题", unsafe_allow_html=True)
        # 此处继续渲染 name_cn, name_kr, title_cn, title_kr 的复制按钮...
        # 为保持回答简洁，此处逻辑同前。
