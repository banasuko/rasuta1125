if submit:
    import pandas as pd
    import os

    data = {
        "掲載日": [date],
        "キャンペーン名": [campaign],
        "バナー名": [banner_name],
        "メディア": [platform],
        "カテゴリ": [category],
        "スコア": [score],
        "広告費": [ad_cost],
        "インプレッション数": [impressions],
        "クリック数": [clicks],
        "フォロワー増加数": [followers],
        "メモ": [notes],
    }

    df = pd.DataFrame(data)

    # ファイルが既にある場合は追記、なければ新規作成
    file_path = "record_data.csv"
    if os.path.exists(file_path):
        df.to_csv(file_path, mode="a", header=False, index=False)
    else:
        df.to_csv(file_path, index=False)

    st.success("✅ データを保存しました！")
