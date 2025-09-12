# -*- coding: utf-8 -*-
import os
import re
import shutil
import time
import logging
import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from . import config
from . import report_generator

STOP_FLAG_FILE = os.path.join(config.BASE_DIR, 'stop.flag')

def validate_excel_file(file_path):
    """Excel 파일 검증 (암호 보호된 파일 포함)"""
    if not file_path.lower().endswith('.xlsx'):
        raise ValueError(f"지원하지 않는 파일 형식입니다: {file_path}")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
    
    # 파일 크기 체크 (100MB 제한)
    file_size = os.path.getsize(file_path)
    if file_size > 100 * 1024 * 1024:
        raise ValueError(f"파일 크기가 너무 큽니다 (100MB 초과): {file_path}")
    
    # 암호 보호된 파일인지 확인 (파일 헤더 체크)
    try:
        with open(file_path, 'rb') as f:
            header = f.read(8)
            # Microsoft Office 암호화된 파일의 시그니처
            if header.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
                logging.info(f"암호 보호된 파일 감지: {os.path.basename(file_path)}")
    except Exception:
        pass  # 헤더 읽기 실패해도 계속 진행
    
    return True

def get_file_info(src_path):
    """파일 경로를 분석하여 스토어, 날짜, 파일 타입, 새 파일명을 반환합니다."""
    try:
        validate_excel_file(src_path)
        path_parts = src_path.split(os.sep)
        if len(path_parts) > 1 and path_parts[-2] != os.path.basename(config.DOWNLOAD_DIR):
            store_name = path_parts[-2]
        else:
            return None, None, None, None

        original_filename = os.path.basename(src_path)
        date_str, file_type, new_filename = None, None, None

        # 주문조회 파일 패턴 매칭 (스토어명이 포함된 경우와 포함되지 않은 경우 모두 처리)
        order_match = re.search(r"스마트스토어_주문조회_(\d{4}-\d{2}-\d{2})\.xlsx", original_filename)
        if order_match:
            date_str = order_match.group(1)
            file_type = '주문'
            new_filename = f"{store_name} 스마트스토어_주문조회_{date_str}.xlsx"
            logging.info(f"[get_file_info] 주문조회 파일 매칭됨: {original_filename} -> {new_filename}")
        
        # 상품성과 파일 패턴 매칭  
        perf_match = re.search(r"상품성과_(\d{4}-\d{2}-\d{2}).*?\.xlsx", original_filename)
        if perf_match:
            date_str = perf_match.group(1)
            file_type = '성과'
            new_filename = f"{store_name} 상품성과_{date_str}.xlsx"
            logging.info(f"[get_file_info] 상품성과 파일 매칭됨: {original_filename} -> {new_filename}")

        if date_str and file_type and new_filename:
            logging.info(f"[get_file_info] ✅ 파일 정보 추출 성공: {original_filename}")
            logging.info(f"[get_file_info]    스토어: {store_name}, 날짜: {date_str}, 타입: {file_type}")
            return store_name, date_str, file_type, new_filename
        else:
            logging.warning(f"[get_file_info] ❌ 파일 패턴 매칭 실패: {original_filename}")
            logging.warning(f"[get_file_info]    지원 패턴: '스마트스토어_주문조회_YYYY-MM-DD.xlsx' 또는 '상품성과_YYYY-MM-DD.xlsx'")
            return None, None, None, None
    except ValueError as e:
        logging.warning(f"[get_file_info] 파일 검증 실패: {e}")
        return None, None, None, None
    except FileNotFoundError as e:
        logging.error(f"[get_file_info] 파일 없음: {e}")
        return None, None, None, None
    except Exception as e:
        logging.error(f"[get_file_info] 정보 추출 중 예상치 못한 오류: {e}")
        return None, None, None, None

