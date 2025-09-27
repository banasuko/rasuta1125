# predictor.py

import base64
import io
import json
from typing import Dict, Any

import streamlit as st
from openai import OpenAI
from PIL import Image

# アプリケーションのバージョンを定義
# このバージョンを変更すると、キャッシュが無効化され、再計算が実行される
APP_VERSION = "1.0.0"

# Streamlitのキャッシュデコレータを使用
# 同じ画像バイトデータとバージョンに対しては、計算を行わずキャッシュ結果を返す
# ttl（Time To Live）を設定して、一定時間でキャッシュをクリアすることも可能
@st.cache_data(ttl="1d")
def get_banasuko_score(image_bytes: bytes, version: str) -> Dict[str, Any]:
    """
    OpenAIのGPT-4oモデルを使用して、バナー画像のスコアを決定論的に測定する。

    Args:
        image_bytes (bytes): 評価対象の画像データ（バイト列）。
        version (str): アプリケーションのバージョン。キャッシュのキーとして使用。

    Returns:
        Dict[str, Any]: 測定結果を含む辞書。
                         例: {"ctr": 5.8, "score": 85, "grade": "A", "reason": "..."}
    """
    try:
        # APIキーをStreamlitのsecretsから取得
        api_key = st.secrets["OPENAI_API_KEY"]
        if not api_key:
            raise ValueError("OpenAI APIキーが設定されていません。")

        client = OpenAI(api_key=api_key)

        # 画像をBase64にエンコード
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        # GPT-4oに渡すプロンプト（指示内容）
        # このプロンプトは変更しない限り、同じ評価基準で分析される
        prompt = """
あなたは広告クリエイティブを評価する専門家です。
提供されたバナー画像を分析し、以下の3つの指標をJSON形式で出力してください。

1.  **予想CTR (ctr)**:
    - このバナーが広告として配信された際のクリック率（%）を、具体的な数値で予測してください。
    - 数値（float）で出力してください。

2.  **総合スコア (score)**:
    - デザイン、コピー、訴求力、情報設計などを総合的に評価し、100点満点のスコアを付けてください。
    - 整数（integer）で出力してください。

3.  **ランク評価 (grade)**:
    - 総合スコアに基づき、S, A, B, C, Dの5段階でランク評価をしてください。
    - 文字列（string）で出力してください。

4.  **評価理由 (reason)**:
    - 上記の評価に至った具体的な理由を、200文字以内で簡潔に説明してください。
    - 文字列（string）で出力してください。

制約条件:
- 必ずJSON形式で、キーも指定通り（`ctr`, `score`, `grade`, `reason`）にしてください。
- 余計な説明や前置きは一切含めず、JSONオブジェクトのみを出力してください。
"""

        # OpenAI APIを呼び出し
        response = client.chat.completions.create(
            model="gpt-4o",  # 最新かつ高性能なモデルを指定
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            # --- 決定論的動作を保証するためのパラメータ ---
            temperature=0,  # 創造性をなくし、最も確からしい単語を選択させる
            seed=1125,      # 同じseed値であれば、同じ入力に対して同じ出力が生成される
            response_format={"type": "json_object"}, # 出力をJSON形式に強制
            max_tokens=500, # 最大トークン数を指定
        )

        # レスポンスからJSON文字列を抽出
        result_json_str = response.choices[0].message.content
        
        # JSON文字列を辞書に変換
        result_data = json.loads(result_json_str)

        # 結果が期待するキーを持っているか簡易的に検証
        required_keys = ["ctr", "score", "grade", "reason"]
        if not all(key in result_data for key in required_keys):
            raise ValueError("APIからのレスポンス形式が不正です。")

        return result_data

    except Exception as e:
        # エラーが発生した場合は、その内容を結果として返す
        st.error(f"分析中にエラーが発生しました: {e}")
        return {
            "error": str(e)
        }
