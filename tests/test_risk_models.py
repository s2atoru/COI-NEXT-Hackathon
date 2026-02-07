"""
リスクモデルのユニットテスト
"""

import pytest
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.cardiovascular_risk import CardiovascularRiskModel
from src.models.metabolic_risk import MetabolicRiskModel
from src.models.renal_risk import RenalRiskModel
from src.models.hepatic_risk import HepaticRiskModel
from src.models.hematologic_risk import HematologicRiskModel
from src.models.composite_risk import CompositeRiskModel


class TestCardiovascularRiskModel:
    """心血管リスクモデルのテスト"""

    def test_optimal_profile(self):
        """最適な脂質プロファイルのテスト"""
        model = CardiovascularRiskModel()
        patient = {
            'RIAGENDR': 1,
            'RIDAGEYR': 35,
            'LBDLDL': 90,
            'LBDHDD': 60,
            'LBXTR': 100,
            'TC_HDL_ratio': 3.0
        }
        score = model.calculate_score(patient)
        assert 0 <= score <= 30, f"Expected low score for optimal profile, got {score}"

    def test_high_risk_profile(self):
        """高リスク脂質プロファイルのテスト"""
        model = CardiovascularRiskModel()
        patient = {
            'RIAGENDR': 1,
            'RIDAGEYR': 65,
            'LBDLDL': 200,
            'LBDHDD': 35,
            'LBXTR': 300,
            'TC_HDL_ratio': 7.0
        }
        score = model.calculate_score(patient)
        assert score >= 60, f"Expected high score for high-risk profile, got {score}"

    def test_identify_risk_factors(self):
        """リスク因子特定のテスト"""
        model = CardiovascularRiskModel()
        patient = {
            'RIAGENDR': 1,
            'RIDAGEYR': 55,
            'LBDLDL': 190,
            'LBDHDD': 35,
            'LBXTR': 250
        }
        risk_factors = model.identify_risk_factors(patient)
        assert len(risk_factors) >= 2, "Expected multiple risk factors"


class TestMetabolicRiskModel:
    """代謝リスクモデルのテスト"""

    def test_normal_glucose(self):
        """正常血糖のテスト"""
        model = MetabolicRiskModel()
        patient = {
            'RIDAGEYR': 40,
            'LBXGLU': 90,
            'LBXGH': 5.2,
            'HOMA_IR': 1.5
        }
        score = model.calculate_score(patient)
        assert score <= 20, f"Expected low score for normal glucose, got {score}"

    def test_diabetes(self):
        """糖尿病のテスト"""
        model = MetabolicRiskModel()
        patient = {
            'RIDAGEYR': 60,
            'LBXGLU': 150,
            'LBXGH': 7.5,
            'HOMA_IR': 6.0
        }
        score = model.calculate_score(patient)
        assert score >= 70, f"Expected high score for diabetes, got {score}"

    def test_diabetes_status(self):
        """糖尿病ステータス判定のテスト"""
        model = MetabolicRiskModel()

        # 正常
        normal_patient = {'LBXGLU': 90, 'LBXGH': 5.2}
        assert model.assess_diabetes_status(normal_patient) == 'normal'

        # 糖尿病
        diabetes_patient = {'LBXGLU': 140, 'LBXGH': 7.0}
        assert model.assess_diabetes_status(diabetes_patient) == 'diabetes'


class TestRenalRiskModel:
    """腎機能リスクモデルのテスト"""

    def test_normal_kidney_function(self):
        """正常腎機能のテスト"""
        model = RenalRiskModel()
        patient = {
            'RIDAGEYR': 40,
            'RIAGENDR': 1,
            'eGFR': 100,
            'ACR': 15
        }
        score = model.calculate_score(patient)
        assert score <= 20, f"Expected low score for normal kidney function, got {score}"

    def test_ckd_stage_3(self):
        """CKDステージ3のテスト"""
        model = RenalRiskModel()
        patient = {
            'RIDAGEYR': 70,
            'RIAGENDR': 2,
            'eGFR': 50,
            'ACR': 80
        }
        score = model.calculate_score(patient)
        assert score >= 45, f"Expected moderate-high score for CKD stage 3, got {score}"

    def test_ckd_stage_assessment(self):
        """CKDステージ判定のテスト"""
        model = RenalRiskModel()
        patient = {
            'eGFR': 50,
            'ACR': 80
        }
        stage = model.assess_ckd_stage(patient)
        assert stage['gfr_stage'] == 'G3a'
        assert stage['albuminuria_stage'] == 'A2'