def _check_and_process_data(store, date):
    """주문조회 파일이 준비되었는지 확인하고 리포트 생성을 트리거합니다."""
    logging.info(f"🔍 [{store}, {date}] ===== 데이터 처리 시작 =====")
    order_file = f"{store} 스마트스토어_주문조회_{date}.xlsx"
    order_path = os.path.join(config.get_processing_dir(), order_file)
    
    logging.info(f"📂 [{store}, {date}] 찾고 있는 파일: {order_path}")
    logging.info(f"📁 [{store}, {date}] 작업폴더 경로: {config.get_processing_dir()}")
    
    # 작업폴더 내 모든 파일 목록 출력
    try:
        if os.path.exists(config.get_processing_dir()):
            all_files = os.listdir(config.get_processing_dir())
            xlsx_files = [f for f in all_files if f.endswith('.xlsx')]
            logging.info(f"📄 [{store}, {date}] 작업폴더 내 Excel 파일들 ({len(xlsx_files)}개): {xlsx_files}")
        else:
            logging.warning(f"❌ [{store}, {date}] 작업폴더가 존재하지 않습니다: {config.get_processing_dir()}")
            return
    except Exception as e:
        logging.error(f"❌ [{store}, {date}] 작업폴더 읽기 오류: {e}")
        return

    if os.path.exists(order_path):
        logging.info(f"✅ [{store}, {date}] 주문조회 파일 발견! 데이터 처리를 시작합니다.")
        
        # 이미 리포트가 생성되어 있는지 확인
        individual_report = f'{store}_통합_리포트_{date}.xlsx'
        individual_report_path = os.path.join(config.get_processing_dir(), individual_report)
        
        logging.info(f"🎯 [{store}, {date}] 생성할 리포트 파일: {individual_report_path}")
        
        if os.path.exists(individual_report_path):
            file_size = os.path.getsize(individual_report_path)
            logging.info(f"✅ [{store}, {date}] 이미 리포트가 생성되어 있습니다. (크기: {file_size:,} bytes)")
        else:
            logging.info(f"🔄 [{store}, {date}] 리포트 생성을 시작합니다...")
            # 개별 리포트만 생성 (파일 이동은 하지 않음)
            try:
                processed_groups = report_generator.generate_individual_reports()
                if processed_groups:
                    logging.info(f"✅ [{store}, {date}] 리포트 생성 성공! 처리된 그룹: {processed_groups}")
                    
                    # 실제로 파일이 생성되었는지 확인
                    if os.path.exists(individual_report_path):
                        file_size = os.path.getsize(individual_report_path)
                        logging.info(f"✅ [{store}, {date}] 리포트 파일 확인됨: {os.path.basename(individual_report_path)} (크기: {file_size:,} bytes)")
                    else:
                        logging.error(f"❌ [{store}, {date}] 리포트 생성했다고 하지만 파일이 없습니다: {individual_report_path}")
                else:
                    logging.error(f"❌ [{store}, {date}] 리포트 생성에 실패했습니다. (processed_groups가 비어있음)")
                    return
            except Exception as e:
                logging.error(f"❌ [{store}, {date}] 리포트 생성 중 예외 발생: {e}")
                import traceback
                logging.error(f"📚 [{store}, {date}] 스택 트레이스: {traceback.format_exc()}")
                return
        
        logging.info(f"✅ [{store}, {date}] 개별 리포트 처리 완료.")
    else:
        logging.warning(f"❌ [{store}, {date}] 주문조회 파일이 아직 준비되지 않았습니다: {order_path}")

def process_file(src_path):
    """감지된 파일을 처리 폴더로 옮기고, 데이터 처리를 시작합니다."""
    logging.info(f"[process_file] 파일 처리 시작: {src_path}")
    store, date, file_type, new_filename = get_file_info(src_path)
    if not all([store, date, file_type, new_filename]):
        logging.warning(f"[process_file] 파일 정보가 올바르지 않아 무시합니다: {src_path}")
        return

    dest_path = os.path.join(config.get_processing_dir(), new_filename)
    try:
        logging.info(f"[process_file] 파일 이동: '{src_path}' -> '{dest_path}'")
        shutil.move(src_path, dest_path)
        logging.info("[process_file] 파일 이동 완료.")
        _check_and_process_data(store, date)
    except Exception as e:
        logging.error(f"[process_file] 파일 이동/처리 중 오류: {e}")

