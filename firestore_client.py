# firestore_client.py
import os
import json
import logging

# dotenvはローカル開発用。Streamlit Cloudではsecrets使うので無くてもOK
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ---------------------------
# Firebase Admin (優先)
# ---------------------------
import firebase_admin
from firebase_admin import credentials, firestore

_db = None  # グローバル参照用

def initialize_firebase_admin():
    """
    サービスアカウントJSONから Admin SDK を初期化し、firestore.Client をセット。
    """
    global _db
    if _db:
        return
    if not firebase_admin._apps:
        try:
            # 推奨：.streamlit/secrets.toml に FIREBASE_SERVICE_ACCOUNT_JSON をそのまま格納
            service_account_info_str = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
            if not service_account_info_str:
                logging.error("FIREBASE_SERVICE_ACCOUNT_JSON not found.")
                return
            service_account_info = json.loads(service_account_info_str.strip())
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            logging.exception("Error initializing Firebase Admin SDK: %s", e)
            return
    try:
        _db = firestore.client()
    except Exception as e:
        logging.exception("Error creating Firestore client: %s", e)
        _db = None

def get_firestore_db():
    """
    呼び出し側が期待しているアクセサ。
    - Admin SDK 初期化済みならその db を返す。
    - 未初期化なら初期化を試みる。
    """
    global _db
    if not _db:
        initialize_firebase_admin()
    if not _db:
        raise ImportError(
            "Firestore client is not available. "
            "Check FIREBASE_SERVICE_ACCOUNT_JSON in secrets/env."
        )
    return _db

# 既存の関数は互換維持
def update_user_plan(customer_id, plan_name, remaining_uses):
    """
    users コレクションで stripe_customer_id == customer_id のユーザを1件探して
    plan / remaining_uses を更新。
    """
    try:
        db = get_firestore_db()
        users_ref = db.collection('users')
        docs = users_ref.where('stripe_customer_id', '==', customer_id).limit(1).stream()
        user_doc = next(docs, None)
        if user_doc:
            user_doc.reference.update({'plan': plan_name, 'remaining_uses': remaining_uses})
            return True
        return False
    except Exception as e:
        logging.exception("Error updating user plan in Firestore: %s", e)
        return False

# 便利ラッパ（呼び出し側から使いやすい形）
def add_doc(collection: str, data: dict) -> str | None:
    """
    コレクションにドキュメント追加。戻り値は doc_id（失敗時 None）。
    """
    try:
        db = get_firestore_db()
        _, doc_ref = db.collection(collection).add(data)
        return doc_ref.id
    except Exception as e:
        logging.exception("add_doc failed: %s", e)
        return None

def get_docs(collection: str, limit: int = 50):
    """
    コレクションを上限件数で取得して返す（Admin SDKの DocumentSnapshot 配列）。
    """
    try:
        db = get_firestore_db()
        return list(db.collection(collection).limit(limit).stream())
    except Exception as e:
        logging.exception("get_docs failed: %s", e)
        return []
