import streamlit as st
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import util # util.pyをインポート

st.set_page_config(layout="wide", page_title="使い方ガイド")

# --- 共通スタイルの適用 ---
# util.apply_common_style() 
# もしstyle.cssファイルを作成した場合は、 util.load_css('style.css') を使用します。
# 今回はデモのため、各ページでCSSを直接読み込む形を維持します。
st.markdown("""
<style>
/* ... (他のページからコピーした共通CSS) ... */
.stApp { background: linear-gradient(135deg, #0f0f1a 0%, #1a1c29 15%, #2d3748 35%, #1a202c 50%, #2d3748 65%, #4a5568 85%, #2d3748 100%) !important; }
.main .block-container { background: rgba(26, 32, 44, 0.4) !important; backdrop-filter: blur(60px) !important; border: 2px solid rgba(255, 255, 255, 0.1) !important; border-radius: 32px !important; padding: 5rem 4rem !important; margin: 2rem auto !important; max-width: 1000px !important; }
h1, .stTitle { font-size: 3.5rem !important; font-weight: 900 !important; background: linear-gradient(135deg, #38bdf8, #a855f7, #3b82f6, #06d6a0, #f59e0b, #38bdf8) !important; background-size: 600% 600% !important; -webkit-background-clip: text !important; -webkit-text-fill-color: transparent !important; text-align: center !important; animation: mega-gradient-shift 12s ease-in-out infinite !important; }
@keyframes mega-gradient-shift { 0%, 100% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } }
p, div, span, label, .stMarkdown, .stCheckbox, h2, h3 { color: #ffffff !important; }
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


st.title("📖 使い方ガイド")
st.markdown("BanasukoAIの各機能の使い方について説明します。")
st.markdown("---")

# --- 各ページの機能説明 ---
st.header("1. コピー生成")
st.markdown("""
このページでは、AIがバナー広告やSNS投稿に使えるキャッチコピーを生成します。

**基本的な使い方**
1.  **業種カテゴリ**を選択します。業種に特有の言い回しやルール（薬機法など）をAIが考慮します。
2.  **ターゲット層**や**商品の特徴**を具体的に入力するほど、より的確なコピーが生成されやすくなります。
3.  **生成オプション**で、欲しいコピーの種類（メイン、キャッチなど）や雰囲気を指定します。
4.  **「コピーを生成する」**ボタンを押すと、AIが複数のコピー案を提案します。

**💡 TIPS**
- 生成されたコピーは、そのまま使うだけでなく、アイデアのヒントとしてご活用ください。
- 「投稿文も作成する」オプションをオンにすると、SNS投稿に便利な文章も同時に作成できます。
""")

st.header("2. 実績記録ページ")
st.markdown("""
過去に生成したコピーや、実際に使用して効果のあった広告の実績を記録・管理するためのページです。

**基本的な使い方**
1.  過去の実績が一覧で表示されます。
2.  **「新しい実績を追加」**ボタンから、新規の記録を作成できます。
3.  **媒体**（例: Instagram、Google広告）、**クリック率（CTR）**、**コンバージョン率（CVR）**などの数値を記録することで、どのようなコピーが良い結果につながるかを分析できます。

**💡 TIPS**
- 定期的に実績を振り返ることで、次の広告戦略の改善に役立ちます。
- メモ欄に、広告配信時の所感や顧客の反応などを記録しておくと、より価値のあるデータになります。
""")

st.header("3. プラン購入")
st.markdown("""
ご利用プランの確認とアップグレードが可能です。

**現在のプラン**
- ログイン後、ページ上部に現在ご契約中のプランと、コピー生成の残り回数が表示されます。

**アップグレード**
- Freeプランよりも多くの機能や生成回数が必要な場合は、LightプランやProプランへのアップグレードをご検討ください。
- 各プランの詳細は、このページでご確認いただけます。
""")

st.header("4. お問い合わせ")
st.markdown("""
サービスに関するご質問、不具合のご報告、改善のご要望などを運営チームに直接送信できます。

**メッセージの送信**
1.  お名前（任意）、返信先のメールアドレス、お問い合わせ内容を入力してください。
2.  内容に間違いがないかご確認の上、「送信する」ボタンを押してください。
3.  運営チームにて内容を確認し、3営業日以内にご返信いたします。
""")
