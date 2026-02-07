"""
血液学的リスク評価モデル

血算データに基づく血液疾患リスクを評価
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union
import yaml
from pathlib import Path


class HematologicRiskModel:
    """
    血液学的リスクスコア計算クラス

    評価項目:
    - ヘモグロビン（貧血評価）
    - 白血球数
    - 血小板数
    - MCV（平均赤血球容積）
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
                self.thresholds = config['hematologic']
        else:
            self.thresholds = thresholds.get('hematologic', {})

    def calculate_score(self, patient: Union[pd.Series, Dict]) -> float:
        """
        血液学的リスクスコアを計算（0-100点）

        Parameters
        ----------
        patient : pd.Series or dict
            患者データ

        Returns
        -------
        float
            血液学的リスクスコア
        """
        score = 0.0
        gender = patient.get('RIAGENDR', np.nan)

        # ヘモグロビンスコア（重み: 40点満点）
        hgb = patient.get('LBXHGB', np.nan)
        if not pd.isna(hgb):
            if gender == 2:  # Female
                threshold = 12
            else:  # Male
                threshold = 13

            if hgb < threshold - 3:  # 重度貧血
                score += 40
            elif hgb < threshold - 2:  # 中等度貧血
                score += 30
            elif hgb < threshold:  # 軽度貧血
                score += 15
            elif hgb > 18:  # 多血症疑い
                score += 10

        # 白血球スコア（重み: 25点満点）
        wbc = patient.get('LBXWBCSI', np.nan)
        if not pd.isna(wbc):
            if wbc < 3.0:  # 重度白血球減少
                score += 25
            elif wbc < 4.0:  # 軽度白血球減少
                score += 12
            elif wbc > 15.0:  # 高度白血球増多
                score += 25
            elif wbc > 11.0:  # 軽度白血球増多
                score += 10

        # 血小板スコア（重み: 25点満点）
        plt = patient.get('LBXPLTSI', np.nan)
        if not pd.isna(plt):
            if plt < 50:  # 重度血小板減少
                score += 25
            elif plt < 100:  # 中等度血小板減少
                score += 20
            elif plt < 150:  # 軽度血小板減少
                score += 10
            elif plt > 450:  # 血小板増多
                score += 15

        # MCVスコア（重み: 10点満点）
        mcv = patient.get('LBXMCVSI', np.nan)
        if not pd.isna(mcv):
            if mcv < 70:  # 高度小球性
                score += 10
            elif mcv < 80:  # 小球性
                score += 5
            elif mcv > 100:  # 大球性
                score += 5

        # 年齢補正（高齢者は貧血リスク高い）
        age = patient.get('RIDAGEYR', np.nan)
        if not pd.isna(age) and age >= 75:
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
        gender = patient.get('RIAGENDR', np.nan)

        # ヘモグロビンチェック
        hgb = patient.get('LBXHGB', np.nan)
        if not pd.isna(hgb):
            if gender == 2:  # Female
                threshold = 12
                gender_label = '女性'
            else:  # Male
                threshold = 13
                gender_label = '男性'

            if hgb < threshold:
                if hgb < threshold - 3:
                    severity = 'critical'
                    category = '重度貧血'
                elif hgb < threshold - 2:
                    severity = 'very_high'
                    category = '中等度貧血'
                else:
                    severity = 'high'
                    category = '軽度貧血'

                risk_factors.append({
                    'marker': 'Hemoglobin',
                    'value': hgb,
                    'unit': 'g/dL',
                    'severity': severity,
                    'category': 'anemia',
                    'description': f'ヘモグロビン: {hgb:.1f} g/dL（{gender_label}{category}: <{threshold}）'
                })
            elif hgb > 18:
                risk_factors.append({
                    'marker': 'Hemoglobin',
                    'value': hgb,
                    'unit': 'g/dL',
                    'severity': 'moderate',
                    'category': 'polycythemia',
                    'description': f'ヘモグロビン: {hgb:.1f} g/dL（多血症疑い: >18）'
                })

        # 白血球チェック
        wbc = patient.get('LBXWBCSI', np.nan)
        if not pd.isna(wbc):
            if wbc < 4.0:
                severity = 'very_high' if wbc < 3.0 else 'high'
                risk_factors.append({
                    'marker': 'WBC',
                    'value': wbc,
                    'unit': '10³/μL',
                    'severity': severity,
                    'category': 'leukopenia',
                    'description': f'白血球: {wbc:.1f} 10³/μL（白血球減少: <4.0）'
                })
            elif wbc > 11.0:
                severity = 'very_high' if wbc > 15.0 else 'moderate'
                risk_factors.append({
                    'marker': 'WBC',
                    'value': wbc,
                    'unit': '10³/μL',
                    'severity': severity,
                    'category': 'leukocytosis',
                    'description': f'白血球: {wbc:.1f} 10³/μL（白血球増多: >11.0）'
                })

        # 血小板チェック
        plt = patient.get('LBXPLTSI', np.nan)
        if not pd.isna(plt):
            if plt < 150:
                if plt < 50:
                    severity = 'critical'
                    category = '重度血小板減少'
                elif plt < 100:
                    severity = 'very_high'
                    category = '中等度血小板減少'
                else:
                    severity = 'high'
                    category = '軽度血小板減少'

                risk_factors.append({
                    'marker': 'Platelet',
                    'value': plt,
                    'unit': '10³/μL',
                    'severity': severity,
                    'category': 'thrombocytopenia',
                    'description': f'血小板: {plt:.0f} 10³/μL（{category}: <150）'
                })
            elif plt > 450:
                risk_factors.append({
                    'marker': 'Platelet',
                    'value': plt,
                    'unit': '10³/μL',
                    'severity': 'moderate',
                    'category': 'thrombocytosis',
                    'description': f'血小板: {plt:.0f} 10³/μL（血小板増多: >450）'
                })

        # MCVチェック（貧血の鑑別に重要）
        mcv = patient.get('LBXMCVSI', np.nan)
        if not pd.isna(mcv):
            if mcv < 80:
                severity = 'high' if mcv < 70 else 'moderate'
                risk_factors.append({
                    'marker': 'MCV',
                    'value': mcv,
                    'unit': 'fL',
                    'severity': severity,
                    'category': 'microcytic_anemia',
                    'description': f'MCV: {mcv:.1f} fL（小球性貧血疑い: <80、鉄欠乏性貧血/サラセミア等）'
                })
            elif mcv > 100:
                risk_factors.append({
                    'marker': 'MCV',
                    'value': mcv,
                    'unit': 'fL',
                    'severity': 'moderate',
                    'category': 'macrocytic_anemia',
                    'description': f'MCV: {mcv:.1f} fL（大球性貧血疑い: >100、ビタミンB12/葉酸欠乏等）'
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
                '【緊急】血液内科への即時紹介',
                '詳細な血算検査（血液像、網状赤血球）',
                '骨髄検査の検討',
                '出血・感染リスクの評価と対策'
            ])
        elif score >= 60:
            recommendations.extend([
                '血液内科への紹介',
                '貧血の原因精査（鉄、ビタミンB12、葉酸、フェリチン）',
                '末梢血液像の確認',
                '必要に応じて追加検査（骨髄検査等）'
            ])
        elif score >= 40:
            recommendations.extend([
                '血液異常の原因検索',
                '鉄欠乏性貧血の除外（血清鉄、TIBC、フェリチン）',
                '慢性疾患に伴う貧血の評価',
                '3ヶ月後の再検査'
            ])
        elif score >= 20:
            recommendations.extend([
                '軽度異常の経過観察',
                '栄養状態の確認',
                '6ヶ月後の再検査'
            ])
        else:
            recommendations.extend([
                '正常範囲内',
                '定期健診での継続観察'
            ])

        # 個別マーカーに基づく推奨
        hgb = patient.get('LBXHGB', np.nan)
        mcv = patient.get('LBXMCVSI', np.nan)

        # 小球性貧血（鉄欠乏性貧血疑い）
        if not pd.isna(hgb) and not pd.isna(mcv):
            gender = patient.get('RIAGENDR', np.nan)
            threshold = 12 if gender == 2 else 13
            if hgb < threshold and mcv < 80:
                recommendations.append('小球性貧血: 鉄剤投与の検討、消化管出血の除外')

        # 血小板減少
        plt = patient.get('LBXPLTSI', np.nan)
        if not pd.isna(plt) and plt < 50:
            recommendations.append('重度血小板減少: 出血リスク高、外傷回避、抗血小板薬の中止検討')

        return recommendations

    def classify_anemia_type(self, patient: Union[pd.Series, Dict]) -> Optional[str]:
        """
        貧血のタイプを分類

        Parameters
        ----------
        patient : pd.Series or dict
            患者データ

        Returns
        -------
        str or None
            貧血タイプ（microcytic/normocytic/macrocytic/None）
        """
        hgb = patient.get('LBXHGB', np.nan)
        mcv = patient.get('LBXMCVSI', np.nan)
        gender = patient.get('RIAGENDR', np.nan)

        # 貧血の有無
        if pd.isna(hgb) or pd.isna(gender):
            return None

        threshold = 12 if gender == 2 else 13
        if hgb >= threshold:
            return None  # 貧血なし

        # MCVに基づく分類
        if pd.isna(mcv):
            return 'anemia_type_unknown'

        if mcv < 80:
            return 'microcytic'  # 小球性貧血（鉄欠乏性、サラセミア等）
        elif mcv <= 100:
            return 'normocytic'  # 正球性貧血（慢性疾患、腎性貧血等）
        else:
            return 'macrocytic'  # 大球性貧血（B12/葉酸欠乏、骨髄異形成等）
