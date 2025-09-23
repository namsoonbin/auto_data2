# -*- coding: utf-8 -*-
"""
자동 업데이트 시스템
Context7 2025 모범 사례: 안전한 자동 업데이트, 버전 관리, 백업/복원
"""

import os
import sys
import json
import shutil
import hashlib
import zipfile
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from .logger import get_logger

logger = get_logger("Updater")


@dataclass
class VersionInfo:
    """버전 정보"""
    version: str
    build_date: str
    download_url: str
    file_size: int
    checksum: str
    release_notes: str
    required: bool = False


class UpdaterError(Exception):
    """업데이터 전용 예외"""
    pass


class SalesAutomationUpdater:
    """판매 자동화 프로그램 업데이터"""

    def __init__(
        self,
        current_version: str = "1.0.0",
        update_server_url: str = "https://api.github.com/repos/your-repo/releases",
        backup_dir: Optional[Path] = None
    ):
        self.current_version = current_version
        self.update_server_url = update_server_url
        self.backup_dir = backup_dir or Path("backups")
        self.temp_dir = Path(tempfile.gettempdir()) / "sales_automation_update"

        # 업데이트 설정
        self.check_interval_hours = 24  # 24시간마다 확인
        self.auto_download = True
        self.auto_install = False  # 기본적으로 수동 설치

        # 현재 실행 파일 경로
        self.current_exe_path = self._get_current_exe_path()

        logger.info(
            "업데이터 초기화",
            current_version=self.current_version,
            exe_path=str(self.current_exe_path),
            update_server=self.update_server_url
        )

    def _get_current_exe_path(self) -> Path:
        """현재 실행 파일 경로 반환"""
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller로 빌드된 경우
            return Path(sys.executable)
        else:
            # 개발 환경
            return Path(__file__).parent.parent / "dist" / "판매데이터자동화.exe"

    def check_for_updates(self) -> Optional[VersionInfo]:
        """업데이트 확인"""
        if not REQUESTS_AVAILABLE:
            logger.warning("requests 라이브러리가 설치되지 않아 업데이트 확인을 건너뜁니다")
            return None

        try:
            logger.info("업데이트 확인 시작")

            # GitHub API 또는 업데이트 서버에서 최신 버전 정보 가져오기
            response = requests.get(self.update_server_url, timeout=10)
            response.raise_for_status()

            releases = response.json()
            if not releases:
                logger.info("사용 가능한 업데이트가 없습니다")
                return None

            latest_release = releases[0]  # 최신 릴리스
            latest_version = latest_release["tag_name"].lstrip("v")

            # 버전 비교
            if self._is_newer_version(latest_version, self.current_version):
                logger.info(
                    "새 버전 발견",
                    current_version=self.current_version,
                    latest_version=latest_version
                )

                # 다운로드 URL 찾기
                download_url = None
                file_size = 0
                for asset in latest_release.get("assets", []):
                    if asset["name"].endswith(".exe"):
                        download_url = asset["browser_download_url"]
                        file_size = asset["size"]
                        break

                if not download_url:
                    logger.error("업데이트 파일을 찾을 수 없습니다")
                    return None

                return VersionInfo(
                    version=latest_version,
                    build_date=latest_release["published_at"],
                    download_url=download_url,
                    file_size=file_size,
                    checksum="",  # GitHub에서 제공하지 않음
                    release_notes=latest_release.get("body", ""),
                    required=False
                )

            else:
                logger.info("현재 버전이 최신입니다")
                return None

        except requests.RequestException as e:
            logger.error("업데이트 확인 실패", error=str(e))
            return None
        except Exception as e:
            logger.error("업데이트 확인 중 예상치 못한 오류", error=str(e))
            return None

    def _is_newer_version(self, latest: str, current: str) -> bool:
        """버전 비교 (간단한 구현)"""
        try:
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]

            # 길이를 맞춤
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))

            return latest_parts > current_parts
        except ValueError:
            # 버전 파싱 실패 시 문자열 비교
            return latest > current

    def download_update(self, version_info: VersionInfo) -> Optional[Path]:
        """업데이트 파일 다운로드"""
        if not REQUESTS_AVAILABLE:
            logger.error("requests 라이브러리가 설치되지 않아 다운로드할 수 없습니다")
            return None

        try:
            # 임시 디렉토리 생성
            self.temp_dir.mkdir(parents=True, exist_ok=True)

            download_path = self.temp_dir / f"update_{version_info.version}.exe"

            logger.info(
                "업데이트 다운로드 시작",
                version=version_info.version,
                url=version_info.download_url,
                download_path=str(download_path)
            )

            # 파일 다운로드
            response = requests.get(version_info.download_url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded_size += len(chunk)

                    # 진행률 로그 (10% 단위)
                    if total_size > 0:
                        progress = (downloaded_size / total_size) * 100
                        if downloaded_size % (total_size // 10) < 8192:
                            logger.info(f"다운로드 진행률: {progress:.1f}%")

            # 파일 크기 검증
            actual_size = download_path.stat().st_size
            if version_info.file_size > 0 and actual_size != version_info.file_size:
                logger.error(
                    "파일 크기 불일치",
                    expected=version_info.file_size,
                    actual=actual_size
                )
                download_path.unlink()
                return None

            logger.info("업데이트 다운로드 완료", file_size=actual_size)
            return download_path

        except requests.RequestException as e:
            logger.error("업데이트 다운로드 실패", error=str(e))
            return None
        except Exception as e:
            logger.error("다운로드 중 예상치 못한 오류", error=str(e))
            return None

    def create_backup(self) -> bool:
        """현재 버전 백업"""
        try:
            # 백업 디렉토리 생성
            self.backup_dir.mkdir(parents=True, exist_ok=True)

            backup_name = f"backup_{self.current_version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.exe"
            backup_path = self.backup_dir / backup_name

            logger.info(
                "백업 생성 시작",
                source=str(self.current_exe_path),
                backup=str(backup_path)
            )

            # 현재 실행 파일 백업
            shutil.copy2(self.current_exe_path, backup_path)

            # 백업 파일 크기 검증
            if backup_path.stat().st_size == self.current_exe_path.stat().st_size:
                logger.info("백업 생성 완료")
                return True
            else:
                logger.error("백업 파일 크기 불일치")
                backup_path.unlink()
                return False

        except Exception as e:
            logger.error("백업 생성 실패", error=str(e))
            return False

    def install_update(self, update_file: Path, create_backup: bool = True) -> bool:
        """업데이트 설치"""
        try:
            # 백업 생성
            if create_backup and not self.create_backup():
                logger.error("백업 생성 실패로 업데이트를 중단합니다")
                return False

            logger.info(
                "업데이트 설치 시작",
                update_file=str(update_file),
                target=str(self.current_exe_path)
            )

            # 업데이트 파일 검증
            if not update_file.exists():
                logger.error("업데이트 파일이 존재하지 않습니다")
                return False

            # 현재 실행 중인 파일은 직접 교체할 수 없으므로
            # 배치 스크립트나 별도 프로세스 필요
            batch_script = self._create_update_script(update_file, self.current_exe_path)

            if batch_script:
                logger.info("업데이트 스크립트 생성 완료")
                logger.info("프로그램이 종료된 후 자동으로 업데이트됩니다")
                return True
            else:
                logger.error("업데이트 스크립트 생성 실패")
                return False

        except Exception as e:
            logger.error("업데이트 설치 실패", error=str(e))
            return False

    def _create_update_script(self, update_file: Path, target_file: Path) -> Optional[Path]:
        """업데이트 배치 스크립트 생성"""
        try:
            script_path = self.temp_dir / "update.bat"

            script_content = f"""@echo off
echo 판매 데이터 자동화 업데이트 중...
timeout /t 3 /nobreak > nul

echo 기존 파일 백업 중...
if exist "{target_file}" (
    move "{target_file}" "{target_file}.old"
)

echo 새 버전 설치 중...
move "{update_file}" "{target_file}"

echo 업데이트 완료!
echo 프로그램을 다시 시작해주세요.

echo 임시 파일 정리 중...
del "%~f0"
"""

            with open(script_path, 'w', encoding='cp949') as f:
                f.write(script_content)

            logger.info("업데이트 스크립트 생성", script_path=str(script_path))
            return script_path

        except Exception as e:
            logger.error("업데이트 스크립트 생성 실패", error=str(e))
            return None

    def rollback_update(self) -> bool:
        """업데이트 롤백"""
        try:
            # 가장 최근 백업 파일 찾기
            backup_files = list(self.backup_dir.glob("backup_*.exe"))
            if not backup_files:
                logger.error("롤백할 백업 파일이 없습니다")
                return False

            latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)

            logger.info(
                "업데이트 롤백 시작",
                backup_file=str(latest_backup),
                target=str(self.current_exe_path)
            )

            # 롤백 실행
            rollback_script = self._create_rollback_script(latest_backup, self.current_exe_path)

            if rollback_script:
                logger.info("롤백 스크립트 생성 완료")
                return True
            else:
                logger.error("롤백 스크립트 생성 실패")
                return False

        except Exception as e:
            logger.error("롤백 실패", error=str(e))
            return False

    def _create_rollback_script(self, backup_file: Path, target_file: Path) -> Optional[Path]:
        """롤백 배치 스크립트 생성"""
        try:
            script_path = self.temp_dir / "rollback.bat"

            script_content = f"""@echo off
echo 판매 데이터 자동화 롤백 중...
timeout /t 3 /nobreak > nul

echo 현재 버전 백업 중...
if exist "{target_file}" (
    move "{target_file}" "{target_file}.failed"
)

echo 이전 버전 복원 중...
copy "{backup_file}" "{target_file}"

echo 롤백 완료!
echo 프로그램을 다시 시작해주세요.

del "%~f0"
"""

            with open(script_path, 'w', encoding='cp949') as f:
                f.write(script_content)

            logger.info("롤백 스크립트 생성", script_path=str(script_path))
            return script_path

        except Exception as e:
            logger.error("롤백 스크립트 생성 실패", error=str(e))
            return None

    def cleanup_temp_files(self):
        """임시 파일 정리"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.info("임시 파일 정리 완료")
        except Exception as e:
            logger.error("임시 파일 정리 실패", error=str(e))

    def get_update_status(self) -> Dict[str, Any]:
        """업데이트 상태 정보 반환"""
        return {
            "current_version": self.current_version,
            "update_server": self.update_server_url,
            "requests_available": REQUESTS_AVAILABLE,
            "last_check": datetime.now().isoformat(),
            "backup_dir_exists": self.backup_dir.exists(),
            "backup_count": len(list(self.backup_dir.glob("backup_*.exe"))) if self.backup_dir.exists() else 0
        }