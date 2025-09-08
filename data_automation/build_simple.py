#!/usr/bin/env python3
"""
판매 데이터 자동화 애플리케이션 PyInstaller 빌드 스크립트
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
    print(f"작업 디렉토리: {current_dir}")
    
    # 필수 파일 존재 확인
    main_script = "desktop_app.py"
    if not Path(main_script).exists():
        print(f"ERROR: 메인 스크립트를 찾을 수 없습니다: {main_script}")
        return False
    
    # modules 폴더 확인
    modules_dir = Path("modules")
    if not modules_dir.exists():
        print(f"ERROR: modules 폴더를 찾을 수 없습니다: {modules_dir}")
        return False
    
    print("필수 파일 확인 완료")
    
    # 기존 빌드 파일들 정리
    print("기존 빌드 파일 정리 중...")
    cleanup_dirs = ["build", "dist", "__pycache__"]
    for cleanup_dir in cleanup_dirs:
        if Path(cleanup_dir).exists():
            shutil.rmtree(cleanup_dir)
            print(f"  삭제: {cleanup_dir}")
    
    # .spec 파일 삭제
    spec_files = list(Path.cwd().glob("*.spec"))
    for spec_file in spec_files:
        spec_file.unlink()
        print(f"  삭제: {spec_file}")
    
    print("정리 완료")
    
    # PyInstaller 명령어 구성
    print("PyInstaller 설정 중...")
    
    pyinstaller_args = [
        "pyinstaller",
        "--onefile",                    # 단일 exe 파일로 패키징
        "--windowed",                   # 콘솔 창 숨김 (GUI 애플리케이션)
        "--clean",                      # 임시 파일 정리
        "--noconfirm",                  # 덮어쓰기 확인 안함
        f"--name=판매데이터자동화_Material3",  # exe 파일명
        "--add-data=modules;modules",   # modules 폴더 포함
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
        "--collect-all=qt_material",
        "--collect-all=qtawesome", 
        "--collect-all=pyqtdarktheme",
        main_script
    ]
    
    # 마진정보.xlsx 파일이 있으면 포함
    margin_file = Path("마진정보.xlsx")
    if margin_file.exists():
        pyinstaller_args.insert(-1, "--add-data=마진정보.xlsx;.")
        print("마진정보.xlsx 파일 포함됨")
    
    print("PyInstaller 명령어 준비 완료")
    
    # PyInstaller 실행
    print("빌드 시작... (시간이 소요될 수 있습니다)")
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
            print("빌드 성공!")
            
            # 생성된 파일 확인
            exe_path = Path("dist") / "판매데이터자동화_Material3.exe"
            if exe_path.exists():
                file_size = exe_path.stat().st_size / (1024 * 1024)  # MB
                print(f"생성된 파일: {exe_path}")
                print(f"파일 크기: {file_size:.1f} MB")
                
                # 마진정보.xlsx 파일 복사 (없으면)
                dist_margin_file = Path("dist") / "마진정보.xlsx"
                if margin_file.exists() and not dist_margin_file.exists():
                    shutil.copy2(margin_file, dist_margin_file)
                    print(f"마진정보.xlsx 파일 복사 완료")
                
                print("\n배포 완료!")
                print("=" * 60)
                print("실행 방법:")
                print("  1. dist 폴더로 이동")
                print("  2. '판매데이터자동화_Material3.exe' 실행")
                print("=" * 60)
                
                return True
            else:
                print("ERROR: exe 파일을 찾을 수 없습니다.")
                return False
                
        else:
            print("ERROR: 빌드 실패!")
            print(f"Return code: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"ERROR: 빌드 중 오류 발생: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n성공적으로 완료되었습니다!")
        print("dist 폴더에서 exe 파일을 확인하세요.")
    else:
        print("\n빌드에 실패했습니다.")
        print("오류를 확인하고 다시 시도해 주세요.")
    
    input("\nPress Enter to exit...")