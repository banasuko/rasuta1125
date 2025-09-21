import streamlit as st
import os
from PIL import Image
from openai import OpenAI
from datetime import datetime
import sys

# --- ▼▼▼ このブロックを追加 ▼▼▼ ---
# プロジェクトのルートディレクトリをPythonのパスに追加
# これにより、別階層にある auth_utils を正しくインポートできる
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# --- ▲▲▲ このブロックを追加 ▲▲▲ ---

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

# Session Stateの初期化
if 'select_all_copies' not in st.session_state:
    st.session_state.select_all_copies = True
if 'cb_main' not in st.session_state:
    st.session_state.cb_main = True
if 'cb_catch' not in st.session_state:
    st.session_state.cb_catch = True
if 'cb_cta' not in st.session_state:
    st.session_state.cb_cta = True
if 'cb_sub' not in st.session_state:
    st.session_state.cb_sub = True


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
        background: #1a1c29 !important; /* Navy Blue */
        color: #FBC02D !important; /* Yellow */
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
    
    /* === セレクトのドロップダウンパネル自体をダークに === */
    [data-baseweb="popover"],
    [role="listbox"],
    [data-baseweb="menu"] {
      background: #11131e !important;
      border: 2px solid rgba(255, 255, 255, 0.2) !important;
      border-radius: 20px !important;
      box-shadow: 0 30px 60px rgba(0,0,0,0.4) !important;
      z-index: 9999 !important;
    }

    /* === ★★★ここからが修正箇所★★★ === */
    /* ④ 選択肢の通常時、ホバー／選択時 */
    body [role="option"] {
      color: #ffffff !important;
      background-color: #0b0d15 !important; /* 選択肢の背景を紺色に */
      transition: background 0.3s ease-in-out !important; /* なめらかな変化 */
    }

    body [role="option"][aria-selected="true"],
    body [role="option"]:hover {
       /* ホバー時の虹色アニメーション */
      background: linear-gradient(270deg, red, orange, yellow, green, blue, indigo, violet) !important;
      background-size: 400% 400% !important;
      animation: rainbow 5s ease infinite !important;
      color: white !important;
    }

    @keyframes rainbow {
        0%{background-position:0% 50%}
        50%{background-position:100% 50%}
        100%{background-position:0% 50%}
    }
    /* === ★★★ここまでが修正箇所★★★ === */


    /* ① セレクトの「プレート」（閉じている時の表示部分） */
    [data-testid="stSelectbox"] > div > div {
      background: #1a1c29 !important; 
      border: 2px solid rgba(255,255,255,0.2) !important;
      border-radius: 16px !important;
    }

    /* ⑤ セレクトの値（閉じている時の表示行）も黒背景で統一 */
    div[data-baseweb="select"] > div[role="combobox"] {
      background: transparent !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("✍️ バナーコピー生成")

# ---------------------------
# プランと残回数の取得
# ---------------------------
user_plan = st.session_state.get("plan", "Guest")
remaining_uses = st.session_state.get("remaining_uses", 0)

# ---------------------------
# Freeプランの期間限定アクセスチェック
# ---------------------------
now = datetime.now()
is_free_trial_period = (now.year <= 2024 and now.month <= 12 and now.day <= 30)

if user_plan == "Free" and not is_free_trial_period:
    st.warning("Freeプランのコピー生成機能の特典期間は2024年12月30日で終了しました。")
    st.info("引き続きご利用になるには、Light以上のプランへのアップグレードが必要です。")
    st.stop()
elif user_plan == "Guest":
    st.warning("この機能はGuestプランではご利用いただけません。")
    st.info("機能をお試しになるには、アカウントを作成してFreeプランをご利用ください。")
    st.stop()


# ---------------------------
# UI表示
# ---------------------------
uploaded_image = st.file_uploader("参考にするバナー画像をアップロード（任意）", type=["jpg", "png"])
if uploaded_image:
    image = Image.open(uploaded_image)
    st.image(image, caption="アップロードされた画像", width=300)

# --- ▼▼▼ 変更点: 業種カテゴリに「不動産」を追加 ▼▼▼ ---
category = st.selectbox(
    "業種カテゴリを選択",
    [
        "美容室", "脱毛サロン", "エステ", "ネイル・まつげ", "ホワイトニング",
        "整体・接骨院", "学習塾", "子ども写真館", "飲食店", "不動産", "その他"
    ]
)
# --- ▲▲▲ 変更点ここまで ▲▲▲ ---

col1, col2 = st.columns(2)
with col1:
    target = st.text_input("ターゲット層（例：30代女性、経営者など）")
    tone = st.selectbox("トーン（雰囲気）", ["親しみやすい", "高級感", "情熱的", "おもしろ系", "真面目"])
with col2:
    feature = st.text_area("商品の特徴・アピールポイント（箇条書きOK）", height=120)

st.markdown("### ⚙️ 生成オプション")

plan_to_max = {
    "Free": 1, "Guest": 0,
    "Light": 3, "Pro": 5, "Team": 10, "Enterprise": 10
}
max_copy_count_per_request = plan_to_max.get(user_plan, 0)
copy_count_options = list(range(1, max_copy_count_per_request + 1)) if max_copy_count_per_request > 0 else [0]


# --- コピータイプ選択のUI ---
st.caption("コピータイプ（複数選択可）")

if st.button("すべて選択 / 解除"):
    st.session_state.select_all_copies = not st.session_state.select_all_copies
    st.session_state.cb_main = st.session_state.select_all_copies
    st.session_state.cb_catch = st.session_state.select_all_copies
    st.session_state.cb_cta = st.session_state.select_all_copies
    st.session_state.cb_sub = st.session_state.select_all_copies

type_cols = st.columns(4)
with type_cols[0]:
    st.checkbox("メインコピー", key="cb_main")
with type_cols[1]:
    st.checkbox("キャッチコピー", key="cb_catch")
with type_cols[2]:
    st.checkbox("CTAコピー", key="cb_cta")
with type_cols[3]:
    st.checkbox("サブコピー", key="cb_sub")

copy_count = st.selectbox(
    f"生成数（各タイプにつき / 上限: {max_copy_count_per_request}案）",
    copy_count_options,
    index=0,
    format_func=lambda x: f"{x}パターン" if x > 0 else "—"
)

opt_cols = st.columns(2)
with opt_cols[0]:
    include_emoji = st.checkbox("絵文字を含める")
with opt_cols[1]:
    include_urgency = st.checkbox("緊急性要素を含める（例：期間限定・先着・残りわずか）")

add_ctr = False
if user_plan not in ["Free", "Guest"]:
    with st.expander("高度な機能 (Lightプラン以上)"):
        add_ctr = st.checkbox("予想CTRを追加")

# --- 投稿文作成のUI ---
st.markdown("---")
enable_caption = False
caption_lines = 0
caption_keywords = ""
selected_hashtags = []

if user_plan != "Free":
    st.subheader("📝 投稿文作成（任意）")
    enable_caption = st.checkbox("投稿文も作成する（3パターン生成）")
    if enable_caption:
        caption_lines = st.selectbox("投稿文の行数", [3, 4, 5], index=0)
        caption_keywords = st.text_input("任意で含めたいワード（カンマ区切り）", placeholder="例）初回割引, 予約リンク, 土日OK")

        if user_plan == "Pro":
            st.markdown("##### # ハッシュタグ選択（Proプラン限定）")
            st.caption("関連性の高いハッシュタグをAIが自動で5個ずつ生成します。")
            hashtag_cols = st.columns(4)
            with hashtag_cols[0]:
                if st.checkbox("業種系", key="ht_cat1"): selected_hashtags.append("業種関連")
            with hashtag_cols[1]:
                if st.checkbox("ターゲット系", key="ht_cat2"): selected_hashtags.append("ターゲット層関連")
            with hashtag_cols[2]:
                if st.checkbox("訴求系", key="ht_cat3"): selected_hashtags.append("訴求ポイント関連")
            with hashtag_cols[3]:
                if st.checkbox("その他", key="ht_cat4"): selected_hashtags.append("その他お悩み・ベネフィット関連")


# ---------------------------
# プロンプト生成 & 実行
# ---------------------------
needs_yakkihou = category in ["脱毛サロン", "エステ", "ホワイトニング"]

def build_prompt():
    type_instructions = []
    if st.session_state.cb_main: type_instructions.append(f"- **メインコピー**：{copy_count}案")
    if st.session_state.cb_catch: type_instructions.append(f"- **キャッチコピー**：{copy_count}案")
    if st.session_state.cb_cta: type_instructions.append(f"- **CTAコピー**：{copy_count}案")
    if st.session_state.cb_sub: type_instructions.append(f"- **サブコピー**：{copy_count}案")

    if not type_instructions and not enable_caption:
        return None

    emoji_rule = "・各案に1〜2個の絵文字を自然に入れてください。" if include_emoji else "・絵文字は使用しないでください。"
    urgency_rule = "・必要に応じて『期間限定』『先着順』『残りわずか』などの緊急性フレーズも自然に織り交ぜてください。" if include_urgency else ""
    yakki_rule = "・薬機法/医療広告ガイドラインに抵触する表現は避けてください（例：治る、即効、永久、医療行為の示唆 など）。" if needs_yakkihou else ""
    ctr_rule = "・各コピー案に対して、予想されるクリックスルー率（CTR）をパーセンテージで示してください。" if add_ctr else ""

    cap_rule = ""
    hashtags_rule = ""
    if enable_caption and caption_lines > 0:
        cap_rule = f"""
### 投稿文作成
- **必ず3パターンの投稿文を生成してください。**
- 各パターンは、**必ず{caption_lines}個の独立した段落（行）で構成してください。** 行数を増やしたり減らしたりすることは絶対に禁止です。
- 各行の終わりでは必ず改行してください。
- 1行あたり読みやすい長さ（40〜60文字目安）でお願いします。
- ターゲットとトーンに合わせて自然な日本語で作成してください。
- ハッシュタグは付けないでください。
- 任意ワードがあれば必ず自然に含めてください（過剰な羅列は禁止）。
"""
        if selected_hashtags:
            hashtags_text = "、".join(selected_hashtags)
            hashtags_rule = f"""
### ハッシュタグ生成
- 投稿文の最後に、以下のカテゴリに沿った人気の日本語ハッシュタグを、それぞれ5個ずつ、合計{len(selected_hashtags) * 5}個生成してください。
- カテゴリ：{hashtags_text}
- フォーマットは `#タグ #タグ` のように半角スペース区切りで一行にまとめてください。
"""

    keywords_text = f"任意ワード：{caption_keywords}" if caption_keywords else "任意ワード：なし"
    
    copy_generation_rule = "下記「生成対象」で指定されたコピータイプのみを生成してください。指定のないコピータイプは絶対に出力しないでください。"
    if not type_instructions:
        copy_generation_rule = "コピータイプの生成は不要です。"


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
{ctr_rule}
- {copy_generation_rule}

### 生成対象
{os.linesep.join(type_instructions) if type_instructions else '- （コピータイプの生成なし）'}

{cap_rule}
{hashtags_rule}

### 追加ガイド
- **キャッチコピー**：インパクト重視/30字以内目安
- **メインコピー**：価値が伝わる説明的コピー/40字前後
- **サブコピー**：補足やベネフィット/60字以内
- **CTAコピー**：行動喚起/16字以内/明快

出力フォーマット例：
## キャッチコピー
1. 〜 (予想CTR: X.X%)
2. 〜 (予想CTR: Y.Y%)

## メインコピー
1. 〜 (予想CTR: Z.Z%)
...
"""

generate_btn = st.button("🚀 コピーを生成する")

if generate_btn:
    if remaining_uses <= 0:
        st.warning(f"残り回数がありません。（現在プラン：{user_plan}）")
        st.info("利用回数を増やすには、プランのアップグレードが必要です。")
        st.stop()
    if copy_count == 0 and not enable_caption:
        st.warning("コピー生成数が0です。少なくとも1案以上を選択するか、投稿文作成を有効にしてください。")
        st.stop()

    prompt = build_prompt()
    if prompt is None:
        st.warning("コピータイプが1つも選択されていない、かつ投稿文作成も無効です。少なくともどちらか一方を有効にしてください。")
        st.stop()

    with st.spinner("コピー案を生成中..."):
        try:
            if auth_utils.update_user_uses_in_firestore(st.session_state["user"]):
                st.session_state.remaining_uses -= 1

                resp = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "あなたは日本語に精通した広告コピーライターです。マーケ基礎と法規を理解し、簡潔で効果的な表現を作ります。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.9,
                )
                output = resp.choices[0].message.content.strip()

                st.subheader("✍️ 生成結果")
                st.markdown(output)

                if needs_yakkihou:
                    st.subheader("🔍 薬機法メモ")
                    st.info("※ このカテゴリでは『治る／即効／永久／医療行為の示唆』などはNG。効能・効果の断定表現も避けましょう。")
            else:
                st.error("利用回数の更新に失敗しました。")
        except Exception as e:
            st.error(f"コピー生成中にエラーが発生しました：{e}")
