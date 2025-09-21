import streamlit as st
import sys
import os

# --- ▼▼▼ このブロックを追加 ▼▼▼ ---
# プロジェクトのルートディレクトリをPythonのパスに追加
# これにより、別階層にある auth_utils を正しくインポートできる
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# --- ▲▲▲ このブロックを追加 ▲▲▲ ---

import auth_utils

# ---------------------------
# ページ設定 & ログインチェック
# ---------------------------
st.set_page_config(layout="wide", page_title="バナスコAI - プラン購入")
auth_utils.check_login()


# ---------------------------
# ★★★ 商品ライブラリ ★★★
# ---------------------------
# 今後、新しいプランや商品を追加する場合は、このリストに新しい辞書を追加してください。
# ---------------------------
PRODUCT_LIBRARY = [
    {
        "name": "Lightプラン",
        "price": "月額¥1,000",
        "description": "【3ヶ月間の期間限定価格！】通常月額1,500円のところ、今ならこの価格。広告主や小規模店舗での日常的な運用に最適なプランです。",
        "features": [
            "月間利用回数：50回",
            "ABテスト診断",
            "CTR予測 & 改善提案",
            "コピー生成機能",
        ],
        "link": "https://buy.stripe.com/aFa6oG84YdRFbPd6Is18c01",
        "recommended": False,
    },
    {
        "name": "Proプラン",
        "price": "月額¥2,980",
        "description": "広告代理店や制作会社など、本格的に利用したい方向けのプランです。全機能が利用可能で、レポート出力や投稿文生成など、より高度な業務にも対応します。",
        "features": [
            "月間利用回数：200回",
            "Lightプランの全機能",
            "Instagram投稿文生成",
            "実績記録の保存・編集",
        ],
        "link": "https://buy.stripe.com/bJe6oG992cNBaL9aYI18c02",
        "recommended": True,
    },
    # --- 新しい商品を追加する場合は、ここに追記 ---
    # {
    #     "name": "新プラン名",
    #     "price": "¥X,XXX / 月",
    #     "description": "新プランの説明文です。",
    #     "features": ["機能1", "機能2"],
    #     "link": "https://新しいStripeリンク...",
    #     "recommended": False,
    # },
    # -----------------------------------------
]


# --- CSS ---
st.markdown("""
<style>
    .plan-card {
        border: 2px solid rgba(255, 255, 255, 0.2);
        border-radius: 16px;
        padding: 2rem;
        background: rgba(26, 32, 44, 0.6);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
        position: relative;
        display: flex;
        flex-direction: column;
        height: 100%;
    }
    .plan-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
        border-color: rgba(56, 189, 248, 0.8);
    }
    .plan-card h3 {
        color: #38bdf8;
        font-size: 1.8rem;
        margin-top: 0;
    }
    .plan-card .price {
        font-size: 2.5rem;
        font-weight: 700;
        color: white;
        margin: 0.5rem 0;
    }
    .plan-card .description {
        font-size: 0.9rem;
        line-height: 1.6;
        color: #a0aec0; /* slightly dimmer text */
        flex-grow: 1; /* Allow description to take up space */
    }
    .plan-card ul {
        list-style-type: '✅ ';
        padding-left: 20px;
        color: #a0aec0;
        flex-grow: 1;
    }
    .purchase-button-link {
        display: inline-block;
        width: 100%;
        text-align: center;
        padding: 1rem 2rem;
        background: linear-gradient(135deg, #38bdf8 0%, #a855f7 50%, #06d6a0 100%);
        color: white !important;
        text-decoration: none;
        border-radius: 60px;
        font-weight: 700;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        box-shadow: 0 10px 20px rgba(56, 189, 248, 0.3);
        margin-top: auto; /* Push button to the bottom */
    }
    .purchase-button-link:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 30px rgba(168, 85, 247, 0.4);
    }
    .recommended-badge {
        position: absolute;
        top: -15px;
        right: 20px;
        background: #f59e0b;
        color: black;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.9rem;
        transform: rotate(10deg);
    }
</style>
""", unsafe_allow_html=True)


# --- ページ本体 ---
st.title("💎 プランのご購入")
st.markdown("---")

# 残回数チェックと警告表示
remaining_uses = st.session_state.get("remaining_uses", 0)
if remaining_uses <= 0:
    st.warning(
        """
        ### ⚠️ 利用回数がなくなりました
        機能の利用を継続するには、プランのアップグレードが必要です。  
        以下のプランからご希望のものを選択し、購入手続きを行ってください。
        """
    )

# 商品ライブラリからプラン一覧を表示
columns = st.columns(len(PRODUCT_LIBRARY) or [1]) # Handle empty library

col_index = 0
for product in PRODUCT_LIBRARY:
    with columns[col_index]:
        # st.container() とカスタムCSSクラスでカードを作成
        st.markdown('<div class="plan-card">', unsafe_allow_html=True)
        
        # recommendedがTrueの場合、おすすめバッジを表示
        if product.get("recommended", False):
            st.markdown('<div class="recommended-badge">おすすめ！</div>', unsafe_allow_html=True)

        st.markdown(f"<h3>{product['name']}</h3>", unsafe_allow_html=True)
        st.markdown(f"<div class='price'>{product['price']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='description'>{product['description']}</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        if "features" in product:
            st.markdown("<ul>" + "".join([f"<li>{feature}</li>" for feature in product["features"]]) + "</ul>", unsafe_allow_html=True)

        st.markdown(
            f'<a href="{product["link"]}" target="_blank" class="purchase-button-link">このプランにアップグレード</a>',
            unsafe_allow_html=True
        )

        st.markdown('</div>', unsafe_allow_html=True)

    # 次の列へ
    col_index = (col_index + 1) % len(columns)


st.markdown("---")
st.info(
    """
    **【決済後の反映について】** 決済完了後、運営にてお客様の購入情報を確認いたします。  
    通常、**1〜2営業日以内**にアカウントへ利用回数が反映されますので、しばらくお待ちください。
    """
)
