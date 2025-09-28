import streamlit as st
import base64
import io
import os
import re
import requests
from PIL import Image
from datetime import datetime
from openai import OpenAI

import auth_utils # Import Firebase authentication

# Google Apps Script (GAS) and Google Drive information (GAS for legacy spreadsheet, will be removed later if not needed)
GAS_URL = "https://script.google.com/macros/s/AKfycby_uD6Jtb9GT0-atbyPKOPc8uyVKodwYVIQ2Tpe-_E8uTOPiir0Ce1NAPZDEOlCUxN4/exec" # Update this URL to your latest GAS deployment URL

# Helper function to sanitize values
def sanitize(value):
    """Replaces None or specific strings with 'エラー' (Error)"""
    if value is None or value == "取得できず":
        return "エラー"
    return value

# Streamlit UI configuration
st.set_page_config(layout="wide", page_title="バナスコAI")

# --- Logo Display ---
logo_path = "banasuko_logo_icon.png"

try:
    logo_image = Image.open(logo_path)
    st.sidebar.image(logo_image, use_container_width=True) # Display logo in sidebar, adjusting to column width
except FileNotFoundError:
    st.sidebar.error(f"ロゴ画像 '{logo_path}' が見つかりません。ファイルが正しく配置されているか確認してください。")

# --- Login Check ---
# This is crucial! Code below this line will only execute if the user is logged in.
auth_utils.check_login()

# --- OpenAI Client Initialization ---
# Initialize OpenAI client after login check, when OpenAI API key is available from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    client = OpenAI(api_key=openai_api_key)
else:
    # For demo purposes without API key
    client = None
    st.warning("デモモード - OpenAI APIが設定されていません")


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

# --- Clean Professional Header ---
st.markdown('<div class="main-header">', unsafe_allow_html=True)

# Use standard Streamlit components instead of complex HTML
st.markdown("# バナスコAI")
st.markdown("## AI広告診断システム")
st.markdown("### もう、無駄打ちしない。広告を\"武器\"に変えるプロフェッショナルAIツール")

st.markdown("---")

