# -*- coding: utf-8 -*-
import sys
import os
import logging
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, date
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QTextEdit, QFileDialog, QLabel, QGroupBox, QGridLayout,
    QDialog, QTableWidget, QTableWidgetItem, QDateEdit, QHeaderView,
    QMessageBox, QSpinBox, QFrame, QProgressBar, QCheckBox, QScrollArea,
    QGraphicsDropShadowEffect, QSizePolicy, QDialogButtonBox, QTabWidget
)
from PySide6.QtCore import QThread, Signal, Qt, QDate, QTimer, QSettings
from PySide6.QtGui import QColor, QIcon, QCursor

# Try to import qtawesome for icons
QTAWESOME_AVAILABLE = False
try:
    import qtawesome as qta
    QTAWESOME_AVAILABLE = True
except ImportError:
    pass

# Import the existing modules
from modules import config, file_handler, report_generator, weekly_reporter
from modules.compatibility import set_engine, get_current_engine
from modules.settings import get_settings, set_download_dir, set_polars_enabled, set_order_file_password
from modules.logger import get_logger, setup_app_logging, log_performance
from modules.updater import SalesAutomationUpdater

# 순위 추적 UI 컴포넌트 임포트
try:
    from modules.ui_rank_tracking import RankTrackingWidget
    RANK_TRACKING_AVAILABLE = True
    logging.info("순위 추적 UI 컴포넌트 임포트 성공")
except ImportError as e:
    RANK_TRACKING_AVAILABLE = False
    logging.warning(f"순위 추적 UI 컴포넌트 임포트 실패: {e}")

# Import AI modules
try:
    from modules.analytics import SalesAnalytics
    from modules.recommendations import SmartRecommendationEngine, RecommendationType, Priority
    import polars as pl
    AI_MODULES_AVAILABLE = True
    logging.info("AI 모듈 임포트 성공")
except ImportError as e:
    AI_MODULES_AVAILABLE = False
    logging.warning(f"AI 모듈 임포트 실패: {e}")

# 2025 AI 모듈은 제거됨
NEW_AI_MODULES_AVAILABLE = False

# UI 컴포넌트 임포트 (Context7 모범 사례)
try:
    from modules.ui_components import (
        NotificationManager, WorkflowProgressGuide, SmartTooltipManager,
        UIComponentFactory, WorkflowStep, NotificationType
    )
    UI_COMPONENTS_AVAILABLE = True
    logging.info("UI 컴포넌트 모듈 임포트 성공")
except ImportError as e:
    UI_COMPONENTS_AVAILABLE = False
    logging.warning(f"UI 컴포넌트 모듈 임포트 실패: {e}")

# --- UI Styling Classes ---

class MaterialColors:
    PRIMARY = "#2563eb"
    SUCCESS = "#059669"
    WARNING = "#ea580c"
    ERROR = "#dc2626"
    DARK_BG = "#1a1a1a"
    DARK_TEXT = "#ffffff"

class AppleStyleButton(QPushButton):
    def __init__(self, text, icon_name=None, color=MaterialColors.PRIMARY, parent=None):
        super().__init__(text, parent)
        if icon_name and QTAWESOME_AVAILABLE:
            try:
                icon = qta.icon(icon_name, color='white')
                self.setIcon(icon)
            except Exception:
                pass

        self.setMinimumSize(100, 38)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        c = QColor(color)
        self.setStyleSheet(f"""
            QPushButton {{ background-color: {color}; color: white; border: none; border-radius: 8px; padding: 10px 16px; font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ background-color: {c.lighter(110).name()}; }}
            QPushButton:pressed {{ background-color: {c.darker(110).name()}; }}
            QPushButton:disabled {{ background-color: #E0E0E0; color: #999999; }}
        """)

