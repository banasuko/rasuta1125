# auth_utils.py
import streamlit as st
import os
import requests
from dotenv import load_dotenv
import firebase_admin # Firestore用
from firebase_admin import credentials, firestore, storage # storageも再度インポート
import json # JSON文字列のパース用
from datetime import datetime


# .envファイルから環境変数を読み込む
load_dotenv()

# Firebase Authentication REST APIに必要なAPIキーを取得
FIREBASE_API_KEY = os.getenv("OPENAI_API_KEY") # OpenAI APIキーをFirebase APIキーとして使用 (以前のコードのまま)

if not FIREBASE_API_KEY:
    st.error("Firebase APIキーが.envファイルに見つかりません。")
    st.stop()

# Firebase Authentication REST APIのエンドポイントベースURL
FIREBASE_AUTH_BASE_URL = "https://identitytoolkit.googleapis.com/v1/accounts:"
# Firestore REST APIのエンドポイントベースURL
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID") # .envに設定されているはず

if not FIREBASE_PROJECT_ID:
    st.error("FirebaseプロジェクトIDが.envファイルに見つかりません。")
    st.stop()

FIREBASE_FIRESTORE_BASE_URL = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/"


# --- Firebase Admin SDKの初期化 (Firestore & Storage用) ---
try:
    if "firebase_admin_initialized" not in st.session_state:
        admin_project_id = os.getenv("FIREBASE_PROJECT_ID_ADMIN")
        admin_private_key = os.getenv("FIREBASE_PRIVATE_KEY_ADMIN")
        admin_client_email = os.getenv("FIREBASE_CLIENT_EMAIL_ADMIN")
        storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET") # Storageバケット名も必要

        # 必須の環境変数が設定されているかチェック
        if not admin_project_id or not admin_private_key or not admin_client_email or not storage_bucket:
            st.error("Firebase Admin SDKの環境変数（PROJECT_ID_ADMIN, PRIVATE_KEY_ADMIN, CLIENT_EMAIL_ADMIN, STORAGE_BUCKET）が不足しています。Secretsを確認してください。")
            st.stop()

        # サービスアカウント情報（辞書形式で構築）
        service_account_info = {
            "type": "service_account",
            "project_id": admin_project_id,
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID_ADMIN"), # もしSecretsにあれば読み込む
            "private_key": admin_private_key, # エスケープ不要な形式で取得
            "client_email": admin_client_email,
            "client_id": os.getenv("FIREBASE_CLIENT_ID_ADMIN"), # もしSecretsにあれば読み込む
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{admin_client_email.replace('@', '%40')}",
            "universe_domain": "googleapis.com"
        }
        
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred, {'storageBucket': storage_bucket}) # Storageバケット名を指定して初期化
        st.session_state.firebase_admin_initialized = True
        db = firestore.client() # Firestoreクライアントを初期化
except Exception as e:
    st.error(f"Firebase Admin SDKの初期化に失敗しました。サービスアカウントキーを確認してください: {e}")
    st.error(f"エラー詳細: {e}")
    st.stop()


# Streamlitのセッションステートを初期化 (初回ロード時のみ)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "email" not in st.session_state:
    st.session_state.email = None
if "id_token" not in st.session_state:
    st.session_state.id_token = None
if "plan" not in st.session_state:
    st.session_state.plan = "Guest"
if "remaining_uses" not in st.session_state:
    st.session_state.remaining_uses = 0
if "firebase_initialized" not in st.session_state: # Admin SDK初期化のtry-exceptで制御されるため、ここはTrueのまま
    st.session_state.firebase_initialized = True


# --- Firebase Authentication REST APIの関数 ---
def sign_in_with_email_and_password(email, password):
    """Firebase REST API を使ってメールとパスワードでサインインする"""
    url = f"{FIREBASE_AUTH_BASE_URL}signInWithPassword?key={FIREBASE_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

