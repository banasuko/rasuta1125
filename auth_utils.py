# auth_utils.py
import streamlit as st
import os
import pyrebase
import requests # Firebase REST APIで使用
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# Firebase設定を環境変数から取得
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")

# Firebase Auth REST APIのエンドポイントベースURL
FIREBASE_AUTH_BASE_URL = "https://identitytoolkit.googleapis.com/v1/accounts:"

# Firebase Admin SDK (Firestore用) の設定
# Firestoreを使うためにFirebase Admin SDKの設定も必要
# Admin SDKはサービスアカウントの認証情報を使用します
# Streamlit SecretsにサービスアカウントキーのJSONを文字列として保存するか、
# .envから読み込むか、別の安全な方法が必要です。
# 今回は簡単のため、FirebaseConfigのprojectIdを利用して初期化を試みますが
# 本格的なAdmin SDK利用にはサービスアカウントキーのJSONが必要です。
# pyrebase(client SDK)とは異なる初期化方法になります。
# そのため、ここではpyrebaseのFirestore機能を利用します (ただしこれは非推奨)

# Pyrebaseの初期化 (AuthとFirestoreの両方に対応)
firebaseConfig = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID"),
    "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID")
}

try:
    firebase = pyrebase.initialize_app(firebaseConfig) # pyrebaseを再利用
    auth = firebase.auth()
    db = firebase.database() # Realtime DatabaseではなくFirestoreの場合は client = firebase.firestore() を使うが、
                              # pyrebaseのfirestore()はpyrebase4で導入された新機能。
                              # pyrebaseではadmin SDKが必要になるか、あるいはclient SDKとしてはRealtime DBがメイン。
                              # ここでは、Firebase REST APIでAuthを扱い、Firestoreは別途Admin SDKで。
                              # OR: pyrebaseを諦め、Firestoreは直接Admin SDKで、AuthはREST APIでやるのが cleanest.
                              # 上記方針でAuthはREST APIに切り替わったので、pyrebaseはAuthではもう使わない。
                              # Firestoreの操作のためにpyrebaseを再導入すると依存関係エラーが再発する可能性が高い。
                              # => ここではFirestoreの操作は、Python Admin SDKに切り替える。

    # Firebase Admin SDKの初期化 (Firestore用)
    # サービスアカウントキーのJSONファイルパスをStreamlit Secretsから取得する想定
    # 例: st.secrets["FIREBASE_ADMIN_SDK_CONFIG"] にJSON文字列が保存されている
    # またはファイルとして配置し、そのパスを指定
    # 今はローカルテスト用にダミーで初期化を試みるが、本番ではService Account JSON必須
    # import firebase_admin
    # from firebase_admin import credentials, firestore
    #
    # # この cred.json はFirebaseコンソールからダウンロードしたもの
    # # 本番デプロイ時は Streamlit Secrets で安全に管理する必要あり
    # # st.secrets["firebase_admin_sdk_config"] を使うのが推奨
    # if "firebase_admin_cred" not in st.session_state:
    #     try:
    #         # 環境変数またはSecretsからJSON文字列を読み込む
    #         service_account_info = json.loads(os.getenv("FIREBASE_ADMIN_SDK_CONFIG"))
    #         cred = credentials.Certificate(service_account_info)
    #         firebase_admin.initialize_app(cred)
    #         st.session_state.firebase_admin_cred = True
    #     except Exception as e:
    #         st.error(f"Firebase Admin SDKの初期化に失敗しました。サービスアカウントキーを確認してください: {e}")
    #         st.stop()
    # db = firestore.client() # Firestoreクライアント

    # セッションステートを初期化
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "email" not in st.session_state:
        st.session_state.email = None
    if "plan" not in st.session_state: # プラン情報
        st.session_state.plan = "Guest"
    if "remaining_uses" not in st.session_state: # 残り回数
        st.session_state.remaining_uses = 0
    if "firebase_initialized" not in st.session_state:
        st.session_state.firebase_initialized = True

except Exception as e:
    st.error(f"Firebaseの初期化に失敗しました。`.env`ファイルの設定、またはFirebaseConfigの内容を確認してください: {e}")
    st.stop()


# Firestore操作のための Admin SDK
import firebase_admin # ✅ 追加
from firebase_admin import credentials, firestore # ✅ 追加
import json # ✅ 追加

