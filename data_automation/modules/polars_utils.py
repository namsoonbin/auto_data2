# -*- coding: utf-8 -*-
"""
Polars 전용 유틸리티 모듈
pandas에서 polars로 마이그레이션을 위한 핵심 함수들
"""
import polars as pl
import pandas as pd
import numpy as np
import io
import logging
from typing import Union, Optional, Any


def normalize_product_id_expr() -> pl.Expr:
    """상품ID를 정규화하는 Polars Expression - 타입 안전성 강화"""
    return (
        pl.col("상품ID")
        .cast(pl.Utf8, strict=False)  # 안전한 타입 변환 (Context7 모범 사례)
        .fill_null("")  # null을 먼저 처리
        .str.strip_chars()  # 공백 제거
        .str.replace_all(r"\.0+$", "", literal=False)  # 끝의 .0 제거
        .str.replace_all(r"^\.+|\.+$", "", literal=False)  # 앞뒤 점 제거
        # 빈 문자열 체크를 추가하여 안전성 확보
        .map_elements(lambda x: x if x and x.strip() else "", return_dtype=pl.Utf8, skip_nulls=True)
    )

def normalize_product_id_polars(value: Any) -> str:
    """하위 호환성을 위한 개별 값 정규화 (비권장 - Expression 사용 권장)"""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ''

    # 임시 DataFrame으로 처리 (성능상 좋지 않음)
    temp_df = pl.DataFrame({"상품ID": [value]})
    result = temp_df.with_columns(normalize_product_id_expr()).get_column("상품ID")[0]
    return result if result is not None else ""


def normalize_option_info_expr() -> pl.Expr:
    """옵션정보를 정규화하는 Polars Expression - 타입 안전성 및 성능 최적화"""
    # Context7 모범 사례: 여러 replace를 하나의 정규식으로 통합
    empty_patterns = r"^(단일|기본옵션|선택안함|null|none|없음|nan|NAN|None|NULL)$"

    return (
        pl.col("옵션정보")
        .cast(pl.Utf8, strict=False)  # 안전한 타입 변환
        .fill_null("")  # null 먼저 처리
        .str.strip_chars()  # 공백 제거
        # 하나의 정규식으로 모든 빈값 패턴 처리 (성능 향상)
        .str.replace_all(empty_patterns, "", literal=False)
        # 빈 문자열인 경우 빈 문자열로 정규화
        .map_elements(lambda x: "" if not x or x.isspace() else x,
                     return_dtype=pl.Utf8, skip_nulls=True)
    )

def normalize_option_info_polars(value: Any) -> str:
    """하위 호환성을 위한 개별 값 정규화 (비권장 - Expression 사용 권장)"""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ''

    # 임시 DataFrame으로 처리 (성능상 좋지 않음)
    temp_df = pl.DataFrame({"옵션정보": [value]})
    result = temp_df.with_columns(normalize_option_info_expr()).get_column("옵션정보")[0]
    return result if result is not None else ""


def read_protected_excel_polars(file_path: str, password: Optional[str] = None, **kwargs) -> pl.DataFrame:
    """
    암호로 보호된 Excel 파일을 Polars DataFrame으로 읽는 함수
    pandas 버전과 호환성 유지하면서 Polars 최적화
    """
    try:
        # 먼저 암호 없이 Polars로 직접 시도
        return pl.read_excel(file_path, **kwargs)
    except Exception as e:
        if password is None:
            logging.error(f"암호 보호된 파일이지만 암호가 제공되지 않았습니다: {file_path}")
            raise e

        # msoffcrypto-tool 사용 시도
        try:
            import msoffcrypto

            with open(file_path, 'rb') as file:
                office_file = msoffcrypto.OfficeFile(file)
                office_file.load_key(password=password)

                # 메모리에서 해독된 파일 처리
                decrypted = io.BytesIO()
                try:
                    # 최신 버전: decrypt 메서드 사용
                    office_file.decrypt(decrypted)
                except AttributeError:
                    # 이전 버전: save 메서드 사용
                    office_file.save(decrypted)

                decrypted.seek(0)
                # 해독된 파일을 pandas로 먼저 읽고 Polars로 변환
                pandas_df = pd.read_excel(decrypted, engine='openpyxl', **kwargs)
                return pl.from_pandas(pandas_df)

        except ImportError:
            logging.error("msoffcrypto-tool이 설치되지 않았습니다.")
            logging.error("해결 방법: pip install msoffcrypto-tool")
            raise ImportError("msoffcrypto-tool 라이브러리가 필요합니다. 'pip install msoffcrypto-tool'로 설치하세요.")
        except Exception as decrypt_error:
            logging.error(f"암호 해독 실패: {decrypt_error}")
            raise decrypt_error


def safe_divide_polars(numerator: pl.Expr, denominator: pl.Expr, fill_value: float = 0.0) -> pl.Expr:
    """안전한 나누기 - Context7 모범 사례 적용 (NaN, inf 처리 포함)"""
    return pl.when(
        # 분모가 0, null, NaN인 경우 또는 분자가 null인 경우
        (denominator == 0) |
        denominator.is_null() |
        denominator.is_nan() |
        numerator.is_null() |
        numerator.is_nan()
    ).then(fill_value).otherwise(
        # 안전한 나누기 실행 후 무한대 값도 처리
        pl.when((numerator / denominator).is_infinite())
        .then(fill_value)
        .otherwise(numerator / denominator)
    )


def convert_pandas_to_polars(df: pd.DataFrame) -> pl.DataFrame:
    """pandas DataFrame을 Polars DataFrame으로 변환"""
    return pl.from_pandas(df)


def convert_polars_to_pandas(df: pl.DataFrame) -> pd.DataFrame:
    """Polars DataFrame을 pandas DataFrame으로 변환"""
    return df.to_pandas()


