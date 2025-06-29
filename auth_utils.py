# auth_utils.py
import streamlit as st
import os
import requests
from dotenv import load_dotenv
# firebase_admin は使用しないため、インポートを削除
# import firebase_admin
# from firebase_admin import credentials, firestore
# jsonモジュールも不要になる
# import json
from datetime import datetime # Firestore REST APIでタイムスタンプを扱うために追加


# .envファイルから環境変数を読み込む
load_dotenv()

# Firebase Authentication REST APIに必要なAPIキーを取得
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")

if not FIREBASE_API_KEY:
    st.error("Firebase APIキーが.envファイルに見つかりません。")
    st.stop()

# Firebase Authentication REST APIのエンドポイントベースURL
FIREBASE_AUTH_BASE_URL = "https://identitytoolkit.googleapis.com/v1/accounts:"
# Firestore REST APIのエンドポイントベースURL
# プロジェクトIDが別途必要
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID") # .envに設定されているはず

if not FIREBASE_PROJECT_ID:
    st.error("FirebaseプロジェクトIDが.envファイルに見つかりません。")
    st.stop()

FIREBASE_FIRESTORE_BASE_URL = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/"


# Streamlitのセッションステートを初期化 (初回ロード時のみ)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "email" not in st.session_state:
    st.session_state.email = None
if "id_token" not in st.session_state: # ✅ 追加: IDトークンを保存
    st.session_state.id_token = None
if "plan" not in st.session_state:
    st.session_state.plan = "Guest"
if "remaining_uses" not in st.session_state:
    st.session_state.remaining_uses = 0
if "firebase_initialized" not in st.session_state: # Auth APIのみ使うため、初期化は成功とみなす
    st.session_state.firebase_initialized = True


# --- Firebase Authentication REST APIの関数 ---
def sign_in_with_email_and_password(email, password):
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


# --- Firestore REST APIの操作関数 ---
def get_user_data_from_firestore_rest(uid, id_token):
    """Firestore REST APIからユーザーのプランと利用回数を取得する (IDトークン認証)"""
    url = f"{FIREBASE_FIRESTORE_BASE_URL}users/{uid}?key={FIREBASE_API_KEY}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {id_token}" # ✅ 認証ヘッダーを追加
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        doc_data = response.json()
        if "fields" in doc_data:
            st.session_state.plan = doc_data["fields"].get("plan", {}).get("stringValue", "Free")
            st.session_state.remaining_uses = int(doc_data["fields"].get("remaining_uses", {}).get("integerValue", 0))
            return True
        else:
            # ドキュメントが存在しないが、200 OKが返ってきた場合 (空のドキュメントパスなど)
            st.session_state.plan = "Free"
            st.session_state.remaining_uses = 5 
            create_user_firestore_rest(uid, id_token, st.session_state.email, st.session_state.plan, st.session_state.remaining_uses)
            return True
    elif response.status_code == 404: # ドキュメントが存在しない
        st.session_state.plan = "Free"
        st.session_state.remaining_uses = 5
        create_user_firestore_rest(uid, id_token, st.session_state.email, st.session_state.plan, st.session_state.remaining_uses)
        return True
    else:
        st.error(f"Firestoreデータ取得エラー: {response.status_code} - {response.text}")
        # st.error(response.json()) # デバッグ用
        return False

