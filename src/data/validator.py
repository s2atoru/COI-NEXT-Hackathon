"""
データ検証モジュール

データの品質チェックと妥当性検証を行う
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from loguru import logger


class DataValidator:
    """
    データの品質と妥当性を検証するクラス
    """

    def __init__(self):
        self.validation_results = {}

    def validate(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        完全な検証パイプラインを実行

        Parameters
        ----------
        df : pd.DataFrame
            検証対象データ

        Returns
        -------
        dict
            検証結果
        """
        logger.info("Starting data validation")

        results = {
            "is_valid": True,
            "checks": {}
        }

        # 各検証を実行
        checks = [
            ("duplicates", self._check_duplicates(df)),
            ("missing_critical", self._check_critical_columns(df)),
            ("value_ranges", self._check_value_ranges(df)),
            ("consistency", self._check_data_consistency(df))
        ]

        for check_name, check_result in checks:
            results["checks"][check_name] = check_result
            if not check_result["passed"]:
                results["is_valid"] = False
                logger.warning(f"Validation check failed: {check_name}")

        if results["is_valid"]:
            logger.info("All validation checks passed")
        else:
            logger.error("Some validation checks failed")

        self.validation_results = results
        return results

    def _check_duplicates(self, df: pd.DataFrame) -> Dict:
        """
        重複行をチェック

        Parameters
        ----------
        df : pd.DataFrame
            検証対象データ

        Returns
        -------
        dict
            チェック結果
        """
        n_duplicates = df.duplicated(subset='SEQN').sum() if 'SEQN' in df.columns else 0

        return {
            "passed": n_duplicates == 0,
            "n_duplicates": int(n_duplicates),
            "message": f"Found {n_duplicates} duplicate SEQN values" if n_duplicates > 0 else "No duplicates"
        }

    def _check_critical_columns(self, df: pd.DataFrame) -> Dict:
        """
        重要カラムの欠損をチェック

        Parameters
        ----------
        df : pd.DataFrame
            検証対象データ

        Returns
        -------
        dict
            チェック結果
        """
        critical_cols = ['SEQN', 'RIDAGEYR', 'RIAGENDR']
        missing_cols = [col for col in critical_cols if col not in df.columns]
        high_missing = {}

        for col in critical_cols:
            if col in df.columns:
                missing_pct = df[col].isnull().sum() / len(df) * 100
                if missing_pct > 10:  # 10%以上欠損
                    high_missing[col] = missing_pct

        passed = len(missing_cols) == 0 and len(high_missing) == 0

        return {
            "passed": passed,
            "missing_columns": missing_cols,
            "high_missing_rate": high_missing,
            "message": "All critical columns present with acceptable missing rates" if passed else "Critical column issues detected"
        }

    def _check_value_ranges(self, df: pd.DataFrame) -> Dict:
        """
        値の範囲をチェック

        Parameters
        ----------
        df : pd.DataFrame
            検証対象データ

        Returns
        -------
        dict
            チェック結果
        """
        range_checks = {
            'RIDAGEYR': (0, 120),
            'RIAGENDR': (1, 2),
            'LBXTC': (0, 500),
            'LBDHDD': (0, 200),
            'LBDLDL': (0, 400),
            'LBXTR': (0, 1000),
            'LBXGLU': (0, 500),
            'LBXSCR': (0, 20),
            'LBXHGB': (0, 25)
        }

        violations = {}

        for col, (min_val, max_val) in range_checks.items():
            if col in df.columns:
                out_of_range = ((df[col] < min_val) | (df[col] > max_val)) & df[col].notna()
                n_violations = out_of_range.sum()
                if n_violations > 0:
                    violations[col] = {
                        "n_violations": int(n_violations),
                        "expected_range": (min_val, max_val),
                        "actual_range": (float(df[col].min()), float(df[col].max()))
                    }

        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "message": "All values within expected ranges" if len(violations) == 0 else f"{len(violations)} columns with out-of-range values"
        }

    def _check_data_consistency(self, df: pd.DataFrame) -> Dict:
        """
        データの一貫性をチェック

        Parameters
        ----------
        df : pd.DataFrame
            検証対象データ

        Returns
        -------
        dict
            チェック結果
        """
        issues = []

        # HDL + LDL ≈ TC の確認（±20%の誤差許容）
        if all(col in df.columns for col in ['LBXTC', 'LBDHDD', 'LBDLDL', 'LBXTR']):
            # Friedewald式: TC = HDL + LDL + TG/5
            calculated_tc = df['LBDHDD'] + df['LBDLDL'] + df['LBXTR'] / 5
            actual_tc = df['LBXTC']
            diff_pct = np.abs((calculated_tc - actual_tc) / actual_tc * 100)

            # 20%以上の差がある行を検出
            inconsistent = (diff_pct > 20) & calculated_tc.notna() & actual_tc.notna()
            n_inconsistent = inconsistent.sum()

            if n_inconsistent > 0:
                issues.append({
                    "type": "lipid_profile_inconsistency",
                    "n_cases": int(n_inconsistent),
                    "description": "TC ≠ HDL + LDL + TG/5 (>20% difference)"
                })

        # eGFRとクレアチニンの整合性
        if 'eGFR' in df.columns and 'LBXSCR' in df.columns:
            # 高クレアチニン(>2)で高eGFR(>60)は矛盾
            inconsistent = (df['LBXSCR'] > 2) & (df['eGFR'] > 60)
            n_inconsistent = inconsistent.sum()

            if n_inconsistent > 0:
                issues.append({
                    "type": "renal_function_inconsistency",
                    "n_cases": int(n_inconsistent),
                    "description": "High creatinine (>2) with high eGFR (>60)"
                })

        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "message": "Data is consistent" if len(issues) == 0 else f"{len(issues)} consistency issues found"
        }

    def generate_report(self) -> str:
        """
        検証結果のレポートを生成

        Returns
        -------
        str
            レポート文字列
        """
        if not self.validation_results:
            return "No validation results available. Run validate() first."

        report = ["=" * 60]
        report.append("DATA VALIDATION REPORT")
        report.append("=" * 60)
        report.append(f"Overall Status: {'PASSED' if self.validation_results['is_valid'] else 'FAILED'}")
        report.append("")

        for check_name, check_result in self.validation_results["checks"].items():
            status = "✓" if check_result["passed"] else "✗"
            report.append(f"{status} {check_name.upper()}: {check_result['message']}")

            # 詳細情報を表示
            if not check_result["passed"]:
                for key, value in check_result.items():
                    if key not in ["passed", "message"] and value:
                        report.append(f"  - {key}: {value}")

        report.append("=" * 60)

        return "\n".join(report)
