import os, re, time, json, requests
import streamlit as st
from datetime import datetime, timezone, timedelta

# ---------------------------
# ページ設定
# ---------------------------
st.set_page_config(page_title="お問い合わせ", layout="centered")

# --- CSS：ハニーポットを完全に不可視化（DOM上にあるが見えない） ---
st.markdown("""
<style>
input[placeholder="__banasuko_hp__"]{ 
  position: absolute !important; 
  left: -10000px !important; 
  width: 1px !important; 
  height: 1px !important; 
  opacity: 0 !important; 
  pointer-events: none !important; 
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# 環境変数（st.secrets 経由）
# ---------------------------
MAIL_PROVIDER = st.secrets.get("MAIL_PROVIDER", "resend").lower()
RESEND_API_KEY = st.secrets.get("RESEND_API_KEY", "")
MAIL_FROM      = st.secrets.get("MAIL_FROM", "no-reply@banasuko.ai")
MAIL_TO_1      = st.secrets.get("MAIL_TO_1", "")
MAIL_TO_2      = st.secrets.get("MAIL_TO_2", "")

# 送信レート制限（同一セッション60秒）
if "last_submit_at" not in st.session_state:
    st.session_state.last_submit_at = 0.0

JST = timezone(timedelta(hours=9))

# ---------------------------
# バリデーション系
# ---------------------------
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def validate(email: str, message: str, agree: bool, honeypot: str):
    if honeypot.strip():  # bot が埋めたら即NG
        return False, "不正な送信が検出されました。"
    if not email or not EMAIL_RE.match(email):
        return False, "メールアドレスの形式が正しくありません。"
    if not message or len(message.strip()) == 0:
        return False, "お問い合わせ内容は必須です。"
    if len(message) > 1000:
        return False, "お問い合わせ内容は1000文字以内で入力してください。"
    if not agree:
        return False, "個人情報の取り扱いに同意が必要です。"
    # レート制限
    now = time.time()
    if now - st.session_state.last_submit_at < 60:
        return False, "短時間に複数回の送信はできません。1分ほど時間をあけてお試しください。"
    return True, ""

def send_email_via_resend(name: str, email: str, message: str):
    if MAIL_PROVIDER != "resend":
        raise RuntimeError("MAIL_PROVIDER は 'resend' を指定してください。")

    if not RESEND_API_KEY or not MAIL_TO_1 or not MAIL_TO_2 or not MAIL_FROM:
        raise RuntimeError("メール送信の設定が不足しています（secrets を確認してください）。")

    sent_at = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S %Z")
    subject = "[お問い合わせ] バナスコ"
    body = f"""お名前: {name or '（未記入）'}
メール: {email}
送信日時: {sent_at}

--- お問い合わせ内容 ---
{message}
"""

    # Resend API（https://resend.com/docs/api-reference/emails/send）
    url = "https://api.resend.com/emails"
    payload = {
        "from": MAIL_FROM,
        "to": [MAIL_TO_1, MAIL_TO_2],   # ← 宛先はサーバ側のみ
        "subject": subject,
        "text": body,
        "reply_to": email,               # 運営がそのまま返信できる
    }
    headers = {"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"}

    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=20)
    if resp.status_code >= 300:
        raise RuntimeError(f"Resend API エラー: {resp.status_code} {resp.text}")

# ---------------------------
# UI
# ---------------------------
st.title("お問い合わせ")

st.write(
    "以下のフォームにご入力ください。**返信は3営業日以内**にメールでご連絡します。"
    "\n\n**営業時間：火曜〜金曜 10:00–17:00（JST）**｜**電話での問い合わせは受け付けておりません。**"
)

with st.form("contact_form", clear_on_submit=True):
    name = st.text_input("お名前（任意）", max_chars=50, placeholder="山田 太郎")
    email = st.text_input("メールアドレス（必須）", placeholder="your-email@example.com")
    message = st.text_area("お問い合わせ内容（必須）", height=180, 
                           placeholder="サービスに関するご質問や改善のご要望などをご自由にお書きください。")
    # 完全不可視のハニーポット（見えない／触れない）
    honeypot = st.text_input("", key="hp", label_visibility="collapsed", placeholder="__banasuko_hp__")
    agree = st.checkbox("個人情報の取り扱いに同意します。（プライバシーポリシー）")

    submitted = st.form_submit_button("送信する")

if submitted:
    ok, err = validate(email, message, agree, honeypot)
    if not ok:
        st.error(err)
    else:
        try:
            send_email_via_resend(name, email, message)
            st.session_state.last_submit_at = time.time()
            st.success(
                "お問い合わせありがとうございます。送信が完了しました。"
                "担当より**3営業日以内**にメールでご連絡します。営業時間：火〜金 10:00–17:00。"
                " **電話対応は行っておりません。**"
            )
        except Exception as e:
            # 内部情報を出しすぎない
            st.error("送信中にエラーが発生しました。時間をおいて再度お試しください。")