class TestHepaticRiskModel:
    """肝機能リスクモデルのテスト"""

    def test_normal_liver_function(self):
        """正常肝機能のテスト"""
        model = HepaticRiskModel()
        patient = {
            'RIAGENDR': 1,
            'RIDAGEYR': 40,
            'LBXSASSI': 25,
            'LBXSGTSI': 28,
            'FIB4': 0.8,
            'AST_ALT_ratio': 25/28
        }
        score = model.calculate_score(patient)
        assert score <= 25, f"Expected low score for normal liver function, got {score}"

    def test_advanced_fibrosis(self):
        """進行性肝線維化のテスト"""
        model = HepaticRiskModel()
        patient = {
            'RIAGENDR': 1,
            'RIDAGEYR': 65,
            'LBXSASSI': 80,
            'LBXSGTSI': 90,
            'FIB4': 4.0,
            'AST_ALT_ratio': 80/90
        }
        score = model.calculate_score(patient)
        assert score >= 60, f"Expected high score for advanced fibrosis, got {score}"


class TestHematologicRiskModel:
    """血液学的リスクモデルのテスト"""

    def test_normal_blood_counts(self):
        """正常血算のテスト"""
        model = HematologicRiskModel()
        patient = {
            'RIAGENDR': 1,
            'RIDAGEYR': 40,
            'LBXHGB': 15.0,
            'LBXWBCSI': 7.0,
            'LBXPLTSI': 250,
            'LBXMCVSI': 90
        }
        score = model.calculate_score(patient)
        assert score <= 20, f"Expected low score for normal blood counts, got {score}"

    def test_anemia(self):
        """貧血のテスト"""
        model = HematologicRiskModel()
        patient = {
            'RIAGENDR': 2,
            'RIDAGEYR': 50,
            'LBXHGB': 9.0,
            'LBXWBCSI': 5.0,
            'LBXPLTSI': 180,
            'LBXMCVSI': 75
        }
        score = model.calculate_score(patient)
        assert score >= 30, f"Expected moderate-high score for anemia, got {score}"

    def test_anemia_classification(self):
        """貧血分類のテスト"""
        model = HematologicRiskModel()

        # 小球性貧血
        microcytic = {'RIAGENDR': 1, 'LBXHGB': 11.0, 'LBXMCVSI': 75}
        assert model.classify_anemia_type(microcytic) == 'microcytic'

        # 大球性貧血
        macrocytic = {'RIAGENDR': 1, 'LBXHGB': 11.0, 'LBXMCVSI': 105}
        assert model.classify_anemia_type(macrocytic) == 'macrocytic'


class TestCompositeRiskModel:
    """総合リスクモデルのテスト"""

    def test_healthy_patient(self):
        """正常健康者のテスト"""
        model = CompositeRiskModel()
        patient = {
            'SEQN': 99999,
            'RIAGENDR': 1,
            'RIDAGEYR': 35,
            'LBDLDL': 95,
            'LBDHDD': 55,
            'LBXGLU': 90,
            'eGFR': 105,
            'LBXSASSI': 22,
            'LBXSGTSI': 25,
            'LBXHGB': 15.0
        }
        result = model.calculate_composite_score(patient)

        assert 0 <= result['composite_score'] <= 30
        assert result['risk_level'] in ['OPTIMAL', 'LOW']
        assert len(result['alerts']) == 0

    def test_high_risk_patient(self):
        """高リスク患者のテスト"""
        model = CompositeRiskModel()
        patient = {
            'SEQN': 88888,
            'RIAGENDR': 2,
            'RIDAGEYR': 68,
            'LBDLDL': 210,
            'LBDHDD': 38,
            'LBXGLU': 140,
            'LBXGH': 7.2,
            'eGFR': 35,
            'ACR': 120,
            'LBXSASSI': 58,
            'LBXSGTSI': 72,
            'FIB4': 2.8,
            'LBXHGB': 11.0
        }
        result = model.calculate_composite_score(patient)

        assert result['composite_score'] >= 60
        assert result['risk_level'] in ['HIGH', 'CRITICAL']
        assert len(result['alerts']) >= 2

    def test_result_structure(self):
        """結果構造のテスト"""
        model = CompositeRiskModel()
        patient = {'SEQN': 1, 'RIDAGEYR': 40, 'RIAGENDR': 1}
        result = model.calculate_composite_score(patient)

        # 必須フィールドの確認
        assert 'composite_score' in result
        assert 'risk_level' in result
        assert 'risk_label' in result
        assert 'domain_scores' in result
        assert 'alerts' in result
        assert 'modifiable_factors' in result
        assert 'recommendations' in result

        # ドメインスコアの確認
        expected_domains = ['cardiovascular', 'metabolic', 'renal', 'hepatic', 'hematologic']
        for domain in expected_domains:
            assert domain in result['domain_scores']

    def test_age_adjustment(self):
        """年齢補正のテスト"""
        model = CompositeRiskModel()

        # 若年者
        young_patient = {'RIDAGEYR': 30, 'RIAGENDR': 1, 'LBDLDL': 150}
        young_result = model.calculate_composite_score(young_patient)

        # 高齢者
        elderly_patient = {'RIDAGEYR': 75, 'RIAGENDR': 1, 'LBDLDL': 150}
        elderly_result = model.calculate_composite_score(elderly_patient)

        # 高齢者のスコアが高いことを確認
        assert elderly_result['composite_score'] > young_result['composite_score']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