class FileProcessorHandler(FileSystemEventHandler):
    """파일 시스템 이벤트를 감지하여 파일 처리를 시작하는 핸들러"""
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.xlsx') and not os.path.basename(event.src_path).startswith('~$'):
            logging.info(f"[on_created] 새 파일 감지: {event.src_path}")
            time.sleep(1)
            process_file(event.src_path)

def process_existing_files():
    """프로그램 시작 시 다운로드 폴더에 이미 있는 파일들을 처리합니다."""
    logging.info("===== 기존 파일 스캔 시작 ====")
    
    if not os.path.exists(config.DOWNLOAD_DIR):
        logging.warning(f"🔍 감시할 다운로드 폴더가 존재하지 않습니다: {config.DOWNLOAD_DIR}")
        return
    
    processed_files = 0
    total_files = 0
    
    # 제외할 시스템 폴더들
    excluded_folders = set()
    try:
        excluded_folders.add(os.path.basename(config.get_processing_dir()))  # 작업폴더
        excluded_folders.add(os.path.basename(config.get_archive_dir()))     # 원본_보관함
        excluded_folders.add(os.path.basename(config.get_report_archive_dir())) # 리포트보관함
    except Exception as e:
        logging.warning(f"시스템 폴더 경로 확인 실패: {e}")
    
    logging.info(f"제외할 시스템 폴더들: {excluded_folders}")
    
    # 다운로드 폴더 내의 스토어 폴더만 탐색 (시스템 폴더 제외)
    for store_folder in os.listdir(config.DOWNLOAD_DIR):
        store_path = os.path.join(config.DOWNLOAD_DIR, store_folder)
        if os.path.isdir(store_path) and store_folder not in excluded_folders:
            logging.info(f"📁 스토어 폴더 스캔: {store_folder}")
            store_files = [f for f in os.listdir(store_path) if f.endswith('.xlsx') and not f.startswith('~')]
            total_files += len(store_files)
            
            if not store_files:
                logging.info(f"   ℹ️ {store_folder}에 처리할 Excel 파일이 없습니다.")
                continue
                
            logging.info(f"   📄 발견된 파일들 ({len(store_files)}개): {store_files}")
            
            for filename in store_files:
                file_path = os.path.join(store_path, filename)
                logging.info(f"🔄 [기존 파일] 처리 시도: '{filename}'")
                try:
                    # 개별 파일 처리 (최종 정리는 나중에 일괄 수행)
                    process_file(file_path)
                    processed_files += 1
                    logging.info(f"✅ [기존 파일] 처리 완료: '{filename}'")
                except Exception as e:
                    logging.error(f"❌ [기존 파일] 처리 실패: '{filename}' - {e}")
    
    logging.info(f"📊 파일 처리 결과: {processed_files}/{total_files}개 성공")
    
    # 2단계: 작업폴더의 미완료 처리 파일들 검사 및 처리
    process_incomplete_files()
    
    # 3단계: 모든 개별 처리 완료 후 전체 통합 리포트 생성 및 파일 정리
    if processed_files > 0:
        logging.info("🔄 개별 처리 완료 - 전체 통합 리포트 생성 시작")
        finalize_all_processing()
    
    logging.info("===== 기존 파일 스캔 완료 =====")

