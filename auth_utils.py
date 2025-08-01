# auth_utils.py
import streamlit as st
import os
import requests
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore, storage
import json
from datetime import datetime

# .envファイルから環境変数を読み込む
load_dotenv()

# --- グローバル変数の定義 ---
db = None

# --- 環境変数の読み込みとチェック ---
FIREBASE_API_KEY = os.getenv("FIREBASE_WEB_API_KEY")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
ADMIN_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID_ADMIN")
ADMIN_PRIVATE_KEY_RAW = os.getenv("FIREBASE_PRIVATE_KEY_ADMIN")
ADMIN_CLIENT_EMAIL = os.getenv("FIREBASE_CLIENT_EMAIL_ADMIN")
STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")

# 必須の環境変数が設定されているかチェック
missing_vars = []
if not FIREBASE_API_KEY: missing_vars.append("FIREBASE_WEB_API_KEY")
if not FIREBASE_PROJECT_ID: missing_vars.append("FIREBASE_PROJECT_ID")
if not ADMIN_PROJECT_ID: missing_vars.append("FIREBASE_PROJECT_ID_ADMIN")
if not ADMIN_PRIVATE_KEY_RAW: missing_vars.append("FIREBASE_PRIVATE_KEY_ADMIN")
if not ADMIN_CLIENT_EMAIL: missing_vars.append("FIREBASE_CLIENT_EMAIL_ADMIN")
if not STORAGE_BUCKET: missing_vars.append("FIREBASE_STORAGE_BUCKET")

if missing_vars:
    st.error(f"❌ 必須の環境変数が不足しています: {', '.join(missing_vars)}。Streamlit CloudのSecretsを確認してください。")
    st.stop()

# --- Firebase Admin SDKの初期化 ---
# アプリのセッション中で一度だけ実行されるように制御
try:
    if not firebase_admin._apps:
        # private_keyの改行コードを正しく処理
        admin_private_key = ADMIN_PRIVATE_KEY_RAW.replace('\\n', '\n')

        # サービスアカウント情報（辞書形式で構築）
        service_account_info = {
            "type": "service_account",
            "project_id": ADMIN_PROJECT_ID,
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID_ADMIN", ""), # オプション
            "private_key": admin_private_key,
            "client_email": ADMIN_CLIENT_EMAIL,
            "client_id": os.getenv("FIREBASE_CLIENT_ID_ADMIN", ""), # オプション
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{ADMIN_CLIENT_EMAIL.replace('@', '%40')}",
        }

        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred, {'storageBucket': STORAGE_BUCKET})

    # 初期化が成功したら、Firestoreクライアントを取得
    db = firestore.client()

except Exception as e:
    st.error(f"❌ Firebase Admin SDKの初期化に失敗しました。サービスアカウントキーを確認してください。")
    st.error(f"エラー詳細: {e}")
    st.stop()

# --- Streamlitのセッションステート初期化 ---
# 初回ロード時のみ実行
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.email = None
    st.session_state.id_token = None
    st.session_state.plan = "Guest"
    st.session_state.remaining_uses = 0

# --- Firebase Authentication REST APIの関数 ---
FIREBASE_AUTH_BASE_URL = "https://identitytoolkit.googleapis.com/v1/accounts:"

def sign_in_with_email_and_password(email, password):
    """Firebase REST API を使ってメールとパスワードでサインインする"""
    url = f"{FIREBASE_AUTH_BASE_URL}signInWithPassword?key={FIREBASE_API_KEY}"
    data = {"email": email, "password": password, "returnSecureToken": True}
    response = requests.post(url, json=data)
    response.raise_for_status()
    return response.json()

def create_user_with_email_and_password(email, password):
    """Firebase REST API を使ってメールとパスワードでユーザーを作成する"""
    url = f"{FIREBASE_AUTH_BASE_URL}signUp?key={FIREBASE_API_KEY}"
    data = {"email": email, "password": password, "returnSecureToken": True}
    response = requests.post(url, json=data)
    response.raise_for_status()
    return response.json()

# --- Firestoreの操作関数 ---
def get_user_data_from_firestore(uid):
    """Firestoreからユーザーのプランと利用回数を取得する"""
    global db
    doc_ref = db.collection('users').document(uid)
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        st.session_state.plan = data.get("plan", "Free")
        st.session_state.remaining_uses = data.get("remaining_uses", 0)
    else:
        st.session_state.plan = "Free"
        st.session_state.remaining_uses = 5
        doc_ref.set({
            "email": st.session_state.email,
            "plan": st.session_state.plan,
            "remaining_uses": st.session_state.remaining_uses,
            "created_at": firestore.SERVER_TIMESTAMP
        })
    return True

