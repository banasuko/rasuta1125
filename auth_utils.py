import os
import requests
from dotenv import load_dotenv
# firebase_admin は使用しないため、インポートを削除
# import firebase_admin
# from firebase_admin import credentials, firestore
# jsonモジュールも不要になる
# import json
from datetime import datetime # Firestore REST APIでタイムスタンプを扱うために追加
import firebase_admin
from firebase_admin import credentials, firestore, storage # ✅ storage を追加
import json
from datetime import datetime


# .envファイルから環境変数を読み込む
@@ -24,7 +22,6 @@
# Firebase Authentication REST APIのエンドポイントベースURL
FIREBASE_AUTH_BASE_URL = "https://identitytoolkit.googleapis.com/v1/accounts:"
# Firestore REST APIのエンドポイントベースURL
# プロジェクトIDが別途必要
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID") # .envに設定されているはず

if not FIREBASE_PROJECT_ID:
@@ -34,14 +31,52 @@
FIREBASE_FIRESTORE_BASE_URL = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/"


# --- Firebase Admin SDKの初期化 (Firestore & Storage用) ---
try:
    if "firebase_admin_initialized" not in st.session_state:
        admin_project_id = os.getenv("FIREBASE_PROJECT_ID_ADMIN")
        admin_private_key = os.getenv("FIREBASE_PRIVATE_KEY_ADMIN")
        admin_client_email = os.getenv("FIREBASE_CLIENT_EMAIL_ADMIN")
        # Storageのバケット名も必要 (通常は projectId.appspot.com)
        storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET") 

        if not admin_project_id or not admin_private_key or not admin_client_email or not storage_bucket:
            st.error("Firebase Admin SDKの環境変数（PROJECT_ID_ADMIN, PRIVATE_KEY_ADMIN, CLIENT_EMAIL_ADMIN, STORAGE_BUCKET）が不足しています。Secretsを確認してください。")
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
        # Storageバケット名を指定して初期化
        firebase_admin.initialize_app(cred, {'storageBucket': storage_bucket})
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
if "id_token" not in st.session_state: # ✅ 追加: IDトークンを保存
if "id_token" not in st.session_state:
    st.session_state.id_token = None
if "plan" not in st.session_state:
    st.session_state.plan = "Guest"
@@ -77,94 +112,100 @@ def create_user_with_email_and_password(email, password):
    return response.json()


# --- Firestore REST APIの操作関数 ---
# --- Firestoreの操作関数 (Admin SDKを使用) ---
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
    """Firestoreからユーザーのプランと利用回数を取得する (IDトークン認証)"""
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
        create_user_firestore_rest(uid, id_token, st.session_state.email, st.session_state.plan, st.session_state.remaining_uses)
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
    """Firestoreのユーザー利用回数を減らす (IDトークン認証)"""
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
    else:
        st.error(f"Firestoreデータ取得エラー: {response.status_code} - {response.text}")
        # st.error(response.json()) # デバッグ用
    except Exception as e:
        st.error(f"利用回数の更新に失敗しました: {e}")
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
# ✅ 追加: Firebase Storageへの画像アップロード関数
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
        # ユーザーIDごとのフォルダに画像を保存
        blob = bucket.blob(f"users/{uid}/diagnoses_images/{filename}")
        
        # BytesIOから直接アップロード
        image_bytes_io.seek(0) # ストリームの先頭に戻す
        blob.upload_from_file(image_bytes_io, content_type="image/png") # content_typeを明示

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
        # 公開アクセスを許可 (Storageのルール設定も必要)
        # 通常は認証されたアクセスが推奨されるが、ここでは公開URLを取得
        blob.make_public() 
        
        return blob.public_url
    except Exception as e:
        st.error(f"Firebase Storageへの画像アップロードに失敗しました: {e}")
        return None

# ✅ 追加: 診断記録をFirestoreに書き込む関数 (image_urlを引数に追加)
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
        # 記録データに画像URLとタイムスタンプを追加
        if image_url:
            record_data["image_url"] = image_url
        record_data["created_at"] = firestore.SERVER_TIMESTAMP # Firestore側でタイムスタンプを生成

        doc_ref.set(record_data) 
        return True
    except Exception as e:
        st.error(f"診断記録のFirestore保存に失敗しました: {e}")
        return False


# --- StreamlitのUI表示と認証フロー ---
def login_page():
@@ -185,9 +226,8 @@ def login_page():
                    st.session_state["user"] = user_info["localId"]
                    st.session_state["email"] = user_info["email"]
                    st.session_state["logged_in"] = True
                    st.session_state["id_token"] = user_info["idToken"] # ✅ IDトークンを保存
                    st.session_state["id_token"] = user_info["idToken"]

                    # ログイン成功時、Firestoreからユーザーデータを読み込む (IDトークンを渡す)
                    get_user_data_from_firestore_rest(st.session_state["user"], st.session_state["id_token"])

                    st.success(f"ログインしました: {user_info['email']}")
@@ -209,17 +249,15 @@ def login_page():
            with st.spinner("アカウント作成中..."):
                try:
                    user_info = create_user_with_email_and_password(email, password)
                    st.session_state["user"] = user_info["localId"] # 新規作成時もIDを保存
                    st.session_state["user"] = user_info["localId"]
                    st.session_state["email"] = user_info["email"]
                    st.session_state["logged_in"] = True # 作成したら即ログイン状態にする
                    st.session_state["id_token"] = user_info["idToken"] # ✅ IDトークンを保存
                    st.session_state["logged_in"] = True
                    st.session_state["id_token"] = user_info["idToken"]

                    # 新規アカウント作成成功時、Firestoreにドキュメントを自動作成 (IDトークンを渡す)
                    # get_user_data_from_firestore_rest 内でドキュメントが存在しない場合に作成されるため、直接呼び出し
                    get_user_data_from_firestore_rest(st.session_state["user"], st.session_state["id_token"])

                    st.success(f"アカウント '{user_info['email']}' を作成しました。そのままログインしました。")
                    st.rerun() # 作成後、アプリを再実行してメインコンテンツを表示
                    st.rerun()
                except requests.exceptions.HTTPError as e:
                    error_json = e.response.json()
                    error_code = error_json.get("error", {}).get("message", "Unknown error")
@@ -235,7 +273,6 @@ def login_page():
def logout():
    """ユーザーをログアウトさせる関数"""
    if st.session_state.get("logged_in"):
        # セッション情報をクリア
        keys_to_clear = ["user", "email", "logged_in", "id_token", "plan", "remaining_uses",
                         "score_a", "comment_a", "yakujihou_a", "score_b", "comment_b", "yakujihou_b",
                         "ai_response_a", "ai_response_b"]
@@ -250,27 +287,25 @@ def check_login():
    ユーザーのログイン状態をチェックし、未ログインならログインページを表示してアプリの実行を停止する。
    Firestoreの残り回数も確認し、サイドバーに表示する。
    """
    # このバージョンではAdmin SDKの初期化は不要になったため、関連チェックを削除
    # st.session_state.firebase_initialized は常にTrueになる想定
    # Admin SDKの初期化状態を確認
    if not st.session_state.get("firebase_admin_initialized"):
        st.stop() 

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
                logout()
                return

        st.sidebar.write(f"残り回数: {st.session_state.remaining_uses}回 ({st.session_state.plan}プラン)")
        st.sidebar.button("ログアウト", on_click=logout)

    # ログインしていない場合は、ログインページを表示してアプリの実行を停止
    if not st.session_state.get("logged_in"):
        login_page()
        st.stop()
