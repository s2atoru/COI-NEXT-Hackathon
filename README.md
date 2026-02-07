# 医療機関向け総合健康リスクスコアシステム

NHANES 2017-2018データを活用した、医療機関・健診センター向けの総合健康リスク評価システムです。

## 概要

本システムは、複数の生理学的マーカーから以下を自動算出します:

- **総合健康リスクスコア（0-100点）**
- **5つのドメイン別評価**（心血管/代謝/肝/腎/血液）
- **リスク因子の特定**と臨床的に重要な異常値の抽出
- **警告メッセージ生成**（要精査レベルの自動判定）
- **医療機関向け推奨事項**

## 主な特徴

### 1. エビデンスベースの評価
- ACC/AHA 2019（心血管ガイドライン）
- ADA 2023（糖尿病診断基準）
- KDIGO 2012（慢性腎臓病分類）
- AASLD 2018（肝疾患ガイドライン）
- WHO基準（血液学的指標）

### 2. 5つの評価ドメイン

| ドメイン | 重み | 主要評価項目 |
|---------|------|------------|
| 心血管系 | 30% | LDL, HDL, 総コレステロール, 中性脂肪 |
| 代謝系 | 25% | 血糖, HbA1c, HOMA-IR |
| 腎機能 | 20% | eGFR, ACR（アルブミン/クレアチニン比） |
| 肝機能 | 15% | AST, ALT, FIB-4 Index |
| 血液系 | 10% | ヘモグロビン, 白血球, 血小板, MCV |

### 3. リスクレベル分類

| スコア | レベル | 推奨アクション |
|--------|--------|--------------|
| 0-20 | 最適 | 現状維持、年1回健診 |
| 20-40 | 低リスク | 生活習慣の維持、年1回健診 |
| 40-60 | 中リスク | 生活習慣改善指導、6ヶ月後再検査 |
| 60-80 | 高リスク | 専門医紹介検討、3ヶ月ごとフォロー |
| 80-100 | 要精査 | 専門医への即時紹介、精密検査 |

## システム構成

```
health-risk-assessment/
├── data/
│   ├── raw/                    # 元データ
│   └── processed/              # 前処理済みデータ
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 03_risk_model_development.ipynb
│   └── ...
├── src/
│   ├── data/                   # データ処理
│   │   ├── loader.py
│   │   ├── preprocessor.py
│   │   └── validator.py
│   ├── features/               # 特徴量エンジニアリング
│   ├── models/                 # リスク評価モデル
│   │   ├── cardiovascular_risk.py
│   │   ├── metabolic_risk.py
│   │   ├── renal_risk.py
│   │   ├── hepatic_risk.py
│   │   ├── hematologic_risk.py
│   │   └── composite_risk.py
│   └── reporting/              # レポート生成
├── config/
│   └── clinical_thresholds.yaml
├── tests/
├── requirements.txt
└── README.md
```

## インストール

### 1. リポジトリのクローン
```bash
git clone <repository-url>
cd COI-NEXT-Hackathon
```

### 2. 仮想環境の作成（推奨）
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate     # Windows
```

### 3. 依存ライブラリのインストール
```bash
pip install -r requirements.txt
```

## 使い方

### 1. データの配置
NHANESデータCSVファイルを `data/raw/` ディレクトリに配置します。

### 2. Jupyterノートブックの起動
```bash
jupyter notebook
```

### 3. データ探索と前処理
`notebooks/01_data_exploration.ipynb` を開いて実行:
- データの読み込み
- 基本統計量の確認
- 欠損値分析
- データの前処理
- 前処理済みデータの保存

### 4. リスクスコアの計算
`notebooks/03_risk_model_development.ipynb` を開いて実行:
- 各ドメインモデルのテスト
- 総合リスクスコアの計算
- スコア分布の可視化
- 高リスク患者の抽出

### 5. プログラムでの使用

```python
from src.models.composite_risk import CompositeRiskModel

# モデルの初期化
model = CompositeRiskModel()

# 患者データ
patient_data = {
    'SEQN': 12345,
    'RIAGENDR': 1,  # 1=Male, 2=Female
    'RIDAGEYR': 55,
    'LBXTC': 220,
    'LBDHDD': 45,
    'LBDLDL': 150,
    'LBXTR': 180,
    'LBXGLU': 105,
    'LBXSCR': 1.1,
    # ... 他のマーカー
}

# スコア計算
result = model.calculate_composite_score(patient_data)

# 結果の表示
print(f"総合スコア: {result['composite_score']:.1f}点")
print(f"リスクレベル: {result['risk_level']}")
print(f"ドメイン別スコア: {result['domain_scores']}")
print(f"警告: {len(result['alerts'])}件")
print(f"推奨事項:")
for rec in result['recommendations']:
    print(f"  - {rec}")