def update_user_uses_in_firestore(uid, uses_to_deduct=1):
    """Firestoreのユーザー利用回数を減らす"""
    global db
    doc_ref = db.collection('users').document(uid)
    try:
        doc_ref.update({
            "remaining_uses": firestore.Increment(-uses_to_deduct),
            "last_used_at": firestore.SERVER_TIMESTAMP
        })
        st.session_state.remaining_uses -= uses_to_deduct
        return True
    except Exception as e:
        st.error(f"利用回数の更新に失敗しました: {e}")
        return False

def add_diagnosis_record_to_firestore(uid, record_data):
    """ユーザーの診断記録をFirestoreのdiagnosesサブコレクションに追加する"""
    global db
    doc_ref = db.collection('users').document(uid).collection('diagnoses').document()
    try:
        record_data["created_at"] = firestore.SERVER_TIMESTAMP
        doc_ref.set(record_data)
        return True
    except Exception as e:
        st.error(f"診断記録のFirestore保存に失敗しました: {e}")
        return False

# --- Firebase Storageの操作関数 ---
def upload_image_to_firebase_storage(uid, image_bytes_io, filename):
    """画像をFirebase Storageにアップロードし、公開URLを返す"""
    try:
        bucket = storage.bucket()
        blob = bucket.blob(f"users/{uid}/diagnoses_images/{filename}")
        image_bytes_io.seek(0)
        blob.upload_from_file(image_bytes_io, content_type="image/png")
        blob.make_public()
        return blob.public_url
    except Exception as e:
        st.error(f"Firebase Storageへの画像アップロードに失敗しました: {e}")
        return None

# --- StreamlitのUI表示と認証フロー ---
def login_page():
    """Streamlit上にログイン画面を表示する関数"""
    st.title("🔐 バナスコAI ログイン")
    st.markdown("機能を利用するにはログインが必要です。")

    email = st.text_input("メールアドレス", key="login_email")
    password = st.text_input("パスワード", type="password", key="login_password")

    login_col, create_col = st.columns(2)
    with login_col:
        if st.button("ログイン", key="login_button"):
            with st.spinner("ログイン中..."):
                try:
                    user_info = sign_in_with_email_and_password(email, password)
                    st.session_state.logged_in = True
                    st.session_state.user = user_info["localId"]
                    st.session_state.email = user_info["email"]
                    st.session_state.id_token = user_info["idToken"]
                    get_user_data_from_firestore(user_info["localId"])
                    st.success(f"ログインしました: {user_info['email']}")
                    st.rerun()
                except requests.exceptions.HTTPError as e:
                    st.error("ログインに失敗しました。メールアドレスまたはパスワードが間違っています。")
                except Exception as e:
                    st.error(f"予期せぬエラーが発生しました: {e}")

    with create_col:
        if st.button("アカウント作成", key="create_account_button"):
            with st.spinner("アカウント作成中..."):
                try:
                    user_info = create_user_with_email_and_password(email, password)
                    st.session_state.logged_in = True
                    st.session_state.user = user_info["localId"]
                    st.session_state.email = user_info["email"]
                    st.session_state.id_token = user_info["idToken"]
                    get_user_data_from_firestore(user_info["localId"])
                    st.success(f"アカウント '{user_info['email']}' を作成し、ログインしました。")
                    st.rerun()
                except requests.exceptions.HTTPError as e:
                    error_json = e.response.json().get("error", {})
                    if error_json.get("message") == "EMAIL_EXISTS":
                        st.error("このメールアドレスは既に使用されています。")
                    elif error_json.get("message") == "WEAK_PASSWORD":
                        st.error("パスワードが弱すぎます（6文字以上必要）。")
                    else:
                        st.error(f"アカウント作成中にエラーが発生しました。")
                except Exception as e:
                    st.error(f"予期せぬエラーが発生しました: {e}")

def logout():
    """ユーザーをログアウトさせ、セッションステートをクリアする関数"""
    # 辞書を変更しながらイテレートしないようにキーのリストをコピー
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.success("ログアウトしました。")
    st.rerun()

def check_login():
    """
    ユーザーのログイン状態をチェックし、未ログインならログインページを表示。
    ログイン済みならサイドバーに情報を表示。
    """
    if not st.session_state.get("logged_in"):
        login_page()
        st.stop()
    else:
        st.sidebar.write(f"ようこそ, {st.session_state.email}!")
        st.sidebar.write(f"残り回数: {st.session_state.remaining_uses}回 ({st.session_state.plan}プラン)")
        st.sidebar.button("ログアウト", on_click=logout)
