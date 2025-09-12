import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import auth_utils 
import os # osライブラリをインポートしてファイルのパスを操作
import requests # 画像ダウンロード用
from PIL import Image # 画像処理用
import io # バイトデータ処理用

# --- ★★★ PDF生成用の日本語フォントへのパスを自動で解決 ★★★ ---
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, os.pardir))
FONT_PATH = os.path.join(project_root, "NotoSansJP-Regular.ttf")

class PDF(FPDF):
    def header(self):
        try:
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
                # MultiCellの前にY位置を記録
                cell_start_y = self.get_y()
                self.multi_cell(width, 5, str(item), border=0, align='L')
                # MultiCell後のY位置と比較
                if self.get_y() - cell_start_y > max_y - y_before:
                    max_y = self.get_y() # 最もY位置が進んだセルを基準にする
                self.set_xy(x_before + sum(col_widths[:i+1]), y_before)
            
            self.set_xy(x_before, y_before)
            
            # 各セルの枠線を描画し、Y位置を合わせる
            for i, item in enumerate(row):
                self.rect(self.get_x(), self.get_y(), col_widths[i], max_y - y_before)
                self.set_x(self.get_x() + col_widths[i])

            self.ln(max_y - y_before) # 最も高くなったセルの高さで行送りを調整
            
    def add_image_from_url(self, url, x, y, w=0, h=0, max_w=80, max_h=80):
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            img_data = io.BytesIO(response.content)
            
            # PILで画像サイズを取得し、アスペクト比を保ちつつ最大サイズに調整
            img = Image.open(img_data)
            original_width, original_height = img.size

            if w == 0 and h == 0:
                # 最大幅・高さに合わせて自動調整
                aspect_ratio = original_width / original_height
                if original_width > max_w:
                    w = max_w
                    h = w / aspect_ratio
                if h > max_h:
                    h = max_h
                    w = h * aspect_ratio
                if w == 0 and h == 0: # どちらも上限以下の場合
                    w = original_width
                    h = original_height
            elif w == 0:
                w = h * aspect_ratio
            elif h == 0:
                h = w / aspect_ratio
            
            self.image(img_data, x=x, y=y, w=w, h=h, type='PNG') # PNGとして追加
            return w, h
        except Exception as e:
            st.error(f"PDFへの画像追加に失敗しました: {e} (URL: {url})")
            return 0, 0


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
    # image_url列を追加（存在しない場合）
    if 'image_url' not in records_df.columns:
        records_df['image_url'] = None
    # 'id'をindexにするか、後で処理しやすいように保持
    records_df.set_index('id', inplace=True, drop=False) 
else:
    records_df = pd.DataFrame(columns=[
        "id", "user_name", "banner_name", "platform", "category", "score", "predicted_ctr",
        "ad_cost", "impressions", "clicks", "actual_ctr", "actual_cvr", "notes", "image_url"
    ])

# ★★★ 表示・編集する列を定義（新しい項目を追加） ★★★
display_cols = [
    "user_name", "banner_name", "platform", "category", "score", "predicted_ctr",
    "ad_cost", "impressions", "clicks", "actual_ctr", "actual_cvr", "notes"
    # image_urlは表示のみで編集不可のため、data_editorのcolumn_configには含めない
]

# DataFrameに列が存在しない場合は作成
for col in display_cols:
    if col not in records_df.columns:
        records_df[col] = ""

# --- データエディタで表を表示・編集 ---
edited_df = st.data_editor(
    records_df[display_cols], # image_urlは編集しない
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
                # edited_dfにimage_urlを追加
                # edited_dfはdisplay_colsのみなので、元のrecords_dfからimage_urlを結合する
                # indexがidになっているので、それを使って結合
                df_to_save = edited_df.copy()
                if 'image_url' in records_df.columns:
                    df_to_save = df_to_save.merge(
                        records_df[['id', 'image_url']], 
                        on='id', 
                        how='left', 
                        suffixes=('_edited', None)
                    )
                    df_to_save['image_url'] = df_to_save['image_url'].fillna(records_df['image_url'])

                if auth_utils.save_diagnosis_records_to_firestore(uid, df_to_save):
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

        # --- 各レコードに対して画像と詳細情報を追加 ---
        for index, row in edited_df.iterrows():
            pdf.ln(5)
            # 画像URLを元のrecords_dfから取得
            image_url = records_df.loc[index, 'image_url'] if 'image_url' in records_df.columns and index in records_df.index else None

            if image_url:
                # PDFに画像を追加（x, yは現在位置、w, hは最大サイズ）
                # 現在のY位置を基準に画像を配置
                current_y = pdf.get_y()
                image_w, image_h = pdf.add_image_from_url(image_url, x=pdf.get_x(), y=current_y, max_w=80, max_h=60)
                
                # 画像の右横にテキスト情報を追加
                # x座標を画像が配置された位置の右側に設定
                text_x = pdf.get_x() + image_w + 5 
                text_y = current_y # 画像と同じ高さから開始

                pdf.set_xy(text_x, text_y)
                try:
                    pdf.set_font('NotoSansJP', '', 10)
                except RuntimeError:
                    pdf.set_font('Arial', '', 10)
                
                pdf.multi_cell(pdf.w - text_x - pdf.r_margin, 5, 
                               f"バナー名: {row.get('banner_name', '')}\n"
                               f"カテゴリ: {row.get('category', '')}\n"
                               f"AIスコア: {row.get('score', '')}\n"
                               f"AI予測CTR: {row.get('predicted_ctr', '')}%", 
                               border=0, align='L')
                
                # 画像とテキストのどちらか大きい方の高さで行送りを調整
                pdf.set_y(max(current_y + image_h + 5, pdf.get_y()))
            else:
                # 画像がない場合でもテキスト情報は出力
                try:
                    pdf.set_font('NotoSansJP', '', 10)
                except RuntimeError:
                    pdf.set_font('Arial', '', 10)
                pdf.multi_cell(0, 5, 
                               f"バナー名: {row.get('banner_name', '')} (画像なし)\n"
                               f"カテゴリ: {row.get('category', '')}\n"
                               f"AIスコア: {row.get('score', '')}\n"
                               f"AI予測CTR: {row.get('predicted_ctr', '')}%", 
                               border=0, align='L')
                pdf.ln(5) # 少し余白

            pdf.ln(5) # 各バナー情報の区切り
            if pdf.get_y() > (pdf.h - pdf.b_margin - 30): # 次の要素が入らない場合
                pdf.add_page()
                pdf.chapter_title("続き")


        # --- 既存のテーブルデータを追加 ---
        pdf.add_page()
        pdf.chapter_title("詳細データテーブル")
        
        header = [
            "ユーザー名", "バナー名", "媒体", "カテゴリ", "スコア", "予測CTR",
            "広告費", "Imp", "Clicks", "実CTR", "実CVR", "メモ"
        ]
        # 列幅を合計257mm (A4横のマージンを除いた幅) に近づけるように調整
        col_widths = [20, 30, 15, 15, 12, 18, 20, 20, 20, 15, 15, 70] 
        
        pdf.table_header(header, col_widths)
        pdf.table_body(df_for_pdf[display_cols].values.tolist(), col_widths)

        pdf_output = pdf.output(dest='S').encode('latin1')

        st.download_button(
            label="📄 PDFでエクスポート",
            data=pdf_output,
            file_name=f"banasuko_report_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
        )
