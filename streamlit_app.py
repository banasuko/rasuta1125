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

st.title("バナー広告をAIで診断！")
st.subheader("診断したいバナーの情報を入力してください")

# Streamlitのセッションステートからユーザー情報を取得
user_email = st.session_state.email
user_uid = st.session_state.user
user_plan = st.session_state.plan
remaining_uses = st.session_state.remaining_uses

# --- 診断機能 ---
st.markdown("---")
uploaded_file = st.file_uploader("診断したいバナー画像をアップロードしてください", type=["jpg", "png"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="アップロードされたバナー", use_column_width=True)

    # Convert uploaded file to bytes for OpenAI Vision API and Firebase Storage
    image_bytes = uploaded_file.getvalue()
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    image_mime_type = uploaded_file.type

    # Store image in session state for later use
    st.session_state.uploaded_image_bytes = image_bytes
    st.session_state.uploaded_image_filename = uploaded_file.name
    st.session_state.image_mime_type = image_mime_type

    with st.form("diagnosis_form"):
        st.subheader("バナーの情報を入力")
        banner_name = st.text_input("バナーの名前（例：初回限定キャンペーンバナー）", value=st.session_state.get('banner_name', ''))
        platform = st.selectbox("掲載媒体", ["Google広告", "Yahoo!広告", "Facebook広告", "Instagram広告", "TikTok広告", "その他"], index=0 if "Google広告" else None)
        category = st.selectbox("業種カテゴリ", ["美容室", "脱毛サロン", "エステ", "ネイル・まつげ", "ホワイトニング", "整体・接骨院", "学習塾", "子ども写真館", "飲食店", "その他"])
        target_audience = st.text_input("ターゲット層（例：30代女性、ビジネスマン、子育て中のママなど）", value=st.session_state.get('target_audience', ''))
        product_features = st.text_area("商品・サービスの特徴やメリット（箇条書きOK）", value=st.session_state.get('product_features', ''))
        ad_goal = st.selectbox("広告の目的", ["認知拡大", "資料請求", "来店促進", "会員登録", "商品購入", "ブランディング", "その他"])

        # Lightプラン以上で利用可能な追加オプション
        add_ctr = False
        check_typos = False
        if user_plan in ["Light", "Pro", "Team", "Enterprise"]:
            st.markdown("---")
            st.markdown("### ⚙️ 高度な機能 (Lightプラン以上)")
            col_opt1, col_opt2 = st.columns(2)
            with col_opt1:
                add_ctr = st.checkbox("予想CTRを追加", help="AIがバナーの予想クリック率を算出します。")
            with col_opt2:
                check_typos = st.checkbox("改善コメントの誤字脱字をチェック", help="AIが生成する改善コメントの質が向上します。")
        else:
            st.markdown("---")
            st.markdown("### ⚙️ 高度な機能 (Lightプラン以上)")
            st.info("「予想CTR」や「改善コメントの誤字脱字チェック」はLightプラン以上でご利用いただけます。")


        submitted = st.form_submit_button("🚀 バナーをAI診断！")

        if submitted:
            if client is None:
                st.error("OpenAI APIキーが設定されていないため、診断を実行できません。")
                st.stop()
            
            # --- 実行回数チェック ---
            if remaining_uses <= 0:
                st.warning(f"今月の利用回数を使い切りました。（現在プラン：{user_plan}）")
                st.info("利用回数は毎月1日にリセットされます。または、プランのアップグレードをご検討ください。")
                st.stop()

            if not all([banner_name, platform, category, target_audience, product_features, ad_goal]):
                st.error("全ての項目を入力してください。")
                st.stop()

            with st.spinner("AIがバナーを診断中..."):
                try:
                    # プロンプトの生成
                    prompt_parts = [
                        "あなたは優秀な広告コンサルタントです。",
                        "以下に示すバナー画像と詳細情報をもとに、バナー広告の改善点を的確に指摘してください。",
                        "出力はMarkdown形式で、読みやすいようにセクション分けしてください。",
                        "各評価項目には点数をつけ、その根拠と具体的な改善提案を詳細に記述してください。",
                        "ユーザーは広告運用の専門家ではないため、専門用語は避け、分かりやすい言葉で説明してください。",
                        "出力は以下の項目を必ず含めてください。",
                        "---",
                        "## 評価サマリー",
                        "総合スコア（100点満点）：",
                        "## 各評価項目と改善提案",
                        "### 1. 視認性・可読性 (20点満点)",
                        "- **評価点**：",
                        "- **根拠と改善提案**：",
                        "### 2. 訴求力・メッセージ性 (20点満点)",
                        "- **評価点**：",
                        "- **根拠と改善提案**：",
                        "### 3. デザイン・クリエイティブ (20点満点)",
                        "- **評価点**：",
                        "- **根拠と改善提案**：",
                        "### 4. ターゲット適合性 (20点満点)",
                        "- **評価点**：",
                        "- **根拠と改善提案**：",
                        "### 5. CTA（Call To Action）の明確さ (20点満点)",
                        "- **評価点**：",
                        "- **根拠と改善提案**：",
                        "---",
                        "## 総合的な改善アドバイス",
                        "- ",
                        "- ",
                        "---",
                        "【バナー詳細情報】",
                        f"バナーの名前: {banner_name}",
                        f"掲載媒体: {platform}",
                        f"業種カテゴリ: {category}",
                        f"ターゲット層: {target_audience}",
                        f"商品・サービスの特徴やメリット: {product_features}",
                        f"広告の目的: {ad_goal}"
                    ]

                    if add_ctr:
                        prompt_parts.insert(1, "さらに、このバナーの予想クリック率（CTR）を小数点以下2桁までパーセンテージで予測してください。")
                        prompt_parts.append("## 予想CTR")
                        prompt_parts.append("- 予想CTR: X.XX%")

                    if check_typos:
                        prompt_parts.insert(1, "提供する改善コメントには誤字脱字がないか、完璧に校正してください。")

                    prompt = "\n".join(prompt_parts)

                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:{image_mime_type};base64,{base64_image}"
                                        },
                                    },
                                ],
                            }
                        ],
                        max_tokens=1500,
                        temperature=0.7,
                    )
                    
                    diagnosis_result = response.choices[0].message.content

                    # --- 実行回数を1回減らす ---
                    if auth_utils.update_user_uses_in_firestore(user_uid):
                        st.session_state.remaining_uses -= 1 # UI上の表示も更新
                    else:
                        st.error("利用回数の更新に失敗しました。")
                        # 失敗しても結果は表示するが、ユーザーには通知

                    # --- 診断結果の表示 ---
                    st.subheader("診断結果")
                    st.markdown(diagnosis_result)

                    # --- 結果からスコアとCTRを抽出 ---
                    overall_score = 0
                    predicted_ctr = None
                    match_score = re.search(r"総合スコア（100点満点）：\s*(\d+)", diagnosis_result)
                    if match_score:
                        overall_score = int(match_score.group(1))
                    
                    if add_ctr:
                        match_ctr = re.search(r"予想CTR:\s*(\d+\.\d+)%", diagnosis_result)
                        if match_ctr:
                            predicted_ctr = float(match_ctr.group(1))

                    # --- 画像をFirebase Storageにアップロード ---
                    image_url = None
                    if st.session_state.uploaded_image_bytes:
                        # ファイル名に日付と時刻を追加してユニークにする
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        unique_filename = f"{timestamp}_{st.session_state.uploaded_image_filename}"
                        
                        image_bytes_io = io.BytesIO(st.session_state.uploaded_image_bytes)
                        image_url = auth_utils.upload_image_to_firebase_storage(
                            user_uid,
                            image_bytes_io,
                            unique_filename
                        )
                        if image_url:
                            st.success("バナー画像を保存しました！")
                        else:
                            st.error("バナー画像の保存に失敗しました。")


                    # --- 診断結果をFirestoreに保存 ---
                    record_data = {
                        "user_name": user_email,
                        "banner_name": banner_name,
                        "platform": platform,
                        "category": category,
                        "target_audience": target_audience,
                        "product_features": product_features,
                        "ad_goal": ad_goal,
                        "score": overall_score,
                        "predicted_ctr": predicted_ctr, # Noneの場合もある
                        "diagnosis_result": diagnosis_result,
                        "image_url": image_url # 画像URLを追加
                    }
                    if auth_utils.add_diagnosis_record_to_firestore(user_uid, record_data):
                        st.success("診断結果を実績記録ページに保存しました！")
                    else:
                        st.error("診断結果の保存に失敗しました。")


                    # --- GAS連携（既存の連携があればそのまま） ---
                    payload = {
                        "timestamp": datetime.now().isoformat(),
                        "user_id": sanitize(user_uid),
                        "email": sanitize(user_email),
                        "plan": sanitize(user_plan),
                        "banner_name": sanitize(banner_name),
                        "platform": sanitize(platform),
                        "category": sanitize(category),
                        "target_audience": sanitize(target_audience),
                        "product_features": sanitize(product_features),
                        "ad_goal": sanitize(ad_goal),
                        "score": sanitize(overall_score),
                        "predicted_ctr": sanitize(predicted_ctr),
                        "image_url": sanitize(image_url),
                        "diagnosis_result": diagnosis_result # 診断結果全文
                    }

                    try:
                        res = requests.post(GAS_URL, data=json.dumps(payload))
                        res.raise_for_status() # HTTPエラーがあれば例外を発生させる
                        # st.success("診断結果をスプレッドシートに記録しました！")
                    except requests.exceptions.RequestException as e:
                        st.warning(f"スプレッドシートへの記録に失敗しました: {e}")
                        st.warning("スプレッドシートへの連携が不要であれば無視してください。")


                except OpenAI.APIStatusError as e:
                    if e.status_code == 429:
                        st.error("APIのレート制限に達しました。しばらく待ってから再度お試しください。")
                    else:
                        st.error(f"OpenAI APIエラーが発生しました: {e.status_code} - {e.response}")
                except Exception as e:
                    st.error(f"診断中に予期せぬエラーが発生しました: {e}")

