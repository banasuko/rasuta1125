import streamlit as st
import base64
import io
from PIL import Image
from openai import OpenAI
import os

# APIキー読み込み
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# ページ設定
st.set_page_config(layout="wide")

# ヘッダー：ロゴ＋タイトル
st.image("ai_logo.png", width=80)
st.title("バナー広告A/Bテスト - バナスコ")

# セッション変数（スコア保持）
if "result_data" not in st.session_state:
    st.session_state.result_data = {}

# カラム分割
left, center, right = st.columns([3, 2, 3])

# 左カラム：A/B画像アップ＆表示
with left:
    st.subheader("A・Bバナー画像")
    uploaded_a = st.file_uploader("▶ Aバナー画像をアップロード", type=["png", "jpg", "jpeg"], key="a")
    uploaded_b = st.file_uploader("▶ Bバナー画像をアップロード", type=["png", "jpg", "jpeg"], key="b")

    if uploaded_a:
        st.image(uploaded_a, caption="Aバナー", width=250)
        if "A" in st.session_state.result_data:
            st.markdown(f"**評価：{st.session_state.result_data['A']['score']}**")
            st.markdown(f"<div style='color:orange'>{st.session_state.result_data['A']['comment']}</div>", unsafe_allow_html=True)

    if uploaded_b:
        st.image(uploaded_b, caption="Bバナー", width=250)
        if "B" in st.session_state.result_data:
            st.markdown(f"**評価：{st.session_state.result_data['B']['score']}**")
            st.markdown(f"<div style='color:orange'>{st.session_state.result_data['B']['comment']}</div>", unsafe_allow_html=True)

# 中央カラム：計測ボタン
with center:
    st.subheader("AIバナー採点")

    if st.button("🚀 計測する"):
    # 🔽 ここを追加！前回の結果を消す（←インデント必要！）
    st.session_state.result_data.clear()

    for label, file in zip(["A", "B"], [uploaded_a, uploaded_b]):
        if file:
            # ...ここもインデントで揃える

                image = Image.open(file)
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                img_str = base64.b64encode(buffer.getvalue()).decode()

                with st.spinner(f"{label}をAIが分析中..."):
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "あなたは優秀な広告ディレクターです。"},
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "以下の基準に従って広告バナーを採点してください：\n\n"
                                                "【評価基準】\n"
                                                "1. 何の広告かが一瞬で伝わるか\n"
                                                "2. メインコピーの見やすさ\n"
                                                "3. 行動喚起があるか\n"
                                                "4. 写真とテキストの整合性\n"
                                                "5. 情報量のバランス\n\n"
                                                "【出力】\n"
                                                "スコア：A / B / C\n"
                                                "改善コメント：2〜3行で、甘口NG・曖昧表現NG"
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {"url": f"data:image/png;base64,{img_str}"}
                                    }
                                ]
                            }
                        ],
                        max_tokens=600
                    )

                content = response.choices[0].message.content
                score = "?"
                comment = "取得失敗"

                for line in content.splitlines():
                    if "スコア" in line:
                        score = line.replace("スコア：", "").strip()
                    if "改善コメント" in line:
                        comment = line.replace("改善コメント：", "").strip()

                st.session_state.result_data[label] = {
                    "score": score,
                    "comment": comment
                }

        st.experimental_rerun()

# 右カラム：未使用スペース（将来用）
with right:
    st.subheader("結果まとめ（将来拡張）")
    st.markdown("3枚比較などの結果をここに表示予定です。")