def create_user_firestore_rest(uid, id_token, email, plan, remaining_uses):
    """Firestore REST APIで新規ユーザーのドキュメントを作成する (IDトークン認証)"""
    url = f"{FIREBASE_FIRESTORE_BASE_URL}users?documentId={uid}&key={FIREBASE_API_KEY}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {id_token}" # ✅ 認証ヘッダーを追加
    }
    data = {
        "fields": {
            "email": {"stringValue": email},
            "plan": {"stringValue": plan},
            "remaining_uses": {"integerValue": remaining_uses},
            "created_at": {"timestampValue": datetime.utcnow().isoformat() + "Z"}
        }
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

def update_user_uses_in_firestore_rest(uid, id_token, uses_to_deduct=1):
    """Firestore REST APIでユーザーの利用回数を減らす (IDトークン認証)"""
    # PATCHメソッドで更新。Firestore REST APIのIncrementは直接サポートされていないため、
    # Read-Modify-Writeのパターンを使用します (まずは読み込んでから書き込む)
    
    # 1. 現在の残り回数を取得
    url_get = f"{FIREBASE_FIRESTORE_BASE_URL}users/{uid}?key={FIREBASE_API_KEY}"
    headers_get = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {id_token}"
    }
    get_response = requests.get(url_get, headers=headers_get)
    get_response.raise_for_status()
    current_data = get_response.json()["fields"]
    
    current_uses = int(current_data.get("remaining_uses", {}).get("integerValue", 0))
    new_uses = current_uses - uses_to_deduct

    # 2. 更新するフィールドだけを指定してPATCHリクエストを送信
    url_patch = f"{FIREBASE_FIRESTORE_BASE_URL}users/{uid}?updateMask.fieldPaths=remaining_uses&updateMask.fieldPaths=last_used_at&key={FIREBASE_API_KEY}"
    headers_patch = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {id_token}" # ✅ 認証ヘッダーを追加
    }
    data = {
        "fields": {
            "remaining_uses": {"integerValue": new_uses},
            "last_used_at": {"timestampValue": datetime.utcnow().isoformat() + "Z"}
        }
    }
    response = requests.patch(url_patch, headers=headers_patch, json=data)
    response.raise_for_status()
    
    st.session_state.remaining_uses = new_uses
    st.sidebar.write(f"残り回数: {st.session_state.remaining_uses}回 ({st.session_state.plan}プラン)")
    return True
    

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
                    st.session_state["id_token"] = user_info["idToken"] # ✅ IDトークンを保存
                    
                    # ログイン成功時、Firestoreからユーザーデータを読み込む (IDトークンを渡す)
                    get_user_data_from_firestore_rest(st.session_state["user"], st.session_state["id_token"])

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
                    st.session_state["user"] = user_info["localId"] # 新規作成時もIDを保存
                    st.session_state["email"] = user_info["email"]
                    st.session_state["logged_in"] = True # 作成したら即ログイン状態にする
                    st.session_state["id_token"] = user_info["idToken"] # ✅ IDトークンを保存

                    # 新規アカウント作成成功時、Firestoreにドキュメントを自動作成 (IDトークンを渡す)
                    # get_user_data_from_firestore_rest 内でドキュメントが存在しない場合に作成されるため、直接呼び出し
                    get_user_data_from_firestore_rest(st.session_state["user"], st.session_state["id_token"])
                    
                    st.success(f"アカウント '{user_info['email']}' を作成しました。そのままログインしました。")
                    st.rerun() # 作成後、アプリを再実行してメインコンテンツを表示
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
        # セッション情報をクリア
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
    # このバージョンではAdmin SDKの初期化は不要になったため、関連チェックを削除
    # st.session_state.firebase_initialized は常にTrueになる想定

    # サイドバーに現在のユーザー名とログアウトボタン、残り回数を配置
    if st.session_state.get("logged_in"):
        st.sidebar.write(f"ようこそ, {st.session_state.get('email')}!")
        
        # ログイン済みだが残り回数がまだ読み込まれていない場合、読み込む (IDトークンを渡す)
        if "remaining_uses" not in st.session_state or st.session_state.remaining_uses is None:
            # IDトークンがない場合は読み込みをスキップ（異常状態）
            if st.session_state.id_token:
                get_user_data_from_firestore_rest(st.session_state["user"], st.session_state.id_token)
            else:
                st.sidebar.warning("IDトークンがありません。ログインし直してください。")
                logout() # IDトークンがない場合はログアウトして再ログインを促す
                return # ログアウトしたのでここで終了
        
        st.sidebar.write(f"残り回数: {st.session_state.remaining_uses}回 ({st.session_state.plan}プラン)")
        st.sidebar.button("ログアウト", on_click=logout)

    # ログインしていない場合は、ログインページを表示してアプリの実行を停止
    if not st.session_state.get("logged_in"):
        login_page()
        st.stop()
