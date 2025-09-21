import streamlit as st
import pandas as pd
import auth_utils
from openai import OpenAI
import os
from fpdf import FPDF
from datetime import datetime

# ---------------------------
# ページ設定 & ログインチェック
# ---------------------------
st.set_page_config(layout="wide", page_title="バナスコAI - 実績記録")
auth_utils.check_login()

# --- Ultimate Professional CSS Theme ---
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
# ★★★ プランによるアクセス制御 ★★★
# ---------------------------
user_plan = st.session_state.get("plan", "Guest")

st.title("📊 実績記録ページ")
st.markdown("過去の診断結果を一覧で確認・編集できます。")
st.markdown("---")

if user_plan not in ["Pro", "Team", "Enterprise"]:
    st.warning("実績記録ページの閲覧・編集機能はProプラン以上でご利用いただけます。")
    st.info("プランをアップグレードすると、過去の診断結果を一覧で管理・分析できるようになります。")
    st.stop()  # ★★★ Proプラン未満はここで処理を停止 ★★★

# ---------------------------
# --- 以下、Proプラン以上のみが表示・実行 ---
# ---------------------------
try:
    # Firestoreからデータを取得
    records = auth_utils.get_diagnosis_records_from_firestore(st.session_state["user"])

    if not records:
        st.info("まだ実績記録がありません。バナー診断ページから採点を行うと自動で記録されます。")
        st.stop()

    # データフレームに変換
    df = pd.DataFrame(records)

    # created_atがTimestamp型の場合、datetimeに変換
    if 'created_at' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['created_at']):
        df['created_at'] = df['created_at'].apply(
            lambda x: x.to_datetime() if hasattr(x, 'to_datetime') else pd.to_datetime(x)
        )

    # 見やすいように列の順番を調整
    desired_order = [
        "id", "banner_name", "pattern", "score", "comment", "predicted_ctr",
        "platform", "category", "industry", "age_group", "purpose", "genre",
        "result", "follower_gain", "memo", "image_url", "created_at"
    ]
    existing_cols = [col for col in desired_order if col in df.columns]
    df_ordered = df[existing_cols]

    st.info("💡 各セルをダブルクリックすると内容を編集できます。編集後は下の「変更を保存する」ボタンを押してください。")

    # データエディタで表示・編集
    edited_df = st.data_editor(
        df_ordered,
        key="diagnosis_editor",
        num_rows="dynamic",  # 行の追加・削除を許可
        use_container_width=True,
        column_config={
            "image_url": st.column_config.ImageColumn(
                "バナー画像", help="クリックで拡大表示"
            ),
            "created_at": st.column_config.DatetimeColumn(
                "診断日時",
                format="YYYY/MM/DD HH:mm",
            ),
            "comment": st.column_config.TextColumn(
                "コメント",
                width="large",
            ),
        },
        height=600  # 高さを固定してスクロール可能に
    )

    if st.button("変更を保存する", type="primary"):
        with st.spinner("保存中..."):
            if auth_utils.save_diagnosis_records_to_firestore(st.session_state["user"], edited_df):
                st.success("変更を保存しました！")
                st.rerun()
            else:
                st.error("保存に失敗しました。")

    # ---------------------------
    # 追加機能: CSV / PDF エクスポート
    # ---------------------------
    st.markdown("---")
    st.subheader("📥 データエクスポート")

    # === CSVダウンロード ===
    csv_bytes = edited_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇️ CSVでダウンロード",
        data=csv_bytes,
        file_name=f"実績記録_{datetime.now():%Y%m%d}.csv",
        mime="text/csv",
    )

    # === PDFダウンロード ===
    def create_pdf(dataframe: pd.DataFrame) -> bytes:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=10)

        # ヘッダー
        for col in dataframe.columns:
            pdf.cell(40, 8, str(col), border=1)
        pdf.ln()

        # 行
        for _, row in dataframe.iterrows():
            for col in dataframe.columns:
                txt = str(row[col]) if not pd.isna(row[col]) else ""
                pdf.cell(40, 8, txt[:15], border=1)  # 長文は切り捨て
            pdf.ln()

        return pdf.output(dest="S").encode("latin-1")

    pdf_bytes = create_pdf(edited_df)
    st.download_button(
        "📄 PDFでダウンロード",
        data=pdf_bytes,
        file_name=f"実績記録_{datetime.now():%Y%m%d}.pdf",
        mime="application/pdf",
    )

except Exception as e:
    st.error(f"データの読み込み中にエラーが発生しました: {e}")
    st.error("お手数ですが、ページを再読み込みしてください。")
