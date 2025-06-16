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
import openai
from PIL import Image
import base64
import io

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
            messages=[
                {"role": "system", "content": "あなたは優秀な広告デザイナーです。"},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "このバナー画像を広告として採点し、改善点を簡潔に教えてください。"},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}}
                    ],
                },
            ],
            max_tokens=500
        )

        # 結果表示
        st.success("採点完了！")
        st.write(response["choices"][0]["message"]["content"])
