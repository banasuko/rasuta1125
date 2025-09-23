import streamlit as st
import re
import time
import random
import resend
import requests
from typing import List, Tuple

# --- ここからメール送信機能（旧mailer.pyの内容） ---

def _get_secrets() -> Tuple:
    """
    Streamlitのsecretsから設定を安全に読み込む
    """
    required_secrets = ["MAIL_PROVIDER", "MAIL_FROM", "MAIL_TO_1", "MAIL_TO_2"]
    for secret in required_secrets:
        if secret not in st.secrets:
            raise ValueError(f"シークレット '{secret}' が設定されていません。")

    provider = st.secrets["MAIL_PROVIDER"].lower()
    mail_from = st.secrets["MAIL_FROM"]
    mail_to = [st.secrets["MAIL_TO_1"], st.secrets["MAIL_TO_2"]]

    api_key, domain = "", ""
    if provider == "resend":
        if "RESEND_API_KEY" not in st.secrets:
            raise ValueError("MAIL_PROVIDERがresendですが、RESEND_API_KEYが設定されていません。")
        api_key = st.secrets["RESEND_API_KEY"]
    elif provider == "mailgun":
        if "MAILGUN_API_KEY" not in st.secrets or "MAILGUN_DOMAIN" not in st.secrets:
            raise ValueError("MAIL_PROVIDERがmailgunですが、MAILGUN_API_KEYまたはMAILGUN_DOMAINが設定されていません。")
        api_key = st.secrets["MAILGUN_API_KEY"]
        domain = st.secrets["MAILGUN_DOMAIN"]
    else:
        raise ValueError(f"サポートされていないMAIL_PROVIDERです: {provider}")
    return provider, api_key, domain, mail_from, mail_to

def _send_with_resend(api_key: str, mail_from: str, mail_to: List[str], subject: str, body_html: str, reply_to: str) -> bool:
    try:
        resend.api_key = api_key
        response = resend.Emails.send(
            from_=mail_from, to=mail_to, subject=subject, html=body_html, reply_to=reply_to
        )
        return 'id' in response
    except Exception as e:
        st.error(f"Resendでのメール送信中にエラーが発生しました: {e}")
        return False

def _send_with_mailgun(api_key: str, domain: str, mail_from: str, mail_to: List[str], subject: str, body_html: str, reply_to: str) -> bool:
    try:
        response = requests.post(
            f"https://api.mailgun.net/v3/{domain}/messages",
            auth=("api", api_key),
            data={"from": mail_from, "to": mail_to, "subject": subject, "html": body_html, "h:Reply-To": reply_to}
        )
        response.raise_for_status()
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        st.error(f"Mailgunでのメール送信中にエラーが発生しました: {e}")
        return False

def send_contact_email(name: str, email: str, message: str) -> bool:
    """
    お問い合わせ内容を運営者にメールで送信するメイン関数
    """
    try:
        provider, api_key, domain, mail_from, mail_to = _get_secrets()
    except ValueError as e:
        st.error(f"設定エラー: {e}")
        return False

    subject = f"【BanasukoAI】お問い合わせがありました（{name or '匿名'}様より）"
    body_html = f"""
    <html>
    <body style="font-family: sans-serif;">
        <h2>BanasukoAIにお問い合わせがありました。</h2><hr>
        <p><strong>お名前:</strong> {name or '未入力'}</p>
        <p><strong>メールアドレス (返信先):</strong> {email}</p>
        <p><strong>お問い合わせ内容:</strong></p>
        <pre style="white-space: pre-wrap; word-wrap: break-word; background-color: #f4f4f4; padding: 15px; border-radius: 5px;">{message}</pre><hr>
        <p style="color: #888; font-size: 12px;">このメールはウェブサイトのお問い合わせフォームから送信されました。</p>
    </body>
    </html>
    """
    if provider == "resend":
        return _send_with_resend(api_key, mail_from, mail_to, subject, body_html, reply_to=email)
    elif provider == "mailgun":
        return _send_with_mailgun(api_key, domain, mail_from, mail_to, subject, body_html, reply_to=email)
    return False