# --- A/Bテスト比較機能 (既存のまま) ---
st.markdown("---")
st.header("✨ A/Bテスト比較")
st.subheader("2つのバナー広告を比較し、より効果的な方を見つけます。")

colA, colB = st.columns(2)

with colA:
    st.subheader("バナーA")
    uploaded_file_a = st.file_uploader("バナーAをアップロード", type=["jpg", "png"], key="uploader_a")
    name_a = st.text_input("バナーAの名前", key="name_a")
    if uploaded_file_a:
        st.image(uploaded_file_a, caption="バナーA", use_column_width=True)

with colB:
    st.subheader("バナーB")
    uploaded_file_b = st.file_uploader("バナーBをアップロード", type=["jpg", "png"], key="uploader_b")
    name_b = st.text_input("バナーBの名前", key="name_b")
    if uploaded_file_b:
        st.image(uploaded_file_b, caption="バナーB", use_column_width=True)

compare_button = st.button("📈 比較診断！", key="compare_button")

if compare_button:
    if client is None:
        st.error("OpenAI APIキーが設定されていないため、比較診断を実行できません。")
        st.stop()
    
    # --- 実行回数チェック ---
    if remaining_uses <= 0:
        st.warning(f"今月の利用回数を使い切りました。（現在プラン：{user_plan}）")
        st.info("利用回数は毎月1日にリセットされます。または、プランのアップグレードをご検討ください。")
        st.stop()

    if not (uploaded_file_a and uploaded_file_b and name_a and name_b):
        st.error("両方のバナー画像と名前を入力してください。")
        st.stop()
    
    # 画像をBase64にエンコード
    image_a_bytes = uploaded_file_a.getvalue()
    base64_image_a = base64.b64encode(image_a_bytes).decode('utf-8')
    image_a_mime_type = uploaded_file_a.type

    image_b_bytes = uploaded_file_b.getvalue()
    base64_image_b = base64.b64encode(image_b_bytes).decode('utf-8')
    image_b_mime_type = uploaded_file_b.type

    with st.spinner("AIがバナーを比較診断中..."):
        try:
            comparison_prompt = f"""
            あなたは優秀な広告コンサルタントです。
            2つのバナー画像（{name_a}と{name_b}）を比較し、どちらがより優れているか、
            そしてそれぞれのバナーの長所と短所、具体的な改善点を詳細に分析してください。
            広告効果を高めるための実践的なアドバイスを含めてください。
            出力はMarkdown形式で、比較表を含め、明確な結論と根拠を示してください。

            比較する項目例：
            - 視認性・可読性
            - 訴求力・メッセージ性
            - デザイン・クリエイティブ
            - ターゲット適合性
            - CTAの明確さ

            最終的な結論として、どちらのバナーが推奨されるかを明記してください。
            """

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": comparison_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{image_a_mime_type};base64,{base64_image_a}"
                                },
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{image_b_mime_type};base64,{base64_image_b}"
                                },
                            },
                        ],
                    }
                ],
                max_tokens=2000,
                temperature=0.7,
            )
            comparison_result = response.choices[0].message.content

            # --- 実行回数を1回減らす ---
            if auth_utils.update_user_uses_in_firestore(user_uid):
                st.session_state.remaining_uses -= 1 # UI上の表示も更新
            else:
                st.error("利用回数の更新に失敗しました。")


            st.subheader("比較診断結果")
            st.markdown(comparison_result)

        except OpenAI.APIStatusError as e:
            if e.status_code == 429:
                st.error("APIのレート制限に達しました。しばらく待ってから再度お試しください。")
            else:
                st.error(f"OpenAI APIエラーが発生しました: {e.status_code} - {e.response}")
        except Exception as e:
            st.error(f"比較診断中に予期せぬエラーが発生しました: {e}")
