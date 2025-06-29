Current action: The user is reporting a `SyntaxError` again, indicating that the introductory Japanese explanation text has been copied into the Python file at the beginning. I need to apologize again for the repeated error and provide the *clean* Python code, explicitly stating that *only* the Python code block should be copied.

大変申し訳ありません！！またしても、コードの冒頭に私が書いた説明文が誤って含まれてしまいました。

これは完全に私のミスです。本当に、本当に申し訳ありません。Pythonのコードとして解釈できない日本語の文字が含まれているため、`SyntaxError` が発生してしまいます。

お手数をおかけし、何度も申し訳ありません。

-----

### 【最終版のStreamlitアプリコード】 (再々々度)

今度こそ、**余計な説明文が一切含まれていない、完全にクリーンなPythonコードのみ**を提供します。

このコードブロックの中身だけを、あなたの`streamlit_app.py`ファイルに**すべてコピー＆ペーストして上書き**してください。

-----

```python
import streamlit as st
import base64
import io
import os
import re
import requests
from PIL import Image
from datetime import datetime
from openai import OpenAI

# OpenAI APIキーの読み込み
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    st.error("❌ OpenAI APIキーが見つかりませんでした。`.env` を確認してください。")
    st.stop()
client = OpenAI(api_key=openai_api_key)

# GASとGoogle Driveの情報
# Replace with your deployed GAS URL
# It's strongly recommended to use your latest deployed GAS URL
GAS_URL = "https://script.google.com/macros/s/AKfycbxUy3JI5xwncRHxv-WoHHNqiF7LLndhHTOzmLOHtNRJ2hNCo8PJi7-0fdbDjnfAGMlL/exec"

# Helper function to sanitize values
def sanitize(value):
    """Replaces None or specific strings with 'エラー' (Error)"""
    if value is None or value == "取得できず":
        return "エラー"
    return value

# Google Drive upload functionality is removed in this version

# Streamlit UI configuration
st.set_page_config(layout="wide", page_title="バナスコAI")

# --- カスタムCSSの追加 ---
st.markdown(
    """
    <style>
    /* 全体の背景に微細なグリッドパターンとグラデーション */
    body {
        background: radial-gradient(circle at top left, #1a1a1a, #0a0a0a);
        background-repeat: repeat;
        background-size: 20px 20px;
        background-image: 
            linear-gradient(to right, #2a2a2a 1px, transparent 1px),
            linear-gradient(to bottom, #2a2a2a 1px, transparent 1px);
        background-attachment: fixed;
    }

    /* Streamlitのメインコンテナに影と少しの角丸 */
    .main .block-container {
        padding-top: 2rem;
        padding-right: 2rem;
        padding-left: 2rem;
        padding-bottom: 2rem;
        border-radius: 8px; /* 少し角丸 */
        box-shadow: 0px 4px 15px rgba(0, 229, 118, 0.2); /* primaryColorのシャドウ */
        background-color: #1a1a1a; /* main background to match */
    }

    /* サイドバーの背景色をテーマに合わせて調整 */
    .stSidebar {
        background-color: #1E1E1E; /* secondaryBackgroundColorに合わせる */
        border-right: 1px solid #333;
    }
    
    /* ボタンのスタイル調整（よりシャープに、アクティブ感を出す） */
    .stButton > button {
        background-color: #008040; /* primaryColorより少し暗め */
        color: white;
        border-radius: 5px;
        border: 1px solid #00E676; /* primaryColorのボーダー */
        box-shadow: 0px 2px 5px rgba(0, 229, 118, 0.2);
        transition: background-color 0.2s, box-shadow 0.2s;
    }
    .stButton > button:hover {
        background-color: #00B359; /* ホバーで少し明るく */
        box-shadow: 0px 4px 10px rgba(0, 229, 118, 0.4);
    }
    .stButton > button:active {
        background-color: #006633; /* クリック時にさらに暗く */
        box-shadow: none;
    }

    /* Expanderのボーダーと背景（メカニックなコンポーネント感を出す） */
    .stExpander {
        border: 1px solid #333;
        border-radius: 5px;
        background-color: #282828; /* 少し明るい背景で目立たせる */
        box-shadow: 0px 1px 3px rgba(0,0,0,0.3);
    }
    .stExpander > div > div { /* ヘッダー部分 */
        background-color: #333;
        border-bottom: 1px solid #444;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
    }
    .stExpanderDetails { /* 展開される内容部分 */
        background-color: #282828; /* Expander本体と同じ */
    }

    /* テキスト入力、セレクトボックスなどの背景 */
    div[data-baseweb="input"],
    div[data-baseweb="select"],
    div[data-baseweb="textarea"] {
        background-color: #333333;
        border-radius: 5px;
        border: 1px solid #555555;
        color: #E0E0E0;
    }
    /* テキスト入力、セレクトボックスなどのテキスト色 */
    div[data-baseweb="input"] input,
    div[data-baseweb="select"] span,
    div[data-baseweb="textarea"] textarea {
        color: #E0E0E0 !important;
    }
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="select"]:focus-within,
    div[data-baseweb="textarea"]:focus-within {
        border-color: #00E676; /* フォーカス時にアクセントカラー */
        box-shadow: 0 0 0 1px #00E676;
    }

    /* メトリック (st.metric) の表示を強調 */
    [data-testid="stMetricValue"] {
        color: #00E676; /* アクセントカラー */
        font-size: 2.5rem; /* 大きめのフォントサイズ */
        font-weight: bold;
    }
    [data-testid="stMetricLabel"] {
        color: #B0B0B0;
        font-size: 0.9rem;
    }
    [data-testid="stMetricDelta"] {
        color: #E0E0E0; /* デルタ（変化量）のテキスト色 */
    }

    /* Infoボックスの強調 */
    .stAlert.stAlert-info {
        background-color: #00331A; /* primaryColorの暗いバージョン */
        border-left: 5px solid #00E676;
        color: #E0E0E0;
    }

    /* Successボックスの強調 */
    .stAlert.stAlert-success {
        background-color: #1a4d2e; /* より深いグリーン */
        border-left: 5px solid #00E676;
        color: #E0E0E0;
    }

    /* Warningボックスの強調 */
    .stAlert.stAlert-warning {
        background-color: #4d401a; /* オレンジ系の警告色 */
        border-left: 5px solid #FFC107;
        color: #E0E0E0;
    }

    /* Errorボックスの強調 */
    .stAlert.stAlert-error {
        background-color: #4d1a1a; /* 赤系のエラー色 */
        border-left: 5px solid #DC3545;
        color: #E0E0E0;
    }

    /* コードブロックの背景 */
    code {
        background-color: #2a2a2a !important;
        color: #00E676 !important; /* コードのテキスト色もアクセントカラーに */
        border-radius: 5px;
        padding: 0.2em 0.4em;
    }
    pre code {
        background-color: #2a2a2a !important;
        padding: 1em !important;
        overflow-x: auto;
    }

    </style>
    """,
    unsafe_allow_html=True
)
# --- カスタムCSSの終わり ---

st.title("🧠 バナー広告 採点AI - バナスコ")
st.subheader("〜もう、無駄打ちしない。広告を“武器”に変えるAIツール〜")

col1, col2 = st.columns([2, 1])

with col1:
    with st.container(border=True): # This border=True is styled by config.toml and CSS
        st.subheader("📝 バナー情報入力フォーム")

        with st.expander("👤 基本情報", expanded=True):
            user_name = st.text_input("ユーザー名", key="user_name_input")
            platform = st.selectbox("媒体", ["Instagram", "GDN", "YDN"], key="platform_select")
            category = st.selectbox("カテゴリ", ["広告", "投稿"] if platform == "Instagram" else ["広告"], key="category_select")
            has_ad_budget = st.selectbox("広告予算", ["あり", "なし"], key="budget_select")
            purpose = st.selectbox("目的", ["プロフィール誘導", "リンククリック", "保存数増加"], key="purpose_select")

        with st.expander("🎯 詳細設定", expanded=True):
            industry = st.selectbox("業種", ["美容", "飲食", "不動産", "子ども写真館", "その他"], key="industry_select")
            genre = st.selectbox("ジャンル", ["お客様の声", "商品紹介", "ノウハウ", "世界観", "キャンペーン"], key="genre_select")
            score_format = st.radio("スコア形式", ["A/B/C", "100点満点"], horizontal=True, key="score_format_radio")
            ab_pattern = st.radio("ABテストパターン", ["Aパターン", "Bパターン", "該当なし"], horizontal=True, key="ab_pattern_radio")
            banner_name = st.text_input("バナー名", key="banner_name_input")

        with st.expander("📌 任意項目", expanded=False):
            result_input = st.text_input("AI評価結果（任意）", help="AIが生成した評価結果を記録したい場合に入力します。", key="result_input_text")
            follower_gain_input = st.text_input("フォロワー増加数（任意）", help="Instagramなどのフォロワー増加数があれば入力します。", key="follower_gain_input_text")
            memo_input = st.text_area("メモ（任意）", help="その他、特記事項があれば入力してください。", key="memo_input_area")

        st.markdown("---")
        st.subheader("🖼️ バナー画像アップロードと診断")

        uploaded_file_a = st.file_uploader("Aパターン画像をアップロード", type=["png", "jpg", "jpeg"], key="a_upload")
        uploaded_file_b = st.file_uploader("Bパターン画像をアップロード", type=["png", "jpg", "jpeg"], key="b_upload")

        # Initialize session state for results
        if 'score_a' not in st.session_state: st.session_state.score_a = None
        if 'comment_a' not in st.session_state: st.session_state.comment_a = None
        if 'yakujihou_a' not in st.session_state: st.session_state.yakujihou_a = None
        if 'score_b' not in st.session_state: st.session_state.score_b = None
        if 'comment_b' not in st.session_state: st.session_state.comment_b = None
        if 'yakujihou_b' not in st.session_state: st.session_state.yakujihou_b = None

        # --- A Pattern Processing ---
        if uploaded_file_a:
            # Columns for image and results side-by-side
            img_col_a, result_col_a = st.columns([1, 2]) # Image 1 part, results 2 parts

            with img_col_a:
                st.image(Image.open(uploaded_file_a), caption="Aパターン画像", use_container_width=True) # use_container_widthでカラム幅に合わせる
                if st.button("🚀 Aパターンを採点", key="score_a_btn"): # Changed button name
                    image_a = Image.open(uploaded_file_a)
                    buf_a = io.BytesIO()
                    image_a.save(buf_a, format="PNG")
                    img_str_a = base64.b64encode(buf_a.getvalue()).decode()

                    with st.spinner("AIがAパターンを採点中です..."):
                        try:
                            response_a = client.chat.completions.create(
                                model="gpt-4o",
                                messages=[
                                    {"role": "system", "content": "あなたは広告のプロです。"},
                                    {"role": "user", "content": [
                                        {"type": "text", "text":
                                            f"以下のバナー画像をプロ視点で採点してください。\n\n【評価基準】\n1. 内容が一瞬で伝わるか\n2. コピーの見やすさ\n3. 行動喚起\n4. 写真とテキストの整合性\n5. 情報量のバランス\n\n【出力形式】\n---\nスコア：{score_format}\n改善コメント：2～3行でお願いします\n---"},
                                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str_a}"}}
                                    ]}
                                ],
                                max_tokens=600
                            )
                            content_a = response_a.choices[0].message.content
                            st.session_state.ai_response_a = content_a # Save raw AI response

                            score_match_a = re.search(r"スコア[:：]\s*(.+)", content_a)
                            comment_match_a = re.search(r"改善コメント[:：]\s*(.+)", content_a)
                            st.session_state.score_a = score_match_a.group(1).strip() if score_match_a else "取得できず"
                            st.session_state.comment_a = comment_match_a.group(1).strip() if comment_match_a else "取得できず"

                            # --- AUTOMATICALLY RECORD TO SPREADSHEET AFTER SCORING ---
                            data_a = {
                                "sheet_name": "record_log",
                                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "platform": sanitize(platform),
                                "category": sanitize(category),
                                "industry": sanitize(industry),
                                "score": sanitize(st.session_state.score_a),
                                "comment": sanitize(st.session_state.comment_a),
                                "result": sanitize(result_input),
                                "follower_gain": sanitize(follower_gain_input),
                                "memo": sanitize(memo_input),
                            }
                            try:
                                response_gas_a = requests.post(GAS_URL, json=data_a)
                                if response_gas_a.status_code == 200:
                                    # st.success("📊 スプレッドシートに記録しました！（Aパターン）") # Hide success message
                                    pass
                                else:
                                    st.error(f"❌ スプレッドシート送信エラー（Aパターン）: ステータスコード {response_gas_a.status_code}, 応答: {response_gas_a.text}")
                            except requests.exceptions.RequestException as e:
                                st.error(f"GASへのデータ送信中にネットワークエラーが発生しました（Aパターン）: {str(e)}")
                            except Exception as e:
                                st.error(f"GASへのデータ送信中に予期せぬエラーが発生しました（Aパターン）: {str(e)}")
                            # --- END AUTOMATIC RECORD ---

                        except Exception as e:
                            st.error(f"AI採点中にエラーが発生しました（Aパターン）: {str(e)}")
                            st.session_state.score_a = "エラー"
                            st.session_state.comment_a = "AI応答エラー"
                            
                    st.success("Aパターンの診断が完了しました！")
            
            # Display results outside the button's if block to persist on re-runs
            with result_col_a: # Column for results display
                if st.session_state.score_a: # Only display if score is available
                    st.markdown("### ✨ Aパターン診断結果")
                    st.metric("総合スコア", st.session_state.score_a)
                    st.info(f"**改善コメント:** {st.session_state.comment_a}")
                    
                    if industry in ["美容", "健康", "医療"]:
                        with st.spinner("⚖️ 薬機法チェックを実行中（Aパターン）..."):
                            # Note: Current Yakujiho check is against AI's improvement comments.
                            # For checking actual ad copy, a separate input field for ad copy would be needed.
                            yakujihou_prompt_a = f"""
以下の広告文（改善コメント）が薬機法に違反していないかをチェックしてください。
※これはバナー画像の内容に対するAIの改善コメントであり、実際の広告文ではありません。

---
{st.session_state.comment_a}
---

違反の可能性がある場合は、その理由も具体的に教えてください。
「OK」「注意あり」どちらかで評価を返してください。
"""
                            try:
                                yakujihou_response_a = client.chat.completions.create(
                                    model="gpt-4o",
                                    messages=[
                                        {"role": "system", "content": "あなたは広告表現の薬機法チェックを行う専門家です。"},
                                        {"role": "user", "content": yakujihou_prompt_a}
                                    ],
                                    max_tokens=500,
                                    temperature=0.3,
                                )
                                st.session_state.yakujihou_a = yakujihou_response_a.choices[0].message.content.strip() if yakujihou_response_a.choices else "薬機法チェックの結果を取得できませんでした。"
                                if "OK" in st.session_state.yakujihou_a:
                                    st.success(f"薬機法チェック：{st.session_state.yakujihou_a}")
                                else:
                                    st.warning(f"薬機法チェック：{st.session_state.yakujihou_a}")
                            except Exception as e:
                                st.error(f"薬機法チェック中にエラーが発生しました（Aパターン）: {str(e)}")
                                st.session_state.yakujihou_a = "エラー"

        st.markdown("---")

        # --- B Pattern Processing --- (Similar changes as A pattern applied)
        if uploaded_file_b:
            img_col_b, result_col_b = st.columns([1, 2]) # Image 1 part, results 2 parts

            with img_col_b:
                st.image(Image.open(uploaded_file_b), caption="Bパターン画像", use_container_width=True)
                if st.button("🚀 Bパターンを採点", key="score_b_btn"): # Changed button name
                    image_b = Image.open(uploaded_file_b) # Corrected to Image.open
                    buf_b = io.BytesIO()
                    image_b.save(buf_b, format="PNG")
                    img_str_b = base64.b64encode(buf_b.getvalue()).decode()

                    with st.spinner("AIがBパターンを採点中です..."):
                        try:
                            response_b = client.chat.completions.create(
                                model="gpt-4o",
                                messages=[
                                    {"role": "system", "content": "あなたは広告のプロです。"},
                                    {"role": "user", "content": [
                                        {"type": "text", "text":
                                            f"以下のバナー画像をプロ視点で採点してください。\n\n【評価基準】\n1. 内容が一瞬で伝わるか\n2. コピーの見やすさ\n3. 行動喚起\n4. 写真とテキストの整合性\n5. 情報量のバランス\n\n【出力形式】\n---\nスコア：{score_format}\n改善コメント：2～3行でお願いします\n---"},
                                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str_b}"}}
                                    ]}
                                ],
                                max_tokens=600
                            )
                            content_b = response_b.choices[0].message.content
                            st.session_state.ai_response_b = content_b

                            score_match_b = re.search(r"スコア[:：]\s*(.+)", content_b)
                            comment_match_b = re.search(r"改善コメント[:：]\s*(.+)", content_b)
                            st.session_state.score_b = score_match_b.group(1).strip() if score_match_b else "取得できず" # Corrected from comment_match_b to score_match_b
                            st.session_state.comment_b = comment_match_b.group(1).strip() if comment_match_b else "取得できず"

                            # --- AUTOMATICALLY RECORD TO SPREADSHEET AFTER SCORING ---
                            data_b = {
                                "sheet_name": "record_log",
                                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "platform": sanitize(platform),
                                "category": sanitize(category),
                                "industry": sanitize(industry),
                                "score": sanitize(st.session_state.score_b),
                                "comment": sanitize(st.session_state.comment_b),
                                "result": sanitize(result_input),
                                "follower_gain": sanitize(follower_gain_input),
                                "memo": sanitize(memo_input),
                            }
                            try:
                                response_gas_b = requests.post(GAS_URL, json=data_b)
                                if response_gas_b.status_code == 200:
                                    # st.success("📊 スプレッドシートに記録しました！（Bパターン）") # Hide success message
                                    pass
                                else:
                                    st.error(f"❌ スプレッドシート送信エラー（Bパターン）: ステータスコード {response_gas_b.status_code}, 応答: {response_gas_b.text}")
                            except requests.exceptions.RequestException as e:
                                st.error(f"GASへのデータ送信中にネットワークエラーが発生しました（Bパターン）: {str(e)}")
                            except Exception as e:
                                st.error(f"GASへのデータ送信中に予期せぬエラーが発生しました（Bパターン）: {str(e)}")
                            # --- END AUTOMATIC RECORD ---

                        except Exception as e:
                            st.error(f"AI採点中にエラーが発生しました（Bパターン）: {str(e)}")
                            st.session_state.score_b = "エラー"
                            st.session_state.comment_b = "AI応答エラー"
                    
                    st.success("Bパターンの診断が完了しました！")

            with result_col_b: # Column for results display
                if st.session_state.score_b: # Only display if score is available
                    st.markdown("### ✨ Bパターン診断結果")
                    st.metric("総合スコア", st.session_state.score_b)
                    st.info(f"**改善コメント:** {st.session_state.comment_b}")

                    if industry in ["美容", "健康", "医療"]:
                        with st.spinner("⚖️ 薬機法チェックを実行中（Bパターン）..."):
                            yakujihou_prompt_b = f"""
以下の広告文（改善コメント）が薬機法に違反していないかをチェックしてください。
※これはバナー画像の内容に対するAIの改善コメントであり、実際の広告文ではありません。

---
{st.session_state.comment_b}
---

違反の可能性がある場合は、その理由も具体的に教えてください。
「OK」「注意あり」どちらかで評価を返してください。
"""
                            try:
                                yakujihou_response_b = client.chat.completions.create(
                                    model="gpt-4o",
                                    messages=[
                                        {"role": "system", "content": "あなたは広告表現の薬機法チェックを行う専門家です。"},
                                        {"role": "user", "content": yakujihou_prompt_b}
                                    ],
                                    max_tokens=500,
                                    temperature=0.3,
                                )
                                st.session_state.yakujihou_b = yakujihou_response_b.choices[0].message.content.strip() if yakujihou_response_b.choices else "薬機法チェックの結果を取得できませんでした。"
                                if "OK" in st.session_state.yakujihou_b:
                                    st.success(f"薬機法チェック：{st.session_state.yakujihou_b}")
                                else:
                                    st.warning(f"薬機法チェック：{st.session_state.yakujihou_b}")
                            except Exception as e:
                                st.error(f"薬機法チェック中にエラーが発生しました（Bパターン）: {str(e)}")
                                st.session_state.yakujihou_b = "エラー"

        st.markdown("---")
        # AB Test Comparison Function (displayed if both scores are available)
        if st.session_state.score_a and st.session_state.score_b and \
           st.session_state.score_a != "エラー" and st.session_state.score_b != "エラー":
            if st.button("📊 A/Bテスト比較を実行", key="ab_compare_final_btn"):
                with st.spinner("AIがA/Bパターンを比較しています..."):
                    ab_compare_prompt = f"""
以下のAパターンとBパターンの広告診断結果を比較し、総合的にどちらが優れているか、その理由と具体的な改善点を提案してください。

---
Aパターン診断結果:
スコア: {st.session_state.score_a}
改善コメント: {st.session_state.comment_a}
薬機法チェック: {st.session_state.yakujihou_a}

Bパターン診断結果:
スコア: {st.session_state.score_b}
改善コメント: {st.session_state.comment_b}
薬機法チェック: {st.session_state.yakujihou_b}
---

【出力形式】
---
総合評価: Aパターンが優れている / Bパターンが優れている / どちらも改善が必要
理由: (2〜3行で簡潔に)
今後の改善提案: (具体的なアクションを1〜2点)
---
"""
                    try:
                        ab_compare_response = client.chat.completions.create(
                            model="gpt-4o", # A/B comparison also uses GPT-4o
                            messages=[
                                {"role": "system", "content": "あなたは広告のプロであり、A/Bテストのスペシャリストです。"},
                                {"role": "user", "content": ab_compare_prompt}
                            ],
                            max_tokens=700,
                            temperature=0.5,
                        )
                        ab_compare_content = ab_compare_response.choices[0].message.content.strip()
                        st.markdown("### 📈 A/Bテスト比較結果")
                        st.write(ab_compare_content)
                    except Exception as e:
                        st.error(f"A/Bテスト比較中にエラーが発生しました: {str(e)}")

with col2:
    with st.expander("📌 採点基準はこちら", expanded=True): # Expand by default
        st.markdown("バナスコAIは以下の観点に基づいて広告画像を評価します。")
        st.markdown(
            """
        - **1. 内容が一瞬で伝わるか**
            - 伝えたいことが最初の1秒でターゲットに伝わるか。
        - **2. コピーの見やすさ**
            - 文字が読みやすいか、サイズや配色が適切か。
        - **3. 行動喚起の明確さ**
            - 『今すぐ予約』『LINE登録』などの行動喚起が明確で、ユーザーを誘導できているか。
        - **4. 写真とテキストの整合性**
            - 背景画像と文字内容が一致し、全体として違和感がないか。
        - **5. 情報量のバランス**
            - 文字が多すぎず、視線誘導が自然で、情報が過負荷にならないか。
        """
        )

    st.markdown("---")
    st.info(
        "💡 **ヒント:** スコアやコメントは、広告改善のヒントとしてご活用ください。AIの提案は参考情報であり、最終的な判断は人間が行う必要があります。"
    )
```
