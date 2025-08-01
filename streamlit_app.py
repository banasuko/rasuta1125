# auth_utils.py
import os
import firebase_admin
from firebase_admin import credentials, firestore, storage

# 環境変数からサービスアカウント情報を取得
PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID_ADMIN")
PRIVATE_KEY = os.getenv("FIREBASE_PRIVATE_KEY_ADMIN")
PRIVATE_KEY_ID = os.getenv("FIREBASE_PRIVATE_KEY_ID_ADMIN")
CLIENT_EMAIL = os.getenv("FIREBASE_CLIENT_EMAIL_ADMIN")
CLIENT_ID = os.getenv("FIREBASE_CLIENT_ID_ADMIN")

# 必須環境変数チェック
required = {"PROJECT_ID": PROJECT_ID, "PRIVATE_KEY": PRIVATE_KEY, "CLIENT_EMAIL": CLIENT_EMAIL}
missing = [k for k,v in required.items() if not v]
if missing:
    raise ValueError(f"Missing Firebase env vars: {missing}")

# 改行エスケープ復元
PRIVATE_KEY = PRIVATE_KEY.replace("\\n", "\n")

# PEM形式チェック
if "-----BEGIN PRIVATE KEY-----" not in PRIVATE_KEY:
    raise ValueError("Invalid PRIVATE_KEY: Missing PEM header/footer")

# サービスアカウント情報
cred_info = {
    "type": "service_account",
    "project_id": PROJECT_ID,
    "private_key_id": PRIVATE_KEY_ID,
    "private_key": PRIVATE_KEY,
    "client_email": CLIENT_EMAIL,
    "client_id": CLIENT_ID
}

# Firebase初期化
try:
    cred = credentials.Certificate(cred_info)
    firebase_admin.initialize_app(cred, {"projectId": PROJECT_ID})
except Exception as e:
    print("[auth_utils] Firebase init error:", e)
    raise

# Firestore/Storageクライアント
db = firestore.client()
bucket = storage.bucket()

# ログインチェック
import streamlit as st

def check_login():
    if "user" not in st.session_state or "id_token" not in st.session_state:
        st.error("ログインが必要です。再度ログインしてください。")
        st.stop()

# Firestore書き込み (実装例)
def update_user_uses_in_firestore_rest(user, id_token):
    # TODO: 既存ロジックを移植
    return True

def add_diagnosis_record_to_firestore(user, id_token, record):
    # TODO: 既存ロジックを移植
    return True

# 画像アップロード
from io import BytesIO

def upload_image_to_firebase_storage(user, img_io: BytesIO, filename: str) -> str:
    try:
        blob = bucket.blob(f"banners/{user['uid']}/{filename}")
        blob.upload_from_file(img_io, content_type="image/png")
        blob.make_public()
        return blob.public_url
    except Exception as e:
        print("[auth_utils] upload error:", e)
        return None


# =========================
# streamlit_app.py
import streamlit as st
import base64
import io
import os
import re
from PIL import Image
from datetime import datetime
from openai import OpenAI
import auth_utils

# GAS URL
GAS_URL = os.getenv("GAS_URL", "https://script.google.com/macros/s/AKfycby_uD6Jtb9GT0-atbyPKOPc8uyVKodwYVIQ2Tpe-_E8uTOPiir0Ce1NAPZDEOlCUxN4/exec")

# sanitize helper
def sanitize(v):
    return "エラー" if v is None or v == "取得できず" else v

# Streamlit config
st.set_page_config(layout="wide", page_title="バナスコAI")

# ロゴ
logo = "banasuko_logo_icon.png"
try:
    st.sidebar.image(Image.open(logo), use_container_width=True)
except:
    st.sidebar.error(f"ロゴ読み込み失敗: {logo}")

# ログインチェック auth_utils
auth_utils.check_login()

# OpenAI init
key = os.getenv("OPENAI_API_KEY")
if not key:
    st.error("🔑 OpenAI APIキーがありません。")
    st.stop()
client = OpenAI(api_key=key)

# CSS
st.markdown("""
<style>
body{background:#fff}
.main .block-container{background:#fff;padding:2rem;border-radius:12px}
.stSidebar{background:#f8f8f8}
.stButton>button{background:#0066ff;color:#fff;border-radius:8px}
</style>
""", unsafe_allow_html=True)

