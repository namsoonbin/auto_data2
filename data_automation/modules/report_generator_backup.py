# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import os
import glob
import re
import logging
import io
import json
from datetime import datetime, timedelta
from . import config

def normalize_product_id(value):
    """상품ID를 정규화 - 문자열과 숫자 타입 모두 처리 (문자열 내 .0 포함)"""
    if pd.isna(value):
        return ''
    
    # 먼저 문자열로 변환하고 공백 제거
    value_str = str(value).strip()

    try:
        # 문자열을 float으로 변환 시도 (예: "12345.0" 처리)
        float_val = float(value_str)
        # float이 정수이면 .0을 제거하고 문자열로 변환
        if float_val.is_integer():
            return str(int(float_val))
        # 소수점이 있는 float이면 그대로 문자열로 변환
        else:
            return str(float_val)
    except (ValueError, TypeError):
        # float 변환에 실패하면 (순수 문자열 ID), 원본 문자열 반환
        return value_str

def read_protected_excel(file_path, password=None, **kwargs):
    """
    암호로 보호된 Excel 파일을 읽는 함수
    msoffcrypto-tool이 설치되어 있으면 사용하고, 없으면 기본 pandas 사용
    """
    try:
        # 먼저 암호 없이 시도
        return pd.read_excel(file_path, engine='openpyxl', **kwargs)
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
                
                # 메모리에서 해독된 파일 처리 (최신 버전 호환)
                decrypted = io.BytesIO()
                try:
                    # 최신 버전: decrypt 메서드 사용
                    office_file.decrypt(decrypted)
                except AttributeError:
                    # 이전 버전: save 메서드 사용
                    office_file.save(decrypted)
                
                decrypted.seek(0)
                return pd.read_excel(decrypted, engine='openpyxl', **kwargs)
                
        except ImportError:
            logging.error("msoffcrypto-tool이 설치되지 않았습니다.")
            logging.error("해결 방법: pip install msoffcrypto-tool")
            logging.error("또는 Excel에서 파일을 열어 암호를 제거한 후 저장하세요.")
            raise ImportError("msoffcrypto-tool 라이브러리가 필요합니다. 'pip install msoffcrypto-tool'로 설치하세요.")
        except Exception as decrypt_error:
            logging.error(f"암호 해독 실패: {decrypt_error}")
            logging.error("암호가 올바른지 확인하거나 Excel에서 수동으로 암호를 제거해보세요.")
            raise decrypt_error

# 전역 리워드 캐시
_reward_cache = None
_reward_cache_timestamp = None

def _load_reward_cache():
    """리워드 설정을 딕셔너리로 로드하여 캐시"""
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
        
        rewards_list = data.get('rewards', [])
        if not isinstance(rewards_list, list):
            _reward_cache = {}
            return
        
        # 효율적인 조회를 위한 딕셔너리 생성
        reward_map = {}
        for reward_entry in rewards_list:
            try:
                # 필수 키 존재 확인
                if not all(k in reward_entry for k in ['start_date', 'end_date', 'product_id', 'reward']):
                    continue
                
                start_date = datetime.strptime(reward_entry['start_date'], '%Y-%m-%d').date()
                end_date = datetime.strptime(reward_entry['end_date'], '%Y-%m-%d').date()
                product_id = normalize_product_id(reward_entry['product_id'])
                reward_value = reward_entry['reward']
                
                # 리워드 값이 숫자인지 확인
                if not isinstance(reward_value, (int, float)) or reward_value < 0:
                    continue
                
                # 날짜 범위의 각 날짜별로 딕셔너리에 저장
                current_date = start_date
                while current_date <= end_date:
                    key = (current_date.strftime('%Y-%m-%d'), product_id)
                    reward_map[key] = int(reward_value)
                    current_date += timedelta(days=1)
                    
            except (ValueError, KeyError, TypeError):
                continue
        
        _reward_cache = reward_map
        _reward_cache_timestamp = file_timestamp
        logging.info(f"리워드 캐시 로드 완료: {len(reward_map)}개 엔트리")
        
    except Exception as e:
        logging.warning(f"리워드 캐시 로드 실패: {e}")
        _reward_cache = {}

def get_reward_for_date_and_product(product_id, date_str):
    """날짜와 상품ID에 해당하는 리워드 값 조회 (캐시 기반 고속 조회)"""
    try:
        # 캐시 로드 (필요시)
        _load_reward_cache()
        
        # 날짜 정규화
        target_date = None
        for date_format in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d']:
            try:
                target_date = datetime.strptime(date_str, date_format).date().strftime('%Y-%m-%d')
                break
            except ValueError:
                continue
        
        if target_date is None:
            return 0
        
        # 상품ID 정규화
        normalized_product_id = normalize_product_id(product_id)
        
        # O(1) 딕셔너리 조회
        key = (target_date, normalized_product_id)
        return _reward_cache.get(key, 0)
        
    except Exception as e:
        logging.warning(f"리워드 조회 오류: {e}")
        return 0

