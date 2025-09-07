import streamlit as st
import os
from PIL import Image
from openai import OpenAI
from datetime import datetime

import auth_utils  # Firebase 認証/残回数管理

# ---------------------------
# ページ設定 & ログインチェック
# ---------------------------
st.set_page_config(layout="wide", page_title="バナスコAI - コピー生成")
auth_utils.check_login()

# OpenAI 初期化
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    st.error("❌ OpenAI APIキーが見つかりませんでした。`.env` を確認してください。")
    st.stop()
client = OpenAI(api_key=openai_api_key)

# --- Ultimate Professional CSS Theme ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');
    
    /* Professional dark gradient background */
    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1c29 15%, #2d3748 35%, #1a202c 50%, #2d3748 65%, #4a5568 85%, #2d3748 100%) !important;
        background-attachment: fixed;
        background-size: 400% 400%;
        animation: background-flow 15s ease-in-out infinite;
    }
    
    @keyframes background-flow {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    body {
        background: transparent !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* Professional main container with glassmorphism */
    .main .block-container {
        background: rgba(26, 32, 44, 0.4) !important;
        backdrop-filter: blur(60px) !important;
        border: 2px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 32px !important;
        box-shadow: 
            0 50px 100px -20px rgba(0, 0, 0, 0.6),
            0 0 0 1px rgba(255, 255, 255, 0.05),
            inset 0 2px 0 rgba(255, 255, 255, 0.15) !important;
        padding: 5rem 4rem !important;
        position: relative !important;
        margin: 2rem auto !important;
        max-width: 1400px !important;
        min-height: 95vh !important;
    }
    
    .main .block-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, 
            rgba(56, 189, 248, 0.04) 0%, 
            rgba(147, 51, 234, 0.04) 25%, 
            rgba(59, 130, 246, 0.04) 50%, 
            rgba(168, 85, 247, 0.04) 75%, 
            rgba(56, 189, 248, 0.04) 100%);
        border-radius: 32px;
        pointer-events: none;
        z-index: -1;
        animation: container-glow 8s ease-in-out infinite alternate;
    }
    
    @keyframes container-glow {
        from { opacity: 0.3; }
        to { opacity: 0.7; }
    }

    /* Professional sidebar */
    .stSidebar {
        background: linear-gradient(180deg, rgba(15, 15, 26, 0.98) 0%, rgba(26, 32, 44, 0.98) 100%) !important;
        backdrop-filter: blur(40px) !important;
        border-right: 2px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 8px 0 50px rgba(0, 0, 0, 0.5) !important;
    }
    
    .stSidebar > div:first-child {
        background: transparent !important;
    }
    
    /* Ultimate gradient button styling */
    .stButton > button {
        background: linear-gradient(135deg, #38bdf8 0%, #a855f7 50%, #06d6a0 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 60px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        padding: 1.25rem 3rem !important;
        letter-spacing: 0.05em !important;
        box-shadow: 
            0 15px 35px rgba(56, 189, 248, 0.4),
            0 8px 20px rgba(168, 85, 247, 0.3),
            0 0 60px rgba(6, 214, 160, 0.2),
            inset 0 2px 0 rgba(255, 255, 255, 0.3) !important;
        transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative !important;
        overflow: hidden !important;
        backdrop-filter: blur(20px) !important;
        width: 100% !important;
        text-transform: uppercase !important;
        transform: perspective(1000px) translateZ(0);
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
        transition: left 0.8s;
        z-index: 1;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #0ea5e9 0%, #9333ea 50%, #059669 100%) !important;
        box-shadow: 
            0 25px 50px rgba(56, 189, 248, 0.6),
            0 15px 35px rgba(168, 85, 247, 0.5),
            0 0 100px rgba(6, 214, 160, 0.4),
            inset 0 2px 0 rgba(255, 255, 255, 0.4) !important;
        transform: translateY(-5px) scale(1.03) perspective(1000px) translateZ(20px) !important;
    }
    
    .stButton > button:active {
        transform: translateY(-2px) scale(1.01) !important;
        box-shadow: 
            0 15px 30px rgba(56, 189, 248, 0.4),
            0 8px 20px rgba(168, 85, 247, 0.3) !important;
    }

    /* Ultimate expander styling */
    .stExpander {
        background: rgba(26, 32, 44, 0.6) !important;
        border: 2px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 24px !important;
        backdrop-filter: blur(40px) !important;
        margin: 2rem 0 !important;
        overflow: hidden !important;
        box-shadow: 
            0 20px 40px rgba(0, 0, 0, 0.3),
            0 0 80px rgba(56, 189, 248, 0.1),
            inset 0 2px 0 rgba(255, 255, 255, 0.15) !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    .stExpander:hover {
        transform: translateY(-4px) scale(1.01) !important;
        box-shadow: 
            0 30px 60px rgba(0, 0, 0, 0.4),
            0 0 120px rgba(56, 189, 248, 0.2),
            inset 0 2px 0 rgba(255, 255, 255, 0.2) !important;
        border-color: rgba(56, 189, 248, 0.3) !important;
    }
    
    .stExpander > div > div {
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.15) 0%, rgba(168, 85, 247, 0.15) 100%) !important;
        border-bottom: 2px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 24px 24px 0 0 !important;
        color: rgba(255, 255, 255, 0.95) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: 0.05em !important;
        padding: 2rem !important;
        font-size: 1.2rem !important;
        text-transform: uppercase;
    }
    /* Hide the "Collapse" text on the expander */
    .stExpander > button > div:last-child {
        display: none;
    }
    
    .stExpanderDetails {
        background: rgba(26, 32, 44, 0.4) !important;
        border-radius: 0 0 24px 24px !important;
        padding: 2.5rem !important;
    }

    /* Ultimate input styling - MODIFIED */
    div[data-baseweb="input"] input,
    div[data-baseweb="select"] span,
    div[data-baseweb="textarea"] textarea,
    .stSelectbox .st-bv,
    .stTextInput .st-eb,
    .stTextArea .st-eb,
    /* --- More robust selectors for text color --- */
    [data-testid="stTextInput"] input,
    [data-testid="stSelectbox"] span,
    [data-testid="stTextarea"] textarea {
        background: rgba(26, 32, 44, 0.8) !important;
        color: #FBC02D !important; /* CHANGED TO YELLOW */
        border: 2px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 16px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        backdrop-filter: blur(40px) !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 
            0 8px 16px rgba(0, 0, 0, 0.2),
            0 0 40px rgba(56, 189, 248, 0.1),
            inset 0 2px 0 rgba(255, 255, 255, 0.15) !important;
        padding: 1rem 1.5rem !important;
        font-size: 1rem !important;
    }
    
    /* Advanced focus effect */
    div[data-baseweb="input"] input:focus,
    div[data-baseweb="select"] span:focus,
    div[data-baseweb="textarea"] textarea:focus,
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="select"]:focus-within,
    div[data-baseweb="textarea"]:focus-within {
        border-color: rgba(56, 189, 248, 0.8) !important;
        box-shadow: 
            0 0 0 4px rgba(56, 189, 248, 0.3),
            0 15px 35px rgba(56, 189, 248, 0.2),
            0 0 80px rgba(56, 189, 248, 0.15),
            inset 0 2px 0 rgba(255, 255, 255, 0.25) !important;
        transform: translateY(-2px) scale(1.01) !important;
        background: rgba(26, 32, 44, 0.9) !important;
    }

    /* Ultimate title styling */
    h1, .stTitle {
        font-size: 5rem !important;
        font-weight: 900 !important;
        background: linear-gradient(135deg, #38bdf8 0%, #a855f7 20%, #3b82f6 40%, #06d6a0 60%, #f59e0b 80%, #38bdf8 100%) !important;
        background-size: 600% 600% !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        text-align: center !important;
        margin: 2rem 0 !important;
        letter-spacing: -0.05em !important;
        animation: mega-gradient-shift 12s ease-in-out infinite !important;
        text-shadow: 0 0 80px rgba(56, 189, 248, 0.5) !important;
        transform: perspective(1000px) rotateX(10deg);
    }
    
    @keyframes mega-gradient-shift {
        0%, 100% { background-position: 0% 50%; }
        20% { background-position: 100% 0%; }
        40% { background-position: 100% 100%; }
        60% { background-position: 50% 100%; }
        80% { background-position: 0% 100%; }
    }
    
    h2, .stSubheader {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1.6rem !important;
        text-align: center !important;
        margin-bottom: 3rem !important;
        letter-spacing: 0.05em !important;
    }
    
    h3, h4, h5, h6 {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: 0.025em !important;
    }

    /* Professional text styling */
    p, div, span, label, .stMarkdown {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 400 !important;
        line-height: 1.7 !important;
    }
    
    /* Ultimate file uploader styling */
    .stFileUploader {
        border: 3px dashed rgba(56, 189, 248, 0.7) !important;
        border-radius: 24px !important;
        background: rgba(26, 32, 44, 0.4) !important;
        backdrop-filter: blur(20px) !important;
        box-shadow: 
            0 15px 35px rgba(0, 0, 0, 0.25),
            0 0 60px rgba(56, 189, 248, 0.2),
            inset 0 2px 0 rgba(255, 255, 255, 0.15) !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        padding: 3rem !important;
    }
    
    .stFileUploader:hover {
        border-color: rgba(168, 85, 247, 0.9) !important;
        background: rgba(26, 32, 44, 0.6) !important;
        box-shadow: 
            0 25px 50px rgba(0, 0, 0, 0.3),
            0 0 100px rgba(168, 85, 247, 0.4),
            inset 0 2px 0 rgba(255, 255, 255, 0.2) !important;
        transform: translateY(-4px) scale(1.02) !important;
    }

    /* Ultimate image styling */
    .stImage > img {
        border: 3px solid rgba(56, 189, 248, 0.4) !important;
        border-radius: 20px !important;
        box-shadow: 
            0 20px 40px rgba(0, 0, 0, 0.3),
            0 0 60px rgba(56, 189, 248, 0.3) !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    .stImage > img:hover {
        transform: scale(1.03) translateY(-4px) !important;
        box-shadow: 
            0 30px 60px rgba(0, 0, 0, 0.4),
            0 0 100px rgba(56, 189, 248, 0.5) !important;
        border-color: rgba(168, 85, 247, 0.6) !important;
    }
    
    /* Remove Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Ultimate scrollbar */
    ::-webkit-scrollbar { width: 12px; }
    ::-webkit-scrollbar-track { background: rgba(26, 32, 44, 0.4); border-radius: 6px; }
    ::-webkit-scrollbar-thumb { background: linear-gradient(135deg, #38bdf8, #a855f7); border-radius: 6px; box-shadow: 0 0 20px rgba(56, 189, 248, 0.5); }
    ::-webkit-scrollbar-thumb:hover { background: linear-gradient(135deg, #0ea5e9, #9333ea); box-shadow: 0 0 30px rgba(168, 85, 247, 0.7); }
    
    /* === 入力欄の文字色を黄色に（値・キャレット・プレースホルダー） === */
    .stTextInput input,
    .stTextArea textarea,
    div[data-baseweb="input"] input {
      color: #FBC02D !important;
      caret-color: #FBC02D !important;
    }
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder,
    div[data-baseweb="input"] input::placeholder {
      color: rgba(251, 192, 45, 0.6) !important;
    }
    .stTextInput input:disabled,
    .stTextArea textarea:disabled,
    div[data-baseweb="input"] input:disabled {
      color: rgba(251, 192, 45, 0.5) !important;
    }
    
    /* === セレクトの表示値（閉じている時のテキスト）を黄色に === */
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div[role="button"] {
      color: #FBC02D !important;
    }
    
    /* ▼アイコンも黄色に */
    div[data-baseweb="select"] svg {
      color: #FBC02D !important;
      fill: #FBC02D !important;
      opacity: 0.95 !important;
    }
    
    /* === セレクトのドロップダウン（ポップオーバー）は body 直下に出るのでグローバル指定 === */
    /* 背景をダーク、文字を白にして可読性を確保 */
    [data-baseweb="popover"],
    [role="listbox"],
    [data-baseweb="menu"] {
      background: #11131e !important;
      border: 2px solid rgba(255, 255, 255, 0.2) !important;
      border-radius: 20px !important;
      box-shadow: 0 30px 60px rgba(0,0,0,0.4) !important;
      z-index: 9999 !important;
    }
    [data-baseweb="popover"] ul li,
    [role="option"],
    [data-baseweb="menu"] li {
      color: #ffffff !important;
    }
    [role="option"][aria-selected="true"],
    [data-baseweb="menu"] li[aria-selected="true"],
    [data-baseweb="menu"] li:hover {
      background: linear-gradient(135deg, rgba(56,189,248,0.3), rgba(168,85,247,0.3)) !important;
      color: #ffffff !important;
    }

    /* ① セレクトの「プレート」（閉じている時の白い板）を黒に */
    [data-testid="stSelectbox"] > div > div {
      background: #0b0d15 !important;              /* 黒 */
      border: 2px solid rgba(255,255,255,0.2) !important;
      border-radius: 16px !important;
    }

    /* ② ドロップダウンのパネル自体（開いた時の白い板）を黒に */
    body > div[role="listbox"],
    body > div[data-baseweb="popover"] {
      background: #0b0d15 !important;              /* 黒 */
      border: 2px solid rgba(255,255,255,0.2) !important;
      border-radius: 20px !important;
      box-shadow: 0 30px 60px rgba(0,0,0,0.4) !important;
      z-index: 9999 !important;
    }

    /* ③ パネル内の要素で白背景が残る場合の保険（透明化） */
    body > div[role="listbox"] * ,
    body > div[data-baseweb="popover"] * {
      background-color: transparent !important;
    }

    /* ④ 選択肢のホバー／選択時 */
    body [role="option"] { color: #ffffff !important; }
    body [role="option"][aria-selected="true"],
    body [role="option"]:hover {
      background: rgba(56,189,248,0.18) !important;
    }

    /* ⑤ セレクトの値（閉じている時の表示行）も黒背景で統一 */
    div[data-baseweb="select"] > div[role="combobox"] {
      background: #0b0d15 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📸 バナー画像からコピー案を生成")

# ---------------------------
# 1) 画像アップロード（任意）
# ---------------------------
uploaded_image = st.file_uploader("バナー画像をアップロード（任意）", type=["jpg", "png"])
if uploaded_image:
    image = Image.open(uploaded_image)
    st.image(image, caption="アップロードされた画像", use_container_width=True)

# ---------------------------
# 2) 業種カテゴリ
# ---------------------------
category = st.selectbox(
    "業種カテゴリを選択",
    [
        "美容室", "脱毛サロン", "エステ", "ネイル・まつげ", "ホワイトニング",
        "整体・接骨院", "学習塾", "子ども写真館", "飲食店", "その他"
    ]
)

# ---------------------------
# 3) 基本情報
# ---------------------------
col1, col2 = st.columns(2)
with col1:
    target = st.text_input("ターゲット層（例：30代女性、経営者など）")
    tone = st.selectbox("トーン（雰囲気）", ["親しみやすい", "高級感", "情熱的", "おもしろ系", "真面目"])
with col2:
    feature = st.text_area("商品の特徴・アピールポイント（箇条書きOK）", height=120)

# ---------------------------
# 4) 生成オプション（UIを拡張）
# ---------------------------
st.markdown("### ⚙️ 生成オプション")

# プランと残回数
user_plan = st.session_state.get("plan", "Guest")
remaining_uses = st.session_state.get("remaining_uses", 0)

# プラン別 1リクエストあたりの最大生成数
plan_to_max = {
    "Free": 0, "Guest": 0,
    "Light": 3, "Pro": 5, "Team": 10, "Enterprise": 10
}
max_copy_count_per_request = plan_to_max.get(user_plan, 0)
if max_copy_count_per_request == 0:
    copy_count_options = [0]
else:
    copy_count_options = list(range(1, max_copy_count_per_request + 1))

# コピータイプ
st.caption("コピータイプ（複数選択可）")
type_cols = st.columns(4)
with type_cols[0]:
    want_main = st.checkbox("メインコピー")
with type_cols[1]:
    want_catch = st.checkbox("キャッチコピー", value=True)
with type_cols[2]:
    want_cta = st.checkbox("CTAコピー")
with type_cols[3]:
    want_sub = st.checkbox("サブコピー")

# 生成数
copy_count = st.selectbox(
    f"生成数（各タイプにつき / 上限: {max_copy_count_per_request}案）",
    copy_count_options,
    index=0 if 0 in copy_count_options else 0,
    format_func=lambda x: f"{x}パターン" if x > 0 else "—"
)

# 絵文字 / 緊急性
opt_cols = st.columns(2)
with opt_cols[0]:
    include_emoji = st.checkbox("絵文字を含める")
with opt_cols[1]:
    include_urgency = st.checkbox("緊急性要素を含める（例：期間限定・先着・残りわずか）")

# 投稿文作成ブロック
st.markdown("---")
st.subheader("📝 投稿文作成（任意）")
enable_caption = st.checkbox("投稿文も作成する")
caption_lines = 0
caption_keywords = ""
if enable_caption:
    caption_lines = st.selectbox("投稿文の行数", [1, 2, 3, 4, 5], index=2)
    caption_keywords = st.text_input("任意で含めたいワード（カンマ区切り）", placeholder="例）初回割引, 予約リンク, 土日OK")

# ---------------------------
# 5) 生成ボタン
# ---------------------------
needs_yakkihou = category in ["脱毛サロン", "エステ", "ホワイトニング"]

def build_prompt():
    # コピータイプの指示をまとめる
    type_instructions = []
    if want_main:
        type_instructions.append(f"- **メインコピー**：{copy_count}案")
    if want_catch:
        type_instructions.append(f"- **キャッチコピー**：{copy_count}案")
    if want_cta:
        type_instructions.append(f"- **CTAコピー**：{copy_count}案")
    if want_sub:
        type_instructions.append(f"- **サブコピー**：{copy_count}案")
    if not type_instructions and not enable_caption:
        return None  # 何も選ばれていない

    emoji_rule = "・各案に1〜2個の絵文字を自然に入れてください。" if include_emoji else "・絵文字は使用しないでください。"
    urgency_rule = "・必要に応じて『期間限定』『先着順』『残りわずか』などの緊急性フレーズも自然に織り交ぜてください。" if include_urgency else ""
    yakki_rule = "・薬機法/医療広告ガイドラインに抵触する表現は避けてください（例：治る、即効、永久、医療行為の示唆 など）。" if needs_yakkihou else ""
    cap_rule = ""
    if enable_caption and caption_lines > 0:
        cap_rule = f"""
### 投稿文作成
- 改行で{caption_lines}行の投稿文を作成（行ごとに要点を変えてください）
- 1行あたり読みやすい長さ（40〜60文字目安）
- ターゲットとトーンに合わせて自然な日本語
- ハッシュタグは付けない
- 任意ワードがあれば必ず自然に含める（過剰な羅列は禁止）
"""

    keywords_text = f"任意ワード：{caption_keywords}" if caption_keywords else "任意ワード：なし"

    # 最終プロンプト
    return f"""
あなたは優秀な広告コピーライターです。下記条件に沿って、用途別に日本語で提案してください。出力は**Markdown**で、各セクションに見出しを付け、番号付きリストで返してください。

【業種】{category}
【ターゲット層】{target or '未指定'}
【特徴・アピールポイント】{feature or '未指定'}
【トーン】{tone}
【{keywords_text}】
【共通ルール】
- 同じ方向性を避け、毎案ニュアンスを変える
- 媒体に載せやすい簡潔な文
- 露骨な煽りは避けつつ、訴求は明確に
{emoji_rule}
{urgency_rule}
{yakki_rule}

### 生成対象
{os.linesep.join(type_instructions) if type_instructions else '- （コピータイプなし）'}

{cap_rule}

### 追加ガイド
- **キャッチコピー**：インパクト重視/30字以内目安
- **メインコピー**：価値が伝わる説明的コピー/40字前後
- **サブコピー**：補足やベネフィット/60字以内
- **CTAコピー**：行動喚起/16字以内/明快

出力フォーマット例：
## キャッチコピー
1. 〜
2. 〜

## メインコピー
1. 〜
...

{ '## 投稿文\n1)\n2)\n...' if enable_caption else '' }
"""

generate_btn = st.button("🚀 コピーを生成する")

if generate_btn:
    # プランチェック
    if user_plan in ["Free", "Guest"]:
        st.warning("この機能はFree/Guestプランではご利用いただけません。Light以上のプランでご利用ください。")
        st.stop()
    # 残回数チェック
    if remaining_uses <= 0:
        st.warning(f"残り回数がありません。（現在プラン：{user_plan}）")
        st.info("利用回数を増やすには、プランのアップグレードが必要です。")
        st.stop()
    # 生成数チェック
    if copy_count == 0 and not enable_caption:
        st.warning("コピー生成数が0です。少なくとも1案以上を選択するか、投稿文作成を有効にしてください。")
        st.stop()

    prompt = build_prompt()
    if prompt is None:
        st.warning("コピータイプが1つも選択されていません。少なくとも1つ選択してください。")
        st.stop()

    with st.spinner("コピー案を生成中..."):
        try:
            # OpenAI へ投げる
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたは日本語に精通した広告コピーライターです。マーケ基礎と法規を理解し、簡潔で効果的な表現を作ります。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,
            )
            output = resp.choices[0].message.content.strip()

            # 表示
            st.subheader("✍️ 生成結果")
            st.markdown(output)

            if needs_yakkihou:
                st.subheader("🔍 薬機法メモ")
                st.info("※ このカテゴリでは『治る／即効／永久／医療行為の示唆』などはNG。効能・効果の断定表現も避けましょう。")

            # 使⽤回数の消費（失敗してもアプリが落ちないよう try）
            try:
                if auth_utils.update_user_uses_in_firestore_rest(
                    st.session_state.get("user"),
                    st.session_state.get("id_token")
                ):
                    # UI上の残回数を1減らす
                    st.session_state["remaining_uses"] = max(0, remaining_uses - 1)
            except Exception:
                pass

        except Exception as e:
            st.error(f"コピー生成中にエラーが発生しました：{e}")
