# app_contact.py
import os, re, time, json, requests
import streamlit as st
from datetime import datetime, timezone, timedelta

# =========================
# ページ設定 & 最小CSS
# =========================
st.set_page_config(page_title="お問い合わせ", layout="centered")

# ハニーポット（隠しフィールド）を完全不可視にする
st.markdown("""
<style>
input[placeholder="__banasuko_hp__"]{
  position:absolute !important;
  left:-10000px !important;
  width:1px !important;
  height:1px !important;
  opacity:0 !important;
  pointer-events:none !important;
}
</style>
""", unsafe_allow_html=True)

JST = timezone(timedelta(hours=9))

# =========================
# Secrets（UIに出しません）
# =========================
MAIL_PROVIDER   = st.secrets.get("MAIL_PROVIDER", "resend").lower()
RESEND_API_KEY  = st.secrets.get("RESEND_API_KEY", "")
MAIL_FROM       = st.secrets.get("MAIL_FROM", "")
MAIL_TO_1       = st.secrets.get("MAIL_TO_1", "")
MAIL_TO_2       = st.secrets.get("MAIL_TO_2", "")
ENABLE_SPAM_QUIZ = bool(st.secrets.get("ENABLE_SPAM_QUIZ", False))

# セッションの送信レート制限（60秒）
if "last_submit_at" not in st.session_state:
    st.session_state.last_submit_at = 0.0

# =========================
# バリデーション
# =========================
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def validate(email: str, message: str, agree: bool, honeypot: str, quiz_ok: bool):
    if honeypot.strip():  # bot はここに入力しがち
        return False, "不正な送信が検出されました。"

    if not email or not EMAIL_RE.match(email):
        return False, "メールアドレスの形式が正しくありません。"

    if not message or len(message.strip()) == 0:
        return False, "お問い合わせ内容は必須です。"

    if len(message) > 1000:
        return False, "お問い合わせ内容は1000文字以内で入力してください。"

    if not agree:
        return False, "個人情報の取り扱いへの同意が必要です。"

    # 任意：足し算クイズ
    if ENABLE_SPAM_QUIZ and not quiz_ok:
        return False, "簡易確認の回答が一致しません。"

    # レート制限
    now = time.time()
    if now - st.session_state.last_submit_at < 60:
        return False, "短時間に複数回の送信はできません。1分ほど時間をあけてお試しください。"

    # メール送信の設定が揃っているか（ここで事前チェック）
    if MAIL_PROVIDER != "resend":
        return False, "メール送信設定が無効です（MAIL_PROVIDERは'resend'を指定してください）。"
    if not RESEND_API_KEY or not MAIL_FROM or not MAIL_TO_1 or not MAIL_TO_2:
        return False, "メール送信の設定が不足しています（secrets を確認してください）。"

    return True, ""

# =========================
# メール送信（Resend）
# =========================
def send_email_via_resend(name: str, email: str, message: str):
    sent_at = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S %Z")
    subject = "[お問い合わせ] バナスコ"
    body = f"""お名前: {name or '（未記入）'}
メール: {email}
送信日時: {sent_at}

--- お問い合わせ内容 ---
{message}
"""

    url = "https://api.resend.com/emails"
    payload = {
        "from": MAIL_FROM,                   # 例: no-reply@aimable00.com（Resendでドメイン認証済み）
        "to": [MAIL_TO_1, MAIL_TO_2],        # 宛先はサーバ側にのみ保持
        "subject": subject,
        "text": body,
        "reply_to": email,                   # 運営がそのまま返信できる
    }
    headers = {"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"}

    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=20)
    if resp.status_code >= 300:
        # Resendのレスポンスをログしたい場合は print に留める（UIには出さない）
        print("Resend error:", resp.status_code, resp.text)
        raise RuntimeError("Resend API からエラー応答がありました。")

# =========================
# UI
# =========================
st.title("お問い合わせ")

st.write(
    "以下のフォームにご入力ください。**返信は3営業日以内**にメールでご連絡します。"
    "\n\n**営業時間：火曜〜金曜 10:00–17:00（JST）**｜**電話での問い合わせは受け付けておりません。**"
)

with st.form("contact_form", clear_on_submit=True):
    name = st.text_input("お名前（任意）", max_chars=50, placeholder="山田 太郎")
    email = st.text_input("メールアドレス（必須）", placeholder="your-email@example.com")
    message = st.text_area(
        "お問い合わせ内容（必須）",
        height=180,
        placeholder="サービスに関するご質問や、改善のご要望などをご自由にお書きください。"
    )

    # 完全不可視のハニーポット（見えない/触れない）
    honeypot = st.text_input("", key="hp", label_visibility="collapsed", placeholder="__banasuko_hp__")

    quiz_ok = True
    if ENABLE_SPAM_QUIZ:
        colq1, colq2 = st.columns(2)
        with colq1:
            q = st.number_input("確認のために 2 + 5 = ?", min_value=0, step=1)
        with colq2:
            st.caption("※ ボット対策です")
        quiz_ok = (q == 7)

    agree = st.checkbox("個人情報の取り扱いに同意します。（プライバシーポリシー）")

    submitted = st.form_submit_button("送信する")

if submitted:
    ok, err = validate(email, message, agree, honeypot, quiz_ok)
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
        except Exception:
            # 内部詳細はUIに出さない（ログはコンソール）
            st.error("送信中にエラーが発生しました。時間をおいて再度お試しください。")