# タイトル
st.title("🧠 バナー広告 採点AI - バナスコ")
st.subheader("〜無駄打ちゼロのA/Bテスト支援〜")

col1, col2 = st.columns([2,1])

with col1:
    # 基本情報
    st.subheader("📝 入力フォーム")
    name = st.text_input("ユーザー名")
    age = st.selectbox("ターゲット年代", ["指定なし","10代","20代","30代","40代","50代","60代以上"])
    media = st.selectbox("媒体", ["Instagram","GDN","YDN"])
    cat = st.selectbox("カテゴリ", ["広告","投稿"] if media=="Instagram" else ["広告"])
    budget = st.selectbox("広告予算", ["あり","なし"])
    purpose = st.selectbox("目的", ["リンククリック","保存数増加","インプレッション増加"])
    # 詳細
    with st.expander("🎯 詳細設定", True):
        industry = st.selectbox("業種", ["美容","飲食","不動産","子ども写真館","その他"])
        genre = st.selectbox("ジャンル", ["声","商品紹介","ノウハウ","世界観","キャンペーン"])
        score_fmt = st.radio("スコア形式", ["A/B/C","100点満点"], horizontal=True)
        ab = st.radio("ABテスト", ["A","B","なし"], horizontal=True)
        title = st.text_input("バナー名")
    # 任意
    with st.expander("📌 任意", False):
        custom = st.text_input("AI結果（任意）")
        gain = st.text_input("増加数（任意）")
        memo = st.text_area("メモ（任意）")

    st.markdown("---")
    st.subheader("🖼️ アップロード & 診断")
    up_a = st.file_uploader("Aパターン", type=["png","jpg","jpeg"], key="up_a")
    up_b = st.file_uploader("Bパターン", type=["png","jpg","jpeg"], key="up_b")

    # セッション初期値
    for k in ["score_a","cm_a","yk_a","score_b","cm_b","yk_b"]:
        if k not in st.session_state: st.session_state[k]=None

    def run_score(file, key_prefix):
        # 共通処理
        img_io = io.BytesIO(); Image.open(file).save(img_io,format="PNG")
        b64 = base64.b64encode(img_io.getvalue()).decode()
        url = auth_utils.upload_image_to_firebase_storage(st.session_state['user'], img_io, f"{key_prefix}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png")
        prompt = f"バナーを採点: 年齢={age},目的={purpose}\n基準:伝わりやすさ,コピー,行動呼びかけ,整合,情報量"
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role":"system","content":"広告プロです。"},{"role":"user","content":[{"type":" text","text":prompt},{"type":"image_url","image_url":{"url":f"data:image/png;base64,{b64}"}}]}],
            max_tokens=500
        )
        cont = resp.choices[0].message.content
        sc = re.search(r"スコア[:：]\s*(\S+)", cont); cm = re.search(r"改善コメント[:：]\s*(.+)", cont)
        st.session_state[f"score_{key_prefix}"] = sc.group(1) if sc else "取得できず"
        st.session_state[f"cm_{key_prefix}"] = cm.group(1) if cm else "取得できず"
        return url

    # Aパターン
    if up_a:
        st.image(Image.open(up_a), caption="Aパターン", use_column_width=True)
        if st.button("🚀 採点 A", key="btn_a"):
            run_score(up_a, 'a')
    if st.session_state.score_a:
        st.metric("A スコア", st.session_state.score_a)
        st.write("A コメント:", st.session_state.cm_a)

    st.markdown("---")
    # Bパターン
    if up_b:
        st.image(Image.open(up_b), caption="Bパターン", use_column_width=True)
        if st.button("🚀 採点 B", key="btn_b"):
            run_score(up_b, 'b')
    if st.session_state.score_b:
        st.metric("B スコア", st.session_state.score_b)
        st.write("B コメント:", st.session_state.cm_b)

    # AB比較
    if st.session_state.score_a and st.session_state.score_b:
        if st.button("🔍 A/B比較"):
            comp = f"A:{st.session_state.score_a}/{st.session_state.cm_a} vs B:{st.session_state.score_b}/{st.session_state.cm_b}"
            r = client.chat.completions.create(model="gpt-4o",messages=[{"role":"system","content":"ABテスト専門家です。"},{"role":"user","content":comp}],max_tokens=300)
            st.write(r.choices[0].message.content)

with col2:
    st.info("💡 AIの提案は参考です。最終判断は人間で。")
