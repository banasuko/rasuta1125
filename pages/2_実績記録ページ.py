import streamlit as st
import pandas as pd
import auth_utils
from fpdf import FPDF
from datetime import datetime

# ---------------------------
# PDF生成用のヘルパー関数
# ---------------------------
def dataframe_to_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    
    # 日本語フォントを追加
    # NotoSansJP-Regular.ttf が同じディレクトリにあることを確認してください
    try:
        pdf.add_font('NotoSansJP', '', 'NotoSansJP-Regular.ttf', uni=True)
        pdf.set_font('NotoSansJP', '', 10)
    except RuntimeError:
        st.error("日本語フォントファイル 'NotoSansJP-Regular.ttf' が見つかりません。")
        return None

    # ヘッダー
    for col in df.columns:
        pdf.cell(40, 10, col, 1, 0, 'C')
    pdf.ln()

    # データ行
    for index, row in df.iterrows():
        for item in row:
            # セルの内容を文字列に変換し、改行をスペースに置換
            text = str(item).replace('\n', ' ')
            pdf.cell(40, 10, text, 1, 0, 'L')
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin-1')


# ---------------------------
# ページ設定 & ログインチェック
# ---------------------------
st.set_page_config(layout="wide", page_title="バナスコAI - 実績記録")
auth_utils.check_login()

# --- CSS ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');
    
    /* (長いCSSのため内容は省略しますが、元のコードをそのままお使いください) */

    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------
# プランによるアクセス制御
# ---------------------------
user_plan = st.session_state.get("plan", "Guest")

st.title("📊 実績記録ページ")
st.markdown("過去の診断結果を一覧で確認・編集できます。")
st.markdown("---")

if user_plan not in ["Pro", "Team", "Enterprise"]:
    st.warning("実績記録ページの閲覧・編集機能はProプラン以上でご利用いただけます。")
    st.info("プランをアップグレードすると、過去の診断結果を一覧で管理・分析できるようになります。")
    st.stop()


# ---------------------------
# --- 以下、Proプラン以上のみが表示・実行 ---
# ---------------------------
try:
    records = auth_utils.get_diagnosis_records_from_firestore(st.session_state["user"])

    if not records:
        st.info("まだ実績記録がありません。バナー診断ページから採点を行うと自動で記録されます。")
        st.stop()

    df = pd.DataFrame(records)

    if 'created_at' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['created_at']):
        df['created_at'] = df['created_at'].apply(lambda x: x.to_datetime() if hasattr(x, 'to_datetime') else pd.to_datetime(x))

    desired_order = [
        "id", "banner_name", "pattern", "score", "comment", "predicted_ctr",
        "platform", "category", "industry", "age_group", "purpose", "genre",
        "result", "follower_gain", "memo", "image_url", "created_at"
    ]
    existing_cols = [col for col in desired_order if col in df.columns]
    df_ordered = df[existing_cols]

    st.info("💡 各セルをダブルクリックすると内容を編集できます。編集後は下の「変更を保存する」ボタンを押してください。")

    edited_df = st.data_editor(
        df_ordered,
        key="diagnosis_editor",
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "image_url": st.column_config.ImageColumn("バナー画像", help="クリックで拡大表示"),
            "created_at": st.column_config.DatetimeColumn("診断日時", format="YYYY/MM/DD HH:mm"),
            "comment": st.column_config.TextColumn("コメント", width="large"),
        },
        height=600
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("変更を保存する", type="primary", use_container_width=True):
            with st.spinner("保存中..."):
                if auth_utils.save_diagnosis_records_to_firestore(st.session_state["user"], edited_df):
                    st.success("変更を保存しました！")
                    st.rerun()
                else:
                    st.error("保存に失敗しました。")
    
    with col2:
        # ★★★ ここから変更 ★★★
        # ダウンロード用に不要な列を削除
        df_for_download = edited_df.drop(columns=['id', 'image_url'], errors='ignore')
        
        pdf_data = dataframe_to_pdf(df_for_download)
        if pdf_data:
            st.download_button(
                label="📜 PDFでダウンロード",
                data=pdf_data,
                file_name=f"banasuko_records_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        # ★★★ ここまで変更 ★★★


except Exception as e:
    st.error(f"データの読み込み中にエラーが発生しました: {e}")
    st.error("お手数ですが、ページを再読み込みしてください。")
