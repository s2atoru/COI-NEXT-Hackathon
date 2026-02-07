"""
代謝リスク評価モデル

血糖・インスリン抵抗性に基づく代謝疾患リスクを評価
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union
import yaml
from pathlib import Path


class MetabolicRiskModel:
    """
    代謝リスクスコア計算クラス

    評価項目:
    - 空腹時血糖
    - HbA1c
    - インスリン
    - HOMA-IR（インスリン抵抗性指標）
    """

    def __init__(self, thresholds: Optional[Dict] = None):
        """
        Parameters
        ----------
        thresholds : dict, optional
            臨床閾値設定
        """
        if thresholds is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "clinical_thresholds.yaml"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.thresholds = config['metabolic']
        else:
            self.thresholds = thresholds.get('metabolic', {})

    def calculate_score(self, patient: Union[pd.Series, Dict]) -> float:
        """
        代謝リスクスコアを計算（0-100点）

        Parameters
        ----------
        patient : pd.Series or dict
            患者データ

        Returns
        -------
        float
            代謝リスクスコア
        """
        score = 0.0

        # 空腹時血糖スコア（重み: 40点満点）
        glucose = patient.get('LBXGLU', np.nan)
        if not pd.isna(glucose):
            if glucose >= 126:  # 糖尿病域
                score += 40
            elif glucose >= 100:  # 前糖尿病域
                score += 20
            else:  # 正常
                score += 0

        # HbA1cスコア（重み: 40点満点）
        hba1c = patient.get('LBXGH', np.nan)
        if not pd.isna(hba1c):
            if hba1c >= 6.5:  # 糖尿病域
                score += 40
            elif hba1c >= 5.7:  # 前糖尿病域
                score += 20
            else:  # 正常
                score += 0

        # HOMA-IRスコア（重み: 20点満点）
        homa_ir = patient.get('HOMA_IR', np.nan)
        if not pd.isna(homa_ir):
            if homa_ir >= 5.0:
                score += 20
            elif homa_ir >= 2.5:
                score += 10
            else:
                score += 0

        # 年齢補正
        age = patient.get('RIDAGEYR', np.nan)
        if not pd.isna(age):
            if age >= 65:
                score *= 1.2
            elif age >= 45:
                score *= 1.1

        # 0-100点に正規化
        score = max(0, min(score, 100))

        return round(score, 1)

    def identify_risk_factors(self, patient: Union[pd.Series, Dict]) -> List[Dict]:
        """
        リスク因子を特定

        Parameters
        ----------
        patient : pd.Series or dict
            患者データ

        Returns
        -------
        list of dict
            リスク因子のリスト
        """
        risk_factors = []

        # 血糖チェック
        glucose = patient.get('LBXGLU', np.nan)
        if not pd.isna(glucose):
            if glucose >= 126:
                risk_factors.append({
                    'marker': 'Fasting glucose',
                    'value': glucose,
                    'unit': 'mg/dL',
                    'severity': 'very_high',
                    'category': 'diabetes',
                    'description': f'空腹時血糖: {glucose:.1f} mg/dL（糖尿病域: ≥126）'
                })
            elif glucose >= 100:
                risk_factors.append({
                    'marker': 'Fasting glucose',
                    'value': glucose,
                    'unit': 'mg/dL',
                    'severity': 'high',
                    'category': 'prediabetes',
                    'description': f'空腹時血糖: {glucose:.1f} mg/dL（前糖尿病域: 100-125）'
                })

        # HbA1cチェック
        hba1c = patient.get('LBXGH', np.nan)
        if not pd.isna(hba1c):
            if hba1c >= 6.5:
                risk_factors.append({
                    'marker': 'HbA1c',
                    'value': hba1c,
                    'unit': '%',
                    'severity': 'very_high',
                    'category': 'diabetes',
                    'description': f'HbA1c: {hba1c:.1f}%（糖尿病域: ≥6.5%）'
                })
            elif hba1c >= 5.7:
                risk_factors.append({
                    'marker': 'HbA1c',
                    'value': hba1c,
                    'unit': '%',
                    'severity': 'high',
                    'category': 'prediabetes',
                    'description': f'HbA1c: {hba1c:.1f}%（前糖尿病域: 5.7-6.4%）'
                })

        # HOMA-IRチェック
        homa_ir = patient.get('HOMA_IR', np.nan)
        if not pd.isna(homa_ir) and homa_ir >= 2.5:
            risk_factors.append({
                'marker': 'HOMA-IR',
                'value': homa_ir,
                'unit': 'index',
                'severity': 'high',
                'category': 'insulin_resistance',
                'description': f'HOMA-IR: {homa_ir:.2f}（インスリン抵抗性: ≥2.5）'
            })

        return risk_factors

    def generate_recommendations(self, patient: Union[pd.Series, Dict], score: float) -> List[str]:
        """
        スコアに基づく推奨事項を生成

        Parameters
        ----------
        patient : pd.Series or dict
            患者データ
        score : float
            リスクスコア

        Returns
        -------
        list of str
            推奨事項のリスト
        """
        recommendations = []

        # 糖尿病診断基準を満たすかチェック
        glucose = patient.get('LBXGLU', np.nan)
        hba1c = patient.get('LBXGH', np.nan)

        is_diabetic = False
        if (not pd.isna(glucose) and glucose >= 126) or (not pd.isna(hba1c) and hba1c >= 6.5):
            is_diabetic = True

        if score >= 80 or is_diabetic:
            recommendations.extend([
                '【緊急】糖尿病診断のための精密検査',
                '内分泌内科/糖尿病専門医への紹介',
                '75g経口ブドウ糖負荷試験（OGTT）の実施',
                '糖尿病合併症スクリーニング（眼科、腎機能、神経）',
                '糖尿病教育プログラムへの参加',
                '食事療法・運動療法の開始'
            ])
        elif score >= 60:
            recommendations.extend([
                '前糖尿病の管理',
                '生活習慣改善指導（低GI食、有酸素運動）',
                '体重管理（5-10%減量を目標）',
                '3-6ヶ月ごとの血糖モニタリング'
            ])
        elif score >= 40:
            recommendations.extend([
                '生活習慣の見直し',
                '適正体重の維持',
                '定期的な運動（週150分以上）',
                '年1回の血糖検査'
            ])
        else:
            recommendations.extend([
                '現在の健康状態を維持',
                'バランスの取れた食事',
                '年1回の定期健診'
            ])

        # インスリン抵抗性がある場合
        homa_ir = patient.get('HOMA_IR', np.nan)
        if not pd.isna(homa_ir) and homa_ir >= 2.5:
            recommendations.append('インスリン抵抗性改善: メトホルミンの検討、減量プログラム')

        return recommendations

    def assess_diabetes_status(self, patient: Union[pd.Series, Dict]) -> str:
        """
        糖尿病ステータスを評価

        Parameters
        ----------
        patient : pd.Series or dict
            患者データ

        Returns
        -------
        str
            ステータス（normal/prediabetes/diabetes/insufficient_data）
        """
        glucose = patient.get('LBXGLU', np.nan)
        hba1c = patient.get('LBXGH', np.nan)

        # 糖尿病基準
        if (not pd.isna(glucose) and glucose >= 126) or (not pd.isna(hba1c) and hba1c >= 6.5):
            return 'diabetes'

        # 前糖尿病基準
        if (not pd.isna(glucose) and 100 <= glucose < 126) or \
           (not pd.isna(hba1c) and 5.7 <= hba1c < 6.5):
            return 'prediabetes'

        # 正常
        if (not pd.isna(glucose) and glucose < 100) or (not pd.isna(hba1c) and hba1c < 5.7):
            return 'normal'

        return 'insufficient_data'
