import streamlit as st
import base64
import io
import os
import re
import requests
from PIL import Image
from datetime import datetime
from openai import OpenAI

import auth_utils  # Import auth_utils.py

# Google Apps Script (GAS) and Google Drive information
GAS_URL = "https://script.google.com/macros/s/AKfycby_uD6Jtb9GT0-atbyPKOPc8uyVKodwYVIQ2Tpe-_E8uTOPiir0Ce1NAPZDEOlCUxN4/exec"  # 必要に応じて更新

# Helper function to sanitize values
def sanitize(value):
    """Replaces None or specific strings with 'エラー' (Error)"""
    if value is None or value == "取得できず":
        return "エラー"
    return value

# Streamlit UI configuration
st.set_page_config(layout="wide", page_title="バナスコAI")

# --- Logo Display ---
logo_path = "banasuko_logo_icon.png"
try:
    logo_image = Image.open(logo_path)
    st.sidebar.image(logo_image, use_container_width=True)
except FileNotFoundError:
    st.sidebar.error(f"ロゴ画像 '{logo_path}' が見つかりません。配置を確認してください。")

# --- Login Check ---
auth_utils.check_login()

# --- OpenAI Client Initialization ---
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    st.error("❌ OpenAI APIキーが見つかりませんでした。`.env` を確認してください。")
    st.stop()
client = OpenAI(api_key=openai_api_key)

# --- Custom CSS ---
st.markdown(
    """
    <style>
    /* 省略: カスタムスタイル */
    </style>
    """,
    unsafe_allow_html=True
)

# --- アプリケーション本体 ---
st.title("🧠 バナー広告 採点AI - バナスコ")
st.subheader("〜もう、無駄打ちしない。広告を“武器”に変えるAIツール〜")

col1, col2 = st.columns([2, 1])

