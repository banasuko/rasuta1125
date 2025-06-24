
import streamlit as st
import base64
import io
import os
import requests
from PIL import Image
from datetime import datetime
from openai import OpenAI
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# --- 設定 ---
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)
GAS_URL = "https://script.google.com/macros/s/AKfycbxjiaQDKTARUWGrDjsDv1WdIYOw3nRu0lo5y1-mcl91Q1aRjyYoENOYBRJNwe5AvH0p/exec"
FOLDER_ID = "1oRyCu2sU9idRrj5tq5foQXp3ArtCW7rP"  # Google DriveフォルダID

# --- Google Drive アップロード関数 ---
def upload_image_to_drive_get_url(pil_image, filename):
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("credentials.json")
    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()
    gauth.SaveCredentialsFile("credentials.json")
    drive = GoogleDrive(gauth)
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    buf.seek(0)
    file_drive = drive.CreateFile({
        'title': filename,
        'mimeType': 'image/png',
        'parents': [{'id': FOLDER_ID}]
    })
    file_drive.SetContentString(base64.b64encode(buf.read()).decode(), encoding='base64')
    file_drive.Upload()
    file_drive.InsertPermission({'type': 'anyone', 'role': 'reader'})
    return f"https://drive.google.com/uc?export=view&id={file_drive['id']}"

# --- UI ---
st.set_page_config(layout="wide", page_title="バナスコAI")
st.title("🧠 バナー広告 採点AI - バナスコ")

col1, col2 = st.columns([2, 1])

with col1:
    user_name = st.text_input("ユーザー名")
    platform = st.selectbox("媒体", ["Instagram", "GDN", "YDN"])
    category = st.selectbox("カテゴリ", ["広告", "投稿"] if platform == "Instagram" else ["広告"])
    has_ad_budget = st.selectbox("広告予算", ["あり", "なし"])
    purpose = st.selectbox("目的", ["プロフィール誘導", "リンククリック", "保存数増加"])
    industry = st.selectbox("業種", ["美容", "飲食", "不動産", "子ども写真館", "その他"])
    genre = st.selectbox("ジャンル", ["お客様の声", "商品紹介", "ノウハウ", "世界観", "キャンペーン"])
    mode = st.selectbox("採点方式", ["単発", "ABテスト"])
    banner_name = st.text_input("バナー名（任意）")
    result = st.text_input("実績（任意）")
    follower_gain = st.text_input("フォロワー増加（任意）")
    memo = st.text_area("メモ（任意）")
    score_format = st.radio("スコア形式", ["A/B/C", "100点満点"], horizontal=True)
    ab_pattern = st.radio("ABテストパターン", ["Aパターン", "Bパターン", "該当なし"], horizontal=True)
    uploaded_file = st.file_uploader("バナー画像をアップロード", type=["png", "jpg", "jpeg"])

    if uploaded_file and st.button("🚀 採点＋保存"):
    # 処理続き...

        image = Image.open(uploaded_file)
        st.image(image, caption="アップロード画像", use_column_width=True)
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        img_str = base64.b64encode(buf.getvalue()).decode()
        with st.spinner("AIが採点中です..."):
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたは広告のプロです。"},
                    {"role": "user", "content": [
                        {"type": "text", "text": """以下の広告バナーをプロ視点で採点してください：\n\n【評価基準】\n1. 内容が一瞬で伝わるか\n2. コピーの見やすさ\n3. 行動喚起\n4. 写真とテキストの整合性\n5. 情報量のバランス\n\n【出力形式】\nスコア：A/B/C\n改善コメント：2～3行"""},
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
        image_url = upload_image_to_drive_get_url(image, uploaded_file.name)
        data = {
            "ジャンル": genre,
            "スコア形式": score_format,
            "ABパターン": ab_pattern,
            "用途種別": category,
            "提案日": datetime.today().strftime("%Y-%m-%d"),
            "画像URL": image_url,
            "採点日": datetime.today().strftime("%Y-%m-%d"),
            "業種": industry,
            "投稿or広告": category,
            "媒体": platform,
            "点数": score,
            "コメント": comment,
            "修正案あり": "あり" if comment else "なし",
            "実施状況": "未実施",
            "クリック率": "",
            "CPC": "",
            "フォロワー増加数": follower_gain,
            "保存数": "",
            "備考": memo
        }
        response = requests.post(GAS_URL, json=data)
        st.write("📡 GAS応答ステータスコード:", response.status_code)
        st.write("📄 GAS応答本文:", response.text)
        if response.status_code == 200:
            st.success("📊 スプレッドシートに記録しました！")
        else:
            st.error("❌ スプレッドシート送信エラー")

with col2:
    with st.expander("📌 採点基準はこちら", expanded=False):
        st.markdown("**1. 内容が一瞬で伝わるか**\n伝えたいことが最初の1秒で伝わるかどうか")
        st.markdown("**2. コピーの見やすさ**\n文字が読みやすく、サイズ・配色が適切か")
        st.markdown("**3. 行動喚起**\n「今すぐ予約」「LINE登録」などが明確か")
        st.markdown("**4. 写真とテキストの整合性**\n背景画像と文字内容が合っているか")
        st.markdown("**5. 情報量のバランス**\n文字が多すぎず、視線誘導があるか")
