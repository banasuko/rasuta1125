import streamlit as st
import os
import requests
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore, storage
import json
from datetime import datetime, timezone
import stripe # ★Stripeライブラリをインポート

# .envファイルから環境変数を読み込む
load_dotenv()

# --- グローバル変数の定義 ---
db = None

# --- ★★★ここから変更★★★ ---
# --- 環境変数の読み込みとチェック ---
FIREBASE_API_KEY = os.getenv("FIREBASE_WEB_API_KEY")
STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")
# Stripeと安全なFirebase認証用の変数を追加
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")


# 必須の環境変数が設定されているかチェック
missing_vars = []
if not FIREBASE_API_KEY: missing_vars.append("FIREBASE_WEB_API_KEY")
if not STORAGE_BUCKET: missing_vars.append("FIREBASE_STORAGE_BUCKET")
# 新しい必須変数をチェックリストに追加
if not STRIPE_SECRET_KEY: missing_vars.append("STRIPE_SECRET_KEY")
if not FIREBASE_SERVICE_ACCOUNT_JSON: missing_vars.append("FIREBASE_SERVICE_ACCOUNT_JSON")


if missing_vars:
    st.error(f"❌ 必須の環境変数が不足しています: {', '.join(missing_vars)}。Streamlit CloudのSecretsを確認してください。")
    st.stop()

# --- APIキーの設定 ---
stripe.api_key = STRIPE_SECRET_KEY

# --- Firebase Admin SDKの初期化 (より安全な方法に変更) ---
try:
    if not firebase_admin._apps:
        # 環境変数からJSON文字列を読み込み、辞書に変換
        service_account_info = json.loads(FIREBASE_SERVICE_ACCOUNT_JSON)
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred, {'storageBucket': STORAGE_BUCKET})
    db = firestore.client()
except Exception as e:
    st.error(f"❌ Firebase Admin SDKの初期化に失敗しました。SecretsのFIREBASE_SERVICE_ACCOUNT_JSONを確認してください。")
    st.error(f"エラー詳細: {e}")
    st.stop()
# --- ★★★ここまで変更★★★ ---

# --- Streamlitのセッションステート初期化 (Stripe顧客IDを追加) ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.email = None
    st.session_state.id_token = None
    st.session_state.plan = "Guest"
    st.session_state.remaining_uses = 0
    st.session_state.stripe_customer_id = None # Stripe顧客ID用のセッションステート

# --- Firebase Authentication REST APIの関数 (変更なし) ---
FIREBASE_AUTH_BASE_URL = "https://identitytoolkit.googleapis.com/v1/accounts:"

def sign_in_with_email_and_password(email, password):
    url = f"{FIREBASE_AUTH_BASE_URL}signInWithPassword?key={FIREBASE_API_KEY}"
    data = {"email": email, "password": password, "returnSecureToken": True}
    response = requests.post(url, json=data)
    response.raise_for_status()
    return response.json()

def create_user_with_email_and_password(email, password):
    url = f"{FIREBASE_AUTH_BASE_URL}signUp?key={FIREBASE_API_KEY}"
    data = {"email": email, "password": password, "returnSecureToken": True}
    response = requests.post(url, json=data)
    response.raise_for_status()
    return response.json()

# --- ★★★ここから変更★★★ ---
# --- Firestoreの操作関数 (Stripe連携機能を追加) ---
def get_user_data_from_firestore(uid):
    """
    元の月次リセット機能に、Stripe顧客IDの取得・作成機能を追加。
    """
    global db
    doc_ref = db.collection('users').document(uid)
    doc = doc_ref.get()
    
    if doc.exists:
        data = doc.to_dict()
        now = datetime.now(timezone.utc)
        last_reset_str = data.get("last_reset")
        needs_reset = False
        if last_reset_str:
            last_reset = datetime.fromisoformat(last_reset_str.replace('Z', '+00:00'))
            if last_reset.year < now.year or last_reset.month < now.month:
                needs_reset = True
        else:
            needs_reset = True
            
        if needs_reset:
            plan = data.get("plan", "Free")
            plan_monthly_uses = {
                "Free": 5, "Guest": 0, "Light": 50, "Pro": 200, "Team": 500, "Enterprise": 1000
            }
            new_remaining_uses = plan_monthly_uses.get(plan, 0)
            
            doc_ref.update({
                "remaining_uses": new_remaining_uses,
                "last_reset": now.isoformat()
            })
            data["remaining_uses"] = new_remaining_uses
            st.toast(f"利用回数がリセットされました。今月の残回数: {new_remaining_uses}回")

        st.session_state.plan = data.get("plan", "Free")
        st.session_state.remaining_uses = data.get("remaining_uses", 0)
        
        # Stripe顧客IDを取得。なければ作成する。
        st.session_state.stripe_customer_id = data.get("stripe_customer_id")
        if not st.session_state.stripe_customer_id:
            _create_stripe_customer_and_update_firestore(uid, doc_ref)

    else:
        # 新規ユーザー作成時にStripe顧客も一緒に作成する
        _create_new_user_in_firestore_and_stripe(uid)
    return True

