"""
心血管リスク評価モデル

脂質プロファイルに基づく心血管疾患リスクを評価
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union
import yaml
from pathlib import Path


class CardiovascularRiskModel:
    """
    心血管リスクスコア計算クラス

    評価項目:
    - LDLコレステロール（最重要）
    - HDLコレステロール（保護因子）
    - 総コレステロール
    - 中性脂肪
    - TC/HDL比
    """

    def __init__(self, thresholds: Optional[Dict] = None):
        """
        Parameters
        ----------
        thresholds : dict, optional
            臨床閾値設定（Noneの場合はデフォルトファイルを読み込み）
        """
        if thresholds is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "clinical_thresholds.yaml"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.thresholds = config['cardiovascular']
        else:
            self.thresholds = thresholds.get('cardiovascular', {})

    def calculate_score(self, patient: Union[pd.Series, Dict]) -> float:
        """
        心血管リスクスコアを計算（0-100点）

        Parameters
        ----------
        patient : pd.Series or dict
            患者データ

        Returns
        -------
        float
            心血管リスクスコア
        """
        score = 0.0
        age = patient.get('RIDAGEYR', np.nan)
        gender = patient.get('RIAGENDR', np.nan)

        # LDLスコア（重み: 40点満点）
        ldl = patient.get('LBDLDL', np.nan)
        if not pd.isna(ldl):
            if ldl >= 190:
                score += 40
            elif ldl >= 160:
                score += 32
            elif ldl >= 130:
                score += 24
            elif ldl >= 100:
                score += 12
            else:  # <100
                score += 0

        # HDLスコア（逆相関、重み: 25点満点）
        hdl = patient.get('LBDHDD', np.nan)
        if not pd.isna(hdl):
            # 性別による閾値
            if gender == 2:  # Female
                threshold = 50
            else:  # Male
                threshold = 40

            if hdl < threshold:
                score += 25
            elif hdl < 60:
                score += 10
            else:  # ≥60 (保護因子)
                score -= 5  # ボーナスポイント

        # 中性脂肪スコア（重み: 20点満点）
        tg = patient.get('LBXTR', np.nan)
        if not pd.isna(tg):
            if tg >= 500:
                score += 20
            elif tg >= 200:
                score += 16
            elif tg >= 150:
                score += 8
            else:  # <150
                score += 0

        # TC/HDL比スコア（重み: 15点満点）
        tc_hdl_ratio = patient.get('TC_HDL_ratio', np.nan)
        if not pd.isna(tc_hdl_ratio):
            if tc_hdl_ratio > 5:
                score += 15
            elif tc_hdl_ratio > 4:
                score += 10
            elif tc_hdl_ratio > 3.5:
                score += 5

        # 年齢補正
        if not pd.isna(age):
            if age >= 65:
                score *= 1.3
            elif age >= 55:
                score *= 1.15
            elif age >= 45:
                score *= 1.0
            else:  # <45
                score *= 0.8

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
        gender = patient.get('RIAGENDR', np.nan)

        # LDLチェック
        ldl = patient.get('LBDLDL', np.nan)
        if not pd.isna(ldl):
            if ldl >= 190:
                risk_factors.append({
                    'marker': 'LDL cholesterol',
                    'value': ldl,
                    'unit': 'mg/dL',
                    'severity': 'very_high',
                    'category': 'dyslipidemia',
                    'description': f'LDL: {ldl:.1f} mg/dL（最高値: ≥190）'
                })
            elif ldl >= 160:
                risk_factors.append({
                    'marker': 'LDL cholesterol',
                    'value': ldl,
                    'unit': 'mg/dL',
                    'severity': 'high',
                    'category': 'dyslipidemia',
                    'description': f'LDL: {ldl:.1f} mg/dL（高値: 160-189）'
                })
            elif ldl >= 130:
                risk_factors.append({
                    'marker': 'LDL cholesterol',
                    'value': ldl,
                    'unit': 'mg/dL',
                    'severity': 'borderline',
                    'category': 'dyslipidemia',
                    'description': f'LDL: {ldl:.1f} mg/dL（境界域: 130-159）'
                })

        # HDLチェック
        hdl = patient.get('LBDHDD', np.nan)
        if not pd.isna(hdl):
            if gender == 2:  # Female
                threshold = 50
                gender_label = '女性'
            else:  # Male
                threshold = 40
                gender_label = '男性'

            if hdl < threshold:
                risk_factors.append({
                    'marker': 'HDL cholesterol',
                    'value': hdl,
                    'unit': 'mg/dL',
                    'severity': 'high',
                    'category': 'dyslipidemia',
                    'description': f'HDL: {hdl:.1f} mg/dL（{gender_label}低値: <{threshold}）'
                })

        # 中性脂肪チェック
        tg = patient.get('LBXTR', np.nan)
        if not pd.isna(tg):
            if tg >= 500:
                risk_factors.append({
                    'marker': 'Triglycerides',
                    'value': tg,
                    'unit': 'mg/dL',
                    'severity': 'very_high',
                    'category': 'dyslipidemia',
                    'description': f'中性脂肪: {tg:.1f} mg/dL（最高値: ≥500）'
                })
            elif tg >= 200:
                risk_factors.append({
                    'marker': 'Triglycerides',
                    'value': tg,
                    'unit': 'mg/dL',
                    'severity': 'high',
                    'category': 'dyslipidemia',
                    'description': f'中性脂肪: {tg:.1f} mg/dL（高値: 200-499）'
                })

        # TC/HDL比チェック
        tc_hdl_ratio = patient.get('TC_HDL_ratio', np.nan)
        if not pd.isna(tc_hdl_ratio) and tc_hdl_ratio > 5:
            risk_factors.append({
                'marker': 'TC/HDL ratio',
                'value': tc_hdl_ratio,
                'unit': 'ratio',
                'severity': 'high',
                'category': 'dyslipidemia',
                'description': f'TC/HDL比: {tc_hdl_ratio:.2f}（高リスク: >5.0）'
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

        if score >= 80:
            recommendations.extend([
                '【緊急】循環器専門医への即時紹介を推奨',
                'スタチン療法の開始を検討',
                '動脈硬化性疾患の精密検査（頸動脈エコー、心臓CT等）',
                '生活習慣の徹底的な改善指導'
            ])
        elif score >= 60:
            recommendations.extend([
                '循環器専門医への紹介を推奨',
                'スタチン療法の検討',
                '生活習慣改善指導（低脂肪食、有酸素運動）',
                '3ヶ月後の再検査'
            ])
        elif score >= 40:
            recommendations.extend([
                '生活習慣改善指導（食事療法、運動療法）',
                '6ヶ月後の再検査',
                '必要に応じて薬物療法を検討'
            ])
        elif score >= 20:
            recommendations.extend([
                '生活習慣の維持・改善',
                '年1回の定期検査'
            ])
        else:
            recommendations.extend([
                '現在の健康状態を維持',
                '年1回の定期健診'
            ])

        # 個別マーカーに基づく推奨
        ldl = patient.get('LBDLDL', np.nan)
        if not pd.isna(ldl) and ldl >= 190:
            recommendations.append('LDL-C ≥190: 家族性高コレステロール血症の除外検査を推奨')

        tg = patient.get('LBXTR', np.nan)
        if not pd.isna(tg) and tg >= 500:
            recommendations.append('TG ≥500: 急性膵炎リスクあり、フィブラート系薬剤の検討')

        return recommendations

    def calculate_10yr_cvd_risk(self, patient: Union[pd.Series, Dict]) -> Optional[float]:
        """
        10年心血管疾患リスクを推定（簡易版）

        Parameters
        ----------
        patient : pd.Series or dict
            患者データ

        Returns
        -------
        float or None
            10年CVDリスク（%）
        """
        # 簡易的なリスク推定（実際のASCVD Pooled Cohort Equationsは血圧や喫煙歴も必要）
        score = self.calculate_score(patient)
        age = patient.get('RIDAGEYR', np.nan)

        if pd.isna(age):
            return None

        # スコアと年齢から大まかなリスクを推定
        if score >= 80:
            base_risk = 30
        elif score >= 60:
            base_risk = 20
        elif score >= 40:
            base_risk = 10
        elif score >= 20:
            base_risk = 5
        else:
            base_risk = 2

        # 年齢による調整
        if age >= 65:
            base_risk *= 1.5
        elif age >= 55:
            base_risk *= 1.2

        return min(base_risk, 100)
