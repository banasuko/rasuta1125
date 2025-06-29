import os
import json
import streamlit as st
import pyrebase
import firebase_admin
from firebase_admin import credentials, firestore

# --- Firebase Authentication (pyrebase for login) ---
firebase_config = {
    "apiKey": os.getenv("API_KEY"),
    "authDomain": os.getenv("AUTH_DOMAIN"),
    "projectId": os.getenv("PROJECT_ID"),
    "storageBucket": os.getenv("STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("MESSAGING_SENDER_ID"),
    "appId": os.getenv("APP_ID"),
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

# --- Firebase Admin SDK (for Firestore) ---
if not firebase_admin._apps:
    cred = credentials.Certificate({
        "type": "service_account",
        "project_id": os.getenv("PROJECT_ID_ADMIN"),
        "private_key": os.getenv("PRIVATE_KEY_ADMIN").replace('\\n', '\n'),
        "client_email": os.getenv("CLIENT_EMAIL_ADMIN"),
        "token_uri": "https://oauth2.googleapis.com/token"
    })
    firebase_admin.initialize_app(cred)

db = firestore.client()

# --- Firestoreからユーザー情報を取得（残回数やプラン） ---
def get_user_data(email):
    doc_ref = db.collection("users").document(email)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        return None

# --- Firestoreにユーザー情報を登録（初回用） ---
def initialize_user(email):
    doc_ref = db.collection("users").document(email)
    doc_ref.set({
        "plan": "free",
        "remaining_uses": 5  # Freeプランは月5回まで
    })
