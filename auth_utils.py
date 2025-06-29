
# auth_utils.py
import streamlit as st
import os
import pyrebase4
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# Firebase設定を環境変数から取得
firebaseConfig = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID"),
    "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID")
}

# Firebaseを初期化
# 初期化が成功したかどうかをセッションステートに保存
try:
    firebase = pyrebase4.initialize_app(firebaseConfig)
    auth = firebase.auth()
    if "firebase_initialized" not in st.session_state:
        st.session_state.firebase_initialized = True
except Exception as e:
    st.error(f"Firebaseの初期化に失敗しました。`.env`ファイルの設定、またはFirebaseConfigの内容を確認してください: {e}")
    st.stop() # Firebase初期化失敗時はここでアプリの実行を停止


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
                # Firebaseでサインイン
                user = auth.sign_in_with_email_and_password(email, password)
                # ログイン成功時、セッションステートに情報を保存
                st.session_state["user"] = user["localId"]
                st.session_state["email"] = user["email"]
                st.session_state["logged_in"] = True
                st.success(f"ログインしました: {user['email']}")
                st.rerun() # ログイン後、アプリを再実行してメインコンテンツを表示
            except Exception as e:
                st.error("ログインに失敗しました。メールアドレスまたはパスワードが間違っています。")
                # より詳細なエラーを見たい場合は以下の行を有効化
                # st.error(e)

    with create_col:
        if st.button("アカウント作成", key="create_account_button"):
            try:
                # Firebaseでユーザー作成
                user = auth.create_user_with_email_and_password(email, password)
                st.success(f"アカウント '{email}' を作成しました。ログインしてください。")
            except Exception as e:
                st.error("アカウント作成に失敗しました。既に存在するメールアドレスか、パスワードが不正です（6文字以上必要）。")
                # より詳細なエラーを見たい場合は以下の行を有効化
                # st.error(e)

def logout():
    """ユーザーをログアウトさせる関数"""
    if st.session_state.get("logged_in"): # ログイン状態であればログアウト処理を実行
        try:
            auth.sign_out()
            # セッションステートのログイン情報をクリア
            keys_to_clear = ["user", "email", "logged_in", "score_a", "comment_a", "yakujihou_a",
                             "score_b", "comment_b", "yakujihou_b", "ai_response_a", "ai_response_b"]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("ログアウトしました。")
            st.rerun() # ログアウト後、アプリを再実行してログイン画面に戻る
        except Exception as e:
            st.error(f"ログアウト中にエラーが発生しました: {e}")
            # エラー時もセッション情報をクリアしてログイン画面に戻す試み
            keys_to_clear = ["user", "email", "logged_in"]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

def check_login():
    """
    ユーザーのログイン状態をチェックし、未ログインならログインページを表示してアプリの実行を停止する。
    この関数は、保護したいStreamlitアプリの各ページの冒頭で呼び出す。
    """
    # サイドバーに現在のユーザー名とログアウトボタンを配置
    if st.session_state.get("logged_in"):
        st.sidebar.write(f"ようこそ, {st.session_state.get('email')}!")
        st.sidebar.button("ログアウト", on_click=logout)

    # ログインしていない、またはFirebase初期化エラーの場合は、ログインページを表示してアプリの実行を停止
    if not st.session_state.get("logged_in") or not st.session_state.get("firebase_initialized"):
        login_page()
        st.stop() # ここでメインアプリの実行を停止
