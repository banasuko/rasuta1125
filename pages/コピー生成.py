import streamlit as st
import os
from PIL import Image
from openai import OpenAI
from datetime import datetime

import auth_utils  # Firebase 認証/残回数管理

# ---------------------------
# ページ設定 & ログインチェック
# ---------------------------
st.set_page_config(layout="wide", page_title="バナスコAI - コピー生成")
auth_utils.check_login()

# OpenAI 初期化
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    st.error("❌ OpenAI APIキーが見つかりませんでした。`.env` を確認してください。")
    st.stop()
client = OpenAI(api_key=openai_api_key)

st.title("📸 バナー画像からコピー案を生成")

# ---------------------------
# 1) 画像アップロード（任意）
# ---------------------------
uploaded_image = st.file_uploader("バナー画像をアップロード（任意）", type=["jpg", "png"])
if uploaded_image:
    image = Image.open(uploaded_image)
    st.image(image, caption="アップロードされた画像", use_container_width=True)

# ---------------------------
# 2) 業種カテゴリ
# ---------------------------
category = st.selectbox(
    "業種カテゴリを選択",
    [
        "美容室", "脱毛サロン", "エステ", "ネイル・まつげ", "ホワイトニング",
        "整体・接骨院", "学習塾", "子ども写真館", "飲食店", "その他"
    ]
)

# ---------------------------
# 3) 基本情報
# ---------------------------
col1, col2 = st.columns(2)
with col1:
    target = st.text_input("ターゲット層（例：30代女性、経営者など）")
    tone = st.selectbox("トーン（雰囲気）", ["親しみやすい", "高級感", "情熱的", "おもしろ系", "真面目"])
with col2:
    feature = st.text_area("商品の特徴・アピールポイント（箇条書きOK）", height=120)

# ---------------------------
# 4) 生成オプション（UIを拡張）
# ---------------------------
st.markdown("### ⚙️ 生成オプション")

# プランと残回数
user_plan = st.session_state.get("plan", "Guest")
remaining_uses = st.session_state.get("remaining_uses", 0)

# プラン別 1リクエストあたりの最大生成数
plan_to_max = {
    "Free": 0, "Guest": 0,
    "Light": 3, "Pro": 5, "Team": 10, "Enterprise": 10
}
max_copy_count_per_request = plan_to_max.get(user_plan, 0)
if max_copy_count_per_request == 0:
    copy_count_options = [0]
else:
    copy_count_options = list(range(1, max_copy_count_per_request + 1))

# コピータイプ
st.caption("コピータイプ（複数選択可）")
type_cols = st.columns(4)
with type_cols[0]:
    want_main = st.checkbox("メインコピー")
with type_cols[1]:
    want_catch = st.checkbox("キャッチコピー", value=True)
with type_cols[2]:
    want_cta = st.checkbox("CTAコピー")
with type_cols[3]:
    want_sub = st.checkbox("サブコピー")

# 生成数
copy_count = st.selectbox(
    f"生成数（各タイプにつき / 上限: {max_copy_count_per_request}案）",
    copy_count_options,
    index=0 if 0 in copy_count_options else 0,
    format_func=lambda x: f"{x}パターン" if x > 0 else "—"
)

# 絵文字 / 緊急性
opt_cols = st.columns(2)
with opt_cols[0]:
    include_emoji = st.checkbox("絵文字を含める")
with opt_cols[1]:
    include_urgency = st.checkbox("緊急性要素を含める（例：期間限定・先着・残りわずか）")

# 投稿文作成ブロック
st.markdown("---")
st.subheader("📝 投稿文作成（任意）")
enable_caption = st.checkbox("投稿文も作成する")
caption_lines = 0
caption_keywords = ""
if enable_caption:
    caption_lines = st.selectbox("投稿文の行数", [1, 2, 3, 4, 5], index=2)
    caption_keywords = st.text_input("任意で含めたいワード（カンマ区切り）", placeholder="例）初回割引, 予約リンク, 土日OK")

# ---------------------------
# 5) 生成ボタン
# ---------------------------
needs_yakkihou = category in ["脱毛サロン", "エステ", "ホワイトニング"]

