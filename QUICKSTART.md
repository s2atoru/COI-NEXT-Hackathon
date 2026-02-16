# クイックスタートガイド

このガイドに従って、5分でシステムを起動できます。

## ステップ1: 環境セットアップ（2分）

### 1.1 仮想環境の作成（推奨）
```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
# または
venv\Scripts\activate     # Windows
```

### 1.2 依存ライブラリのインストール
```bash
pip install -r requirements.txt
```

## ステップ2: データの確認（1分）

プロジェクトには既にNHANESデータが含まれています:
- `nhanes_2017_2018_demo_lab_numeric_and_gender.csv`
- `nhanes_2017_2018_demo_lab_all.csv`

データを `data/raw/` に移動（任意）:
```bash
mkdir -p data/raw
mv nhanes_2017_2018_*.csv data/raw/
```

## ステップ3: 動作確認（2分）

### 3.1 使用例スクリプトの実行
```bash
python example_usage.py
```

期待される出力:
```
総合健康リスクスコアシステム - 使用例

============================================================
例1: 正常健康者（35歳男性）
============================================================

総合スコア: 15.2点
リスクレベル: OPTIMAL (最適)
...
```

### 3.2 テストの実行（オプション）
```bash
pytest tests/test_risk_models.py -v
```

全18テストがパスすることを確認。

## ステップ4: Jupyter Notebookで探索（オプション）

```bash
cd notebooks
jupyter notebook
```

ブラウザで以下を順番に開く:
1. `01_data_exploration.ipynb` - データ探索・前処理
2. `02_feature_engineering.ipynb` - 特徴量エンジニアリング・臨床分類 ✨
3. `03_risk_model_development.ipynb` - モデル開発・テスト
4. `04_validation_analysis.ipynb` - 妥当性検証・感度分析 ✨

## よく使う機能

### 単一患者のスコア計算

```python
from src.models.composite_risk import CompositeRiskModel

# モデル初期化
model = CompositeRiskModel()

# 患者データ
patient = {
    'SEQN': 12345,
    'RIAGENDR': 1,      # 1=Male, 2=Female
    'RIDAGEYR': 55,
    'LBDLDL': 150,      # LDL cholesterol
    'LBDHDD': 45,       # HDL cholesterol
    'LBXGLU': 105,      # Glucose
    'LBXSCR': 1.1,      # Creatinine
    'LBXHGB': 14.5,     # Hemoglobin
}

# スコア計算
result = model.calculate_composite_score(patient)

# 結果表示
print(f"総合スコア: {result['composite_score']:.1f}点")
print(f"リスクレベル: {result['risk_level']} ({result['risk_label']})")
print(f"\nドメイン別スコア:")
for domain, score in result['domain_scores'].items():
    print(f"  {domain}: {score:.1f}点")
```

### 複数患者の一括処理

```python
import pandas as pd
from src.data.loader import NHANESLoader
from src.data.preprocessor import NHANESPreprocessor
from src.models.composite_risk import CompositeRiskModel

# データ読み込み
loader = NHANESLoader('data/raw')
df = loader.load_csv('nhanes_2017_2018_demo_lab_all.csv')

# 前処理
preprocessor = NHANESPreprocessor()
df_processed = preprocessor.preprocess(df)

# 一括スコア計算（サンプル100名）
model = CompositeRiskModel()
df_sample = df_processed.head(100)
df_with_scores = model.batch_calculate(df_sample)

# 高リスク患者の抽出
high_risk = df_with_scores[df_with_scores['composite_score'] >= 80]
print(f"高リスク患者: {len(high_risk)}名")
```

## トラブルシューティング

### Q: ModuleNotFoundError が出る
**A**: プロジェクトルートディレクトリから実行していますか？
```bash
pwd  # 現在のディレクトリを確認
# COI-NEXT-Hackathon ディレクトリにいることを確認
```

### Q: データファイルが見つからない
**A**: データファイルの場所を確認:
```bash
ls -la *.csv
# または
ls -la data/raw/*.csv
```

### Q: ライブラリのインストールエラー
**A**: Python 3.8以上を使用していますか？
```bash
python --version
# Python 3.8.0以上であることを確認
```

## 次のステップ

1. **データ探索**: `notebooks/01_data_exploration.ipynb` を実行
2. **特徴量生成**: `notebooks/02_feature_engineering.ipynb` を実行 ✨
3. **モデル開発**: `notebooks/03_risk_model_development.ipynb` を実行
4. **妥当性検証**: `notebooks/04_validation_analysis.ipynb` を実行 ✨
5. **カスタマイズ**: `config/clinical_thresholds.yaml` で閾値を調整
6. **詳細ドキュメント**: `README.md` と `IMPLEMENTATION_SUMMARY.md` を参照

## サポート

問題が発生した場合:
1. `README.md` のトラブルシューティングセクションを確認
2. GitHubでIssueを作成
3. エラーメッセージをコピーして報告

---

**注意**: 本システムは研究・教育目的です。臨床使用前に必ず医学的妥当性を検証してください。
