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
GAS_URL = "https://script.google.com/macros/s/AKfycbxtXdRDYmtuzqGuDFYAehC6KP3dcoEz36i1PuUgzMBseqE0cuYcJHoaZ-s7Tmt-Zw1a/exec"  # Web Apps Script のURLに置換

# --- ヘッダー・サイドバー ---
st.set_page_config(page_title="バナー広告A/Bテスト バナスコ", layout="wide")
st.markdown("<style>body { zoom: 0.95; }</style>", unsafe_allow_html=True)

st.sidebar.title("🧭 モード切替")
mode = st.sidebar.selectbox("使用目的", ["Instagram投稿", "Instagram広告", "Google", "YDN"])
tone = st.sidebar.selectbox("コメントトーン", ["プロ目線で辛口", "優しく丁寧に", "専門家としてシビアに"])
genre = st.sidebar.selectbox("ジャンル", ["不動産", "こども写真館", "飲食", "美容・サロン"])

st.title("📊 バナー広告ＡＢテストバナスコ")

# --- 単発採点エリア ---
st.subheader("🟠 単発バナー採点")
col1, col2 = st.columns([2, 3])

with col1:
    uploaded_single = st.file_uploader("画像をアップロード（単発）", type=["png", "jpg", "jpeg"], key="single")

with col2:
    if uploaded_single and st.button("📌 単発バナーを計測"):
        image = Image.open(uploaded_single)
        st.image(image, caption="アップロード画像", use_column_width=True)
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        img_str = base64.b64encode(buf.getvalue()).decode()

        with st.spinner("AIが採点中..."):
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": f"あなたは{mode}の広告バナーを評価するプロです。口調は『{tone}』でお願いします。"},
                    {"role": "user", "content": [
                        {"type": "text", "text": "以下の広告バナーを評価し、スコア（A/B/C）と改善コメント（2〜3行）をください："},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}}
                    ]}
                ],
                max_tokens=600
            )
            content = response.choices[0].message.content
            score = next((l.replace("スコア：", "").strip() for l in content.splitlines() if "スコア" in l), "")
            comment = next((l.replace("改善コメント：", "").strip() for l in content.splitlines() if "改善コメント" in l), content)

        st.success(f"スコア：{score}")
        st.markdown(f"**改善コメント：** {comment}")

# --- A/Bテスト採点 ---
st.subheader("🟠 A/Bバナー採点")
ab1, ab2 = st.columns(2)

with ab1:
    uploaded_a = st.file_uploader("Aバナーをアップロード", type=["png", "jpg", "jpeg"], key="ab_a")
with ab2:
    uploaded_b = st.file_uploader("Bバナーをアップロード", type=["png", "jpg", "jpeg"], key="ab_b")

if uploaded_a and uploaded_b and st.button("📌 A/Bバナーを計測"):
    result_ab = {}
    for label, file in zip(["A", "B"], [uploaded_a, uploaded_b]):
        image = Image.open(file)
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        img_str = base64.b64encode(buf.getvalue()).decode()

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"あなたは{mode}の広告バナーを評価するプロです。トーンは『{tone}』。"},
                {"role": "user", "content": [
                    {"type": "text", "text": f"以下のA/Bバナー（{label}）を評価してください。スコアと改善コメントをください。"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}}
                ]}
            ],
            max_tokens=600
        )
        content = response.choices[0].message.content
        score = next((l.replace("スコア：", "").strip() for l in content.splitlines() if "スコア" in l), "")
        comment = next((l.replace("改善コメント：", "").strip() for l in content.splitlines() if "改善コメント" in l), content)
        result_ab[label] = {"score": score, "comment": comment}

    ab_col1, ab_col2 = st.columns(2)
    with ab_col1:
        st.markdown("### 🅰️ Aバナー")
        st.image(uploaded_a, use_column_width=True)
        st.markdown(f"スコア：**{result_ab['A']['score']}**")
        st.markdown(f"改善コメント：{result_ab['A']['comment']}")
    with ab_col2:
        st.markdown("### 🅱️ Bバナー")
        st.image(uploaded_b, use_column_width=True)
        st.markdown(f"スコア：**{result_ab['B']['score']}**")
        st.markdown(f"改善コメント：{result_ab['B']['comment']}")

    # AとBの比較表示
    if result_ab['A']['score'] < result_ab['B']['score']:
        st.info("💡 Aバナーの方が効果が高そうです")
    elif result_ab['A']['score'] > result_ab['B']['score']:
        st.info("💡 Bバナーの方が効果が高そうです")
    else:
        st.info("📊 スコアは互角です。コメントを参考に改善を検討しましょう")

# --- コピー提案機能（仮） ---
st.markdown("---")
st.subheader("📝 コピー文言のアイデア")
copy_input = st.text_area("ターゲットや意図を入力（例：20代女性向け、お得感を出したいなど）")
if copy_input and st.button("💡 コピーを提案してもらう"):
    with st.spinner("提案生成中..."):
        copy_res = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "あなたは広告コピーの専門家です。"},
                {"role": "user", "content": f"以下の条件に基づいて3つの短い広告コピーを提案してください：\n{copy_input}"}
            ],
            max_tokens=300
        )
        st.markdown(copy_res.choices[0].message.content)

        response = requests.post(GAS_URL, json=data)
        st.write("📡 GAS応答ステータスコード:", response.status_code)
        st.write("📄 GAS応答本文:", response.text)

        if response.status_code == 200:
            st.success("📊 スプレッドシートに記録しました！")
        else:
            st.error("❌ スプレッドシート送信エラー")
