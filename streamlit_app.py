import streamlit as st
import base64
import io
import os
import re
import requests
from PIL import Image
from datetime import datetime
from openai import OpenAI

# 修正済みのauth_utilsをインポート
import auth_utils

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
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, use_container_width=True)
else:
    st.sidebar.warning(f"ロゴ画像 '{logo_path}' が見つかりません。")

# --- Login Check ---
# ログイン済みでない場合、この関数がログインページを表示して処理を停止する
auth_utils.check_login()

# --- OpenAI Client Initialization ---
# ログインチェック後にAPIキーを初期化
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    st.error("❌ OpenAI APIキーが見つかりませんでした。環境変数 'OPENAI_API_KEY' を確認してください。")
    st.stop()
client = OpenAI(api_key=openai_api_key)

# --- Custom CSS ---
st.markdown(
    """
    <style>
    /* Force white background for the entire body */
    body {
        background-color: #FFFFFF !important;
        background-image: none !important; /* Disable any background images */
    }
    /* Streamlit's main content container */
    .main .block-container {
        background-color: #FFFFFF;
        padding-top: 2rem;
        padding-right: 2rem;
        padding-left: 2rem;
        padding-bottom: 2rem;
        border-radius: 12px;
        box-shadow: 0px 8px 20px rgba(0, 0, 0, 0.08);
    }
    /* Sidebar styling */
    .stSidebar {
        background-color: #F8F8F8;
        border-right: none;
        box-shadow: 2px 0px 10px rgba(0, 0, 0, 0.05);
    }
    /* Button styling */
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
    </style>
    """,
    unsafe_allow_html=True
)

# --- アプリケーション本体 ---
st.title("🧠 バナー広告 採点AI - バナスコ")
st.subheader("〜もう、無駄打ちしない。広告を“武器”に変えるAIツール〜")

col1, col2 = st.columns([2, 1])

