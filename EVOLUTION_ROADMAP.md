# 🚀 판매 데이터 자동화 시스템 진화 로드맵

## 📋 프로젝트 현황 분석
- **강점**: 완성도 높은 데스크톱 GUI, 안정적인 데이터 처리, 옵션별 세밀한 관리
- **제약**: 단일 사용자, 로컬 환경 제한, pandas 성능 한계, 실시간 모니터링 부족
- **목표**: 비용 부담 없이 로컬 환경에서 차세대 수준 업그레이드

---

## 💻 로컬 중심 진화 전략 (총 비용: 0원)

### 1. 🔥 성능 혁신: Pandas → Polars 마이그레이션

**현재 문제점**:
```python
# 현재 pandas 기반 (느린 처리)
final_df = pd.merge(option_summary, margin_df, on=['상품ID', '옵션정보'])
final_df['순이익'] = final_df['판매마진'] - final_df['가구매 비용'] - final_df['리워드']
```

**Polars 기반 개선안**:
```python
import polars as pl

# 10-100배 빠른 처리
final_df = (
    option_summary
    .join(margin_df, on=['상품ID', '옵션정보'], how='left')
    .with_columns([
        (pl.col('판매마진') - pl.col('가구매 비용') - pl.col('리워드')).alias('순이익'),
        ((pl.col('리워드') + pl.col('가구매 비용')) / pl.col('순매출') * 100).alias('광고비율')
    ])
)

# Excel 직접 읽기/쓰기 (더 빠름)
df = pl.read_excel("주문조회.xlsx", engine="fastexcel")
df.write_excel("리포트.xlsx")
```

**예상 효과**:
- ✅ 처리 속도: 10-100배 향상
- ✅ 메모리 사용량: 50% 감소
- ✅ 설치만 하면 즉시 적용 가능

---

### 2. 🖥️ 로컬 웹 대시보드 (Streamlit)

**구현 예시**:
```python
# dashboard.py
import streamlit as st
import polars as pl

def main():
    st.set_page_config(page_title="판매 데이터 분석", layout="wide")

    # 파일 업로드
    uploaded_file = st.file_uploader("주문조회 파일 업로드", type=['xlsx'])

    if uploaded_file:
        # 실시간 분석
        df = pl.read_excel(uploaded_file)

        # 대시보드 표시
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("총 매출", f"{df.select(pl.sum('매출')).item():,.0f}원")
        with col2:
            st.metric("순이익", f"{df.select(pl.sum('순이익')).item():,.0f}원")
        with col3:
            st.metric("광고비율", f"{calculate_ad_ratio(df):.1f}%")

        # 인터랙티브 차트
        st.line_chart(daily_sales_data)

        # 필터링된 테이블
        st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    main()
```

**실행 방법**: `streamlit run dashboard.py` → `http://localhost:8501`

**장점**:
- ✅ 로컬에서만 실행 (비용 0원)
- ✅ 브라우저 기반 현대적 UI
- ✅ 기존 PySide6과 병행 사용 가능

---

### 3. 📊 고급 분석 기능 추가 (AI/ML)

**로컬 AI 분석 엔진**:
```python
# analytics.py
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans

class LocalAnalytics:
    def __init__(self):
        self.anomaly_detector = IsolationForest(contamination=0.1)

    def detect_anomalies(self, sales_data):
        """이상 매출 패턴 탐지"""
        features = sales_data[['매출', '순이익', '광고비율']].values
        anomalies = self.anomaly_detector.fit_predict(features)
        return sales_data[anomalies == -1]

    def segment_products(self, product_data):
        """상품 성과 기반 클러스터링"""
        kmeans = KMeans(n_clusters=4)
        clusters = kmeans.fit_predict(product_data[['매출', '이윤율']])

        return {
            '스타 상품': product_data[clusters == 0],
            '성장 상품': product_data[clusters == 1],
            '관심 필요': product_data[clusters == 2],
            '재검토 대상': product_data[clusters == 3]
        }

    def recommend_actions(self, analysis_result):
        """데이터 기반 액션 추천"""
        recommendations = []

        for category, products in analysis_result.items():
            if category == '스타 상품':
                recommendations.append("리워드 늘려서 더 홍보")
            elif category == '재검토 대상':
                recommendations.append("리워드 줄이거나 중단 고려")

        return recommendations
```