def process_incomplete_files():
    """작업폴더에 있는 미완료 처리 파일들을 검사하고 리포트 생성을 시도합니다."""
    logging.info("--- 작업폴더 미완료 파일 검사 시작 ---")
    
    # 중지 신호 확인
    if os.path.exists(STOP_FLAG_FILE):
        logging.info("중지 신호 감지. 작업폴더 처리를 중단합니다.")
        return
    
    if not os.path.exists(config.get_processing_dir()):
        return
    
    # 작업폴더의 모든 엑셀 파일 스캔
    all_files = [f for f in os.listdir(config.get_processing_dir()) if f.endswith('.xlsx') and not f.startswith('~')]
    source_files = [f for f in all_files if '통합_리포트' not in f and '마진정보' not in f]
    
    if not source_files:
        logging.info("작업폴더에 미처리 파일이 없습니다.")
        return
    
    # 스토어별, 날짜별 파일 그룹 생성
    file_groups = {}
    for f in source_files:
        store, date, file_type = None, None, None
        if '상품성과' in f:
            parts = f.split(' 상품성과_')
            if len(parts) == 2: 
                store, date, file_type = parts[0], parts[1].replace('.xlsx',''), '성과'
        elif '스마트스토어_주문조회' in f:
            parts = f.split(' 스마트스토어_주문조회_')
            if len(parts) == 2: 
                store, date, file_type = parts[0], parts[1].replace('.xlsx',''), '주문'
        
        if store and date and file_type:
            key = (store, date)
            if key not in file_groups: 
                file_groups[key] = {}
            file_groups[key][file_type] = f
    
    # 완전한 파일 쌍이 있는데 리포트가 없는 경우 처리
    processed_any = False
    for (store, date), files in file_groups.items():
        # 중지 신호 확인
        if os.path.exists(STOP_FLAG_FILE):
            logging.info("중지 신호 감지. 미완료 파일 처리를 중단합니다.")
            return
            
        if '성과' in files and '주문' in files:
            individual_report = f'{store}_통합_리포트_{date}.xlsx'
            individual_report_path = os.path.join(config.get_processing_dir(), individual_report)
            
            if not os.path.exists(individual_report_path):
                logging.info(f"[미완료 처리 발견] {store} ({date}) - 리포트 생성을 재시도합니다.")
                _check_and_process_data(store, date)
    
    logging.info("--- 작업폴더 미완료 파일 검사 완료 ---")

