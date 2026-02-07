"""
肝機能リスク評価モデル

肝酵素とFIB-4 Indexに基づく肝疾患リスクを評価
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union
import yaml
from pathlib import Path


class HepaticRiskModel:
    """
    肝機能リスクスコア計算クラス

    評価項目:
    - AST（GOT）
    - ALT（GPT）
    - FIB-4 Index（肝線維化マーカー）
    - AST/ALT比
    - アルブミン
    - ビリルビン
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
                self.thresholds = config['hepatic']
        else:
            self.thresholds = thresholds.get('hepatic', {})

    def calculate_score(self, patient: Union[pd.Series, Dict]) -> float:
        """
        肝機能リスクスコアを計算（0-100点）

        Parameters
        ----------
        patient : pd.Series or dict
            患者データ

        Returns
        -------
        float
            肝機能リスクスコア
        """
        score = 0.0
        gender = patient.get('RIAGENDR', np.nan)

        # ASTスコア（重み: 20点満点）
        ast = patient.get('LBXSASSI', np.nan)
        if not pd.isna(ast):
            threshold = 40 if gender == 1 else 32
            if ast > threshold * 3:
                score += 20
            elif ast > threshold * 2:
                score += 15
            elif ast > threshold:
                score += 8

        # ALTスコア（重み: 25点満点）
        alt = patient.get('LBXSGTSI', np.nan)
        if not pd.isna(alt):
            threshold = 41 if gender == 1 else 33
            if alt > threshold * 3:
                score += 25
            elif alt > threshold * 2:
                score += 18
            elif alt > threshold:
                score += 10

        # FIB-4 Indexスコア（重み: 35点満点）
        fib4 = patient.get('FIB4', np.nan)
        if not pd.isna(fib4):
            if fib4 > 3.25:  # 高リスク（進行性線維化）
                score += 35
            elif fib4 > 1.45:  # 中リスク
                score += 18
            else:  # 低リスク
                score += 0

        # AST/ALT比スコア（重み: 10点満点）
        # AST/ALT > 1は肝硬変や進行性肝疾患を示唆
        ast_alt_ratio = patient.get('AST_ALT_ratio', np.nan)
        if not pd.isna(ast_alt_ratio):
            if ast_alt_ratio > 2:
                score += 10
            elif ast_alt_ratio > 1:
                score += 5

        # アルブミン低値（重み: 5点）
        albumin = patient.get('LBXSAL', np.nan)
        if not pd.isna(albumin) and albumin < 3.5:
            score += 5

        # ビリルビン高値（重み: 5点）
        bilirubin = patient.get('LBXSTB', np.nan)
        if not pd.isna(bilirubin) and bilirubin > 1.2:
            score += 5

        # 年齢補正（肝線維化は加齢で進行）
        age = patient.get('RIDAGEYR', np.nan)
        if not pd.isna(age):
            if age >= 65:
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

        # ASTチェック
        ast = patient.get('LBXSASSI', np.nan)
        if not pd.isna(ast):
            threshold = 40 if gender == 1 else 32
            if ast > threshold:
                severity = 'very_high' if ast > threshold * 2 else 'high'
                risk_factors.append({
                    'marker': 'AST',
                    'value': ast,
                    'unit': 'U/L',
                    'severity': severity,
                    'category': 'hepatic_injury',
                    'description': f'AST: {ast:.1f} U/L（基準値: <{threshold}）'
                })

        # ALTチェック
        alt = patient.get('LBXSGTSI', np.nan)
        if not pd.isna(alt):
            threshold = 41 if gender == 1 else 33
            if alt > threshold:
                severity = 'very_high' if alt > threshold * 2 else 'high'
                risk_factors.append({
                    'marker': 'ALT',
                    'value': alt,
                    'unit': 'U/L',
                    'severity': severity,
                    'category': 'hepatic_injury',
                    'description': f'ALT: {alt:.1f} U/L（基準値: <{threshold}）'
                })

        # FIB-4 Indexチェック
        fib4 = patient.get('FIB4', np.nan)
        if not pd.isna(fib4):
            if fib4 > 3.25:
                risk_factors.append({
                    'marker': 'FIB-4 Index',
                    'value': fib4,
                    'unit': 'index',
                    'severity': 'very_high',
                    'category': 'advanced_fibrosis',
                    'description': f'FIB-4: {fib4:.2f}（高リスク: >3.25、進行性線維化疑い）'
                })
            elif fib4 > 1.45:
                risk_factors.append({
                    'marker': 'FIB-4 Index',
                    'value': fib4,
                    'unit': 'index',
                    'severity': 'moderate',
                    'category': 'indeterminate_fibrosis',
                    'description': f'FIB-4: {fib4:.2f}（中リスク: 1.45-3.25）'
                })

        # AST/ALT比チェック
        ast_alt_ratio = patient.get('AST_ALT_ratio', np.nan)
        if not pd.isna(ast_alt_ratio) and ast_alt_ratio > 1:
            risk_factors.append({
                'marker': 'AST/ALT ratio',
                'value': ast_alt_ratio,
                'unit': 'ratio',
                'severity': 'moderate',
                'category': 'chronic_liver_disease',
                'description': f'AST/ALT比: {ast_alt_ratio:.2f}（>1: 肝硬変・慢性肝疾患疑い）'
            })

        # アルブミン低値
        albumin = patient.get('LBXSAL', np.nan)
        if not pd.isna(albumin) and albumin < 3.5:
            risk_factors.append({
                'marker': 'Albumin',
                'value': albumin,
                'unit': 'g/dL',
                'severity': 'high',
                'category': 'hepatic_synthetic_dysfunction',
                'description': f'アルブミン: {albumin:.1f} g/dL（低値: <3.5）'
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

        fib4 = patient.get('FIB4', np.nan)

        if score >= 80 or (not pd.isna(fib4) and fib4 > 3.25):
            recommendations.extend([
                '【緊急】肝臓専門医への即時紹介',
                '肝線維化の精密評価（FibroScan、肝生検の検討）',
                '肝硬変合併症のスクリーニング（食道静脈瘤、肝癌）',
                '原因疾患の精査（B型・C型肝炎、NASH、アルコール性等）',
                '肝庇護療法の開始'
            ])
        elif score >= 60:
            recommendations.extend([
                '肝臓専門医への紹介',
                '腹部超音波検査・CT検査',
                'ウイルス性肝炎マーカー（HBs抗原、HCV抗体）',
                '自己免疫性肝疾患の除外検査',
                '生活習慣改善（禁酒、減量）',
                '3-6ヶ月ごとの肝機能チェック'
            ])
        elif score >= 40:
            recommendations.extend([
                '肝機能異常の原因検索',
                '腹部超音波検査',
                'アルコール摂取量の確認・制限',
                '体重管理（BMI < 25目標）',
                '肝毒性薬剤の回避',
                '6ヶ月ごとの再検査'
            ])
        elif score >= 20:
            recommendations.extend([
                '生活習慣の見直し',
                '適正飲酒（男性20g/日、女性10g/日以下）',
                '年1回の肝機能検査'
            ])
        else:
            recommendations.extend([
                '現在の肝機能を維持',
                '定期健診での継続観察'
            ])

        # ALT高値でFIB-4低リスクの場合（NAFLD疑い）
        alt = patient.get('LBXSGTSI', np.nan)
        if not pd.isna(alt) and alt > 40 and not pd.isna(fib4) and fib4 < 1.45:
            recommendations.append('NAFLD（非アルコール性脂肪肝）疑い: 代謝性リスク因子の管理、減量')

        return recommendations

    def assess_fibrosis_risk(self, patient: Union[pd.Series, Dict]) -> str:
        """
        肝線維化リスクを評価

        Parameters
        ----------
        patient : pd.Series or dict
            患者データ

        Returns
        -------
        str
            線維化リスク（low/intermediate/high/insufficient_data）
        """
        fib4 = patient.get('FIB4', np.nan)

        if pd.isna(fib4):
            return 'insufficient_data'

        if fib4 > 3.25:
            return 'high'
        elif fib4 > 1.45:
            return 'intermediate'
        else:
            return 'low'
