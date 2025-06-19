
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="実績記録", layout="centered")
st.title("📈 広告実績記録ページ")

st.markdown("このページでは、広告の成果を記録し、分析の材料として保存できます。")

# --- 入力フォーム ---
with st.form("record_form"):
    col1, col2 = st.columns(2)
    with col1:
        campaign_name = st.text_input("キャンペーン名")
        banner_name = st.text_input("バナー名（任意）")
        platform = st.selectbox("媒体", ["Instagram", "GDN", "YDN"])
        category = st.selectbox("カテゴリ", ["広告", "投稿"])
        score = st.selectbox("スコア", ["A", "B", "C"])
    with col2:
        date = st.date_input("掲載日", value=datetime.today())
        ad_cost = st.text_input("広告費（円）")
        impressions = st.text_input("インプレッション数")
        clicks = st.text_input("クリック数")
        followers = st.text_input("フォロワー増加数")

    notes = st.text_area("メモ・気づきなど", height=100)

    submitted = st.form_submit_button("📩 データを保存（仮）")

if submitted:
    st.success("✅ 入力内容を仮保存しました（今後PDF化・学習連携予定）")
    st.json({
        "キャンペーン名": campaign_name,
        "バナー名": banner_name,
        "媒体": platform,
        "カテゴリ": category,
        "スコア": score,
        "掲載日": str(date),
        "広告費": ad_cost,
        "表示回数": impressions,
        "クリック数": clicks,
        "フォロワー増": followers,
        "メモ": notes
    })
