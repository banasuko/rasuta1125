# auth_utils.py
import streamlit as st
import os
import requests # ✅ 追加: requestsモジュールをインポート
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# Firebase設定を環境変数から取得
# REST APIを使用するため、主にapiKeyが必要です
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")

if not FIREBASE_API_KEY:
    st.error("Firebase APIキーが.envファイルに見つかりません。")
    st.stop()

# Firebase Authentication REST APIのエンドポイントベースURL
# Googleの公式ドキュメントに基づいて構築
FIREBASE_AUTH_BASE_URL = "https://identitytoolkit.googleapis.com/v1/accounts:"

# Streamlitのセッションステートを初期化
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "email" not in st.session_state:
    st.session_state.email = None
if "firebase_initialized" not in st.session_state:
    st.session_state.firebase_initialized = True # REST APIなので初期化自体はエラーになりにくい


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
    response.raise_for_status() # HTTPエラーが発生した場合に例外を発生させる
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
    response.raise_for_status() # HTTPエラーが発生した場合に例外を発生させる
    return response.json()


def login_page():
    """Streamlit上にログイン画面を表示する関数"""
    st.title("🔐 バナスコAI ログイン")
    st.markdown("アカウント情報入力フォームの機能を利用するにはログインが必要です。")

    email = st.text_input("メールアドレス", key="login_email")
    password = st.text_input("パスワード", type="password", key="login_password")

    login_col, create_col = st.columns(2)

    with login_col:
        if st.button("ログイン", key="login_button"):
            try:
                user_info = sign_in_with_email_and_password(email, password)
                st.session_state["user"] = user_info["localId"]
                st.session_state["email"] = user_info["email"]
                st.session_state["logged_in"] = True
                st.success(f"ログインしました: {user_info['email']}")
                st.rerun() # ログイン後、アプリを再実行してメインコンテンツを表示
            except requests.exceptions.HTTPError as e:
                error_code = e.response.json().get("error", {}).get("message", "Unknown error")
                if error_code == "EMAIL_NOT_FOUND" or error_code == "INVALID_PASSWORD":
                    st.error("ログインに失敗しました。メールアドレスまたはパスワードが間違っています。")
                elif error_code == "USER_DISABLED":
                    st.error("このアカウントは無効化されています。")
                else:
                    st.error(f"ログイン中にエラーが発生しました: {error_code}")
                    # st.error(e.response.json()) # デバッグ用
            except Exception as e:
                st.error(f"予期せぬエラーが発生しました: {e}")

    with create_col:
        if st.button("アカウント作成", key="create_account_button"):
            try:
                user_info = create_user_with_email_and_password(email, password)
                st.success(f"アカウント '{user_info['email']}' を作成しました。ログインしてください。")
            except requests.exceptions.HTTPError as e:
                error_code = e.response.json().get("error", {}).get("message", "Unknown error")
                if error_code == "EMAIL_EXISTS":
                    st.error("このメールアドレスは既に使用されています。")
                elif error_code == "WEAK_PASSWORD":
                    st.error("パスワードが弱すぎます（6文字以上必要）。")
                else:
                    st.error(f"アカウント作成中にエラーが発生しました: {error_code}")
                    # st.error(e.response.json()) # デバッグ用
            except Exception as e:
                st.error(f"予期せぬエラーが発生しました: {e}")

def logout():
    """ユーザーをログアウトさせる関数"""
    if st.session_state.get("logged_in"):
        # Firebase REST API にはログアウトのための直接的なエンドポイントはないため、
        # セッション情報をクリアすることで「クライアント側でログアウト状態にする」
        keys_to_clear = ["user", "email", "logged_in", "score_a", "comment_a", "yakujihou_a",
                         "score_b", "comment_b", "yakujihou_b", "ai_response_a", "ai_response_b"]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.success("ログアウトしました。")
        st.rerun() # ログアウト後、アプリを再実行してログイン画面に戻る

def check_login():
    """
    ユーザーのログイン状態をチェックし、未ログインならログインページを表示してアプリの実行を停止する。
    この関数は、保護したいStreamlitアプリの各ページの冒頭で呼び出す。
    """
    # サイドバーに現在のユーザー名とログアウトボタンを配置
    if st.session_state.get("logged_in"):
        st.sidebar.write(f"ようこそ, {st.session_state.get('email')}!")
        st.sidebar.button("ログアウト", on_click=logout)

    # ログインしていない場合は、ログインページを表示してアプリの実行を停止
    if not st.session_state.get("logged_in"):
        login_page()
        st.stop() # ここでメインアプリの実行を停止
