import streamlit as st
import base64
import io
from PIL import Image
from openai import OpenAI
import os

# 環境変数からAPIキーを取得
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# ページ設定
st.set_page_config(layout="wide")

# ヘッダー：ロゴ＋タイトル
 st.container():
    col1, col2 = st.columns([1, 8])
     col1:
    st.image("Ai (1).png", =80)  # ロゴ画像ファイル名に応じて変更可
     col2:
        st.markdown("### バナー広告ＡＢテストバナスコ")

# サイドバー：モードリンク
st.sidebar.markdown("### モード切替")
for link in ["Instagram", "インスタ投稿", "インスタ広告", "Google", "YDN"]:
    st.sidebar.markdown(f"[{link}](#)")

# セッション保持
if "result_data" not in st.session_state:
    st.session_state.result_data = {}

# メインレイアウト（3列）
left, center, right = st.columns([3, 2, 3])

# A・Bバナー画像アップロード欄
with left:
    st.markdown("### インスタ投稿モード")
    uploaded_a = st.file_uploader("Aバナーをアップロード", type=["png", "jpg", "jpeg"], key="a")
    uploaded_b = st.file_uploader("Bバナーをアップロード", type=["png", "jpg", "jpeg"], key="b")

    if uploaded_a:
        st.image(uploaded_a, caption="Aバナー", width=250)
        if "A" in st.session_state.result_data:
            st.markdown(f"### {st.session_state.result_data['A']['score']}評価")
            st.markdown(f"<p style='color: orange'>{st.session_state.result_data['A']['comment']}</p>", unsafe_allow_html=True)

    if uploaded_b:
        st.image(uploaded_b, caption="Bバナー", width=250)
        if "B" in st.session_state.result_data:
            st.markdown(f"### {st.session_state.result_data['B']['score']}評価")
            st.markdown(f"<p style='color: orange'>{st.session_state.result_data['B']['comment']}</p>", unsafe_allow_html=True)

# 中央カラム：タイトルと空枠
with center:
    st.markdown("### AIバナー計測")
    st.markdown("<div style='border:2px solid black; height:300px;'></div>", unsafe_allow_html=True)

# 右カラム：将来3枚目用
with right:
    st.markdown("<div style='border:2px solid black; height:300px;'></div>", unsafe_allow_html=True)

# 計測ボタン
_, btn_col = st.columns([8, 2])
with btn_col:
    if st.button("計測"):
        for label, file in zip(["A", "B"], [uploaded_a, uploaded_b]):
            if file:
                image = Image.open(file)
                buf = io.BytesIO()
                image.save(buf, format="PNG")
                img_base64 = base64.b64encode(buf.getvalue()).decode()

                with st.spinner(f"{label}バナーをAIが分析中..."):
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
                                            "url": f"data:image/png;base64,{img_base64}"
                                        }
                                    }
                                ]
                            }
                        ],
                        max_tokens=600
                    )

                content = response.choices[0].message.content
                score = "不明"
                comment = "取得できませんでした"
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
