# auth_utils.py
import streamlit as st
import os
import requests
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore, storage 
import json
from datetime import datetime

# .envファイルに設定すべき環境変数の例:
# OPENAI_API_KEY="sk-proj-YOUR_OPENAI_API_KEY"
# FIREBASE_WEB_API_KEY="AIzaSyAflp1vqSA21sSYihZDTpje-MB1mCALxBs"
# FIREBASE_PROJECT_ID="your-project-id" # FirebaseプロジェクトのID
#
# # Firebase Admin SDK (Secretsに設定推奨)
# FIREBASE_PROJECT_ID_ADMIN="your-project-id"
# FIREBASE_PRIVATE_KEY_ADMIN="-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_CONTENT\n-----END PRIVATE KEY-----\n" # JSONからそのままコピー
# FIREBASE_CLIENT_EMAIL_ADMIN="firebase-adminsdk-fbsvc@your-project-id.iam.gserviceaccount.com"
# FIREBASE_STORAGE_BUCKET="your-project-id.appspot.com"
# # 以下はオプションですが、JSONにあるなら設定しても良い
# # FIREBASE_PRIVATE_KEY_ID_ADMIN="your_private_key_id"
# # FIREBASE_CLIENT_ID_ADMIN="your_client_id"

# .envファイルから環境変数を読み込む
load_dotenv()

# Firebase Authentication REST APIに必要なAPIキーを取得
FIREBASE_API_KEY = os.getenv("FIREBASE_WEB_API_KEY")

if not FIREBASE_API_KEY:
    st.error("❌ 環境変数 'FIREBASE_WEB_API_KEY' が設定されていません。FirebaseのWeb APIキーが必要です。")
    st.stop()

FIREBASE_AUTH_BASE_URL = "https://identitytoolkit.googleapis.com/v1/accounts:"
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")

if not FIREBASE_PROJECT_ID:
    st.error("❌ 環境変数 'FIREBASE_PROJECT_ID' が設定されていません。FirebaseプロジェクトIDが必要です。")
    st.stop()

FIREBASE_FIRESTORE_BASE_URL = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/"

# Firebase Admin SDK 初期化
try:
    if "firebase_admin_initialized" not in st.session_state:
        admin_project_id = os.getenv("FIREBASE_PROJECT_ID_ADMIN")
        admin_private_key_raw = os.getenv("FIREBASE_PRIVATE_KEY_ADMIN")
        admin_client_email = os.getenv("FIREBASE_CLIENT_EMAIL_ADMIN")
        storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET") 

        missing_vars = []
        if not admin_project_id: missing_vars.append("FIREBASE_PROJECT_ID_ADMIN")
        if not admin_private_key_raw: missing_vars.append("FIREBASE_PRIVATE_KEY_ADMIN")
        if not admin_client_email: missing_vars.append("FIREBASE_CLIENT_EMAIL_ADMIN")
        if not storage_bucket: missing_vars.append("FIREBASE_STORAGE_BUCKET")

        if missing_vars:
            st.error(f"❌ Firebase Admin SDKの環境変数が不足しています: {', '.join(missing_vars)}。Secretsを確認してください。")
            st.stop()

        admin_private_key = admin_private_key_raw.replace('\n', '\n').replace('\\n', '\n')

        service_account_info = {
            "type": "service_account",
            "project_id": admin_project_id,
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID_ADMIN"),
            "private_key": admin_private_key,
            "client_email": admin_client_email,
            "client_id": os.getenv("FIREBASE_CLIENT_ID_ADMIN"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{admin_client_email.replace('@', '%40')}",
            "universe_domain": "googleapis.com"
        }

        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred, {'storageBucket': storage_bucket})
        st.session_state.firebase_admin_initialized = True
        db = firestore.client()
except Exception as e:
    st.error(f"❌ Firebase Admin SDKの初期化に失敗しました: {e}")
    st.stop()
