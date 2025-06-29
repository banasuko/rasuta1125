import streamlit as st
import base64
import io
import os
import re
import requests
from PIL import Image
from datetime import datetime
from openai import OpenAI

# --- ロゴの表示 ---
# ロゴ画像のパス
logo_path = "banasuko_logo_icon.png"

# 画像ファイルを読み込み、サイドバーに表示
try:
    logo_image = Image.open(logo_path)
    st.sidebar.image(logo_image, use_container_width=True) # サイドバーの幅に合わせて表示
except FileNotFoundError:
    st.sidebar.error(f"ロゴ画像 '{logo_path}' が見つかりません。ファイルが正しく配置されているか確認してください。")


# OpenAI APIキーの読み込み
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    st.error("❌ OpenAI APIキーが見つかりませんでした。`.env` を確認してください。")
    st.stop()
client = OpenAI(api_key=openai_api_key)

# GASとGoogle Driveの情報
GAS_URL = "https://script.google.com/macros/s/AKfycbxUy3JI5xwncRHxv-WoHHNqiF7LLndhHTOzmLOHtNRJ2hNCo8PJi7-0fdbDjnfAGMlL/exec"

# Helper function to sanitize values
def sanitize(value):
    """Replaces None or specific strings with 'エラー' (Error)"""
    if value is None or value == "取得できず":
        return "エラー"
    return value

# Google Drive upload functionality is removed in this version

# Streamlit UI configuration
st.set_page_config(layout="wide", page_title="バナスコAI")

# --- カスタムCSSの追加 (背景色を完全に白に固定) ---
st.markdown(
    """
    <style>
    /* 全体の背景色を強制的に白に設定 */
    body {
        background-color: #FFFFFF !important;
        background-image: none !important; /* 念のため、背景画像も無効化 */
    }

    /* Streamlitのメインコンテナ */
    .main .block-container {
        background-color: #FFFFFF; /* メインコンテナの背景も白 */
        padding-top: 2rem;
        padding-right: 2rem;
        padding-left: 2rem;
        padding-bottom: 2rem;
        border-radius: 12px;
        box-shadow: 0px 8px 20px rgba(0, 0, 0, 0.08);
    }

    /* サイドバー */
    .stSidebar {
        background-color: #F8F8F8; /* 少し明るいグレー */
        border-right: none;
        box-shadow: 2px 0px 10px rgba(0, 0, 0, 0.05);
    }

    /* ボタン */
    .stButton > button {
        background-color: #0000FF;
        color: white;
        border-radius: 8px;
        border: none;
        box-shadow: 0px 4px 10px rgba(0, 0, 255, 0.2);
        transition: background-color 0.2s, box-shadow 0.2s;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #3333FF;
        box-shadow: 0px 6px 15px rgba(0, 0, 255, 0.3);
    }
    .stButton > button:active {
        background-color: #0000CC;
        box-shadow: none;
    }

    /* Expander */
    .stExpander {
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        background-color: #FFFFFF;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
    }
    .stExpander > div > div {
        background-color: #F8F8F8;
        border-bottom: 1px solid #E0E0E0;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }
    .stExpanderDetails {
        background-color: #FFFFFF;
    }

    /* テキスト入力、セレクトボックスなど */
    div,
    input,
    textarea,
    select {
        background-color: #FFFFFF !important;
        color: #333333 !important;
        border-radius: 8px;
        border: 1px solid #E0E0E0;
        box-shadow: inset 0px 1px 3px rgba(0,0,0,0.05);
    }
    div:focus-within,
    input:focus,
    textarea:focus,
    select:focus {
        border-color: #0000FF;
        box-shadow: 0 0 0 2px rgba(0, 0, 255, 0.3);
    }
    .st-eb { /* セレクトボックスの内部要素にも適用 */
        background-color: #FFFFFF !important;
        color: #333333 !important;
    }

    /* メトリック */
    /* Info, Success, Warning, Errorボックス */
    .stAlert {
        color: #333333;
    }
    .stAlert.stAlert-info {
        background-color: #E0EFFF;
        border-left-color: #0000FF;
    }
    .stAlert.stAlert-success {
        background-color: #E0FFE0;
        border-left-color: #00AA00;
    }
    .stAlert.stAlert-warning {
        background-color: #FFFBE0;
        border-left-color: #FFD700;
    }
    .stAlert.stAlert-error {
        background-color: #FFE0E0;
        border-left-color: #FF0000;
    }

    /* コードブロック */
    code {
        background-color: #F0F0F0 !important;
        color: #000080 !important;
    }
    pre code {
        background-color: #F0F0F0 !important;
    }

    /* サイドバーのテキスト色 */
    .stSidebar [data-testid="stText"],
    .stSidebar [data-testid="stMarkdownContainer"],
    .stSidebar .st-emotion-cache-1jm692h {
        color: #333333;
    }

    </style>
    """,
    unsafe_allow_html=True
)
# --- カスタムCSSの終わり ---