def create_user_with_email_and_password(email, password):
    """Firebase REST API を使ってメールとパスワードでユーザーを作成する"""
    url = f"{FIREBASE_AUTH_BASE_URL}signUp?key={FIREBASE_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


# --- Firestoreの操作関数 (Admin SDKを使用) ---
def get_user_data_from_firestore_rest(uid, id_token):
    """Firestoreからユーザーのプランと利用回数を取得する (Admin SDK)"""
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
    st.sidebar.write(f"残り回数: {st.session_state.remaining_uses}回 ({st.session_state.plan}プラン)")
    return True

def update_user_uses_in_firestore_rest(uid, id_token, uses_to_deduct=1):
    """Firestoreのユーザー利用回数を減らす (Admin SDKを使用)"""
    global db
    doc_ref = db.collection('users').document(uid)
    try:
        doc_ref.update({
            "remaining_uses": firestore.Increment(-uses_to_deduct),
            "last_used_at": firestore.SERVER_TIMESTAMP
        })
        st.session_state.remaining_uses -= uses_to_deduct
        st.sidebar.write(f"残り回数: {st.session_state.remaining_uses}回 ({st.session_state.plan}プラン)")
        return True
    except Exception as e:
        st.error(f"利用回数の更新に失敗しました: {e}")
        st.error(f"利用回数更新エラー詳細: {e}")
        return False

# Firebase Storageへの画像アップロード関数
def upload_image_to_firebase_storage(uid, image_bytes_io, filename):
    """
    画像をFirebase Storageにアップロードし、公開URLを返す。
    Args:
        uid (str): ユーザーID (画像をユーザーフォルダに整理するため)
        image_bytes_io (io.BytesIO): PIL ImageをBytesIOに変換したデータ
        filename (str): 保存するファイル名 (例: banner_A_YYYYMMDDHHMMSS.png)
    Returns:
        str: アップロードされた画像の公開URL, またはNone (失敗時)
    """
    try:
        bucket = storage.bucket() # Firebase Admin SDKで初期化されたStorageバケットを取得
        blob = bucket.blob(f"users/{uid}/diagnoses_images/{filename}")
        
        image_bytes_io.seek(0)
        blob.upload_from_file(image_bytes_io, content_type="image/png")

        blob.make_public() # 公開アクセスを許可 (Storageのルール設定も必要)
        
        return blob.public_url
    except Exception as e:
        st.error(f"Firebase Storageへの画像アップロードに失敗しました: {e}")
        st.error(f"Storageアップロードエラー詳細: {e}")
        return None

# 診断記録をFirestoreに書き込む関数 (image_urlを引数に追加)
def add_diagnosis_record_to_firestore(uid, id_token, record_data, image_url=None):
    """
    ユーザーの診断記録をFirestoreのdiagnosesサブコレクションに追加する。
    Args:
        uid (str): ユーザーID
        id_token (str): ユーザーのIDトークン
        record_data (dict): 記録したい診断データ
        image_url (str, optional): アップロードされた画像のURL. Defaults to None.
    Returns:
        bool: 成功すればTrue, 失敗すればFalse
    """
    global db
    doc_ref = db.collection('users').document(uid).collection('diagnoses').document()
    
    try:
        if image_url:
            record_data["image_url"] = image_url
        record_data["created_at"] = firestore.SERVER_TIMESTAMP
        
        doc_ref.set(record_data) 
        return True
    except Exception as e:
        st.error(f"診断記録のFirestore保存に失敗しました: {e}")
        st.error(f"Firestore記録エラー詳細: {e}")
        return False


