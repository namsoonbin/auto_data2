#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
순위 추적 기능 통합 테스트 스크립트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

try:
    print("=" * 60)
    print("순위 추적 기능 통합 테스트")
    print("=" * 60)

    # 1. 기본 모듈들 테스트
    print("\n1. 기본 모듈 import 테스트...")
    from modules.settings import get_settings
    print("   ✅ settings 모듈 import 성공")

    from modules.rank_tracker.naver_api import NaverShopAPI
    print("   ✅ naver_api 모듈 import 성공")

    from modules.rank_tracker.database import RankDatabase
    print("   ✅ database 모듈 import 성공")

    from modules.rank_tracker.scheduler import RankScheduler
    print("   ✅ scheduler 모듈 import 성공")

    from modules.rank_tracker.rank_calculator import RankCalculator
    print("   ✅ rank_calculator 모듈 import 성공")

    # 2. UI 모듈 테스트
    print("\n2. UI 모듈 import 테스트...")
    from modules.ui_rank_tracking import RankTrackingWidget, KeywordManagementDialog
    print("   ✅ ui_rank_tracking 모듈 import 성공")

    # 3. 설정 로드 테스트
    print("\n3. 설정 시스템 테스트...")
    settings = get_settings()
    rank_settings = settings.rank_tracking
    print(f"   ✅ 순위 추적 설정 로드 성공")
    print(f"      - API 호출 간격: {rank_settings.api_rate_limit_min}~{rank_settings.api_rate_limit_max}초")
    print(f"      - 스케줄 간격: {rank_settings.schedule_interval_minutes}분")
    print(f"      - 최대 스캔 깊이: {rank_settings.max_scan_depth}")
    print(f"      - 재시도 횟수: {rank_settings.retry_attempts}")

    # 4. 데이터베이스 초기화 테스트
    print("\n4. 데이터베이스 초기화 테스트...")
    try:
        db = RankDatabase()
        print("   ✅ 데이터베이스 초기화 성공")
        print(f"      - DB 파일: {rank_settings.db_file_name}")

        # 테이블 존재 여부 확인
        targets = db.get_active_targets()
        print(f"   ✅ 추적 대상 조회 성공 ({len(targets)}개)")

    except Exception as e:
        print(f"   ❌ 데이터베이스 오류: {e}")

    # 5. 메인 앱 통합 테스트
    print("\n5. 메인 앱 통합 테스트...")
    try:
        from desktop_app import ModernSalesAutomationApp, RANK_TRACKING_AVAILABLE
        print(f"   ✅ 메인 앱 import 성공")
        print(f"   ✅ 순위 추적 기능 사용 가능: {RANK_TRACKING_AVAILABLE}")

        if RANK_TRACKING_AVAILABLE:
            print("   ✅ 순위 추적 탭이 메인 앱에 통합되어 있습니다")
        else:
            print("   ⚠️ 순위 추적 기능을 사용할 수 없습니다")

    except Exception as e:
        print(f"   ❌ 메인 앱 통합 오류: {e}")

    print("\n" + "=" * 60)
    print("테스트 완료! 🎉")
    print("=" * 60)

    # 간단한 사용법 안내
    print("\n📋 순위 추적 기능 사용 방법:")
    print("1. 메인 애플리케이션 실행")
    print("2. '🔍 순위 추적' 탭 클릭")
    print("3. API 설정에서 네이버 클라이언트 ID/Secret 입력")
    print("4. '📝 키워드 관리'에서 추적할 상품과 키워드 등록")
    print("5. '🔍 수동 확인' 또는 '⏰ 자동 추적 시작' 실행")

    print("\n🔗 관련 파일:")
    print(f"   - 설정 파일: settings.json")
    print(f"   - 순위 데이터: {rank_settings.db_file_name}")
    print(f"   - 로그 파일: sales_automation.log")

except Exception as e:
    print(f"❌ 테스트 실패: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)