def create_agg_expressions(agg_dict: dict) -> list[pl.Expr]:
    """
    집계 딕셔너리를 Polars Expression 리스트로 변환
    Context7 모범 사례: Expression을 미리 생성하여 병렬 처리
    """
    agg_exprs = []

    for col, func in agg_dict.items():
        if func == 'sum':
            agg_exprs.append(pl.col(col).sum())
        elif func == 'mean':
            agg_exprs.append(pl.col(col).mean())
        elif func == 'count':
            agg_exprs.append(pl.col(col).count())
        elif func == 'first':
            agg_exprs.append(pl.col(col).first())
        elif func == 'last':
            agg_exprs.append(pl.col(col).last())
        elif func == 'nunique':
            agg_exprs.append(pl.col(col).n_unique())
        elif func == 'max':
            agg_exprs.append(pl.col(col).max())
        elif func == 'min':
            agg_exprs.append(pl.col(col).min())
        elif func == 'std':
            agg_exprs.append(pl.col(col).std())
        elif func == 'var':
            agg_exprs.append(pl.col(col).var())
        else:
            # 기본적으로 sum 사용
            agg_exprs.append(pl.col(col).sum())

    return agg_exprs

def polars_groupby_agg(df: pl.DataFrame, group_cols: list, agg_dict: dict) -> pl.DataFrame:
    """
    pandas groupby().agg() 스타일을 효율적인 Polars로 변환
    """
    agg_exprs = create_agg_expressions(agg_dict)
    return df.group_by(group_cols, maintain_order=True).agg(agg_exprs)


def polars_pivot_table(df: pl.DataFrame, index: str, columns: str, values: str,
                      aggfunc: str = 'sum', fill_value: float = 0) -> pl.DataFrame:
    """
    pandas pivot_table을 Polars로 구현

    Args:
        df: Polars DataFrame
        index: 인덱스로 사용할 컬럼
        columns: 컬럼으로 사용할 컬럼
        values: 값으로 사용할 컬럼
        aggfunc: 집계 함수
        fill_value: 결측값 채울 값

    Returns:
        피벗된 Polars DataFrame
    """
    return df.pivot(index=index, columns=columns, values=values, aggregate_function=aggfunc)


def log_dataframe_info_polars(df: pl.DataFrame, step_name: str, store: str = "", date: str = ""):
    """Polars DataFrame 상태를 상세히 로깅"""
    prefix = f"-> {store}({date})" if store and date else ""
    logging.info(f"{prefix} === {step_name} (Polars) ===")
    logging.info(f"{prefix} 행 수: {df.height}")
    logging.info(f"{prefix} 컬럼: {df.columns}")
    logging.info(f"{prefix} 메모리 사용량: {df.estimated_size('mb'):.2f}MB")

    # 핵심 컬럼 샘플 데이터
    if '상품명' in df.columns:
        sample_names = df.select(pl.col('상품명')).filter(pl.col('상품명').is_not_null()).head(3)
        logging.info(f"{prefix} 상품명 샘플: {sample_names.to_pandas()['상품명'].tolist()}")


def validate_polars_columns(df: pl.DataFrame, required_columns: list) -> bool:
    """필수 컬럼 존재 확인"""
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"필수 컬럼 누락: {missing_columns}")
    return True


def create_vectorized_expressions(*expressions: pl.Expr) -> list[pl.Expr]:
    """
    여러 Expression을 병렬 처리용으로 묶어서 반환
    Context7 모범 사례: with_columns에서 병렬 실행을 위함
    """
    return list(expressions)

def polars_apply_function(df: pl.DataFrame, func, column_name: str, new_column: str = None) -> pl.DataFrame:
    """
    pandas apply()를 Polars로 변환 (권장하지 않음 - 벡터화된 연산 사용 권장)
    """
    logging.warning(f"polars_apply_function 사용 감지 - 성능을 위해 벡터화된 연산 사용을 권장합니다: {column_name}")
    if new_column is None:
        new_column = column_name

    return df.with_columns(
        pl.col(column_name).map_elements(func, return_dtype=pl.Utf8).alias(new_column)
    )


class PolarsPerformanceMonitor:
    """Polars 성능 모니터링 클래스"""

    def __init__(self):
        self.start_time = None
        self.start_memory = None

    def start(self):
        """성능 측정 시작"""
        import time
        import psutil
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss

    def end(self) -> dict:
        """성능 측정 종료 및 결과 반환"""
        import time
        import psutil

        if self.start_time is None:
            raise ValueError("start() 메서드를 먼저 호출해야 합니다.")

        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss

        return {
            'execution_time': end_time - self.start_time,
            'memory_used': end_memory - self.start_memory,
            'memory_used_mb': (end_memory - self.start_memory) / 1024 / 1024
        }


# 타입 변환 헬퍼 함수들
def to_numeric_polars(series: pl.Series, errors: str = 'coerce') -> pl.Series:
    """pd.to_numeric() 동등 기능"""
    if errors == 'coerce':
        return series.cast(pl.Float64, strict=False)
    else:
        return series.cast(pl.Float64)


def fillna_polars(df: pl.DataFrame, value: Any, subset: list = None) -> pl.DataFrame:
    """pandas fillna() 동등 기능"""
    if subset is None:
        return df.fill_null(value)
    else:
        return df.with_columns([
            pl.col(col).fill_null(value) for col in subset
        ])


def isna_polars(series: pl.Series) -> pl.Series:
    """pandas isna() 동등 기능"""
    return series.is_null()


def value_counts_polars(series: pl.Series) -> pl.DataFrame:
    """pandas value_counts() 동등 기능"""
    return series.value_counts()