---

### 4. 🔄 자동화 스케줄러

**Windows 작업 스케줄러 연동**:
```python
# scheduler.py
import schedule
import time
from pathlib import Path
import logging

class LocalScheduler:
    def __init__(self, download_folder):
        self.download_folder = Path(download_folder)

    def auto_process_new_files(self):
        """새 파일 자동 감지 및 처리"""
        new_files = list(self.download_folder.glob("*주문조회*.xlsx"))

        for file in new_files:
            if self.is_new_file(file):
                logging.info(f"새 파일 처리 시작: {file.name}")
                self.process_file(file)
                self.mark_as_processed(file)

    def daily_report_generation(self):
        """매일 자동 리포트 생성"""
        today = datetime.now().strftime("%Y-%m-%d")
        self.generate_daily_report(today)

    def run_scheduler(self):
        """스케줄러 실행"""
        schedule.every(30).minutes.do(self.auto_process_new_files)
        schedule.every().day.at("09:00").do(self.daily_report_generation)

        while True:
            schedule.run_pending()
            time.sleep(60)

# 백그라운드 실행
if __name__ == "__main__":
    scheduler = LocalScheduler("C:/Downloads")
    scheduler.run_scheduler()
```

---

### 5. 📱 하이브리드 데스크톱 앱

**PySide6 + Streamlit 통합**:
```python
# hybrid_app.py
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QThread
import subprocess
import time

class StreamlitThread(QThread):
    def run(self):
        # Streamlit 서버를 백그라운드에서 실행
        subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", "dashboard.py",
            "--server.port", "8521", "--server.headless", "true"
        ])

class HybridApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("판매 데이터 분석 - 고급 버전")
        self.setGeometry(100, 100, 1400, 900)

        # Streamlit 서버 시작
        self.streamlit_thread = StreamlitThread()
        self.streamlit_thread.start()

        # 웹뷰로 Streamlit 임베드
        time.sleep(3)  # 서버 시작 대기
        self.web_view = QWebEngineView()
        self.web_view.load(QUrl("http://localhost:8521"))

        self.setCentralWidget(self.web_view)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HybridApp()
    window.show()
    sys.exit(app.exec())
```

**결과**: 데스크톱 앱 안에서 웹 대시보드 실행 (완전 로컬)

---

### 6. 🗂️ 로컬 데이터베이스 (SQLite)

**데이터 관리 개선**:
```python
# database.py
import sqlite3
import polars as pl
from datetime import datetime

class LocalDatabase:
    def __init__(self, db_path="sales_data.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """데이터베이스 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sales_history (
                    id INTEGER PRIMARY KEY,
                    date TEXT,
                    store TEXT,
                    product_id TEXT,
                    option_info TEXT,
                    sales REAL,
                    profit REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def save_daily_data(self, df, date):
        """일일 데이터 저장"""
        df_sqlite = df.with_columns([
            pl.lit(date).alias("date"),
            pl.lit(datetime.now()).alias("created_at")
        ])

        # Polars → SQLite 직접 저장
        with sqlite3.connect(self.db_path) as conn:
            df_sqlite.write_database("sales_history", conn, if_exists="append")

    def get_trend_data(self, days=30):
        """트렌드 분석용 데이터 조회"""
        query = f"""
            SELECT date, SUM(sales) as total_sales, SUM(profit) as total_profit
            FROM sales_history
            WHERE date >= date('now', '-{days} days')
            GROUP BY date
            ORDER BY date
        """
        return pl.read_database(query, sqlite3.connect(self.db_path))
```

---

## 📈 점진적 업그레이드 계획

### Phase 1: 성능 향상 (1주일)
**목표**: 기존 시스템 성능 대폭 개선
- ✅ Polars 마이그레이션으로 속도 10배+ 향상
- ✅ 메모리 사용량 50% 감소
- ✅ Excel 처리 속도 향상

