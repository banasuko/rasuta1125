
import requests
from datetime import datetime
import streamlit as st

# --- Streamlit UI 設定 ---
st.set_page_config(layout="centered", page_title="バナスコAI")
st.title("🧠 バナー広告A/Bテスト - バナスコ")

# --- フォーム入力 ---
platform = st.selectbox("媒体", ["Instagram", "GDN", "YDN"])
category = st.selectbox("カテゴリ", ["広告", "投稿"] if platform == "Instagram" else ["広告"])
has_ad_budget = st.selectbox("広告予算", ["あり", "なし"])
purpose = st.selectbox("目的", ["プロフィール誘導", "リンククリック", "保存数増加"])
banner_name_a = st.text_input("Aバナー名（任意）")
banner_name_b = st.text_input("Bバナー名（任意）")
result = st.text_input("実績（任意）")
follower_gain = st.text_input("フォロワー増加（任意）")
memo = st.text_area("メモ（任意）")
comment_tone = st.selectbox("コメントトーン（任意）", ["プロ目線で辛口", "優しく丁寧に", "専門家としてシビアに"])

# --- 画像アップロード ---
a_image = st.file_uploader("Aバナーをアップロード", type=["png", "jpg", "jpeg"], key="a")
b_image = st.file_uploader("Bバナーをアップロード", type=["png", "jpg", "jpeg"], key="b")

# --- 採点トリガー ---
if st.button("🚀 A/Bバナー採点＋記録"):
    st.write("⚙️ 採点処理・保存処理は別スクリプトにて実装済み")
    st.write("🔁 上記UIデータは、GASとGPT処理に渡されます")

