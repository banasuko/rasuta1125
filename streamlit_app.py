from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4-vision-preview",
    messages=[
        {
            "role": "system",
            "content": "あなたは優秀な広告デザイナーです。"
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "以下の基準に従って、この広告バナーをプロの視点で**遠慮なく厳しく辛口で**採点してください：\n\n【評価基準】\n1. 何の広告かが一瞬で伝わるか（内容の明確さ）\n2. メインコピーの見やすさ（フォント・サイズ・色の使い方）\n3. 行動喚起があるか（予約・購入などにつながるか）\n4. 写真とテキストが噛み合っているか（世界観や目的にズレがないか）\n5. 情報量のバランス（不要な装飾・ごちゃごちゃしていないか）\n\n【出力フォーマット】\nスコア：A / B / C（A: 優れた広告 / B: 改善の余地あり / C: 問題が多い）\n改善コメント：端的に2〜3行で具体的に指摘（甘口NG、曖昧表現NG）"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img_str}"
                    }
                }
            ]
        }
    ],
    max_tokens=600
)