# Add professional badge
st.markdown("""
<div style="text-align: center; margin: 2rem 0;">
    <span style="background: linear-gradient(135deg, rgba(56, 189, 248, 0.2), rgba(168, 85, 247, 0.2)); 
                   padding: 1rem 2rem; 
                   border-radius: 50px; 
                   border: 1px solid rgba(255, 255, 255, 0.2); 
                   color: rgba(255, 255, 255, 0.9);
                   font-weight: 600;
                   letter-spacing: 0.1em;">
        Professional Banner Analysis Platform
    </span>
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- プランと残回数の取得 ---
user_plan = st.session_state.get("plan", "Guest")
remaining_uses = st.session_state.get("remaining_uses", 0)

# --- Ultimate Main Content Layout ---
col1, col2 = st.columns([3, 2], gap="large")

with col1:
    # Clean Form Header
    st.subheader("📝 バナー診断フォーム")

    st.markdown("### 基本情報")
    with st.container():
        user_name = st.text_input("ユーザー名", key="user_name")
        age_group = st.selectbox(
            "ターゲット年代",
            ["指定なし", "10代", "20代", "30代", "40代", "50代", "60代以上"],
            key="age_group"
        )
        platform = st.selectbox("媒体", ["Instagram", "GDN", "YDN"], key="platform")
        category = st.selectbox("カテゴリ", ["広告", "投稿"] if platform == "Instagram" else ["広告"], key="category")
        has_ad_budget = st.selectbox("広告予算", ["あり", "なし"], key="has_ad_budget")
        
        purpose = st.selectbox(
            "目的",
            ["プロフィール誘導", "リンククリック", "保存数増加", "インプレッション増加"],
            key="purpose"
        )

    st.markdown("### 詳細設定")
    with st.container():
        # ★★★ ここから変更 ★★★
        industry = st.selectbox(
            "業種",
            [
                "美容", "飲食", "不動産", "子ども写真館",
                "スクール・習い事", "健康・フィットネス", "ファッション・アパレル",
                "人材・求人", "金融・保険", "エンタメ", "旅行・レジャー",
                "EC・通販", "BtoBサービス", "その他"
            ],
            key="industry"
        )
        # ★★★ ここまで変更 ★★★
        genre = st.selectbox("ジャンル", ["お客様の声", "商品紹介", "ノウハウ", "世界観", "キャンペーン"], key="genre")
        score_format = st.radio("スコア形式", ["A/B/C", "100点満点"], horizontal=True, key="score_format")
        ab_pattern = st.radio("ABテストパターン", ["Aパターン", "Bパターン", "該当なし"], horizontal=True, key="ab_pattern")
        banner_name = st.text_input("バナー名", key="banner_name")

    # --- 追加機能 ---
    add_ctr = False
    check_typos = False
    if user_plan not in ["Free", "Guest"]:
        with st.expander("高度な機能 (Lightプラン以上)"):
            add_ctr = st.checkbox("予想CTRを追加")
            check_typos = st.checkbox("改善コメントの誤字脱字をチェック")

    st.markdown("### 任意項目")
    with st.container():
        result_input = st.text_input("AI評価結果（任意）", help="AIが生成した評価結果を記録したい場合に入力します。", key="result_input")
        follower_gain_input = st.text_input("フォロワー増加数（任意）", help="Instagramなどのフォロワー増加数があれば入力します。", key="follower_gain")
        memo_input = st.text_area("メモ（任意）", help="その他、特記事項があれば入力してください。", key="memo_input")

    # Clean Upload Header
    st.subheader("📸 画像アップロード・AI診断")
    st.markdown("---")

    uploaded_file_a = st.file_uploader("Aパターン画像をアップロード", type=["png", "jpg", "jpeg"], key="a_upload")
    uploaded_file_b = st.file_uploader("Bパターン画像をアップロード", type=["png", "jpg", "jpeg"], key="b_upload")

    # Initialize session state for results
    if 'score_a' not in st.session_state: st.session_state.score_a = None
    if 'comment_a' not in st.session_state: st.session_state.comment_a = None
    if 'yakujihou_a' not in st.session_state: st.session_state.yakujihou_a = None
    if 'score_b' not in st.session_state: st.session_state.score_b = None
    if 'comment_b' not in st.session_state: st.session_state.comment_b = None
    if 'yakujihou_b' not in st.session_state: st.session_state.yakujihou_b = None

    # --- A Pattern Processing ---
    if uploaded_file_a:
        st.markdown("#### 🔷 Aパターン診断")
        
        img_col_a, result_col_a = st.columns([1, 2])

        with img_col_a:
            st.image(Image.open(uploaded_file_a), caption="Aパターン画像", use_container_width=True)
            if st.button("Aパターンを採点", key="score_a_button"):
                if remaining_uses <= 0:
                    st.warning(f"残り回数がありません。（{user_plan}プラン）")
                    st.info("利用回数を増やすには、プランのアップグレードが必要です。")
                else:
                    if auth_utils.update_user_uses_in_firestore(st.session_state["user"]):
                        st.session_state.remaining_uses -= 1 # UI上の残回数を即時更新
                        image_a_bytes = io.BytesIO()
                        Image.open(uploaded_file_a).save(image_a_bytes, format="PNG")
                        image_filename_a = f"banner_A_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                        
                        image_url_a = auth_utils.upload_image_to_firebase_storage(
                            st.session_state["user"], image_a_bytes, image_filename_a
                        )

                        if image_url_a:
                            with st.spinner("AIがAパターンを採点中です..."):
                                try:
                                    ctr_instruction = "また、このバナー広告の予想CTR（クリックスルー率）もパーセンテージで示してください。" if add_ctr else ""
                                    typo_instruction = "生成する改善コメントに誤字脱字がないか厳密にチェックしてください。" if check_typos else ""
                                    
                                    ai_prompt_text = f"""
以下のバナー画像をプロ視点で採点してください。
この広告のターゲット年代は「{age_group}」で、主な目的は「{purpose}」です。

【評価基準】
1. 内容が一瞬で伝わるか
2. コピーの見やすさ
3. 行動喚起
4. 写真とテキストの整合性
5. 情報量のバランス

【ターゲット年代「{age_group}」と目的「{purpose}」を考慮した具体的なフィードバックをお願いします。】
{ctr_instruction}
{typo_instruction}

【出力形式】
---
スコア：{score_format}
改善コメント：2～3行でお願いします
{ "予想CTR：X.X%" if add_ctr else "" }
---"""
                                    if client:
                                        img_str_a = base64.b64encode(image_a_bytes.getvalue()).decode()
                                        response_a = client.chat.completions.create(
                                            model="gpt-4o",
                                            messages=[
                                                {"role": "system", "content": "あなたは広告のプロです。"},
                                                {"role": "user", "content": [
                                                    {"type": "text", "text": ai_prompt_text},
                                                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str_a}"}}
                                                ]}
                                            ],
                                            max_tokens=600
                                        )
                                        content_a = response_a.choices[0].message.content
                                    else:
                                        content_a = "---\nスコア：A+\n改善コメント：プロフェッショナルなデザインで非常に優秀です。\n予想CTR：5.5%\n---"
                                    st.session_state.ai_response_a = content_a

                                    score_match_a = re.search(r"スコア[:：]\s*(.+)", content_a)
                                    comment_match_a = re.search(r"改善コメント[:：]\s*(.+)", content_a, re.DOTALL)
                                    ctr_match_a = re.search(r"予想CTR[:：]\s*(.+)", content_a)
                                    
                                    st.session_state.score_a = score_match_a.group(1).strip() if score_match_a else "取得できず"
                                    st.session_state.comment_a = comment_match_a.group(1).strip() if comment_match_a else "取得できず"
                                    st.session_state.ctr_a = ctr_match_a.group(1).strip() if ctr_match_a else None

                                    if user_plan in ["Pro", "Team", "Enterprise"]:
                                        firestore_record_data = {
                                            "user_name": sanitize(user_name), "banner_name": sanitize(banner_name), "pattern": "A",
                                            "platform": sanitize(platform), "category": sanitize(category), "industry": sanitize(industry),
                                            "age_group": sanitize(age_group), "purpose": sanitize(purpose), "genre": sanitize(genre),
                                            "score": sanitize(st.session_state.score_a), "comment": sanitize(st.session_state.comment_a),
                                            "predicted_ctr": sanitize(st.session_state.ctr_a) if add_ctr else "N/A",
                                            "result": sanitize(result_input), "follower_gain": sanitize(follower_gain_input), "memo": sanitize(memo_input),
                                            "image_url": image_url_a
                                        }
                                        if auth_utils.add_diagnosis_record_to_firestore(st.session_state["user"], firestore_record_data):
                                            st.success("診断結果を実績記録ページに記録しました！")
                                        else:
                                            st.error("診断結果の記録に失敗しました。")

                                except Exception as e:
                                    st.error(f"AI採点中にエラーが発生しました（Aパターン）: {str(e)}")
                                    st.session_state.score_a = "エラー"
                                    st.session_state.comment_a = "AI応答エラー"
                        else:
                            st.error("画像アップロードに失敗したため、採点を行いませんでした。")
                    else:
                        st.error("利用回数の更新に失敗しました。")
                st.rerun() 
        
        with result_col_a:
            if st.session_state.score_a:
                st.markdown("### 🎯 Aパターン診断結果")
                st.metric("総合スコア", st.session_state.score_a)
                if st.session_state.get("ctr_a"):
                    st.metric("予想CTR", st.session_state.ctr_a)
                st.info(f"**改善コメント:** {st.session_state.comment_a}")
                
                if industry in ["美容", "健康・フィットネス"]:
                    st.warning("【薬機法】美容・健康系の広告では、効果効能を保証する表現にご注意ください。")

    # --- B Pattern Processing ---
    if uploaded_file_b:
        st.markdown("---")
        st.markdown("#### 🔷 Bパターン診断")
        
        img_col_b, result_col_b = st.columns([1, 2])

        with img_col_b:
            st.image(Image.open(uploaded_file_b), caption="Bパターン画像", use_container_width=True)
            if st.button("Bパターンを採点", key="score_b_button"):
                if remaining_uses <= 0:
                    st.warning(f"残り回数がありません。（{user_plan}プラン）")
                    st.info("利用回数を増やすには、プランのアップグレードが必要です。")
                else:
                    if auth_utils.update_user_uses_in_firestore(st.session_state["user"]):
                        st.session_state.remaining_uses -= 1
                        image_b_bytes = io.BytesIO()
                        Image.open(uploaded_file_b).save(image_b_bytes, format="PNG")
                        image_filename_b = f"banner_B_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                        
                        image_url_b = auth_utils.upload_image_to_firebase_storage(
                            st.session_state["user"], image_b_bytes, image_filename_b
                        )

                        if image_url_b:
                            with st.spinner("AIがBパターンを採点中です..."):
                                try:
                                    # (Aパターンと同様のAIプロンプトと処理)
                                    # ...
                                    pass # ここにBパターン用の処理を実装
                                except Exception as e:
                                    st.error(f"AI採点中にエラーが発生しました（Bパターン）: {str(e)}")

                        else:
                            st.error("画像アップロードに失敗したため、採点を行いませんでした。")
                    else:
                        st.error("利用回数の更新に失敗しました。")
                st.rerun()

        with result_col_b:
            if st.session_state.score_b:
                st.markdown("### 🎯 Bパターン診断結果")
                # ... (Bパターンの結果表示)
    
with col2:
    st.markdown("### 採点基準はこちら")
    with st.container():
        st.markdown("バナスコAIは以下の観点に基づいて広告画像を評価します。")
        st.markdown(
            """
        - **1. 内容が一瞬で伝わるか**
          - 伝えたいことが最初の1秒でターゲットに伝わるか。
        - **2. コピーの見やすさ**
          - 文字が読みやすいか、サイズや配色が適切か。
        - **3. 行動喚起の明確さ**
          - 『今すぐ予約』『LINE登録』などの行動喚起が明確で、ユーザーを誘導できているか。
        - **4. 写真とテキストの整合性**
          - 背景画像と文字内容が一致し、全体として違和感がないか。
        - **5. 情報量のバランス**
          - 文字が多すぎず、視線誘導が自然で、情報が過負荷にならないか。
        """
        )
