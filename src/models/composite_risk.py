"""
総合健康リスクスコアモデル

各ドメインのリスクスコアを統合し、総合評価を行う
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union
import yaml
from pathlib import Path

from .cardiovascular_risk import CardiovascularRiskModel
from .metabolic_risk import MetabolicRiskModel
from .renal_risk import RenalRiskModel
from .hepatic_risk import HepaticRiskModel
from .hematologic_risk import HematologicRiskModel


class CompositeRiskModel:
    """
    総合健康リスクスコア計算クラス

    5つのドメイン（心血管、代謝、腎、肝、血液）のスコアを統合し、
    総合的な健康リスクを評価
    """

    def __init__(self, thresholds_path: Optional[str] = None):
        """
        Parameters
        ----------
        thresholds_path : str, optional
            臨床閾値設定ファイルのパス
        """
        # 設定ファイルの読み込み
        if thresholds_path is None:
            thresholds_path = Path(__file__).parent.parent.parent / "config" / "clinical_thresholds.yaml"

        with open(thresholds_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        # 各ドメインモデルの初期化
        self.cv_model = CardiovascularRiskModel(self.config)
        self.metabolic_model = MetabolicRiskModel(self.config)
        self.renal_model = RenalRiskModel(self.config)
        self.hepatic_model = HepaticRiskModel(self.config)
        self.hematologic_model = HematologicRiskModel(self.config)

        # 医学的重要度に基づく重み
        self.weights = self.config.get('risk_weights', {
            'cardiovascular': 0.30,
            'metabolic': 0.25,
            'renal': 0.20,
            'hepatic': 0.15,
            'hematologic': 0.10
        })

        # リスクレベル分類
        self.risk_levels = self.config.get('risk_levels', {})

    def calculate_composite_score(self, patient_data: Union[pd.Series, Dict]) -> Dict:
        """
        総合リスクスコアを計算

        Parameters
        ----------
        patient_data : pd.Series or dict
            患者データ

        Returns
        -------
        dict
            総合評価結果
            {
                'composite_score': 65.3,
                'risk_level': 'HIGH',
                'risk_label': '高リスク',
                'domain_scores': {...},
                'alerts': [...],
                'modifiable_factors': [...],
                'recommendations': [...],
                'age_adjusted_percentile': 85
            }
        """
        # 各ドメインスコアを計算
        domain_scores = {
            'cardiovascular': self.cv_model.calculate_score(patient_data),
            'metabolic': self.metabolic_model.calculate_score(patient_data),
            'renal': self.renal_model.calculate_score(patient_data),
            'hepatic': self.hepatic_model.calculate_score(patient_data),
            'hematologic': self.hematologic_model.calculate_score(patient_data)
        }

        # 重み付け統合
        composite = sum(self.weights[k] * v for k, v in domain_scores.items())

        # 年齢補正
        age = patient_data.get('RIDAGEYR', np.nan)
        age_multiplier = 1.0
        if not pd.isna(age):
            if age >= 75:
                age_multiplier = 1.2
            elif age >= 65:
                age_multiplier = 1.1

        composite *= age_multiplier

        # 複数ドメイン高リスクペナルティ
        high_risk_threshold = self.config.get('multi_domain_penalty', {}).get('threshold_score', 70)
        min_domains = self.config.get('multi_domain_penalty', {}).get('min_domains', 2)
        penalty_multiplier = self.config.get('multi_domain_penalty', {}).get('multiplier', 1.15)

        high_risk_count = sum(1 for s in domain_scores.values() if s > high_risk_threshold)
        if high_risk_count >= min_domains:
            composite = min(composite * penalty_multiplier, 100)

        composite = max(0, min(composite, 100))

        # リスクレベルと警告を生成
        risk_level, risk_label = self._classify_risk(composite)
        alerts = self._generate_alerts(domain_scores, patient_data)

        # 修正可能な因子を特定
        modifiable_factors = self._identify_modifiable_factors(domain_scores, patient_data)

        # 統合推奨事項を生成
        recommendations = self._generate_composite_recommendations(
            composite, domain_scores, patient_data, alerts
        )

        # 年齢調整パーセンタイルを計算（仮想）
        age_adjusted_percentile = self._calculate_percentile(composite, age)

        return {
            'composite_score': round(composite, 1),
            'risk_level': risk_level,
            'risk_label': risk_label,
            'domain_scores': {k: round(v, 1) for k, v in domain_scores.items()},
            'alerts': alerts,
            'modifiable_factors': modifiable_factors,
            'recommendations': recommendations,
            'age_adjusted_percentile': age_adjusted_percentile,
            'age_multiplier': age_multiplier,
            'multi_domain_penalty_applied': high_risk_count >= min_domains
        }

    def _classify_risk(self, score: float) -> tuple:
        """
        スコアからリスクレベルを分類

        Parameters
        ----------
        score : float
            総合スコア

        Returns
        -------
        tuple
            (risk_level, risk_label)
        """
        for level_name, level_info in self.risk_levels.items():
            min_score, max_score = level_info['range']
            if min_score <= score < max_score:
                return level_info['severity'], level_info['label']

        # デフォルト（最大レベル）
        return 'CRITICAL', '要精査'

    def _generate_alerts(
        self,
        domain_scores: Dict[str, float],
        patient_data: Union[pd.Series, Dict]
    ) -> List[Dict]:
        """
        警告メッセージを生成

        Parameters
        ----------
        domain_scores : dict
            各ドメインのスコア
        patient_data : pd.Series or dict
            患者データ

        Returns
        -------
        list of dict
            警告リスト
        """
        alerts = []

        # 各ドメインで高リスク（≥60点）の場合、詳細な警告を生成
        if domain_scores['cardiovascular'] >= 60:
            risk_factors = self.cv_model.identify_risk_factors(patient_data)
            cvd_risk = self.cv_model.calculate_10yr_cvd_risk(patient_data)

            alert = {
                'domain': '心血管系',
                'domain_key': 'cardiovascular',
                'severity': 'CRITICAL' if domain_scores['cardiovascular'] >= 80 else 'HIGH',
                'score': domain_scores['cardiovascular'],
                'abnormal_markers': [rf['description'] for rf in risk_factors],
                'recommendations': self.cv_model.generate_recommendations(
                    patient_data, domain_scores['cardiovascular']
                ),
                'estimated_10yr_cvd_risk': f"{cvd_risk:.1f}%" if cvd_risk else 'N/A'
            }
            alerts.append(alert)

        if domain_scores['metabolic'] >= 60:
            risk_factors = self.metabolic_model.identify_risk_factors(patient_data)
            diabetes_status = self.metabolic_model.assess_diabetes_status(patient_data)

            alert = {
                'domain': '代謝系',
                'domain_key': 'metabolic',
                'severity': 'CRITICAL' if domain_scores['metabolic'] >= 80 else 'HIGH',
                'score': domain_scores['metabolic'],
                'abnormal_markers': [rf['description'] for rf in risk_factors],
                'recommendations': self.metabolic_model.generate_recommendations(
                    patient_data, domain_scores['metabolic']
                ),
                'diabetes_status': diabetes_status
            }
            alerts.append(alert)

        if domain_scores['renal'] >= 60:
            risk_factors = self.renal_model.identify_risk_factors(patient_data)
            ckd_stage = self.renal_model.assess_ckd_stage(patient_data)

            alert = {
                'domain': '腎機能',
                'domain_key': 'renal',
                'severity': 'CRITICAL' if domain_scores['renal'] >= 80 else 'HIGH',
                'score': domain_scores['renal'],
                'abnormal_markers': [rf['description'] for rf in risk_factors],
                'recommendations': self.renal_model.generate_recommendations(
                    patient_data, domain_scores['renal']
                ),
                'ckd_stage': ckd_stage.get('ckd_stage', 'unknown'),
                'risk_category': ckd_stage.get('risk_category', 'unknown')
            }
            alerts.append(alert)

        if domain_scores['hepatic'] >= 60:
            risk_factors = self.hepatic_model.identify_risk_factors(patient_data)
            fibrosis_risk = self.hepatic_model.assess_fibrosis_risk(patient_data)

            alert = {
                'domain': '肝機能',
                'domain_key': 'hepatic',
                'severity': 'CRITICAL' if domain_scores['hepatic'] >= 80 else 'HIGH',
                'score': domain_scores['hepatic'],
                'abnormal_markers': [rf['description'] for rf in risk_factors],
                'recommendations': self.hepatic_model.generate_recommendations(
                    patient_data, domain_scores['hepatic']
                ),
                'fibrosis_risk': fibrosis_risk
            }
            alerts.append(alert)

        if domain_scores['hematologic'] >= 60:
            risk_factors = self.hematologic_model.identify_risk_factors(patient_data)
            anemia_type = self.hematologic_model.classify_anemia_type(patient_data)

            alert = {
                'domain': '血液系',
                'domain_key': 'hematologic',
                'severity': 'CRITICAL' if domain_scores['hematologic'] >= 80 else 'HIGH',
                'score': domain_scores['hematologic'],
                'abnormal_markers': [rf['description'] for rf in risk_factors],
                'recommendations': self.hematologic_model.generate_recommendations(
                    patient_data, domain_scores['hematologic']
                ),
                'anemia_type': anemia_type if anemia_type else 'none'
            }
            alerts.append(alert)

        return alerts

    def _identify_modifiable_factors(
        self,
        domain_scores: Dict[str, float],
        patient_data: Union[pd.Series, Dict]
    ) -> List[str]:
        """
        修正可能なリスク因子を特定

        Parameters
        ----------
        domain_scores : dict
            各ドメインのスコア
        patient_data : pd.Series or dict
            患者データ

        Returns
        -------
        list of str
            修正可能な因子のリスト
        """
        modifiable = []

        # LDLコレステロール
        ldl = patient_data.get('LBDLDL', np.nan)
        if not pd.isna(ldl) and ldl >= 130:
            modifiable.append('LDLコレステロール（食事療法・スタチン）')

        # 血糖
        glucose = patient_data.get('LBXGLU', np.nan)
        if not pd.isna(glucose) and glucose >= 100:
            modifiable.append('血糖値（食事・運動・薬物療法）')

        # HbA1c
        hba1c = patient_data.get('LBXGH', np.nan)
        if not pd.isna(hba1c) and hba1c >= 5.7:
            modifiable.append('HbA1c（糖尿病管理）')

        # 中性脂肪
        tg = patient_data.get('LBXTR', np.nan)
        if not pd.isna(tg) and tg >= 150:
            modifiable.append('中性脂肪（食事・運動・フィブラート）')

        # HDL（低値）
        hdl = patient_data.get('LBDHDD', np.nan)
        gender = patient_data.get('RIAGENDR', np.nan)
        if not pd.isna(hdl):
            threshold = 50 if gender == 2 else 40
            if hdl < threshold:
                modifiable.append('HDLコレステロール（運動・禁煙）')

        # ALT高値（NAFLD疑い）
        alt = patient_data.get('LBXSGTSI', np.nan)
        if not pd.isna(alt) and alt > 40:
            modifiable.append('肝機能異常（減量・節酒）')

        return modifiable

    def _generate_composite_recommendations(
        self,
        composite_score: float,
        domain_scores: Dict[str, float],
        patient_data: Union[pd.Series, Dict],
        alerts: List[Dict]
    ) -> List[str]:
        """
        総合的な推奨事項を生成

        Parameters
        ----------
        composite_score : float
            総合スコア
        domain_scores : dict
            各ドメインのスコア
        patient_data : pd.Series or dict
            患者データ
        alerts : list
            警告リスト

        Returns
        -------
        list of str
            推奨事項のリスト
        """
        recommendations = []

        # 総合スコアに基づく推奨
        if composite_score >= 80:
            recommendations.extend([
                '【総合評価: 要精査】',
                '複数の専門医への紹介を推奨',
                '包括的な精密検査の実施',
                '多職種連携による介入プログラムの開始'
            ])
        elif composite_score >= 60:
            recommendations.extend([
                '【総合評価: 高リスク】',
                '専門医への紹介を検討',
                '生活習慣の徹底的な改善',
                '3ヶ月ごとの定期フォローアップ'
            ])
        elif composite_score >= 40:
            recommendations.extend([
                '【総合評価: 中リスク】',
                '生活習慣改善指導',
                '6ヶ月ごとの再評価'
            ])
        elif composite_score >= 20:
            recommendations.extend([
                '【総合評価: 低リスク】',
                '現在の健康状態を維持',
                '年1回の定期健診'
            ])
        else:
            recommendations.extend([
                '【総合評価: 最適】',
                '優良な健康状態',
                '年1回の定期健診'
            ])

        # 複数ドメインで高リスクの場合
        high_risk_domains = [k for k, v in domain_scores.items() if v >= 60]
        if len(high_risk_domains) >= 2:
            recommendations.append(
                f'注意: {len(high_risk_domains)}つのドメインで高リスク検出 '
                f'（{", ".join(high_risk_domains)}）- 統合的な管理が必要'
            )

        return recommendations

    def _calculate_percentile(self, score: float, age: float) -> int:
        """
        年齢調整パーセンタイルを計算（仮想）

        Parameters
        ----------
        score : float
            総合スコア
        age : float
            年齢

        Returns
        -------
        int
            パーセンタイル（0-100）
        """
        # 簡易的な計算（実際には集団データから算出）
        if pd.isna(age):
            age = 50  # デフォルト年齢

        # 年齢による基準値の調整
        base_score = score
        if age >= 65:
            base_score *= 0.9  # 高齢者は基準を緩和
        elif age < 45:
            base_score *= 1.1  # 若年者は基準を厳格化

        # スコアをパーセンタイルに変換（仮想）
        percentile = int(base_score)
        return max(0, min(percentile, 100))

    def batch_calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        複数患者のスコアを一括計算

        Parameters
        ----------
        df : pd.DataFrame
            患者データフレーム

        Returns
        -------
        pd.DataFrame
            スコア追加済みデータフレーム
        """
        from tqdm import tqdm

        results = []
        for idx, row in tqdm(df.iterrows(), total=len(df), desc="Calculating risk scores"):
            result = self.calculate_composite_score(row)
            result['SEQN'] = row.get('SEQN', idx)
            results.append(result)

        # 結果をDataFrameに変換
        results_df = pd.DataFrame(results)

        # 元データと結合
        df_with_scores = df.merge(results_df, on='SEQN', how='left')

        return df_with_scores
