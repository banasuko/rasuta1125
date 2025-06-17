import streamlit as st
import base64
import io
from PIL import Image
from openai import OpenAI
import os
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

# APIキーの取得
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# ページ設定
st.set_page_config(layout="wide", page_title="バナスコAI", page_icon="📊")

# Google Sheets 認証（事前にgspread用JSONを設定）
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
gc = gspread.authorize(credentials)
sheet_url = "https://docs.google.com/spreadsheets/d/1uUxZRY_ZHvwm1gMF_F936yRu0vbgtd6uGOHt-Ejgeao/edit"
sheet = gc.open_by_url(sheet_url).sheet1

# タブ構成
tabs = st.tabs(["📊 バナー採点", "💡 コピー提案"])

with tabs[0]:
    st.image("ai_logo.png", width=80)
    st.markdown("## バナー広告ＡＢテストバナスコ")

    # 入力欄（共通情報）
    st.sidebar.markdown("### ユーザー入力")
    user_name = st.sidebar.text_input("あなたの名前")
    product_name = st.sidebar.text_input("商品・サービス名")
    target_audience = st.sidebar.text_input("ターゲット層（例：20代女性など）")
    memo = st.sidebar.text_area("補足・備考（任意）")

    st.sidebar.markdown("---")
    mode = st.sidebar.selectbox("使用モード", ["Instagram広告", "Instagram投稿", "Google広告（GDN）", "Yahoo広告（YDN）"])
    tone = st.sidebar.selectbox("コメントトーン", ["プロ目線で辛口", "優しく丁寧に", "専門家としてシビアに"])

    if "result_data" not in st.session_state:
        st.session_state.result_data = {}

    left, center, right = st.columns([3, 2, 3])

    with left:
        st.subheader("画像アップロード")
        uploaded_a = st.file_uploader("Aバナーをアップロード", type=["png", "jpg", "jpeg"], key="a")
        uploaded_b = st.file_uploader("Bバナーをアップロード", type=["png", "jpg", "jpeg"], key="b")

        if uploaded_a:
            st.image(uploaded_a, caption="Aバナー", width=250)
            if "A" in st.session_state.result_data:
                st.markdown(f"**評価：{st.session_state.result_data['A']['score']}**")
                st.markdown(f"<p style='color:orange'>{st.session_state.result_data['A']['comment']}</p>", unsafe_allow_html=True)

        if uploaded_b:
            st.image(uploaded_b, caption="Bバナー", width=250)
            if "B" in st.session_state.result_data:
                st.markdown(f"**評価：{st.session_state.result_data['B']['score']}**")
                st.markdown(f"<p style='color:orange'>{st.session_state.result_data['B']['comment']}</p>", unsafe_allow_html=True)

    with center:
        st.subheader("AIバナー採点")

        if st.button("🚀 計測する"):
            st.session_state.result_data.clear()

            for label, file in zip(["A", "B"], [uploaded_a, uploaded_b]):
                if file:
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
                                            "text": f"以下のバナーを対象に、\n商品：{product_name}\nターゲット：{target_audience}\n補足：{memo}\n\n以下の基準に従って、プロの視点で{tone}で採点してください：\n\n【評価基準】\n1. 何の広告かが一瞬で伝わるか（内容の明確さ）\n2. メインコピーの見やすさ（フォント・サイズ・色の使い方）\n3. 行動喚起があるか（予約・購入などにつながるか）\n4. 写真とテキストが噛み合っているか（世界観や目的にズレがないか）\n5. 情報量のバランス（不要な装飾・ごちゃごちゃしていないか）\n\n【出力フォーマット】\nスコア：A / B / C のいずれかで採点してください\n改善コメント：2〜3行で具体的に（甘口NG）"
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

            # 🔽 採点結果をスプレッドシートに保存
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sheet.append_row([
                now, user_name, product_name, target_audience, memo, mode,
                st.session_state.result_data.get("A", {}).get("score", ""),
                st.session_state.result_data.get("A", {}).get("comment", ""),
                st.session_state.result_data.get("B", {}).get("score", ""),
                st.session_state.result_data.get("B", {}).get("comment", "")
            ])

    with right:
        st.markdown("<div style='border:2px dashed #ccc; height:300px; text-align:center; padding:20px;'>3つ目のバナー枠（今後追加予定）</div>", unsafe_allow_html=True)
)
