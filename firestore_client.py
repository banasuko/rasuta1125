import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv
import json

load_dotenv()
db = None

def initialize_firebase_admin():
    global db
    if not firebase_admin._apps:
        try:
            service_account_info_str = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
            if not service_account_info_str:
                print("Error: FIREBASE_SERVICE_ACCOUNT_JSON env var not found.")
                return
            service_account_info = json.loads(service_account_info_str)
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
        except Exception as e:
            print(f"Error initializing Firebase Admin SDK for webhook: {e}")

def update_user_plan(customer_id, plan_name, remaining_uses):
    global db
    if not db: return False
    try:
        users_ref = db.collection('users')
        docs = users_ref.where('stripe_customer_id', '==', customer_id).limit(1).stream()
        user_doc = next(docs, None)
        if user_doc:
            user_doc.reference.update({'plan': plan_name, 'remaining_uses': remaining_uses})
            return True
        return False
    except Exception as e:
        print(f"Error updating user plan in Firestore: {e}")
        return False

initialize_firebase_admin()
