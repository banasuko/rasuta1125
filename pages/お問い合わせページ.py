import streamlit as st

st.set_page_config(page_title="お問い合わせ", layout="centered")

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeIllJydg7pKoz6riObLrl34Hwi6lDlYuj7TQ9SO-oycLPmAg/viewform?embedded=true"

st.title("お問い合わせ")
st.caption("返信は**3営業日以内**にご連絡します。営業時間：火〜金 10:00–17:00。**電話での問い合わせは受け付けておりません。**")

st.markdown(
    f"""
    <div style="max-width:900px;margin:0 auto;">
      <iframe src="{FORM_URL}" width="100%" height="1050" frameborder="0" marginheight="0" marginwidth="0">
        Loading…
      </iframe>
    </div>
    """,
    unsafe_allow_html=True
)