# --- ここから画面表示機能 ---

st.set_page_config(layout="wide", page_title="お問い合わせ")

st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(135deg, #0f0f1a 0%, #1a1c29 15%, #2d3748 35%, #1a202c 50%, #2d3748 65%, #4a5568 85%, #2d3748 100%) !important; background-attachment: fixed; }
    .main .block-container { background: rgba(26, 32, 44, 0.4) !important; backdrop-filter: blur(60px) !important; border: 2px solid rgba(255, 255, 255, 0.1) !important; border-radius: 32px !important; padding: 5rem 4rem !important; margin: 2rem auto !important; max-width: 900px !important; }
    .stButton > button { background: linear-gradient(135deg, #38bdf8 0%, #a855f7 50%, #06d6a0 100%) !important; color: #ffffff !important; border: none !important; border-radius: 60px !important; font-weight: 700 !important; font-size: 1.1rem !important; padding: 1.25rem 3rem !important; width: 100% !important; }
    div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea { background: #1a1c29 !important; color: #FBC02D !important; border: 2px solid rgba(255, 255, 255, 0.2) !important; border-radius: 16px !important; }
    h1, .stTitle { font-size: 3.5rem !important; font-weight: 900 !important; background: linear-gradient(135deg, #38bdf8, #a855f7, #3b82f6, #06d6a0, #f59e0b, #38bdf8) !important; background-size: 600% 600% !important; -webkit-background-clip: text !important; -webkit-text-fill-color: transparent !important; text-align: center !important; animation: mega-gradient-shift 12s ease-in-out infinite !important; }
    @keyframes mega-gradient-shift { 0%, 100% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } }
    p, div, span, label, .stMarkdown, .stCheckbox { color: #ffffff !important; }
    #MainMenu, footer, header { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True
)

def is_valid_email(email):
    return re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", email)

if 'last_submission_time' not in st.session_state:
    st.session_state.last_submission_time = 0

st.title("✉️ お問い合わせ")
st.markdown("ご意見、ご感想、不具合の報告などはこちらからお送りください。")
st.markdown("---")

with st.form(key='contact_form'):
    name = st.text_input("お名前（任意）", max_chars=50, placeholder="山田 太郎")
    email = st.text_input("メールアドレス（必須）", placeholder="your-email@example.com")
    message = st.text_area("お問い合わせ内容（必須）", max_chars=1000, height=200, placeholder="サービスに関するご質問や、改善のご要望などをご自由にお書きください。")
    honeypot = st.text_input("このフィールドは入力しないでください", key="honeypot", label_visibility="collapsed")
    agree = st.checkbox("個人情報の取り扱いに同意します。（プライバシーポリシー）")
    submitted = st.form_submit_button("送信する")

if submitted:
    if time.time() - st.session_state.last_submission_time < 60:
        st.error("エラー: 送信頻度が高すぎます。1分後に再度お試しください。")
    elif honeypot:
        st.success("お問い合わせありがとうございます。")
    elif not email or not message or not agree:
        st.error("エラー: 必須項目をすべて入力してください。")
    elif not is_valid_email(email):
        st.error("エラー: 正しい形式のメールアドレスを入力してください。")
    else:
        with st.spinner("メッセージを送信中です..."):
            # ローカル関数を直接呼び出す
            success = send_contact_email(name, email, message)
        if success:
            st.success("✅ お問い合わせありがとうございます。3営業日以内にご連絡いたします。")
            st.session_state.last_submission_time = time.time()
        else:
            st.error("❌ 送信に失敗しました。時間をおいて再度お試しください。")

st.markdown("---")
st.subheader("ご案内")
st.info(
    """
    - **返信は3営業日以内**にご連絡いたします。
    - **営業時間：火曜〜金曜 10:00–17:00（JST）**
    - **電話での問い合わせは受け付けておりません。**
    """
)
