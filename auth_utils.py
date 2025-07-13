import streamlit as st
import os
import requests
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore, storage
import json
from datetime import datetime

load_dotenv()

FIREBASE_API_KEY = os.getenv("OPENAI_API_KEY")

if not FIREBASE_API_KEY:
    st.error("Firebase APIキーが.envファイルに見つかりません。")
    st.stop()

FIREBASE_AUTH_BASE_URL = "https://identitytoolkit.googleapis.com/v1/accounts:"
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")

if not FIREBASE_PROJECT_ID:
    st.error("FirebaseプロジェクトIDが.envファイルに見つかりません。")
    st.stop()

FIREBASE_FIRESTORE_BASE_URL = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/"

try:
    if "firebase_admin_initialized" not in st.session_state:
        admin_project_id = os.getenv("FIREBASE_PROJECT_ID_ADMIN")
        admin_private_key = os.getenv("FIREBASE_PRIVATE_KEY_ADMIN")
        admin_client_email = os.getenv("FIREBASE_CLIENT_EMAIL_ADMIN")
        storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET")

        if not admin_project_id or not admin_private_key or not admin_client_email or not storage_bucket:
            st.error("Firebase Admin SDKの環境変数が不足しています。Secretsを確認してください。")
            st.stop()

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
    st.error(f"Firebase Admin SDKの初期化に失敗しました: {e}")
    st.stop()

def sign_in_with_email_and_password(email, password):
    url = f"{FIREBASE_AUTH_BASE_URL}signInWithPassword?key={FIREBASE_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {"email": email, "password": password, "returnSecureToken": True}
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

def create_user_with_email_and_password(email, password):
    url = f"{FIREBASE_AUTH_BASE_URL}signUp?key={FIREBASE_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {"email": email, "password": password, "returnSecureToken": True}
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

def get_user_data_from_firestore_rest(uid, id_token):
    global db 
    doc_ref = db.collection('users').document(uid)
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        plan = data.get("plan", "Free")
        remaining_uses = data.get("remaining_uses", 0)
        if plan.lower() == "free":
            remaining_uses = min(remaining_uses, 5)
        st.session_state.plan = plan
        st.session_state.remaining_uses = remaining_uses
    else:
        st.session_state.plan = "Free"
        st.session_state.remaining_uses = 5
        doc_ref.set({
            "email": st.session_state.email,
            "plan": st.session_state.plan,
            "remaining_uses": st.session_state.remaining_uses,
            "created_at": firestore.SERVER_TIMESTAMP
        })
    st.sidebar.write(f"残り回数: {st.session_state.remaining_uses}回 ({st.session_state.plan}プラン)")
    return True

def update_user_uses_in_firestore_rest(uid, id_token, uses_to_deduct=1):
    global db
    doc_ref = db.collection('users').document(uid)
    try:
        doc = doc_ref.get()
        if not doc.exists:
            st.error("ユーザーデータがFirestoreに存在しません。")
            return False
        user_data = doc.to_dict()
        plan = user_data.get("plan", "Free").lower()
        current_uses = user_data.get("remaining_uses", 0)
        if plan == "free" and current_uses <= 0:
            st.warning("Freeプランの残り回数がありません。")
            return False
        doc_ref.update({
            "remaining_uses": firestore.Increment(-uses_to_deduct),
            "last_used_at": firestore.SERVER_TIMESTAMP
        })
        st.session_state.remaining_uses = max(0, st.session_state.remaining_uses - uses_to_deduct)
        st.sidebar.write(f"残り回数: {st.session_state.remaining_uses}回 ({st.session_state.plan}プラン)")
        return True
    except Exception as e:
        st.error(f"利用回数の更新に失敗しました: {e}")
        return False
