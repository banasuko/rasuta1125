# auth_utils.py
import os
import firebase_admin
from firebase_admin import credentials, firestore, storage, auth

# --- Firebase Admin SDK Initialization ---
# 環境変数からサービスアカウント情報を取得し、改行エスケープを復元します。
admin_project_id = os.getenv("FIREBASE_PROJECT_ID_ADMIN")
private_key = os.getenv("FIREBASE_PRIVATE_KEY_ADMIN")
private_key_id = os.getenv("FIREBASE_PRIVATE_KEY_ID_ADMIN")
client_email = os.getenv("FIREBASE_CLIENT_EMAIL_ADMIN")
client_id = os.getenv("FIREBASE_CLIENT_ID_ADMIN")

# 環境変数内の"\n"を実際の改行に置き換え
if private_key:
    private_key = private_key.replace("\\n", "\n")

# サービスアカウント情報を辞書で定義
service_account_info = {
    "type": "service_account",
    "project_id": admin_project_id,
    "private_key_id": private_key_id,
    "private_key": private_key,
    "client_email": client_email,
    "client_id": client_id
}

# 認証情報を用いて Firebase Admin SDK を初期化
cred = credentials.Certificate(service_account_info)
firebase_admin.initialize_app(cred, {
    'projectId': admin_project_id,
    # 'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET")  # 必要に応じて設定
})

# Firestore と Storage クライアントを用意
db = firestore.client()
bucket = storage.bucket()

# --- 認証・ログイン関連ユーティリティ ---
def check_login():
    """
    Streamlit でのログインチェックを行います。
    セッションに user および id_token の存在を確認し、なければストップします。
    """
    import streamlit as st
    if "user" not in st.session_state or "id_token" not in st.session_state:
        st.error("ログインが必要です。再度ログインしてください。")
        st.stop()

# --- Firestore 更新 / 登録ユーティリティ ---
def update_user_uses_in_firestore_rest(user, id_token):
    """
    Firestore のユーザー利用回数を REST 経由でデクリメントします。
    成功時 True, 失敗時 False を返します。
    """
    # ... 既存の実装をここにコピー
    pass

def add_diagnosis_record_to_firestore(user, id_token, record_data):
    """
    AI 診断結果を Firestore に記録します。
    成功時 True, 失敗時 False を返します。
    """
    # ... 既存の実装をここにコピー
    pass

# --- Firebase Storage アップロードユーティリティ ---
def upload_image_to_firebase_storage(user, image_bytes_io, filename):
    """
    画像 (BytesIO) を Firebase Storage にアップロードし、ダウンロード可能な URL を返します。
    アップロード失敗時は None を返します。
    """
    try:
        blob = bucket.blob(f"banners/{user['uid']}/{filename}")
        blob.upload_from_file(image_bytes_io, content_type='image/png')
        blob.make_public()
        return blob.public_url
    except Exception as e:
        print(f"[auth_utils] upload error: {e}")
        return None

# ---------------------------------------------------------


# streamlit_app.py
import streamlit as st
import base64
import io
import os
import re
from PIL import Image
from datetime import datetime
from openai import OpenAI

import auth_utils  # auth_utils.py をインポート

# Google Apps Script (GAS) and Google Drive information
GAS_URL = "https://script.google.com/macros/s/AKfycby_uD6Jtb9GT0-atbyPKOPc8uyVKodwYVIQ2Tpe-_E8uTOPiir0Ce1NAPZDEOlCUxN4/exec"

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
    st.sidebar.image(logo_image, use_container_width=True)
except FileNotFoundError:
    st.sidebar.error(f"ロゴ画像 '{logo_path}' が見つかりません。配置を確認してください。")

# --- Login Check ---
auth_utils.check_login()

# --- OpenAI Client Initialization ---
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    st.error("❌ OpenAI APIキーが見つかりませんでした。`.env` を確認してください。")
    st.stop()
client = OpenAI(api_key=openai_api_key)

