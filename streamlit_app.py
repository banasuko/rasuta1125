import streamlit as st
import base64
import io
import os
import requests
from PIL import Image
from datetime import datetime
from openai import OpenAI

# --- 設定 ---
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# Web Apps Script のエンドポイント
GAS_URL = "https://script.google.com/macros/s/AKfycbxtXdRDYmtuzqGuDFYAehC6KP3dcoEz36i1PuUgzMBseqE0cuYcJHoaZ-s7Tmt-Zw1a/exec"

# --- UI構成（3カラム） ---
st.set_page_config(layout="wide", page_title="バナスコAI")
st.markdown("<h1 style='text-align:center;'>🧠 バナー広告 採点AI - バナスコ</h1>", unsafe_allow_html=True)

left, center, right = st.columns([1.2, 2.5, 1.2])

with left:
    st.subheader("📥 アップロード")
    uploaded_file = st.file_uploader("バナー画像をアップロード", type=["png", "jpg", "jpeg"])

    if uploaded_file:
        st.image(uploaded_file, caption="アップロード画像", use_container_width=True)

with center:
    st.subheader("📝 情報入力")
    user_name = st.text_input("ユーザー名")
    platform = st.selectbox("媒体", ["Instagram", "GDN", "YDN"])
    category = st.selectbox("カテゴリ", ["広告", "投稿"] if platform == "Instagram" else ["広告"])
    has_ad_budget = st.selectbox("広告予算", ["あり", "なし"])
    purpose = st.selectbox("目的", ["プロフィール誘導", "リンククリック", "保存数増加"])
    banner_name = st.text_input("バナー名（任意）")
    result = st.text_input("実績（任意）")
    follower_gain = st.text_input("フォロワー増加（任意）")
    memo = st.text_area("メモ（任意）")
    image_url = st.text_input("画像URL（任意、Drive等で共有リンク）")

with right:
    st.subheader("📊 採点結果")

    if uploaded_file and st.button("🚀 採点＋保存"):
        image = Image.open(uploaded_file)
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        img_str = base64.b64encode(buf.getvalue()).decode()

        with st.spinner("AIが採点中です..."):
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたは広告のプロです。"},
                    {"role": "user", "content": [
                        {"type": "text", "text":
                            "以下の広告バナーをプロ視点で採点してください：\n"
                            "【評価基準】\n"
                            "1. 内容が一瞬で伝わるか\n"
                            "2. コピーの見やすさ\n"
                            "3. 行動喚起\n"
                            "4. 写真とテキストの整合性\n"
                            "5. 情報量のバランス\n"
                            "【出力形式】\nスコア：A/B/C\n改善コメント：2～3行"
                        },
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}}
                    ]}
                ],
                max_tokens=600
            )
            content = response.choices[0].message.content
            score = next((l.replace("スコア：", "").strip() for l in content.splitlines() if "スコア" in l), "")
            comment = next((l.replace("改善コメント：", "").strip() for l in content.splitlines() if "改善コメント" in l), "")

        st.success(f"スコア：{score}")
        st.markdown(f"**改善コメント：** {comment}")

        sheet_name = f"{platform}_{category}用"
        data = {
            "sheetName": sheet_name,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "platform": platform,
            "category": category,
            "hasAdBudget": has_ad_budget,
            "purpose": purpose,
            "bannerName": banner_name,
            "score": score,
            "comment": comment,
            "result": result,
            "followerGain": follower_gain,
            "memo": memo,
            "imageUrl": image_url
        }

        response = requests.post(GAS_URL, json=data)
        st.write("📡 GAS応答ステータスコード:", response.status_code)
        st.write("📄 GAS応答本文:", response.text)

        if response.status_code == 200:
            st.success("📊 スプレッドシートに記録しました！")
        else:
            st.error("❌ スプレッドシート送信エラー")