# --- StreamlitのUI表示と認証フロー ---
def login_page():
    """Streamlit上にログイン画面を表示する関数"""
    st.title("🔐 バナスコAI ログイン")
    st.markdown("アカウント情報入力フォームの機能を利用するにはログインが必要です。")

    email = st.text_input("メールアドレス", key="login_email")
    password = st.text_input("パスワード", type="password", key="login_password")

    login_col, create_col = st.columns(2)

    with login_col:
        if st.button("ログイン", key="login_button"):
            with st.spinner("ログイン中..."):
                try:
                    user_info = sign_in_with_email_and_password(email, password)
                    st.session_state["user"] = user_info["localId"]
                    st.session_state["email"] = user_info["email"]
                    st.session_state["logged_in"] = True
                    st.session_state["id_token"] = user_info["idToken"]
                    
                    get_user_data_from_firestore(st.session_state["user"], st.session_state["id_token"])

                    st.success(f"ログインしました: {user_info['email']}")
                    st.rerun()
                except requests.exceptions.HTTPError as e:
                    error_json = e.response.json()
                    error_code = error_json.get("error", {}).get("message", "Unknown error")
                    if error_code == "EMAIL_NOT_FOUND" or error_code == "INVALID_PASSWORD":
                        st.error("ログインに失敗しました。メールアドレスまたはパスワードが間違っています。")
                    elif error_code == "USER_DISABLED":
                        st.error("このアカウントは無効化されています。")
                    else:
                        st.error(f"ログイン中にエラーが発生しました: {error_code}")
                except Exception as e:
                    st.error(f"予期せぬエラーが発生しました: {e}")

    with create_col:
        if st.button("アカウント作成", key="create_account_button"):
            with st.spinner("アカウント作成中..."):
                try:
                    user_info = create_user_with_email_and_password(email, password)
                    st.session_state["user"] = user_info["localId"]
                    st.session_state["email"] = user_info["email"]
                    st.session_state["logged_in"] = True
                    st.session_state["id_token"] = user_info["idToken"]

                    get_user_data_from_firestore(st.session_state["user"], st.session_state["id_token"])
                    
                    st.success(f"アカウント '{user_info['email']}' を作成しました。そのままログインしました。")
                    st.rerun()
                except requests.exceptions.HTTPError as e:
                    error_json = e.response.json()
                    error_code = error_json.get("error", {}).get("message", "Unknown error")
                    if error_code == "EMAIL_EXISTS":
                        st.error("このメールアドレスは既に使用されています。")
                    elif error_code == "WEAK_PASSWORD":
                        st.error("パスワードが弱すぎます（6文字以上必要）。")
                    else:
                        st.error(f"アカウント作成中にエラーが発生しました: {error_code}")
                except Exception as e:
                    st.error(f"予期せぬエラーが発生しました: {e}")

def logout():
    """ユーザーをログアウトさせる関数"""
    if st.session_state.get("logged_in"):
        keys_to_clear = ["user", "email", "logged_in", "id_token", "plan", "remaining_uses",
                         "score_a", "comment_a", "yakujihou_a", "score_b", "comment_b", "yakujihou_b",
                         "ai_response_a", "ai_response_b"]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.success("ログアウトしました。")
        st.rerun()

def check_login():
    """
    ユーザーのログイン状態をチェックし、未ログインならログインページを表示してアプリの実行を停止する。
    Firestoreの残り回数も確認し、サイドバーに表示する。
    """
    if not st.session_state.get("firebase_admin_initialized"):
        st.stop() 

    if st.session_state.get("logged_in"):
        st.sidebar.write(f"ようこそ, {st.session_state.get('email')}!")
        
        if "remaining_uses" not in st.session_state or st.session_state.remaining_uses is None:
            if st.session_state.id_token:
                get_user_data_from_firestore(st.session_state["user"], st.session_state.id_token)
            else:
                st.sidebar.warning("IDトークンがありません。ログインし直してください。")
                logout()
                return
        
        st.sidebar.write(f"残り回数: {st.session_state.remaining_uses}回 ({st.session_state.plan}プラン)")
        st.sidebar.button("ログアウト", on_click=logout)

    if not st.session_state.get("logged_in"):
        login_page()
        st.stop()