# サービスアカウントキーの設定
# これはStreamlit Secretsに保存することを強く推奨します
# secrets.tomlに [firebase_admin] service_account_key = "{...JSONキーをここにペースト...}"
# または環境変数 FIREBASE_ADMIN_SDK_CONFIG にJSON文字列を保存
try:
    if "firebase_admin_initialized" not in st.session_state:
        # 環境変数からJSON文字列を読み込み、Python辞書に変換
        service_account_info_str = os.getenv("FIREBASE_ADMIN_SDK_CONFIG")
        if not service_account_info_str:
            st.error("環境変数 'FIREBASE_ADMIN_SDK_CONFIG' が設定されていません。Firebase Admin SDKのサービスアカウントキーが必要です。")
            st.stop()
        
        service_account_info = json.loads(service_account_info_str)
        
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred)
        st.session_state.firebase_admin_initialized = True
        db = firestore.client() # Firestoreクライアントを初期化
except Exception as e:
    st.error(f"Firebase Admin SDKの初期化に失敗しました。サービスアカウントキーを確認してください: {e}")
    st.stop()


def get_user_data_from_firestore(uid):
    """Firestoreからユーザーのプランと利用回数を取得する"""
    doc_ref = db.collection('users').document(uid)
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        st.session_state.plan = data.get("plan", "Free")
        st.session_state.remaining_uses = data.get("remaining_uses", 0)
    else:
        # ドキュメントが存在しない場合（例：新規作成されたばかりのユーザー）
        st.session_state.plan = "Free"
        st.session_state.remaining_uses = 5 # デフォルトの無料回数
        # Firestoreに新規ドキュメントを作成
        doc_ref.set({
            "email": st.session_state.email,
            "plan": st.session_state.plan,
            "remaining_uses": st.session_state.remaining_uses,
            "created_at": firestore.SERVER_TIMESTAMP # 作成日時を追加
        })
    st.sidebar.write(f"残り回数: {st.session_state.remaining_uses}回 ({st.session_state.plan}プラン)")


def update_user_uses_in_firestore(uid, uses_to_deduct=1):
    """Firestoreのユーザー利用回数を減らす"""
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
        return False


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
                
                # ログイン成功時、Firestoreからユーザーデータを読み込む
                get_user_data_from_firestore(st.session_state["user"])

                st.success(f"ログインしました: {user_info['email']}")
                st.rerun()
            except requests.exceptions.HTTPError as e:
                error_code = e.response.json().get("error", {}).get("message", "Unknown error")
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
            try:
                user_info = create_user_with_email_and_password(email, password)
                
                # アカウント作成成功時、Firestoreに新規ユーザーデータを書き込む
                # ただし、AuthのsignUpが完了した直後ではFirestoreのドキュメント作成はまだしない
                # ログイン時にget_user_data_from_firestoreで自動作成されるようにする
                
                st.success(f"アカウント '{user_info['email']}' を作成しました。ログインしてください。")
            except requests.exceptions.HTTPError as e:
                error_code = e.response.json().get("error", {}).get("message", "Unknown error")
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
        keys_to_clear = ["user", "email", "logged_in", "plan", "remaining_uses",
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
    # Firebase Admin SDKの初期化状態を確認
    if "firebase_admin_initialized" not in st.session_state:
        st.error("Firebase Admin SDKが初期化されていません。サービスアカウントキーが正しく設定されているか確認してください。")
        st.stop() # 初期化エラーならここで停止

    # サイドバーに現在のユーザー名とログアウトボタン、残り回数を配置
    if st.session_state.get("logged_in"):
        st.sidebar.write(f"ようこそ, {st.session_state.get('email')}!")
        
        # ログイン済みだが残り回数がまだ読み込まれていない場合、読み込む
        if "remaining_uses" not in st.session_state or st.session_state.remaining_uses is None:
            get_user_data_from_firestore(st.session_state["user"])
        
        st.sidebar.write(f"残り回数: {st.session_state.remaining_uses}回 ({st.session_state.plan}プラン)")
        st.sidebar.button("ログアウト", on_click=logout)

    # ログインしていない場合は、ログインページを表示してアプリの実行を停止
    if not st.session_state.get("logged_in"):
        login_page()
        st.stop() # ここでメインアプリの実行を停止
