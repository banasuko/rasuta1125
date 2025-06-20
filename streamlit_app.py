import streamlit as st
import base64
import io
from PIL import Image
from openai import OpenAI

# 🔑 OpenAI APIキーを直接記述（セキュリティ上、後で .env に戻すのが理想）
client = OpenAI(api_key="sk-ここにあなたのキーを記述")

# --- Streamlit UI ---
st.set_page_config(layout="centered", page_title="バナスコAI")
st.title("🧠 バナー広告 採点AI - バナスコ")

uploaded_file = st.file_uploader("バナー画像をアップロード", type=["png", "jpg", "jpeg"])

if uploaded_file and st.button("🚀 採点開始"):
    image = Image.open(uploaded_file)
    st.image(image, caption="アップロード画像", use_column_width=True)

    # 画像をbase64に変換
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