def finalize_all_processing():
    """모든 개별 처리 완료 후 전체 통합 리포트 생성 및 파일 정리를 일괄 수행합니다."""
    logging.info("🏁 ===== 최종 정리 작업 시작 =====")
    
    # 중지 신호 확인
    if os.path.exists(STOP_FLAG_FILE):
        logging.info("⛔ 중지 신호 감지. 최종 정리 작업을 중단합니다.")
        return
    
    processing_dir = config.get_processing_dir()
    logging.info(f"📁 작업폴더 경로: {processing_dir}")
    
    # 처리할 것이 있는지 확인
    if not os.path.exists(processing_dir):
        logging.warning(f"❌ 작업폴더가 존재하지 않습니다: {processing_dir}")
        return
    
    # 작업폴더 내 모든 파일 확인
    try:
        all_files = os.listdir(processing_dir)
        all_xlsx_files = [f for f in all_files if f.endswith('.xlsx') and not f.startswith('~')]
        logging.info(f"📄 작업폴더 내 모든 Excel 파일들 ({len(all_xlsx_files)}개): {all_xlsx_files}")
    except Exception as e:
        logging.error(f"❌ 작업폴더 읽기 오류: {e}")
        return
    
    # 원본 파일이나 개별 리포트가 있는지 확인
    source_files = [f for f in all_xlsx_files if '통합_리포트' not in f]
    report_files = [f for f in all_xlsx_files if '통합_리포트' in f]
    
    logging.info(f"📋 원본 파일들 ({len(source_files)}개): {source_files}")
    logging.info(f"📊 리포트 파일들 ({len(report_files)}개): {report_files}")
    
    if not source_files and not report_files:
        logging.info("ℹ️ 정리할 파일이 없습니다.")
        return
    
    # 1단계: 전체 통합 리포트 생성 (개별 리포트가 있는 경우에만)
    if report_files:
        logging.info(f"🔄 1단계: 전체 통합 리포트 생성 중... (개별 리포트 {len(report_files)}개 통합)")
        try:
            report_generator.consolidate_daily_reports()
            logging.info("✅ 1단계: 전체 통합 리포트 생성 완료")
            
            # 생성된 전체 통합 리포트 확인
            updated_files = os.listdir(processing_dir)
            full_reports = [f for f in updated_files if f.startswith('전체_통합_리포트_') and f.endswith('.xlsx')]
            logging.info(f"📊 생성된 전체 통합 리포트들 ({len(full_reports)}개): {full_reports}")
        except Exception as e:
            logging.error(f"❌ 1단계 실패: 전체 통합 리포트 생성 중 오류: {e}")
            import traceback
            logging.error(f"📚 스택 트레이스: {traceback.format_exc()}")
    else:
        logging.info("ℹ️ 1단계 스킵: 개별 리포트가 없어서 전체 통합 리포트를 생성하지 않습니다.")
    
    # 2단계: 모든 원본 파일들을 원본_보관함으로 이동
    if source_files:
        logging.info(f"🔄 2단계: 원본 파일들을 원본_보관함으로 이동 중... ({len(source_files)}개)")
        try:
            move_source_files_to_archive()
            logging.info("✅ 2단계: 원본 파일 이동 완료")
        except Exception as e:
            logging.error(f"❌ 2단계 실패: 원본 파일 이동 중 오류: {e}")
    else:
        logging.info("ℹ️ 2단계 스킵: 이동할 원본 파일이 없습니다.")
    
    # 3단계: 모든 리포트 파일들을 리포트보관함으로 이동
    logging.info("🔄 3단계: 리포트 파일들을 리포트보관함으로 이동 중...")
    try:
        # 이동 전 작업폴더 내 리포트 파일들 다시 확인
        current_files = os.listdir(processing_dir)
        current_reports = [f for f in current_files if f.endswith('.xlsx') and '통합_리포트' in f and not f.startswith('~')]
        logging.info(f"📊 이동할 리포트 파일들 ({len(current_reports)}개): {current_reports}")
        
        move_reports_to_archive()
        logging.info("✅ 3단계: 리포트 파일 이동 완료")
        
        # 리포트보관함 확인
        report_archive_dir = config.get_report_archive_dir()
        if os.path.exists(report_archive_dir):
            archived_reports = [f for f in os.listdir(report_archive_dir) if f.endswith('.xlsx')]
            logging.info(f"📁 리포트보관함 내 파일들 ({len(archived_reports)}개): {archived_reports}")
        else:
            logging.warning(f"❌ 리포트보관함이 존재하지 않습니다: {report_archive_dir}")
            
    except Exception as e:
        logging.error(f"❌ 3단계 실패: 리포트 파일 이동 중 오류: {e}")
        import traceback
        logging.error(f"📚 스택 트레이스: {traceback.format_exc()}")
    
    logging.info("🏁 ===== 최종 정리 작업 완료 =====")

def move_source_files_to_archive():
    """작업폴더의 모든 원본 파일들(상품성과, 주문조회)을 원본_보관함으로 이동합니다."""
    processing_dir = config.get_processing_dir()
    archive_dir = config.get_archive_dir()
    
    if not os.path.exists(processing_dir):
        return
    
    # 원본 파일들 찾기 (통합_리포트가 아닌 파일들)
    source_files = [f for f in os.listdir(processing_dir) 
                   if f.endswith('.xlsx') and '통합_리포트' not in f and not f.startswith('~')]
    
    if not source_files:
        logging.info("이동할 원본 파일이 없습니다.")
        return
    
    logging.info(f"--- 원본 파일들을 원본_보관함으로 이동 시작 ({len(source_files)}개 파일) ---")
    
    for source_file in source_files:
        try:
            src_path = os.path.join(processing_dir, source_file)
            dst_path = os.path.join(archive_dir, source_file)
            shutil.move(src_path, dst_path)
            logging.info(f"원본 파일 이동 완료: {source_file}")
        except Exception as e:
            logging.error(f"원본 파일 이동 실패 ({source_file}): {e}")
    
    logging.info("--- 원본 파일 이동 완료 ---")

