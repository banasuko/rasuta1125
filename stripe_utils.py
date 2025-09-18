import streamlit as st
import stripe
import os

# --- Stripe API Setup ---
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8501") # StreamlitアプリのURL

def create_checkout_session(price_id, customer_id):
    """Stripe Checkoutセッションを作成し、決済ページのURLを返す"""
    try:
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            success_url=f'{APP_BASE_URL}?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=APP_BASE_URL,
        )
        return checkout_session.url
    except Exception as e:
        st.error(f"決済ページの作成に失敗しました: {e}")
        return None

def create_portal_session(customer_id):
    """Stripe顧客ポータルセッションを作成し、管理ページのURLを返す"""
    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=APP_BASE_URL,
        )
        return portal_session.url
    except Exception as e:
        st.error(f"顧客ポータルの作成に失敗しました: {e}")
        return None
