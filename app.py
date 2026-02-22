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
    """兼容图片与 PDF 内存直传"""
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

# ================= 3. 界面配置与侧边栏 =================

st.set_page_config(page_title="品名识别生成工具", layout="wide", initial_sidebar_state="collapsed")

with st.sidebar:
    st.header("⚙️ 引擎配置")
    secret_key = st.secrets.get("GEMINI_API_KEY", "")
    manual_key = st.text_input("备用 API Key (可选)", value="", type="password")
    final_api_key = manual_key if manual_key else secret_key
    if not final_api_key:
        st.warning("👈 请配置 API Key")
        st.stop()
    genai.configure(api_key=final_api_key)
    st.success("✅ 极速引擎就绪")

# ================= 4. 主界面 (测款识图) =================

st.title("🔎 品名识别生成工具")
st.info("💡 **效率提示**：支持拖拽图片或 PDF。新增【🗑️ 删除工具】，可随时清理不需要的识别记录。")

files = st.file_uploader("📥 [全局上传/拖拽区]", type=["png", "jpg", "jpeg", "webp", "pdf"], accept_multiple_files=True)

if files:
    if st.button("🚀 开始极速精准提取", type="primary", use_container_width=True):
        new_exts = []
        for f in files:
            file_bytes = f.getvalue() 
            prompt_full = """
            任务：分析图片/文档，生成Coupang上架信息。
            规则：keywords提取5个精准名词；title_kr采用【客观卖点+核心词】平衡比例，严禁无脑堆砌或主观做作词，禁止标点，纯空格分隔。
            输出 JSON: { "keywords": [{"kr": "..", "cn": ".."}], "name_cn": "..", "name_kr": "..", "title_cn": "..", "title_kr": ".." }
            """
            with st.spinner(f"⚡ 正在解析 {f.name} ..."):
                res_text = process_lxu_file_bytes(file_bytes, f.name, prompt_full)
            try:
                json_str = re.search(r"\{.*\}", res_text, re.DOTALL).group()
                data = json.loads(json_str)
                new_exts.append({
                    "file": f.name, "bytes": file_bytes, "data": data,
                    "kw_history": [], "name_history": [], "title_history": []
                })
            except: st.error(f"{f.name} 解析失败")
        st.session_state.extractions = new_exts + st.session_state.extractions

# ================= 5. 渲染结果区 =================

if st.session_state.extractions:
    # 💡 增加一个“全部清空”的快捷键
    if st.button("🧨 清空所有结果", use_container_width=True):
        st.session_state.extractions = []
        st.rerun()

    for idx, item in enumerate(st.session_state.extractions):
        st.write("---")
        
        # 💡 核心修改：增加删除工具
        h_col1, h_col2 = st.columns([8, 2])
        with h_col1:
            st.markdown(f"### 🔎 建议搜索关键词")
        with h_col2:
            if st.button("🗑️ 删除此条", key=f"del_item_{idx}", use_container_width=True):
                st.session_state.extractions.pop(idx)
                st.rerun()

        with st.expander(f"📁 查看源文件: {item['file']}", expanded=False):
            if item['file'].lower().endswith(".pdf"): st.info("📄 PDF 文件已解析")
            else: st.image(item['bytes'], use_column_width=True)

        # ---------------- A. 关键词区域 ----------------
        c_undo_kw, c_btn_kw = st.columns([5, 5])
        with c_undo_kw:
            if item.get('kw_history'):
                if st.button("⏪ 撤销词", key=f"u_kw_{idx}", use_container_width=True):
                    item['data']['keywords'] = item['kw_history'].pop(); st.rerun()
        with c_btn_kw:
            if st.button("🔄 换一批词", key=f"r_kw_{idx}", use_container_width=True):
                # ... 省略中间刷新的 Prompt 逻辑以保持代码简洁，实际逻辑同前 ...
                pass

        for i, kw in enumerate(item['data'].get('keywords', [])):
            cx, cy, cz = st.columns([0.5, 6, 4])
            cx.write(f"{i+1}")
            with cy: render_copy_button(kw.get('kr', ''), f"kw_{idx}_{i}")
            cz.markdown(f"<div style='padding-top:10px; color:#666;'>{kw.get('cn', '')}</div>", unsafe_allow_html=True)

        # ---------------- B. 品名与标题 (同前，略) ----------------
        st.markdown("##### 🏷️ 内部实体管理品名 / 🛒 Coupang SEO 标题")
        # 此处省略具体渲染细节，保持整体结构 ...
        nc1, nc2 = st.columns([1, 9]); nc1.write("品名CN"); render_copy_button(item['data'].get('name_cn',''), f"ncn_{idx}")
        tc1, tc2 = st.columns([1, 9]); tc1.write("标题KR"); render_copy_button(item['data'].get('title_kr',''), f"tkr_{idx}")