with col1:
    with st.container():  # border引数を削除しました
        st.subheader("📝 バナー情報入力フォーム")
        # --- フォーム ---
        with st.expander("👤 基本情報", expanded=True):
            user_name = st.text_input("ユーザー名")
            age_group = st.selectbox(
                "ターゲット年代",
                ["指定なし", "10代", "20代", "30代", "40代", "50代", "60代以上"]
            )
            platform = st.selectbox("媒体", ["Instagram", "GDN", "YDN"])
            category = st.selectbox(
                "カテゴリ",
                ["広告", "投稿"] if platform == "Instagram" else ["広告"]
            )
            has_ad_budget = st.selectbox("広告予算", ["あり", "なし"])
            purpose = st.selectbox(
                "目的",
                ["プロフィール誘導", "リンククリック", "保存数増加", "インプレッション増加"]
            )

        with st.expander("🎯 詳細設定", expanded=True):
            industry = st.selectbox("業種", ["美容", "飲食", "不動産", "子ども写真館", "その他"])
            genre = st.selectbox(
                "ジャンル", ["お客様の声", "商品紹介", "ノウハウ", "世界観", "キャンペーン"]
            )
            score_format = st.radio("スコア形式", ["A/B/C", "100点満点"], horizontal=True)
            ab_pattern = st.radio("ABテストパターン", ["Aパターン", "Bパターン", "該当なし"], horizontal=True)
            banner_name = st.text_input("バナー名")

        with st.expander("📌 任意項目", expanded=False):
            result_input = st.text_input("AI評価結果（任意）")
            follower_gain_input = st.text_input("フォロワー増加数（任意）")
            memo_input = st.text_area("メモ（任意）")

        st.markdown("---")
        st.subheader("🖼️ バナー画像アップロードと診断")
        uploaded_file_a = st.file_uploader("Aパターン画像をアップロード", type=["png", "jpg", "jpeg"])
        uploaded_file_b = st.file_uploader("Bパターン画像をアップロード", type=["png", "jpg", "jpeg"])

        # セッションステート初期化
        for key in ["score_a", "comment_a", "yakujihou_a", "score_b", "comment_b", "yakujihou_b"]:
            if key not in st.session_state:
                st.session_state[key] = None

        # --- A パターン ---
        if uploaded_file_a:
            img_col_a, result_col_a = st.columns([1, 2])
            with img_col_a:
                st.image(Image.open(uploaded_file_a), caption="Aパターン画像", use_container_width=True)
                if st.button("🚀 Aパターンを採点", key="score_a_btn"):
                    if st.session_state.remaining_uses <= 0:
                        st.warning(f"残り回数がありません。（{st.session_state.plan}プラン）")
                        st.info("プランのアップグレードをご検討ください。")
                    else:
                        if auth_utils.update_user_uses_in_firestore_rest(
                            st.session_state["user"], st.session_state["id_token"]
                        ):
                            # 画像 bytes と base64
                            image_a_bytes = io.BytesIO()
                            Image.open(uploaded_file_a).save(image_a_bytes, format="PNG")
                            img_str_a = base64.b64encode(image_a_bytes.getvalue()).decode()

                            # Firebase Storage へのアップロード
                            image_url_a = auth_utils.upload_image_to_firebase_storage(
                                st.session_state["user"], image_a_bytes, f"banner_A_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                            )

                            if image_url_a:
                                with st.spinner("AIがAパターンを採点中です..."):
                                    try:
                                        ai_prompt_text = f"""
以下のバナー画像をプロ視点で採点してください。
年齢: {age_group}, 目的: {purpose}
【評価基準】1.伝わりやすさ 2.コピー見やすさ 3.行動喚起 4.整合性 5.バランス
"""
                                        response_a = client.chat.completions.create(
                                            model="gpt-4o",
                                            messages=[
                                                {"role": "system", "content": "あなたは広告のプロです。"},
                                                {"role": "user", "content": [
                                                    {"type": "text", "text": ai_prompt_text},
                                                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str_a}"}}
                                                ]}
                                            ],
                                            max_tokens=600
                                        )
                                        content_a = response_a.choices[0].message.content
                                        st.session_state.ai_response_a = content_a
                                        # スコアとコメント抽出
                                        st.session_state.score_a = (
                                            re.search(r"スコア[:：]\s*(.+)", content_a).group(1).strip()
                                            if re.search(r"スコア[:：]\s*(.+)", content_a)
                                            else "取得できず"
                                        )
                                        st.session_state.comment_a = (
                                            re.search(r"改善コメント[:：]\s*(.+)", content_a).group(1).strip()
                                            if re.search(r"改善コメント[:：]\s*(.+)", content_a)
                                            else "取得できず"
                                        )

                                        # Firestore へ記録
                                        firestore_record_data = {
                                            "timestamp": datetime.now().isoformat() + "Z",
                                            "platform": sanitize(platform),
                                            "category": sanitize(category),
                                            "industry": sanitize(industry),
                                            "age_group": sanitize(age_group),
                                            "purpose": sanitize(purpose),
                                            "score": sanitize(st.session_state.score_a),
                                            "comment": sanitize(st.session_state.comment_a),
                                            "result": sanitize(result_input),
                                            "follower_gain": sanitize(follower_gain_input),
                                            "memo": sanitize(memo_input),
                                            "image_url": image_url_a
                                        }
                                        if auth_utils.add_diagnosis_record_to_firestore(
                                            st.session_state["user"], st.session_state["id_token"], firestore_record_data
                                        ):
                                            st.success("📊 診断結果をFirestoreに記録しました！")
                                        else:
                                            st.error("❌ 記録に失敗しました。")
                                    except Exception as e:
                                        st.error(f"AI採点中にエラーが発生しました（Aパターン）: {str(e)}")
                                        st.session_state.score_a = "エラー"
                                        st.session_state.comment_a = "AI応答エラー"
                            else:
                                st.error("画像アップロードに失敗しました。")
                        else:
                            st.error("利用回数の更新に失敗しました。")
                    st.success("Aパターンの診断が完了しました！")

            with result_col_a:
                if st.session_state.score_a:
                    st.markdown("### ✨ Aパターン診断結果")
                    st.metric("総合スコア", st.session_state.score_a)
                    st.info(f"**改善コメント:** {st.session_state.comment_a}")

                    if industry in ["美容", "健康", "医療"]:
                        with st.spinner("⚖️ 薬機法チェックを実行中（Aパターン）..."):
                            try:
                                yakujihou_prompt_a = f"""
以下の広告文（改善コメント）が薬機法に違反していないかチェックしてください。
---
{st.session_state.comment_a}
---
"""
                                yakujihou_response_a = client.chat.completions.create(
                                    model="gpt-4o",
                                    messages=[
                                        {"role": "system", "content": "あなたは広告表現の専門家です。"},
                                        {"role": "user", "content": yakujihou_prompt_a}
                                    ],
                                    max_tokens=500,
                                    temperature=0.3,
                                )
                                st.session_state.yakujihou_a = yakujihou_response_a.choices[0].message.content.strip()
                                if "OK" in st.session_state.yakujihou_a:
                                    st.success(f"薬機法チェック：{st.session_state.yakujihou_a}")
                                else:
                                    st.warning(f"薬機法チェック：{st.session_state.yakujihou_a}")
                            except Exception as e:
                                st.error(f"薬機法チェック中にエラーが発生しました: {str(e)}")
                                st.session_state.yakujihou_a = "エラー"

        st.markdown("---")

        # --- B パターン ---
        if uploaded_file_b:
            img_col_b, result_col_b = st.columns([1, 2])
            with img_col_b:
                st.image(Image.open(uploaded_file_b), caption="Bパターン画像", use_container_width=True)
                if st.button("🚀 Bパターンを採点", key="score_b_btn"):
                    if st.session_state.plan == "Free":
                        st.warning("この機能はFreeプランではご利用いただけません。")
                        st.info("プランのアップグレードを検討してください。")
                    elif st.session_state.remaining_uses <= 0:
                        st.warning(f"残り回数がありません。（{st.session_state.plan}プラン）")
                        st.info("プランのアップグレードを検討してください。")
                    else:
                        if auth_utils.update_user_uses_in_firestore_rest(
                            st.session_state["user"], st.session_state["id_token"]
                        ):
                            image_b_bytes = io.BytesIO()
                            Image.open(uploaded_file_b).save(image_b_bytes, format="PNG")
                            img_str_b = base64.b64encode(image_b_bytes.getvalue()).decode()

                            image_url_b = auth_utils.upload_image_to_firebase_storage(
                                st.session_state["user"], image_b_bytes, f"banner_B_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                            )
                            if image_url_b:
                                with st.spinner("AIがBパターンを採点中です..."):
                                    try:
                                        ai_prompt_text = f"""
以下のバナー画像をプロ視点で採点してください。
年齢: {age_group}, 目的: {purpose}
【評価基準】1.伝わりやすさ 2.コピー見やすさ 3.行動喚起 4.整合性 5.バランス
"""
                                        response_b = client.chat.completions.create(
                                            model="gpt-4o",
                                            messages=[
                                                {"role": "system", "content": "あなたは広告のプロです。"},
                                                {"role": "user", "content": [
                                                    {"type": "text", "text": ai_prompt_text},
                                                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str_b}"}}
                                                ]}
                                            ],
                                            max_tokens=600
                                        )
                                        content_b = response_b.choices[0].message.content
                                        st.session_state.ai_response_b = content_b
                                        # スコアとコメント抽出
                                        st.session_state.score_b = (
                                            re.search(r"スコア[:：]\s*(.+)", content_b).group(1).strip()
                                            if re.search(r"スコア[:：]\s*(.+)", content_b)
                                            else "取得できず"
                                        )
                                        st.session_state.comment_b = (
                                            re.search(r"改善コメント[:：]\s*(.+)", content_b).group(1).strip()
                                            if re.search(r"改善コメント[:：]\s*(.+)", content_b)
                                            else "取得できず"
                                        )
                                        # Firestore へ記録
                                        firestore_record_data = {
                                            "timestamp": datetime.now().isoformat() + "Z",
                                            "platform": sanitize(platform),
                                            "category": sanitize(category),
                                            "industry": sanitize(industry),
                                            "age_group": sanitize(age_group),
                                            "purpose": sanitize(purpose),
                                            "score": sanitize(st.session_state.score_b),
                                            "comment": sanitize(st.session_state.comment_b),
                                            "result": sanitize(result_input),
                                            "follower_gain": sanitize(follower_gain_input),
                                            "memo": sanitize(memo_input),
                                            "image_url": image_url_b
                                        }
                                        if auth_utils.add_diagnosis_record_to_firestore(
                                            st.session_state["user"], st.session_state["id_token"], firestore_record_data
                                        ):
                                            st.success("📊 診断結果をFirestoreに記録しました！")
                                        else:
                                            st.error("❌ 記録に失敗しました。")
                                    except Exception as e:
                                        st.error(f"AI採点中にエラーが発生しました（Bパターン）: {str(e)}")
                                        st.session_state.score_b = "エラー"
                                        st.session_state.comment_b = "AI応答エラー"
                            else:
                                st.error("画像アップロードに失敗しました。")
                        else:
                            st.error("利用回数の更新に失敗しました。")
                    st.success("Bパターンの診断が完了しました！")

            with result_col_b:
                if st.session_state.score_b:
                    st.markdown("### ✨ Bパターン診断結果")
                    st.metric("総合スコア", st.session_state.score_b)
                    st.info(f"**改善コメント:** {st.session_state.comment_b}")

                    if industry in ["美容", "健康", "医療"]:
                        with st.spinner("⚖️ 薬機法チェックを実行中（Bパターン）..."):
                            try:
                                yakujihou_prompt_b = f"""
以下の広告文（改善コメント）が薬機法に違反していないかチェックしてください。
---
{st.session_state.comment_b}
---
"""
                                yakujihou_response_b = client.chat.completions.create(
                                    model="gpt-4o",
                                    messages=[
                                        {"role": "system", "content": "あなたは広告表現の専門家です。"},
                                        {"role": "user", "content": yakujihou_prompt_b}
                                    ],
                                    max_tokens=500,
                                    temperature=0.3,
                                )
                                st.session_state.yakujihou_b = yakujihou_response_b.choices[0].message.content.strip()
                                if "OK" in st.session_state.yakujihou_b:
                                    st.success(f"薬機法チェック：{st.session_state.yakujihou_b}")
                                else:
                                    st.warning(f"薬機法チェック：{st.session_state.yakujihou_b}")
                            except Exception as e:
                                st.error(f"薬機法チェック中にエラーが発生しました: {str(e)}")
                                st.session_state.yakujihou_b = "エラー"

        st.markdown("---")
        # ABテスト比較
        if st.session_state.score_a and st.session_state.score_b:
            if st.button("📊 A/Bテスト比較を実行", key="ab_compare_final_btn"):
                with st.spinner("AIがA/Bパターンを比較しています..."):
                    try:
                        ab_compare_prompt = f"""
以下のA/B診断結果を比較してください。
A: {st.session_state.score_a} / {st.session_state.comment_a} / {st.session_state.yakujihou_a}
B: {st.session_state.score_b} / {st.session_state.comment_b} / {st.session_state.yakujihou_b}
"""
                        ab_compare_response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {"role": "system", "content": "あなたはA/Bテストの専門家です。"},
                                {"role": "user", "content": ab_compare_prompt}
                            ],
                            max_tokens=700,
                            temperature=0.5,
                        )
                        st.markdown("### 📈 A/Bテスト比較結果")
                        st.write(ab_compare_response.choices[0].message.content)
                    except Exception as e:
                        st.error(f"A/Bテスト比較中にエラーが発生しました: {str(e)}")

with col2:
    with st.expander("📌 採点基準はこちら", expanded=True):
        st.markdown("バナスコAIは以下の観点に基づいて広告画像を評価します。")
        st.markdown(
            """
- **内容が一瞬で伝わるか**
- **コピーの見やすさ**
- **行動喚起の明確さ**
- **写真とテキストの整合性**
- **情報量のバランス**
"""
        )
    st.markdown("---")
    st.info("💡 AIの提案は参考情報です。最終判断は人間でお願いします。")
