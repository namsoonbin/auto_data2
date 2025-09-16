# -*- coding: utf-8 -*-
"""
Pandas와 Polars 간 호환성 레이어
기존 코드의 인터페이스를 유지하면서 점진적으로 Polars로 전환
"""
import polars as pl
import pandas as pd
import logging
from typing import Union, Callable, Any
from functools import wraps


# 전역 설정
USE_POLARS = True  # True: Polars 사용, False: Pandas 사용


def polars_with_pandas_fallback(polars_func: Callable, pandas_func: Callable, return_pandas: bool = False):
    """
    Polars 함수와 pandas 폴백을 명확히 분리한 호환성 래퍼

    Args:
        polars_func: Polars로 처리하는 함수
        pandas_func: pandas로 폴백하는 함수
        return_pandas: True이면 결과를 pandas DataFrame으로 반환
    """
    @wraps(polars_func)
    def wrapper(*args, **kwargs):
        try:
            if USE_POLARS:
                # Polars로 처리 시도
                result = polars_func(*args, **kwargs)

                if return_pandas and isinstance(result, pl.DataFrame):
                    return result.to_pandas()
                return result
            else:
                # pandas 함수 직접 호출
                logging.info(f"pandas 모드로 실행: {polars_func.__name__}")
                return pandas_func(*args, **kwargs)

        except Exception as e:
            # 오류 시 pandas로 폴백
            logging.warning(f"Polars 처리 실패, pandas로 폴백: {polars_func.__name__}, 오류: {e}")
            try:
                return pandas_func(*args, **kwargs)
            except Exception as fallback_error:
                logging.error(f"pandas 폴백도 실패: {fallback_error}")
                raise fallback_error

    return wrapper


class DataFrameEngine:
    """DataFrame 엔진을 추상화하는 클래스 - Context7 모범 사례 적용"""

    @staticmethod
    def read_excel(file_path: str, **kwargs) -> Union[pd.DataFrame, pl.DataFrame]:
        """Excel 파일을 읽는 통합 인터페이스 - 타입 안전성 강화"""
        def _polars_read():
            # Context7 모범 사례: 타입 안전성 확보
            try:
                return pl.read_excel(file_path, **kwargs)
            except Exception as e:
                logging.error(f"Polars Excel 읽기 실패: {e}")
                raise e

        def _pandas_read():
            try:
                return pd.read_excel(file_path, engine='openpyxl', **kwargs)
            except Exception as e:
                logging.error(f"Pandas Excel 읽기 실패: {e}")
                raise e

        # 함수를 직접 실행하도록 수정
        wrapper_func = polars_with_pandas_fallback(_polars_read, _pandas_read)
        return wrapper_func()

    @staticmethod
    def from_pandas(df: pd.DataFrame) -> Union[pd.DataFrame, pl.DataFrame]:
        """pandas DataFrame을 현재 엔진에 맞게 변환"""
        if USE_POLARS:
            return pl.from_pandas(df)
        else:
            return df

    @staticmethod
    def to_pandas(df: Union[pd.DataFrame, pl.DataFrame]) -> pd.DataFrame:
        """DataFrame을 pandas로 변환"""
        if isinstance(df, pl.DataFrame):
            return df.to_pandas()
        else:
            return df

    @staticmethod
    def groupby_agg(df: Union[pd.DataFrame, pl.DataFrame],
                   group_cols: list, agg_dict: dict) -> Union[pd.DataFrame, pl.DataFrame]:
        """그룹화 및 집계 통합 인터페이스 - Context7 Expression 패턴 적용"""
        if isinstance(df, pl.DataFrame):
            # Polars 방식 - 벡터화된 Expression 사용
            from .polars_utils import create_agg_expressions
            agg_exprs = create_agg_expressions(agg_dict)
            return df.group_by(group_cols, maintain_order=True).agg(agg_exprs)
        else:
            # pandas 방식
            return df.groupby(group_cols, as_index=False).agg(agg_dict)

    @staticmethod
    def merge_join(left: Union[pd.DataFrame, pl.DataFrame],
                  right: Union[pd.DataFrame, pl.DataFrame],
                  on: list, how: str = 'left', validate: str = None) -> Union[pd.DataFrame, pl.DataFrame]:
        """병합/조인 통합 인터페이스 - Context7 모범 사례 적용"""
        if isinstance(left, pl.DataFrame) and isinstance(right, pl.DataFrame):
            # Polars 방식 - validate는 pandas 전용이므로 제외
            return left.join(right, on=on, how=how)
        else:
            # pandas 방식 (필요시 변환)
            left_pd = DataFrameEngine.to_pandas(left)
            right_pd = DataFrameEngine.to_pandas(right)
            merge_kwargs = {'on': on, 'how': how}
            if validate:
                merge_kwargs['validate'] = validate
            return pd.merge(left_pd, right_pd, **merge_kwargs)


