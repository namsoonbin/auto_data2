# -*- coding: utf-8 -*-
"""
기존 리포트 파일들을 새로운 분류 체계로 마이그레이션하는 스크립트
사용법: python migrate_reports.py [다운로드_폴더_경로]
"""
import os
import sys
import shutil
import re
import logging
from datetime import datetime
from modules import config

def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('migration.log', encoding='utf-8')
        ]
    )

def migrate_existing_reports(download_folder=None):
    """기존 리포트 파일들을 분류된 폴더 구조로 마이그레이션"""
    logging.info("🔄 기존 리포트 파일 마이그레이션 시작")
    
    # 다운로드 폴더 설정
    if download_folder:
        config.DOWNLOAD_DIR = download_folder
        logging.info(f"📁 사용자 지정 폴더: {download_folder}")
    elif config.DOWNLOAD_DIR is None:
        logging.error("❌ 다운로드 폴더가 설정되지 않았습니다.")
        return False
    
    report_archive_dir = config.get_report_archive_dir()
    if not os.path.exists(report_archive_dir):
        logging.error(f"❌ 리포트보관함 폴더를 찾을 수 없습니다: {report_archive_dir}")
        return False
    
    # 기존 리포트 파일들 찾기
    all_files = []
    for root, dirs, files in os.walk(report_archive_dir):
        for file in files:
            if file.endswith('.xlsx') and '통합_리포트' in file and not file.startswith('~'):
                all_files.append(os.path.join(root, file))
    
    logging.info(f"📊 발견된 리포트 파일 수: {len(all_files)}")
    
    if not all_files:
        logging.info("ℹ️ 마이그레이션할 리포트 파일이 없습니다.")
        return True
    
    # 마이그레이션 통계
    migrated_count = 0
    skipped_count = 0
    failed_count = 0
    
    for file_path in all_files:
        try:
            filename = os.path.basename(file_path)
            relative_path = os.path.relpath(file_path, report_archive_dir)
            
            # 이미 분류된 폴더에 있는 파일은 건너뛰기
            if any(folder in relative_path for folder in ['개별리포트', '일간통합리포트', '주간통합리포트']):
                logging.info(f"⏭️ 이미 분류됨: {relative_path}")
                skipped_count += 1
                continue
            
            # 리포트 타입 감지
            report_type = config.detect_report_type(filename)
            if report_type == 'unknown':
                logging.warning(f"⚠️ 알 수 없는 리포트 타입: {filename}")
                skipped_count += 1
                continue
            
            # 날짜 추출
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
            if not date_match:
                logging.warning(f"⚠️ 날짜를 찾을 수 없음: {filename}")
                skipped_count += 1
                continue
            
            date_str = date_match.group(1)
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # 새로운 경로 생성
            new_path = config.get_categorized_report_path(report_type, date_obj, filename)
            
            # 이미 동일한 파일이 있는지 확인
            if os.path.exists(new_path):
                # 파일 크기 비교
                if os.path.getsize(file_path) == os.path.getsize(new_path):
                    logging.info(f"📄 동일한 파일 존재, 원본 삭제: {filename}")
                    os.remove(file_path)
                    migrated_count += 1
                    continue
                else:
                    # 다른 파일이면 백업 생성
                    timestamp = datetime.now().strftime("_%Y%m%d_%H%M%S")
                    name, ext = os.path.splitext(filename)
                    backup_name = f"{name}_backup{timestamp}{ext}"
                    backup_path = os.path.join(os.path.dirname(new_path), backup_name)
                    shutil.move(new_path, backup_path)
                    logging.info(f"📋 기존 파일 백업: {backup_name}")
            
            # 파일 이동
            shutil.move(file_path, new_path)
            
            # 이동 확인
            if os.path.exists(new_path) and not os.path.exists(file_path):
                logging.info(f"✅ 마이그레이션 완료: {filename} → {report_type}")
                migrated_count += 1
            else:
                logging.error(f"❌ 마이그레이션 실패: {filename}")
                failed_count += 1
                
        except Exception as e:
            logging.error(f"❌ {os.path.basename(file_path)} 처리 중 오류: {e}")
            failed_count += 1
    
    # 빈 폴더 정리
    cleanup_empty_directories(report_archive_dir)
    
    # 결과 요약
    logging.info("📊 마이그레이션 완료 요약:")
    logging.info(f"   ✅ 성공: {migrated_count}개")
    logging.info(f"   ⏭️ 건너뜀: {skipped_count}개")
    logging.info(f"   ❌ 실패: {failed_count}개")
    
    return failed_count == 0

