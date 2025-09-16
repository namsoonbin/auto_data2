# -*- coding: utf-8 -*-
"""
Pandas vs Polars 성능 비교 테스트 스크립트
실제 데이터로 성능 차이를 측정하고 벤치마크 수행
"""
import os
import sys
import time
import logging
import psutil
import pandas as pd
import numpy as np
from datetime import datetime

# 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Polars 설치 확인 및 import
try:
    import polars as pl
    POLARS_AVAILABLE = True
    print(f"✅ Polars 버전: {pl.__version__}")
except ImportError:
    POLARS_AVAILABLE = False
    print("❌ Polars가 설치되지 않았습니다!")
    print("설치 명령: pip install polars")
    sys.exit(1)

from modules import config
from modules.compatibility import PerformanceComparator, set_engine
from modules.polars_utils import PolarsPerformanceMonitor


class DataGenerationHelper:
    """테스트용 데이터 생성 도우미"""

    @staticmethod
    def create_test_order_data(num_rows=10000):
        """테스트용 주문조회 데이터 생성"""
        np.random.seed(42)  # 재현 가능한 결과를 위해

        stores = ['스토어A', '스토어B', '스토어C']
        products = [f'상품{i:06d}' for i in range(1, 501)]  # 500개 상품
        options = ['', '색상:빨강', '색상:파랑', '사이즈:L', '사이즈:M', '사이즈:S', '세트:기본']
        statuses = ['정상', '취소완료', '반품요청', '반품완료']

        data = {
            '상품ID': np.random.choice(products, num_rows),
            '상품명': [f'테스트상품{i%100}' for i in range(num_rows)],
            '옵션정보': np.random.choice(options, num_rows),
            '수량': np.random.randint(1, 10, num_rows),
            '클레임상태': np.random.choice(statuses, num_rows, p=[0.8, 0.1, 0.05, 0.05]),
            '상품주문번호': [f'ORD{i:08d}' for i in range(num_rows)]
        }

        return pd.DataFrame(data)

    @staticmethod
    def create_test_margin_data(num_products=500):
        """테스트용 마진정보 데이터 생성"""
        np.random.seed(42)

        data = []
        for i in range(1, num_products + 1):
            product_id = f'상품{i:06d}'

            # 각 상품당 1-5개의 옵션
            num_options = np.random.randint(1, 6)
            options = ['', '색상:빨강', '색상:파랑', '사이즈:L', '사이즈:M', '사이즈:S', '세트:기본']
            selected_options = np.random.choice(options, min(num_options, len(options)), replace=False)

            for j, option in enumerate(selected_options):
                data.append({
                    '상품ID': product_id,
                    '상품명': f'테스트상품{i%100}',
                    '옵션정보': option,
                    '판매가': np.random.randint(1000, 50000),
                    '마진율': np.random.uniform(0.1, 0.5),
                    '대표옵션': j == 0,  # 첫 번째 옵션이 대표옵션
                    '개당 가구매 비용': np.random.randint(100, 1000)
                })

        return pd.DataFrame(data)