class PolarsPerformanceTracker:
    """Polars 성능 추적 클래스 - Context7 모범 사례 적용"""

    def __init__(self):
        self.results = {}
        self.polars_enabled = USE_POLARS

    def compare_operations(self, operation_name: str,
                          pandas_func: Callable, polars_func: Callable,
                          *args, **kwargs):
        """두 엔진의 성능을 비교"""
        import time
        import psutil

        # Pandas 성능 측정
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss

        pandas_result = pandas_func(*args, **kwargs)

        pandas_time = time.time() - start_time
        pandas_memory = psutil.Process().memory_info().rss - start_memory

        # Polars 성능 측정
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss

        polars_result = polars_func(*args, **kwargs)

        polars_time = time.time() - start_time
        polars_memory = psutil.Process().memory_info().rss - start_memory

        # 결과 저장
        self.results[operation_name] = {
            'pandas': {
                'time': pandas_time,
                'memory': pandas_memory,
                'memory_mb': pandas_memory / 1024 / 1024
            },
            'polars': {
                'time': polars_time,
                'memory': polars_memory,
                'memory_mb': polars_memory / 1024 / 1024
            },
            'speedup': pandas_time / polars_time if polars_time > 0 else float('inf'),
            'memory_reduction': (pandas_memory - polars_memory) / pandas_memory * 100 if pandas_memory > 0 else 0
        }

        # 로깅
        logging.info(f"성능 비교 - {operation_name}:")
        logging.info(f"  Pandas: {pandas_time:.3f}초, {pandas_memory/1024/1024:.1f}MB")
        logging.info(f"  Polars: {polars_time:.3f}초, {polars_memory/1024/1024:.1f}MB")
        logging.info(f"  속도 향상: {self.results[operation_name]['speedup']:.1f}배")
        logging.info(f"  메모리 절약: {self.results[operation_name]['memory_reduction']:.1f}%")

        return polars_result, pandas_result

    def get_summary(self) -> dict:
        """전체 성능 비교 요약"""
        if not self.results:
            return {}

        total_speedup = sum(result['speedup'] for result in self.results.values()) / len(self.results)
        total_memory_reduction = sum(result['memory_reduction'] for result in self.results.values()) / len(self.results)

        return {
            'operations_count': len(self.results),
            'average_speedup': total_speedup,
            'average_memory_reduction': total_memory_reduction,
            'details': self.results
        }


def set_engine(use_polars: bool, validate_dependencies: bool = True):
    """전역 엔진 설정 - Context7 모범 사례 적용"""
    global USE_POLARS

    if use_polars and validate_dependencies:
        try:
            # Polars 의존성 확인
            import polars as pl
            logging.info(f"Polars {pl.__version__} 사용 가능")
        except ImportError:
            logging.error("Polars가 설치되지 않았습니다. pandas로 폴백합니다.")
            use_polars = False

    USE_POLARS = use_polars
    engine_name = "Polars" if use_polars else "Pandas"
    logging.info(f"DataFrame 엔진을 {engine_name}로 설정했습니다.")


def get_current_engine() -> str:
    """현재 사용 중인 엔진 반환"""
    return "Polars" if USE_POLARS else "Pandas"


class BackwardCompatibility:
    """기존 pandas 코드와의 하위 호환성을 보장하는 클래스"""

    @staticmethod
    def ensure_pandas_output(func: Callable) -> Callable:
        """함수 출력이 항상 pandas DataFrame이 되도록 보장"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return DataFrameEngine.to_pandas(result)
        return wrapper

    @staticmethod
    def pandas_interface_wrapper(polars_func: Callable) -> Callable:
        """Polars 함수를 pandas 인터페이스로 감싸기"""
        @wraps(polars_func)
        def wrapper(*args, **kwargs):
            # 입력을 Polars로 변환
            converted_args = []
            for arg in args:
                if isinstance(arg, pd.DataFrame):
                    converted_args.append(pl.from_pandas(arg))
                else:
                    converted_args.append(arg)

            # Polars 함수 실행
            result = polars_func(*converted_args, **kwargs)

            # 결과를 pandas로 변환하여 반환
            if isinstance(result, pl.DataFrame):
                return result.to_pandas()
            return result

        return wrapper


# 편의 함수들
def log_engine_status():
    """현재 엔진 상태 로깅"""
    engine = get_current_engine()
    logging.info(f"현재 DataFrame 엔진: {engine}")

    if USE_POLARS:
        try:
            import polars as pl
            logging.info(f"Polars 버전: {pl.__version__}")
        except ImportError:
            logging.error("Polars가 설치되지 않았습니다!")

    try:
        import pandas as pd
        logging.info(f"Pandas 버전: {pd.__version__}")
    except ImportError:
        logging.error("Pandas가 설치되지 않았습니다!")


def benchmark_simple_operations():
    """간단한 연산들의 성능 벤치마크 - Context7 Expression 패턴 적용"""
    tracker = PolarsPerformanceTracker()

    # 테스트 데이터 생성
    test_data = pd.DataFrame({
        'A': range(10000),
        'B': range(10000, 20000),
        'C': ['test'] * 10000
    })

    test_data_polars = pl.from_pandas(test_data)

    # 그룹화 테스트
    def pandas_groupby():
        return test_data.groupby('C').agg({'A': 'sum', 'B': 'mean'})

    def polars_groupby():
        return test_data_polars.group_by('C').agg([
            pl.col('A').sum(),
            pl.col('B').mean()
        ])

    comparator.compare_operations('groupby', pandas_groupby, polars_groupby)

    return comparator.get_summary()