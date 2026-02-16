# 医療機関向け総合健康リスクスコアシステム

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-18%2F18%20passing-brightgreen.svg)](tests/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![AI Generated](https://img.shields.io/badge/AI%20Generated-Claude%20Opus%204.6-blueviolet.svg)](https://claude.ai)

> 🤖 **AI Generated Code**: このプロジェクトのコード、ドキュメント、テストは[Claude](https://claude.ai)（Anthropic社のAI）によって生成されました。
>
> AIが生成したコードには予期しない動作やエラーが含まれる可能性があります。実用前に必ず専門家によるレビューと検証を行ってください。

NHANES 2017-2018データを活用した健康リスク評価システムの**教育・デモンストレーション用サンプル実装**です。

**⚠️ 本システムは実際の医療現場での使用を想定していません。実用目的での使用は禁止されています。**

---

## ⚠️ 重要な警告 / IMPORTANT WARNING

**🚨 このシステムは教育・デモンストレーション目的のサンプル実装です 🚨**

**本システムは以下の用途には決して使用しないでください:**

- ❌ **実際の医療診断**
- ❌ **治療方針の決定**
- ❌ **患者の健康管理**
- ❌ **臨床現場での使用**
- ❌ **商用医療サービス**

### なぜ実用してはいけないのか

1. **医療機器としての承認を受けていません**
   - 本システムは規制当局（FDA、PMDA等）の承認を受けていません
   - 医療機器としての安全性・有効性の検証が行われていません

2. **限定的な検証しか行われていません**
   - 限られたテストケースでのみ動作確認
   - 大規模臨床試験による検証なし
   - 外部妥当性の確認なし

3. **責任の所在が不明確です**
   - 本ソフトウェアはMITライセンスで「無保証」として提供
   - 使用による損害について開発者は一切の責任を負いません

4. **医学的限界があります**
   - 米国集団（NHANES）データに基づいており、他の人種・民族への適用は未検証
   - 横断研究データのため、経時的変化を評価できません
   - あくまで相関関係であり、因果関係は証明されていません

### 適切な使用方法

✅ **許容される用途:**
- プログラミング学習
- データサイエンス教育
- 医療情報学の研究
- アルゴリズム開発の参考
- 概念実証（PoC）の出発点
- オープンソースコントリビューションの練習

### 実用化する場合の必須要件

もし本システムをベースに実用システムを開発する場合、以下が**最低限**必要です：

1. ✅ 大規模臨床試験による妥当性検証
2. ✅ 規制当局への承認申請と取得
3. ✅ 医療専門家による監修
4. ✅ 倫理委員会の承認
5. ✅ 個人情報保護対策の実装
6. ✅ 医療過誤保険の加入
7. ✅ 継続的なモニタリング体制の構築

---

**免責事項**: 本ソフトウェアを使用したことによる一切の損害について、開発者は責任を負いません。医療に関する判断は、必ず有資格の医療従事者に相談してください。

---

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
│   ├── 02_feature_engineering.ipynb
│   ├── 03_risk_model_development.ipynb
│   └── 04_validation_analysis.ipynb
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

### 3. Notebookの実行（推奨順序）

#### 3.1 データ探索と前処理
`notebooks/01_data_exploration.ipynb` を開いて実行:
- データの読み込み
- 基本統計量の確認
- 欠損値分析
- データの前処理
- 前処理済みデータの保存（`nhanes_processed.csv`）

#### 3.2 特徴量エンジニアリング
`notebooks/02_feature_engineering.ipynb` を開いて実行:
- 派生変数の分布分析（TC_HDL比、eGFR、HOMA-IR、FIB4等）
- 臨床カテゴリの生成（糖尿病、CKD、肝線維化、貧血ステータス）
- ドメイン内・ドメイン間相関分析
- 性別・年齢グループ別分析
- データ完全性評価
- 強化データセットの保存（`nhanes_enhanced.csv`）

#### 3.3 リスクモデル開発
`notebooks/03_risk_model_development.ipynb` を開いて実行:
- 各ドメインモデルのテスト
- 総合リスクスコアの計算
- スコア分布の可視化
- 高リスク患者の抽出
- 既知グループ妥当性の基本評価

#### 3.4 妥当性検証と感度分析
`notebooks/04_validation_analysis.ipynb` を開いて実行:
- 統計的妥当性検証（ANOVA、Kruskal-Wallis）
- ROC曲線分析（循環性警告付き）
- 感度分析（ウェイト摂動、年齢調整、ペナルティ）
- スコアキャリブレーション評価
- 欠損データ影響分析
- 内部整合性評価（Cronbach's α）
- Plotlyインタラクティブ可視化

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

**🚨 重要: 本システムは実用禁止です 🚨**

本システムには以下の重大な制限があり、実際の医療現場では使用できません：

#### 医学的制限
- ❌ **診断ツールではない**: 医療診断には使用できません
- ❌ **治療判断不可**: 治療方針の決定には使用できません
- ❌ **横断研究のみ**: 経時的変化は評価できません
- ❌ **因果関係未証明**: 相関関係のみで因果関係は不明
- ❌ **人種バイアス**: NHANES（米国）データベースで日本人への適用は未検証

#### 技術的制限
- ❌ **医療機器未承認**: FDA、PMDA等の承認なし
- ❌ **限定的検証**: 大規模臨床試験未実施
- ❌ **セキュリティ未対応**: 医療情報保護基準（HIPAA、個人情報保護法等）非準拠
- ❌ **保守体制なし**: 商用サポート・保守契約なし

#### 法的制限
- ❌ **責任免除**: MITライセンスにより無保証
- ❌ **医療過誤保険なし**: 使用による損害の補償なし
- ❌ **規制非準拠**: 医療機器規制に非対応

**本システムは教育・研究目的のサンプル実装です。実際の医療判断は必ず医師に相談してください。**

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

本プロジェクトはMITライセンスの下で公開されています。

**⚠️ 重要な免責事項:**
- 本ソフトウェアは「現状のまま」提供され、いかなる保証もありません
- 本ソフトウェアは教育・研究・デモンストレーション目的のみです
- **実際の医療現場・診断・治療判断には絶対に使用しないでください**
- 使用による損害について、開発者は一切の責任を負いません
- 医療に関する判断は、必ず医師・医療従事者に相談してください

詳細は [LICENSE](LICENSE) ファイルをご覧ください。

## お問い合わせ

質問や提案がある場合は、Issueを作成してください。

## 開発について

### AI生成コードについて

🤖 **このプロジェクトは完全にAIによって生成されました**

- **AIモデル**: Claude Opus 4.6（Anthropic社）
- **生成日**: 2026年2月7日
- **コード行数**: 約5,700行（全てAI生成）
- **テストケース**: 18個（全てAI生成）
- **ドキュメント**: 4つの詳細ガイド（全てAI生成）

### AI生成コードの特性と注意点

**利点:**
- ✅ 短時間での開発（数時間で完成）
- ✅ 包括的なドキュメント
- ✅ 一貫したコーディングスタイル
- ✅ 多数のテストケース

**注意点:**
- ⚠️ 人間の専門家によるレビューが必要
- ⚠️ 予期しないエッジケースが存在する可能性
- ⚠️ 医学的妥当性は人間の医療専門家が検証すべき
- ⚠️ セキュリティ監査が未実施
- ⚠️ 本番環境使用前に必ず検証が必要

### コントリビューション

このAI生成コードをベースに、人間の開発者・医療専門家による改善を歓迎します：

- 🔍 コードレビューとバグ修正
- 🏥 医学的妥当性の検証
- 🔒 セキュリティの強化
- 📚 追加のドキュメント
- 🧪 追加のテストケース
- 🌍 多言語対応

プルリクエストを送る前に、必ず医学的・倫理的観点から適切かどうかご確認ください。

---

**注意**: 本システムはスクリーニングツールであり、最終的な診断・治療方針の決定は必ず医師が行ってください。

**AI Generated**: このドキュメントを含む全てのコンテンツは、Claude（Anthropic社のAI）によって生成されました。内容の正確性について、人間の専門家による検証を推奨します。