st.title("🧠 バナー広告 採点AI - バナスコ")
st.subheader("〜もう、無駄打ちしない。広告を“武器”に変えるAIツール〜")

col1, col2 = st.columns([2, 1])

with col1:
    with st.container(border=True):
        st.subheader("📝 バナー情報入力フォーム")

        with st.expander("👤 基本情報", expanded=True):
            user_name = st.text_input("ユーザー名", key="user_name_input")
            age_group = st.selectbox(
                "ターゲット年代",
                ["指定なし", "10代", "20代", "30代", "40代", "50代", "60代以上"],
                key="age_group_select"
            )
            platform = st.selectbox("媒体", ["Instagram", "GDN", "YDN"], key="platform_select")
            category = st.selectbox("カテゴリ", ["広告", "投稿"] if platform == "Instagram" else ["広告"], key="category_select")
            has_ad_budget = st.selectbox("広告予算", ["あり", "なし"], key="budget_select")
            purpose = st.selectbox(
                "目的",
                ["プロフィール誘導", "リンククリック", "保存数増加", "インプレッション増加"],
                key="purpose_select"
            )

        with st.expander("🎯 詳細設定", expanded=True):
            industry = st.selectbox("業種", ["美容", "飲食", "不動産", "子ども写真館", "その他"], key="industry_select")
            genre = st.selectbox("ジャンル", ["お客様の声", "商品紹介", "ノウハウ", "世界観", "キャンペーン"], key="genre_select")
            score_format = st.radio("スコア形式", ["A/B/C", "100点満点"], horizontal=True, key="score_format_radio")
            ab_pattern = st.radio("ABテストパターン", ["Aパターン", "Bパターン", "該当なし"], horizontal=True, key="ab_pattern_radio")
            banner_name = st.text_input("バナー名", key="banner_name_input")

        with st.expander("📌 任意項目", expanded=False):
            result_input = st.text_input("AI評価結果（任意）", help="AIが生成した評価結果を記録したい場合に入力します。", key="result_input_text")
            follower_gain_input = st.text_input("フォロワー増加数（任意）", help="Instagramなどのフォロワー増加数があれば入力します。", key="follower_gain_input_text")
            memo_input = st.text-area("メモ（任意）", help="その他、特記事項があれば入力してください。", key="memo_input_area")

        st.markdown("---")
        st.subheader("🖼️ バナー画像アップロードと診断")

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
            img_col_a, result_col_a = st.columns([1, 2])

            with img_col_a:
                st.image(Image.open(uploaded_file_a), caption="Aパターン画像", use_container_width=True)
                if st.button("🚀 Aパターンを採点", key="score_a_btn"):
                    image_a = Image.open(uploaded_file_a)
                    buf_a = io.BytesIO()
                    image_a.save(buf_a, format="PNG")
                    img_str_a = base64.b64encode(buf_a.getvalue()).decode()

                    with st.spinner("AIがAパターンを採点中です..."):
                        try:
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

【出力形式】
---
スコア：{score_format}
改善コメント：2～3行でお願いします
---"""
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
                            content_a = response_a.choices