with col1:
    with st.container(border=True):
        st.subheader("📝 バナー情報入力フォーム")

        with st.expander("👤 基本情報", expanded=True):
            user_name = st.text_input("ユーザー名", key="user_name_input")
            age_group = st.selectbox("ターゲット年代", ["指定なし", "10代", "20代", "30代", "40代", "50代", "60代以上"], key="age_group_select")
            platform = st.selectbox("媒体", ["Instagram", "GDN", "YDN"], key="platform_select")
            category = st.selectbox("カテゴリ", ["広告", "投稿"] if platform == "Instagram" else ["広告"], key="category_select")
            has_ad_budget = st.selectbox("広告予算", ["あり", "なし"], key="budget_budget_select")
            purpose = st.selectbox("目的", ["プロフィール誘導", "リンククリック", "保存数増加", "インプレッション増加"], key="purpose_select")

        with st.expander("🎯 詳細設定", expanded=True):
            industry = st.selectbox("業種", ["美容", "飲食", "不動産", "子ども写真館", "その他"], key="industry_select")
            genre = st.selectbox("ジャンル", ["お客様の声", "商品紹介", "ノウハウ", "世界観", "キャンペーン"], key="genre_select")
            score_format = st.radio("スコア形式", ["A/B/C", "100点満点"], horizontal=True, key="score_format_radio")
            banner_name = st.text_input("バナー名", key="banner_name_input")

        with st.expander("📌 任意項目", expanded=False):
            result_input = st.text_input("AI評価結果（任意）", help="AIが生成した評価結果を記録したい場合に入力します。", key="result_input_text")
            follower_gain_input = st.text_input("フォロワー増加数（任意）", help="Instagramなどのフォロワー増加数があれば入力します。", key="follower_gain_input_text")
            memo_input = st.text_area("メモ（任意）", help="その他、特記事項があれば入力してください。", key="memo_input_area")

        st.markdown("---")
        st.subheader("🖼️ バナー画像アップロードと診断")

        uploaded_file_a = st.file_uploader("Aパターン画像をアップロード", type=["png", "jpg", "jpeg"], key="a_upload")
        uploaded_file_b = st.file_uploader("Bパターン画像をアップロード", type=["png", "jpg", "jpeg"], key="b_upload")

        # Initialize session state for results
        for key in ['score_a', 'comment_a', 'yakujihou_a', 'score_b', 'comment_b', 'yakujihou_b', 'ai_response_a', 'ai_response_b']:
            if key not in st.session_state:
                st.session_state[key] = None

        def run_ai_diagnosis(pattern_char, uploaded_file):
            """AI診断を実行し、結果を返す共通関数"""
            if st.session_state.remaining_uses <= 0:
                st.warning(f"残り回数がありません。（{st.session_state.plan}プラン）")
                return None, None

            # 利用回数を減らす
            if not auth_utils.update_user_uses_in_firestore(st.session_state["user"]):
                st.error("利用回数の更新に失敗しました。")
                return None, None

            with st.spinner(f"AIが{pattern_char}パターンを採点中です..."):
                try:
                    image_bytes = uploaded_file.getvalue()
                    image_url = auth_utils.upload_image_to_firebase_storage(
                        st.session_state["user"],
                        io.BytesIO(image_bytes),
                        f"banner_{pattern_char}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                    )

                    if not image_url:
                        st.error("画像アップロードに失敗しました。")
                        return None, None

                    ai_prompt_text = f"""以下のバナー画像をプロ視点で採点してください。この広告のターゲット年代は「{age_group}」で、主な目的は「{purpose}」です。【評価基準】1. 内容が一瞬で伝わるか 2. コピーの見やすさ 3. 行動喚起 4. 写真とテキストの整合性 5. 情報量のバランス【出力形式】---スコア：{score_format}改善コメント：2～3行でお願いします---"""
                    img_str = base64.b64encode(image_bytes).decode()
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "あなたは広告のプロです。"},
                            {"role": "user", "content": [
                                {"type": "text", "text": ai_prompt_text},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}}
                            ]}
                        ],
                        max_tokens=600
                    )
                    content = response.choices[0].message.content
                    score_match = re.search(r"スコア[:：]\s*(.+)", content)
                    comment_match = re.search(r"改善コメント[:：]\s*(.+)", content, re.DOTALL)
                    
                    score = score_match.group(1).strip() if score_match else "取得できず"
                    comment = comment_match.group(1).strip() if comment_match else "取得できず"

                    # Firestoreに記録
                    firestore_record_data = {
                        "pattern": pattern_char, "platform": sanitize(platform), "category": sanitize(category), "industry": sanitize(industry),
                        "age_group": sanitize(age_group), "purpose": sanitize(purpose), "score": sanitize(score),
                        "comment": sanitize(comment), "image_url": image_url,
                        "result": sanitize(result_input), "follower_gain": sanitize(follower_gain_input), "memo": sanitize(memo_input)
                    }
                    if auth_utils.add_diagnosis_record_to_firestore(st.session_state["user"], firestore_record_data):
                        st.success("📊 診断結果を記録しました！")
                    else:
                        st.error("❌ 診断結果の記録に失敗しました。")
                    
                    return score, comment

                except Exception as e:
                    st.error(f"AI採点中にエラーが発生しました: {e}")
                    return "エラー", "AI応答エラー"

        # --- A Pattern Processing ---
        if uploaded_file_a:
            img_col_a, result_col_a = st.columns([1, 2])
            with img_col_a:
                st.image(uploaded_file_a, caption="Aパターン画像", use_container_width=True)
                if st.button("🚀 Aパターンを採点", key="score_a_btn"):
                    score, comment = run_ai_diagnosis("A", uploaded_file_a)
                    if score and comment:
                        st.session_state.score_a = score
                        st.session_state.comment_a = comment
            
            with result_col_a:
                if st.session_state.score_a:
                    st.markdown("### ✨ Aパターン診断結果")
                    st.metric("総合スコア", st.session_state.score_a)
                    st.info(f"**改善コメント:** {st.session_state.comment_a}")

        st.markdown("---")

        # --- B Pattern Processing ---
        if uploaded_file_b:
            img_col_b, result_col_b = st.columns([1, 2])
            with img_col_b:
                st.image(uploaded_file_b, caption="Bパターン画像", use_container_width=True)
                if st.button("🚀 Bパターンを採点", key="score_b_btn"):
                    if st.session_state.plan == "Free":
                        st.warning("この機能はFreeプランではご利用いただけません。")
                    else:
                        score, comment = run_ai_diagnosis("B", uploaded_file_b)
                        if score and comment:
                            st.session_state.score_b = score
                            st.session_state.comment_b = comment

            with result_col_b:
                if st.session_state.score_b:
                    st.markdown("### ✨ Bパターン診断結果")
                    st.metric("総合スコア", st.session_state.score_b)
                    st.info(f"**改善コメント:** {st.session_state.comment_b}")

with col2:
    with st.expander("📌 採点基準はこちら", expanded=True):
        st.markdown("""
        - **1. 内容が一瞬で伝わるか**
        - **2. コピーの見やすさ**
        - **3. 行動喚起の明確さ**
        - **4. 写真とテキストの整合性**
        - **5. 情報量のバランス**
        """)
    st.info("💡 **ヒント:** スコアやコメントは、広告改善のヒントとしてご活用ください。")

# (薬機法チェックとA/Bテスト比較のロジックは変更ないため省略)
# この部分は必要に応じて、A/Bパターンの診断結果が出た後に表示するロジックを追加してください。
