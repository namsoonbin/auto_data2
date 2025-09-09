# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import os
import glob
import re
import logging
from datetime import datetime
from . import config

def create_weekly_report(start_date_str, end_date_str, download_folder=None):
    """
    지정된 기간 동안의 일일 전체 통합 리포트를 취합하여 주간/월간 통합 리포트를 생성합니다.
    이 함수는 자동화 흐름에 포함되지 않으며, 별도로 호출해야 합니다.
    
    Args:
        start_date_str (str): 시작 날짜 (YYYY-MM-DD)
        end_date_str (str): 종료 날짜 (YYYY-MM-DD)
        download_folder (str, optional): 다운로드 폴더 경로. None이면 기존 config 사용
    """
    logging.info(f"--- 3단계: 주간/월간 통합 리포트 생성 시작 ({start_date_str} ~ {end_date_str}) ---")

    # 날짜 검증
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError as e:
        logging.error(f"날짜 형식이 잘못되었습니다. 'YYYY-MM-DD' 형식으로 입력해주세요: {e}")
        return False

    # 날짜 범위 검증
    if start_date > end_date:
        logging.error("시작 날짜가 종료 날짜보다 늦을 수 없습니다.")
        return False

    # 다운로드 폴더 설정 (전역 상태 변경 방지)
    if download_folder:
        try:
            validated_path = config.validate_directory(download_folder)
            report_archive_dir = os.path.join(validated_path, '리포트보관함')
        except ValueError as e:
            logging.error(f"다운로드 폴더 경로 오류: {e}")
            return False
    else:
        report_archive_dir = config.get_report_archive_dir()
    if not os.path.exists(report_archive_dir):
        logging.warning(f"리포트 보관함 폴더를 찾을 수 없습니다: {report_archive_dir}")
        return False

    # 리포트 보관함에서 전체 통합 리포트 파일 찾기
    all_daily_reports = glob.glob(os.path.join(report_archive_dir, '전체_통합_리포트_*.xlsx'))
    
    date_pattern = re.compile(r'전체_통합_리포트_(\d{4}-\d{2}-\d{2})\.xlsx')
    
    target_files = []
    for report_path in all_daily_reports:
        match = date_pattern.search(os.path.basename(report_path))
        if match:
            report_date_str = match.group(1)
            report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date()
            if start_date <= report_date <= end_date:
                target_files.append(report_path)

    if not target_files:
        logging.warning(f"기간 내({start_date_str} ~ {end_date_str})에 취합할 일일 통합 리포트가 없습니다.")
        return False

    logging.info(f"총 {len(target_files)}개의 일일 리포트를 취합합니다.")

    all_dfs = []
    successful_files = []
    failed_files = []
    
    for file_path in target_files:
        try:
            # 파일 존재 및 접근 가능 여부 확인
            if not os.path.exists(file_path):
                failed_files.append((file_path, "파일이 존재하지 않음"))
                continue
            
            if not os.access(file_path, os.R_OK):
                failed_files.append((file_path, "파일 읽기 권한 없음"))
                continue
            
            # Excel 파일 읽기
            df = pd.read_excel(file_path, sheet_name='전체 통합 데이터', engine='openpyxl')
            
            # 데이터 검증
            if df.empty:
                logging.warning(f"-> '{os.path.basename(file_path)}' 파일이 비어있습니다. 건너뛰기")
                failed_files.append((file_path, "빈 데이터"))
                continue
            
            # 필수 컬럼 검증
            required_cols = ['상품ID', '상품명', '옵션정보']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logging.warning(f"-> '{os.path.basename(file_path)}' 필수 컬럼 누락: {missing_cols}. 건너뛰기")
                failed_files.append((file_path, f"필수 컬럼 누락: {missing_cols}"))
                continue
            
            all_dfs.append(df)
            successful_files.append(file_path)
            logging.info(f"-> '{os.path.basename(file_path)}' 통합 완료: {len(df)}행 데이터 추가")
            
        except FileNotFoundError:
            error_msg = "파일을 찾을 수 없음"
            failed_files.append((file_path, error_msg))
            logging.error(f"-> '{os.path.basename(file_path)}' 처리 실패: {error_msg}")
        except PermissionError:
            error_msg = "파일 접근 권한 없음"
            failed_files.append((file_path, error_msg))
            logging.error(f"-> '{os.path.basename(file_path)}' 처리 실패: {error_msg}")
        except pd.errors.ExcelFileError as e:
            error_msg = f"Excel 파일 형식 오류: {str(e)}"
            failed_files.append((file_path, error_msg))
            logging.error(f"-> '{os.path.basename(file_path)}' 처리 실패: {error_msg}")
        except ValueError as e:
            error_msg = f"시트를 찾을 수 없음: {str(e)}"
            failed_files.append((file_path, error_msg))
            logging.error(f"-> '{os.path.basename(file_path)}' 처리 실패: {error_msg}")
        except Exception as e:
            error_msg = f"예상치 못한 오류: {str(e)}"
            failed_files.append((file_path, error_msg))
            logging.error(f"-> '{os.path.basename(file_path)}' 처리 실패: {error_msg}")
    
    # 결과 요약
    logging.info(f"-> 파일 처리 결과: 성공 {len(successful_files)}개, 실패 {len(failed_files)}개")
    if failed_files:
        logging.warning("-> 실패한 파일들:")
        for failed_file, reason in failed_files:
            logging.warning(f"   - {os.path.basename(failed_file)}: {reason}")

    if not all_dfs:
        logging.error("리포트 데이터를 읽는 데 모두 실패했습니다.")
        return False
    
    # 부분 성공 시 경고 메시지
    if failed_files:
        success_rate = len(successful_files) / len(target_files) * 100
        if success_rate < 50:
            logging.warning(f"성공률이 낮습니다 ({success_rate:.1f}%). 결과의 정확성을 확인하세요.")
        else:
            logging.info(f"부분 성공: {success_rate:.1f}%의 파일이 성공적으로 처리되었습니다.")

    # 데이터 통합 및 재집계
    try:
        master_df = pd.concat(all_dfs, ignore_index=True)
        logging.info(f"-> 총 {len(master_df)}행의 데이터를 통합했습니다. 이제 재집계합니다.")
        
        # 데이터 무결성 검증
        if master_df.empty:
            logging.error("통합된 데이터가 비어있습니다.")
            return False
            
    except pd.errors.OutOfBoundsDatetime as e:
        logging.error(f"날짜/시간 데이터 오류: {e}")
        return False
    except MemoryError:
        logging.error("메모리 부족으로 데이터 통합에 실패했습니다. 파일이 너무 큽니다.")
        return False
    except Exception as e:
        logging.error(f"데이터 통합 중 예상치 못한 오류: {e}")
        return False

    # 개선된 집계 로직 - 비율 지표는 가중평균으로 재계산
    grouping_keys = ['스토어명', '상품ID', '상품명', '옵션정보']
    for key in grouping_keys:
        if key in master_df.columns:
            master_df[key] = master_df[key].fillna('').astype(str)

    # 기본 집계 (합계 위주)
    sum_agg_methods = {
        '수량': 'sum', '판매마진': 'sum', '결제수': 'sum', '결제금액': 'sum',
        '환불건수': 'sum', '환불금액': 'sum', '환불수량': 'sum', '가구매 개수': 'sum',
        '가구매 비용': 'sum', '순매출': 'sum', '매출': 'sum', '가구매 금액': 'sum',
        '순이익': 'sum', '리워드': 'sum'
    }
    actual_sum_methods = {k: v for k, v in sum_agg_methods.items() if k in master_df.columns}
    
    # 기본 집계 수행
    try:
        aggregated_df = master_df.groupby(grouping_keys, as_index=False).agg(actual_sum_methods)
        logging.info(f"-> 주간 데이터 기본 집계 완료: {len(aggregated_df)}행")
        
        if aggregated_df.empty:
            logging.error("집계 결과가 비어있습니다.")
            return False
            
    except KeyError as e:
        logging.error(f"집계 중 필요한 컬럼을 찾을 수 없습니다: {e}")
        return False
    except Exception as e:
        logging.error(f"데이터 집계 중 오류: {e}")
        return False
    
    # 비율 지표는 가중평균으로 재계산 (매출액 기준)
    def safe_weighted_average(group, value_col, weight_col='매출'):
        """안전한 가중평균 계산"""
        if weight_col not in group.columns or value_col not in group.columns:
            return group[value_col].mean() if value_col in group.columns else 0
        
        weights = pd.to_numeric(group[weight_col], errors='coerce').fillna(0)
        values = pd.to_numeric(group[value_col], errors='coerce').fillna(0)
        
        total_weight = weights.sum()
        if total_weight == 0:
            return values.mean() if len(values) > 0 else 0
        
        return (values * weights).sum() / total_weight

    # 판매가 가중평균 계산 (수량 기준)
    if '판매가' in master_df.columns and '수량' in master_df.columns:
        weighted_price = master_df.groupby(grouping_keys).apply(
            lambda x: safe_weighted_average(x, '판매가', '수량')
        ).reset_index(name='판매가')
        
        aggregated_df = aggregated_df.merge(weighted_price, on=grouping_keys, how='left')
    
    # 비율 지표들 가중평균 계산 (매출액 기준)
    ratio_columns = ['마진율', '광고비율', '이윤율']
    for ratio_col in ratio_columns:
        if ratio_col in master_df.columns:
            weighted_ratio = master_df.groupby(grouping_keys).apply(
                lambda x: safe_weighted_average(x, ratio_col, '매출')
            ).reset_index(name=ratio_col)
            
            aggregated_df = aggregated_df.merge(weighted_ratio, on=grouping_keys, how='left')
    
    logging.info(f"-> 가중평균 비율 계산 완료")

    # 소수점 반올림
    for col in ['마진율', '광고비율', '이윤율']:
        if col in aggregated_df.columns:
            aggregated_df[col] = pd.to_numeric(aggregated_df[col], errors='coerce').fillna(0).round(1)

    final_columns = ['스토어명'] + [col for col in config.COLUMNS_TO_KEEP if col in aggregated_df.columns]
    aggregated_df = aggregated_df[final_columns]

    # 주간 리포트 파일 저장
    output_filename = f'주간_전체_통합_리포트_{start_date_str}_to_{end_date_str}.xlsx'
    output_path = os.path.join(report_archive_dir, output_filename)

    try:
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            aggregated_df.to_excel(writer, sheet_name='주간 통합 데이터', index=False)
            worksheet = writer.sheets['주간 통합 데이터']
            (max_row, max_col) = aggregated_df.shape
            worksheet.add_table(0, 0, max_row, max_col - 1, {'columns': [{'header': col} for col in aggregated_df.columns]})
            for i, col in enumerate(aggregated_df.columns):
                col_len = max(aggregated_df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, col_len)
        
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            logging.info(f"-> '{os.path.basename(output_path)}' 생성 완료: {output_path} (파일 크기: {file_size:,} bytes)")
            logging.info(f"--- 3단계: 주간/월간 통합 리포트 생성 완료 ---")
            return True
        else:
            logging.error(f"-> 주간 리포트 생성 실패: {output_path} 파일이 생성되지 않음")
            return False

    except Exception as e:
        logging.error(f"-> 주간 리포트 파일 저장 중 오류: {e}")
        return False
    finally:
        logging.info(f"--- 3단계: 주간/월간 통합 리포트 생성 완료 ---")
