# auth_utils.py
import streamlit as st
import os
import requests
import firebase_admin
from firebase_admin import credentials, firestore, storage
from dotenv import load_dotenv
from datetime import datetime

# ---------- 1) 環境変数読み込み (モジュールレベルで一度だけ) ----------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
FIREBASE_PROJECT_ID_ADMIN = os.getenv("FIREBASE_PROJECT_ID_ADMIN")
FIREBASE_PRIVATE_KEY_ADMIN_RAW = os.getenv("FIREBASE_PRIVATE_KEY_ADMIN")
FIREBASE_PRIVATE_KEY_ID_ADMIN = os.getenv("FIREBASE_PRIVATE_KEY_ID_ADMIN")
FIREBASE_CLIENT_EMAIL_ADMIN = os.getenv("FIREBASE_CLIENT_EMAIL_ADMIN")
FIREBASE_CLIENT_ID_ADMIN = os.getenv("FIREBASE_CLIENT_ID_ADMIN")
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")

# ---------- 2) Firebase Admin SDK の初期化をキャッシュ ----------
@st.cache_resource
def init_firebase_admin():
    missing = []
    if not FIREBASE_PROJECT_ID_ADMIN:
        missing.append("FIREBASE_PROJECT_ID_ADMIN")
    if not FIREBASE_PRIVATE_KEY_ADMIN_RAW:
        missing.append("FIREBASE_PRIVATE_KEY_ADMIN")
    if not FIREBASE_CLIENT_EMAIL_ADMIN:
        missing.append("FIREBASE_CLIENT_EMAIL_ADMIN")
    if not FIREBASE_STORAGE_BUCKET:
        missing.append("FIREBASE_STORAGE_BUCKET")
    if missing:
        st.error(f"❌ Firebase Admin SDKの環境変数が不足しています: {', '.join(missing)}。Secretsを確認してください。")
        st.stop()

    # PEM キーのクリーニング
    key = FIREBASE_PRIVATE_KEY_ADMIN_RAW.replace('\\r\\n', '\\n').replace('\\r', '\\n').strip()
    key = key.replace('\\n', '\n')
    if not key.startswith("-----BEGIN PRIVATE KEY-----"):
        st.error("❌ PRIVATE_KEY_ADMIN のフォーマットが不正です。改行を確認してください。")
        st.stop()

    service_account = {
        "type": "service_account",
        "project_id": FIREBASE_PROJECT_ID_ADMIN,
        "private_key_id": FIREBASE_PRIVATE_KEY_ID_ADMIN,
        "private_key": key,
        "client_email": FIREBASE_CLIENT_EMAIL_ADMIN,
        "client_id": FIREBASE_CLIENT_ID_ADMIN,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{FIREBASE_CLIENT_EMAIL_ADMIN.replace('@','%40')}",
        "universe_domain": "googleapis.com",
    }
    cred = credentials.Certificate(service_account)
    firebase_admin.initialize_app(cred, {"storageBucket": FIREBASE_STORAGE_BUCKET})
    return firestore.client(), storage.bucket()

# Admin SDK 初期化
db, bucket = init_firebase_admin()

# ---------- 3) キャッシュ付きデータ取得 ----------
@st.cache_data(ttl=300)
def get_user_data(uid: str) -> dict:
    """Firestore からユーザーデータを取得してキャッシュ"""
    doc = db.collection('users').document(uid).get()
    return doc.to_dict() if doc.exists else {}

# ---------- 4) 認証 REST API ヘルパー ----------
def sign_in_with_email_and_password(email: str, password: str) -> dict:
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
    res = requests.post(url, json={"email":email, "password":password, "returnSecureToken":True})
    res.raise_for_status()
    return res.json()


def create_user_with_email_and_password(email: str, password: str) -> dict:
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_WEB_API_KEY}"
    res = requests.post(url, json={"email":email, "password":password, "returnSecureToken":True})
    res.raise_for_status()
    return res.json()

# ---------- 5) Firestore 操作 ----------
def update_user_uses(uid: str, uses: int = -1) -> bool:
    try:
        db.collection('users').document(uid).update({
            "remaining_uses": firestore.Increment(uses),
            "last_used_at": firestore.SERVER_TIMESTAMP
        })
        return True
    except Exception as e:
        st.error(f"利用回数の更新に失敗: {e}")
        return False

# ---------- 6) Storage アップロード ----------
def upload_image(uid: str, image_bytes_io, filename: str) -> str | None:
    try:
        blob = bucket.blob(f"users/{uid}/diagnoses_images/{filename}")
        image_bytes_io.seek(0)
        blob.upload_from_file(image_bytes_io, content_type='image/png')
        blob.make_public()
        return blob.public_url
    except Exception as e:
        st.error(f"Storage アップロードに失敗: {e}")
        return None
