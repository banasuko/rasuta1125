# ✅ Streamlit 側の送信コード（デバッグ用ログ付き）
import requests
import streamlit as st
from datetime import datetime

# あなたのGAS URL（最新に必ず更新）
GAS_URL = "https://script.google.com/macros/s/AKfycbzQadO4iuzhETiiDZb2ZQ7et_Rgjb_kR7OIUyL0mK2wqU2-FB2UeN4FVtdyK3Xod3Tm/exec
"

# サンプル送信データ（最低限のテスト）
data = {
    "sheet_name": "record_log",
    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "score": "A",
    "comment": "テスト送信（Streamlit側から）"
}

st.write("🖋 送信データ:", data)

try:
    response = requests.post(GAS_URL, json=data, headers={"Content-Type": "application/json"})
    st.write("📡 GAS応答ステータスコード:", response.status_code)
    st.write("📄 GAS応答本文:", response.text)
    if response.status_code == 200:
        st.success("📊 スプレッドシートに記録されました！")
    else:
        st.error("❌ GAS送信エラー：ステータスコードが200ではありません")
except Exception as e:
    st.error(f"❌ リクエスト送信中にエラー: {e}")
