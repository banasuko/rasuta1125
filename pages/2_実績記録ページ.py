import streamlit as st
import pandas as pd

st.set_page_config(page_title="実績記録", layout="wide")
st.title("📋 バナスコ｜広告実績記録ページ")

# データ取得（例：Google Sheets or 仮データ）
# 仮データで構築
if "records" not in st.session_state:
    st.session_state["records"] = [
        {
            "campaign": "キャンペーンA",
            "banner_name": "バナーA",
            "platform": "Instagram",
            "category": "広告",
            "score": "A",
            "ad_cost": "",
            "impressions": "",
            "clicks": "",
            "followers": "",
            "notes": ""
        }
    ]

# 表として編集できるように
df = pd.DataFrame(st.session_state["records"])
edited_df = st.data_editor(df, num_rows="dynamic")

# 上書き保存ボタン（仮実装）
if st.button("💾 編集内容を保存"):
    st.session_state["records"] = edited_df.to_dict(orient="records")
    st.success("保存しました（仮）")