class PerformanceTester:
    """성능 테스트 실행 클래스"""

    def __init__(self, test_data_size=10000):
        self.test_data_size = test_data_size
        self.comparator = PerformanceComparator()
        self.results = {}

        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        print(f"🚀 성능 테스트 시작 - 테스트 데이터 크기: {test_data_size:,} 행")

    def setup_test_data(self):
        """테스트 데이터 준비"""
        print("📊 테스트 데이터 생성 중...")

        # 테스트 데이터 생성
        self.order_data_pandas = DataGenerationHelper.create_test_order_data(self.test_data_size)
        self.margin_data_pandas = DataGenerationHelper.create_test_margin_data(500)

        # Polars 버전으로 변환
        self.order_data_polars = pl.from_pandas(self.order_data_pandas)
        self.margin_data_polars = pl.from_pandas(self.margin_data_pandas)

        print(f"   ✅ 주문조회 데이터: {len(self.order_data_pandas):,} 행")
        print(f"   ✅ 마진정보 데이터: {len(self.margin_data_pandas):,} 행")

    def test_data_loading(self):
        """데이터 로딩 성능 테스트"""
        print("\n🔄 1. 데이터 로딩 성능 테스트")

        # 임시 Excel 파일 생성
        test_file = os.path.join(config.BASE_DIR, 'test_data.xlsx')
        self.order_data_pandas.to_excel(test_file, index=False)

        def pandas_load():
            return pd.read_excel(test_file)

        def polars_load():
            return pl.read_excel(test_file)

        polars_result, pandas_result = self.comparator.compare_operations(
            "Excel 파일 로딩", pandas_load, polars_load
        )

        # 임시 파일 정리
        if os.path.exists(test_file):
            os.remove(test_file)

    def test_data_filtering(self):
        """데이터 필터링 성능 테스트"""
        print("\n🔍 2. 데이터 필터링 성능 테스트")

        def pandas_filter():
            return self.order_data_pandas[
                (self.order_data_pandas['수량'] > 3) &
                (self.order_data_pandas['클레임상태'] == '정상')
            ]

        def polars_filter():
            return self.order_data_polars.filter(
                (pl.col('수량') > 3) &
                (pl.col('클레임상태') == '정상')
            )

        polars_result, pandas_result = self.comparator.compare_operations(
            "데이터 필터링", pandas_filter, polars_filter
        )

    def test_groupby_aggregation(self):
        """그룹화 및 집계 성능 테스트"""
        print("\n📊 3. 그룹화 및 집계 성능 테스트")

        def pandas_groupby():
            return self.order_data_pandas.groupby(['상품ID', '옵션정보']).agg({
                '수량': 'sum',
                '상품주문번호': 'nunique'
            }).reset_index()

        def polars_groupby():
            return self.order_data_polars.group_by(['상품ID', '옵션정보']).agg([
                pl.col('수량').sum(),
                pl.col('상품주문번호').n_unique()
            ])

        polars_result, pandas_result = self.comparator.compare_operations(
            "그룹화 및 집계", pandas_groupby, polars_groupby
        )

    def test_join_operations(self):
        """조인 연산 성능 테스트"""
        print("\n🔗 4. 조인 연산 성능 테스트")

        def pandas_join():
            return pd.merge(
                self.order_data_pandas,
                self.margin_data_pandas,
                on=['상품ID', '옵션정보'],
                how='left'
            )

        def polars_join():
            return self.order_data_polars.join(
                self.margin_data_polars,
                on=['상품ID', '옵션정보'],
                how='left'
            )

        polars_result, pandas_result = self.comparator.compare_operations(
            "조인 연산", pandas_join, polars_join
        )

    def test_complex_calculations(self):
        """복잡한 계산 성능 테스트"""
        print("\n🧮 5. 복잡한 계산 성능 테스트")

        # 먼저 조인된 데이터 준비
        joined_pandas = pd.merge(
            self.order_data_pandas,
            self.margin_data_pandas,
            on=['상품ID', '옵션정보'],
            how='left'
        ).fillna(0)

        joined_polars = self.order_data_polars.join(
            self.margin_data_polars,
            on=['상품ID', '옵션정보'],
            how='left'
        ).fill_null(0)

        def pandas_calculations():
            result = joined_pandas.copy()
            result['결제금액'] = result['수량'] * result['판매가']
            result['판매마진'] = result['결제금액'] * result['마진율']
            result['마진율_퍼센트'] = result['마진율'] * 100
            # 안전한 나누기
            result['효율성'] = np.where(
                result['수량'] > 0,
                result['판매마진'] / result['수량'],
                0
            )
            return result

        def polars_calculations():
            return joined_polars.with_columns([
                (pl.col('수량') * pl.col('판매가')).alias('결제금액'),
                (pl.col('결제금액') * pl.col('마진율')).alias('판매마진'),
                (pl.col('마진율') * 100).alias('마진율_퍼센트'),
                # 안전한 나누기
                pl.when(pl.col('수량') > 0)
                  .then(pl.col('판매마진') / pl.col('수량'))
                  .otherwise(0)
                  .alias('효율성')
            ])

        polars_result, pandas_result = self.comparator.compare_operations(
            "복잡한 계산", pandas_calculations, polars_calculations
        )

    def test_memory_usage(self):
        """메모리 사용량 비교"""
        print("\n💾 6. 메모리 사용량 비교")

        # pandas 메모리 사용량
        pandas_memory = self.order_data_pandas.memory_usage(deep=True).sum()
        pandas_memory_mb = pandas_memory / 1024 / 1024

        # polars 메모리 사용량 (추정)
        polars_memory_mb = self.order_data_polars.estimated_size('mb')

        print(f"   📊 Pandas 메모리 사용량: {pandas_memory_mb:.2f} MB")
        print(f"   📊 Polars 메모리 사용량: {polars_memory_mb:.2f} MB")
        print(f"   📈 메모리 절약률: {(pandas_memory_mb - polars_memory_mb) / pandas_memory_mb * 100:.1f}%")

        self.results['memory_comparison'] = {
            'pandas_mb': pandas_memory_mb,
            'polars_mb': polars_memory_mb,
            'savings_percent': (pandas_memory_mb - polars_memory_mb) / pandas_memory_mb * 100
        }

    def run_full_benchmark(self):
        """전체 벤치마크 실행"""
        print("🏁 전체 성능 벤치마크 실행")
        print("=" * 60)

        # 테스트 데이터 준비
        self.setup_test_data()

        # 개별 테스트 실행
        self.test_data_loading()
        self.test_data_filtering()
        self.test_groupby_aggregation()
        self.test_join_operations()
        self.test_complex_calculations()
        self.test_memory_usage()

        # 전체 결과 요약
        self.print_summary()

    def print_summary(self):
        """결과 요약 출력"""
        print("\n" + "=" * 60)
        print("🎯 최종 성능 비교 결과")
        print("=" * 60)

        summary = self.comparator.get_summary()

        if summary:
            print(f"📊 테스트된 연산 수: {summary['operations_count']}개")
            print(f"⚡ 평균 속도 향상: {summary['average_speedup']:.2f}배")
            print(f"💾 평균 메모리 절약: {summary['average_memory_reduction']:.1f}%")

            print(f"\n🏆 최고 성능 개선 연산들:")
            sorted_ops = sorted(
                summary['details'].items(),
                key=lambda x: x[1]['speedup'],
                reverse=True
            )

            for op_name, result in sorted_ops[:3]:
                print(f"   • {op_name}: {result['speedup']:.2f}배 빠름, "
                      f"{result['memory_reduction']:.1f}% 메모리 절약")

        # 권장사항
        print(f"\n💡 권장사항:")
        if summary and summary['average_speedup'] > 2:
            print("   ✅ Polars 마이그레이션 강력 권장 - 상당한 성능 향상 예상")
        elif summary and summary['average_speedup'] > 1.5:
            print("   ⚡ Polars 마이그레이션 권장 - 중간 수준 성능 향상")
        else:
            print("   📊 현재 데이터 크기에서는 성능 차이가 제한적")

        print(f"\n📁 상세 결과는 로그 파일에서 확인 가능합니다.")


