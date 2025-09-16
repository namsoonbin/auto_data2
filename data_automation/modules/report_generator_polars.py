# -*- coding: utf-8 -*-
"""
Polars 기반 리포트 생성 모듈
기존 report_generator.py의 Polars 최적화 버전
성능 향상을 위해 pandas 대신 polars 사용
"""
import polars as pl
import pandas as pd  # 하위 호환성을 위해 유지
import numpy as np
import os
import glob
import re
import logging
import io
import json
from datetime import datetime, timedelta
from . import config
from .polars_utils import (
    normalize_product_id_polars,
    normalize_option_info_polars,
    read_protected_excel_polars,
    safe_divide_polars,
    polars_groupby_agg,
    log_dataframe_info_polars,
    PolarsPerformanceMonitor
)
from .compatibility import DataFrameEngine, USE_POLARS


def create_purchase_dataframe_for_date(target_date: str) -> pl.DataFrame:
    """특정 날짜의 가구매 설정을 Polars DataFrame으로 변환 - Context7 타입 안전성 강화"""
    # Context7 모범 사례: 명확한 스키마 정의
    PURCHASE_SCHEMA = {
        '상품ID': pl.Utf8,
        '옵션정보': pl.Utf8,
        '가구매_개수': pl.Int32
    }

    try:
        purchase_file = os.path.join(config.BASE_DIR, '가구매설정.json')
        if not os.path.exists(purchase_file):
            return pl.DataFrame(schema=PURCHASE_SCHEMA)

        # 파일 크기 검증 (Context7 모범 사례)
        if os.path.getsize(purchase_file) == 0:
            logging.warning(f"빈 가구매 설정 파일: {purchase_file}")
            return pl.DataFrame(schema=PURCHASE_SCHEMA)

        with open(purchase_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 데이터 구조 검증
        if not isinstance(data, dict) or 'purchases' not in data:
            logging.warning("가구매 설정 파일 구조가 올바르지 않습니다")
            return pl.DataFrame(schema=PURCHASE_SCHEMA)

        purchase_records = []
        for entry in data.get('purchases', []):
            try:
                # 필수 필드 검증
                if not all(key in entry for key in ['start_date', 'product_id', 'purchase_count']):
                    continue

                if entry.get('start_date') == target_date:
                    # 타입 안전성 확보
                    product_id = normalize_product_id_polars(entry['product_id'])
                    option_info = str(entry.get('option_info', ''))
                    purchase_count = int(entry['purchase_count'])

                    if purchase_count < 0:  # 음수 가구매 방지
                        continue

                    purchase_records.append({
                        '상품ID': product_id,
                        '옵션정보': option_info,
                        '가구매_개수': purchase_count
                    })
            except (KeyError, ValueError, TypeError) as e:
                logging.debug(f"가구매 엔트리 파싱 실패: {entry}, 오류: {e}")
                continue

        # Context7 모범 사례: 스키마 강제 적용
        if purchase_records:
            try:
                return pl.DataFrame(purchase_records, schema=PURCHASE_SCHEMA)
            except Exception as schema_error:
                logging.error(f"가구매 DataFrame 스키마 적용 실패: {schema_error}")
                return pl.DataFrame(schema=PURCHASE_SCHEMA)
        else:
            return pl.DataFrame(schema=PURCHASE_SCHEMA)

    except json.JSONDecodeError as e:
        logging.error(f"가구매 설정 JSON 파싱 실패: {e}")
        return pl.DataFrame(schema=PURCHASE_SCHEMA)
    except Exception as e:
        logging.warning(f"가구매 DataFrame 생성 실패: {e}")
        return pl.DataFrame(schema=PURCHASE_SCHEMA)


def create_reward_dataframe_for_date(target_date: str) -> pl.DataFrame:
    """특정 날짜의 리워드 설정을 Polars DataFrame으로 변환 - Context7 타입 안전성 강화"""
    # Context7 모범 사례: 명확한 스키마 정의
    REWARD_SCHEMA = {
        '상품ID': pl.Utf8,
        '옵션정보': pl.Utf8,
        '리워드_금액': pl.Int32
    }

    try:
        reward_file = os.path.join(config.BASE_DIR, '리워드설정.json')
        if not os.path.exists(reward_file):
            return pl.DataFrame(schema=REWARD_SCHEMA)

        # 파일 크기 검증
        if os.path.getsize(reward_file) == 0:
            logging.warning(f"빈 리워드 설정 파일: {reward_file}")
            return pl.DataFrame(schema=REWARD_SCHEMA)

        with open(reward_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 데이터 구조 검증
        if not isinstance(data, dict) or 'rewards' not in data:
            logging.warning("리워드 설정 파일 구조가 올바르지 않습니다")
            return pl.DataFrame(schema=REWARD_SCHEMA)

        # 목표 날짜 파싱 (타입 안전성)
        try:
            target_date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
        except ValueError as e:
            logging.error(f"잘못된 날짜 형식: {target_date}, 오류: {e}")
            return pl.DataFrame(schema=REWARD_SCHEMA)

        reward_records = []
        for entry in data.get('rewards', []):
            try:
                # 필수 필드 검증
                required_fields = ['start_date', 'end_date', 'product_id', 'reward']
                if not all(key in entry for key in required_fields):
                    continue

                # 날짜 범위 확인 (타입 안전성)
                start_date = datetime.strptime(entry['start_date'], '%Y-%m-%d').date()
                end_date = datetime.strptime(entry['end_date'], '%Y-%m-%d').date()

                if start_date <= target_date_obj <= end_date:
                    # 타입 안전성 확보
                    product_id = normalize_product_id_polars(entry['product_id'])
                    option_info = str(entry.get('option_info', ''))
                    reward_amount = int(entry['reward'])

                    if reward_amount < 0:  # 음수 리워드 방지
                        continue

                    reward_records.append({
                        '상품ID': product_id,
                        '옵션정보': option_info,
                        '리워드_금액': reward_amount
                    })
            except (KeyError, ValueError, TypeError) as e:
                logging.debug(f"리워드 엔트리 파싱 실패: {entry}, 오류: {e}")
                continue

        # Context7 모범 사례: 스키마 강제 적용
        if reward_records:
            try:
                return pl.DataFrame(reward_records, schema=REWARD_SCHEMA)
            except Exception as schema_error:
                logging.error(f"리워드 DataFrame 스키마 적용 실패: {schema_error}")
                return pl.DataFrame(schema=REWARD_SCHEMA)
        else:
            return pl.DataFrame(schema=REWARD_SCHEMA)

    except json.JSONDecodeError as e:
        logging.error(f"리워드 설정 JSON 파싱 실패: {e}")
        return pl.DataFrame(schema=REWARD_SCHEMA)
    except Exception as e:
        logging.warning(f"리워드 DataFrame 생성 실패: {e}")
        return pl.DataFrame(schema=REWARD_SCHEMA)


def normalize_product_id(value):
    """상품ID를 정규화 - Polars 최적화 버전으로 리다이렉트"""
    return normalize_product_id_polars(value)


# 전역 리워드 캐시 (기존과 동일한 구조 유지)
_reward_cache = None
_reward_cache_timestamp = None


def _migrate_legacy_rewards_polars(data):
    """기존 리워드 설정을 옵션별 설정으로 자동 마이그레이션 - Polars 버전"""
    try:
        # 마진정보 파일 로드 (Polars 사용)
        margin_file = config.MARGIN_FILE
        if not os.path.exists(margin_file):
            return data

        # Polars로 Excel 읽기
        margin_df = pl.read_excel(margin_file)

        # 컬럼명 정규화
        if '상품번호' in margin_df.columns:
            margin_df = margin_df.rename({'상품번호': '상품ID'})

        # 상품ID 정규화 (Polars 방식)
        margin_df = margin_df.with_columns([
            pl.col('상품ID').map_elements(normalize_product_id_polars).alias('상품ID')
        ])

        # 빈 상품ID 제거
        margin_df = margin_df.filter(pl.col('상품ID') != '')

        # 대표옵션을 boolean으로 변환 (Polars 방식)
        if '대표옵션' in margin_df.columns:
            margin_df = margin_df.with_columns([
                pl.col('대표옵션').cast(pl.Utf8).str.to_uppercase().is_in(['O', 'Y', 'TRUE']).alias('대표옵션')
            ])

        migrated_rewards = []
        migration_count = 0

        for reward_entry in data.get('rewards', []):
            # 이미 option_info가 있으면 그대로 유지
            if 'option_info' in reward_entry:
                migrated_rewards.append(reward_entry)
                continue

            # 기존 형식이면 마이그레이션 수행
            product_id = normalize_product_id_polars(reward_entry.get('product_id', ''))
            if not product_id:
                continue

            # 해당 상품의 모든 대표옵션 찾기 (Polars 방식)
            rep_options = margin_df.filter(
                (pl.col('상품ID') == product_id) &
                (pl.col('대표옵션') == True)
            )

            if rep_options.height == 0:
                # 대표옵션이 없으면 빈 옵션정보로 저장
                new_entry = reward_entry.copy()
                new_entry['option_info'] = ''
                migrated_rewards.append(new_entry)
                migration_count += 1
            else:
                # 각 대표옵션별로 개별 엔트리 생성
                for row in rep_options.iter_rows(named=True):
                    new_entry = reward_entry.copy()
                    option_info = row.get('옵션정보', '')
                    if option_info is None:
                        option_info = ''
                    new_entry['option_info'] = str(option_info)
                    migrated_rewards.append(new_entry)
                    migration_count += 1

        if migration_count > 0:
            logging.info(f"리워드 설정 마이그레이션 (Polars): {migration_count}개 엔트리 생성")
            # 마이그레이션된 데이터를 파일에 저장
            migrated_data = {'rewards': migrated_rewards}
            reward_file = os.path.join(config.BASE_DIR, '리워드설정.json')
            with open(reward_file, 'w', encoding='utf-8') as f:
                json.dump(migrated_data, f, ensure_ascii=False, indent=2)
            return migrated_data

        return data

    except Exception as e:
        logging.warning(f"리워드 마이그레이션 실패 (Polars): {e}")
        return data


def _load_reward_cache():
    """리워드 설정을 딕셔너리로 로드하여 캐시 (Polars 최적화)"""
    global _reward_cache, _reward_cache_timestamp

    try:
        reward_file = os.path.join(config.BASE_DIR, '리워드설정.json')

        # 파일 존재 확인
        if not os.path.exists(reward_file):
            _reward_cache = {}
            return

        # 파일 수정 시간 확인 (캐시 무효화용)
        file_timestamp = os.path.getmtime(reward_file)
        if _reward_cache is not None and _reward_cache_timestamp == file_timestamp:
            return  # 캐시 유효함

        # 파일 크기 확인
        if os.path.getsize(reward_file) == 0:
            _reward_cache = {}
            return

        # JSON 파일 읽기
        with open(reward_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 데이터 구조 검증
        if not isinstance(data, dict) or 'rewards' not in data:
            _reward_cache = {}
            return

        # Polars 기반 자동 마이그레이션 수행
        data = _migrate_legacy_rewards_polars(data)

        # 마이그레이션 후 파일 타임스탬프 다시 확인
        new_file_timestamp = os.path.getmtime(reward_file)

        rewards_list = data.get('rewards', [])
        if not isinstance(rewards_list, list):
            _reward_cache = {}
            return

        # 효율적인 조회를 위한 딕셔너리 생성 (옵션 포함)
        reward_map = {}
        for reward_entry in rewards_list:
            try:
                # 필수 키 존재 확인
                if not all(k in reward_entry for k in ['start_date', 'end_date', 'product_id', 'reward']):
                    continue

                start_date = datetime.strptime(reward_entry['start_date'], '%Y-%m-%d').date()
                end_date = datetime.strptime(reward_entry['end_date'], '%Y-%m-%d').date()
                product_id = normalize_product_id_polars(reward_entry['product_id'])
                option_info = reward_entry.get('option_info', '')
                reward_value = reward_entry['reward']

                # 리워드 값 검증
                if not isinstance(reward_value, (int, float)) or reward_value < 0:
                    continue

                # 날짜 범위별로 딕셔너리에 저장 (성능 최적화)
                current_date = start_date
                while current_date <= end_date:
                    # 3-tuple 키: (date, product_id, option_info)
                    key = (current_date.strftime('%Y-%m-%d'), product_id, option_info)
                    reward_map[key] = int(reward_value)
                    current_date += timedelta(days=1)

            except (ValueError, KeyError, TypeError) as e:
                # 개별 엔트리 파싱 실패는 로그만 남기고 계속 진행
                logging.debug(f"리워드 엔트리 파싱 실패: {reward_entry}, 오류: {e}")
                continue

        _reward_cache = reward_map
        _reward_cache_timestamp = new_file_timestamp

        logging.info(f"리워드 캐시 로드 완료 (Polars): {len(reward_map)}개 엔트리")

    except FileNotFoundError:
        _reward_cache = {}
    except json.JSONDecodeError as e:
        logging.warning(f"리워드 설정 JSON 파일 형식 오류 (Polars): {e}")
        _reward_cache = {}
    except Exception as e:
        logging.warning(f"리워드 캐시 로드 중 예상치 못한 오류 (Polars): {e}")
        _reward_cache = {}


def get_reward_for_date_and_product(product_id, date_str, option_info=''):
    """특정 날짜와 상품의 리워드 금액 조회 (옵션별) - Polars 최적화"""
    # 캐시가 없으면 로드
    if _reward_cache is None:
        _load_reward_cache()

    # 상품ID 정규화
    normalized_product_id = normalize_product_id_polars(product_id)

    # 날짜 문자열 검증
    try:
        target_date = date_str
        if not isinstance(target_date, str):
            target_date = str(target_date)
    except:
        return 0

    # 옵션정보 정규화
    normalized_option_info = normalize_option_info_polars(option_info)

    # O(1) 딕셔너리 조회
    key = (target_date, normalized_product_id, normalized_option_info)
    return _reward_cache.get(key, 0)


def get_purchase_count_for_date_and_product(product_id, date_str, option_info=''):
    """특정 날짜와 상품의 가구매 개수 조회 (옵션별) - Polars 최적화"""
    try:
        purchase_file = os.path.join(config.BASE_DIR, '가구매설정.json')

        if not os.path.exists(purchase_file):
            return 0

        # 상품ID와 옵션정보 정규화
        normalized_product_id = normalize_product_id_polars(product_id)
        normalized_option_info = normalize_option_info_polars(option_info)

        with open(purchase_file, 'r', encoding='utf-8') as f:
            purchase_data = json.load(f)

        # 해당 날짜의 설정 찾기
        for purchase_entry in purchase_data.get('purchases', []):
            try:
                if (purchase_entry.get('start_date') == date_str and
                    normalize_product_id_polars(purchase_entry.get('product_id', '')) == normalized_product_id and
                    normalize_option_info_polars(purchase_entry.get('option_info', '')) == normalized_option_info):

                    purchase_count = purchase_entry['purchase_count']
                    # 가구매 개수가 숫자인지 확인
                    if isinstance(purchase_count, (int, float)) and purchase_count >= 0:
                        return int(purchase_count)
            except (ValueError, KeyError, TypeError):
                continue

        return 0  # 설정이 없으면 0

    except FileNotFoundError:
        return 0
    except json.JSONDecodeError as e:
        logging.warning(f"가구매 설정 JSON 파일 형식 오류 (Polars): {e}")
        return 0
    except Exception as e:
        logging.warning(f"가구매 개수 조회 중 예상치 못한 오류 (Polars): {e}")
        return 0


def read_protected_excel(file_path, password=None, **kwargs):
    """암호로 보호된 Excel 파일을 읽는 함수 - Polars 버전"""
    return read_protected_excel_polars(file_path, password, **kwargs)


def load_and_validate_margin_data_polars():
    """마진정보 파일을 Polars로 로드하고 검증"""
    try:
        # Polars로 Excel 읽기
        margin_df = pl.read_excel(config.MARGIN_FILE)
        logging.info(f"'{os.path.basename(config.MARGIN_FILE)}' 파일을 성공적으로 불러왔습니다 (Polars).")

        # 필수 컬럼 존재 확인
        required_columns = ['상품번호', '상품명', '판매가', '마진율']
        missing_columns = [col for col in required_columns if col not in margin_df.columns]
        if missing_columns:
            raise ValueError(f"마진정보 파일에 필수 컬럼이 없습니다: {missing_columns}")

        # 컬럼명 정규화
        if '상품번호' in margin_df.columns:
            margin_df = margin_df.rename({'상품번호': '상품ID'})

        # 상품ID 데이터 타입 정규화 (Polars 방식)
        margin_df = margin_df.with_columns([
            pl.col('상품ID').map_elements(normalize_product_id_polars).alias('상품ID')
        ])

        # 빈 상품ID 제거
        original_count = margin_df.height
        margin_df = margin_df.filter(pl.col('상품ID') != '')
        filtered_count = margin_df.height

        if original_count != filtered_count:
            logging.warning(f"마진정보에 빈 상품ID가 있습니다. {original_count - filtered_count}개 행 제거됨.")

        # 데이터 타입 검증 및 변환 (Polars 방식)
        margin_df = margin_df.with_columns([
            pl.col('판매가').cast(pl.Float64, strict=False),
            pl.col('마진율').cast(pl.Float64, strict=False)
        ])

        # 대표옵션 정보 처리
        if '대표옵션' in margin_df.columns:
            margin_df = margin_df.with_columns([
                pl.col('대표옵션').cast(pl.Utf8).str.to_uppercase().is_in(['O', 'Y', 'TRUE']).alias('대표옵션')
            ])

            # 대표옵션 판매가 정보 생성 (pandas 호환성을 위해)
            rep_options = margin_df.filter(pl.col('대표옵션') == True)
            rep_price_map = dict(zip(
                rep_options.select(pl.col('상품ID')).to_series().to_list(),
                rep_options.select(pl.col('판매가')).to_series().to_list()
            ))
            logging.info("대표옵션 판매가 정보를 생성했습니다 (Polars).")
        else:
            logging.warning(f"경고: '{os.path.basename(config.MARGIN_FILE)}'에 '대표옵션' 컬럼이 없습니다.")
            margin_df = margin_df.with_columns([pl.lit(False).alias('대표옵션')])
            rep_price_map = {}

        # 옵션정보 정규화
        if '옵션정보' not in margin_df.columns:
            margin_df = margin_df.with_columns([pl.lit('').alias('옵션정보')])
        else:
            margin_df = margin_df.with_columns([
                pl.col('옵션정보').map_elements(normalize_option_info_polars).alias('옵션정보')
            ])

        return margin_df, rep_price_map

    except FileNotFoundError:
        logging.error(f"마진정보 파일을 찾을 수 없습니다: {config.MARGIN_FILE}")
        raise
    except PermissionError:
        logging.error(f"마진정보 파일에 접근할 수 없습니다: {config.MARGIN_FILE}")
        raise
    except ValueError as e:
        logging.error(f"마진정보 파일 데이터 검증 실패: {e}")
        raise
    except Exception as e:
        logging.error(f"마진정보 파일 읽기 중 예상치 못한 오류: {e}")
        raise


def process_order_file_polars(order_file, store, date, margin_df):
    """개별 주문조회 파일을 Polars로 처리"""
    monitor = PolarsPerformanceMonitor()
    monitor.start()

    try:
        # 주문조회 파일 읽기 (암호 보호될 수 있음)
        order_path = os.path.join(config.get_processing_dir(), order_file)
        order_df = read_protected_excel_polars(order_path, password=config.ORDER_FILE_PASSWORD)

        # 파일이 비어있는지 확인
        if order_df.height == 0:
            logging.error(f"-> {store}({date}) 주문조회 파일이 비어있습니다: {order_file}")
            return None

        log_dataframe_info_polars(order_df, "주문조회 파일 로드", store, date)

        # 필수 컬럼 확인 및 추가
        if '상품ID' not in order_df.columns:
            possible_id_cols = ['상품번호', '상품코드', 'ProductID']
            id_col = None
            for col in possible_id_cols:
                if col in order_df.columns:
                    id_col = col
                    break

            if id_col:
                logging.info(f"-> {store}({date}) '{id_col}' 컬럼을 상품ID로 사용합니다.")
                order_df = order_df.rename({id_col: '상품ID'})
            else:
                logging.error(f"-> {store}({date}) 상품ID 컬럼을 찾을 수 없습니다.")
                return None

        # 데이터 정규화 및 컬럼 추가 (Context7 병렬 Expression 패턴)
        normalization_exprs = [
            # 상품ID 정규화 - 벡터화된 Expression 사용
            pl.col('상품ID').cast(pl.Utf8).str.strip_chars()
              .str.replace_all(r"\.0+$", "", literal=False)
              .str.replace_all(r"^\\.+|\\.+$", "", literal=False)
              .fill_null("").alias('상품ID')
        ]

        # 옵션정보 처리 - 조건부 Expression 추가
        if '옵션정보' not in order_df.columns:
            normalization_exprs.append(pl.lit('').alias('옵션정보'))
        else:
            normalization_exprs.append(
                pl.col('옵션정보').cast(pl.Utf8).str.strip_chars().fill_null("")
                  .str.replace_all("^단일$", "", literal=True)
                  .str.replace_all("^기본옵션$", "", literal=True)
                  .str.replace_all("^선택안함$", "", literal=True)
                  .str.replace_all("^null$", "", literal=True)
                  .str.replace_all("^none$", "", literal=True)
                  .str.replace_all("^없음$", "", literal=True)
                  .str.replace_all("^nan$", "", literal=True)
                  .alias('옵션정보')
            )

        # 모든 정규화를 한 번에 병렬 실행 (Context7 모범 사례)
        order_df = order_df.with_columns(normalization_exprs)

        # 수량 컬럼 확인 및 설정
        if '수량' not in order_df.columns:
            possible_quantity_cols = ['결제수량', '주문수량', '상품수량', '결제상품수량']
            quantity_col = None
            for col in possible_quantity_cols:
                if col in order_df.columns:
                    quantity_col = col
                    break

            if quantity_col:
                logging.info(f"-> {store}({date}) '{quantity_col}' 컬럼을 수량으로 사용합니다.")
                order_df = order_df.rename({quantity_col: '수량'})
            else:
                logging.warning(f"-> {store}({date}) 수량 컬럼을 찾을 수 없습니다. 기본값 1 사용")
                order_df = order_df.with_columns([pl.lit(1).alias('수량')])

        # 컬럼 처리 및 계산을 병렬로 실행 (Context7 모범 사례)
        column_processing_exprs = [
            # 클레임상태 처리
            pl.col('클레임상태').fill_null('정상').alias('클레임상태') if '클레임상태' in order_df.columns
            else pl.lit('정상').alias('클레임상태'),

            # 수량을 숫자형으로 변환
            pl.col('수량').cast(pl.Float64, strict=False).fill_null(1).alias('수량'),

            # 환불수량 계산 (한 번에 처리)
            pl.when(pl.col('클레임상태').is_in(config.CANCEL_OR_REFUND_STATUSES))
              .then(pl.col('수량'))
              .otherwise(0)
              .alias('환불수량')
        ]

        # 클레임상태가 없는 경우 기본값 처리
        if '클레임상태' not in order_df.columns:
            logging.warning(f"-> {store}({date}) 클레임상태 컬럼이 없습니다. 기본값 '정상' 사용")
            column_processing_exprs[0] = pl.lit('정상').alias('클레임상태')

        order_df = order_df.with_columns(column_processing_exprs)

        # 클레임상태 분포 확인
        status_counts = order_df.select(pl.col('클레임상태').value_counts()).to_pandas()
        logging.info(f"-> {store}({date}) 클레임상태 분포: {status_counts}")

        # 환불수량 계산 결과 (이미 위에서 계산됨)
        total_refund_quantity = order_df.select(pl.col('환불수량').sum()).item()
        refund_rows = order_df.filter(pl.col('환불수량') > 0).height
        logging.info(f"-> {store}({date}) 총 환불수량: {total_refund_quantity}, 환불 행 수: {refund_rows}")

        # 성능 측정 결과
        perf_result = monitor.end()
        logging.info(f"-> {store}({date}) 주문조회 파일 처리 완료: "
                    f"{perf_result['execution_time']:.2f}초, {perf_result['memory_used_mb']:.1f}MB")

        return order_df

    except Exception as e:
        logging.error(f"-> {store}({date}) 주문조회 파일 처리 중 오류: {e}")
        return None


def aggregate_options_polars(order_df, store, date):
    """옵션별 데이터 집계 - Polars 최적화"""
    logging.info(f"-> {store}({date}) 옵션별 데이터 집계 시작 (Polars)...")

    # 상품명 컬럼 확인
    group_cols = ['상품ID', '옵션정보']
    if '상품명' in order_df.columns:
        group_cols = ['상품ID', '상품명', '옵션정보']
    else:
        logging.warning(f"-> {store}({date}) 주문조회 파일에 상품명 컬럼이 없습니다.")

    # 중복 데이터 검증
    duplicates = order_df.select(
        pl.struct(group_cols).is_duplicated().sum().alias('duplicates')
    ).item()

    if duplicates > 0:
        logging.warning(f"-> {store}({date}) 주문조회 데이터에 중복된 상품ID-옵션정보 조합이 {duplicates}개 있습니다.")

    # 옵션별 집계 (Polars 방식)
    option_summary = order_df.group_by(group_cols).agg([
        pl.col('수량').sum().alias('수량'),
        pl.col('환불수량').sum().alias('환불수량')
    ])

    logging.info(f"-> {store}({date}) 옵션별 집계 완료 (Polars): {option_summary.height}개 옵션")

    return option_summary


def generate_individual_reports_polars():
    """개별 스토어의 주문조회 파일을 기반으로 옵션별 통합 리포트를 생성 - Polars 버전"""
    logging.info("🎡 ===== GENERATE_INDIVIDUAL_REPORTS_POLARS 함수 호출됨 =====")
    logging.info("--- 1단계: 주문조회 기반 개별 통합 리포트 생성 시작 (Polars) ---")

    # 마진정보 파일 로드 및 검증
    try:
        margin_df, rep_price_map = load_and_validate_margin_data_polars()
    except Exception as e:
        logging.error(f"마진정보 로드 실패: {e}")
        return []

    # 처리 가능한 파일들 찾기
    logging.info(f"🔍 작업폴더 스캔: {config.get_processing_dir()}")
    all_files = [f for f in os.listdir(config.get_processing_dir()) if f.endswith('.xlsx') and not f.startswith('~')]
    logging.info(f"📄 전체 Excel 파일들 ({len(all_files)}개): {all_files}")

    source_files = [f for f in all_files if '통합_리포트' not in f and '마진정보' not in f]
    logging.info(f"📊 원본 파일들 ({len(source_files)}개): {source_files}")

    # 주문조회 파일만 필터링
    order_files = [f for f in source_files if '스마트스토어_주문조회' in f]
    logging.info(f"🛍 주문조회 파일들 ({len(order_files)}개): {order_files}")

    if not order_files:
        logging.warning("⚠️ 처리할 주문조회 파일이 없습니다!")
        logging.info("📋 파일명 패턴을 확인해주세요: 파일명에 '스마트스토어_주문조회'가 포함되어야 합니다.")
        return []

    logging.info(f"총 {len(order_files)}개의 주문조회 파일에 대한 리포트를 생성합니다. (Polars 엔진)")
    processed_groups = []

    for order_file in order_files:
        # 파일명에서 스토어명과 날짜 추출
        if '스마트스토어_주문조회' in order_file:
            parts = order_file.split(' 스마트스토어_주문조회_')
            if len(parts) == 2:
                store = parts[0]
                date = parts[1].replace('.xlsx', '')
            else:
                continue
        else:
            continue

        output_filename = f'{store}_통합_리포트_{date}.xlsx'
        output_path = os.path.join(config.get_processing_dir(), output_filename)

        # 이미 리포트가 존재하는지 확인
        if os.path.exists(output_path):
            logging.info(f"- {store} ({date}) 이미 리포트가 생성되어 있습니다.")
            processed_groups.append((store, date))
            continue

        logging.info(f"- {store} ({date}) 주문조회 기반 데이터 처리 시작 (Polars)...")

        try:
            # 주문조회 파일 처리
            order_df = process_order_file_polars(order_file, store, date, margin_df)
            if order_df is None:
                continue

            # 옵션별 집계
            option_summary = aggregate_options_polars(order_df, store, date)

            # 리워드 누락 상품 추가 로직
            option_summary = add_missing_reward_products_polars(option_summary, store, date, margin_df)

            # 마진정보와 병합
            final_df = merge_with_margin_data_polars(option_summary, margin_df, store, date)

            # 계산 필드 추가
            final_df = add_calculated_fields_polars(final_df, store, date, rep_price_map)

            # 주문조회 기반 추가 지표 계산
            final_df = add_order_based_metrics_polars(final_df, order_df, store, date)

            # 최종 데이터 정리 및 저장
            success = save_report_polars(final_df, output_path, store, date)

            if success:
                processed_groups.append((store, date))

        except Exception as e:
            logging.error(f"-> {store}({date}) 처리 중 오류 (Polars): {e}")
            continue

    logging.info(f"✅ 개별 리포트 생성 완료 (Polars): {len(processed_groups)}개 그룹 처리됨")
    return processed_groups


def add_missing_reward_products_polars(option_summary, store, date, margin_df):
    """리워드 설정된 상품 중 누락된 것들을 0 데이터로 추가 - Polars 버전"""
    logging.info(f"-> {store}({date}) 리워드 설정된 상품 중 누락된 상품 체크 (Polars)...")

    try:
        reward_file = os.path.join(config.BASE_DIR, '리워드설정.json')

        if not os.path.exists(reward_file):
            logging.info(f"-> {store}({date}) 리워드 설정 파일이 없습니다.")
            return option_summary

        with open(reward_file, 'r', encoding='utf-8') as f:
            reward_data = json.load(f)

        # 해당 날짜에 리워드가 설정된 상품들 찾기
        rewarded_products = set()
        for reward_entry in reward_data.get('rewards', []):
            start_date = reward_entry.get('start_date', '')
            end_date = reward_entry.get('end_date', '')
            product_id = str(reward_entry.get('product_id', ''))
            reward_amount = reward_entry.get('reward', 0)

            if (start_date <= date <= end_date and
                product_id and product_id != 'nan' and product_id != '' and
                reward_amount and reward_amount > 0):
                normalized_id = normalize_product_id_polars(product_id)
                rewarded_products.add(normalized_id)

        logging.info(f"-> {store}({date}) 리워드 설정된 상품들: {list(rewarded_products)}")

        # 스토어별 필터링
        if '스토어' in margin_df.columns:
            store_products = set(
                margin_df.filter(pl.col('스토어') == store)
                         .select(pl.col('상품ID'))
                         .to_series()
                         .to_list()
            )
            store_rewarded_products = rewarded_products & store_products
        else:
            store_rewarded_products = rewarded_products

        # 기존 상품들 (Polars에서 집합으로 변환)
        existing_products = set(
            option_summary.select(pl.col('상품ID'))
                          .to_series()
                          .to_list()
        )

        missing_rewarded_products = store_rewarded_products - existing_products

        if missing_rewarded_products:
            logging.info(f"-> {store}({date}) 주문조회에 없는 리워드 설정 상품 {len(missing_rewarded_products)}개: {list(missing_rewarded_products)}")

            # 누락된 상품들을 0 데이터로 추가
            missing_rows = []
            for normalized_product_id in missing_rewarded_products:
                # 마진정보에서 대표옵션 찾기
                product_margin = margin_df.filter(
                    (pl.col('상품ID') == normalized_product_id) &
                    (pl.col('대표옵션') == True)
                )

                if '스토어' in margin_df.columns:
                    product_margin = product_margin.filter(pl.col('스토어') == store)

                if product_margin.height > 0:
                    product_info = product_margin.row(0, named=True)

                    # 0 데이터 행 생성
                    zero_row = {
                        '상품ID': normalized_product_id,
                        '옵션정보': product_info.get('옵션정보', ''),
                        '수량': 0,
                        '환불수량': 0
                    }

                    # 상품명 추가
                    if '상품명' in product_info:
                        zero_row['상품명'] = product_info['상품명']
                    else:
                        zero_row['상품명'] = f'상품{normalized_product_id}'

                    missing_rows.append(zero_row)
                    logging.info(f"-> {store}({date}) 0 데이터 추가: 상품 {normalized_product_id} (상품단: {zero_row['상품명']})")

            # 누락된 상품들을 option_summary에 추가
            if missing_rows:
                missing_df = pl.DataFrame(missing_rows)
                option_summary = pl.concat([option_summary, missing_df], how="diagonal")
                logging.info(f"-> {store}({date}) {len(missing_rows)}개 누락 상품 추가 완료")
        else:
            logging.info(f"-> {store}({date}) 모든 리워드 설정 상품이 주문조회에 존재합니다.")

        return option_summary

    except Exception as e:
        logging.warning(f"-> {store}({date}) 리워드 누락 상품 처리 실패: {e}")
        return option_summary


def merge_with_margin_data_polars(option_summary, margin_df, store, date):
    """옵션 요약과 마진정보를 병합 - Polars 최적화"""
    logging.info(f"-> {store}({date}) 마진정보와 병합 시작 (Polars)...")

    # 1차: 정확한 매칭 (상품ID + 옵션정보)
    exact_match = option_summary.join(
        margin_df,
        on=['상품ID', '옵션정보'],
        how='inner'
    )

    logging.info(f"-> {store}({date}) 정확한 매칭: {exact_match.height}/{option_summary.height} ({exact_match.height/option_summary.height*100:.1f}%)")

    # 매칭률이 낮으면 대안 매칭 시도
    if exact_match.height < option_summary.height * 0.8:  # 80% 미만 매칭 시
        logging.warning(f"-> {store}({date}) 정확한 매칭 비율이 낮아 대안 매칭 시도")

        # 상품ID만으로 매칭 (옵션 무시)
        margin_id_only = margin_df.group_by('상품ID').first()
        fallback_match = option_summary.join(
            margin_id_only,
            on='상품ID',
            how='left'
        )

        logging.info(f"-> {store}({date}) 대안 매칭 (상품ID만): {fallback_match.height - fallback_match.filter(pl.col('판매가').is_null()).height}/{option_summary.height}")

        final_df = fallback_match
    else:
        # 정확한 매칭 + 매칭 실패 데이터 처리
        unmatched = option_summary.join(
            margin_df.select(['상품ID', '옵션정보']),
            on=['상품ID', '옵션정보'],
            how='anti'
        )

        if unmatched.height > 0:
            logging.warning(f"-> {store}({date}) 매칭 실패 데이터 {unmatched.height}개를 상품ID로만 매칭 시도")

            margin_id_only = margin_df.group_by('상품ID').first()
            unmatched_fixed = unmatched.join(
                margin_id_only,
                on='상품ID',
                how='left'
            )

            final_df = pl.concat([exact_match, unmatched_fixed], how="diagonal")
        else:
            final_df = exact_match

    # 매칭 결과 확인
    matched_count = final_df.filter(pl.col('판매가').is_not_null()).height
    logging.info(f"-> {store}({date}) 최종 매칭 결과: {matched_count}/{option_summary.height} ({matched_count/option_summary.height*100:.1f}%)")

    return final_df


def add_calculated_fields_polars(final_df, store, date, rep_price_map):
    """계산 필드 추가 - Polars 최적화"""
    logging.info(f"-> {store}({date}) 계산 필드 추가 시작 (Polars)...")

    # 상품명 처리
    if '상품명' not in final_df.columns:
        logging.error(f"-> {store}({date}) 상품명 컬럼을 찾을 수 없습니다!")
        final_df = final_df.with_columns([pl.col('상품ID').alias('상품명')])
        logging.warning(f"-> {store}({date}) 임시로 상품ID를 상품명으로 사용합니다.")

    # 기본 계산 필드들을 병렬로 처리 (Context7 모범 사례)
    basic_calculation_exprs = [
        (pl.col('수량') * pl.col('판매가')).alias('결제금액'),
        (pl.col('환불수량') * pl.col('판매가')).alias('환불금액'),
    ]

    final_df = final_df.with_columns(basic_calculation_exprs)

    # 매출 계산 (환불금액 오타 수정)
    final_df = final_df.with_columns([
        (pl.col('결제금액') - pl.col('환불금액')).alias('매출')
    ])

    # 대표판매가 매핑 (rep_price_map 사용)
    if rep_price_map:
        # Polars에서 map_dict 사용
        final_df = final_df.with_columns([
            pl.col('상품ID').map_dict(rep_price_map, default=0.0).alias('대표판매가')
        ])
    else:
        final_df = final_df.with_columns([pl.lit(0.0).alias('대표판매가')])

    # 가구매 개수 적용 - Context7 join 패턴으로 완전 벡터화
    logging.info(f"-> {store}({date}) 가구매 개수 적용 시작 (벡터화)...")

    # 가구매 설정을 DataFrame으로 변환
    purchase_df = create_purchase_dataframe_for_date(date)

    if purchase_df.height > 0:
        # join으로 가구매 개수 매핑 (Context7 모범 사례)
        final_df = final_df.join(
            purchase_df,
            on=['상품ID', '옵션정보'],
            how='left'
        ).with_columns([
            # 대표옵션이면서 가구매 설정이 있는 경우에만 적용
            pl.when(
                (pl.col('대표옵션') == True) &
                (pl.col('가구매_개수').is_not_null())
            )
            .then(pl.col('가구매_개수'))
            .otherwise(0)
            .alias('가구매 개수')
        ]).drop('가구매_개수')  # 임시 컬럼 제거
    else:
        # 가구매 설정이 없으면 기본값 0
        final_df = final_df.with_columns([pl.lit(0).alias('가구매 개수')])

    logging.info(f"-> {store}({date}) 가구매 개수 적용 완료")

    # 모든 계산 필드를 병렬로 처리 (Context7 모범 사례)
    calculation_exprs = [
        # 기본 계산
        (pl.col('수량') - pl.col('환불수량') - pl.col('가구매 개수')).alias('실판매개수'),
        pl.col('가구매 개수').alias('가구매 수량'),
        pl.col('대표판매가').alias('개당 가구매 금액'),
    ]

    final_df = final_df.with_columns(calculation_exprs)

    # 의존성이 있는 계산들을 두 번째 단계로 처리
    dependent_calculation_exprs = [
        (pl.col('개당 가구매 금액') * pl.col('가구매 수량')).alias('가구매 금액'),
    ]

    final_df = final_df.with_columns(dependent_calculation_exprs)

    # 최종 계산들
    final_calculation_exprs = [
        (pl.col('매출') - pl.col('가구매 금액')).alias('순매출'),
        (pl.col('개당 가구매 비용') * pl.col('가구매 수량')).alias('가구매 비용')
    ]

    final_df = final_df.with_columns(final_calculation_exprs)

    # 리워드 적용 - Context7 join 패턴으로 완전 벡터화
    logging.info(f"-> {store}({date}) 리워드 적용 시작 (벡터화)...")

    # 리워드 설정을 DataFrame으로 변환
    reward_df = create_reward_dataframe_for_date(date)

    if reward_df.height > 0:
        # join으로 리워드 매핑 (Context7 모범 사례)
        final_df = final_df.join(
            reward_df,
            on=['상품ID', '옵션정보'],
            how='left'
        ).with_columns([
            # 대표옵션이면서 리워드 설정이 있는 경우에만 적용
            pl.when(
                (pl.col('대표옵션') == True) &
                (pl.col('리워드_금액').is_not_null())
            )
            .then(pl.col('리워드_금액'))
            .otherwise(0)
            .alias('리워드')
        ]).drop('리워드_금액')  # 임시 컬럼 제거
    else:
        # 리워드 설정이 없으면 기본값 0
        final_df = final_df.with_columns([pl.lit(0).alias('리워드')])

    logging.info(f"-> {store}({date}) 리워드 적용 완료")

    # 모든 비율 계산을 병렬로 처리 (Context7 모범 사례)
    ratio_calculation_exprs = [
        # 기본 계산
        (pl.col('순매출') * pl.col('마진율')).alias('판매마진'),
        # 광고비율 = (리워드 + 가구매 비용) / 순매출
        safe_divide_polars(
            pl.col('리워드') + pl.col('가구매 비용'),
            pl.col('순매출'),
            0.0
        ).alias('광고비율')
    ]

    final_df = final_df.with_columns(ratio_calculation_exprs)

    # 의존성 있는 계산과 퍼센트 변환을 병렬로 처리
    final_ratio_exprs = [
        # 이윤율과 순이익 계산
        (pl.col('마진율') - pl.col('광고비율')).alias('이윤율'),
        (pl.col('판매마진') - pl.col('가구매 비용') - pl.col('리워드')).alias('순이익'),
        # 퍼센트 변환 (동시 처리)
        (pl.col('마진율') * 100).round(1).alias('마진율_percent'),
        (pl.col('광고비율') * 100).round(1).alias('광고비율_percent'),
    ]

    final_df = final_df.with_columns(final_ratio_exprs)

    # 이윤율 퍼센트 변환 (의존성 때문에 별도 처리)
    final_df = final_df.with_columns([
        (pl.col('이윤율') * 100).round(1).alias('이윤율_percent')
    ])

    # 원래 컬럼명으로 복원
    final_df = final_df.with_columns([
        pl.col('마진율_percent').alias('마진율'),
        pl.col('광고비율_percent').alias('광고비율'),
        pl.col('이윤율_percent').alias('이윤율')
    ]).drop(['마진율_percent', '광고비율_percent', '이윤율_percent'])

    logging.info(f"-> {store}({date}) 계산 필드 추가 완료 (Polars)")
    return final_df


def add_order_based_metrics_polars(final_df, order_df, store, date):
    """주문조회 기반 추가 지표 계산 - Polars 버전"""
    logging.info(f"-> {store}({date}) 주문조회 기반 지표 계산 (Polars)...")

    # 상품주문번호 컬럼이 있는 경우
    if '상품주문번호' in order_df.columns:
        # 결제수 (상품주문번호 개수)
        order_count = order_df.group_by(['상품ID', '옵션정보']).agg([
            pl.col('상품주문번호').n_unique().alias('결제수')
        ])

        final_df = final_df.join(order_count, on=['상품ID', '옵션정보'], how='left')
        final_df = final_df.with_columns([pl.col('결제수').fill_null(0)])

        # 환불건수 (환불 상태인 주문번호 개수)
        cancel_orders = order_df.filter(pl.col('클레임상태').is_in(config.CANCEL_OR_REFUND_STATUSES))
        if cancel_orders.height > 0:
            refund_count = cancel_orders.group_by(['상품ID', '옵션정보']).agg([
                pl.col('상품주문번호').n_unique().alias('환부건수')
            ])

            final_df = final_df.join(refund_count, on=['상품ID', '옵션정보'], how='left')
            final_df = final_df.with_columns([pl.col('환부건수').fill_null(0)])
        else:
            final_df = final_df.with_columns([pl.lit(0).alias('환부건수')])
    else:
        final_df = final_df.with_columns([
            pl.lit(0).alias('결제수'),
            pl.lit(0).alias('환부건수')
        ])

    return final_df


def save_report_polars(final_df, output_path, store, date):
    """최종 리포트 저장 - Polars 버전"""
    try:
        # 최종 컬럼 정리
        final_columns = [col for col in config.COLUMNS_TO_KEEP if col in final_df.columns]
        sorted_df = final_df.select(final_columns).sort(['상품명', '옵션정보'])

        # 데이터 요약 로깅
        logging.info(f"-> {store}({date}) 최종 데이터 요약 (Polars):")
        logging.info(f"   - 총 옵션 수: {sorted_df.height}")
        logging.info(f"   - 총 판매수량: {sorted_df.select(pl.col('수량').sum()).item()}")
        logging.info(f"   - 총 환부수량: {sorted_df.select(pl.col('환부수량').sum()).item()}")
        logging.info(f"   - 총 매출: {sorted_df.select(pl.col('매출').sum()).item():,.0f}원")
        logging.info(f"   - 총 판매마진: {sorted_df.select(pl.col('판매마진').sum()).item():,.0f}원")

        # pandas로 변환하여 Excel 저장 (기존 호환성 유지)
        sorted_df_pandas = sorted_df.to_pandas()

        # 피벗 테이블 생성
        pivot_quantity = sorted_df_pandas.pivot_table(
            index='상품명',
            columns='옵션정보',
            values='수량',
            aggfunc='sum',
            fill_value=0
        )

        pivot_margin = sorted_df_pandas.pivot_table(
            index='상품명',
            columns='옵션정보',
            values='판매마진',
            aggfunc='sum',
            fill_value=0
        )

        # Excel 파일 생성
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            sorted_df_pandas.to_excel(writer, sheet_name='정리된 데이터', index=False)
            pivot_quantity.to_excel(writer, sheet_name='옵션별 판매수량')
            pivot_margin.to_excel(writer, sheet_name='옵션별 판매마진')

            # 표 서식 적용
            worksheet = writer.sheets['정리된 데이터']
            (max_row, max_col) = sorted_df_pandas.shape
            worksheet.add_table(0, 0, max_row, max_col - 1, {
                'columns': [{'header': col} for col in sorted_df_pandas.columns]
            })

            # 컬럼 폭 자동 조정
            for i, col in enumerate(sorted_df_pandas.columns):
                col_len = max(sorted_df_pandas[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, col_len)

        # 생성 완료 확인
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            output_filename = os.path.basename(output_path)
            logging.info(f"-> '{output_filename}' 생성 완료 (Polars): (파일 크기: {file_size:,} bytes)")
            return True
        else:
            logging.error(f"-> {store}({date}) 파일 생성 실패")
            return False

    except Exception as e:
        logging.error(f"-> {store}({date}) 리포트 저장 중 오류 (Polars): {e}")
        return False


# 기존 함수와의 호환성을 위한 래퍼 함수
def generate_individual_reports():
    """기존 pandas 버전과의 호환성을 위한 래퍼 함수"""
    if USE_POLARS:
        logging.info("⚡ Polars 엔진을 사용하여 리포트를 생성합니다.")
        return generate_individual_reports_polars()
    else:
        logging.info("🐌 Pandas 엔진을 사용하여 리포트를 생성합니다.")
        # 기존 pandas 버전 호출 (import된 경우)
        try:
            from . import report_generator
            return report_generator.generate_individual_reports()
        except ImportError:
            logging.error("Pandas 버전을 찾을 수 없습니다. Polars 버전을 사용합니다.")
            return generate_individual_reports_polars()