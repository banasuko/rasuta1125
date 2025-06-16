import streamlit as st
import openai
import base64
import os

# OpenAIのAPIキー（StreamlitのSecretsから）
openai.api_key = os.getenv("OPENAI_API_KEY")

st.title("バナスコAI 採点ツール")
st.write("バナー画像をアップすると、AIが辛口で採点＆改善コメントを出します。")

uploaded_file = st.file_uploader("バナー画像をアップロードしてください", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image_bytes = uploaded_file.read()
    img_str = base64.b64encode(image_bytes).decode("utf-8")

    with st.spinner("AIが採点中..."):
        response = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",
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
                            "text":
"以下の基準に従って、この広告バナーをプロの視点で**遠慮なく厳しく辛口で**採点してください：\n\n"
"【評価基準】\n"
"1. 何の広告かが一瞬で伝わるか（内容の明確さ）\n"
"2. メインコピーの見やすさ（フォント・サイズ・色の使い方）\n"
"3. 行動喚起があるか（予約・購入などにつながるか）\n"
"4. 写真とテキストが噛み合っているか（世界観や目的にズレがないか）\n"
"5. 情報量のバランス（不要な装飾・ごちゃごちゃしていないか）\n\n"
"【出力フォーマット】\n"
"スコア：A / B / C のいずれかで採点してください\n"
"（A：優れた広告 / B：改善の余地あり / C：問題が多い）\n\n"
"改善コメント：端的に2〜3行で指摘（甘口NG、曖昧表現NG）"
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
