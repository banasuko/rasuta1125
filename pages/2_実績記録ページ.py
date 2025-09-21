import streamlit as st
import pandas as pd
from firestore_client import get_firestore_db
from datetime import datetime, timedelta
import auth_utils
from fpdf import FPDF
import io

# ---------------------------
# ページ設定 & ログインチェック
# ---------------------------
st.set_page_config(layout="wide", page_title="バナスコAI - 実績記録")
auth_utils.check_login()

# ---------------------------
# Firestoreからデータ取得
# ---------------------------
def get_user_records(user_id):
    db = get_firestore_db()
    records_ref = db.collection('users').document(user_id).collection('records')
    records = [doc.to_dict() for doc in records_ref.stream()]
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    # タイムスタンプをdatetimeオブジェクトに変換
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

# ---------------------------
# PDF生成関数
# ---------------------------
def create_pdf(dataframe):
    pdf = FPDF()
    pdf.add_page()

    # 日本語フォントを追加
    # プロジェクトのルートにあるフォントファイルを指定
    try:
        pdf.add_font('NotoSansJP', '', 'NotoSansJP-Regular.ttf', uni=True)
        pdf.set_font('NotoSansJP', '', 10)
    except Exception as e:
        # フォント読み込みエラーの代替処理
        st.warning(f"フォントの読み込みに失敗しました。PDFは標準フォントで生成されます。エラー: {e}")
        pdf.set_font('Arial', '', 10)

    # ヘッダー
    col_widths = {'日付': 30, 'カテゴリ': 35, 'ターゲット': 45, '生成コピー': 80}
    for col_name, width in col_widths.items():
        pdf.cell(width, 10, col_name, border=1, ln=0, align='C')
    pdf.ln()

    # データ行
    for index, row in dataframe.iterrows():
        # 日付を 'YYYY-MM-DD HH:MM' 形式にフォーマット
        date_str = row['timestamp'].strftime('%Y-%m-%d %H:%M')
        
        # サービスの改行をスペースに置換
        service_text = row.get('service', 'N/A').replace('\n', ' ')

        # 各セルの高さを揃えるためにMultiCellを使用
        x_before = pdf.get_x()
        y_before = pdf.get_y()
        
        pdf.multi_cell(col_widths['日付'], 8, date_str, border=1, align='L')
        pdf.set_xy(x_before + col_widths['日付'], y_before)
        
        pdf.multi_cell(col_widths['カテゴリ'], 8, row.get('category', 'N/A'), border=1, align='L')
        pdf.set_xy(x_before + col_widths['日付'] + col_widths['カテゴリ'], y_before)

        pdf.multi_cell(col_widths['ターゲット'], 8, row.get('target_audience', 'N/A'), border=1, align='L')
        pdf.set_xy(x_before + col_widths['日付'] + col_widths['カテゴリ'] + col_widths['ターゲット'], y_before)

        pdf.multi_cell(col_widths['生成コピー'], 8, service_text, border=1, align='L')
        
    # PDFをバイトデータとして返す
    return pdf.output(dest='S').encode('latin-1')


# ---------------------------
# メインUI
# ---------------------------
st.title("📊 実績記録")

if "user" not in st.session_state or st.session_state["user"] is None:
    st.warning("ログインしてください。")
    st.stop()

user_id = st.session_state["user"]["uid"]
df = get_user_records(user_id)

if df.empty:
    st.info("まだ実績記録はありません。")
else:
    # 表示用データフレームの準備
    display_df = df.copy()
    display_df = display_df.rename(columns={
        'timestamp': '日付',
        'category': 'カテゴリ',
        'target_audience': 'ターゲット',
        'service': '生成コピー' # 列名をUIに合わせて変更
    })

    # 日付で降順にソート
    display_df = display_df.sort_values(by='日付', ascending=False)
    
    # 日付のフォーマットを 'YYYY-MM-DD HH:MM' に変更
    display_df['日付'] = display_df['日付'].dt.strftime('%Y-%m-%d %H:%M')

    # 表示する列を選択
    display_df = display_df[['日付', 'カテゴリ', 'ターゲット', '生成コピー']]

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # --- PDFダウンロードボタン ---
    st.markdown("---")
    
    # PDF生成
    pdf_data = create_pdf(display_df)
    
    # ダウンロードボタン
    st.download_button(
        label="📄 PDFとしてダウンロード",
        data=pdf_data,
        file_name=f"実績記録_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
    )
