　import streamlit as st
import base64
import io
import os
from dotenv import load_dotenv
load_dotenv()
import requests
from PIL import Image
from datetime import datetime
from openai import OpenAI

# --- 設定 ---
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# --- UI構成 ---
st.set_page_config(layout="centered", page_title="バナスコAI")
st.title("🧠 バナー広告 採点AI - バナスコ")

st.markdown("### 🎯 基本情報入力")
col1, col2 = st.columns(2)
with col1:
    user_name = st.text_input("ユーザー名")
    platform = st.selectbox("媒体", ["Instagram", "GDN", "YDN"])
    category = st.selectbox("カテゴリ", ["広告", "投稿"] if platform == "Instagram" else ["広告"])
    purpose = st.selectbox("目的", ["プロフィール誘導", "リンククリック", "保存数増加"])
with col2:
    banner_name = st.text_input("バナー名（任意）")
    result = st.text_input("実績（任意）")
    follower_gain = st.text_input("フォロワー増加（任意）")
    memo = st.text_area("メモ（任意）")

st.markdown("---")
st.markdown("### 🖼️ 採点したいバナーをアップロードしてください")
uploaded_file = st.file_uploader("画像ファイル", type=["png", "jpg", "jpeg"])

is_ab_test = st.checkbox("ABテストを行う（2枚アップロード）")

uploaded_file_b = None
if is_ab_test:
    uploaded_file_b = st.file_uploader("比較用画像（B案）", type=["png", "jpg", "jpeg"], key="b")

# --- 採点関数 ---
def score_banner(image_file):
    image = Image.open(image_file)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    img_str = base64.b64encode(buf.getvalue()).decode()

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "あなたは優秀な広告マーケターです。"},
            {"role": "user", "content": [
                {"type": "text", "text":
                    "以下のバナー画像を広告のプロ視点で採点してください：
"
                    "【評価基準】
"
                    "1. 内容が一瞬で伝わるか
"
                    "2. コピーの見やすさ
"
                    "3. 行動喚起があるか
"
                    "4. 写真と文字の整合性
"
                    "5. 情報量のバランス
"
                    "【出力形式】
スコア：A/B/C
改善コメント：2〜3行程度"
                },
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}}
            ]}
        ],
        max_tokens=700
    )

    content = response.choices[0].message.content
    score = next((l.replace("スコア：", "").strip() for l in content.splitlines() if "スコア" in l), "")
    comment = next((l.replace("改善コメント：", "").strip() for l in content.splitlines() if "改善コメント" in l), "")
    return score, comment, image

# --- 実行ボタン ---
if uploaded_file and st.button("🚀 採点開始"):
    st.markdown("### ✅ 採点結果")

    score_a, comment_a, image_a = score_banner(uploaded_file)
    st.image(image_a, caption=f"A案（スコア：{score_a}）", use_column_width=True)
    st.markdown(f"**改善コメント：** {comment_a}")

    if is_ab_test and uploaded_file_b:
        score_b, comment_b, image_b = score_banner(uploaded_file_b)
        st.image(image_b, caption=f"B案（スコア：{score_b}）", use_column_width=True)
        st.markdown(f"**改善コメント（B案）：** {comment_b}")
    elif is_ab_test:
        st.warning("⚠️ B案画像が未アップロードです")