def cleanup_empty_directories(base_dir):
    """빈 폴더들을 정리"""
    logging.info("🧹 빈 폴더 정리 중...")
    
    for root, dirs, files in os.walk(base_dir, topdown=False):
        # 분류 폴더는 건드리지 않음
        if any(folder in root for folder in ['개별리포트', '일간통합리포트', '주간통합리포트']):
            continue
            
        # 빈 폴더 삭제
        try:
            if not dirs and not files and root != base_dir:
                os.rmdir(root)
                logging.info(f"🗑️ 빈 폴더 삭제: {os.path.relpath(root, base_dir)}")
        except OSError:
            pass  # 폴더가 비어있지 않거나 삭제할 수 없는 경우

def preview_migration(download_folder=None):
    """마이그레이션 미리보기 (실제 이동하지 않음)"""
    logging.info("👁️ 마이그레이션 미리보기 모드")
    
    # 다운로드 폴더 설정
    if download_folder:
        config.DOWNLOAD_DIR = download_folder
    elif config.DOWNLOAD_DIR is None:
        logging.error("❌ 다운로드 폴더가 설정되지 않았습니다.")
        return False
    
    report_archive_dir = config.get_report_archive_dir()
    if not os.path.exists(report_archive_dir):
        logging.error(f"❌ 리포트보관함 폴더를 찾을 수 없습니다: {report_archive_dir}")
        return False
    
    # 기존 리포트 파일들 찾기
    all_files = []
    for root, dirs, files in os.walk(report_archive_dir):
        for file in files:
            if file.endswith('.xlsx') and '통합_리포트' in file and not file.startswith('~'):
                all_files.append(os.path.join(root, file))
    
    logging.info(f"📊 분석 대상 파일 수: {len(all_files)}")
    
    # 타입별 카운트
    type_counts = {'individual': 0, 'daily_consolidated': 0, 'weekly': 0, 'unknown': 0}
    
    for file_path in all_files:
        filename = os.path.basename(file_path)
        relative_path = os.path.relpath(file_path, report_archive_dir)
        
        # 이미 분류된 파일인지 확인
        if any(folder in relative_path for folder in ['개별리포트', '일간통합리포트', '주간통합리포트']):
            continue
        
        report_type = config.detect_report_type(filename)
        type_counts[report_type] += 1
        
        if report_type != 'unknown':
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
            if date_match:
                date_str = date_match.group(1)
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                new_path = config.get_categorized_report_path(report_type, date_obj, filename)
                logging.info(f"📁 {filename} → {os.path.relpath(new_path, report_archive_dir)}")
    
    logging.info("📊 마이그레이션 예상 결과:")
    logging.info(f"   📄 개별리포트: {type_counts['individual']}개")
    logging.info(f"   📊 일간통합리포트: {type_counts['daily_consolidated']}개") 
    logging.info(f"   📈 주간통합리포트: {type_counts['weekly']}개")
    logging.info(f"   ❓ 알 수 없음: {type_counts['unknown']}개")

if __name__ == "__main__":
    setup_logging()
    
    download_folder = None
    preview_mode = False
    
    # 명령행 인수 처리
    for arg in sys.argv[1:]:
        if arg == "--preview":
            preview_mode = True
        elif os.path.exists(arg):
            download_folder = arg
        else:
            print(f"사용법: python migrate_reports.py [--preview] [다운로드_폴더_경로]")
            print(f"  --preview: 실제 이동하지 않고 미리보기만")
            print(f"  다운로드_폴더_경로: 리포트보관함이 있는 폴더")
            sys.exit(1)
    
    try:
        if preview_mode:
            success = preview_migration(download_folder)
        else:
            success = migrate_existing_reports(download_folder)
        
        if success:
            logging.info("🎉 마이그레이션이 성공적으로 완료되었습니다!")
        else:
            logging.error("❌ 마이그레이션 중 오류가 발생했습니다.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logging.info("⏹️ 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"❌ 예상치 못한 오류: {e}")
        sys.exit(1)