class ModernLogViewer(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setMinimumHeight(200)
        self.setStyleSheet(f'''
            QTextEdit {{ background-color: {MaterialColors.DARK_BG}; color: {MaterialColors.DARK_TEXT}; font-family: 'Consolas', monospace; font-size: 12px; border: 1px solid #374151; border-radius: 8px; padding: 12px; }}
        ''')

class ModernDataCard(QFrame):
    def __init__(self, title, value, icon_name, color=MaterialColors.PRIMARY, tooltip=""):
        super().__init__()
        self.color = color
        self.setMinimumHeight(160)
        self.setMaximumHeight(200)
        if tooltip:
            self.setToolTip(tooltip)

        # 확실하게 보이는 스타일 적용
        self.setStyleSheet(f"""
            ModernDataCard {{
                background-color: #FFFFFF;
                border: 3px solid #DDDDDD;
                border-radius: 10px;
                padding: 15px;
            }}
            ModernDataCard:hover {{
                border-color: {self.color};
                background-color: #F5F5F5;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        # 헤더 (아이콘 + 제목)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        # 크고 명확한 이모지 아이콘
        icon_map = {
            "fa5s.file-alt": "📄",
            "fa5s.dollar-sign": "💰", 
            "fa5s.chart-line": "📈",
            "fa5s.exclamation-triangle": "⚠️"
        }
        icon_text = icon_map.get(icon_name, "📊")
        icon_label = QLabel(icon_text)
        icon_label.setStyleSheet("""
            font-size: 24px;
            padding: 0;
            margin: 0;
        """)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: #333333;
            margin: 0;
            padding: 0;
            background-color: transparent;
        """)

        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # 값 표시 - 매우 명확하게
        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #000000;
            margin: 0;
            padding: 8px 0;
            background-color: transparent;
        """)
        self.value_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.value_label)
        layout.addStretch()

    def update_value(self, new_value):
        self.value_label.setText(str(new_value))

# --- Worker Threads ---

class ModernWorker(QThread):
    output_signal = Signal(str)
    finished_signal = Signal()
    error_signal = Signal(str)
    stats_signal = Signal(dict)  # 통계 업데이트 시그널 추가

    def __init__(self, download_folder, password="1234"):
        super().__init__()
        self.download_folder = download_folder
        self.password = password

    def run(self):
        try:
            config.DOWNLOAD_DIR = self.download_folder
            config.ORDER_FILE_PASSWORD = self.password
            self.output_signal.emit("[INFO] 자동화 시작!")
            file_handler.start_monitoring()
            
            # 모니터링이 완료되면 통계 수집
            self.collect_and_send_stats()
            
        except Exception as e:
            self.error_signal.emit(f"[ERROR] 모니터링 중 오류: {str(e)}")
        finally:
            self.finished_signal.emit()

    def collect_and_send_stats(self):
        """통계 정보를 수집해서 시그널로 전송"""
        try:
            import glob
            import pandas as pd
            
            # 처리된 리포트 파일들 찾기 (보관함에서)
            archive_dir = config.get_report_archive_dir()
            if not os.path.exists(archive_dir):
                return
                
            report_files = glob.glob(os.path.join(archive_dir, '*_통합_리포트_*.xlsx'))
            
            total_files = len(report_files)
            total_sales = 0
            total_profit = 0
            
            # 최근 파일들만 읽어서 통계 계산 (성능을 위해 최근 10개만)
            recent_files = sorted(report_files, key=os.path.getmtime, reverse=True)[:10]
            
            for report_file in recent_files:
                try:
                    df = pd.read_excel(report_file, sheet_name='정리된 데이터')
                    if '매출' in df.columns:
                        total_sales += df['매출'].sum()
                    if '순이익' in df.columns:
                        total_profit += df['순이익'].sum()
                except Exception:
                    continue
            
            # 통계 정보 전송
            stats = {
                'files': f"{total_files}개",
                'sales': f"₩{total_sales:,.0f}",
                'profit': f"₩{total_profit:,.0f}"
            }
            self.stats_signal.emit(stats)
            
        except Exception as e:
            self.output_signal.emit(f"[DEBUG] 통계 수집 중 오류: {e}")

class ModernManualWorker(QThread):
    output_signal = Signal(str)
    finished_signal = Signal()
    error_signal = Signal(str)  # 오류 전용 시그널 추가
    stats_signal = Signal(dict)  # 통계 업데이트 시그널 추가
    
    def __init__(self, download_folder, password="1234"):
        super().__init__()
        self.download_folder = download_folder
        self.password = password

    def run(self):
        try:
            config.DOWNLOAD_DIR = self.download_folder
            config.ORDER_FILE_PASSWORD = self.password
            self.output_signal.emit("[INFO] 🔄 작업폴더 수동 처리 시작...")
            
            # 1단계: 작업폴더에 있는 파일들로 개별 리포트 생성
            self.output_signal.emit("[INFO] 📊 1단계: 작업폴더 파일들로 개별 리포트 생성 중...")
            from modules import report_generator
            processed_groups = report_generator.generate_individual_reports()
            
            if processed_groups:
                self.output_signal.emit(f"[INFO] ✅ 1단계 완료: {len(processed_groups)}개 그룹 처리됨")
            else:
                self.output_signal.emit("[INFO] ⚠️ 1단계: 처리할 파일이 없거나 리포트 생성 실패")
            
            # 2단계: 최종 통합 처리 (일일/주간 리포트 생성 및 파일 정리)
            self.output_signal.emit("[INFO] 🏁 2단계: 최종 통합 처리 중...")
            file_handler.finalize_all_processing()
            self.output_signal.emit("[INFO] ✅ 2단계: 최종 통합 처리 완료")
            
            self.output_signal.emit("[INFO] 🎯 작업폴더 처리 완료!")
            
            # 통계 정보 수집 및 전송
            self.collect_and_send_stats()
            
        except Exception as e:
            error_msg = f"[ERROR] 수동 처리 중 오류: {str(e)}"
            self.output_signal.emit(error_msg)
            self.error_signal.emit(error_msg)  # 오류 시그널 발생
            import traceback
            self.output_signal.emit(f"[DEBUG] 상세 오류: {traceback.format_exc()}")
        finally:
            self.finished_signal.emit()

    def collect_and_send_stats(self):
        """통계 정보를 수집해서 시그널로 전송"""
        try:
            import glob
            import pandas as pd
            
            # 처리된 리포트 파일들 찾기
            processing_dir = config.get_processing_dir()
            report_files = glob.glob(os.path.join(processing_dir, '*_통합_리포트_*.xlsx'))
            
            total_files = len(report_files)
            total_sales = 0
            total_profit = 0
            
            # 각 리포트 파일에서 통계 추출
            for report_file in report_files:
                try:
                    df = pd.read_excel(report_file, sheet_name='정리된 데이터')
                    if '매출' in df.columns:
                        total_sales += df['매출'].sum()
                    if '순이익' in df.columns:
                        total_profit += df['순이익'].sum()
                except Exception:
                    continue
            
            # 통계 정보 전송
            stats = {
                'files': f"{total_files}개",
                'sales': f"₩{total_sales:,.0f}",
                'profit': f"₩{total_profit:,.0f}"
            }
            self.stats_signal.emit(stats)
            
        except Exception as e:
            self.output_signal.emit(f"[DEBUG] 통계 수집 중 오류: {e}")

class WeeklyWorker(QThread):
    output_signal = Signal(str)
    finished_signal = Signal()
    error_signal = Signal(str)  # 오류 전용 시그널 추가
    stats_signal = Signal(dict)  # 통계 업데이트 시그널 추가

    def __init__(self, start_date, end_date, download_folder):
        super().__init__()
        self.start_date = start_date
        self.end_date = end_date
        self.download_folder = download_folder

    def run(self):
        try:
            self.output_signal.emit(f"[INFO] 📅 주간 리포트 생성 시작...")
            
            # config 전역 상태 변경 대신 매개변수로 전달
            success = weekly_reporter.create_weekly_report(
                self.start_date, 
                self.end_date, 
                self.download_folder
            )
            
            if success:
                self.output_signal.emit("[INFO] ✅ 주간 리포트 생성 완료!")
            else:
                error_msg = "[ERROR] 주간 리포트 생성 실패 - 로그를 확인해주세요."
                self.output_signal.emit(error_msg)
                self.error_signal.emit(error_msg)  # 오류 시그널 발생
                
        except Exception as e:
            error_msg = f"[ERROR] 주간 리포트 생성 중 예외 발생: {str(e)}"
            self.output_signal.emit(error_msg)
            self.error_signal.emit(error_msg)  # 오류 시그널 발생
        finally:
            self.finished_signal.emit()

class AIAnalysisWorker(QThread):
    output_signal = Signal(str)
    finished_signal = Signal()
    error_signal = Signal(str)
    results_signal = Signal(dict)  # AI 분석 결과 시그널

    def __init__(self, data_path):
        super().__init__()
        self.data_path = data_path

    def run(self):
        try:
            if not AI_MODULES_AVAILABLE:
                error_msg = "[ERROR] AI 모듈이 설치되지 않았습니다"
                self.output_signal.emit(error_msg)
                self.error_signal.emit(error_msg)
                return

            self.output_signal.emit("[INFO] 🤖 AI 분석 시작...")

            # 1. 최신 리포트 파일 검색
            self.output_signal.emit("[INFO] 📊 분석할 데이터 검색 중...")
            data_files = self._find_latest_reports()

            if not data_files:
                error_msg = "[ERROR] 분석할 리포트 파일을 찾을 수 없습니다"
                self.output_signal.emit(error_msg)
                self.error_signal.emit(error_msg)
                return

            # 2. 데이터 로드 및 전처리
            self.output_signal.emit(f"[INFO] 📈 {len(data_files)}개 파일에서 데이터 로드 중...")
            combined_data = self._load_and_combine_data(data_files)

            if combined_data is None or len(combined_data) == 0:
                error_msg = "[ERROR] 유효한 데이터를 로드할 수 없습니다"
                self.output_signal.emit(error_msg)
                self.error_signal.emit(error_msg)
                return

            self.output_signal.emit(f"[INFO] ✅ {len(combined_data)}개 상품 데이터 로드 완료")

            # 3. AI 분석 실행
            self.output_signal.emit("[INFO] 🧠 AI 분석 엔진 초기화...")
            recommendation_engine = SmartRecommendationEngine(min_confidence_threshold=0.6)

            self.output_signal.emit("[INFO] 🔍 이상 탐지 및 클러스터링 분석 중...")
            # 날짜 추출을 위해 가장 최신 파일 경로 전달
            latest_file_path = data_files[0] if data_files else None
            analysis_results = recommendation_engine.analyze_and_recommend(combined_data, file_path=latest_file_path)

            # 4. 결과 요약 생성
            self.output_signal.emit("[INFO] 📋 분석 결과 정리 중...")
            summary = self._create_analysis_summary(analysis_results)

            self.output_signal.emit("[INFO] ✅ AI 분석 완료!")
            self.results_signal.emit({
                'analysis_results': analysis_results,
                'summary': summary,
                'data_info': {
                    'total_products': len(combined_data),
                    'files_analyzed': len(data_files),
                    'analysis_date': datetime.now().isoformat()
                }
            })

        except Exception as e:
            error_msg = f"[ERROR] AI 분석 중 오류: {str(e)}"
            self.output_signal.emit(error_msg)
            self.error_signal.emit(error_msg)
            logging.error(f"AI 분석 오류: {str(e)}", exc_info=True)
        finally:
            self.finished_signal.emit()

    def _find_latest_reports(self):
        """최신 리포트 파일들 검색"""
        import glob

        # 리포트 보관함에서 최신 파일들 검색
        report_dir = os.path.join(self.data_path, "리포트보관함")
        if not os.path.exists(report_dir):
            return []

        # 일간통합리포트 폴더에서만 검색 (중복 방지)
        daily_report_dir = os.path.join(report_dir, "일간통합리포트")
        if not os.path.exists(daily_report_dir):
            return []

        # 일간통합리포트 파일만 검색
        files = glob.glob(os.path.join(daily_report_dir, "전체_통합_리포트_*.xlsx"))

        # 최신 순 정렬
        files.sort(key=os.path.getmtime, reverse=True)
        return files

    def _load_and_combine_data(self, file_paths):
        """여러 Excel 파일에서 데이터 로드 및 결합"""
        combined_data = []

        for file_path in file_paths:
            try:
                # pandas로 Excel 파일 읽기
                df = pd.read_excel(file_path)

                # 필수 컬럼 확인
                required_columns = ["상품ID", "상품명", "매출", "순이익", "수량"]
                missing_columns = [col for col in required_columns if col not in df.columns]

                if missing_columns:
                    self.output_signal.emit(f"[WARNING] {os.path.basename(file_path)}: 필수 컬럼 누락 {missing_columns}")
                    continue

                # 옵션 컬럼 추가 (없으면 기본값)
                if "리워드" not in df.columns:
                    df["리워드"] = 0
                if "가구매 비용" not in df.columns:
                    df["가구매 비용"] = 0

                # 숫자 컬럼 변환
                numeric_columns = ["매출", "순이익", "수량", "리워드", "가구매 비용"]
                for col in numeric_columns:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

                # 유효한 데이터만 추가
                valid_data = df[df["매출"] > 0].copy()
                if len(valid_data) > 0:
                    combined_data.append(valid_data)

            except Exception as e:
                self.output_signal.emit(f"[WARNING] {os.path.basename(file_path)} 로드 실패: {str(e)}")
                continue

        if not combined_data:
            return None

        # 모든 데이터 결합
        final_df = pd.concat(combined_data, ignore_index=True)

        # 중복 제거 (상품ID 기준)
        final_df = final_df.drop_duplicates(subset=["상품ID"], keep="last")

        # Polars DataFrame으로 변환 (타입 안전성 강화)
        try:
            # 데이터 타입 정리 및 검증
            for col in final_df.columns:
                if final_df[col].dtype == 'object':
                    # 문자열 컬럼 처리
                    if col in ["상품ID", "상품명"]:
                        final_df[col] = final_df[col].astype(str).fillna("")
                    else:
                        # 숫자로 변환 가능한지 확인
                        try:
                            final_df[col] = pd.to_numeric(final_df[col], errors='coerce').fillna(0)
                        except:
                            final_df[col] = final_df[col].astype(str).fillna("")
                elif final_df[col].dtype in ['int64', 'float64']:
                    # 숫자 컬럼의 NaN 처리
                    final_df[col] = final_df[col].fillna(0)

            # 모든 문자열 컬럼을 명시적으로 문자열로 변환
            string_columns = ["상품ID", "상품명"]
            for col in string_columns:
                if col in final_df.columns:
                    final_df[col] = final_df[col].astype(str)

            # 숫자 컬럼을 명시적으로 숫자로 변환
            numeric_columns = ["매출", "순이익", "수량", "리워드", "가구매 비용"]
            for col in numeric_columns:
                if col in final_df.columns:
                    final_df[col] = pd.to_numeric(final_df[col], errors='coerce').fillna(0).astype('float64')

            self.output_signal.emit(f"[INFO] 데이터 타입 정리 완료 - {len(final_df)}행")

            # Polars로 안전하게 변환
            polars_df = pl.from_pandas(final_df)
            self.output_signal.emit(f"[INFO] ✅ Polars 변환 성공")
            return polars_df

        except Exception as e:
            self.output_signal.emit(f"[ERROR] Polars 변환 실패: {str(e)}")
            self.output_signal.emit(f"[INFO] 📊 pandas DataFrame으로 대체 처리 시도...")

            # Polars 변환 실패 시 pandas로 직접 처리
            try:
                # pandas DataFrame을 직접 사용하는 대안 구현
                return self._create_polars_compatible_data(final_df)
            except Exception as fallback_error:
                self.output_signal.emit(f"[ERROR] 대체 처리도 실패: {str(fallback_error)}")
                return None

    def _create_polars_compatible_data(self, pandas_df):
        """pandas DataFrame을 Polars 호환 형태로 변환"""
        try:
            # 수동으로 Polars DataFrame 생성
            data_dict = {}

            for col in pandas_df.columns:
                series = pandas_df[col]

                if col in ["상품ID", "상품명"]:
                    # 문자열 컬럼
                    data_dict[col] = series.astype(str).fillna("").tolist()
                else:
                    # 숫자 컬럼
                    numeric_series = pd.to_numeric(series, errors='coerce').fillna(0)
                    data_dict[col] = numeric_series.tolist()

            # Polars DataFrame 생성
            polars_df = pl.DataFrame(data_dict)
            self.output_signal.emit(f"[INFO] ✅ 수동 Polars 변환 성공")
            return polars_df

        except Exception as e:
            self.output_signal.emit(f"[ERROR] 수동 변환도 실패: {str(e)}")
            self.output_signal.emit(f"[INFO] 🔄 pandas 호환 모드로 전환...")

            # 최종 대안: pandas DataFrame을 Polars처럼 사용
            return self._create_pandas_wrapper(pandas_df)

    def _create_pandas_wrapper(self, pandas_df):
        """pandas DataFrame을 Polars 인터페이스로 래핑"""
        class PandasPolarsWrapper:
            def __init__(self, df):
                self.df = df
                self.columns = df.columns.tolist()

            def __len__(self):
                return len(self.df)

            def __getitem__(self, key):
                return self.df[key]

            def select(self, columns):
                if isinstance(columns, list):
                    return PandasPolarsWrapper(self.df[columns])
                return PandasPolarsWrapper(self.df[[columns]])

            def to_numpy(self):
                return self.df.values

            def iter_rows(self, named=True):
                if named:
                    for _, row in self.df.iterrows():
                        yield row.to_dict()
                else:
                    for _, row in self.df.iterrows():
                        yield row.tolist()

            def filter(self, condition):
                # 간단한 필터링 지원
                return PandasPolarsWrapper(self.df)

            def head(self, n=5):
                return PandasPolarsWrapper(self.df.head(n))

            def sort(self, column, descending=False):
                ascending = not descending
                return PandasPolarsWrapper(self.df.sort_values(column, ascending=ascending))

        self.output_signal.emit(f"[INFO] ✅ pandas 래퍼 모드로 분석 진행")
        return PandasPolarsWrapper(pandas_df)

    def _create_analysis_summary(self, results):
        """분석 결과 요약 생성"""
        try:
            recommendations = results.get("product_recommendations", [])
            portfolio = results.get("portfolio_insights", {})
            impact = results.get("business_impact", {})

            summary = {
                "총_추천수": len(recommendations),
                "긴급_추천수": len([r for r in recommendations if r.priority.value == "긴급"]),
                "높은_우선순위": len([r for r in recommendations if r.priority.value == "높음"]),
                "포트폴리오_건강도": portfolio.get("overall_health", "알 수 없음"),
                "예상_매출_증가": impact.get("예상_매출_증가", 0),
                "예상_이익_증가": impact.get("예상_이익_증가", 0),
                "ROI_개선율": impact.get("ROI_개선율", 0),
                "주요_추천사항": [
                    {
                        "상품명": r.product_name,
                        "추천유형": r.recommendation_type.value,
                        "우선순위": r.priority.value,
                        "액션": r.action_details
                    }
                    for r in recommendations[:5]  # 상위 5개만
                ]
            }

            return summary

        except Exception as e:
            self.output_signal.emit(f"[WARNING] 요약 생성 중 오류: {str(e)}")
            return {"오류": "요약 생성 실패"}

# --- Dialog Classes ---

class WeeklyReportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📅 주간 리포트 생성")
        self.setFixedSize(400, 200)
        layout = QVBoxLayout(self)
        
        # 설명 레이블 추가
        info_label = QLabel("생성할 주간 리포트의 날짜 범위를 선택하세요.")
        info_label.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        form_layout = QGridLayout()
        
        # 날짜 선택기 설정
        self.start_date_edit = QDateEdit(QDate.currentDate().addDays(-7))
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setMaximumDate(QDate.currentDate())
        
        self.end_date_edit = QDateEdit(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setMaximumDate(QDate.currentDate())
        
        # 날짜 변경 시 검증
        self.start_date_edit.dateChanged.connect(self.validate_date_range)
        self.end_date_edit.dateChanged.connect(self.validate_date_range)
        
        form_layout.addWidget(QLabel("시작 날짜:"), 0, 0)
        form_layout.addWidget(self.start_date_edit, 0, 1)
        form_layout.addWidget(QLabel("종료 날짜:"), 1, 0)
        form_layout.addWidget(self.end_date_edit, 1, 1)
        layout.addLayout(form_layout)
        
        # 경고 메시지 레이블
        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet("color: red; font-size: 11px; margin: 5px 0px;")
        self.warning_label.hide()
        layout.addWidget(self.warning_label)
        
        # 버튼
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
        # 초기 검증
        self.validate_date_range()

    def validate_date_range(self):
        """날짜 범위 검증"""
        start_date = self.start_date_edit.date()
        end_date = self.end_date_edit.date()
        
        if start_date > end_date:
            self.warning_label.setText("⚠️ 시작 날짜가 종료 날짜보다 늦을 수 없습니다.")
            self.warning_label.setStyleSheet("color: red; font-size: 11px; margin: 5px 0px;")
            self.warning_label.show()
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
            return False
        elif start_date == end_date:
            self.warning_label.setText("💡 동일한 날짜로 설정되었습니다. 해당 날짜의 리포트만 생성됩니다.")
            self.warning_label.setStyleSheet("color: #ff8800; font-size: 11px; margin: 5px 0px;")
            self.warning_label.show()
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
            return True
        else:
            days_diff = start_date.daysTo(end_date) + 1
            if days_diff > 31:
                self.warning_label.setText(f"⚠️ 너무 긴 기간입니다 ({days_diff}일). 31일 이하로 설정해주세요.")
                self.warning_label.setStyleSheet("color: red; font-size: 11px; margin: 5px 0px;")
                self.warning_label.show()
                self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
                return False
            else:
                self.warning_label.hide()
                self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
                return True

    def validate_and_accept(self):
        """확인 버튼 클릭 시 최종 검증"""
        if self.validate_date_range():
            self.accept()

    def get_dates(self):
        """검증된 날짜 반환"""
        if self.validate_date_range():
            return (
                self.start_date_edit.date().toString("yyyy-MM-dd"), 
                self.end_date_edit.date().toString("yyyy-MM-dd")
            )
        else:
            return None, None

class ErrorDetailsDialog(QDialog):
    def __init__(self, error_messages, parent=None):
        super().__init__(parent)
        self.error_messages = error_messages
        self.setWindowTitle("🚨 오류 상세 정보")
        self.setFixedSize(800, 600)
        self.setModal(True)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 헤더 정보
        header_layout = QHBoxLayout()
        
        title_label = QLabel(f"총 {len(self.error_messages)}개의 오류가 발생했습니다")
        title_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #dc3545; margin: 10px 0px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 클리어 버튼
        clear_btn = QPushButton("오류 기록 지우기")
        clear_btn.setStyleSheet("QPushButton { background-color: #6c757d; color: white; font-weight: bold; padding: 6px 12px; border: none; border-radius: 4px; } QPushButton:hover { background-color: #545b62; }")
        clear_btn.clicked.connect(self.clear_errors)
        header_layout.addWidget(clear_btn)
        
        layout.addLayout(header_layout)
        
        # 오류 테이블
        self.error_table = QTableWidget()
        self.error_table.setColumnCount(3)
        self.error_table.setHorizontalHeaderLabels(['시간', '유형', '오류 메시지'])
        
        # 테이블 스타일링
        self.error_table.setAlternatingRowColors(True)
        self.error_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # 컬럼 크기 조정
        header = self.error_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 시간
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 유형
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # 메시지
        
        self.populate_table()
        layout.addWidget(self.error_table)
        
        # 통계 정보
        stats_layout = QHBoxLayout()
        error_types = {}
        for error in self.error_messages:
            error_type = error['type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        stats_text = " | ".join([f"{error_type}: {count}개" for error_type, count in error_types.items()])
        stats_label = QLabel(f"오류 유형별 통계: {stats_text}")
        stats_label.setStyleSheet("font-size: 12px; color: #666; padding: 8px;")
        stats_layout.addWidget(stats_label)
        layout.addLayout(stats_layout)
        
        # 닫기 버튼
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("QPushButton { background-color: #007bff; color: white; font-weight: bold; padding: 10px 20px; border: none; border-radius: 6px; min-width: 80px; } QPushButton:hover { background-color: #0056b3; }")
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)
    
    def populate_table(self):
        """테이블에 오류 데이터 채우기"""
        self.error_table.setRowCount(len(self.error_messages))
        
        for row, error in enumerate(reversed(self.error_messages)):  # 최신 오류가 위에 오도록
            # 시간
            time_item = QTableWidgetItem(error['timestamp'])
            time_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.error_table.setItem(row, 0, time_item)
            
            # 유형 (색상으로 구분)
            type_item = QTableWidgetItem(error['type'])
            type_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            
            # 유형별 색상 설정
            if error['type'] == '파일 오류':
                type_item.setBackground(QColor("#fff3cd"))
            elif error['type'] == '권한 오류':
                type_item.setBackground(QColor("#f8d7da"))
            elif error['type'] == '메모리 오류':
                type_item.setBackground(QColor("#d1ecf1"))
            elif error['type'] == '네트워크 오류':
                type_item.setBackground(QColor("#d4edda"))
            else:
                type_item.setBackground(QColor("#e2e3e5"))
            
            self.error_table.setItem(row, 1, type_item)
            
            # 메시지
            message_item = QTableWidgetItem(error['message'])
            message_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            message_item.setToolTip(error['message'])  # 툴팁으로 전체 메시지 보기
            self.error_table.setItem(row, 2, message_item)
    
    def clear_errors(self):
        """오류 기록 삭제 확인"""
        reply = QMessageBox.question(
            self, 
            "오류 기록 삭제", 
            "모든 오류 기록을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 부모 앱의 오류 기록 삭제
            if self.parent():
                self.parent().error_messages.clear()
                self.parent().error_count = 0
                self.parent().error_card.update_value("0개")
            
            self.accept()
            QMessageBox.information(self, "삭제 완료", "모든 오류 기록이 삭제되었습니다.")

class ModernRewardDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('💰 일일 리워드 관리')
        self.setFixedSize(950, 750)
        self.setModal(True)
        
        self.reward_file = os.path.join(config.BASE_DIR, '리워드설정.json')
        self.margin_file = config.MARGIN_FILE
        self.all_rewards_data = {'rewards': []}
        self.products_df = pd.DataFrame()

        # 초기화 완료 플래그
        self._initialization_complete = False

        self.initUI()
        self.load_data_sources()
        # 초기화 완료 플래그 설정
        self._initialization_complete = True
        # 초기 데이터 로드
        self.load_initial_data()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 최소화된 헤더 섹션
        header_widget = QWidget()
        header_widget.setStyleSheet("background: #f8f9fa; border-radius: 8px; padding: 12px; margin-bottom: 8px;")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 8, 12, 8)
        
        title_label = QLabel("일일 리워드 설정")
        title_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #E65100; margin: 0;")
        subtitle_label = QLabel("상품별 리워드 금액을 날짜별로 설정하세요")
        subtitle_label.setStyleSheet("font-size: 12px; color: #6c757d; margin-top: 4px;")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        main_layout.addWidget(header_widget)
        
        # 스크롤 가능한 컨텐츠 영역
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 날짜 선택 및 복사
        date_group = QGroupBox("날짜 선택 및 설정 복사")
        date_layout = QGridLayout()
        date_layout.addWidget(QLabel("<b>수정할 날짜:</b>"), 0, 0)
        self.target_date_edit = QDateEdit(QDate.currentDate()); self.target_date_edit.setCalendarPopup(True)
        self.target_date_edit.dateChanged.connect(self.load_rewards_for_date)
        date_layout.addWidget(self.target_date_edit, 0, 1)
        date_layout.addWidget(QLabel("<b>설정 복사:</b>"), 1, 0)
        self.source_date_edit = QDateEdit(QDate.currentDate().addDays(-1)); self.source_date_edit.setCalendarPopup(True)
        date_layout.addWidget(self.source_date_edit, 1, 1)
        self.copy_button = QPushButton("설정 불러오기"); self.copy_button.clicked.connect(self.copy_rewards)
        date_layout.addWidget(self.copy_button, 1, 2)
        date_group.setLayout(date_layout)
        layout.addWidget(date_group)
        
        # 검색 및 일괄 설정
        control_group = QGroupBox("검색 및 일괄 설정")
        control_layout = QGridLayout()
        control_layout.addWidget(QLabel("검색:"), 0, 0)
        self.search_box = QLineEdit(); self.search_box.setPlaceholderText("상품명으로 검색...")
        self.search_box.textChanged.connect(self.filter_products)
        control_layout.addWidget(self.search_box, 0, 1, 1, 2)
        self.select_all_checkbox = QCheckBox("전체 선택/해제"); self.select_all_checkbox.clicked.connect(self.toggle_all_selection)
        control_layout.addWidget(self.select_all_checkbox, 1, 0)
        self.selected_count_label = QLabel("선택됨: 0개")
        control_layout.addWidget(self.selected_count_label, 1, 1)
        control_layout.addWidget(QLabel("선택된 항목에 적용:"), 2, 0)
        bulk_layout = QHBoxLayout()
        self.bulk_reward = QSpinBox()
        self.bulk_reward.setRange(0, 999999)
        self.bulk_reward.setSingleStep(1000)  # 1000원 단위로 증감
        self.bulk_reward.setSuffix(" 원")
        # 기본 스타일만 적용 (가구매 관리처럼)
        self.bulk_reward.setMinimumHeight(32)
        bulk_layout.addWidget(self.bulk_reward)
        
        # 빠른 설정 버튼들
        quick_buttons = [("0원", 0), ("3000원", 3000), ("6000원", 6000), ("9000원", 9000)]
        for text, value in quick_buttons:
            btn = QPushButton(text)
            btn.setMaximumWidth(60)
            btn.clicked.connect(lambda checked, v=value: self.bulk_reward.setValue(v))
            btn.setStyleSheet("font-size: 11px; padding: 4px;")
            bulk_layout.addWidget(btn)
        
        bulk_layout.addStretch()
        control_layout.addLayout(bulk_layout, 2, 1, 1, 2)
        self.apply_selected_button = QPushButton("선택된 항목에 적용"); self.apply_selected_button.clicked.connect(self.apply_to_selected)
        self.apply_selected_button.setStyleSheet("background-color: #17a2b8; color: white; font-weight: bold;")
        control_layout.addWidget(self.apply_selected_button, 3, 0, 1, 3)
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 상품 테이블
        self.reward_table = QTableWidget()
        self.reward_table.setColumnCount(5)
        self.reward_table.setHorizontalHeaderLabels(['선택', '상품ID', '상품명', '옵션정보', '리워드 금액'])
        self.reward_table.setMinimumHeight(350)  # 높이 약간 줄여서 버튼 공간 확보
        header = self.reward_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 체크박스
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 상품ID
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 상품명
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 옵션정보
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 리워드 금액
        layout.addWidget(self.reward_table)
        
        # 스크롤 영역 설정 (버튼들은 제외)
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        # 하단 고정 버튼들 (스크롤 영역 밖에 배치)
        button_widget = QWidget()
        button_widget.setStyleSheet("background: #f8f9fa; border-top: 1px solid #dee2e6; padding: 10px;")
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(20, 15, 20, 15)
        
        self.save_button = QPushButton("💾 저장")
        self.save_button.clicked.connect(self.save_rewards)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        self.cancel_button = QPushButton("❌ 취소")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        # 하단 고정 버튼 위젯을 메인 레이아웃에 추가
        main_layout.addWidget(button_widget)
    
    def load_initial_data(self):
        """UI 완성 후 초기 데이터 로드"""
        if hasattr(self, '_initialization_complete') and self._initialization_complete:
            self.load_rewards_for_date(QDate.currentDate())

    def load_data_sources(self):
        try:
            if os.path.exists(self.margin_file):
                df = pd.read_excel(self.margin_file, engine='openpyxl')
                df = df.rename(columns={'상품번호': '상품ID'})
                if '대표옵션' in df.columns:
                    df['대표옵션'] = df['대표옵션'].astype(str).str.upper().isin(['O', 'Y', 'TRUE'])
                    df = df[df['대표옵션'] == True]
                # 옵션정보 컬럼도 포함하여 products_df 생성
                columns_to_keep = ['상품ID', '상품명']
                if '옵션정보' in df.columns:
                    columns_to_keep.append('옵션정보')
                self.products_df = df[columns_to_keep].drop_duplicates().sort_values(by='상품명')
            if os.path.exists(self.reward_file):
                with open(self.reward_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.all_rewards_data = json.loads(content) if content else {'rewards': []}
        except Exception as e:
            QMessageBox.critical(self, "오류", f"데이터 소스 로드 오류: {e}")

    def normalize_product_id(self, product_id):
        """product_id 정규화 (.0 제거)"""
        product_id_str = str(product_id)
        if product_id_str.endswith('.0'):
            return product_id_str[:-2]
        return product_id_str
    
    def safe_get_option_info(self, product):
        """상품 데이터에서 옵션정보를 안전하게 가져오기"""
        import pandas as pd
        option_info = product.get('옵션정보', '')
        
        # pandas NA 값 처리
        if pd.isna(option_info):
            return ''
        
        # 문자열로 변환하고 공백 제거
        return str(option_info).strip()
    
    def find_reward_value(self, product_id, reward_map, option_info=''):
        """product_id와 옵션정보에 대한 리워드 값 찾기"""
        clean_id = self.normalize_product_id(product_id)
        dotted_id = clean_id + '.0'
        
        # 3-tuple 키로 옵션별 설정 확인
        option_key = (clean_id, option_info)
        dotted_option_key = (dotted_id, option_info)
        
        # 옵션별 설정이 있으면 우선 사용
        if option_key in reward_map:
            return reward_map[option_key]
        if dotted_option_key in reward_map:
            return reward_map[dotted_option_key]
        
        # 기존 방식 (하위 호환성)
        return reward_map.get(clean_id, reward_map.get(dotted_id, 0))
    
    def clear_table_widgets(self):
        """테이블 위젯들을 안전하게 정리"""
        try:
            for row in range(self.reward_table.rowCount()):
                # 체크박스 정리
                checkbox = self.reward_table.cellWidget(row, 0)
                if checkbox:
                    checkbox.deleteLater()
                # 스핀박스 정리
                spinbox = self.reward_table.cellWidget(row, 3)
                if spinbox:
                    spinbox.deleteLater()
            
            # 테이블 내용 클리어
            self.reward_table.clearContents()
        except Exception as e:
            import logging
            logging.error(f"리워드 테이블 위젯 정리 중 오류: {e}")

    def load_rewards_for_date(self, q_date):
        target_date_str = q_date.toString("yyyy-MM-dd")
        
        # 기존 위젯들 정리
        self.clear_table_widgets()
        
        # 모든 형식의 product_id를 포함하는 reward_map 생성 (정규화된 ID 사용)
        reward_map = {}
        for e in self.all_rewards_data.get('rewards', []):
            if e.get('start_date') == target_date_str:
                product_id = str(e['product_id'])
                normalized_product_id = self.normalize_product_id(product_id)
                option_info = e.get('option_info', '')
                
                # 옵션별 설정이 있으면 3-tuple 키로 저장
                if option_info:
                    reward_map[(normalized_product_id, option_info)] = e['reward']
                else:
                    # 기존 방식 (하위 호환성) - 정규화된 ID 사용
                    reward_map[normalized_product_id] = e['reward']
        
        self.reward_table.setRowCount(len(self.products_df))
        
        for row, (_, product) in enumerate(self.products_df.iterrows()):
            product_id = str(product['상품ID'])
            option_info = self.safe_get_option_info(product)
            
            # 체크박스 생성 및 이벤트 연결
            checkbox = QCheckBox()
            checkbox.clicked.connect(self.update_selected_count)
            self.reward_table.setCellWidget(row, 0, checkbox)
            
            self.reward_table.setItem(row, 1, QTableWidgetItem(product_id))
            self.reward_table.setItem(row, 2, QTableWidgetItem(str(product['상품명'])))
            self.reward_table.setItem(row, 3, QTableWidgetItem(option_info))
            
            # 스핀박스 생성 (1000원 단위, 개선된 UI)
            spinbox = QSpinBox()
            spinbox.setRange(0, 999999)
            spinbox.setSingleStep(1000)  # 1000원 단위로 증감
            spinbox.setSuffix(" 원")
            # 호환성을 위해 두 형식 모두 확인
            reward_value = self.find_reward_value(product_id, reward_map, option_info)
            spinbox.setValue(reward_value)
            # 기본 스타일만 적용 (가구매 관리처럼)
            spinbox.setMinimumHeight(28)
            self.reward_table.setCellWidget(row, 4, spinbox)
        
        self.filter_products()
        self.update_selected_count()

    def copy_rewards(self):
        source_date_str = self.source_date_edit.date().toString("yyyy-MM-dd")
        
        # load_rewards_for_date()와 동일한 방식으로 reward_map 생성 (정규화된 ID 사용)
        reward_map = {}
        for e in self.all_rewards_data.get('rewards', []):
            if e.get('start_date') == source_date_str:
                product_id = str(e['product_id'])
                normalized_product_id = self.normalize_product_id(product_id)
                option_info = e.get('option_info', '')
                
                # 옵션별 설정이 있으면 3-tuple 키로 저장
                if option_info:
                    reward_map[(normalized_product_id, option_info)] = e['reward']
                else:
                    # 기존 방식 (하위 호환성) - 정규화된 ID 사용
                    reward_map[normalized_product_id] = e['reward']
        
        if not reward_map:
            QMessageBox.information(self, "알림", f"{source_date_str}에 저장된 리워드 설정이 없습니다.")
            return
            
        # 현재 테이블에 적용 (올바른 컬럼 인덱스 사용)
        applied_count = 0
        for row in range(self.reward_table.rowCount()):
            product_id_item = self.reward_table.item(row, 1)      # 상품ID
            option_info_item = self.reward_table.item(row, 3)     # 옵션정보 (컬럼 3)
            spinbox = self.reward_table.cellWidget(row, 4)        # 스핀박스 (컬럼 4)
            if product_id_item and spinbox:
                product_id = product_id_item.text()
                option_info = option_info_item.text() if option_info_item else ''
                
                # find_reward_value()와 동일한 방식으로 찾기
                reward_value = self.find_reward_value(product_id, reward_map, option_info)
                if reward_value > 0:
                    spinbox.setValue(reward_value)
                    applied_count += 1
        
        QMessageBox.information(self, "복사 완료", f"{applied_count}개 상품의 리워드 설정을 복사했습니다.")

    def toggle_all_selection(self):
        is_checked = self.select_all_checkbox.isChecked()
        for row in range(self.reward_table.rowCount()):
            if not self.reward_table.isRowHidden(row):
                checkbox = self.reward_table.cellWidget(row, 0)
                if checkbox:
                    checkbox.setChecked(is_checked)
        self.update_selected_count()

    def apply_to_selected(self):
        """선택된 항목에 일괄 적용 (예외 처리 강화)"""
        try:
            bulk_value = self.bulk_reward.value()
            applied_count = 0
            for row in range(self.reward_table.rowCount()):
                checkbox = self.reward_table.cellWidget(row, 0)
                spinbox = self.reward_table.cellWidget(row, 4)
                if checkbox and checkbox.isChecked() and spinbox:
                    spinbox.setValue(bulk_value)
                    applied_count += 1
            
            if applied_count > 0:
                QMessageBox.information(self, "적용 완료", f"{applied_count}개 상품에 {bulk_value}원 리워드를 적용했습니다.")
            else:
                QMessageBox.warning(self, "선택 없음", "적용할 상품을 먼저 선택해주세요.")
        except Exception as e:
            import logging
            logging.error(f"리워드 일괄 적용 중 오류: {e}")
            QMessageBox.critical(self, "오류", f"일괄 적용 중 오류가 발생했습니다:\n{str(e)}")

    def update_selected_count(self):
        """선택된 항목 수 업데이트 (예외 처리 강화)"""
        try:
            selected_count = 0
            for row in range(self.reward_table.rowCount()):
                if not self.reward_table.isRowHidden(row):
                    checkbox = self.reward_table.cellWidget(row, 0)
                    if checkbox and checkbox.isChecked():
                        selected_count += 1
            
            if hasattr(self, 'selected_count_label'):
                self.selected_count_label.setText(f"선택됨: {selected_count}개")
            
            if hasattr(self, 'apply_selected_button'):
                self.apply_selected_button.setEnabled(selected_count > 0)
        except Exception as e:
            import logging
            logging.error(f"리워드 선택 개수 업데이트 중 오류: {e}")
            if hasattr(self, 'selected_count_label'):
                self.selected_count_label.setText("선택됨: 오류")

    def filter_products(self):
        search_text = self.search_box.text().lower()
        for row in range(self.reward_table.rowCount()):
            product_name = self.reward_table.item(row, 2).text().lower()
            self.reward_table.setRowHidden(row, search_text not in product_name)
        self.update_selected_count()

    def add_reward(self):
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")
        product_id = self.product_id.text().strip()
        if not product_id:
            QMessageBox.warning(self, "입력 오류", "상품 ID를 입력해주세요.")
            return
        row = self.reward_table.rowCount()
        self.reward_table.insertRow(row)
        self.reward_table.setItem(row, 0, QTableWidgetItem(start_date))
        self.reward_table.setItem(row, 1, QTableWidgetItem(end_date))
        self.reward_table.setItem(row, 2, QTableWidgetItem(product_id))
        self.reward_table.setItem(row, 3, QTableWidgetItem(f"{self.reward_amount.value():,}원"))
        delete_btn = AppleStyleButton("삭제", "fa5s.trash", MaterialColors.ERROR)
        delete_btn.clicked.connect(lambda: self.delete_reward(row))
        self.reward_table.setCellWidget(row, 4, delete_btn)
        self.product_id.clear(); self.reward_amount.setValue(0)

    def delete_reward(self, row):
        self.reward_table.removeRow(row)
        self.refresh_table_buttons()

    def refresh_table_buttons(self):
        for row in range(self.reward_table.rowCount()):
            delete_btn = AppleStyleButton("삭제", "fa5s.trash", MaterialColors.ERROR)
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_reward(r))
            self.reward_table.setCellWidget(row, 4, delete_btn)

    def load_rewards(self):
        try:
            reward_file = os.path.join(config.BASE_DIR, '리워드설정.json')
            if not os.path.exists(reward_file): return
            with open(reward_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for reward in data.get('rewards', []):
                row = self.reward_table.rowCount()
                self.reward_table.insertRow(row)
                self.reward_table.setItem(row, 0, QTableWidgetItem(reward['start_date']))
                self.reward_table.setItem(row, 1, QTableWidgetItem(reward['end_date']))
                self.reward_table.setItem(row, 2, QTableWidgetItem(reward['product_id']))
                self.reward_table.setItem(row, 3, QTableWidgetItem(f"{reward['reward']:,}원"))
                delete_btn = AppleStyleButton("삭제", "fa5s.trash", MaterialColors.ERROR)
                delete_btn.clicked.connect(lambda checked, r=row: self.delete_reward(r))
                self.reward_table.setCellWidget(row, 4, delete_btn)
        except Exception as e:
            logging.warning(f"리워드 설정 로드 실패: {e}")

    def save_rewards(self):
        try:
            target_date_str = self.target_date_edit.date().toString("yyyy-MM-dd")
            other_days_rewards = [e for e in self.all_rewards_data.get('rewards', []) if e.get('start_date') != target_date_str]
            new_rewards = []
            for row in range(self.reward_table.rowCount()):
                reward_entry = {
                    'start_date': target_date_str, 'end_date': target_date_str,
                    'product_id': self.reward_table.item(row, 1).text(),
                    'reward': self.reward_table.cellWidget(row, 4).value()
                }
                # 옵션정보가 있으면 추가
                option_info = self.reward_table.item(row, 3).text()
                if option_info:
                    reward_entry['option_info'] = option_info
                new_rewards.append(reward_entry)
            self.all_rewards_data['rewards'] = other_days_rewards + new_rewards
            with open(self.reward_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_rewards_data, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "완료", f"{target_date_str}의 리워드 설정이 저장되었습니다.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "오류", f"리워드 설정 저장 중 오류가 발생했습니다:\n{str(e)}")

class PurchaseManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('🛒 일일 가구매 개수 관리')
        self.setFixedSize(950, 750)
        self.setModal(True)
        
        self.purchase_file = os.path.join(config.BASE_DIR, '가구매설정.json')
        self.margin_file = config.MARGIN_FILE
        self.all_purchases_data = {'purchases': []}
        self.products_df = pd.DataFrame()

        # 초기화 완료 플래그
        self._initialization_complete = False

        self.initUI()
        self.load_data_sources()
        # 초기화 완료 플래그 설정
        self._initialization_complete = True
        # 초기 데이터 로드
        self.load_initial_data()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 최소화된 헤더 섹션
        header_widget = QWidget()
        header_widget.setStyleSheet("background: #f8f9fa; border-radius: 8px; padding: 12px; margin-bottom: 8px;")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 8, 12, 8)
        
        title_label = QLabel("일일 가구매 개수 설정")
        title_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #01579B; margin: 0;")
        subtitle_label = QLabel("상품별 가구매 개수를 날짜별로 설정하세요")
        subtitle_label.setStyleSheet("font-size: 12px; color: #6c757d; margin-top: 4px;")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        main_layout.addWidget(header_widget)
        
        # 스크롤 가능한 컨텐츠 영역
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        date_group = QGroupBox("날짜 선택 및 설정 복사")
        date_layout = QGridLayout()
        date_layout.addWidget(QLabel("<b>수정할 날짜:</b>"), 0, 0)
        self.target_date_edit = QDateEdit(QDate.currentDate()); self.target_date_edit.setCalendarPopup(True)
        self.target_date_edit.dateChanged.connect(self.load_purchases_for_date)
        date_layout.addWidget(self.target_date_edit, 0, 1)
        date_layout.addWidget(QLabel("<b>설정 복사:</b>"), 1, 0)
        self.source_date_edit = QDateEdit(QDate.currentDate().addDays(-1)); self.source_date_edit.setCalendarPopup(True)
        date_layout.addWidget(self.source_date_edit, 1, 1)
        self.copy_button = QPushButton("의 설정 불러오기"); self.copy_button.clicked.connect(self.copy_purchases)
        date_layout.addWidget(self.copy_button, 1, 2)
        date_group.setLayout(date_layout)
        layout.addWidget(date_group)
        
        control_group = QGroupBox("검색 및 일괄 설정")
        control_layout = QGridLayout()
        control_layout.addWidget(QLabel("검색:"), 0, 0)
        self.search_box = QLineEdit(); self.search_box.setPlaceholderText("상품명으로 검색...")
        self.search_box.textChanged.connect(self.filter_products)
        control_layout.addWidget(self.search_box, 0, 1, 1, 2)
        self.select_all_checkbox = QCheckBox("전체 선택/해제"); self.select_all_checkbox.clicked.connect(self.toggle_all_selection)
        control_layout.addWidget(self.select_all_checkbox, 1, 0)
        self.selected_count_label = QLabel("선택됨: 0개")
        control_layout.addWidget(self.selected_count_label, 1, 1)
        control_layout.addWidget(QLabel("선택된 항목에 적용:"), 2, 0)
        bulk_layout = QHBoxLayout()
        self.bulk_purchase = QSpinBox(); self.bulk_purchase.setRange(0, 9999); self.bulk_purchase.setSuffix(" 개")
        bulk_layout.addWidget(self.bulk_purchase)
        
        # 빠른 설정 버튼들
        quick_buttons = [("0개", 0), ("1개", 1), ("3개", 3), ("5개", 5), ("10개", 10)]
        for text, value in quick_buttons:
            btn = QPushButton(text)
            btn.setMaximumWidth(50)
            btn.clicked.connect(lambda checked, v=value: self.bulk_purchase.setValue(v))
            btn.setStyleSheet("font-size: 11px; padding: 4px;")
            bulk_layout.addWidget(btn)
        
        bulk_layout.addStretch()
        control_layout.addLayout(bulk_layout, 2, 1, 1, 2)
        self.apply_selected_button = QPushButton("선택된 항목에 적용"); self.apply_selected_button.clicked.connect(self.apply_to_selected)
        self.apply_selected_button.setStyleSheet("background-color: #17a2b8; color: white; font-weight: bold;")
        control_layout.addWidget(self.apply_selected_button, 3, 0, 1, 3)
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 상품 테이블
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(5)
        self.product_table.setHorizontalHeaderLabels(['선택', '상품ID', '상품명', '옵션정보', '가구매 개수'])
        self.product_table.setMinimumHeight(350)  # 높이 설정하여 버튼 공간 확보
        header = self.product_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 체크박스
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 상품ID
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 상품명
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 옵션정보
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 가구매 개수
        layout.addWidget(self.product_table)
        
        # 스크롤 영역 설정 (버튼들은 제외)
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        # 하단 고정 버튼들 (스크롤 영역 밖에 배치)
        button_widget = QWidget()
        button_widget.setStyleSheet("background: #f8f9fa; border-top: 1px solid #dee2e6; padding: 10px;")
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(20, 15, 20, 15)
        
        self.save_button = QPushButton("💾 저장")
        self.save_button.clicked.connect(self.save_purchases)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        self.cancel_button = QPushButton("❌ 취소")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        # 하단 고정 버튼 위젯을 메인 레이아웃에 추가
        main_layout.addWidget(button_widget)
    
    def load_initial_data(self):
        """UI 완성 후 초기 데이터 로드"""
        if hasattr(self, '_initialization_complete') and self._initialization_complete:
            self.load_purchases_for_date(QDate.currentDate())

    def load_data_sources(self):
        try:
            if os.path.exists(self.margin_file):
                df = pd.read_excel(self.margin_file, engine='openpyxl')
                df = df.rename(columns={'상품번호': '상품ID'})
                if '대표옵션' in df.columns:
                    df['대표옵션'] = df['대표옵션'].astype(str).str.upper().isin(['O', 'Y', 'TRUE'])
                    df = df[df['대표옵션'] == True]
                # 옵션정보 컬럼도 포함하여 products_df 생성
                columns_to_keep = ['상품ID', '상품명']
                if '옵션정보' in df.columns:
                    columns_to_keep.append('옵션정보')
                self.products_df = df[columns_to_keep].drop_duplicates().sort_values(by='상품명')
            if os.path.exists(self.purchase_file):
                with open(self.purchase_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.all_purchases_data = json.loads(content) if content else {'purchases': []}
        except Exception as e:
            QMessageBox.critical(self, "오류", f"데이터 소스 로드 오류: {e}")

    def normalize_product_id(self, product_id):
        """product_id 정규화 (.0 제거)"""
        product_id_str = str(product_id)
        if product_id_str.endswith('.0'):
            return product_id_str[:-2]
        return product_id_str

    def safe_get_option_info(self, product):
        """상품 데이터에서 옵션정보를 안전하게 가져오기"""
        import pandas as pd
        option_info = product.get('옵션정보', '')
        
        # pandas NA 값 처리
        if pd.isna(option_info):
            return ''
        
        # 문자열로 변환하고 공백 제거
        return str(option_info).strip()

    def find_purchase_value(self, product_id, purchase_map, option_info=''):
        """product_id와 옵션정보에 대한 가구매 값 찾기"""
        clean_id = self.normalize_product_id(product_id)
        dotted_id = clean_id + '.0'
        
        # 3-tuple 키로 옵션별 설정 확인
        option_key = (clean_id, option_info)
        dotted_option_key = (dotted_id, option_info)
        
        # 옵션별 설정이 있으면 우선 사용
        if option_key in purchase_map:
            return purchase_map[option_key]
        if dotted_option_key in purchase_map:
            return purchase_map[dotted_option_key]
        
        # 기존 방식 (하위 호환성)
        return purchase_map.get(clean_id, purchase_map.get(dotted_id, 0))
    
    def clear_table_widgets(self):
        """테이블 위젯들을 안전하게 정리"""
        try:
            for row in range(self.product_table.rowCount()):
                # 체크박스 정리
                checkbox = self.product_table.cellWidget(row, 0)
                if checkbox:
                    checkbox.deleteLater()
                # 스핀박스 정리
                spinbox = self.product_table.cellWidget(row, 3)
                if spinbox:
                    spinbox.deleteLater()
            
            # 테이블 내용 클리어
            self.product_table.clearContents()
        except Exception as e:
            import logging
            logging.error(f"가구매 테이블 위젯 정리 중 오류: {e}")

    def load_purchases_for_date(self, q_date):
        target_date_str = q_date.toString("yyyy-MM-dd")
        
        # 기존 위젯들 정리
        self.clear_table_widgets()
        
        # 모든 형식의 product_id를 포함하는 purchase_map 생성 (정규화된 ID 사용)
        purchase_map = {}
        for e in self.all_purchases_data.get('purchases', []):
            if e.get('start_date') == target_date_str:
                product_id = str(e['product_id'])
                normalized_product_id = self.normalize_product_id(product_id)
                option_info = e.get('option_info', '')
                
                # 옵션별 설정이 있으면 3-tuple 키로 저장
                if option_info:
                    purchase_map[(normalized_product_id, option_info)] = e['purchase_count']
                else:
                    # 기존 방식 (하위 호환성) - 정규화된 ID 사용
                    purchase_map[normalized_product_id] = e['purchase_count']
        
        self.product_table.setRowCount(len(self.products_df))
        
        for row, (_, product) in enumerate(self.products_df.iterrows()):
            product_id = str(product['상품ID'])
            option_info = self.safe_get_option_info(product)
            
            # 체크박스 생성 및 이벤트 연결
            checkbox = QCheckBox()
            checkbox.clicked.connect(self.update_selected_count)
            self.product_table.setCellWidget(row, 0, checkbox)
            
            self.product_table.setItem(row, 1, QTableWidgetItem(product_id))
            self.product_table.setItem(row, 2, QTableWidgetItem(str(product['상품명'])))
            self.product_table.setItem(row, 3, QTableWidgetItem(option_info))
            
            # 스핀박스 생성
            spinbox = QSpinBox()
            spinbox.setRange(0, 9999)
            spinbox.setSuffix(" 개")
            # 호환성을 위해 두 형식 모두 확인
            purchase_value = self.find_purchase_value(product_id, purchase_map, option_info)
            spinbox.setValue(purchase_value)
            self.product_table.setCellWidget(row, 4, spinbox)
        
        self.filter_products()
        self.update_selected_count()  # 초기 상태 업데이트

    def copy_purchases(self):
        source_date_str = self.source_date_edit.date().toString("yyyy-MM-dd")
        
        # load_purchases_for_date()와 동일한 방식으로 purchase_map 생성 (정규화된 ID 사용)
        purchase_map = {}
        for e in self.all_purchases_data.get('purchases', []):
            if e.get('start_date') == source_date_str:
                product_id = str(e['product_id'])
                normalized_product_id = self.normalize_product_id(product_id)
                option_info = e.get('option_info', '')
                
                # 옵션별 설정이 있으면 3-tuple 키로 저장
                if option_info:
                    purchase_map[(normalized_product_id, option_info)] = e['purchase_count']
                else:
                    # 기존 방식 (하위 호환성) - 정규화된 ID 사용
                    purchase_map[normalized_product_id] = e['purchase_count']
        
        if not purchase_map:
            QMessageBox.information(self, "알림", f"{source_date_str}에 저장된 가구매 설정이 없습니다.")
            return
            
        # 현재 테이블에 적용 (올바른 컬럼 인덱스 사용)
        applied_count = 0
        for row in range(self.product_table.rowCount()):
            product_id_item = self.product_table.item(row, 1)      # 상품ID
            option_info_item = self.product_table.item(row, 3)     # 옵션정보 (컬럼 3)
            spinbox = self.product_table.cellWidget(row, 4)        # 스핀박스 (컬럼 4)
            if product_id_item and spinbox:
                product_id = product_id_item.text()
                option_info = option_info_item.text() if option_info_item else ''
                
                # find_purchase_value()와 동일한 방식으로 찾기
                purchase_value = self.find_purchase_value(product_id, purchase_map, option_info)
                if purchase_value > 0:
                    spinbox.setValue(purchase_value)
                    applied_count += 1
        
        QMessageBox.information(self, "복사 완료", f"{applied_count}개 상품의 가구매 설정을 복사했습니다.")

    def toggle_all_selection(self):
        is_checked = self.select_all_checkbox.isChecked()
        for row in range(self.product_table.rowCount()):
            if not self.product_table.isRowHidden(row):
                checkbox = self.product_table.cellWidget(row, 0)
                if checkbox:
                    checkbox.setChecked(is_checked)
        self.update_selected_count()

    def apply_to_selected(self):
        """선택된 항목에 일괄 적용 (예외 처리 강화)"""
        try:
            bulk_value = self.bulk_purchase.value()
            applied_count = 0
            for row in range(self.product_table.rowCount()):
                checkbox = self.product_table.cellWidget(row, 0)
                spinbox = self.product_table.cellWidget(row, 4)
                if checkbox and checkbox.isChecked() and spinbox:
                    spinbox.setValue(bulk_value)
                    applied_count += 1
            
            if applied_count > 0:
                QMessageBox.information(self, "적용 완료", f"{applied_count}개 상품에 {bulk_value}개 가구매를 적용했습니다.")
            else:
                QMessageBox.warning(self, "선택 없음", "적용할 상품을 먼저 선택해주세요.")
        except Exception as e:
            import logging
            logging.error(f"가구매 일괄 적용 중 오류: {e}")
            QMessageBox.critical(self, "오류", f"일괄 적용 중 오류가 발생했습니다:\n{str(e)}")

    def update_selected_count(self):
        """선택된 항목 수 업데이트 (예외 처리 강화)"""
        try:
            selected_count = 0
            total_visible = 0
            
            for row in range(self.product_table.rowCount()):
                if not self.product_table.isRowHidden(row):
                    total_visible += 1
                    checkbox = self.product_table.cellWidget(row, 0)
                    if checkbox and checkbox.isChecked():
                        selected_count += 1
            
            if hasattr(self, 'selected_count_label'):
                self.selected_count_label.setText(f"선택됨: {selected_count}개")
            
            # 적용 버튼 활성화 상태 업데이트
            if hasattr(self, 'apply_selected_button'):
                self.apply_selected_button.setEnabled(selected_count > 0)
        except Exception as e:
            import logging
            logging.error(f"가구매 선택 개수 업데이트 중 오류: {e}")
            if hasattr(self, 'selected_count_label'):
                self.selected_count_label.setText("선택됨: 오류")

    def filter_products(self):
        search_text = self.search_box.text().lower()
        for row in range(self.product_table.rowCount()):
            product_name = self.product_table.item(row, 2).text().lower()
            self.product_table.setRowHidden(row, search_text not in product_name)
        self.update_selected_count()  # 필터링 후 선택 수 업데이트

    def save_purchases(self):
        try:
            target_date_str = self.target_date_edit.date().toString("yyyy-MM-dd")
            other_days_purchases = [e for e in self.all_purchases_data.get('purchases', []) if e.get('start_date') != target_date_str]
            new_purchases = []
            for row in range(self.product_table.rowCount()):
                purchase_entry = {
                    'start_date': target_date_str, 'end_date': target_date_str,
                    'product_id': self.product_table.item(row, 1).text(),
                    'purchase_count': self.product_table.cellWidget(row, 4).value()
                }
                # 옵션정보가 있으면 추가
                option_info = self.product_table.item(row, 3).text()
                if option_info:
                    purchase_entry['option_info'] = option_info
                new_purchases.append(purchase_entry)
            self.all_purchases_data['purchases'] = other_days_purchases + new_purchases
            with open(self.purchase_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_purchases_data, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "완료", f"{target_date_str}의 가구매 설정이 저장되었습니다.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "오류", f"가구매 설정 저장 중 오류가 발생했습니다:\n{str(e)}")

class AIAnalysisResultsDialog(QDialog):
    def __init__(self, results_data, parent=None):
        super().__init__(parent)
        self.results_data = results_data
        self.setWindowTitle("🤖 AI 분석 결과")
        self.setMinimumSize(900, 700)
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 헤더
        header_layout = QHBoxLayout()
        header_label = QLabel("🤖 AI 분석 결과")
        header_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2563eb; margin: 10px 0px;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        # 분석 정보
        info_layout = QHBoxLayout()
        data_info = self.results_data.get('data_info', {})
        info_text = f"분석 상품: {data_info.get('total_products', 0)}개 | 분석 파일: {data_info.get('files_analyzed', 0)}개"
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: #666; font-size: 12px;")
        info_layout.addWidget(info_label)
        info_layout.addStretch()

        layout.addLayout(header_layout)
        layout.addLayout(info_layout)

        # 탭 위젯 생성
        tab_widget = QTabWidget()

        # 요약 탭
        summary_tab = self.create_summary_tab()
        tab_widget.addTab(summary_tab, "📊 요약")

        # 추천사항 탭
        recommendations_tab = self.create_recommendations_tab()
        tab_widget.addTab(recommendations_tab, "💡 추천사항")

        # 클러스터 분석 탭
        cluster_tab = self.create_cluster_tab()
        tab_widget.addTab(cluster_tab, "🎯 클러스터 분석")

        # 고급 분석 탭들 (Context7 기반)
        trend_tab = self.create_trend_analysis_tab()
        tab_widget.addTab(trend_tab, "📈 트렌드 분석")

        advanced_cluster_tab = self.create_advanced_clustering_tab()
        tab_widget.addTab(advanced_cluster_tab, "🔬 고급 클러스터링")

        pattern_tab = self.create_pattern_analysis_tab()
        tab_widget.addTab(pattern_tab, "🎯 패턴 분석")

        layout.addWidget(tab_widget)

        # 닫기 버튼
        close_btn = QPushButton("닫기")
        close_btn.setStyleSheet("QPushButton { background-color: #6c757d; color: white; font-weight: bold; padding: 8px 16px; border: none; border-radius: 4px; } QPushButton:hover { background-color: #545b62; }")
        close_btn.clicked.connect(self.accept)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

    def create_summary_tab(self):
        scroll_area = QScrollArea()
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)

        summary = self.results_data.get('summary', {})

        # 전체 개요
        overview_card = QGroupBox("📋 분석 개요")
        overview_layout = QGridLayout(overview_card)

        overview_data = [
            ("총 추천 수", summary.get("총_추천수", 0)),
            ("긴급 추천", summary.get("긴급_추천수", 0)),
            ("높은 우선순위", summary.get("높은_우선순위", 0)),
            ("포트폴리오 건강도", summary.get("포트폴리오_건강도", "알 수 없음"))
        ]

        for i, (label, value) in enumerate(overview_data):
            label_widget = QLabel(f"{label}:")
            label_widget.setStyleSheet("font-weight: bold;")
            value_widget = QLabel(str(value))
            value_widget.setStyleSheet("color: #2563eb; font-weight: bold;")

            overview_layout.addWidget(label_widget, i // 2, (i % 2) * 2)
            overview_layout.addWidget(value_widget, i // 2, (i % 2) * 2 + 1)

        layout.addWidget(overview_card)

        # 비즈니스 임팩트
        impact_card = QGroupBox("💰 예상 비즈니스 임팩트")
        impact_layout = QVBoxLayout(impact_card)

        impact_data = [
            ("예상 매출 증가", f"{summary.get('예상_매출_증가', 0):,.0f}원"),
            ("예상 이익 증가", f"{summary.get('예상_이익_증가', 0):,.0f}원"),
            ("ROI 개선율", f"{summary.get('ROI_개선율', 0):.1f}%")
        ]

        for label, value in impact_data:
            item_layout = QHBoxLayout()
            label_widget = QLabel(f"{label}:")
            label_widget.setStyleSheet("font-weight: bold;")
            value_widget = QLabel(value)
            value_widget.setStyleSheet("color: #059669; font-weight: bold; font-size: 14px;")

            item_layout.addWidget(label_widget)
            item_layout.addStretch()
            item_layout.addWidget(value_widget)
            impact_layout.addLayout(item_layout)

        layout.addWidget(impact_card)

        layout.addStretch()
        scroll_area.setWidget(content_widget)
        return scroll_area

    def create_recommendations_tab(self):
        scroll_area = QScrollArea()
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)

        summary = self.results_data.get('summary', {})
        recommendations = summary.get("주요_추천사항", [])

        if not recommendations:
            no_data_label = QLabel("추천사항이 없습니다.")
            no_data_label.setStyleSheet("color: #666; font-style: italic; text-align: center; margin: 50px;")
            layout.addWidget(no_data_label)
        else:
            for i, rec in enumerate(recommendations, 1):
                rec_card = QGroupBox(f"추천 {i}: {rec.get('상품명', 'Unknown')}")
                rec_layout = QVBoxLayout(rec_card)

                # 추천 유형 및 우선순위
                type_layout = QHBoxLayout()
                type_label = QLabel(f"유형: {rec.get('추천유형', 'Unknown')}")
                type_label.setStyleSheet("font-weight: bold; color: #8b5cf6;")
                priority_label = QLabel(f"우선순위: {rec.get('우선순위', 'Unknown')}")
                priority_label.setStyleSheet("font-weight: bold; color: #dc2626;")

                type_layout.addWidget(type_label)
                type_layout.addStretch()
                type_layout.addWidget(priority_label)
                rec_layout.addLayout(type_layout)

                # 액션
                action_label = QLabel("권장 액션:")
                action_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
                action_text = QLabel(rec.get('액션', 'No action specified'))
                action_text.setStyleSheet("color: #333; margin: 5px 0px; padding: 10px; background-color: #f8f9fa; border-radius: 4px;")
                action_text.setWordWrap(True)

                rec_layout.addWidget(action_label)
                rec_layout.addWidget(action_text)

                layout.addWidget(rec_card)

        layout.addStretch()
        scroll_area.setWidget(content_widget)
        return scroll_area

    def create_cluster_tab(self):
        scroll_area = QScrollArea()
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)

        analysis_results = self.results_data.get('analysis_results', {})
        cluster_analysis = analysis_results.get('cluster_analysis', {})

        if not cluster_analysis:
            no_data_label = QLabel("클러스터 분석 데이터가 없습니다.")
            no_data_label.setStyleSheet("color: #666; font-style: italic; text-align: center; margin: 50px;")
            layout.addWidget(no_data_label)
        else:
            for cluster_id, cluster_info in cluster_analysis.items():
                cluster_card = QGroupBox(f"클러스터 {cluster_id}: {cluster_info.get('label', 'Unknown')}")
                cluster_layout = QVBoxLayout(cluster_card)

                # 통계 정보
                stats = cluster_info.get('stats', {})
                stats_layout = QGridLayout()

                stats_data = [
                    ("상품 수", f"{stats.get('product_count', 0)}개"),
                    ("총 매출", f"{stats.get('total_sales', 0):,.0f}원"),
                    ("평균 이익률", f"{stats.get('avg_profit_margin', 0):.1f}%"),
                    ("평균 광고비율", f"{stats.get('avg_ad_ratio', 0):.1f}%")
                ]

                for i, (label, value) in enumerate(stats_data):
                    label_widget = QLabel(f"{label}:")
                    label_widget.setStyleSheet("font-weight: bold;")
                    value_widget = QLabel(value)
                    value_widget.setStyleSheet("color: #2563eb;")

                    stats_layout.addWidget(label_widget, i // 2, (i % 2) * 2)
                    stats_layout.addWidget(value_widget, i // 2, (i % 2) * 2 + 1)

                cluster_layout.addLayout(stats_layout)

                # 추천 액션
                action_label = QLabel("추천 액션:")
                action_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
                action_text = QLabel(cluster_info.get('recommended_action', 'No action specified'))
                action_text.setStyleSheet("color: #333; margin: 5px 0px; padding: 10px; background-color: #f0f9ff; border-radius: 4px;")
                action_text.setWordWrap(True)

                cluster_layout.addWidget(action_label)
                cluster_layout.addWidget(action_text)

                # 우선순위
                priority_label = QLabel(f"우선순위: {cluster_info.get('priority', 'Unknown')}")
                priority_label.setStyleSheet("font-weight: bold; color: #dc2626; margin-top: 5px;")
                cluster_layout.addWidget(priority_label)

                layout.addWidget(cluster_card)

        layout.addStretch()
        scroll_area.setWidget(content_widget)
        return scroll_area

    def create_trend_analysis_tab(self):
        """트렌드 분석 탭 생성"""
        scroll_area = QScrollArea()
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)

        analysis_results = self.results_data.get('analysis_results', {})
        trend_analysis = analysis_results.get('enhanced_analytics', {}).get('trend_analysis', {})

        if trend_analysis.get('error'):
            error_label = QLabel(f"❌ {trend_analysis['error']}")
            error_label.setStyleSheet("color: #dc2626; font-style: italic; text-align: center; margin: 50px;")
            layout.addWidget(error_label)
        elif not trend_analysis:
            no_data_label = QLabel("📈 트렌드 분석 데이터가 없습니다.")
            no_data_label.setStyleSheet("color: #666; font-style: italic; text-align: center; margin: 50px;")
            layout.addWidget(no_data_label)
        else:
            # 트렌드 요약
            summary = trend_analysis.get('summary', {})
            summary_card = QGroupBox("📊 트렌드 요약")
            summary_layout = QVBoxLayout(summary_card)

            trend_info = [
                ("📈 전반적 트렌드", summary.get('trend_direction', '알수없음')),
                ("💚 비즈니스 건강도", summary.get('business_health', '보통')),
                ("📅 분석 데이터 점수", f"{trend_analysis.get('data_points', 0)}개")
            ]

            for label, value in trend_info:
                info_layout = QHBoxLayout()
                label_widget = QLabel(label)
                label_widget.setStyleSheet("font-weight: bold;")
                value_widget = QLabel(str(value))
                value_widget.setStyleSheet("color: #2563eb; font-weight: bold;")

                info_layout.addWidget(label_widget)
                info_layout.addStretch()
                info_layout.addWidget(value_widget)
                summary_layout.addLayout(info_layout)

            layout.addWidget(summary_card)

            # 매출 트렌드
            sales_trend = trend_analysis.get('sales_trend', {})
            if sales_trend:
                sales_card = QGroupBox("💰 매출 트렌드")
                sales_layout = QGridLayout(sales_card)

                sales_data = [
                    ("방향", sales_trend.get('direction', '알수없음')),
                    ("기울기", str(sales_trend.get('slope', 0))),
                    ("신뢰도 (R²)", str(sales_trend.get('r_squared', 0))),
                    ("강도", sales_trend.get('strength', '보통'))
                ]

                for i, (label, value) in enumerate(sales_data):
                    label_widget = QLabel(f"{label}:")
                    label_widget.setStyleSheet("font-weight: bold;")
                    value_widget = QLabel(value)
                    value_widget.setStyleSheet("color: #059669;")

                    sales_layout.addWidget(label_widget, i // 2, (i % 2) * 2)
                    sales_layout.addWidget(value_widget, i // 2, (i % 2) * 2 + 1)

                layout.addWidget(sales_card)

            # 변동성 분석
            volatility = trend_analysis.get('volatility_analysis', {})
            if volatility:
                volatility_card = QGroupBox("📊 변동성 분석")
                volatility_layout = QGridLayout(volatility_card)

                volatility_data = [
                    ("매출 변동성", f"{volatility.get('sales_volatility', 0)}%"),
                    ("수익 변동성", f"{volatility.get('profit_volatility', 0)}%"),
                    ("안정성 점수", f"{volatility.get('stability_score', 0)}/100")
                ]

                for i, (label, value) in enumerate(volatility_data):
                    label_widget = QLabel(f"{label}:")
                    label_widget.setStyleSheet("font-weight: bold;")
                    value_widget = QLabel(value)
                    value_widget.setStyleSheet("color: #7c3aed;")

                    volatility_layout.addWidget(label_widget, i, 0)
                    volatility_layout.addWidget(value_widget, i, 1)

                layout.addWidget(volatility_card)

            # 추천사항
            recommendations = summary.get('recommendations', [])
            if recommendations:
                rec_card = QGroupBox("💡 트렌드 기반 추천사항")
                rec_layout = QVBoxLayout(rec_card)

                for i, rec in enumerate(recommendations, 1):
                    rec_label = QLabel(f"{i}. {rec}")
                    rec_label.setWordWrap(True)
                    rec_label.setStyleSheet("color: #333; margin: 5px 0px; padding: 8px; background-color: #f0f9ff; border-radius: 4px;")
                    rec_layout.addWidget(rec_label)

                layout.addWidget(rec_card)

        layout.addStretch()
        scroll_area.setWidget(content_widget)
        return scroll_area

    def create_advanced_clustering_tab(self):
        """고급 클러스터링 탭 생성"""
        scroll_area = QScrollArea()
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)

        analysis_results = self.results_data.get('analysis_results', {})
        advanced_clustering = analysis_results.get('enhanced_analytics', {}).get('advanced_clustering', {})

        if advanced_clustering.get('error'):
            error_label = QLabel(f"❌ {advanced_clustering['error']}")
            error_label.setStyleSheet("color: #dc2626; font-style: italic; text-align: center; margin: 50px;")
            layout.addWidget(error_label)
        elif not advanced_clustering:
            no_data_label = QLabel("🔬 고급 클러스터링 데이터가 없습니다.")
            no_data_label.setStyleSheet("color: #666; font-style: italic; text-align: center; margin: 50px;")
            layout.addWidget(no_data_label)
        else:
            # 알고리즘 비교 결과
            algorithm_comparison = advanced_clustering.get('algorithm_comparison', {})
            best_algorithm = advanced_clustering.get('best_algorithm', 'kmeans')

            if algorithm_comparison:
                comparison_card = QGroupBox("🔬 알고리즘 성능 비교")
                comparison_layout = QVBoxLayout(comparison_card)

                for algo_name, results in algorithm_comparison.items():
                    algo_layout = QHBoxLayout()

                    # 알고리즘 이름 및 선택 표시
                    algo_label = QLabel(f"{'⭐ ' if algo_name == best_algorithm else '  '}{algo_name.upper()}")
                    algo_label.setStyleSheet("font-weight: bold; color: #059669;" if algo_name == best_algorithm else "font-weight: bold;")

                    silhouette = results.get('silhouette_score', 0)
                    clusters = results.get('n_clusters', 0)

                    score_label = QLabel(f"실루엣: {silhouette:.3f}")
                    score_label.setStyleSheet("color: #2563eb;")

                    clusters_label = QLabel(f"클러스터: {clusters}개")
                    clusters_label.setStyleSheet("color: #7c3aed;")

                    if algo_name == 'dbscan' and 'n_noise' in results:
                        noise_label = QLabel(f"노이즈: {results['n_noise']}개")
                        noise_label.setStyleSheet("color: #dc2626;")
                        algo_layout.addWidget(noise_label)

                    algo_layout.addWidget(algo_label)
                    algo_layout.addStretch()
                    algo_layout.addWidget(score_label)
                    algo_layout.addWidget(clusters_label)

                    comparison_layout.addLayout(algo_layout)

                layout.addWidget(comparison_card)

            # 최적 알고리즘 클러스터 분석
            cluster_analysis = advanced_clustering.get('cluster_analysis', {})
            if cluster_analysis:
                clusters_card = QGroupBox(f"🎯 {best_algorithm.upper()} 클러스터 분석")
                clusters_layout = QVBoxLayout(clusters_card)

                for cluster_id, cluster_info in cluster_analysis.items():
                    cluster_widget = QGroupBox(f"클러스터 {cluster_id}: {cluster_info.get('label', 'Unknown')}")
                    cluster_layout = QVBoxLayout(cluster_widget)

                    # 통계 정보
                    stats = cluster_info.get('stats', {})
                    if stats:
                        stats_layout = QGridLayout()
                        stats_data = [
                            ("상품 수", f"{stats.get('product_count', 0)}개"),
                            ("평균 매출", f"{stats.get('avg_sales', 0):,.0f}원"),
                            ("평균 이익률", f"{stats.get('avg_profit_margin', 0):.1f}%"),
                            ("평균 광고비율", f"{stats.get('avg_ad_ratio', 0):.1f}%")
                        ]

                        for i, (label, value) in enumerate(stats_data):
                            label_widget = QLabel(f"{label}:")
                            label_widget.setStyleSheet("font-weight: bold;")
                            value_widget = QLabel(value)
                            value_widget.setStyleSheet("color: #2563eb;")

                            stats_layout.addWidget(label_widget, i // 2, (i % 2) * 2)
                            stats_layout.addWidget(value_widget, i // 2, (i % 2) * 2 + 1)

                        cluster_layout.addLayout(stats_layout)

                    # 추천 액션
                    action = cluster_info.get('recommended_action', 'No action specified')
                    action_label = QLabel(action)
                    action_label.setWordWrap(True)
                    action_label.setStyleSheet("color: #333; margin: 10px 0px; padding: 10px; background-color: #f0f9ff; border-radius: 4px;")
                    cluster_layout.addWidget(action_label)

                    clusters_layout.addWidget(cluster_widget)

                layout.addWidget(clusters_card)

            # 추천사항
            recommendations = advanced_clustering.get('recommendations', [])
            if recommendations:
                rec_card = QGroupBox("💡 고급 클러스터링 추천사항")
                rec_layout = QVBoxLayout(rec_card)

                for i, rec in enumerate(recommendations, 1):
                    rec_label = QLabel(f"{i}. {rec}")
                    rec_label.setWordWrap(True)
                    rec_label.setStyleSheet("color: #333; margin: 5px 0px; padding: 8px; background-color: #fef3c7; border-radius: 4px;")
                    rec_layout.addWidget(rec_label)

                layout.addWidget(rec_card)

        layout.addStretch()
        scroll_area.setWidget(content_widget)
        return scroll_area

    def create_pattern_analysis_tab(self):
        """패턴 분석 탭 생성"""
        scroll_area = QScrollArea()
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)

        analysis_results = self.results_data.get('analysis_results', {})
        pattern_analysis = analysis_results.get('enhanced_analytics', {}).get('pattern_analysis', {})

        if pattern_analysis.get('error'):
            error_label = QLabel(f"❌ {pattern_analysis['error']}")
            error_label.setStyleSheet("color: #dc2626; font-style: italic; text-align: center; margin: 50px;")
            layout.addWidget(error_label)
        elif not pattern_analysis:
            no_data_label = QLabel("🎯 패턴 분석 데이터가 없습니다.")
            no_data_label.setStyleSheet("color: #666; font-style: italic; text-align: center; margin: 50px;")
            layout.addWidget(no_data_label)
        else:
            # ABC 분석
            abc_analysis = pattern_analysis.get('abc_analysis', {})
            if abc_analysis and abc_analysis.get('category_stats'):
                abc_card = QGroupBox("🏆 ABC 분석 (파레토 원칙)")
                abc_layout = QVBoxLayout(abc_card)

                for stat in abc_analysis['category_stats']:
                    category = stat['abc_category']
                    count = stat['product_count']
                    sales = stat['total_sales']
                    profit = stat['total_profit']

                    category_layout = QHBoxLayout()

                    category_label = QLabel(f"등급 {category}")
                    category_label.setStyleSheet("font-weight: bold; color: #059669;")

                    details_label = QLabel(f"상품 {count}개 | 매출 {sales:,.0f}원 | 이익 {profit:,.0f}원")
                    details_label.setStyleSheet("color: #2563eb;")

                    category_layout.addWidget(category_label)
                    category_layout.addStretch()
                    category_layout.addWidget(details_label)

                    abc_layout.addLayout(category_layout)

                layout.addWidget(abc_card)

            # 파레토 분석
            pareto_analysis = pattern_analysis.get('pareto_analysis', {})
            if pareto_analysis:
                pareto_card = QGroupBox("📊 파레토 분석 (80-20 법칙)")
                pareto_layout = QVBoxLayout(pareto_card)

                contribution = pareto_analysis.get('top_20_percent_contribution', 0)
                efficiency = pareto_analysis.get('pareto_efficiency', '보통')

                pareto_info = QLabel(f"상위 20% 상품이 전체 매출의 {contribution}% 기여 (효율성: {efficiency})")
                pareto_info.setStyleSheet("font-weight: bold; color: #7c3aed; padding: 10px; background-color: #faf5ff; border-radius: 4px;")
                pareto_layout.addWidget(pareto_info)

                layout.addWidget(pareto_card)

            # 수익성 세그멘테이션
            profitability = pattern_analysis.get('profitability_segments', {})
            if profitability and profitability.get('segment_stats'):
                profit_card = QGroupBox("💰 수익성 세그멘테이션")
                profit_layout = QVBoxLayout(profit_card)

                for stat in profitability['segment_stats']:
                    segment = stat['profitability_segment']
                    count = stat['product_count']
                    total_profit = stat['total_profit']

                    segment_layout = QHBoxLayout()

                    segment_label = QLabel(f"{segment} 상품")
                    segment_label.setStyleSheet("font-weight: bold;")

                    details_label = QLabel(f"{count}개 (총 이익: {total_profit:,.0f}원)")
                    details_label.setStyleSheet("color: #059669;")

                    segment_layout.addWidget(segment_label)
                    segment_layout.addStretch()
                    segment_layout.addWidget(details_label)

                    profit_layout.addLayout(segment_layout)

                layout.addWidget(profit_card)

            # 리워드 효율성
            reward_efficiency = pattern_analysis.get('reward_efficiency', {})
            if reward_efficiency and not reward_efficiency.get('no_reward_data'):
                reward_card = QGroupBox("🎁 리워드 효율성 분석")
                reward_layout = QVBoxLayout(reward_card)

                avg_roi = reward_efficiency.get('average_reward_roi', 0)
                grade = reward_efficiency.get('efficiency_grade', '보통')
                total_products = reward_efficiency.get('total_reward_products', 0)

                reward_info = QLabel(f"평균 ROI: {avg_roi:.2f} | 효율성: {grade} | 리워드 적용 상품: {total_products}개")
                reward_info.setStyleSheet("font-weight: bold; color: #dc2626; padding: 10px; background-color: #fef2f2; border-radius: 4px;")
                reward_layout.addWidget(reward_info)

                layout.addWidget(reward_card)

            # 전략적 인사이트
            strategic_insights = pattern_analysis.get('strategic_insights', [])
            if strategic_insights:
                insights_card = QGroupBox("🧠 전략적 인사이트")
                insights_layout = QVBoxLayout(insights_card)

                for i, insight in enumerate(strategic_insights, 1):
                    insight_label = QLabel(f"{i}. {insight}")
                    insight_label.setWordWrap(True)
                    insight_label.setStyleSheet("color: #333; margin: 5px 0px; padding: 8px; background-color: #ecfdf5; border-radius: 4px;")
                    insights_layout.addWidget(insight_label)

                layout.addWidget(insights_card)

            # 우선순위 액션
            action_priorities = pattern_analysis.get('action_priorities', [])
            if action_priorities:
                actions_card = QGroupBox("⚡ 우선순위 액션 플랜")
                actions_layout = QVBoxLayout(actions_card)

                for action in action_priorities:
                    priority = action.get('priority', '보통')
                    action_text = action.get('action', 'No action')
                    category = action.get('category', '일반')

                    action_layout = QHBoxLayout()

                    priority_label = QLabel(f"[{priority}]")
                    priority_color = "#dc2626" if priority == "긴급" else "#059669" if priority == "최우선" else "#2563eb"
                    priority_label.setStyleSheet(f"font-weight: bold; color: {priority_color};")

                    action_label = QLabel(f"{action_text} ({category})")
                    action_label.setWordWrap(True)
                    action_label.setStyleSheet("color: #333;")

                    action_layout.addWidget(priority_label)
                    action_layout.addWidget(action_label)

                    actions_layout.addLayout(action_layout)

                layout.addWidget(actions_card)

        layout.addStretch()
        scroll_area.setWidget(content_widget)
        return scroll_area

class ModernSalesAutomationApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Pydantic Settings 초기화
        self.settings = get_settings()

        # 기존 변수들을 settings에서 가져오기 (안전한 방식)
        self.download_folder_path = str(self.settings.paths.download_dir) if self.settings.paths.download_dir else ""
        self.password = self.settings.file_processing.order_file_password

        # config.py와의 호환성을 위해 전역 변수도 업데이트
        if self.download_folder_path:
            config.DOWNLOAD_DIR = Path(self.download_folder_path)

        self.worker = None
        self.manual_worker = None
        self.weekly_worker = None
        self.ai_worker = None

        # 오류 추적 시스템
        self.error_messages = []  # 오류 메시지 리스트
        self.error_count = 0      # 오류 카운터

        self.init_ui()
        self.setup_logging()
        self.load_settings()

        # 구조화된 로깅 초기화
        setup_app_logging()
        self.app_logger = get_logger("MainApp")

        # 자동 업데이트 시스템 초기화
        self.updater = SalesAutomationUpdater(current_version="2.0.0")

        # 시작 시 업데이트 확인 (백그라운드) - 비활성화
        # if self.settings.check_updates:
        #     QTimer.singleShot(3000, self.check_for_updates)  # 3초 후 확인

        # Context7 모범 사례: UI 컴포넌트 초기화
        self.init_ui_components()

    def init_ui_components(self):
        """Context7 모범 사례: UI 컴포넌트 초기화"""
        if not UI_COMPONENTS_AVAILABLE:
            return

        # 알림 관리자 초기화
        self.notification_manager = NotificationManager(self)

        # 스마트 툴팁 관리자 초기화
        self.tooltip_manager = SmartTooltipManager()

        # 워크플로우 가이드 초기화 (init_ui 이후에 추가됨)
        self.workflow_guide = None

        # 현재 워크플로우 상태
        self.current_workflow_step = WorkflowStep.FOLDER_SETUP

    def init_ui(self):
        self.setWindowTitle("📊 판매 데이터 자동화 & 순위 추적")
        self.setMinimumSize(1400, 900)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 헤더는 탭 위에 공통으로 표시
        main_layout.addLayout(self.create_header())

        # 탭 위젯 생성
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)

        # 탭 스타일 설정
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                background: #ffffff;
                margin-top: 8px;
            }
            QTabBar::tab {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-bottom: none;
                padding: 12px 24px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 600;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #2563eb;
                border-bottom: 2px solid #2563eb;
            }
            QTabBar::tab:hover:!selected {
                background: #e9ecef;
            }
        """)

        # 데이터 자동화 탭
        self.automation_tab = self.create_automation_tab()
        self.tab_widget.addTab(self.automation_tab, "📊 데이터 자동화")

        # 순위 추적 탭
        if RANK_TRACKING_AVAILABLE:
            self.rank_tracking_tab = RankTrackingWidget()
            self.tab_widget.addTab(self.rank_tracking_tab, "🔍 순위 추적")

        main_layout.addWidget(self.tab_widget)
        self.statusBar().showMessage("✅ 준비됨")

        # 초기화 완료 후 성능 버튼 상태 업데이트
        self.setup_smart_tooltips()

    def create_automation_tab(self):
        """데이터 자동화 탭 생성"""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Context7 모범 사례: 워크플로우 가이드 추가
        if UI_COMPONENTS_AVAILABLE:
            self.workflow_guide = WorkflowProgressGuide()
            self.workflow_guide.next_action_requested.connect(self.handle_workflow_action)
            layout.addWidget(self.workflow_guide)

            # 초기 단계 설정
            self.update_workflow_step(WorkflowStep.FOLDER_SETUP)

        layout.addWidget(self.create_settings_section())
        layout.addWidget(self.create_stats_section())
        layout.addWidget(self.create_log_section())

        return tab_widget

    def update_workflow_step(self, step: WorkflowStep):
        """Context7 모범 사례: 워크플로우 단계 업데이트"""
        if not UI_COMPONENTS_AVAILABLE or not self.workflow_guide:
            return

        self.current_workflow_step = step

        # 단계별 설정
        step_configs = {
            WorkflowStep.FOLDER_SETUP: UIComponentFactory.create_step_guide(
                step=WorkflowStep.FOLDER_SETUP,
                title="1단계: 폴더 설정",
                description="Excel 파일이 있는 다운로드 폴더를 선택해주세요",
                next_action="📁 폴더 선택" if not self.download_folder_path else None
            ),
            WorkflowStep.AUTOMATION_START: UIComponentFactory.create_step_guide(
                step=WorkflowStep.AUTOMATION_START,
                title="2단계: 자동화 시작",
                description="설정이 완료되었습니다. 자동화를 시작하세요",
                next_action="🚀 자동화 시작"
            ),
            WorkflowStep.MONITORING: UIComponentFactory.create_step_guide(
                step=WorkflowStep.MONITORING,
                title="자동화 실행 중",
                description="파일 모니터링이 시작되었습니다. 새 파일을 폴더에 넣으면 자동 처리됩니다",
                next_action="⏹️ 중지"
            ),
            WorkflowStep.RESULT_CHECK: UIComponentFactory.create_step_guide(
                step=WorkflowStep.RESULT_CHECK,
                title="3단계: 결과 확인",
                description="자동화가 완료되었습니다. 생성된 리포트를 확인하세요",
                next_action="📋 리포트 보기"
            ),
            WorkflowStep.ADVANCED_FEATURES: UIComponentFactory.create_step_guide(
                step=WorkflowStep.ADVANCED_FEATURES,
                title="추가 기능 활용",
                description="리워드 관리, 주간 리포트 등 고급 기능을 활용해보세요",
                next_action=None
            )
        }

        config = step_configs.get(step)
        if config:
            self.workflow_guide.update_step(config)

    def handle_workflow_action(self, action: str):
        """Context7 모범 사례: 워크플로우 액션 처리"""
        action_handlers = {
            "📁 폴더 선택": self.select_folder,
            "🚀 자동화 시작": self.start_monitoring,
            "📋 리포트 보기": self.open_report_folder
        }

        handler = action_handlers.get(action)
        if handler:
            handler()

    def open_report_folder(self):
        """리포트 폴더 열기"""
        import subprocess
        import platform

        try:
            report_dir = config.get_report_archive_dir()
            if report_dir.exists():
                if platform.system() == "Windows":
                    subprocess.run(["explorer", str(report_dir)])
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", str(report_dir)])
                else:  # Linux
                    subprocess.run(["xdg-open", str(report_dir)])

                self.show_notification(
                    NotificationType.SUCCESS,
                    "폴더 열기 완료",
                    f"리포트 폴더가 열렸습니다: {report_dir}"
                )
        except Exception as e:
            self.show_notification(
                NotificationType.ERROR,
                "폴더 열기 실패",
                f"리포트 폴더를 열 수 없습니다: {str(e)}"
            )

    def show_notification(self, notification_type: NotificationType, title: str, message: str, **kwargs):
        """Context7 모범 사례: 알림 표시"""
        if not UI_COMPONENTS_AVAILABLE:
            # 기존 로그 방식 대체
            self.update_log(f"[{notification_type.value.upper()}] {title}: {message}")
            return

        config_factory = {
            NotificationType.SUCCESS: UIComponentFactory.create_success_notification,
            NotificationType.ERROR: UIComponentFactory.create_error_notification,
            NotificationType.WARNING: lambda t, m, **k: UIComponentFactory.create_error_notification(t, m, **k),
            NotificationType.INFO: UIComponentFactory.create_success_notification
        }

        factory_method = config_factory.get(notification_type, UIComponentFactory.create_success_notification)
        config = factory_method(title, message, **kwargs)
        self.notification_manager.show_notification(config)

    def setup_smart_tooltips(self):
        """Context7 모범 사례: 스마트 툴팁 설정 (안전한 초기화 체크)"""
        if not UI_COMPONENTS_AVAILABLE:
            return

        # Context7 모범 사례: 안전한 초기화 체크
        if not hasattr(self, 'tooltip_manager') or self.tooltip_manager is None:
            self.tooltip_manager = SmartTooltipManager()

        # 폴더 선택 상태에 따른 툴팁
        self.update_folder_tooltip()

        # 버튼별 상태 기반 툴팁
        try:
            self.tooltip_manager.update_tooltip(
                self.start_btn, "automation_button",
                "ready" if self.download_folder_path else "disabled"
            )

            self.tooltip_manager.update_tooltip(
                self.password_input, "password_input", "default"
            )
        except Exception as e:
            # 툴팁 설정 실패 시 조용히 무시 (기능에 영향 없음)
            pass

    def update_folder_tooltip(self):
        """폴더 선택 상태 기반 툴팁 업데이트 (Context7 안전 처리)"""
        if not UI_COMPONENTS_AVAILABLE:
            return

        # Context7 모범 사례: 안전한 초기화 체크
        if not hasattr(self, 'tooltip_manager') or self.tooltip_manager is None:
            return

        try:
            if not self.download_folder_path:
                state = "empty"
            elif Path(self.download_folder_path).exists():
                state = "selected"
            else:
                state = "invalid"

            self.tooltip_manager.update_tooltip(
                self.folder_label, "folder_selection", state
            )
        except Exception as e:
            # 툴팁 업데이트 실패 시 조용히 무시
            pass

    def create_header(self):
        """Context7 모범 사례: 안전한 헤더 생성 (이모지 제외)"""
        header_layout = QHBoxLayout()
        # Context7 모범 사례: 이모지 대신 텍스트 아이콘 사용
        icon_label = QLabel("[판매데이터]")
        icon_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2563eb;")

        title_label = QLabel("자동화 시스템")
        title_label.setStyleSheet("font-size: 28px; font-weight: 700; color: #1f2937;")

        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        return header_layout

    def create_settings_section(self):
        settings_card = QGroupBox("⚙️ 설정")
        layout = QVBoxLayout(settings_card)
        form_layout = QGridLayout()
        self.folder_label = QLabel("폴더를 선택해주세요..."); self.folder_label.setStyleSheet("color: #666; font-style: italic;")
        folder_btn = AppleStyleButton("📁 폴더 선택", "fa5s.folder-open", color="#555")
        folder_btn.clicked.connect(self.select_folder)
        folder_layout = QHBoxLayout(); folder_layout.addWidget(self.folder_label, 1); folder_layout.addWidget(folder_btn)
        form_layout.addWidget(QLabel("다운로드 폴더:"), 0, 0); form_layout.addLayout(folder_layout, 0, 1)
        self.password_input = QLineEdit("1234"); self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.textChanged.connect(self.update_password)
        form_layout.addWidget(QLabel("주문조회 파일 암호:"), 1, 0); form_layout.addWidget(self.password_input, 1, 1)

        # Polars 엔진 설정 추가
        self.polars_checkbox = QCheckBox("🚀 Polars 엔진 사용 (고성능 모드)")
        self.polars_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                font-weight: 600;
                color: #059669;
                padding: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #d1d5db;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #059669;
                border-radius: 4px;
                background-color: #059669;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDQuNUw0LjUgOEwxMSAxIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }
        """)
        self.polars_checkbox.clicked.connect(self.toggle_polars_engine)
        self.polars_checkbox.setToolTip("Polars 엔진을 사용하면 대용량 데이터 처리 성능이 10-100배 향상됩니다.")

        # Polars 설정을 별도 행에 추가
        form_layout.addWidget(QLabel("데이터 처리 엔진:"), 2, 0)
        form_layout.addWidget(self.polars_checkbox, 2, 1)

        layout.addLayout(form_layout)
        
        control_layout = QHBoxLayout()
        self.start_btn = AppleStyleButton("🚀 자동화 시작", "fa5s.play", MaterialColors.SUCCESS); self.start_btn.clicked.connect(self.start_monitoring)
        self.stop_btn = AppleStyleButton("⏹️ 중지", "fa5s.stop", MaterialColors.ERROR); self.stop_btn.clicked.connect(self.stop_monitoring); self.stop_btn.setEnabled(False)
        self.manual_btn = AppleStyleButton("🔄 작업폴더 처리", "fa5s.cog", MaterialColors.WARNING); self.manual_btn.clicked.connect(self.manual_process)
        self.reward_btn = AppleStyleButton("💰 리워드 관리", "fa5s.gift", "#8b5cf6"); self.reward_btn.clicked.connect(self.show_reward_dialog)
        self.purchase_btn = AppleStyleButton("🛒 가구매 관리", "fa5s.shopping-cart", "#f59e0b"); self.purchase_btn.clicked.connect(self.show_purchase_dialog)
        self.weekly_report_btn = AppleStyleButton("📅 주간 리포트", "fa5s.calendar-week", "#10b981"); self.weekly_report_btn.clicked.connect(self.show_weekly_report_dialog)
        self.ai_analysis_btn = AppleStyleButton("🤖 AI 분석", "fa5s.brain", "#6366f1"); self.ai_analysis_btn.clicked.connect(self.start_ai_analysis)
        self.update_btn = AppleStyleButton("🔄 업데이트 확인", "fa5s.download", "#6b7280"); self.update_btn.clicked.connect(self.manual_check_updates)
        self.update_btn.setEnabled(False)
        self.update_btn.setToolTip("업데이트 기능이 비활성화되었습니다")

        # AI 버튼 활성화 여부 설정
        if not AI_MODULES_AVAILABLE:
            self.ai_analysis_btn.setEnabled(False)
            self.ai_analysis_btn.setToolTip("AI 모듈이 설치되지 않았습니다")


        # 기본 버튼들 첫 번째 줄
        control_layout.addWidget(self.start_btn); control_layout.addWidget(self.stop_btn); control_layout.addWidget(self.manual_btn)
        control_layout.addWidget(self.reward_btn); control_layout.addWidget(self.purchase_btn); control_layout.addWidget(self.weekly_report_btn)
        control_layout.addWidget(self.ai_analysis_btn); control_layout.addWidget(self.update_btn)
        control_layout.addStretch()
        layout.addLayout(control_layout)


        return settings_card

    def create_stats_section(self):
        stats_card = QGroupBox("📈 실시간 통계")
        kpi_layout = QGridLayout(stats_card)
        
        # 그리드 레이아웃 여백 설정
        kpi_layout.setContentsMargins(20, 20, 20, 20)
        kpi_layout.setSpacing(15)
        
        self.files_card = ModernDataCard("처리된 파일", "0개", "fa5s.file-alt", MaterialColors.SUCCESS)
        self.sales_card = ModernDataCard("총 매출", "₩0", "fa5s.dollar-sign", MaterialColors.PRIMARY)
        self.margin_card = ModernDataCard("순이익", "₩0", "fa5s.chart-line", MaterialColors.WARNING)
        self.error_card = ModernDataCard("에러", "0개", "fa5s.exclamation-triangle", MaterialColors.ERROR)
        
        # 에러 카드를 클릭 가능하게 만들기
        self.error_card.setCursor(Qt.PointingHandCursor)
        self.error_card.mousePressEvent = self.show_error_details
        
        # 그리드에 카드 추가 (여백 있게)
        kpi_layout.addWidget(self.files_card, 0, 0)
        kpi_layout.addWidget(self.sales_card, 0, 1)
        kpi_layout.addWidget(self.margin_card, 0, 2)
        kpi_layout.addWidget(self.error_card, 0, 3)
        
        # 컬럼별 균등 크기 설정
        kpi_layout.setColumnStretch(0, 1)
        kpi_layout.setColumnStretch(1, 1)
        kpi_layout.setColumnStretch(2, 1)
        kpi_layout.setColumnStretch(3, 1)
        
        return stats_card

    def create_log_section(self):
        log_card = QGroupBox("📋 처리 로그")
        layout = QVBoxLayout(log_card)
        self.log_output = ModernLogViewer()
        self.log_output.append("[INFO] 💡 애플리케이션이 준비되었습니다.")
        layout.addWidget(self.log_output)
        log_controls = QHBoxLayout()
        clear_btn = AppleStyleButton("🗑️ 로그 지우기", "fa5s.trash", MaterialColors.ERROR); clear_btn.clicked.connect(self.log_output.clear)
        log_controls.addWidget(clear_btn); log_controls.addStretch()
        layout.addLayout(log_controls)
        return log_card

    def setup_logging(self):
        """Context7 모범 사례: 안전한 UTF-8 로깅 설정"""
        try:
            # Context7 모범 사례: UTF-8 인코딩으로 콘솔 및 파일 로깅 설정
            import sys
            import io

            # 콘솔 출력을 UTF-8로 설정 (이모지 지원)
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
                sys.stderr.reconfigure(encoding='utf-8')

            # 로깅 핸들러 설정
            handlers = [
                # 파일 핸들러: UTF-8 인코딩
                logging.FileHandler('sales_automation.log', encoding='utf-8'),
                # 콘솔 핸들러: 안전한 콘솔 출력
                logging.StreamHandler(sys.stdout)
            ]

            # 로깅 기본 설정
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=handlers,
                force=True  # 기존 설정 덮어쓰기
            )

            # Context7 모범 사례: 로깅 테스트 (이모지 제외)
            logging.info("UTF-8 로깅 시스템 초기화 완료")

        except Exception as e:
            # 로깅 설정 실패 시 기본 설정
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
            print(f"\ub85c깅 설정 오류: {e}")

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "다운로드 폴더 선택")
        if folder:
            self.download_folder_path = folder
            # Context7 모범 사례: 안전한 폴더 라벨 설정 (이모지 제외)
            self.folder_label.setText(f"폴더: {folder}")
            # Pydantic Settings에 저장
            from pathlib import Path
            set_download_dir(Path(folder))
            self.update_log(f"[INFO] 다운로드 폴더 설정: {folder}")

            # Context7 모범 사례: 실시간 알림 및 워크플로우 업데이트
            self.show_notification(
                NotificationType.SUCCESS,
                "폴더 설정 완료",
                f"다운로드 폴더가 성공적으로 설정되었습니다\n경로: {folder}"
            )

            # 워크플로우 다음 단계로 진행
            self.update_workflow_step(WorkflowStep.PASSWORD_SETUP)

    def update_password(self):
        self.password = self.password_input.text()
        # Pydantic Settings에 저장
        set_order_file_password(self.password)

        # Context7 모범 사례: 패스워드 설정 알림
        if self.password:
            self.show_notification(
                NotificationType.SUCCESS,
                "패스워드 설정 완료",
                "주문조회 파일 암호가 설정되었습니다"
            )
            # 워크플로우 다음 단계로 진행
            if self.download_folder_path:
                self.update_workflow_step(WorkflowStep.READY_TO_START)

    def toggle_polars_engine(self):
        """Context7 모범 사례: Polars 엔진 토글 (안전한 유니코드 처리)"""
        use_polars = self.polars_checkbox.isChecked()
        set_engine(use_polars)

        # Pydantic Settings에 저장
        set_polars_enabled(use_polars)

        current_engine = get_current_engine()
        engine_status = "활성화" if use_polars else "비활성화"

        # Context7 모범 사례: 안전한 로깅 (이모지 제거)
        safe_log_message = f"[INFO] Polars 엔진 {engine_status}: {current_engine} 사용"
        self.update_log(safe_log_message)

        if use_polars:
            self.update_log("[INFO] 고성능 모드 활성화 - 대용량 데이터 처리 속도가 향상됩니다")
        else:
            self.update_log("[INFO] 표준 모드 활성화 - Pandas 엔진을 사용합니다")

        # Context7 모범 사례: 알림 시스템 통합
        notification_title = "Polars 엔진 활성화" if use_polars else "Pandas 엔진 활성화"
        notification_message = f"데이터 처리 엔진이 {current_engine}으로 전환되었습니다"

        self.show_notification(
            NotificationType.SUCCESS,
            notification_title,
            notification_message
        )



    @log_performance
    def start_monitoring(self):
        if not self.download_folder_path:
            # Context7 모범 사례: 에러 알림 표시
            self.show_notification(
                NotificationType.ERROR,
                "설정 오류",
                "다운로드 폴더를 먼저 선택해주세요"
            )
            QMessageBox.warning(self, "설정 오류", "다운로드 폴더를 먼저 선택해주세요.")
            return

        # 구조화된 로깅
        self.app_logger.info(
            "자동화 모니터링 시작",
            download_folder=self.download_folder_path,
            password_set=bool(self.password),
            polars_enabled=self.polars_checkbox.isChecked()
        )

        stop_flag_path = os.path.join(config.BASE_DIR, 'stop.flag')
        if os.path.exists(stop_flag_path):
            try:
                os.remove(stop_flag_path)
                self.update_log("[INFO] 이전 중지 플래그 파일을 삭제했습니다.")
            except Exception as e:
                self.update_log(f"[ERROR] 중지 플래그 파일 삭제 실패: {e}")

        # Context7 모범 사례: 시작 알림 및 워크플로우 업데이트
        self.show_notification(
            NotificationType.INFO,
            "자동화 시작",
            "판매 데이터 자동화 모니터링을 시작합니다"
        )
        self.update_workflow_step(WorkflowStep.MONITORING)

        self.set_controls_enabled(False)
        self.worker = ModernWorker(self.download_folder_path, self.password)
        self.worker.output_signal.connect(self.update_log)
        self.worker.finished_signal.connect(self.on_monitoring_finished)
        self.worker.error_signal.connect(self.on_error)
        self.worker.stats_signal.connect(self.update_stats)  # 통계 시그널 연결
        self.worker.start()

    def stop_monitoring(self):
        self.update_log("[INFO] ⏹️ 자동화 중지를 요청합니다...")
        try:
            stop_flag_path = os.path.join(config.BASE_DIR, 'stop.flag')
            with open(stop_flag_path, 'w') as f:
                f.write('stop')
            self.update_log("[INFO] 'stop.flag' 파일 생성 완료. 현재 작업 완료 후 모니터링이 종료됩니다.")
            self.stop_btn.setEnabled(False)
        except Exception as e:
            self.update_log(f"[ERROR] 중지 신호 파일 생성 실패: {e}")

    def manual_process(self):
        if not self.download_folder_path:
            # Context7 모범 사례: 에러 알림 표시
            self.show_notification(
                NotificationType.ERROR,
                "설정 오류",
                "다운로드 폴더를 먼저 선택해주세요"
            )
            QMessageBox.warning(self, "설정 오류", "다운로드 폴더를 먼저 선택해주세요.")
            return

        # Context7 모범 사례: 수동 처리 시작 알림
        self.show_notification(
            NotificationType.INFO,
            "수동 처리 시작",
            "작업폴더의 파일들을 수동으로 처리합니다"
        )

        self.set_controls_enabled(False)
        self.manual_worker = ModernManualWorker(self.download_folder_path, self.password)
        self.manual_worker.output_signal.connect(self.update_log)
        self.manual_worker.error_signal.connect(self.on_error)  # 오류 시그널 연결
        self.manual_worker.finished_signal.connect(self.on_manual_finished)
        self.manual_worker.stats_signal.connect(self.update_stats)  # 통계 시그널 연결
        self.manual_worker.start()

    def show_reward_dialog(self):
        dialog = ModernRewardDialog(self)
        dialog.exec()

    def show_purchase_dialog(self):
        dialog = PurchaseManagerDialog(self)
        dialog.exec()

    def show_weekly_report_dialog(self):
        if not self.download_folder_path:
            QMessageBox.warning(self, "설정 오류", "다운로드 폴더를 먼저 선택해주세요.")
            return
        dialog = WeeklyReportDialog(self)
        if dialog.exec():
            start_date, end_date = dialog.get_dates()
            if start_date and end_date:  # 날짜 검증 통과한 경우만 실행
                self.run_weekly_report_creation(start_date, end_date)
            else:
                QMessageBox.warning(self, "날짜 오류", "올바른 날짜 범위를 선택해주세요.")

    def start_ai_analysis(self):
        """AI 분석 시작"""
        if not self.download_folder_path:
            QMessageBox.warning(self, "설정 오류", "다운로드 폴더를 먼저 선택해주세요.")
            return

        if not AI_MODULES_AVAILABLE:
            QMessageBox.critical(self, "AI 모듈 오류", "AI 분석 모듈이 설치되지 않았습니다.\n\nscikit-learn, polars 패키지를 설치해주세요.")
            return

        # 확인 대화상자
        reply = QMessageBox.question(
            self,
            "AI 분석 시작",
            "리포트 보관함의 최신 데이터를 분석하여 AI 기반 비즈니스 인사이트를 생성합니다.\n\n분석을 시작하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # AI 분석 워커 초기화 및 시작
        self.set_controls_enabled(False)
        self.ai_worker = AIAnalysisWorker(self.download_folder_path)
        self.ai_worker.output_signal.connect(self.update_log)
        self.ai_worker.error_signal.connect(self.on_error)
        self.ai_worker.finished_signal.connect(self.on_ai_analysis_finished)
        self.ai_worker.results_signal.connect(self.on_ai_analysis_results)
        self.ai_worker.start()

        self.update_log("[INFO] 🤖 AI 분석을 시작합니다...")

    def on_ai_analysis_finished(self):
        """AI 분석 완료 후 처리"""
        self.ai_worker = None
        self.set_controls_enabled(True)
        self.update_log("[INFO] ✅ AI 분석이 완료되었습니다.")

    def on_ai_analysis_results(self, results_data):
        """AI 분석 결과 받아서 다이얼로그 표시"""
        try:
            # 결과 다이얼로그 표시
            dialog = AIAnalysisResultsDialog(results_data, self)
            dialog.exec()
        except Exception as e:
            self.update_log(f"[ERROR] AI 분석 결과 표시 중 오류: {str(e)}")
            QMessageBox.critical(self, "오류", f"AI 분석 결과를 표시하는 중 오류가 발생했습니다:\n{str(e)}")

    def run_weekly_report_creation(self, start_date, end_date):
        self.set_controls_enabled(False)
        self.weekly_worker = WeeklyWorker(start_date, end_date, self.download_folder_path)
        self.weekly_worker.output_signal.connect(self.update_log)
        self.weekly_worker.error_signal.connect(self.on_error)  # 오류 시그널 연결
        self.weekly_worker.finished_signal.connect(self.on_weekly_report_finished)
        self.weekly_worker.start()

    def on_monitoring_finished(self):
        self.set_controls_enabled(True)
        self.update_log("[INFO] ⏹️ 모니터링이 중지되었습니다.")

        # Context7 모범 사례: 완료 알림 및 워크플로우 업데이트
        self.show_notification(
            NotificationType.SUCCESS,
            "모니터링 완료",
            "판매 데이터 자동화 모니터링이 완료되었습니다"
        )
        self.update_workflow_step(WorkflowStep.COMPLETED)

    def on_manual_finished(self):
        self.set_controls_enabled(True)

        # Context7 모범 사례: 수동 처리 완료 알림
        self.show_notification(
            NotificationType.SUCCESS,
            "수동 처리 완료",
            "작업폴더의 파일 처리가 완료되었습니다"
        )

    def on_weekly_report_finished(self):
        self.set_controls_enabled(True)
        self.update_log("[INFO] ✅ 주간 리포트 생성이 완료되었습니다.")

        # Context7 모범 사례: 주간 리포트 완료 알림
        self.show_notification(
            NotificationType.SUCCESS,
            "주간 리포트 완료",
            "주간 통합 리포트가 성공적으로 생성되었습니다"
        )

    def update_stats(self, stats_dict):
        """통계 카드들을 업데이트"""
        try:
            if 'files' in stats_dict:
                self.files_card.update_value(stats_dict['files'])
            if 'sales' in stats_dict:
                self.sales_card.update_value(stats_dict['sales'])
            if 'profit' in stats_dict:
                self.margin_card.update_value(stats_dict['profit'])
        except Exception as e:
            self.update_log(f"[DEBUG] 통계 업데이트 중 오류: {e}")

    def on_error(self, msg):
        self.update_log(msg)

        # 구조화된 로깅으로 에러 기록
        if hasattr(self, 'app_logger'):
            self.app_logger.error(
                "애플리케이션 에러",
                error_message=msg,
                error_type=self.classify_error(msg),
                error_count=self.error_count + 1
            )

        # 오류 메시지 추가 (시간과 함께 저장)
        error_entry = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'message': msg,
            'type': self.classify_error(msg)
        }
        self.error_messages.append(error_entry)

        # 오류 카운터 업데이트
        self.error_count += 1
        self.error_card.update_value(f"{self.error_count}개")

        # 최근 100개 오류만 유지 (메모리 관리)
        if len(self.error_messages) > 100:
            self.error_messages = self.error_messages[-100:]

    def classify_error(self, msg):
        """오류 메시지를 분류하여 타입 반환"""
        msg_lower = msg.lower()
        if 'file' in msg_lower or '파일' in msg:
            return '파일 오류'
        elif 'permission' in msg_lower or '권한' in msg:
            return '권한 오류'
        elif 'memory' in msg_lower or '메모리' in msg:
            return '메모리 오류'
        elif 'network' in msg_lower or '네트워크' in msg:
            return '네트워크 오류'
        elif 'validation' in msg_lower or '검증' in msg:
            return '검증 오류'
        else:
            return '일반 오류'

    def show_error_details(self, event):
        """오류 상세 정보를 팝업으로 표시"""
        if self.error_count == 0:
            QMessageBox.information(self, "오류 없음", "현재까지 발생한 오류가 없습니다.")
            return
        
        dialog = ErrorDetailsDialog(self.error_messages, self)
        dialog.exec()

    def update_log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"

        # GUI 로그 출력
        self.log_output.append(formatted_message)
        self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())

        # 구조화된 로깅에도 기록
        if hasattr(self, 'app_logger'):
            # 로그 레벨 자동 감지
            if "[ERROR]" in message:
                self.app_logger.error(message)
            elif "[WARNING]" in message or "[WARN]" in message:
                self.app_logger.warning(message)
            else:
                self.app_logger.info(message)

    def set_controls_enabled(self, enabled):
        """Context7 모범 사례: 상태 기반 시각적 피드백을 포함한 컨트롤 설정"""

        # 기본 활성화/비활성화
        self.start_btn.setEnabled(enabled)
        self.manual_btn.setEnabled(enabled)
        self.weekly_report_btn.setEnabled(enabled)
        self.reward_btn.setEnabled(enabled)
        self.purchase_btn.setEnabled(enabled)
        self.stop_btn.setEnabled(not enabled)

        # Context7 모범 사례: 상태에 따른 시각적 피드백
        self.apply_visual_feedback(enabled)

    def apply_visual_feedback(self, enabled):
        """Context7 모범 사례: 상태에 따른 시각적 피드백 적용"""
        try:
            if enabled:
                # 활성 상태: 기본 색상 및 스타일
                self.start_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #28a745;
                        color: white;
                        border: 2px solid #28a745;
                        border-radius: 8px;
                        padding: 10px 20px;
                        font-weight: bold;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        background-color: #218838;
                        border-color: #1e7e34;
                        transform: translateY(-2px);
                    }
                    QPushButton:pressed {
                        background-color: #1e7e34;
                        transform: translateY(0px);
                    }
                """)

                self.manual_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #007bff;
                        color: white;
                        border: 2px solid #007bff;
                        border-radius: 8px;
                        padding: 10px 20px;
                        font-weight: bold;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        background-color: #0056b3;
                        border-color: #004085;
                        transform: translateY(-2px);
                    }
                    QPushButton:pressed {
                        background-color: #004085;
                        transform: translateY(0px);
                    }
                """)

                self.stop_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #6c757d;
                        color: white;
                        border: 2px solid #6c757d;
                        border-radius: 8px;
                        padding: 10px 20px;
                        font-weight: bold;
                        font-size: 14px;
                        opacity: 0.6;
                    }
                """)

            else:
                # 비활성 상태: 회색 계열 및 로딩 효과
                disabled_style = """
                    QPushButton {
                        background-color: #f8f9fa;
                        color: #6c757d;
                        border: 2px solid #e9ecef;
                        border-radius: 8px;
                        padding: 10px 20px;
                        font-weight: bold;
                        font-size: 14px;
                        opacity: 0.6;
                    }
                """

                self.start_btn.setStyleSheet(disabled_style)
                self.manual_btn.setStyleSheet(disabled_style)

                # 중지 버튼은 활성 상태로 강조
                self.stop_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #dc3545;
                        color: white;
                        border: 2px solid #dc3545;
                        border-radius: 8px;
                        padding: 10px 20px;
                        font-weight: bold;
                        font-size: 14px;
                        animation: pulse 1.5s infinite;
                    }
                    QPushButton:hover {
                        background-color: #c82333;
                        border-color: #bd2130;
                        transform: scale(1.05);
                    }
                    QPushButton:pressed {
                        background-color: #bd2130;
                        transform: scale(0.95);
                    }
                """)

            # 추가 시각적 효과
            self.update_status_indicators(enabled)

        except Exception as e:
            # 시각적 피드백 오류는 조용히 무시 (기능에 영향 없음)
            pass

    def update_status_indicators(self, enabled):
        """Context7 모범 사례: 상태 표시기 업데이트"""
        try:
            if hasattr(self, 'folder_label'):
                if enabled:
                    # 준비 상태
                    self.folder_label.setStyleSheet("""
                        QLabel {
                            color: #28a745;
                            font-weight: bold;
                            padding: 5px;
                            border-left: 4px solid #28a745;
                            background-color: #f8fff9;
                        }
                    """)
                else:
                    # 작업 중 상태
                    self.folder_label.setStyleSheet("""
                        QLabel {
                            color: #ffc107;
                            font-weight: bold;
                            padding: 5px;
                            border-left: 4px solid #ffc107;
                            background-color: #fffbf0;
                        }
                    """)
        except Exception:
            pass
    
    def load_settings(self):
        """애플리케이션 설정 로드"""
        try:
            # 레거시 QSettings에서 창 위치만 복원
            qt_settings = QSettings("SalesAutomation", "ModernSalesApp")
            geometry = qt_settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)

            # Pydantic Settings에서 앱 설정 로드
            if self.settings.paths.download_dir and self.settings.paths.download_dir.exists():
                self.download_folder_path = str(self.settings.paths.download_dir)
                self.folder_label.setText(f"📁 {self.download_folder_path}")

            # Polars 엔진 설정 복원
            use_polars = self.settings.database.use_polars
            self.polars_checkbox.setChecked(use_polars)
            set_engine(use_polars)

            # 패스워드 설정 복원
            self.password_input.setText(self.settings.file_processing.order_file_password)

            # 현재 엔진 상태를 로그에 표시
            current_engine = get_current_engine()
            self.update_log(f"[INFO] 📊 데이터 처리 엔진: {current_engine}")

        except Exception as e:
            import logging
            logging.error(f"설정 로드 중 오류: {e}")
            # 기본값 설정
            self.polars_checkbox.setChecked(True)
            set_engine(True)
    
    def save_settings(self):
        """애플리케이션 설정 저장 - Pydantic Settings 자동 저장"""
        try:
            # 레거시 QSettings에는 창 위치만 저장
            qt_settings = QSettings("SalesAutomation", "ModernSalesApp")
            qt_settings.setValue("geometry", self.saveGeometry())

            # Pydantic Settings는 각 설정 변경 시 자동으로 저장됨
            # (별도 저장 작업 불필요)

        except Exception as e:
            import logging
            logging.error(f"설정 저장 중 오류: {e}")

    def check_for_updates(self):
        """백그라운드 업데이트 확인"""
        try:
            self.app_logger.info("자동 업데이트 확인 시작")
            version_info = self.updater.check_for_updates()

            if version_info:
                self.app_logger.info(
                    "새 버전 발견",
                    current_version=self.updater.current_version,
                    new_version=version_info.version
                )

                # 새 버전 발견 시 사용자에게 알림
                self.update_log(f"[INFO] 🔄 새 버전 {version_info.version}이 발견되었습니다!")
                self.update_log(f"[INFO] 업데이트 확인 버튼을 클릭하여 수동으로 업데이트하실 수 있습니다.")

            else:
                self.app_logger.info("현재 최신 버전입니다")

        except Exception as e:
            self.app_logger.error("자동 업데이트 확인 실패", error=str(e))

    def manual_check_updates(self):
        """수동 업데이트 확인"""
        try:
            self.update_log("[INFO] 🔄 업데이트를 확인하고 있습니다...")
            self.update_btn.setEnabled(False)

            version_info = self.updater.check_for_updates()

            if version_info:
                # 업데이트 다이얼로그 표시
                from PySide6.QtWidgets import QMessageBox

                msg = QMessageBox(self)
                msg.setWindowTitle("업데이트 발견")
                msg.setIcon(QMessageBox.Information)
                msg.setText(f"새 버전 {version_info.version}이 발견되었습니다!")
                msg.setInformativeText(
                    f"현재 버전: {self.updater.current_version}\n"
                    f"새 버전: {version_info.version}\n"
                    f"출시일: {version_info.build_date}\n\n"
                    "지금 다운로드하시겠습니까?"
                )

                download_btn = msg.addButton("다운로드", QMessageBox.YesRole)
                later_btn = msg.addButton("나중에", QMessageBox.NoRole)
                msg.setDefaultButton(download_btn)

                msg.exec()

                if msg.clickedButton() == download_btn:
                    self.download_update(version_info)

            else:
                QMessageBox.information(
                    self,
                    "업데이트 확인",
                    f"현재 버전 {self.updater.current_version}이 최신입니다."
                )

        except Exception as e:
            self.update_log(f"[ERROR] 업데이트 확인 실패: {e}")
            QMessageBox.critical(self, "오류", f"업데이트 확인 중 오류가 발생했습니다:\n{e}")
        finally:
            self.update_btn.setEnabled(True)

    def download_update(self, version_info):
        """업데이트 다운로드"""
        from PySide6.QtWidgets import QProgressDialog
        from PySide6.QtCore import QThread, Signal

        class DownloadWorker(QThread):
            progress_signal = Signal(str)
            finished_signal = Signal(bool, str)

            def __init__(self, updater, version_info):
                super().__init__()
                self.updater = updater
                self.version_info = version_info

            def run(self):
                try:
                    self.progress_signal.emit("다운로드를 시작합니다...")
                    download_path = self.updater.download_update(self.version_info)

                    if download_path:
                        self.progress_signal.emit("설치 준비 중...")
                        success = self.updater.install_update(download_path)
                        if success:
                            self.finished_signal.emit(True, str(download_path))
                        else:
                            self.finished_signal.emit(False, "설치 준비 실패")
                    else:
                        self.finished_signal.emit(False, "다운로드 실패")

                except Exception as e:
                    self.finished_signal.emit(False, str(e))

        # 다운로드 프로그레스 다이얼로그
        progress = QProgressDialog("업데이트 다운로드 중...", "취소", 0, 0, self)
        progress.setWindowTitle("업데이트")
        progress.setMinimumDuration(0)
        progress.show()

        # 다운로드 워커 시작
        download_worker = DownloadWorker(self.updater, version_info)
        download_worker.progress_signal.connect(lambda msg: progress.setLabelText(msg))
        download_worker.finished_signal.connect(
            lambda success, message: self.on_download_finished(success, message, progress)
        )
        download_worker.start()

    def on_download_finished(self, success, message, progress_dialog):
        """다운로드 완료 처리"""
        progress_dialog.close()

        if success:
            QMessageBox.information(
                self,
                "업데이트 준비 완료",
                "업데이트가 준비되었습니다.\n"
                "프로그램을 종료하면 자동으로 업데이트됩니다.\n\n"
                "지금 프로그램을 종료하시겠습니까?"
            )
            # 사용자가 원하면 프로그램 종료
            self.close()
        else:
            QMessageBox.critical(
                self,
                "업데이트 실패",
                f"업데이트에 실패했습니다:\n{message}"
            )

    def cleanup_workers(self):
        """모든 워커 스레드 안전 정리"""
        workers = [
            ('worker', self.worker),
            ('manual_worker', self.manual_worker), 
            ('weekly_worker', self.weekly_worker)
        ]
        
        for name, worker in workers:
            if worker and worker.isRunning():
                try:
                    self.update_log(f"[INFO] {name} 스레드 종료 중...")
                    worker.quit()
                    if not worker.wait(3000):  # 3초 대기
                        self.update_log(f"[WARNING] {name} 스레드 강제 종료")
                        worker.terminate()
                        worker.wait(1000)
                    else:
                        self.update_log(f"[INFO] {name} 스레드 정상 종료")
                except Exception as e:
                    self.update_log(f"[ERROR] {name} 스레드 정리 중 오류: {e}")
    
    def closeEvent(self, event):
        """애플리케이션 종료 시 정리 작업"""
        try:
            # 실행 중인 작업이 있는지 확인
            running_workers = []
            if self.worker and self.worker.isRunning():
                running_workers.append("자동 모니터링")
            if self.manual_worker and self.manual_worker.isRunning():
                running_workers.append("수동 처리")
            if self.weekly_worker and self.weekly_worker.isRunning():
                running_workers.append("주간 리포트")
            
            if running_workers:
                reply = QMessageBox.question(
                    self, 
                    "작업 진행 중",
                    f"다음 작업이 진행 중입니다:\n{', '.join(running_workers)}\n\n정말 종료하시겠습니까?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply != QMessageBox.Yes:
                    event.ignore()
                    return
            
            # 설정 저장
            self.save_settings()
            
            # 워커 스레드 정리
            self.cleanup_workers()
            
            # 부모 클래스의 closeEvent 호출
            super().closeEvent(event)
            
        except Exception as e:
            import logging
            logging.error(f"애플리케이션 종료 중 오류: {e}")
            # 오류가 있어도 종료 진행
            super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    window = ModernSalesAutomationApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
