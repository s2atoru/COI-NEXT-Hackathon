"""
NHANESデータ前処理パイプライン

欠損値処理、外れ値除去、派生変数生成などを行う
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Tuple
from loguru import logger


class NHANESPreprocessor:
    """
    NHANESデータの前処理を行うクラス

    主な機能:
    - 欠損値の数値化
    - データ型変換
    - 外れ値処理（Winsorization）
    - 派生変数の生成（eGFR, HOMA-IR, FIB-4等）
    """

    def __init__(self, winsorize_percentile: float = 0.995):
        """
        Parameters
        ----------
        winsorize_percentile : float
            外れ値処理の上限パーセンタイル（デフォルト: 99.5%）
        """
        self.winsorize_percentile = winsorize_percentile

    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        完全な前処理パイプラインを実行

        Parameters
        ----------
        df : pd.DataFrame
            元データ

        Returns
        -------
        pd.DataFrame
            前処理済みデータ
        """
        logger.info("Starting preprocessing pipeline")
        df = df.copy()

        # 1. 欠損値の数値化
        df = self._handle_missing_values(df)

        # 2. データ型変換
        df = self._convert_dtypes(df)

        # 3. 外れ値処理
        df = self._handle_outliers(df)

        # 4. 年齢・性別グループの作成
        df = self._create_demographic_groups(df)

        # 5. 派生変数の生成
        df = self._calculate_derived_features(df)

        logger.info(f"Preprocessing complete: {len(df)} rows, {len(df.columns)} columns")
        return df

    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        欠損値を数値化（"NA"文字列 → np.nan）

        Parameters
        ----------
        df : pd.DataFrame
            元データ

        Returns
        -------
        pd.DataFrame
            欠損値処理済みデータ
        """
        logger.info("Handling missing values")
        df = df.replace(['NA', 'na', 'N/A', ''], np.nan)

        # 欠損率をログ出力
        missing_pct = (df.isnull().sum() / len(df) * 100).round(2)
        high_missing = missing_pct[missing_pct > 50]
        if len(high_missing) > 0:
            logger.warning(f"Columns with >50% missing data:\n{high_missing}")

        return df

    def _convert_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        データ型を適切に変換

        Parameters
        ----------
        df : pd.DataFrame
            元データ

        Returns
        -------
        pd.DataFrame
            型変換済みデータ
        """
        logger.info("Converting data types")

        # 数値列を特定（SEQN, RIAGENDR以外）
        exclude_cols = ['SEQN', 'RIAGENDR']
        numeric_cols = [col for col in df.columns if col not in exclude_cols]

        # 数値型に変換
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # SEQNは整数型
        if 'SEQN' in df.columns:
            df['SEQN'] = pd.to_numeric(df['SEQN'], errors='coerce').astype('Int64')

        # 性別はカテゴリ型
        if 'RIAGENDR' in df.columns:
            df['RIAGENDR'] = df['RIAGENDR'].astype('category')

        return df

    def _handle_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        外れ値をWinsorization（上限値でクリッピング）

        Parameters
        ----------
        df : pd.DataFrame
            元データ

        Returns
        -------
        pd.DataFrame
            外れ値処理済みデータ
        """
        logger.info(f"Handling outliers (winsorization at {self.winsorize_percentile * 100}%)")

        numeric_cols = df.select_dtypes(include=[np.number]).columns
        exclude_cols = ['SEQN', 'RIDAGEYR', 'RIAGENDR']
        cols_to_winsorize = [col for col in numeric_cols if col not in exclude_cols]

        for col in cols_to_winsorize:
            if df[col].notna().sum() > 0:
                upper = df[col].quantile(self.winsorize_percentile)
                n_clipped = (df[col] > upper).sum()
                if n_clipped > 0:
                    df[col] = df[col].clip(upper=upper)
                    logger.debug(f"{col}: clipped {n_clipped} values at {upper:.2f}")

        return df

    def _create_demographic_groups(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        年齢・性別グループを作成

        Parameters
        ----------
        df : pd.DataFrame
            元データ

        Returns
        -------
        pd.DataFrame
            グループ変数追加済みデータ
        """
        logger.info("Creating demographic groups")

        if 'RIDAGEYR' in df.columns:
            df['age_group'] = pd.cut(
                df['RIDAGEYR'],
                bins=[0, 18, 40, 65, 80, 120],
                labels=['pediatric', 'young_adult', 'middle_age', 'elderly', 'very_elderly'],
                right=False
            )

        if 'RIAGENDR' in df.columns:
            # 性別ラベルを作成（既に文字列の場合はそのまま、数値の場合は変換）
            # NHANES data may have either string ('Male'/'Female') or numeric (1/2) format
            if df['RIAGENDR'].dtype in ['object', 'category']:
                # Already in string format
                df['gender_label'] = df['RIAGENDR'].astype(str)
            else:
                # Numeric format: 1=Male, 2=Female
                gender_map = {1: 'Male', 2: 'Female'}
                df['gender_label'] = df['RIAGENDR'].map(gender_map)

        return df

    def _calculate_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        派生変数を計算

        Parameters
        ----------
        df : pd.DataFrame
            元データ

        Returns
        -------
        pd.DataFrame
            派生変数追加済みデータ
        """
        logger.info("Calculating derived features")

        # TC/HDL比
        if 'LBXTC' in df.columns and 'LBDHDD' in df.columns:
            df['TC_HDL_ratio'] = df['LBXTC'] / df['LBDHDD']
            logger.debug("Calculated TC/HDL ratio")

        # LDL/HDL比
        if 'LBDLDL' in df.columns and 'LBDHDD' in df.columns:
            df['LDL_HDL_ratio'] = df['LBDLDL'] / df['LBDHDD']
            logger.debug("Calculated LDL/HDL ratio")

        # 非HDLコレステロール
        if 'LBXTC' in df.columns and 'LBDHDD' in df.columns:
            df['non_HDL'] = df['LBXTC'] - df['LBDHDD']
            logger.debug("Calculated non-HDL cholesterol")

        # eGFR (CKD-EPI式)
        if all(col in df.columns for col in ['LBXSCR', 'RIDAGEYR', 'RIAGENDR']):
            df['eGFR'] = df.apply(self._calculate_egfr, axis=1)
            logger.debug("Calculated eGFR")

        # HOMA-IR (インスリン抵抗性指標)
        if 'LBXIN' in df.columns and 'LBXGLU' in df.columns:
            df['HOMA_IR'] = (df['LBXIN'] * df['LBXGLU']) / 405
            logger.debug("Calculated HOMA-IR")

        # FIB-4 Index (肝線維化マーカー)
        if all(col in df.columns for col in ['RIDAGEYR', 'LBXSASSI', 'LBXPLTSI', 'LBXSGTSI']):
            df['FIB4'] = (df['RIDAGEYR'] * df['LBXSASSI']) / \
                         (df['LBXPLTSI'] * np.sqrt(df['LBXSGTSI']))
            logger.debug("Calculated FIB-4 Index")

        # AST/ALT比
        if 'LBXSASSI' in df.columns and 'LBXSGTSI' in df.columns:
            df['AST_ALT_ratio'] = df['LBXSASSI'] / df['LBXSGTSI']
            logger.debug("Calculated AST/ALT ratio")

        # 尿中アルブミン/クレアチニン比 (ACR)
        if 'URXUMA' in df.columns and 'URXUCR' in df.columns:
            df['ACR'] = df['URXUMA'] / df['URXUCR'] * 1000  # mg/g単位に変換
            logger.debug("Calculated ACR")

        return df

    @staticmethod
    def _calculate_egfr(row: pd.Series) -> float:
        """
        eGFRをCKD-EPI式で計算

        Parameters
        ----------
        row : pd.Series
            患者データの1行

        Returns
        -------
        float
            eGFR値（mL/min/1.73m²）
        """
        try:
            scr = row['LBXSCR']  # 血清クレアチニン (mg/dL)
            age = row['RIDAGEYR']
            gender = row['RIAGENDR']  # 1=Male, 2=Female

            if pd.isna(scr) or pd.isna(age) or pd.isna(gender):
                return np.nan

            # CKD-EPI式のパラメータ
            if gender == 2:  # Female
                kappa = 0.7
                alpha = -0.329
                if scr <= kappa:
                    egfr = 144 * (scr / kappa) ** alpha * (0.993 ** age)
                else:
                    egfr = 144 * (scr / kappa) ** -1.209 * (0.993 ** age)
            else:  # Male
                kappa = 0.9
                alpha = -0.411
                if scr <= kappa:
                    egfr = 141 * (scr / kappa) ** alpha * (0.993 ** age)
                else:
                    egfr = 141 * (scr / kappa) ** -1.209 * (0.993 ** age)

            return egfr

        except Exception:
            return np.nan

    def get_preprocessing_summary(self, df_original: pd.DataFrame, df_processed: pd.DataFrame) -> dict:
        """
        前処理の要約統計を取得

        Parameters
        ----------
        df_original : pd.DataFrame
            元データ
        df_processed : pd.DataFrame
            前処理済みデータ

        Returns
        -------
        dict
            前処理の要約
        """
        summary = {
            "original_shape": df_original.shape,
            "processed_shape": df_processed.shape,
            "new_columns": [col for col in df_processed.columns if col not in df_original.columns],
            "missing_data_reduction": {
                "before": df_original.isnull().sum().sum(),
                "after": df_processed.isnull().sum().sum()
            }
        }

        return summary