def build_prompt():
    # コピータイプの指示をまとめる
    type_instructions = []
    if want_main:
        type_instructions.append(f"- **メインコピー**：{copy_count}案")
    if want_catch:
        type_instructions.append(f"- **キャッチコピー**：{copy_count}案")
    if want_cta:
        type_instructions.append(f"- **CTAコピー**：{copy_count}案")
    if want_sub:
        type_instructions.append(f"- **サブコピー**：{copy_count}案")
    if not type_instructions and not enable_caption:
        return None  # 何も選ばれていない

    emoji_rule = "・各案に1〜2個の絵文字を自然に入れてください。" if include_emoji else "・絵文字は使用しないでください。"
    urgency_rule = "・必要に応じて『期間限定』『先着順』『残りわずか』などの緊急性フレーズも自然に織り交ぜてください。" if include_urgency else ""
    yakki_rule = "・薬機法/医療広告ガイドラインに抵触する表現は避けてください（例：治る、即効、永久、医療行為の示唆 など）。" if needs_yakkihou else ""
    cap_rule = ""
    if enable_caption and caption_lines > 0:
        cap_rule = f"""
### 投稿文作成
- 改行で{caption_lines}行の投稿文を作成（行ごとに要点を変えてください）
- 1行あたり読みやすい長さ（40〜60文字目安）
- ターゲットとトーンに合わせて自然な日本語
- ハッシュタグは付けない
- 任意ワードがあれば必ず自然に含める（過剰な羅列は禁止）
"""

    keywords_text = f"任意ワード：{caption_keywords}" if caption_keywords else "任意ワード：なし"

    # 最終プロンプト
    return f"""
あなたは優秀な広告コピーライターです。下記条件に沿って、用途別に日本語で提案してください。出力は**Markdown**で、各セクションに見出しを付け、番号付きリストで返してください。

【業種】{category}
【ターゲット層】{target or '未指定'}
【特徴・アピールポイント】{feature or '未指定'}
【トーン】{tone}
【{keywords_text}】
【共通ルール】
- 同じ方向性を避け、毎案ニュアンスを変える
- 媒体に載せやすい簡潔な文
- 露骨な煽りは避けつつ、訴求は明確に
{emoji_rule}
{urgency_rule}
{yakki_rule}

### 生成対象
{os.linesep.join(type_instructions) if type_instructions else '- （コピータイプなし）'}

{cap_rule}

### 追加ガイド
- **キャッチコピー**：インパクト重視/30字以内目安
- **メインコピー**：価値が伝わる説明的コピー/40字前後
- **サブコピー**：補足やベネフィット/60字以内
- **CTAコピー**：行動喚起/16字以内/明快

出力フォーマット例：
## キャッチコピー
1. 〜
2. 〜

## メインコピー
1. 〜
...

{ '## 投稿文\n1)\n2)\n...' if enable_caption else '' }
"""

generate_btn = st.button("🚀 コピーを生成する")

if generate_btn:
    # プランチェック
    if user_plan in ["Free", "Guest"]:
        st.warning("この機能はFree/Guestプランではご利用いただけません。Light以上のプランでご利用ください。")
        st.stop()
    # 残回数チェック
    if remaining_uses <= 0:
        st.warning(f"残り回数がありません。（現在プラン：{user_plan}）")
        st.info("利用回数を増やすには、プランのアップグレードが必要です。")
        st.stop()
    # 生成数チェック
    if copy_count == 0 and not enable_caption:
        st.warning("コピー生成数が0です。少なくとも1案以上を選択するか、投稿文作成を有効にしてください。")
        st.stop()

    prompt = build_prompt()
    if prompt is None:
        st.warning("コピータイプが1つも選択されていません。少なくとも1つ選択してください。")
        st.stop()

    with st.spinner("コピー案を生成中..."):
        try:
            # OpenAI へ投げる
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたは日本語に精通した広告コピーライターです。マーケ基礎と法規を理解し、簡潔で効果的な表現を作ります。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,
            )
            output = resp.choices[0].message.content.strip()

            # 表示
            st.subheader("✍️ 生成結果")
            st.markdown(output)

            if needs_yakkihou:
                st.subheader("🔍 薬機法メモ")
                st.info("※ このカテゴリでは『治る／即効／永久／医療行為の示唆』などはNG。効能・効果の断定表現も避けましょう。")

            # 使⽤回数の消費（失敗してもアプリが落ちないよう try）
            try:
                if auth_utils.update_user_uses_in_firestore_rest(
                    st.session_state.get("user"),
                    st.session_state.get("id_token")
                ):
                    # UI上の残回数を1減らす
                    st.session_state["remaining_uses"] = max(0, remaining_uses - 1)
            except Exception:
                pass

        except Exception as e:
            st.error(f"コピー生成中にエラーが発生しました：{e}")