**작업 내용**:
1. `report_generator.py`의 pandas 코드를 Polars로 변환
2. Excel 읽기/쓰기 부분 최적화
3. 벡터화 연산 강화
4. 성능 테스트 및 벤치마크

**필요 패키지**: `pip install polars`

---

### Phase 2: 분석 고도화 (2주일)
**목표**: AI 기반 자동 분석 및 추천 시스템
- 🤖 이상 패턴 자동 탐지
- 📊 상품 성과 분석 및 클러스터링
- 💡 데이터 기반 액션 추천

**작업 내용**:
1. 이상 탐지 모델 구현 (`IsolationForest`)
2. 상품 성과 클러스터링 (`KMeans`)
3. 추천 엔진 개발
4. 분석 결과 시각화

**필요 패키지**: `pip install scikit-learn matplotlib seaborn`

---

### Phase 3: UI/UX 개선 (3주일)
**목표**: 현대적인 웹 기반 인터페이스 추가
- 🌐 Streamlit 대시보드 구현
- 📱 하이브리드 앱 개발
- 📊 인터랙티브 차트 및 필터링

**작업 내용**:
1. Streamlit 대시보드 개발
2. 기존 PySide6과 통합
3. 웹뷰 기반 하이브리드 앱 구현
4. 사용자 경험 최적화

**필요 패키지**: `pip install streamlit plotly altair`

---

### Phase 4: 자동화 강화 (1주일)
**목표**: 완전 자동화된 워크플로우
- 🔄 파일 자동 감지 및 처리
- ⏰ 스케줄 기반 리포트 생성
- 📡 백그라운드 모니터링

**작업 내용**:
1. 파일 감시 시스템 구현
2. 스케줄러 개발
3. 백그라운드 서비스 구현
4. Windows 작업 스케줄러 연동

**필요 패키지**: `pip install schedule watchdog`

---

## 💰 비용 분석

### 총 비용: 0원
**필요한 것**:
- ✅ Python 패키지 추가 설치만 (`pip install`)
- ✅ 기존 하드웨어 그대로 사용
- ✅ 인터넷 연결도 선택사항 (로컬 실행)

### 예상 효과
**즉시 효과**:
- 🚀 처리 속도: 10-100배 향상 (Polars)
- 💾 메모리 사용량: 50% 감소
- 🖥️ 현대적인 웹 기반 UI

**중장기 효과**:
- 🤖 AI 기반 자동 분석 및 추천
- 🔄 완전 자동화된 워크플로우
- 📊 실시간 데이터 모니터링
- 📈 예측 분석 및 트렌드 분석

---

## 🛠️ 필요 패키지 목록

```bash
# 성능 향상
pip install polars

# 분석 고도화
pip install scikit-learn matplotlib seaborn

# 웹 대시보드
pip install streamlit plotly altair

# 자동화
pip install schedule watchdog

# 데이터베이스
pip install sqlite3  # Python 내장

# 웹뷰 (이미 설치됨)
# PySide6
```

---

## 🎯 성공 지표

### 성능 지표
- ✅ 데이터 처리 속도: 10배 이상 향상
- ✅ 메모리 사용량: 50% 이상 감소
- ✅ 파일 처리 시간: 대용량 파일 30초 이내

### 사용성 지표
- ✅ 웹 대시보드 반응 속도: 1초 이내
- ✅ 자동화 성공률: 95% 이상
- ✅ 이상 탐지 정확도: 90% 이상

### 비즈니스 지표
- ✅ 수동 작업 시간: 80% 이상 감소
- ✅ 분석 인사이트 품질: 현재 대비 3배 향상
- ✅ 의사결정 속도: 실시간 대응 가능

---

## 📝 다음 단계

1. **Phase 1 시작**: Polars 마이그레이션부터 시작
2. **성능 테스트**: 기존 시스템과 속도 비교
3. **점진적 적용**: 기능별로 단계적 업그레이드
4. **사용자 피드백**: 각 단계별 사용성 검증
5. **문서화**: 새로운 기능 사용법 정리

이 로드맵을 통해 **비용 부담 없이 현재 시스템을 차세대 수준으로 업그레이드**할 수 있습니다!