# --- Custom CSS (White background + theme) ---
st.markdown(
    """
    <style>
    /* Force white background */
    body { background-color: #FFFFFF !important; }
    .main .block-container { background-color: #FFFFFF; padding: 2rem; border-radius: 12px; box-shadow: 0 8px 20px rgba(0,0,0,0.08); }
    .stSidebar { background-color: #F8F8F8; box-shadow: 2px 0 10px rgba(0,0,0,0.05); }
    .stButton > button { background-color: #0000FF; color: white; border-radius:8px; font-weight:bold; }
    .stButton > button:hover { background-color: #3333FF; }
    .stExpander { border:1px solid #E0E0E0; border-radius:8px; }
    div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea { border-radius:8px; }
    [data-testid="stMetricValue"] { color:#FFD700; font-size:2.5rem; font-weight:bold; }
    .stAlert-info { background-color:#E0EFFF; border-left-color:#0000FF; }
    .stAlert-success { background-color:#E0FFE0; border-left-color:#00AA00; }
    .stAlert-warning { background-color:#FFFBE0; border-left-color:#FFD700; }
    .stAlert-error { background-color:#FFE0E0; border-left-color:#FF0000; }
    code { background-color:#F0F0F0; color:#000080; border-radius:5px; padding:0.2em; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Main Application ---
st.title("🧠 バナー広告 採点AI - バナスコ")
st.subheader("〜もう、無駄打ちしない。広告を“武器”に変えるAIツール〜")

col1, col2 = st.columns([2,1])

with col1:
    with st.container():
        st.subheader("📝 バナー情報入力フォーム")
        with st.expander("👤 基本情報", expanded=True):
            user_name = st.text_input("ユーザー名")
            age_group = st.selectbox("ターゲット年代", ["指定なし","10代","20代","30代","40代","50代","60代以上"])
            platform = st.selectbox("媒体",["Instagram","GDN","YDN"])
            category = st.selectbox("カテゴリ", ["広告","投稿"] if platform=="Instagram" else ["広告"] )
            has_ad_budget = st.selectbox("広告予算", ["あり","なし"])
            purpose = st.selectbox("目的", ["プロフィール誘導","リンククリック","保存数増加","インプレッション増加"])
        with st.expander("🎯 詳細設定", expanded=True):
            industry = st.selectbox("業種", ["美容","飲食","不動産","子ども写真館","その他"])
            genre = st.selectbox("ジャンル", ["お客様の声","商品紹介","ノウハウ","世界観","キャンペーン"] )
            score_format = st.radio("スコア形式", ["A/B/C","100点満点"], horizontal=True)
            ab_pattern = st.radio("ABテストパターン", ["Aパターン","Bパターン","該当なし"], horizontal=True)
            banner_name = st.text_input("バナー名")
        with st.expander("📌 任意項目", expanded=False):
            result_input = st.text_input("AI評価結果（任意）")
            follower_gain_input = st.text_input("フォロワー増加数（任意）")
            memo_input = st.text_area("メモ（任意）")

        st.markdown("---")
        st.subheader("🖼️ バナー画像アップロードと診断")
        uploaded_file_a = st.file_uploader("Aパターン画像をアップロード", type=["png","jpg","jpeg"], key="a_upload")
        uploaded_file_b = st.file_uploader("Bパターン画像をアップロード", type=["png","jpg","jpeg"], key="b_upload")

        # セッションステート初期化
        for key in ["score_a","comment_a","yakujihou_a","score_b","comment_b","yakujihou_b"]:
            if key not in st.session_state:
                st.session_state[key] = None

        # --- A Pattern ---
        if uploaded_file_a:
            img_col_a, result_col_a = st.columns([1,2])
            with img_col_a:
                st.image(Image.open(uploaded_file_a), caption="Aパターン画像", use_container_width=True)
                if st.button("🚀 Aパターンを採点", key="score_a_btn"):
                    if st.session_state.remaining_uses <=0:
                        st.warning(f"残り回数がありません。（{st.session_state.plan}プラン）")
                        st.info("プランのアップグレードをご検討ください。")
                    else:
                        if auth_utils.update_user_uses_in_firestore_rest(st.session_state["user"], st.session_state["id_token"]):
                            image_a_bytes = io.BytesIO()
                            Image.open(uploaded_file_a).save(image_a_bytes, format="PNG")
                            img_str_a = base64.b64encode(image_a_bytes.getvalue()).decode()

                            image_url_a = auth_utils.upload_image_to_firebase_storage(
                                st.session_state["user"], image_a_bytes,
                                f"banner_A_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                            )
                            if image_url_a:
                                with st.spinner("AIがAパターンを採点中です..."):
                                    try:
                                        ai_prompt_text = f"""
以下のバナー画像をプロ視点で採点してください。
年齢: {age_group}, 目的: {purpose}
【評価基準】1.伝わりやすさ 2.コピー見やすさ 3.行動喚起 4.整合性 5.バランス
"""
                                        response_a = client.chat.completions.create(
                                            model="gpt-4o",
                                            messages=[
                                                {"role":"system","content":"あなたは広告のプロです。"},
                                                {"role":"user","content":[{"type":"text","text":ai_prompt_text},
                                                   {"type":"image_url","image_url":{"url":f"data:image/png;base64,{img_str_a}"}}]}
                                            ], max_tokens=600
                                        )
                                        content_a = response_a.choices[0].message.content
                                        st.session_state.score_a = re.search(r"スコア[:：]\s*(.+)", content_a).group(1).strip() if re.search(r"スコア[:：]\s*(.+)", content_a) else "取得できず"
                                        st.session_state.comment_a = re.search(r"改善コメント[:：]\s*(.+)", content_a).group(1).strip() if re.search(r"改善コメント[:：]\s*(.+)", content_a) else "取得できず"

                                        record = {"timestamp":datetime.now().isoformat()+"Z",
                                                  "platform":sanitize(platform),"category":sanitize(category),
                                                  "industry":sanitize(industry),"age_group":sanitize(age_group),
                                                  "purpose":sanitize(purpose),"score":sanitize(st.session_state.score_a),
                                                  "comment":sanitize(st.session_state.comment_a),
                                                  "result":sanitize(result_input),
                                                  "follower_gain":sanitize(follower_gain_input),
                                                  "memo":sanitize(memo_input),
                                                  "image_url":image_url_a}
                                        if auth_utils.add_diagnosis_record_to_firestore(st.session_state["user"], st.session_state["id_token"], record):
                                            st.success("📊 診断結果をFirestoreに記録しました！")
                                        else:
                                            st.error("❌ 記録に失敗しました。")
                                    except Exception as e:
                                        st.error(f"AI採点エラー（Aパターン）: {e}")
                                        st.session_state.score_a="エラー"
                                        st.session_state.comment_a="AI応答エラー"
                            else:
                                st.error("画像アップロードに失敗しました。")
                        else:
                            st.error("利用回数更新に失敗しました。")
                    st.success("Aパターン診断完了！")

            with result_col_a:
                if st.session_state.score_a:
                    st.markdown("### ✨ Aパターン診断結果")
                    st.metric("総合スコア",st.session_state.score_a)
                    st.info(f"**改善コメント:** {st.session_state.comment_a}")
                    if industry in ["美容","健康","医療"]:
                        with st.spinner("⚖️ 薬機法チェック中..."):
                            try:
                                yakujihou_prompt=f"以下のコメントが薬機法違反していないかチェックしてください。---\n{st.session_state.comment_a}\n---"
                                yak_resp=client.chat.completions.create(model="gpt-4o",messages=[{"role":"system","content":"広告表現専門家です。"},{"role":"user","content":yakujihou_prompt}],max_tokens=500,temperature=0.3)
                                st.session_state.yakujihou_a=yak_resp.choices[0].message.content.strip()
                                if "OK" in st.session_state.yakujihou_a:
                                    st.success(f"薬機法チェック：{st.session_state.yakujihou_a}")
                                else:
                                    st.warning(f"薬機法チェック：{st.session_state.yakujihou_a}")
                            except Exception as e:
                                st.error(f"薬機法チェックエラー: {e}")

        st.markdown("---")
        # --- B Pattern ---
        if uploaded_file_b:
            img_col_b,result_col_b=st.columns([1,2])
            with img_col_b:
                st.image(Image.open(uploaded_file_b),caption="Bパターン画像",use_container_width=True)
                if st.button("🚀 Bパターンを採点",key="score_b_btn"):
                    if st.session_state.plan=="Free":
                        st.warning("Freeプランでは利用できません。")
                        st.info("Lightプラン以上をご検討ください。")
                    elif st.session_state.remaining_uses<=0:
                        st.warning(f"残回数なし（{st.session_state.plan}）")
                        st.info("プランアップグレードを。")
                    else:
                        if auth_utils.update_user_uses_in_firestore_rest(st.session_state["user"],st.session_state["id_token"]):
                            image_b_bytes=io.BytesIO()
                            Image.open(uploaded_file_b).save(image_b_bytes,format="PNG")
                            img_str_b=base64.b64encode(image_b_bytes.getvalue()).decode()
                            image_url_b=auth_utils.upload_image_to_firebase_storage(
                                st.session_state["user"],image_b_bytes,
                                f"banner_B_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                            )
                            if image_url_b:
                                with st.spinner("AIがBパターンを採点中..."):
                                    try:
                                        ai_prompt=f"以下のバナー(Age:{age_group},Purpose:{purpose})を採点してください。【基準】1.伝わりやすさ 2.コピー 3.行動 4.整合 5.バランス"
                                        response_b=client.chat.completions.create(
                                            model="gpt-4o",
                                            messages=[
                                                {"role":"system","content":"広告のプロです。"},
                                                {"role":"user","content":[{"type":"text","text":ai_prompt},{"type":"image_url","image_url":{"url":f"data:image/png;base64,{img_str_b}"}}]}
                                            ],max_tokens=600
                                        )
                                        content_b=response_b.choices[0].message.content
                                        st.session_state.score_b=re.search(r"スコア[:：]\s*(.+)",content_b).group(1).strip() if re.search(r"スコア[:：]\s*(.+)",content_b) else "取得できず"
                                        st.session_state.comment_b=re.search(r"改善コメント[:：]\s*(.+)",content_b).group(1).strip() if re.search(r"改善コメント[:：]\s*(.+)",content_b) else "取得できず"
                                        rec_b={"timestamp":datetime.now().isoformat()+"Z","platform":sanitize(platform),"category":sanitize(category),"industry":sanitize(industry),"age_group":sanitize(age_group),"purpose":sanitize(purpose),"score":sanitize(st.session_state.score_b),"comment":sanitize(st.session_state.comment_b),"result":sanitize(result_input),"follower_gain":sanitize(follower_gain_input),"memo":sanitize(memo_input),"image_url":image_url_b}
                                        if auth_utils.add_diagnosis_record_to_firestore(st.session_state["user"],st.session_state["id_token"],rec_b):
                                            st.success("📊 Firestore記録完了！")
                                        else:
                                            st.error("❌ Firestore記録失敗。")
                                    except Exception as e:
                                        st.error(f"AI採点エラー(Bパターン): {e}")
                                        st.session_state.score_b="エラー"
                                        st.session_state.comment_b="AI応答エラー"
                            else:
                                st.error("画像アップロード失敗。")
                        else:
                            st.error("利用回数更新失敗。")
                    st.success("Bパターン診断完了！")

            with result_col_b:
                if st.session_state.score_b:
                    st.markdown("### ✨ Bパターン診断結果")
                    st.metric("総合スコア",st.session_state.score_b)
                    st.info(f"**改善コメント:** {st.session_state.comment_b}")
                    if industry in ["美容","健康","医療"]:
                        with st.spinner("⚖️ 薬機法チェック中..."):
                            try:
                                yakb=f"以下のコメントが薬機法違反かチェック:---\n{st.session_state.comment_b}\n---"
                                yab_resp=client.chat.completions.create(model="gpt-4o",messages=[{"role":"system","content":"広告専門家です。"},{"role":"user","content":yakb}],max_tokens=500,temperature=0.3)
                                st.session_state.yakujihou_b=yab_resp.choices[0].message.content.strip()
                                if "OK" in st.session_state.yakujihou_b:
                                    st.success(f"薬機法チェック：{st.session_state.yakujihou_b}")
                                else:
                                    st.warning(f"薬機法チェック：{st.session_state.yakujihou_b}")
                            except Exception as e:
                                st.error(f"薬機法チェックエラー: {e}")

        st.markdown("---")
        # AB比較
        if st.session_state.score_a and st.session_state.score_b and st.session_state.score_a!="エラー" and st.session_state.score_b!="エラー":
            if st.button("📊 A/Bテスト比較を実行",key="ab_compare_final_btn"):
                with st.spinner("A/B比較中..."):
                    try:
                        comp=f"比較: A({st.session_state.score_a}/{st.session_state.comment_a}/{st.session_state.yakujihou_a}) vs B({st.session_state.score_b}/{st.session_state.comment_b}/{st.session_state.yakujihou_b})"
                        resp=client.chat.completions.create(model="gpt-4o",messages=[{"role":"system","content":"ABテストの専門家です。"},{"role":"user","content":comp}],max_tokens=700,temperature=0.5)
                        st.markdown("### 📈 A/Bテスト比較結果")
                        st.write(resp.choices[0].message.content)
                    except Exception as e:
                        st.error(f"AB比較エラー: {e}")

with col2:
    with st.expander("📌 採点基準はこちら",expanded=True):
        st.markdown("- 内容が一瞬で伝わるか\n- コピーの見やすさ\n- 行動喚起の明確さ\n- 写真とテキストの整合性\n- 情報量のバランス")
    st.markdown("---")
    st.info("💡 AIの提案は参考です。最終判断は人間で！")