def main():
    """메인 실행 함수"""
    print("🔥 Pandas vs Polars 성능 비교 테스트")
    print("=" * 60)

    # 시스템 정보 출력
    print(f"🖥️  시스템 정보:")
    print(f"   • Python 버전: {sys.version.split()[0]}")
    print(f"   • Pandas 버전: {pd.__version__}")
    print(f"   • Polars 버전: {pl.__version__}")
    print(f"   • 사용 가능한 메모리: {psutil.virtual_memory().total / (1024**3):.1f} GB")
    print(f"   • CPU 코어 수: {psutil.cpu_count()}")

    # 테스트 크기 선택
    data_sizes = [1000, 5000, 10000, 50000]
    print(f"\n📏 테스트할 데이터 크기를 선택하세요:")
    for i, size in enumerate(data_sizes, 1):
        print(f"   {i}. {size:,} 행")
    print(f"   5. 모든 크기로 테스트")

    try:
        choice = input("\n선택 (1-5): ").strip()

        if choice == '5':
            # 모든 크기로 테스트
            for size in data_sizes:
                print(f"\n🔄 {size:,} 행 데이터로 테스트 중...")
                tester = PerformanceTester(size)
                tester.run_full_benchmark()
                print(f"\n{'='*60}")
        else:
            size_index = int(choice) - 1
            if 0 <= size_index < len(data_sizes):
                selected_size = data_sizes[size_index]
                tester = PerformanceTester(selected_size)
                tester.run_full_benchmark()
            else:
                print("❌ 잘못된 선택입니다.")
                return

    except (ValueError, KeyboardInterrupt):
        print("❌ 테스트가 중단되었습니다.")
        return

    print(f"\n✅ 성능 테스트 완료!")
    print(f"💡 Polars 마이그레이션을 진행하려면 compatibility.py에서 USE_POLARS = True로 설정하세요.")


if __name__ == "__main__":
    main()