def move_reports_to_archive():
    """작업폴더의 리포트 파일들을 리포트보관함으로 이동합니다."""
    logging.info("📦 ===== 리포트 파일 이동 시작 =====")
    
    processing_dir = config.get_processing_dir()
    report_archive_dir = config.get_report_archive_dir()
    
    logging.info(f"📁 작업폴더: {processing_dir}")
    logging.info(f"📁 리포트보관함: {report_archive_dir}")
    
    if not os.path.exists(processing_dir):
        logging.warning(f"❌ 작업폴더가 존재하지 않습니다: {processing_dir}")
        return
    
    # 리포트보관함 폴더 생성 확인
    if not os.path.exists(report_archive_dir):
        try:
            os.makedirs(report_archive_dir, exist_ok=True)
            logging.info(f"✅ 리포트보관함 폴더 생성: {report_archive_dir}")
        except Exception as e:
            logging.error(f"❌ 리포트보관함 폴더 생성 실패: {e}")
            return
    
    # 리포트 파일들 찾기 (통합_리포트로 시작하는 파일들)
    try:
        all_files = os.listdir(processing_dir)
        report_files = [f for f in all_files if f.endswith('.xlsx') and '통합_리포트' in f and not f.startswith('~')]
        logging.info(f"📊 찾은 리포트 파일들 ({len(report_files)}개): {report_files}")
        
        # 추가로 일일_통합_리포트와 주간_통합_리포트도 포함
        additional_reports = [f for f in all_files if f.endswith('.xlsx') and ('일일_통합_리포트' in f or '주간_통합_리포트' in f) and not f.startswith('~')]
        if additional_reports:
            logging.info(f"📈 추가 통합 리포트들 ({len(additional_reports)}개): {additional_reports}")
            report_files.extend(additional_reports)
            # 중복 제거
            report_files = list(set(report_files))
            
    except Exception as e:
        logging.error(f"❌ 작업폴더 읽기 오류: {e}")
        return
    
    if not report_files:
        logging.info("ℹ️ 이동할 리포트 파일이 없습니다.")
        # 작업폴더 전체 파일 목록 로그로 확인
        try:
            all_files = os.listdir(processing_dir)
            xlsx_files = [f for f in all_files if f.endswith('.xlsx')]
            logging.info(f"🔍 작업폴더 내 Excel 파일들: {xlsx_files}")
        except:
            pass
        return
    
    logging.info(f"🔄 리포트 파일들을 리포트보관함으로 이동 시작 (총 {len(report_files)}개 파일)")
    
    moved_count = 0
    failed_count = 0
    
    for report_file in report_files:
        try:
            src_path = os.path.join(processing_dir, report_file)
            dst_path = os.path.join(report_archive_dir, report_file)
            
            # 원본 파일 존재 여부 확인
            if not os.path.exists(src_path):
                logging.error(f"❌ 원본 파일이 존재하지 않음: {report_file}")
                failed_count += 1
                continue
                
            logging.info(f"🔄 이동 시작: {report_file}")
            
            # 이미 같은 이름의 파일이 존재하는 경우에만 백업 (과도한 백업 방지)
            if os.path.exists(dst_path):
                # 파일 크기나 수정 시간이 다른 경우에만 백업
                src_stat = os.path.getsize(src_path)
                dst_stat = os.path.getsize(dst_path)
                
                if src_stat != dst_stat:  # 크기가 다르면 새로운 데이터
                    timestamp = datetime.datetime.now().strftime("_%Y%m%d_%H%M%S")
                    name, ext = os.path.splitext(report_file)
                    backup_name = f"{name}_backup{timestamp}{ext}"
                    backup_path = os.path.join(report_archive_dir, backup_name)
                    shutil.move(dst_path, backup_path)
                    logging.info(f"📋 기존 리포트 백업: {backup_name}")
                else:
                    # 같은 크기면 덮어쓰기 (백업하지 않음)
                    os.remove(dst_path)
                    logging.info(f"🔄 동일한 리포트 덮어쓰기: {report_file}")
            
            # 파일 이동 실행
            shutil.move(src_path, dst_path)
            
            # 이동 검증
            if os.path.exists(dst_path) and not os.path.exists(src_path):
                logging.info(f"✅ 리포트 이동 완료: {report_file}")
                moved_count += 1
            else:
                logging.error(f"❌ 이동 검증 실패: {report_file}")
                failed_count += 1
                
        except Exception as e:
            logging.error(f"❌ 리포트 이동 실패 ({report_file}): {e}")
            import traceback
            logging.error(f"🔍 상세 오류: {traceback.format_exc()}")
            failed_count += 1
    
    # 이동 결과 요약
    logging.info(f"📊 리포트 이동 결과:")
    logging.info(f"   ✅ 성공: {moved_count}개")
    logging.info(f"   ❌ 실패: {failed_count}개")
    
    # 리포트보관함 최종 상태 확인
    try:
        archived_files = [f for f in os.listdir(report_archive_dir) if f.endswith('.xlsx')]
        logging.info(f"📁 리포트보관함 최종 상태: {len(archived_files)}개 파일")
        if archived_files:
            logging.info(f"📋 보관된 파일들: {archived_files}")
    except Exception as e:
        logging.error(f"❌ 리포트보관함 상태 확인 실패: {e}")
    
    logging.info("🎯 ===== 리포트 파일 이동 완료 =====")
    
    if moved_count == 0 and len(report_files) > 0:
        logging.warning("⚠️ 모든 리포트 파일 이동이 실패했습니다. 권한이나 경로를 확인해주세요.")

