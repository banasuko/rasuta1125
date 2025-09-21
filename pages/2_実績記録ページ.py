import streamlit as st
import pandas as pd
import auth_utils
from fpdf import FPDF
from datetime import datetime
import os

# ---------------------------
# PDF生成用のヘルパー関数
# ---------------------------
def dataframe_to_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    
    # 日本語フォントを追加
    # フォントファイル 'NotoSansJP-Regular.ttf' がコードと同じ階層にあることを確認してください
    font_path = 'NotoSansJP-Regular.ttf'
    if not os.path.exists(font_path):
        st.error(f"日本語フォントファイル '{font_path}' が見つかりません。PDFをダウンロードできません。")
        return None
        
    try:
        pdf.add_font('NotoSansJP', '', font_path, uni=True)
        pdf.set_font('NotoSansJP', '', 8) # フォントサイズを小さめに設定
    except Exception as e:
        st.error(f"フォントの読み込み中にエラーが発生しました: {e}")
        return None

    # ヘッダー
    col_widths = {'banner_name': 40, 'comment': 80, 'score': 15, 'predicted_ctr': 20} # 列幅を調整
    for col in df.columns:
        width = col_widths.get(col, 25) # デフォルト幅
        pdf.cell(width, 10, col, 1, 0, 'C')
    pdf.ln()

    # データ行
    for index, row in df.iterrows():
        # 各行の高さを計算
        max_height = 10 # 基本の高さ
        for col_name, item in row.items():
            width = col_widths.get(col_name, 25)
            text = str(item).replace('\n', ' ')
            lines = pdf.multi_cell(width, 10, text, border=0, dry_run=True, output='L')
            if len(lines) * 10 > max_height:
                max_height = len(lines) * 10

        # セルを描画
        for col_name, item in row.items():
            width = col_widths.get(col_name, 25)
            text = str(item).replace('\n', ' ')
            pdf.multi_cell(width, max_height, text, 1, 'L')
        pdf.ln()
        
    # PDFデータをバイナリ形式で返す
    return pdf.output(dest='S').encode('latin-1')


# ---------------------------
# ページ設定 & ログインチェック
# ---------------------------
st.set_page_config(layout="wide", page_title="バナスコAI - 実績記録")
auth_utils.check_login()

# --- CSS ---
# (CSS部分は省略せずに全て含んでいます)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');
    
    .stDataFrame > div > div > div > div > div[data-testid="stDataGridColHeader"] {
        background-color: rgba(56, 189, 248, 0.2) !important;
        color: white !important;
        font-weight: 600 !important;
    }

    .stDataFrame > div > div > div > div > div[data-testid="stDataGridCell"] {
        background-color: #1a1c29 !important;
        color: #FBC02D !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
    }
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
        df_for_download = edited_df.drop(columns=['id', 'image_url', 'created_at'], errors='ignore')
        
        pdf_data = dataframe_to_pdf(df_for_download)
        if pdf_data:
            st.download_button(
                label="📜 PDFでダウンロード",
                data=pdf_data,
                file_name=f"banasuko_records_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

except Exception as e:
    st.error(f"データの読み込み中にエラーが発生しました: {e}")
    st.error("お手数ですが、ページを再読み込みしてください。")
