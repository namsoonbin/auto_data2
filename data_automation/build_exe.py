#!/usr/bin/env python3
"""
판매 데이터 자동화 애플리케이션 PyInstaller 빌드 스크립트
Material Design 3 UI가 적용된 최종 버전
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def main():
    """PyInstaller를 사용하여 exe 파일 생성"""
    
    print("판매 데이터 자동화 애플리케이션 빌드 시작...")
    print("=" * 60)
    
    # 현재 디렉토리 확인
    current_dir = Path.cwd()
    print(f"📁 작업 디렉토리: {current_dir}")
    
    # 필수 파일 존재 확인
    main_script = "desktop_app.py"
    if not Path(main_script).exists():
        print(f"❌ 메인 스크립트를 찾을 수 없습니다: {main_script}")
        return False
    
    # modules 폴더 확인
    modules_dir = Path("modules")
    if not modules_dir.exists():
        print(f"❌ modules 폴더를 찾을 수 없습니다: {modules_dir}")
        return False
    
    print("✅ 필수 파일 확인 완료")
    
    # 기존 빌드 파일들 정리
    print("\n🧹 기존 빌드 파일 정리 중...")
    cleanup_dirs = ["build", "dist", "__pycache__"]
    for cleanup_dir in cleanup_dirs:
        if Path(cleanup_dir).exists():
            shutil.rmtree(cleanup_dir)
            print(f"  🗑️ 삭제: {cleanup_dir}")
    
    # .spec 파일 삭제
    spec_files = list(Path.cwd().glob("*.spec"))
    for spec_file in spec_files:
        spec_file.unlink()
        print(f"  🗑️ 삭제: {spec_file}")
    
    print("✅ 정리 완료")
    
    # PyInstaller 명령어 구성
    print("\n⚙️ PyInstaller 설정 중...")
    
    pyinstaller_args = [
        "pyinstaller",
        "--onefile",                    # 단일 exe 파일로 패키징
        "--windowed",                   # 콘솔 창 숨김 (GUI 애플리케이션)
        "--clean",                      # 임시 파일 정리
        "--noconfirm",                  # 덮어쓰기 확인 안함
        f"--name=판매데이터자동화_Material3",  # exe 파일명
        "--add-data=modules;modules",   # modules 폴더 포함
        "--add-data=마진정보.xlsx;.",     # 마진정보 파일 포함
        "--hidden-import=pandas",
        "--hidden-import=openpyxl", 
        "--hidden-import=xlsxwriter",
        "--hidden-import=watchdog",
        "--hidden-import=numpy",
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=msoffcrypto",
        "--hidden-import=cryptography",
        # Material Design 3 관련 (선택적)
        "--hidden-import=qt_material",
        "--hidden-import=qtawesome",
        "--hidden-import=pyqtdarktheme",
        # 콘솔 출력도 보려면 아래 주석 해제
        # "--console",
        main_script
    ]
    
    print("📋 PyInstaller 명령어:")
    for arg in pyinstaller_args:
        print(f"   {arg}")
    
    # PyInstaller 실행
    print(f"\n🔨 빌드 시작... (시간이 소요될 수 있습니다)")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            pyinstaller_args,
            capture_output=False,  # 실시간 출력 보기
            text=True,
            cwd=current_dir
        )
        
        if result.returncode == 0:
            print("=" * 60)
            print("✅ 빌드 성공!")
            
            # 생성된 파일 확인
            exe_path = Path("dist") / "판매데이터자동화_Material3.exe"
            if exe_path.exists():
                file_size = exe_path.stat().st_size / (1024 * 1024)  # MB
                print(f"📦 생성된 파일: {exe_path}")
                print(f"📏 파일 크기: {file_size:.1f} MB")
                
                # 추가 파일들 복사
                print("\n📋 추가 파일 복사 중...")
                
                # 마진정보.xlsx가 dist 폴더에 있는지 확인하고 없으면 복사
                margin_file = Path("마진정보.xlsx")
                dist_margin_file = Path("dist") / "마진정보.xlsx"
                
                if margin_file.exists() and not dist_margin_file.exists():
                    shutil.copy2(margin_file, dist_margin_file)
                    print(f"  ✅ 복사: {margin_file} -> {dist_margin_file}")
                
                # README 파일 생성
                create_readme()
                
                print("\n🎉 배포 완료!")
                print("=" * 60)
                print("📍 실행 방법:")
                print(f"   1. dist 폴더로 이동")
                print(f"   2. '판매데이터자동화_Material3.exe' 실행")
                print(f"   3. 마진정보.xlsx 파일이 같은 폴더에 있는지 확인")
                print("=" * 60)
                
                return True
            else:
                print("❌ exe 파일을 찾을 수 없습니다.")
                return False
                
        else:
            print("❌ 빌드 실패!")
            print(f"Return code: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ 빌드 중 오류 발생: {str(e)}")
        return False

def create_readme():
    """배포용 README 파일 생성"""
    readme_content = """# 판매 데이터 자동화 애플리케이션 v3.0
## Material Design 3 Edition

### 🎯 개요
네이버 스마트스토어 판매 데이터를 자동으로 처리하고 분석하는 현대적인 GUI 애플리케이션입니다.

### ✨ 주요 기능
- 🎨 **Material Design 3 UI**: 현대적이고 직관적인 사용자 인터페이스
- 🌙 **다크/라이트 테마**: 자동 시스템 테마 감지 및 수동 전환
- 📊 **실시간 통계 대시보드**: 처리 현황을 한눈에 확인
- 🔐 **암호 보호된 Excel 지원**: 주문조회 파일 자동 처리
- 💰 **GUI 리워드 관리**: 상품별 리워드 설정 시스템
- 🛒 **GUI 가구매 관리**: 상품별 가구매 개수 설정
- 🔄 **자동/수동 처리**: 폴더 감시 자동화 + 수동 처리 모드

### 🚀 사용법
1. **판매데이터자동화_Material3.exe** 실행
2. 다운로드 폴더 선택 (네이버 스마트스토어에서 다운로드한 파일들이 저장될 위치)
3. 주문조회 파일 암호 입력 (기본: 1234)
4. **자동화 시작** 또는 **작업폴더 처리** 버튼 클릭

### 📁 필수 파일
- **마진정보.xlsx**: 상품 마진 정보 (반드시 exe와 같은 폴더에 위치)
- 네이버 스마트스토어 다운로드 파일들:
  - 상품성과 파일
  - 주문조회 파일

### ⚙️ 고급 설정
- **💰 리워드 관리**: 날짜별/상품별 리워드 금액 설정
- **🛒 가구매 관리**: 상품별 가구매 개수 설정
- **🌙 테마 전환**: 다크/라이트 모드 수동 전환

### 📊 생성되는 리포트
- 일별 통합 리포트 (매출, 순이익, 광고비율 등)
- 옵션별 상세 분석
- 환불 데이터 정확 반영

### 🔧 시스템 요구사항
- Windows 10/11 64-bit
- 최소 4GB RAM 권장
- 500MB 이상 여유 저장공간

### 📞 문의
기술적 문제나 개선 요청사항이 있으시면 연락 주세요.

---
**개발**: Material Design Team | **버전**: 3.0 | **빌드 날짜**: 2025-09-08
"""
    
    readme_path = Path("dist") / "README.txt"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"  ✅ 생성: {readme_path}")

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 성공적으로 완료되었습니다!")
        print("dist 폴더에서 exe 파일을 확인하세요.")
    else:
        print("\n❌ 빌드에 실패했습니다.")
        print("오류를 확인하고 다시 시도해 주세요.")
    
    input("\nPress Enter to exit...")