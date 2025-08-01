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
if "-----BEGIN PRIVATE KEY-----" not in PRIVATE_KEY or "-----END PRIVATE KEY-----" not in PRIVATE_KEY:
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
GAS_URL = os.getenv(
    "GAS_URL",
    "https://script.google.com/macros/s/AKfycby_uD6Jtb9GT0-atbyPKOPc8uyVKodwYVIQ2Tpe-_E8uTOPiir0Ce1NAPZDEOlCUxN4/exec"
)

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

# ログインチェック
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
body{background:#fff !important;}
.main .block-container{background:#fff;padding:2rem;border-radius:12px;box-shadow:0 8px 20px rgba(0,0,0,0.08);}
.stSidebar{background:#f8f8f8;box-shadow:2px 0 10px rgba(0,0,0,0.05);}
.stButton>button{background:#0066ff;color:#fff;border-radius:8px;font-weight:bold;}
.stButton>button:hover{background:#0052cc;}
.stExpander{border:1px solid #e0e0e0;border-radius:8px;}
code{background:#f0f0f0;color:#000080;border-radius:5px;padding:0.2em;}
</style>
""", unsafe_allow_html=True)

# タイトル
st.title("🧠 バナー広告 採点AI - バナスコ")
st.subheader("〜もう、無駄打ちしない。広告を武器に変えるAIツール〜")

col1, col2 = st.columns([2,1])
with col1:
    # 入力フォーム省略（元コードを踏襲）
    # --- Upload & Scoring ---
    up_a = st.file_uploader("Aパターン画像をアップロード", type=["png","jpg","jpeg"], key="up_a")
    up_b = st.file_uploader("Bパターン画像をアップロード", type=["png","jpg","jpeg"], key="up_b")
    for k in ["score_a","comment_a","yakujihou_a"]:
        if k not in st.session_state: st.session_state[k]=None
    for k in ["score_b","comment_b","yakujihou_b"]:
        if k not in st.session_state: st.session_state[k]=None

    # Aパターン処理
    if up_a:
        st.image(up_a, caption="Aパターン", use_column_width=True)
        if st.button("🚀 採点 A", key="btn_a"):
            img_io = io.BytesIO(); Image.open(up_a).save(img_io,format='PNG')
            b64 = base64.b64encode(img_io.getvalue()).decode()
            try:
                resp = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role":"system","content":"広告のプロです。"},
                        {"role":"user","content":[{"type":"text","text":"Aパターンを採点してください。"},{"type":"image_url","image_url":{"url":f"data:image/png;base64,{b64}"}}]}
                    ],
                    max_tokens=500
                )
                cont = resp.choices[0].message.content
                m1 = re.search(r"スコア[:：]\s*(\S+)", cont)
                m2 = re.search(r"改善コメント[:：]\s*(.+)", cont)
                st.session_state.score_a = m1.group(1) if m1 else "取得できず"
                st.session_state.comment_a = m2.group(1) if m2 else "取得できず"
            except Exception as e:
                st.error(f"AパターンAIエラー: {e}")
    if st.session_state.score_a:
        st.metric("Aスコア", st.session_state.score_a)
        st.write(st.session_state.comment_a)

    st.markdown("---")
    # Bパターン処理
    if up_b:
        st.image(up_b, caption="Bパターン", use_column_width=True)
        if st.button("🚀 採点 B", key="btn_b"):
            img_io = io.BytesIO(); Image.open(up_b).save(img_io,format='PNG')
            b64 = base64.b64encode(img_io.getvalue()).decode()
            try:
                resp = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role":"system","content":"広告のプロです。"},
                        {"role":"user","content":[{"type":"text","text":"Bパターンを採点してください。"},{"type":"image_url","image_url":{"url":f"data:image/png;base64,{b64}"}}]}
                    ],
                    max_tokens=500
                )
                cont = resp.choices[0].message.content
                m1 = re.search(r"スコア[:：]\s*(\S+)", cont)
                m2 = re.search(r"改善コメント[:：]\s*(.+)", cont)
                st.session_state.score_b = m1.group(1) if m1 else "取得できず"
                st.session_state.comment_b = m2.group(1) if m2 else "取得できず"
            except Exception as e:
                st.error(f"BパターンAIエラー: {e}")
    if st.session_state.score_b:
        st.metric("Bスコア", st.session_state.score_b)
        st.write(st.session_state.comment_b)

    # A/B比較
    if st.session_state.score_a and st.session_state.score_b:
        if st.button("🔍 A/B比較"):
            try:
                comp = f"A:{st.session_state.score_a}/{st.session_state.comment_a} vs B:{st.session_state.score_b}/{st.session_state.comment_b}"
                resp = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role":"system","content":"ABテスト専門家です。"},{"role":"user","content":comp}],
                    max_tokens=300
                )
                st.write(resp.choices[0].message.content)
            except Exception as e:
                st.error(f"A/B比較エラー: {e}")

with col2:
    st.info("💡 AIの提案は参考です。最終判断は人間でお願いします。")
