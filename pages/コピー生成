import streamlit as st
from PIL import Image
import openai
import io
import datetime

# APIキーの読み込み（環境変数 or .envに設定済みとして想定）
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- UI構成 ---

st.title("バナー画像からコピー案を生成")

# 1. 画像アップロード
uploaded_image = st.file_uploader("バナー画像をアップロード", type=["jpg", "png"])
if uploaded_image:
    st.image(uploaded_image, caption="アップロードされた画像", use_column_width=True)

# 2. カテゴリー選択
category = st.selectbox("カテゴリーを選択", [
    "美容室", "脱毛サロン", "エステ", "ネイル・まつげ", "ホワイトニング",
    "整体・接骨院", "学習塾", "子ども写真館", "飲食店", "その他"
])

# 3. 補足情報入力
target = st.text_input("ターゲット層（例：30代女性、経営者など）")
feature = st.text_area("商品の特徴・アピールポイント")
tone = st.selectbox("トーン（雰囲気）を選択", ["親しみやすい", "高級感", "情熱的", "おもしろ系", "真面目"])

# 4. コピー生成数
copy_count = st.selectbox("コピー生成数", [2, 5, 10], index=1)

# 5. コピー生成ボタン
if st.button("コピーを生成する"):

    # --- プロンプト生成 ---
    system_prompt = "あなたは広告コピーライターです。"
    user_prompt = f"""
以下の情報をもとに、バナー広告に使えるキャッチコピーを{copy_count}案、簡潔に提案してください。
【業種】{category}
【ターゲット層】{target}
【特徴・アピールポイント】{feature}
【トーン】{tone}
- 30文字以内でインパクトのあるコピーにしてください。
- 同じ方向性のコピーを繰り返さないようにしてください。
- {"薬機法に配慮した表現を使用してください（効果保証・医療行為的表現は禁止）" if category in ["脱毛サロン", "エステ", "ホワイトニング"] else ""}
"""

    # --- GPTへリクエスト ---
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        output = response.choices[0].message.content
        st.subheader("🎯 コピー案")
        st.markdown(output)

        # 薬機法チェック表示（美容系）
        if category in ["脱毛サロン", "エステ", "ホワイトニング"]:
            st.subheader("🔍 薬機法チェック：美容ジャンルのため表現に注意が必要です")
            st.caption("※ 明確な効果表現や『治る』『即効』などの語句を避けてください。")

    except Exception as e:
        st.error(f"エラーが発生しました：{e}")
