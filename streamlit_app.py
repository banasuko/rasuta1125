import streamlit as st
import base64
import io
from PIL import Image
from openai import OpenAI
import os

# 環境変数からAPIキーを読み込む
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

st.title("🧠 バナスコAI 採点ツール")
st.write("バナー画像をアップすると、AIが採点＆改善コメントを表示します。")

# 画像アップロード
uploaded_file = st.file_uploader("▶ バナー画像をアップロード", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="アップロードされた画像", use_column_width=True)

    # base64変換
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    # GPTへ送信
    with st.spinner("AIが採点中です..."):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "あなたは優秀な広告ディレクターです。"
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "以下の基準に従って、この広告バナーをプロの視点で遠慮なく辛口で採点してください：\n\n【評価基準】\n1. 何の広告かが一瞬で伝わるか（内容の明確さ）\n2. メインコピーの見やすさ（フォント・サイズ・色の使い方）\n3. 行動喚起があるか（予約・購入などにつながるか）\n4. 写真とテキストが噛み合っているか（世界観や目的にズレがないか）\n5. 情報量のバランス（不要な装飾・ごちゃごちゃしていないか）\n\n【出力フォーマット】\nスコア：A / B / C のいずれかで採点してください（A：優れた広告 / B：改善の余地あり / C：問題が多い）\n\n改善コメント：端的に2〜3行で具体的に指摘（甘口NG、曖昧表現NG）"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_str}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=600
        )

        result = response.choices[0].message.content
        st.success("✅ 採点が完了しました！")
        st.markdown(result)

