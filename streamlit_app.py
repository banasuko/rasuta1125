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

# Google Apps Script WebアプリのURL（変更してください）
GAS_URL = "https://script.google.com/macros/s/XXXXXXXXXXXXXXXXXXXX/exec"

# --- Streamlit UI ---
st.set_page_config(layout="centered", page_title="バナスコAI")
st.title("🧠 バナー広告 採点AI - バナスコ")

mode = st.radio("モード選択", ["単体バナーを採点", "A/Bバナーを比較"])

def get_gpt_feedback(image_file):
    image = Image.open(image_file)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    img_str = base64.b64encode(buf.getvalue()).decode()

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
                    "【出力形式】\nスコア：A/B/C\n改善コメント：2～3行\nコピー改善案：1案"
                },
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}}
            ]}
        ],
        max_tokens=600
    )
    return response.choices[0].message.content

def post_to_gsheet(data):
    try:
        response = requests.post(GAS_URL, json=data)
        st.write("📡 GAS応答ステータスコード:", response.status_code)
        st.write("📄 GAS応答本文:", response.text)
        if response.status_code == 200:
            st.success("📊 スプレッドシートに記録しました！")
        else:
            st.error("❌ スプレッドシート送信エラー")
    except Exception as e:
        st.error(f"送信時にエラーが発生しました: {e}")

if mode == "単体バナーを採点":
    uploaded_file = st.file_uploader("バナー画像をアップロード", type=["png", "jpg", "jpeg"])
    if uploaded_file and st.button("🚀 採点する（1枚）"):
        content = get_gpt_feedback(uploaded_file)
        st.success("✅ 採点結果")
        st.markdown(content)

        score = next((l.replace("スコア：", "").strip() for l in content.splitlines() if "スコア" in l), "")
        comment = next((l.replace("改善コメント：", "").strip() for l in content.splitlines() if "改善コメント" in l), "")
        copyidea = next((l.replace("コピー改善案：", "").strip() for l in content.splitlines() if "コピー改善案" in l), "")

        # GAS送信
        data = {
            "sheetName": "バナスコ_単体",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "score": score,
            "comment": comment,
            "copyidea": copyidea
        }
        post_to_gsheet(data)

elif mode == "A/Bバナーを比較":
    uploaded_a = st.file_uploader("バナーA", type=["png", "jpg", "jpeg"], key="a")
    uploaded_b = st.file_uploader("バナーB", type=["png", "jpg", "jpeg"], key="b")
    if uploaded_a and uploaded_b and st.button("🚀 採点する（A/Bバナー）"):
        content_a = get_gpt_feedback(uploaded_a)
        content_b = get_gpt_feedback(uploaded_b)

        st.success("✅ バナーAの評価")
        st.markdown(content_a)
        st.success("✅ バナーBの評価")
        st.markdown(content_b)

        # スコア・コメント抽出
        score_a = next((l.replace("スコア：", "").strip() for l in content_a.splitlines() if "スコア" in l), "")
        comment_a = next((l.replace("改善コメント：", "").strip() for l in content_a.splitlines() if "改善コメント" in l), "")
        copy_a = next((l.replace("コピー改善案：", "").strip() for l in content_a.splitlines() if "コピー改善案" in l), "")

        score_b = next((l.replace("スコア：", "").strip() for l in content_b.splitlines() if "スコア" in l), "")
        comment_b = next((l.replace("改善コメント：", "").strip() for l in content_b.splitlines() if "改善コメント" in l), "")
        copy_b = next((l.replace("コピー改善案：", "").strip() for l in content_b.splitlines() if "コピー改善案" in l), "")

        data = {
            "sheetName": "バナスコ_AB比較",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "score_a": score_a,
            "comment_a": comment_a,
            "copy_a": copy_a,
            "score_b": score_b,
            "comment_b": comment_b,
            "copy_b": copy_b
        }
        post_to_gsheet(data)

