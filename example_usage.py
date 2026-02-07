"""
総合健康リスクスコアシステムの使用例

このスクリプトは、リスクスコアシステムの基本的な使い方を示します。

⚠️ AI Generated Code
このコードは Claude Opus 4.6 (Anthropic社のAI) によって生成されました。
教育・デモンストレーション目的のみです。実際の医療現場での使用は禁止されています。
"""

from src.models.composite_risk import CompositeRiskModel


def example_healthy_patient():
    """正常健康者のサンプル"""
    print("=" * 60)
    print("例1: 正常健康者（35歳男性）")
    print("=" * 60)

    patient = {
        'SEQN': 99999,
        'RIAGENDR': 1,  # Male
        'RIDAGEYR': 35,
        'LBXTC': 180,      # 総コレステロール: 正常
        'LBDHDD': 55,      # HDL: 正常
        'LBDLDL': 95,      # LDL: 最適
        'LBXTR': 100,      # 中性脂肪: 正常
        'TC_HDL_ratio': 180/55,
        'LBXGLU': 90,      # 血糖: 正常
        'LBXGH': 5.2,      # HbA1c: 正常
        'LBXIN': 8,        # インスリン: 正常
        'HOMA_IR': (8 * 90) / 405,
        'LBXSCR': 0.9,     # クレアチニン: 正常
        'eGFR': 105,       # eGFR: 正常
        'ACR': 15,         # ACR: 正常
        'LBXSASSI': 22,    # AST: 正常
        'LBXSGTSI': 25,    # ALT: 正常
        'LBXPLTSI': 250,   # 血小板: 正常
        'FIB4': 0.8,       # FIB-4: 低リスク
        'AST_ALT_ratio': 22/25,
        'LBXSAL': 4.2,     # アルブミン: 正常
        'LBXSTB': 0.8,     # ビリルビン: 正常
        'LBXHGB': 15.0,    # ヘモグロビン: 正常
        'LBXWBCSI': 7.0,   # 白血球: 正常
        'LBXMCVSI': 90     # MCV: 正常
    }

    model = CompositeRiskModel()
    result = model.calculate_composite_score(patient)

    print_results(result)


def example_high_risk_patient():
    """高リスク患者のサンプル"""
    print("\n" + "=" * 60)
    print("例2: 高リスク患者（68歳女性）")
    print("=" * 60)

    patient = {
        'SEQN': 88888,
        'RIAGENDR': 2,  # Female
        'RIDAGEYR': 68,
        'LBXTC': 280,      # 総コレステロール: 高値
        'LBDHDD': 38,      # HDL: 低値
        'LBDLDL': 210,     # LDL: 最高値
        'LBXTR': 250,      # 中性脂肪: 高値
        'TC_HDL_ratio': 280/38,
        'LBXGLU': 140,     # 血糖: 糖尿病域
        'LBXGH': 7.2,      # HbA1c: 糖尿病域
        'LBXIN': 25,       # インスリン: 高値
        'HOMA_IR': (25 * 140) / 405,
        'LBXSCR': 1.8,     # クレアチニン: 高値
        'eGFR': 35,        # eGFR: G3b（中等度〜高度低下）
        'ACR': 120,        # ACR: 微量アルブミン尿
        'URXUMA': 120,
        'LBXSASSI': 58,    # AST: 高値
        'LBXSGTSI': 72,    # ALT: 高値
        'LBXPLTSI': 180,   # 血小板: やや低値
        'FIB4': 2.8,       # FIB-4: 中リスク
        'AST_ALT_ratio': 58/72,
        'LBXSAL': 3.2,     # アルブミン: 低値
        'LBXSTB': 1.5,     # ビリルビン: 高値
        'LBXHGB': 11.0,    # ヘモグロビン: 貧血
        'LBXWBCSI': 9.5,   # 白血球: やや高値
        'LBXMCVSI': 78     # MCV: 小球性
    }

    model = CompositeRiskModel()
    result = model.calculate_composite_score(patient)

    print_results(result)


def print_results(result):
    """結果を整形して表示"""
    print(f"\n総合スコア: {result['composite_score']:.1f}点")
    print(f"リスクレベル: {result['risk_level']} ({result['risk_label']})")

    print(f"\nドメイン別スコア:")
    for domain, score in result['domain_scores'].items():
        print(f"  {domain:15s}: {score:5.1f}点")

    if result['modifiable_factors']:
        print(f"\n修正可能因子: {len(result['modifiable_factors'])}個")
        for factor in result['modifiable_factors']:
            print(f"  - {factor}")

    if result['alerts']:
        print(f"\n警告: {len(result['alerts'])}件")
        for i, alert in enumerate(result['alerts'], 1):
            print(f"\n  警告{i}: {alert['domain']} ({alert['severity']})")
            print(f"  スコア: {alert['score']:.1f}点")
            print(f"  異常マーカー:")
            for marker in alert['abnormal_markers'][:3]:  # 最初の3つ
                print(f"    - {marker}")

    print(f"\n推奨事項:")
    for rec in result['recommendations'][:5]:  # 最初の5つ
        print(f"  - {rec}")


def example_batch_processing():
    """複数患者の一括処理例"""
    print("\n" + "=" * 60)
    print("例3: 複数患者の一括処理")
    print("=" * 60)

    import pandas as pd

    # サンプルデータ作成
    patients = [
        {'SEQN': 1, 'RIDAGEYR': 35, 'RIAGENDR': 1, 'LBDLDL': 95, 'LBDHDD': 55,
         'LBXGLU': 90, 'eGFR': 105, 'LBXHGB': 15.0},
        {'SEQN': 2, 'RIDAGEYR': 68, 'RIAGENDR': 2, 'LBDLDL': 210, 'LBDHDD': 38,
         'LBXGLU': 140, 'eGFR': 35, 'LBXHGB': 11.0},
        {'SEQN': 3, 'RIDAGEYR': 45, 'RIAGENDR': 1, 'LBDLDL': 150, 'LBDHDD': 42,
         'LBXGLU': 110, 'eGFR': 75, 'LBXHGB': 14.0},
    ]

    df = pd.DataFrame(patients)

    model = CompositeRiskModel()

    print("\n個別にスコア計算:")
    for idx, row in df.iterrows():
        result = model.calculate_composite_score(row)
        print(f"  患者{row['SEQN']}: スコア {result['composite_score']:.1f}点 ({result['risk_label']})")


if __name__ == "__main__":
    print("\n総合健康リスクスコアシステム - 使用例\n")

    try:
        example_healthy_patient()
        example_high_risk_patient()
        example_batch_processing()

        print("\n" + "=" * 60)
        print("すべての例が正常に実行されました")
        print("=" * 60)

    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        print("\n注意: このスクリプトを実行するには、以下を確認してください:")
        print("  1. 必要なライブラリがインストールされている (pip install -r requirements.txt)")
        print("  2. config/clinical_thresholds.yaml が存在する")
        print("  3. src/ ディレクトリ内のモジュールが正しく配置されている")