def get_purchase_count_for_date_and_product(product_id, date_str):
    """날짜와 상품ID에 해당하는 가구매 개수 조회 (리워드 방식과 동일)"""
    try:
        purchase_file = os.path.join(config.BASE_DIR, '가구매설정.json')
        
        # 파일 존재 확인
        if not os.path.exists(purchase_file):
            return 0
        
        # 파일 크기 확인 (빈 파일 체크)
        if os.path.getsize(purchase_file) == 0:
            return 0
        
        # JSON 파일 읽기
        with open(purchase_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 데이터 구조 검증
        if not isinstance(data, dict) or 'purchases' not in data:
            return 0
        
        purchases_list = data.get('purchases', [])
        if not isinstance(purchases_list, list):
            return 0
        
        # 날짜 파싱 (여러 형식 지원)
        target_date = None
        for date_format in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d']:
            try:
                target_date = datetime.strptime(date_str, date_format).date()
                break
            except ValueError:
                continue
        
        if target_date is None:
            logging.warning(f"가구매 개수 조회: 날짜 형식을 파싱할 수 없습니다: {date_str}")
            return 0
        
        # 해당 상품과 날짜에 맞는 가구매 개수 찾기
        for purchase_entry in purchases_list:
            try:
                # 필수 키 존재 확인
                if not all(k in purchase_entry for k in ['start_date', 'end_date', 'product_id', 'purchase_count']):
                    continue
                
                start_date = datetime.strptime(purchase_entry['start_date'], '%Y-%m-%d').date()
                end_date = datetime.strptime(purchase_entry['end_date'], '%Y-%m-%d').date()
                
                # 상품ID 정규화하여 비교
                normalized_entry_id = normalize_product_id(purchase_entry['product_id'])
                normalized_target_id = normalize_product_id(product_id)
                
                if (start_date <= target_date <= end_date and 
                    normalized_entry_id == normalized_target_id):
                    purchase_count = purchase_entry['purchase_count']
                    # 가구매 개수가 숫자인지 확인
                    if isinstance(purchase_count, (int, float)) and purchase_count >= 0:
                        return int(purchase_count)
            except (ValueError, KeyError, TypeError) as e:
                # 개별 엔트리 파싱 실패는 로그만 남기고 계속 진행
                continue
        
        return 0  # 설정이 없으면 0
        
    except FileNotFoundError:
        return 0
    except json.JSONDecodeError as e:
        logging.warning(f"가구매 설정 JSON 파일 형식 오류: {e}")
        return 0
    except Exception as e:
        logging.warning(f"가구매 개수 조회 중 예상치 못한 오류: {e}")
        return 0

def generate_individual_reports():
    """개별 스토어의 주문조회 파일을 기반으로 옵션별 통합 리포트를 생성합니다."""
    logging.info("🎯 ===== GENERATE_INDIVIDUAL_REPORTS 함수 호출됨 =====")
    logging.info("--- 1단계: 주문조회 기반 개별 통합 리포트 생성 시작 ---")
    
    # 마진정보 파일 로드 및 검증
    try:
        margin_df = pd.read_excel(config.MARGIN_FILE, engine='openpyxl')
        logging.info(f"'{os.path.basename(config.MARGIN_FILE)}' 파일을 성공적으로 불러왔습니다.")
        
        # 필수 컬럼 존재 확인
        required_columns = ['상품번호', '상품명', '판매가', '마진율']
        missing_columns = [col for col in required_columns if col not in margin_df.columns]
        if missing_columns:
            raise ValueError(f"마진정보 파일에 필수 컬럼이 없습니다: {missing_columns}")
        
        # 컬럼명 정규화
        margin_df = margin_df.rename(columns={'상품번호': '상품ID'})
        
        # 상품ID 데이터 타입 정규화 (문자열/숫자 모두 처리)
        margin_df['상품ID'] = margin_df['상품ID'].apply(normalize_product_id)
        if margin_df['상품ID'].isna().any():
            logging.warning("마진정보에 빈 상품ID가 있습니다. 해당 행들을 제거합니다.")
            margin_df = margin_df.dropna(subset=['상품ID'])
        
        # 데이터 타입 검증 및 변환
        if not pd.api.types.is_numeric_dtype(margin_df['판매가']):
            logging.warning("판매가 컬럼이 숫자 타입이 아닙니다. 변환을 시도합니다.")
            margin_df['판매가'] = pd.to_numeric(margin_df['판매가'], errors='coerce')
        
        if not pd.api.types.is_numeric_dtype(margin_df['마진율']):
            logging.warning("마진율 컬럼이 숫자 타입이 아닙니다. 변환을 시도합니다.")
            margin_df['마진율'] = pd.to_numeric(margin_df['마진율'], errors='coerce')
        
        # 대표옵션 정보 처리
        if '대표옵션' in margin_df.columns:
            margin_df['대표옵션'] = margin_df['대표옵션'].astype(str).str.upper().isin(['O', 'Y', 'TRUE'])
            rep_price_map = margin_df[margin_df['대표옵션'] == True].set_index('상품ID')['판매가'].to_dict()
            logging.info("대표옵션 판매가 정보를 생성했습니다.")
        else:
            logging.warning(f"경고: '{os.path.basename(config.MARGIN_FILE)}'에 '대표옵션' 컬럼이 없습니다.")
            margin_df['대표옵션'] = False
            rep_price_map = {}
            
        # 옵션정보 정규화 (마진정보) - pandas의 nullable 데이터 처리 모범사례 적용
        def normalize_option_info(value):
            """옵션정보 정규화 - 마진정보 매칭을 위한 일관된 처리"""
            if pd.isna(value):
                return ''
            
            value_str = str(value).strip()
            # 다양한 빈값 표현들을 빈 문자열로 통일 (마진정보와 매칭되도록)
            if value_str == '' or value_str.lower() in ['단일', '기본옵션', '선택안함', 'null', 'none', '없음', 'nan']:
                return ''
            
            return value_str
            
        if '옵션정보' not in margin_df.columns:
            margin_df['옵션정보'] = ''
        else:
            margin_df['옵션정보'] = margin_df['옵션정보'].apply(normalize_option_info)
            
    except FileNotFoundError:
        logging.error(f"마진정보 파일을 찾을 수 없습니다: {config.MARGIN_FILE}")
        return []
    except PermissionError:
        logging.error(f"마진정보 파일에 접근할 수 없습니다: {config.MARGIN_FILE}")
        return []
    except ValueError as e:
        logging.error(f"마진정보 파일 데이터 검증 실패: {e}")
        return []
    except Exception as e:
        logging.error(f"마진정보 파일 읽기 중 예상치 못한 오류: {e}")
        return []

    # 처리 가능한 파일들 찾기
    logging.info(f"🔍 작업폴더 스캔: {config.get_processing_dir()}")
    all_files = [f for f in os.listdir(config.get_processing_dir()) if f.endswith('.xlsx') and not f.startswith('~')]
    logging.info(f"📄 전체 Excel 파일들 ({len(all_files)}개): {all_files}")
    
    source_files = [f for f in all_files if '통합_리포트' not in f and '마진정보' not in f]
    logging.info(f"📊 원본 파일들 ({len(source_files)}개): {source_files}")

    # 주문조회 파일만 필터링
    order_files = [f for f in source_files if '스마트스토어_주문조회' in f]
    logging.info(f"🛒 주문조회 파일들 ({len(order_files)}개): {order_files}")
    
    if not order_files:
        logging.warning("⚠️ 처리할 주문조회 파일이 없습니다!")
        logging.info("📋 파일명 패턴을 확인해주세요: 파일명에 '스마트스토어_주문조회'가 포함되어야 합니다.")
        return []  # True 대신 빈 리스트 반환

    logging.info(f"총 {len(order_files)}개의 주문조회 파일에 대한 리포트를 생성합니다.")
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
            
        logging.info(f"- {store} ({date}) 주문조회 기반 데이터 처리 시작...")
        
        try:
            # 이 파일 처리를 위한 로컬 변수들 (다른 파일과 완전히 독립)
            local_missing_products = []  # 이 파일에서만 사용되는 누락 상품 리스트
            
            # 주문조회 파일 읽기 (암호 보호될 수 있음)
            order_path = os.path.join(config.get_processing_dir(), order_file)
            order_df = read_protected_excel(order_path, password=config.ORDER_FILE_PASSWORD)
            
            # 파일이 비어있는지 확인
            if order_df.empty:
                logging.error(f"-> {store}({date}) 주문조회 파일이 비어있습니다: {order_file}")
                continue
            
            logging.info(f"-> {store}({date}) 주문조회 파일 로드 완료: {len(order_df)}행")
            logging.info(f"-> {store}({date}) 주문조회 파일 컬럼: {list(order_df.columns)}")
            
            # 상품번호 -> 상품ID 변환 (컬럼이 있는 경우에만)
            if '상품번호' in order_df.columns:
                order_df = order_df.rename(columns={'상품번호': '상품ID'})
            
            # 필수 컬럼 존재 확인
            required_cols = ['상품ID']
            missing_cols = [col for col in required_cols if col not in order_df.columns]
            if missing_cols:
                logging.error(f"-> {store}({date}) 필수 컬럼 누락: {missing_cols}")
                continue
            
            # 상품ID 데이터 타입 정규화 (마진정보와 동일한 방식)
            order_df['상품ID'] = order_df['상품ID'].apply(normalize_product_id)
            
            # 옵션정보 정규화 
            def normalize_option_info(value):
                """주문조회 옵션정보 정규화 - 마진정보와 동일한 처리"""
                if pd.isna(value) or value == '' or str(value).strip() == '':
                    return ''
                value_str = str(value).strip()
                # 다양한 빈값 표현들을 빈 문자열로 통일 (마진정보와 매칭되도록)
                if value_str.lower() in ['단일', '기본옵션', '선택안함', 'null', 'none', '없음', 'nan']:
                    return ''
                return value_str
            
            if '옵션정보' not in order_df.columns:
                order_df['옵션정보'] = ''
            else:
                order_df['옵션정보'] = order_df['옵션정보'].apply(normalize_option_info)
            
            logging.info(f"-> {store}({date}) 옵션정보 정규화 후 샘플: {order_df['옵션정보'].head(5).tolist()}")
            
            # 클레임상태 컬럼 확인 및 환불 관련 처리
            if '클레임상태' not in order_df.columns:
                # 다른 가능한 컬럼명들 확인
                possible_status_cols = ['상태', '주문상태', '처리상태', '배송상태', '주문처리상태', '결제상태']
                status_col = None
                for col in possible_status_cols:
                    if col in order_df.columns:
                        status_col = col
                        break
                
                if status_col:
                    logging.info(f"-> {store}({date}) '{status_col}' 컬럼을 클레임상태로 사용합니다.")
                    order_df['클레임상태'] = order_df[status_col]
                else:
                    logging.warning(f"-> {store}({date}) 클레임상태 컬럼을 찾을 수 없습니다.")
                    order_df['클레임상태'] = '정상'
            
            # 수량 컬럼 확인
            if '수량' not in order_df.columns:
                possible_quantity_cols = ['결제수량', '주문수량', '상품수량', '결제상품수량']
                quantity_col = None
                for col in possible_quantity_cols:
                    if col in order_df.columns:
                        quantity_col = col
                        break
                
                if quantity_col:
                    logging.info(f"-> {store}({date}) '{quantity_col}' 컬럼을 수량으로 사용합니다.")
                    order_df['수량'] = order_df[quantity_col]
                else:
                    logging.warning(f"-> {store}({date}) 수량 컬럼을 찾을 수 없습니다. 기본값 1 사용")
                    order_df['수량'] = 1
            
            # 수량을 숫자형으로 변환
            order_df['수량'] = pd.to_numeric(order_df['수량'], errors='coerce').fillna(1)
            
            # 클레임상태 분포 확인
            status_counts = order_df['클레임상태'].value_counts()
            logging.info(f"-> {store}({date}) 클레임상태 분포: {status_counts.to_dict()}")
            
            # 환불수량 계산
            cancel_mask = order_df['클레임상태'].isin(config.CANCEL_OR_REFUND_STATUSES)
            order_df['환불수량'] = order_df['수량'].where(cancel_mask, 0)
            
            # 환불수량 계산 결과
            total_refund_quantity = order_df['환불수량'].sum()
            refund_rows = (order_df['환불수량'] > 0).sum()
            logging.info(f"-> {store}({date}) 총 환불수량: {total_refund_quantity}, 환불 행 수: {refund_rows}")
            
            # 옵션별 집계 (핵심 로직!) - 상품명도 함께 집계
            logging.info(f"-> {store}({date}) 옵션별 데이터 집계 시작...")
            
            # 상품명 컬럼 확인
            if '상품명' in order_df.columns:
                group_cols = ['상품ID', '상품명', '옵션정보']
                agg_dict = {
                    '수량': 'sum',           # 옵션별 총 판매수량
                    '환불수량': 'sum'        # 옵션별 총 환불수량
                }
            else:
                group_cols = ['상품ID', '옵션정보'] 
                agg_dict = {
                    '수량': 'sum',           # 옵션별 총 판매수량
                    '환불수량': 'sum'        # 옵션별 총 환불수량
                }
                logging.warning(f"-> {store}({date}) 주문조회 파일에 상품명 컬럼이 없습니다.")
            
            # 중복 데이터 검증
            duplicates = order_df.duplicated(group_cols).sum()
            if duplicates > 0:
                logging.warning(f"-> {store}({date}) 주문조회 데이터에 중복된 상품ID-옵션정보 조합이 {duplicates}개 있습니다.")
            
            option_summary = order_df.groupby(group_cols, as_index=False).agg(agg_dict)
            
            logging.info(f"-> {store}({date}) 옵션별 집계 완료: {len(option_summary)}개 옵션")
            
            # 리워드가 설정된 상품 중 누락된 것들을 0 데이터로 추가
            logging.info(f"-> {store}({date}) 리워드 설정된 상품 중 누락된 상품 체크...")
            try:
                # 리워드 설정 파일에서 해당 날짜의 설정된 상품들 가져오기
                reward_file = os.path.join(config.BASE_DIR, '리워드설정.json')
                logging.info(f"-> {store}({date}) 리워드 파일 경로: {reward_file}")
                logging.info(f"-> {store}({date}) 리워드 파일 절대경로: {os.path.abspath(reward_file)}")
                
                if os.path.exists(reward_file):
                    logging.info(f"-> {store}({date}) 리워드 파일 존재함, 파일 크기: {os.path.getsize(reward_file)} bytes")
                    logging.info(f"-> {store}({date}) 파일 읽기 권한 확인: {os.access(reward_file, os.R_OK)}")
                    
                    try:
                        with open(reward_file, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                            logging.info(f"-> {store}({date}) 파일 내용 길이: {len(file_content)} 문자")
                            logging.info(f"-> {store}({date}) 파일 내용 첫 100자: {file_content[:100]}")
                            
                        # JSON 파싱
                        with open(reward_file, 'r', encoding='utf-8') as f:
                            reward_data = json.load(f)
                            logging.info(f"-> {store}({date}) JSON 파싱 성공, 데이터 타입: {type(reward_data)}")
                            if isinstance(reward_data, dict):
                                logging.info(f"-> {store}({date}) JSON 키들: {list(reward_data.keys())}")
                                if 'rewards' in reward_data:
                                    logging.info(f"-> {store}({date}) rewards 배열 길이: {len(reward_data.get('rewards', []))}")
                    except json.JSONDecodeError as e:
                        logging.error(f"-> {store}({date}) JSON 파싱 오류: {e}")
                        logging.error(f"-> {store}({date}) 오류 위치: line {e.lineno}, column {e.colno}")
                        raise
                    except Exception as e:
                        logging.error(f"-> {store}({date}) 파일 읽기 오류: {e}")
                        raise
                    
                    # 해당 날짜에 리워드가 설정된 상품들 찾기
                    rewarded_products = set()
                    original_to_normalized = {}  # 원본 ID -> 정규화 ID 매핑
                    for reward_entry in reward_data.get('rewards', []):
                        start_date = reward_entry.get('start_date', '')
                        end_date = reward_entry.get('end_date', '')
                        product_id = str(reward_entry.get('product_id', ''))
                        reward_amount = reward_entry.get('reward', 0)
                        
                        # 유효한 리워드인지 체크: 날짜 범위, 상품ID, 리워드 금액 모두 확인
                        if (start_date <= date <= end_date and 
                            product_id and 
                            product_id != 'nan' and 
                            product_id != '' and
                            reward_amount and 
                            reward_amount > 0):
                            # 상품ID 정규화하여 저장 (.0 제거)
                            normalized_id = normalize_product_id(product_id)
                            rewarded_products.add(normalized_id)
                            original_to_normalized[product_id] = normalized_id
                            logging.debug(f"-> {store}({date}) 유효한 리워드 상품 추가: {product_id} -> {normalized_id} (리워드: {reward_amount}원)")
                    
                    logging.info(f"-> {store}({date}) 리워드 설정된 상품들: {list(rewarded_products)}")
                    
                    # 마진정보에 스토어 컬럼이 있으면 해당 스토어 상품만 필터링
                    if '스토어' in margin_df.columns:
                        # 현재 스토어에서 판매하는 상품들만 추출 (정규화하여 저장)
                        store_products = set(margin_df[margin_df['스토어'] == store]['상품ID'].astype(str).apply(normalize_product_id))
                        logging.info(f"-> {store}({date}) {store} 스토어에서 판매하는 상품: {len(store_products)}개")
                        
                        # 리워드 설정된 상품 중 이 스토어에서 판매하는 상품만 체크
                        store_rewarded_products = rewarded_products & store_products
                        logging.info(f"-> {store}({date}) {store} 스토어에서 판매하는 리워드 설정 상품: {list(store_rewarded_products)}")
                    else:
                        # 스토어 컬럼이 없으면 기존 방식 사용 (모든 상품 체크)
                        store_rewarded_products = rewarded_products
                        logging.info(f"-> {store}({date}) 스토어 컬럼이 없어 모든 리워드 상품 체크")
                    
                    # 주문조회에 없는 리워드 설정 상품들 찾기 (스토어별로 필터링됨)
                    # 기존 상품들도 정규화하여 비교
                    existing_products = set(option_summary['상품ID'].astype(str).apply(normalize_product_id))
                    missing_rewarded_products = store_rewarded_products - existing_products
                    
                    if missing_rewarded_products:
                        logging.info(f"-> {store}({date}) {store} 스토어에서 주문조회에 없는 리워드 설정 상품 {len(missing_rewarded_products)}개: {list(missing_rewarded_products)}")
                        
                        # 누락된 상품들을 0 데이터로 추가
                        for normalized_product_id in missing_rewarded_products:
                            # 마진정보에서 정규화된 ID로 매칭하여 상품 정보 찾기
                            margin_df_normalized = margin_df.copy()
                            margin_df_normalized['정규화_상품ID'] = margin_df_normalized['상품ID'].astype(str).apply(normalize_product_id)
                            # 대표옵션을 boolean으로 변환 (메인 로직과 동일하게)
                            if '대표옵션' in margin_df_normalized.columns:
                                margin_df_normalized['대표옵션'] = margin_df_normalized['대표옵션'].astype(str).str.upper().isin(['O', 'Y', 'TRUE'])
                            
                            if '스토어' in margin_df.columns:
                                # 단계별 디버깅 로그
                                id_matches = margin_df_normalized[margin_df_normalized['정규화_상품ID'] == normalized_product_id]
                                logging.info(f"-> {store}({date}) 상품 {normalized_product_id}: 정규화ID 매칭 {len(id_matches)}개")
                                
                                store_matches = margin_df_normalized[
                                    (margin_df_normalized['정규화_상품ID'] == normalized_product_id) & 
                                    (margin_df_normalized['스토어'] == store)
                                ]
                                logging.info(f"-> {store}({date}) 상품 {normalized_product_id}: 스토어 매칭 {len(store_matches)}개")
                                if len(store_matches) > 0:
                                    logging.info(f"-> {store}({date}) 상품 {normalized_product_id}: 대표옵션 값들 {store_matches['대표옵션'].tolist()}")
                                
                                product_margin = margin_df_normalized[
                                    (margin_df_normalized['정규화_상품ID'] == normalized_product_id) & 
                                    (margin_df_normalized['스토어'] == store) &
                                    (margin_df_normalized['대표옵션'] == True)
                                ]
                                logging.info(f"-> {store}({date}) 상품 {normalized_product_id}: 최종 매칭 {len(product_margin)}개")
                            else:
                                # 스토어 컬럼이 없으면 기존 방식
                                product_margin = margin_df_normalized[
                                    (margin_df_normalized['정규화_상품ID'] == normalized_product_id) & 
                                    (margin_df_normalized['대표옵션'] == True)
                                ]
                            
                            if len(product_margin) > 0:
                                product_info = product_margin.iloc[0]
                                # 0 데이터 행 생성 (정규화된 상품ID 사용)
                                zero_row = {
                                    '상품ID': normalized_product_id,
                                    '옵션정보': product_info.get('옵션정보', ''),
                                    '수량': 0,
                                    '환불수량': 0
                                }
                                
                                # 상품명 추가 (마진정보에서 가져오기)
                                if '상품명' in product_info:
                                    zero_row['상품명'] = product_info['상품명']
                                else:
                                    zero_row['상품명'] = f'상품{normalized_product_id}'
                                
                                local_missing_products.append(zero_row)
                                logging.info(f"-> {store}({date}) 0 데이터 추가: 상품 {normalized_product_id} (상품명: {zero_row['상품명']})")
                            else:
                                logging.info(f"-> {store}({date}) 상품 {normalized_product_id}의 대표옵션을 찾을 수 없음")
                    else:
                        logging.info(f"-> {store}({date}) 모든 리워드 설정 상품이 주문조회에 존재합니다.")
                
                # 누락된 상품들을 option_summary에 추가
                if local_missing_products:
                    missing_df = pd.DataFrame(local_missing_products)
                    option_summary = pd.concat([option_summary, missing_df], ignore_index=True)
                    logging.info(f"-> {store}({date}) {len(local_missing_products)}개 리워드 상품을 0 데이터로 추가 완료")
                    logging.info(f"-> {store}({date}) 최종 옵션별 집계: {len(option_summary)}개 옵션")
                else:
                    logging.info(f"-> {store}({date}) 리워드 파일이 존재하지 않습니다: {reward_file}")
                    logging.info(f"-> {store}({date}) 0 데이터 추가 없이 계속 진행합니다.")
                    
            except json.JSONDecodeError as e:
                logging.error(f"-> {store}({date}) 리워드 설정 파일 JSON 형식 오류: {e}")
                logging.error(f"-> {store}({date}) 파일 내용을 확인해주세요.")
            except FileNotFoundError:
                logging.info(f"-> {store}({date}) 리워드 설정 파일을 찾을 수 없습니다. 0 데이터 추가 없이 진행합니다.")
            except PermissionError:
                logging.error(f"-> {store}({date}) 리워드 설정 파일 읽기 권한이 없습니다.")
            except Exception as e:
                logging.error(f"-> {store}({date}) 리워드 설정 상품 추가 중 예상치 못한 오류: {e}")
                import traceback
                logging.error(f"-> {store}({date}) 상세 오류 정보: {traceback.format_exc()}")
            
            # 판매가는 마진정보 파일에서만 가져옴 (주문조회 파일에는 판매가 컬럼이 없음)
            logging.info(f"-> {store}({date}) 판매가는 마진정보 파일에서 가져옵니다.")
            
            # 병합 전 데이터 확인
            logging.info(f"-> {store}({date}) 병합 전 주문조회 상품ID 샘플: {option_summary['상품ID'].head(3).tolist()}")
            logging.info(f"-> {store}({date}) 병합 전 주문조회 옵션정보 샘플: {option_summary['옵션정보'].head(3).tolist()}")
            logging.info(f"-> {store}({date}) 병합 전 마진정보 상품ID 샘플: {margin_df['상품ID'].head(3).tolist()}")
            logging.info(f"-> {store}({date}) 병합 전 마진정보 옵션정보 샘플: {margin_df['옵션정보'].head(3).tolist()}")
            
            # 마진정보와 안전한 병합 with 검증
            logging.info(f"-> {store}({date}) 마진정보와 병합 시작...")
            
            # 병합 전 마진정보 중복 검증
            margin_duplicates = margin_df.duplicated(['상품ID', '옵션정보']).sum()
            if margin_duplicates > 0:
                logging.warning(f"-> {store}({date}) 마진정보에 중복된 상품ID-옵션정보 조합이 {margin_duplicates}개 있습니다.")
                # 첫 번째 값만 유지
                margin_df = margin_df.drop_duplicates(['상품ID', '옵션정보'], keep='first')
                logging.info(f"-> {store}({date}) 중복 제거 후 마진정보 행 수: {len(margin_df)}")
            
            # 마진정보에서 상품명 컬럼 제거 (주문조회의 상품명 유지)
            margin_cols_to_use = [col for col in margin_df.columns if col != '상품명']
            margin_df_clean = margin_df[margin_cols_to_use].copy()
            
            try:
                # 안전한 병합 with validation (상품명은 주문조회에서만 사용)
                final_df = pd.merge(
                    option_summary, 
                    margin_df_clean, 
                    on=['상품ID', '옵션정보'], 
                    how='left',
                    validate='many_to_one'  # 마진정보의 각 상품-옵션은 고유해야 함
                )
                
                # 매칭 결과 확인
                margin_matched = final_df['판매가'].notna().sum()
                total_products = len(final_df)
                match_rate = (margin_matched / total_products) * 100 if total_products > 0 else 0
                
                logging.info(f"-> {store}({date}) 마진정보 매칭 결과: {margin_matched}/{total_products} ({match_rate:.1f}%)")
                
                # 매칭 실패한 빈 옵션정보 상품들에 대한 대안 매칭 시도
                unmatched_df = final_df[final_df['판매가'].isna()]
                empty_option_unmatched = unmatched_df[unmatched_df['옵션정보'] == '']
                
                if len(empty_option_unmatched) > 0:
                    logging.info(f"-> {store}({date}) 빈 옵션정보로 매칭 실패한 상품 {len(empty_option_unmatched)}개, 상품ID만으로 재매칭 시도")
                    
                    # 빈 옵션정보를 가진 마진정보로 매칭 시도
                    margin_empty_options = margin_df_clean[margin_df_clean['옵션정보'] == ''].copy()
                    
                    if len(margin_empty_options) > 0:
                        # 상품ID만으로 매칭 (옵션정보는 빈값끼리)
                        for idx, row in empty_option_unmatched.iterrows():
                            product_id = row['상품ID']
                            margin_match = margin_empty_options[margin_empty_options['상품ID'] == product_id]
                            
                            if len(margin_match) > 0:
                                # 매칭된 마진정보로 업데이트
                                margin_info = margin_match.iloc[0]
                                for col in margin_info.index:
                                    if col not in ['상품ID', '옵션정보']:  # 키 컬럼 제외
                                        final_df.at[idx, col] = margin_info[col]
                        
                        # 재매칭 후 결과 확인
                        margin_matched_after = final_df['판매가'].notna().sum()
                        additional_matches = margin_matched_after - margin_matched
                        if additional_matches > 0:
                            logging.info(f"-> {store}({date}) 빈 옵션정보 재매칭으로 {additional_matches}개 추가 매칭 성공")
                
                final_match_rate = (final_df['판매가'].notna().sum() / len(final_df)) * 100 if len(final_df) > 0 else 0
                logging.info(f"-> {store}({date}) 최종 마진정보 매칭률: {final_match_rate:.1f}%")
            except pd.errors.MergeError as e:
                logging.error(f"-> {store}({date}) 병합 검증 실패: {e}")
                # validation 없이 재시도
                final_df = pd.merge(option_summary, margin_df_clean, on=['상품ID', '옵션정보'], how='left')
            
            # 병합 결과 확인
            merged_count = len(final_df)
            margin_matched = final_df['마진율'].notna().sum()
            logging.info(f"-> {store}({date}) 병합 완료: {merged_count}행, 마진 매칭 {margin_matched}행")
            
            # 매칭 실패한 경우 디버깅 정보 및 변드을 통한 대안 매칭 시도
            if margin_matched == 0:
                logging.warning(f"-> {store}({date}) 마진정보 매칭 실패! 디버깅 정보:")
                logging.warning(f"   주문조회 고유 상품ID: {option_summary['상품ID'].unique()[:5]}")
                logging.warning(f"   마진정보 고유 상품ID: {margin_df['상품ID'].unique()[:5]}")
                logging.warning(f"   주문조회 고유 옵션정보: {option_summary['옵션정보'].unique()[:5]}")
                logging.warning(f"   마진정보 고유 옵션정보: {margin_df['옵션정보'].unique()[:5]}")
                
                # 상품ID만으로 대안 매칭 시도 (옵션 무시)
                logging.info(f"-> {store}({date}) 옵션정보 없이 상품ID만으로 대안 매칭 시도...")
                
                # 빈 옵션정보만 필터링하여 대안 매칭 (상품명도 제외)
                margin_df_no_option = margin_df[margin_df['옵션정보'] == ''].copy()
                if len(margin_df_no_option) > 0:
                    # 옵션정보와 상품명 모두 제외
                    alt_cols = margin_df_no_option.columns.difference(['옵션정보', '상품명'])
                    final_df_alt = pd.merge(
                        option_summary, 
                        margin_df_no_option[alt_cols], 
                        on='상품ID', 
                        how='left'
                    )
                    alt_matched = final_df_alt['마진율'].notna().sum()
                    if alt_matched > 0:
                        logging.info(f"-> {store}({date}) 대안 매칭 성공: {alt_matched}개 상품 매칭")
                        # 옵션정보 컬럼 다시 추가
                        final_df_alt['옵션정보'] = option_summary['옵션정보']
                        final_df = final_df_alt
                        margin_matched = alt_matched
            
            # 기본값 설정 및 데이터 타입 검증
            numeric_columns = ['마진율', '판매가', '개당 가구매 비용']
            for col in numeric_columns:
                if col in final_df.columns:
                    # 숫자 타입을 강제로 변환
                    final_df[col] = pd.to_numeric(final_df[col], errors='coerce')
            
            final_df.fillna({
                '마진율': 0.0, 
                '판매가': 0.0,  # 마진정보의 판매가
                '개당 가구매 비용': 0.0, 
                '대표옵션': False
            }, inplace=True)
            
            # 상품명 확인 (마진정보에서 상품명을 제외했으므로 주문조회의 상품명이 유지됨)
            logging.info(f"-> {store}({date}) 상품명 확인 - 현재 컬럼: {list(final_df.columns)}")
            
            if '상품명' not in final_df.columns:
                logging.error(f"-> {store}({date}) 상품명 컬럼을 찾을 수 없습니다!")
                # 응급 처치: 상품ID를 상품명으로 사용
                final_df['상품명'] = final_df['상품ID']
                logging.warning(f"-> {store}({date}) 임시로 상품ID를 상품명으로 사용합니다.")
            else:
                logging.info(f"-> {store}({date}) 상품명 유지 완료 - 샘플: {final_df['상품명'].head(2).tolist()}")
            
            # 기본 계산 필드들
            final_df['결제금액'] = final_df['수량'] * final_df['판매가']
            final_df['환불금액'] = final_df['환불수량'] * final_df['판매가'] 
            final_df['매출'] = final_df['결제금액'] - final_df['환불금액']
            
            # 대표판매가 (가구매 금액 계산용)
            final_df['대표판매가'] = final_df['상품ID'].map(rep_price_map).fillna(0)
            
            # 가구매 개수 적용 (대표옵션에만, GUI에서 설정한 값)
            final_df['가구매 개수'] = 0  # 기본값
            rep_option_mask = final_df['대표옵션'] == True
            
            if rep_option_mask.sum() > 0:
                for product_id in final_df.loc[rep_option_mask, '상품ID'].unique():
                    purchase_count = get_purchase_count_for_date_and_product(product_id, date)
                    final_df.loc[(final_df['상품ID'] == product_id) & rep_option_mask, '가구매 개수'] = purchase_count
                    if purchase_count > 0:
                        logging.info(f"-> {store}({date}) 상품 {product_id} 가구매 개수: {purchase_count}")
            
            # 추가 계산 필드들
            final_df['가구매 수량'] = final_df['가구매 개수']
            final_df['개당 가구매 금액'] = final_df['대표판매가']
            final_df['가구매 금액'] = final_df['개당 가구매 금액'] * final_df['가구매 수량']
            final_df['순매출'] = final_df['매출'] - final_df['가구매 금액']
            final_df['가구매 비용'] = final_df['개당 가구매 비용'] * final_df['가구매 수량']
            
            # 리워드 적용 (대표옵션에만)
            final_df['리워드'] = 0
            if rep_option_mask.sum() > 0:
                for product_id in final_df.loc[rep_option_mask, '상품ID'].unique():
                    reward_value = get_reward_for_date_and_product(product_id, date)
                    final_df.loc[(final_df['상품ID'] == product_id) & rep_option_mask, '리워드'] = reward_value
                    if reward_value > 0:
                        logging.info(f"-> {store}({date}) 상품 {product_id} 리워드: {reward_value}원")
            
            # 안전한 나누기 함수 정의
            def safe_divide(numerator, denominator, fill_value=0.0):
                """안전한 나누기 - 0 나누기와 NaN 처리"""
                with np.errstate(divide='ignore', invalid='ignore'):
                    result = np.where(
                        (denominator == 0) | pd.isna(denominator),
                        fill_value,
                        numerator / denominator
                    )
                return result
            
            # 판매마진 및 비율 계산 (안전한 방식)
            final_df['판매마진'] = final_df['순매출'] * final_df['마진율']
            
            # 광고비율 = (리워드 + 가구매 비용) / 순매출
            final_df['광고비율'] = safe_divide(
                final_df['리워드'] + final_df['가구매 비용'],
                final_df['순매출'],
                fill_value=0.0  # 순매출이 0이면 광고비율은 0%
            )
            
            final_df['이윤율'] = final_df['마진율'] - final_df['광고비율']
            final_df['순이익'] = final_df['판매마진'] - final_df['가구매 비용'] - final_df['리워드']
            
            # 퍼센트 값 변환
            final_df['마진율'] = (final_df['마진율'] * 100).round(1)
            final_df['광고비율'] = (final_df['광고비율'] * 100).round(1)
            final_df['이윤율'] = (final_df['이윤율'] * 100).round(1)
            
            # 결제수, 환불건수 계산 (주문조회 기반)
            if '상품주문번호' in order_df.columns:
                # 결제수 (상품주문번호 개수)
                order_count = order_df.groupby(['상품ID', '옵션정보'])['상품주문번호'].nunique().reset_index()
                order_count.rename(columns={'상품주문번호': '결제수'}, inplace=True)
                final_df = pd.merge(final_df, order_count, on=['상품ID', '옵션정보'], how='left')
                final_df['결제수'] = final_df['결제수'].fillna(0)
                
                # 환불건수 (환불 상태인 주문번호 개수)  
                cancel_orders = order_df[order_df['클레임상태'].isin(config.CANCEL_OR_REFUND_STATUSES)]
                if not cancel_orders.empty:
                    refund_count = cancel_orders.groupby(['상품ID', '옵션정보'])['상품주문번호'].nunique().reset_index()
                    refund_count.rename(columns={'상품주문번호': '환불건수'}, inplace=True)
                    final_df = pd.merge(final_df, refund_count, on=['상품ID', '옵션정보'], how='left')
                    final_df['환불건수'] = final_df['환불건수'].fillna(0)
                else:
                    final_df['환불건수'] = 0
            else:
                final_df['결제수'] = 0
                final_df['환불건수'] = 0
                
            # 최종 컬럼 정리
            final_columns = [col for col in config.COLUMNS_TO_KEEP if col in final_df.columns]
            sorted_df = final_df[final_columns].sort_values(by=['상품명', '옵션정보'])
            
            # 데이터 요약 로깅
            logging.info(f"-> {store}({date}) 최종 데이터 요약:")
            logging.info(f"   - 총 옵션 수: {len(sorted_df)}")
            logging.info(f"   - 총 판매수량: {sorted_df['수량'].sum()}")
            logging.info(f"   - 총 환불수량: {sorted_df['환불수량'].sum()}")
            logging.info(f"   - 총 매출: {sorted_df['매출'].sum():,.0f}원")
            logging.info(f"   - 총 판매마진: {sorted_df['판매마진'].sum():,.0f}원")
            
            # 엑셀 파일 생성
            pivot_quantity = pd.pivot_table(sorted_df, index='상품명', columns='옵션정보', values='수량', aggfunc='sum', fill_value=0)
            pivot_margin = pd.pivot_table(sorted_df, index='상품명', columns='옵션정보', values='판매마진', aggfunc='sum', fill_value=0)
            
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                sorted_df.to_excel(writer, sheet_name='정리된 데이터', index=False)
                pivot_quantity.to_excel(writer, sheet_name='옵션별 판매수량')
                pivot_margin.to_excel(writer, sheet_name='옵션별 판매마진')
                
                # 표 서식 적용
                worksheet = writer.sheets['정리된 데이터']
                (max_row, max_col) = sorted_df.shape
                worksheet.add_table(0, 0, max_row, max_col - 1, {'columns': [{'header': col} for col in sorted_df.columns]})
                for i, col in enumerate(sorted_df.columns):
                    col_len = max(sorted_df[col].astype(str).map(len).max(), len(col)) + 2
                    worksheet.set_column(i, i, col_len)
            
            # 생성 완료 확인
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                logging.info(f"-> '{output_filename}' 생성 완료: (파일 크기: {file_size:,} bytes)")
                processed_groups.append((store, date))
            else:
                logging.error(f"-> 파일 생성 실패: {output_path}")
                
        except Exception as e:
            logging.error(f"-> {store}({date}) 처리 중 오류 발생: {e}")
            import traceback
            logging.error(f"-> {store}({date}) 상세 오류: {traceback.format_exc()}")
        finally:
            # 메모리 정리
            try:
                if 'order_df' in locals():
                    del order_df
                if 'final_df' in locals():
                    del final_df
                if 'sorted_df' in locals():
                    del sorted_df
            except:
                pass
    
    logging.info("--- 1단계: 주문조회 기반 개별 통합 리포트 생성 완료 ---")
    logging.info(f"🎯 ===== GENERATE_INDIVIDUAL_REPORTS 함수 종료: {len(processed_groups)}개 그룹 처리됨 =====")
    logging.info(f"📋 처리된 그룹들: {processed_groups}")
    return processed_groups



def consolidate_daily_reports():
    """날짜별로 생성된 모든 개별 리포트를 취합하여 전체 통합 리포트를 생성합니다."""
    logging.info("--- 2단계: 전체 통합 리포트 생성 시작 ---")
    all_report_files = [f for f in glob.glob(os.path.join(config.get_processing_dir(), '*_통합_리포트_*.xlsx')) if not os.path.basename(f).startswith('~') and not os.path.basename(f).startswith('전체_')]
    if not all_report_files:
        logging.info("취합할 개별 통합 리포트가 없습니다.")
        return

    date_pattern = re.compile(r'_(\d{4}-\d{2}-\d{2})\.xlsx$')
    unique_dates = set()
    for f in all_report_files:
        match = date_pattern.search(os.path.basename(f))
        if match:
            unique_dates.add(match.group(1))
    
    if not unique_dates:
        logging.info("파일에서 날짜 정보를 찾을 수 없습니다.")
        return

    logging.info(f"총 {len(sorted(list(unique_dates)))}개의 날짜에 대한 전체 리포트를 생성합니다: {sorted(list(unique_dates))}")
    logging.info(f"처리할 개별 리포트 파일 수: {len(all_report_files)}")
    for date in sorted(list(unique_dates)):
        logging.info(f"- {date} 데이터 통합 중...")
        output_file = os.path.join(config.get_processing_dir(), f'전체_통합_리포트_{date}.xlsx')
        # 정확한 날짜 매칭으로 파일 필터링 (부분 매칭 방지)
        daily_files = [f for f in all_report_files if f'_통합_리포트_{date}.xlsx' in f]
        logging.info(f"-> {date} 날짜에 대한 개별 파일 수: {len(daily_files)}")
        
        # 디버깅: 찾은 파일들 출력
        for file_path in daily_files:
            logging.info(f"-> 발견된 파일: {os.path.basename(file_path)}")
        
        daily_dfs = []
        for file_path in daily_files:
            try:
                store_name = os.path.basename(file_path).split('_통합_리포트_')[0]
                df = pd.read_excel(file_path, sheet_name='정리된 데이터', engine='openpyxl')
                df['스토어명'] = store_name
                daily_dfs.append(df)
                logging.info(f"-> '{os.path.basename(file_path)}' 통합 완료: {len(df)}행 데이터 추가")
            except Exception as e:
                logging.error(f"-> '{os.path.basename(file_path)}' 처리 중 오류: {e}")
        
        if daily_dfs:
            total_rows_before = sum(len(df) for df in daily_dfs)
            logging.info(f"-> {date} 날짜 병합 전 총 데이터 행 수: {total_rows_before}")
            
            master_df = pd.concat(daily_dfs, ignore_index=True)
            logging.info(f"-> {date} 날짜 병합 후 데이터 행 수: {len(master_df)}")
            
            # 디버깅: 병합 후 스토어별 데이터 개수 확인
            if '스토어명' in master_df.columns:
                store_counts = master_df['스토어명'].value_counts()
                logging.info(f"-> 병합 후 스토어별 데이터 개수: {dict(store_counts)}")
            
            master_df = master_df[['스토어명'] + [col for col in master_df.columns if col != '스토어명']]
            
            # 집계 키의 NULL 값 처리
            grouping_keys = ['스토어명', '상품ID', '상품명', '옵션정보']
            
            for key in grouping_keys:
                if key in master_df.columns:
                    before_null_count = master_df[key].isna().sum()
                    # 모든 집계 키를 문자열로 변환하고 NULL을 빈 문자열로 대체
                    master_df[key] = master_df[key].fillna('').astype(str)
                    after_empty_count = (master_df[key] == '').sum()
                    logging.info(f"-> '{key}' 컬럼: NULL 값 {before_null_count}개를 빈 문자열로 대체 (빈값 총 {after_empty_count}개)")
            
            # 집계를 위한 임시 옵션정보 컬럼 생성 (표시용)
            master_df['옵션정보_표시'] = master_df['옵션정보'].apply(
                lambda x: '옵션없음' if x == '' else x
            )
            
            # 집계 키를 표시용 옵션정보로 변경
            grouping_keys = ['스토어명', '상품ID', '상품명', '옵션정보_표시']
            
            empty_option_count = (master_df['옵션정보'] == '').sum()
            logging.info(f"-> 집계용 옵션정보 처리: 빈값 {empty_option_count}개를 '옵션없음'으로 표시")
            
            # 디버깅: NULL 값 처리 후 데이터 확인
            before_nulls = len(master_df)
            master_df_clean = master_df.dropna(subset=grouping_keys)
            after_nulls = len(master_df_clean)
            if before_nulls != after_nulls:
                logging.warning(f"-> 집계 키에 NULL이 남아있는 {before_nulls - after_nulls}개 행 발견, 제거됨")
                master_df = master_df_clean
            agg_methods = {
                '수량': 'sum', '판매마진': 'sum', '결제수': 'sum', '결제금액': 'sum',
                '환불건수': 'sum', '환불금액': 'sum', '환불수량': 'sum',
                '가구매 개수': 'sum', '판매가': 'mean', '마진율': 'mean',
                '가구매 비용': 'sum', '순매출': 'sum', '매출': 'sum', '가구매 금액': 'sum',
                '이윤율': 'mean', '광고비율': 'mean', '순이익': 'sum', '리워드': 'sum'
            }
            actual_agg_methods = {k: v for k, v in agg_methods.items() if k in master_df.columns}
            logging.info(f"-> {date} 날짜 집계 전 데이터 행 수: {len(master_df)}, 사용 가능한 집계 컬럼: {list(actual_agg_methods.keys())}")
            
            # 디버깅: NULL 값 처리 후 스토어별 데이터 개수 확인
            if '스토어명' in master_df.columns:
                clean_store_counts = master_df['스토어명'].value_counts()
                logging.info(f"-> NULL 처리 후 스토어별 데이터 개수: {dict(clean_store_counts)}")
            
            aggregated_df = master_df.groupby(grouping_keys, as_index=False).agg(actual_agg_methods)
            logging.info(f"-> {date} 날짜 집계 후 데이터 행 수: {len(aggregated_df)}")
            
            # 디버깅: 집계 후 스토어별 데이터 개수 확인
            if '스토어명' in aggregated_df.columns:
                agg_store_counts = aggregated_df['스토어명'].value_counts()
                logging.info(f"-> 집계 후 스토어별 데이터 개수: {dict(agg_store_counts)}")
            
            # 옵션정보_표시를 옵션정보로 변경 (최종 리포트용)
            if '옵션정보_표시' in aggregated_df.columns:
                aggregated_df['옵션정보'] = aggregated_df['옵션정보_표시']
                aggregated_df = aggregated_df.drop(columns=['옵션정보_표시'])
                logging.info(f"-> 집계 후 옵션정보 컬럼 정리: '옵션정보_표시' → '옵션정보'")
            
            # 퍼센트 필드들을 소수점 첫 자리까지 반올림
            for col in ['마진율', '광고비율', '이윤율']:
                if col in aggregated_df.columns:
                    aggregated_df[col] = aggregated_df[col].round(1)
            
            final_columns = ['스토어명'] + [col for col in config.COLUMNS_TO_KEEP if col in aggregated_df.columns]
            logging.info(f"-> {date} 날짜 최종 컬럼 수: {len(final_columns)}, 컬럼: {final_columns[:10]}...")  # 처음 10개만
            
            aggregated_df = aggregated_df[final_columns]
            logging.info(f"-> {date} 날짜 최종 데이터: {len(aggregated_df)}행")
            
            # 디버깅: 최종 저장 전 스토어별 데이터 개수 확인
            if '스토어명' in aggregated_df.columns:
                final_store_counts = aggregated_df['스토어명'].value_counts()
                logging.info(f"-> 최종 저장 전 스토어별 데이터 개수: {dict(final_store_counts)}")
            try:
                with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
                    aggregated_df.to_excel(writer, sheet_name='전체 통합 데이터', index=False)
                    worksheet = writer.sheets['전체 통합 데이터']
                    (max_row, max_col) = aggregated_df.shape
                    worksheet.add_table(0, 0, max_row, max_col - 1, {'columns': [{'header': col} for col in aggregated_df.columns]})
                    for i, col in enumerate(aggregated_df.columns):
                        col_len = max(aggregated_df[col].astype(str).map(len).max(), len(col)) + 2
                        worksheet.set_column(i, i, col_len)
                if os.path.exists(output_file):
                    file_size = os.path.getsize(output_file)
                    logging.info(f"-> '{os.path.basename(output_file)}' 생성 완료: {output_file} (파일 크기: {file_size:,} bytes)")
                    
                    # 생성된 파일 내용 검증
                    try:
                        verify_df = pd.read_excel(output_file, sheet_name='전체 통합 데이터')
                        logging.info(f"-> 검증: 전체 통합 리포트에 {len(verify_df)}행 데이터 저장됨")
                    except Exception as verify_e:
                        logging.error(f"-> 전체 리포트 검증 중 오류: {verify_e}")
                else:
                    logging.error(f"-> 전체 리포트 생성 실패: {output_file} 파일이 생성되지 않음")
            except Exception as e:
                logging.error(f"-> 최종 파일 저장 중 오류: {e}")
            finally:
                # 메모리 정리
                try:
                    del master_df, aggregated_df
                except:
                    pass
        
        # daily_dfs 메모리 정리
        try:
            del daily_dfs
        except:
            pass
        else:
            logging.warning(f"-> {date} 날짜에 대한 개별 리포트가 없어 전체 리포트를 생성할 수 없습니다.")
            
    logging.info("--- 2단계: 전체 통합 리포트 생성 완료 ---")