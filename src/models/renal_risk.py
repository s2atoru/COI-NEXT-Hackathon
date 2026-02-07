"""
腎機能リスク評価モデル

eGFRとアルブミン尿に基づく腎疾患リスクを評価
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union
import yaml
from pathlib import Path


class RenalRiskModel:
    """
    腎機能リスクスコア計算クラス

    評価項目:
    - eGFR（推定糸球体濾過量）
    - 尿中アルブミン/クレアチニン比（ACR）
    - 血清クレアチニン
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
                self.thresholds = config['renal']
        else:
            self.thresholds = thresholds.get('renal', {})

    def calculate_score(self, patient: Union[pd.Series, Dict]) -> float:
        """
        腎機能リスクスコアを計算（0-100点）

        Parameters
        ----------
        patient : pd.Series or dict
            患者データ

        Returns
        -------
        float
            腎機能リスクスコア
        """
        score = 0.0

        # eGFRスコア（重み: 60点満点）
        egfr = patient.get('eGFR', np.nan)
        if not pd.isna(egfr):
            if egfr < 15:  # G5: 腎不全
                score += 60
            elif egfr < 30:  # G4: 高度低下
                score += 50
            elif egfr < 45:  # G3b: 中等度〜高度低下
                score += 40
            elif egfr < 60:  # G3a: 軽度〜中等度低下
                score += 25
            elif egfr < 90:  # G2: 軽度低下
                score += 10
            else:  # G1: 正常
                score += 0

        # ACR（アルブミン/クレアチニン比）スコア（重み: 40点満点）
        acr = patient.get('ACR', np.nan)
        if not pd.isna(acr):
            if acr >= 300:  # A3: 顕性アルブミン尿
                score += 40
            elif acr >= 30:  # A2: 微量アルブミン尿
                score += 20
            else:  # A1: 正常
                score += 0

        # 年齢補正
        age = patient.get('RIDAGEYR', np.nan)
        if not pd.isna(age):
            if age >= 75:
                score *= 1.15
            elif age >= 65:
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

        # eGFRチェック
        egfr = patient.get('eGFR', np.nan)
        if not pd.isna(egfr):
            if egfr < 15:
                risk_factors.append({
                    'marker': 'eGFR',
                    'value': egfr,
                    'unit': 'mL/min/1.73m²',
                    'severity': 'critical',
                    'category': 'kidney_failure',
                    'description': f'eGFR: {egfr:.1f}（G5: 腎不全）'
                })
            elif egfr < 30:
                risk_factors.append({
                    'marker': 'eGFR',
                    'value': egfr,
                    'unit': 'mL/min/1.73m²',
                    'severity': 'very_high',
                    'category': 'severe_ckd',
                    'description': f'eGFR: {egfr:.1f}（G4: 高度低下）'
                })
            elif egfr < 45:
                risk_factors.append({
                    'marker': 'eGFR',
                    'value': egfr,
                    'unit': 'mL/min/1.73m²',
                    'severity': 'high',
                    'category': 'moderate_ckd',
                    'description': f'eGFR: {egfr:.1f}（G3b: 中等度〜高度低下）'
                })
            elif egfr < 60:
                risk_factors.append({
                    'marker': 'eGFR',
                    'value': egfr,
                    'unit': 'mL/min/1.73m²',
                    'severity': 'moderate',
                    'category': 'mild_ckd',
                    'description': f'eGFR: {egfr:.1f}（G3a: 軽度〜中等度低下）'
                })

        # ACRチェック
        acr = patient.get('ACR', np.nan)
        if not pd.isna(acr):
            if acr >= 300:
                risk_factors.append({
                    'marker': 'ACR',
                    'value': acr,
                    'unit': 'mg/g',
                    'severity': 'very_high',
                    'category': 'macroalbuminuria',
                    'description': f'ACR: {acr:.1f} mg/g（A3: 顕性アルブミン尿）'
                })
            elif acr >= 30:
                risk_factors.append({
                    'marker': 'ACR',
                    'value': acr,
                    'unit': 'mg/g',
                    'severity': 'high',
                    'category': 'microalbuminuria',
                    'description': f'ACR: {acr:.1f} mg/g（A2: 微量アルブミン尿）'
                })

        # クレアチニン高値チェック
        creatinine = patient.get('LBXSCR', np.nan)
        gender = patient.get('RIAGENDR', np.nan)
        if not pd.isna(creatinine):
            if gender == 2:  # Female
                threshold = 1.1
            else:  # Male
                threshold = 1.3

            if creatinine > threshold:
                risk_factors.append({
                    'marker': 'Creatinine',
                    'value': creatinine,
                    'unit': 'mg/dL',
                    'severity': 'high',
                    'category': 'elevated_creatinine',
                    'description': f'クレアチニン: {creatinine:.2f} mg/dL（基準値超過）'
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

        egfr = patient.get('eGFR', np.nan)

        if score >= 80:
            recommendations.extend([
                '【緊急】腎臓専門医への即時紹介',
                '透析・腎移植の検討',
                'CKD合併症の精密評価（貧血、骨ミネラル代謝異常等）',
                '腎保護療法の強化',
                '薬剤投与量の調整（腎機能に応じた減量）'
            ])
        elif score >= 60:
            recommendations.extend([
                '腎臓専門医への紹介',
                'CKDステージに応じた管理',
                'ACE阻害薬/ARBによる腎保護',
                '血圧管理（目標<130/80 mmHg）',
                '蛋白制限食（0.6-0.8 g/kg/日）',
                '3ヶ月ごとのモニタリング'
            ])
        elif score >= 40:
            recommendations.extend([
                'CKD進行予防のための生活習慣改善',
                '血圧・血糖の厳格管理',
                '減塩（6g/日未満）',
                'NSAIDs等腎毒性薬剤の回避',
                '6ヶ月ごとの腎機能チェック'
            ])
        elif score >= 20:
            recommendations.extend([
                '腎機能の定期モニタリング',
                '高血圧・糖尿病の管理',
                '適正な水分摂取',
                '年1回の検査'
            ])
        else:
            recommendations.extend([
                '現在の腎機能を維持',
                '定期健診での継続観察'
            ])

        # eGFR<60でACR≥30の場合（CKD確定）
        acr = patient.get('ACR', np.nan)
        if not pd.isna(egfr) and egfr < 60 and not pd.isna(acr) and acr >= 30:
            recommendations.append('CKD診断確定: 腎臓病手帳の発行、患者教育の実施')

        return recommendations

    def assess_ckd_stage(self, patient: Union[pd.Series, Dict]) -> Dict[str, str]:
        """
        CKDステージを評価（KDIGO分類）

        Parameters
        ----------
        patient : pd.Series or dict
            患者データ

        Returns
        -------
        dict
            CKDステージ情報
        """
        egfr = patient.get('eGFR', np.nan)
        acr = patient.get('ACR', np.nan)

        result = {
            'gfr_stage': 'unknown',
            'albuminuria_stage': 'unknown',
            'ckd_stage': 'unknown',
            'risk_category': 'unknown'
        }

        # GFRステージ
        if not pd.isna(egfr):
            if egfr >= 90:
                result['gfr_stage'] = 'G1'
            elif egfr >= 60:
                result['gfr_stage'] = 'G2'
            elif egfr >= 45:
                result['gfr_stage'] = 'G3a'
            elif egfr >= 30:
                result['gfr_stage'] = 'G3b'
            elif egfr >= 15:
                result['gfr_stage'] = 'G4'
            else:
                result['gfr_stage'] = 'G5'

        # アルブミン尿ステージ
        if not pd.isna(acr):
            if acr < 30:
                result['albuminuria_stage'] = 'A1'
            elif acr < 300:
                result['albuminuria_stage'] = 'A2'
            else:
                result['albuminuria_stage'] = 'A3'

        # CKDステージ統合
        if result['gfr_stage'] != 'unknown' and result['albuminuria_stage'] != 'unknown':
            result['ckd_stage'] = f"{result['gfr_stage']}{result['albuminuria_stage']}"

            # リスクカテゴリ（KDIGO heat map）
            risk_matrix = {
                'G1A1': 'low', 'G1A2': 'moderate', 'G1A3': 'high',
                'G2A1': 'low', 'G2A2': 'moderate', 'G2A3': 'high',
                'G3aA1': 'moderate', 'G3aA2': 'high', 'G3aA3': 'very_high',
                'G3bA1': 'high', 'G3bA2': 'very_high', 'G3bA3': 'very_high',
                'G4A1': 'very_high', 'G4A2': 'very_high', 'G4A3': 'very_high',
                'G5A1': 'very_high', 'G5A2': 'very_high', 'G5A3': 'very_high'
            }
            result['risk_category'] = risk_matrix.get(result['ckd_stage'], 'unknown')

        return result
