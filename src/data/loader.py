"""
NHANESデータローダー

CSVファイルからデータを読み込み、基本的なデータ型変換を行う
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Union
from loguru import logger


class NHANESLoader:
    """
    NHANESデータを読み込むクラス
    """

    def __init__(self, data_dir: Union[str, Path] = "data/raw"):
        """
        Parameters
        ----------
        data_dir : str or Path
            データディレクトリのパス
        """
        self.data_dir = Path(data_dir)
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")

    def load_csv(self, filename: str, **kwargs) -> pd.DataFrame:
        """
        CSVファイルを読み込む

        Parameters
        ----------
        filename : str
            ファイル名
        **kwargs
            pd.read_csvに渡す追加引数

        Returns
        -------
        pd.DataFrame
            読み込んだデータフレーム
        """
        filepath = self.data_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        logger.info(f"Loading data from {filepath}")
        df = pd.read_csv(filepath, **kwargs)
        logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")

        return df

    def load_all_datasets(self) -> dict:
        """
        データディレクトリ内の全CSVファイルを読み込む

        Returns
        -------
        dict
            ファイル名をキー、DataFrameを値とする辞書
        """
        datasets = {}
        csv_files = list(self.data_dir.glob("*.csv"))

        if not csv_files:
            logger.warning(f"No CSV files found in {self.data_dir}")
            return datasets

        logger.info(f"Found {len(csv_files)} CSV files")

        for filepath in csv_files:
            try:
                df = pd.read_csv(filepath)
                datasets[filepath.stem] = df
                logger.info(f"Loaded {filepath.name}: {len(df)} rows")
            except Exception as e:
                logger.error(f"Error loading {filepath.name}: {e}")

        return datasets

    def get_data_info(self, df: pd.DataFrame) -> dict:
        """
        データの基本情報を取得

        Parameters
        ----------
        df : pd.DataFrame
            対象データフレーム

        Returns
        -------
        dict
            データの基本情報
        """
        info = {
            "n_rows": len(df),
            "n_columns": len(df.columns),
            "columns": df.columns.tolist(),
            "dtypes": df.dtypes.to_dict(),
            "missing_counts": df.isnull().sum().to_dict(),
            "missing_percentages": (df.isnull().sum() / len(df) * 100).to_dict(),
            "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
        }

        return info

    def merge_datasets(
        self,
        datasets: dict,
        on: str = "SEQN",
        how: str = "outer"
    ) -> pd.DataFrame:
        """
        複数のデータセットを統合

        Parameters
        ----------
        datasets : dict
            統合するデータセット群
        on : str
            統合キー（デフォルト: SEQN）
        how : str
            統合方法（デフォルト: outer）

        Returns
        -------
        pd.DataFrame
            統合されたデータフレーム
        """
        if not datasets:
            raise ValueError("No datasets to merge")

        logger.info(f"Merging {len(datasets)} datasets on '{on}' using '{how}' join")

        # 最初のデータセットから開始
        merged_df = list(datasets.values())[0].copy()

        # 残りのデータセットを順次統合
        for name, df in list(datasets.items())[1:]:
            before_cols = len(merged_df.columns)
            merged_df = merged_df.merge(df, on=on, how=how, suffixes=("", f"_{name}"))
            after_cols = len(merged_df.columns)
            logger.info(f"Merged {name}: {after_cols - before_cols} new columns")

        logger.info(f"Final merged dataset: {len(merged_df)} rows, {len(merged_df.columns)} columns")

        return merged_df