def _create_stripe_customer_and_update_firestore(uid, doc_ref):
    """Stripe顧客を作成し、既存のFirestoreドキュメントを更新する"""
    try:
        customer = stripe.Customer.create(email=st.session_state.email, metadata={'firebase_uid': uid})
        st.session_state.stripe_customer_id = customer.id
        doc_ref.update({'stripe_customer_id': customer.id})
    except Exception as e:
        st.error(f"Stripe顧客の作成に失敗: {e}")

def _create_new_user_in_firestore_and_stripe(uid):
    """新規ユーザーのFirestoreドキュメントとStripe顧客を同時に作成する"""
    st.session_state.plan = "Free"
    st.session_state.remaining_uses = 5
    try:
        # Stripeで顧客を作成
        customer = stripe.Customer.create(email=st.session_state.email, metadata={'firebase_uid': uid})
        st.session_state.stripe_customer_id = customer.id
        
        # FirestoreにStripe顧客IDを含めて保存
        db.collection('users').document(uid).set({
            "email": st.session_state.email,
            "plan": st.session_state.plan,
            "remaining_uses": st.session_state.remaining_uses,
            "created_at": firestore.SERVER_TIMESTAMP,
            "last_reset": datetime.now(timezone.utc).isoformat(),
            "stripe_customer_id": customer.id
        })
    except Exception as e:
        st.error(f"新規ユーザーのStripe連携に失敗: {e}")

# --- ★★★ここまで変更★★★ ---

def update_user_uses_in_firestore(uid, uses_to_deduct=1):
    # (この関数はお客様の元のコードのまま、変更ありません)
    global db
    doc_ref = db.collection('users').document(uid)
    try:
        doc_ref.update({
            "remaining_uses": firestore.Increment(-uses_to_deduct),
            "last_used_at": firestore.SERVER_TIMESTAMP
        })
        st.session_state.remaining_uses -= uses_to_deduct # セッションステートも更新
        return True
    except Exception as e:
        st.error(f"利用回数の更新に失敗しました: {e}")
        return False

def add_diagnosis_record_to_firestore(uid, record_data):
    # (この関数はお客様の元のコードのまま、変更ありません)
    global db
    doc_ref = db.collection('users').document(uid).collection('diagnoses').document()
    try:
        record_data["created_at"] = firestore.SERVER_TIMESTAMP
        doc_ref.set(record_data)
        return True
    except Exception as e:
        st.error(f"診断記録のFirestore保存に失敗しました: {e}")
        return False

def get_diagnosis_records_from_firestore(uid):
    # (この関数はお客様の元のコードのまま、変更ありません)
    global db
    records = []
    docs = db.collection('users').document(uid).collection('diagnoses').order_by("created_at", direction=firestore.Query.DESCENDING).stream()
    for doc in docs:
        record = doc.to_dict()
        record["id"] = doc.id
        records.append(record)
    return records

def save_diagnosis_records_to_firestore(uid, records_df):
    # (この関数はお客様の元のコードのまま、変更ありません)
    global db
    user_diagnoses_ref = db.collection('users').document(uid).collection('diagnoses')

    for doc in user_diagnoses_ref.stream():
        doc.reference.delete()

    for _, row in records_df.iterrows():
        record_data = row.to_dict()
        if 'id' in record_data:
            del record_data['id']
        record_data["created_at"] = firestore.SERVER_TIMESTAMP
        user_diagnoses_ref.add(record_data)
    return True

def upload_image_to_firebase_storage(uid, image_bytes_io, filename):
    # (この関数はお客様の元のコードのまま、変更ありません)
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

# --- StreamlitのUI表示と認証フロー (変更なし) ---
def login_page():
    # (この関数はお客様の元のコードのまま、変更ありません)
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
                except requests.exceptions.HTTPError:
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
    # (この関数はお客様の元のコードのまま、変更ありません)
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.success("ログアウトしました。")
    st.rerun()

def check_login():
    # (この関数はお客様の元のコードのまま、変更ありません)
    if not st.session_state.get("logged_in"):
        login_page()
        st.stop()
    else:
        # ★★★サイドバーの表示をメトリックに変更★★★
        st.sidebar.write(f"ようこそ, {st.session_state.email}!")
        st.sidebar.metric("現在のプラン", st.session_state.plan)
        st.sidebar.metric("残り回数", f"{st.session_state.remaining_uses}回")
        st.sidebar.button("ログアウト", on_click=logout, use_container_width=True)
