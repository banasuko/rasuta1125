import streamlit as st

st.title("バナスコAI 採点ツール")
st.write("バナー画像をアップすると、AIが採点＆改善コメントを表示します。")
import streamlit as st
from PIL import Image

st.title("バナスコAI 採点ツール")
st.write("バナー画像をアップすると、AIが採点＆改善コメントを表示します。")

# ① 画像アップロード欄
uploaded_file = st.file_uploader("▶︎ バナー画像をアップロード", type=["png", "jpg", "jpeg"])

# ② アップロードされた画像を表示
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="アップロードされた画像", use_column_width=True)

    # ③ 仮スコア＆コメント（ここは後でAI連携と差し替え）
    st.subheader("🧠 AIの採点結果（仮）")
    st.write("📊 スコア：**A評価**")
    st.write("💬 コメント：`文字の視認性が良く、パッと目を引きます！`")
import streamlit as st
import os
import openai
import base64
import io
from PIL import Image

# 環境変数からAPIキーを取得
openai.api_key = os.getenv("OPENAI_API_KEY")


openai.api_key = os.getenv("OPENAI_API_KEY")


# 画像アップロード
uploaded_file = st.file_uploader("バナー画像をアップロード", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="アップロードされた画像", use_column_width=True)

    # base64変換
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    # GPTへ送信（仮のプロンプト）
    with st.spinner("AIが採点中です..."):
        response = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",
           messages = [
    {
        "role": "system",
        "content": "あなたは優秀な広告デザイナーです。"
    },
    {
        "role": "user",
        "content": [
            {
                "type": "text",
"text": """以下の基準に従って、この広告バナーをプロの視点で辛口に採点してください：

【評価基準】
1. 何の広告かが一瞬で伝わるか（内容の明確さ）
2. メインコピーの見やすさ（フォント・サイズ・色の使い方）
3. 行動喚起があるか（予約・購入などにつながるか）
4. 写真とテキストが噛み合っているか（世界観や目的にズレがないか）
5. 情報量のバランス（不要な装飾・ごちゃごちゃしていないか）

【出力フォーマット】
スコア：A / B / C のいずれかで採点してください
（A：優れた広告 / B：改善の余地あり / C：問題が多い）

改善コメント：端的に2〜3行で指摘（甘口NG、曖昧表現NG）
"""

            }
        ]
    }
]

            max_tokens=500
        )

        # 結果表示
        st.success("採点完了！")
        st.write(response["choices"][0]["message"]["content"])