def initialize_folders():
    """필요한 모든 폴더가 존재하는지 확인하고 없으면 생성합니다."""
    if not os.path.exists(config.get_processing_dir()): os.makedirs(config.get_processing_dir())
    if not os.path.exists(config.get_archive_dir()): os.makedirs(config.get_archive_dir())
    if not os.path.exists(config.get_report_archive_dir()): os.makedirs(config.get_report_archive_dir())

def start_monitoring():
    """파일 시스템 모니터링을 시작하고, stop.flag 파일이 생기면 중지합니다."""
    initialize_folders()
    # 시작 시 혹시 남아있을지 모르는 플래그 파일 삭제
    if os.path.exists(STOP_FLAG_FILE):
        os.remove(STOP_FLAG_FILE)

    process_existing_files()
    
    logging.info("\n===== 스마트 폴더 실시간 모니터링 시작 =====")
    logging.info(f"- 감시 대상: {config.DOWNLOAD_DIR} (하위 폴더 포함)")
    logging.info("- 파일을 각 스토어 폴더에 넣으면 처리가 시작됩니다.")
    
    event_handler = FileProcessorHandler()
    observer = Observer()
    observer.schedule(event_handler, config.DOWNLOAD_DIR, recursive=True)
    observer.start()

    try:
        while True:
            if os.path.exists(STOP_FLAG_FILE):
                logging.info("'stop.flag' 파일 감지. 모니터링을 중지합니다.")
                break
            time.sleep(1)
    finally:
        observer.stop()
        observer.join() # 스레드가 완전히 종료될 때까지 대기
        if os.path.exists(STOP_FLAG_FILE):
            os.remove(STOP_FLAG_FILE)
        logging.info("\n===== 모니터링이 정상적으로 종료되었습니다. =====")
