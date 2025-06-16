import streamlit as st
import base64
import io
from PIL import Image
from openai import OpenAI
import os

# APIキーの取得
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# ページ設定
st.set_page_config(layout="wide", page_title="バナスコAI", page_icon="📊")

# タブ構成（採点／提案）
tabs = st.tabs(["📊 バナー採点", "💡 コピー提案"])

with tabs[0]:
    # ロゴとタイトル
    st.image("ai_logo.png", width=80)
    st.markdown("## バナー広告ＡＢテストバナスコ")

    # サイドバー：モード切替
    st.sidebar.markdown("### 📂 モード切替")
    mode = st.sidebar.selectbox("使用目的", ["Instagram広告", "Instagram投稿", "Google広告（GDN）", "Yahoo広告（YDN）"])
    tone = st.sidebar.selectbox("コメントトーン", ["プロ目線で辛口", "優しく丁寧に", "専門家としてシビアに"])

    # セッション状態の初期化
    if "result_data" not in st.session_state:
        st.session_state.result_data = {}

    # レイアウト：3列
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
                                            "text": f"以下の基準に従って、この広告バナーをプロの視点で{tone}で採点してください：\n\n【評価基準】\n1. 何の広告かが一瞬で伝わるか（内容の明確さ）\n2. メインコピーの見やすさ（フォント・サイズ・色の使い方）\n3. 行動喚起があるか（予約・購入などにつながるか）\n4. 写真とテキストが噛み合っているか（世界観や目的にズレがないか）\n5. 情報量のバランス（不要な装飾・ごちゃごちゃしていないか）\n\n【出力フォーマット】\nスコア：A / B / C のいずれかで採点してください（A：優れた広告 / B：改善の余地あり / C：問題が多い）\n\n改善コメント：端的に2〜3行で具体的に指摘（甘口NG、曖昧表現NG）"
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

    with right:
        st.markdown("<div style='border:2px dashed #ccc; height:300px; text-align:center; padding:20px;'>3つ目のバナー枠（今後追加予定）</div>", unsafe_allow_html=True)


with tabs[1]:
    st.subheader("💡 バナーコピー自動提案（β版）")
    category = st.selectbox("ジャンルを選んでください", ["ホテル広告", "カフェ紹介", "習い事スクール", "物件紹介", "ECセール"])
    tone2 = st.radio("トーン設定", ["親しみやすく", "専門的に", "インパクト重視"])
    prompt = st.text_area("📝 補足情報（任意）", "例：沖縄の海沿いで家族向け。夏限定。")

    if st.button("🪄 コピーを生成"):
        with st.spinner("生成中..."):
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたは広告コピーライターです。"},
                    {"role": "user", "content": f"ジャンル：{category}\nトーン：{tone2}\n補足情報：{prompt}\n\n上記に基づいて、SNS広告に使えるキャッチコピーを5つ提案してください。1行ずつ表示してください。"}
                ],
                max_tokens=500
            )
            st.markdown(response.choices[0].message.content)
