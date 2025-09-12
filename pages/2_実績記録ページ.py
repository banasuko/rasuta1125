import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import auth_utils 
import os # osライブラリをインポートしてファイルのパスを操作

# --- ★★★ PDF生成用の日本語フォントへのパスを自動で解決 ★★★ ---
# スクリプトの絶対パスを取得し、そこからプロジェクトのルートディレクトリを特定
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, os.pardir))
FONT_PATH = os.path.join(project_root, "NotoSansJP-Regular.ttf")

class PDF(FPDF):
    def header(self):
        try:
            # 修正された絶対パスを使用
            self.add_font('NotoSansJP', '', FONT_PATH, uni=True)
            self.set_font('NotoSansJP', '', 12)
        except RuntimeError:
            self.set_font('Arial', 'B', 12)
            if 'font_warning_shown' not in st.session_state:
                st.warning(f"日本語フォントファイル '{FONT_PATH}' が見つかりません。PDFの日本語が文字化けする可能性があります。")
                st.session_state.font_warning_shown = True
        
        self.cell(0, 10, '広告実績レポート', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        try:
            self.set_font('NotoSansJP', '', 8)
        except RuntimeError:
            self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def table_header(self, header, col_widths):
        try:
            self.set_font('NotoSansJP', '', 8)
        except RuntimeError:
            self.set_font('Arial', 'B', 8)
        
        self.set_fill_color(230, 230, 230)
        for i, col_name in enumerate(header):
            self.cell(col_widths[i], 7, col_name, 1, 0, 'C', 1)
        self.ln()

    def table_body(self, data, col_widths):
        try:
            self.set_font('NotoSansJP', '', 8)
        except RuntimeError:
            self.set_font('Arial', '', 8)

        for row in data:
            x_before = self.get_x()
            y_before = self.get_y()
            max_y = y_before

            for i, item in enumerate(row):
                width = col_widths[i]
                self.multi_cell(width, 5, str(item), border=0, align='L')
                if self.get_y() > max_y:
                    max_y = self.get_y()
                self.set_xy(x_before + sum(col_widths[:i+1]), y_before)
            
            self.set_xy(x_before, y_before)
            
            for i, item in enumerate(row):
                self.rect(self.get_x(), self.get_y(), col_widths[i], max_y - y_before)
                self.set_x(self.get_x() + col_widths[i])

            self.ln(max_y - y_before)


# Streamlitページの基本設定
st.set_page_config(page_title="実績記録", layout="wide")

# --- ログイン & プランチェック ---
auth_utils.check_login()
user_plan = st.session_state.get("plan", "Guest")

# ★★★ Lightプラン以上でない場合はアクセス制限 ★★★
if user_plan in ["Free", "Guest"]:
    st.warning("このページはLightプラン以上の限定機能です。")
    st.info("実績記録を管理するには、プランのアップグレードが必要です。")
    st.stop()

st.title("📋 バナスコ｜広告実績記録ページ")
st.markdown("AIによる採点結果が自動で記録されます。実際の広告費やCTRなどの成果は、後からこの表で直接編集・追記してください。")

# --- Firestoreからデータを取得 ---
uid = st.session_state.user

records_data = auth_utils.get_diagnosis_records_from_firestore(uid)
if records_data:
    records_df = pd.DataFrame(records_data)
else:
    records_df = pd.DataFrame()

# ★★★ 表示・編集する列を定義（新しい項目を追加） ★★★
display_cols = [
    "user_name", "banner_name", "platform", "category", "score", "predicted_ctr",
    "ad_cost", "impressions", "clicks", "actual_ctr", "actual_cvr", "notes"
]
for col in display_cols:
    if col not in records_df.columns:
        records_df[col] = ""

# --- データエディタで表を表示・編集 ---
edited_df = st.data_editor(
    records_df[display_cols],
    column_config={
        "user_name": "ユーザー名",
        "banner_name": "バナー名",
        "platform": "媒体",
        "category": "カテゴリ",
        "score": "AIスコア",
        "predicted_ctr": "AI予測CTR",
        "ad_cost": st.column_config.NumberColumn("広告費 (円)", format="¥%d"),
        "impressions": st.column_config.NumberColumn("Impression数"),
        "clicks": st.column_config.NumberColumn("クリック数"),
        "actual_ctr": st.column_config.NumberColumn("実CTR (%)", format="%.2f%%"),
        "actual_cvr": st.column_config.NumberColumn("実CVR (%)", format="%.2f%%"),
        "notes": "メモ"
    },
    num_rows="dynamic",
    height=500,
    use_container_width=True,
    key="data_editor"
)

# --- 保存ボタンとPDFエクスポートボタン ---
col1, col2, _ = st.columns([1, 1, 2])
with col1:
    if st.button("💾 編集内容を保存", type="primary"):
        with st.spinner("保存中..."):
            try:
                if auth_utils.save_diagnosis_records_to_firestore(uid, edited_df):
                    st.success("実績を保存しました！")
                else:
                    st.error("保存に失敗しました。")
            except Exception as e:
                st.error(f"保存中にエラーが発生しました: {e}")

with col2:
    df_for_pdf = edited_df.fillna('')
    if not df_for_pdf.empty:
        pdf = PDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()
        pdf.chapter_title(f"ユーザー: {st.session_state.email} の広告実績")

        header = [
            "ユーザー名", "バナー名", "媒体", "カテゴリ", "スコア", "予測CTR",
            "広告費", "Imp", "Clicks", "実CTR", "実CVR", "メモ"
        ]
        col_widths = [20, 30, 15, 15, 12, 18, 20, 20, 20, 15, 15, 70]
        
        pdf.table_header(header, col_widths)
        pdf.table_body(df_for_pdf[display_cols].values.tolist(), col_widths)

        # PDFをバイトデータとして出力
        pdf_output = pdf.output(dest='S').encode('latin1')

        st.download_button(
            label="📄 PDFでエクスポート",
            data=pdf_output,
            file_name=f"banasuko_report_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
        )