```

### 6. 一括処理

```python
import pandas as pd
from src.data.loader import NHANESLoader
from src.data.preprocessor import NHANESPreprocessor
from src.models.composite_risk import CompositeRiskModel

# データ読み込み
loader = NHANESLoader('data/raw')
df = loader.load_csv('your_data.csv')

# 前処理
preprocessor = NHANESPreprocessor()
df_processed = preprocessor.preprocess(df)

# 一括スコア計算
model = CompositeRiskModel()
df_with_scores = model.batch_calculate(df_processed)

# 結果の保存
df_with_scores.to_csv('data/processed/risk_scores.csv', index=False)
```

## 重要な派生変数

本システムでは以下の派生変数を自動計算します:

| 変数 | 計算式 | 用途 |
|------|--------|------|
| TC/HDL比 | 総コレステロール ÷ HDL | 心血管リスク |
| LDL/HDL比 | LDL ÷ HDL | 心血管リスク |
| eGFR | CKD-EPI式 | 腎機能評価 |
| HOMA-IR | (インスリン × 血糖) ÷ 405 | インスリン抵抗性 |
| FIB-4 Index | (年齢 × AST) ÷ (血小板 × √ALT) | 肝線維化 |
| AST/ALT比 | AST ÷ ALT | 肝疾患パターン |
| ACR | 尿中アルブミン ÷ 尿中クレアチニン × 1000 | 腎疾患 |

## テストケース例

### 正常健康者
```python
healthy_patient = {
    'RIDAGEYR': 35,
    'RIAGENDR': 1,
    'LBDLDL': 95,      # LDL: 最適
    'LBDHDD': 55,      # HDL: 正常
    'LBXGLU': 90,      # 血糖: 正常
    'LBXGH': 5.2,      # HbA1c: 正常
    'eGFR': 105,       # eGFR: 正常
    # ...
}
# 期待結果: スコア 10-20点、リスクレベル「最適」
```

### 高リスク患者
```python
high_risk_patient = {
    'RIDAGEYR': 68,
    'RIAGENDR': 2,
    'LBDLDL': 210,     # LDL: 最高値
    'LBDHDD': 38,      # HDL: 低値
    'LBXGLU': 140,     # 血糖: 糖尿病域
    'LBXGH': 7.2,      # HbA1c: 糖尿病域
    'eGFR': 35,        # eGFR: G3b（中等度〜高度低下）
    # ...
}
# 期待結果: スコア 80-90点、リスクレベル「要精査」
```

## 医学的妥当性

### 検証方法
1. **既知グループ妥当性**: 糖尿病群 vs 非糖尿病群でスコアが有意に異なるか
2. **構成概念妥当性**: 各ドメインスコアが臨床的に意味のある範囲に分布するか
3. **基準関連妥当性**: 既存の臨床リスクスコアとの相関
4. **感度分析**: 閾値変更時のスコア分布の変化

### 制限事項
- **診断ツールではない**: あくまでスクリーニングツール
- **横断研究**: 経時的変化は評価できない
- **因果推論不可**: 相関関係のみ
- **人種・民族**: NHANES（米国）データのため、日本人への適用には注意

## 参考文献

### 臨床ガイドライン
1. **心血管**: ACC/AHA 2019 Guideline on the Primary Prevention of Cardiovascular Disease
2. **代謝**: American Diabetes Association Standards of Care 2023
3. **腎**: KDIGO 2012 Clinical Practice Guideline for CKD
4. **肝**: AASLD 2018 Practice Guidance on NAFLD
5. **血液**: WHO Hemoglobin Thresholds

### データソース
- **NHANES 2017-2018**: National Health and Nutrition Examination Survey
- サンプルサイズ: 9,254名
- URL: https://wwwn.cdc.gov/nchs/nhanes/

## トラブルシューティング

### Q1: "FileNotFoundError: data file not found"
**A**: データファイルを `data/raw/` ディレクトリに配置してください。

### Q2: "ModuleNotFoundError: No module named 'src'"
**A**: プロジェクトルートディレクトリから実行しているか確認してください。

### Q3: 欠損値が多すぎる
**A**: NHANESの一部の検査は受検者が限定的です。欠損率50%以上の変数は慎重に扱ってください。

### Q4: スコアが異常に高い/低い
**A**:
- 入力データの単位を確認（mg/dL, g/dL等）
- 欠損値が適切に処理されているか確認
- データ型が数値型になっているか確認

## ライセンス

本プロジェクトは教育・研究目的で作成されています。
臨床使用前に必ず医学的妥当性の検証を行ってください。

## お問い合わせ

質問や提案がある場合は、Issueを作成してください。

---

**注意**: 本システムはスクリーニングツールであり、最終的な診断・治療方針の決定は必ず医師が行ってください。
