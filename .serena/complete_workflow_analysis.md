# 쿠팡 판매 데이터 자동화 시스템 - 전체 작업 흐름 분석

## 📋 목차
1. [시스템 개요](#시스템-개요)
2. [아키텍처](#아키텍처)
3. [데이터 흐름](#데이터-흐름)
4. [핵심 컴포넌트](#핵심-컴포넌트)
5. [계산 로직](#계산-로직)
6. [주요 수정 이력](#주요-수정-이력)

---

## 시스템 개요

### 목적
쿠팡 판매 데이터, 광고 데이터, 마진 데이터를 통합하여 상품별 성과를 자동으로 분석하는 웹 기반 대시보드 시스템

### 기술 스택
- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: React + Vite + Material-UI + Recharts
- **Data Processing**: Pandas
- **Server**: Uvicorn (auto-reload 활성화)

### 주요 기능
1. 3개 엑셀 파일 통합 업로드 및 파싱
2. 옵션 ID 기준 데이터 통합
3. 순이익, 이윤율, ROAS 자동 계산
4. 옵션별 상품 성과 대시보드 표시
5. 기간별 필터링 및 분석

---

## 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                        사용자                                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   Frontend (React)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ UploadPage   │  │ DashboardPage│  │  Components  │      │
│  │  (미구현)     │  │ (성과 표시)   │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST API
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Routers                                              │  │
│  │  ├─ upload.py  (/api/upload/integrated)             │  │
│  │  ├─ metrics.py (/api/metrics)                        │  │
│  │  └─ report.py  (/api/report)                         │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Services                                             │  │
│  │  ├─ integrated_parser.py (파일 파싱 & 통합)          │  │
│  │  └─ database.py (모델 & 계산 로직)                   │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Models                                               │  │
│  │  └─ schemas.py (Pydantic 스키마)                     │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              Database (SQLite)                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  integrated_records (통합 데이터 테이블)              │  │
│  │  - option_id (PK, unique, indexed)                   │  │
│  │  - 판매 데이터 (매출, 판매량, 주문수 등)              │  │
│  │  - 광고 데이터 (광고비, 노출수, 클릭수 등)            │  │
│  │  - 마진 데이터 (도매가, 수수료, 부가세 등)            │  │
│  │  - 계산 데이터 (순이익, 이윤율, ROAS 등)             │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 데이터 흐름

### 1. 파일 업로드 및 통합 프로세스

```
┌─────────────────┐
│  사용자          │
│  3개 엑셀 업로드 │
│  - 판매.xlsx    │
│  - 광고.xlsx    │
│  - 마진.xlsx    │
└────────┬────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────┐
│  POST /api/upload/integrated                                 │
│  - sales_file: UploadFile                                    │
│  - ads_file: UploadFile                                      │
│  - margin_file: UploadFile                                   │
│  - data_date: Optional[str]                                  │
└────────┬────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────┐
│  integrated_parser.parse_integrated_files()                  │
│                                                               │
│  STEP 1: 판매 데이터 파싱 (sales_df)                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 필수 컬럼 매핑:                                         │ │
│  │  - '옵션 ID' → option_id (int64)                       │ │
│  │  - '옵션명' → option_name                              │ │
│  │  - '상품명' → product_name                             │ │
│  │  - '매출(원)' → sales_amount                           │ │
│  │  - '판매량' → sales_quantity                           │ │
│  │  - '주문' → order_count                                │ │
│  │  - '총 매출(원)' → total_sales                         │ │
│  │  - '총 판매수' → total_sales_quantity                  │ │
│  │                                                          │ │
│  │ 처리:                                                   │ │
│  │  - option_id를 int64로 변환                            │ │
│  │  - NaN 제거                                             │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  STEP 2: 광고 데이터 파싱 (ads_df)                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 컬럼 매핑:                                              │ │
│  │  - '광고 집행 옵션 ID' → option_id (int64)             │ │
│  │  - '광고비(원)' → ad_cost                              │ │
│  │  - '노출수' → impressions                              │ │
│  │  - '클릭수' → clicks                                   │ │
│  │  - '총 판매 수량 (1일)' → ad_sales_quantity            │ │
│  │                                                          │ │
│  │ 예외 처리:                                              │ │
│  │  - 파싱 실패 시 빈 DataFrame 사용                      │ │
│  │  - 경고 메시지 추가                                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  STEP 3: 마진 데이터 파싱 (margin_df)                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 컬럼 매핑:                                              │ │
│  │  - 'Option_ID' → option_id (int64)                     │ │
│  │    (대체: 'OptionID', '옵션ID', 'option_id')           │ │
│  │  - '도매가' → cost_price ⭐ (한국원가에서 변경됨)      │ │
│  │  - '판매가' → selling_price                            │ │
│  │  - '판매마진' → margin_amount                          │ │
│  │  - '제품순이익%' → margin_rate                         │ │
│  │  - '부가세' → vat                                      │ │
│  │  - '총 수수료(%)' → fee_rate                           │ │
│  │  - '총 수수료(원)' → fee_amount                        │ │
│  │                                                          │ │
│  │ 유연한 컬럼명 처리:                                     │ │
│  │  - 여러 옵션ID 변형 지원                                │ │
│  │  - 존재하는 컬럼만 선택                                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  STEP 4: 데이터 병합 (LEFT JOIN 기반)                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ sales_df ←[LEFT JOIN]→ ads_df (on: option_id)          │ │
│  │         ↓                                               │ │
│  │ merged_df ←[LEFT JOIN]→ margin_df (on: option_id)      │ │
│  │                                                          │ │
│  │ 병합 로직:                                              │ │
│  │  - 판매 데이터를 기준으로 LEFT JOIN                    │ │
│  │  - 매칭되지 않는 광고/마진 데이터는 0으로 채움          │ │
│  │  - 중복 option_id는 첫 번째만 유지 (drop_duplicates)  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  STEP 5: 데이터베이스 저장                                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ For each row in merged_df:                              │ │
│  │   1. option_id로 기존 레코드 확인                       │ │
│  │   2. 존재 시: UPDATE (덮어쓰기)                         │ │
│  │   3. 미존재 시: INSERT (새로 생성)                      │ │
│  │   4. calculate_metrics() 호출 → 계산 필드 업데이트     │ │
│  │   5. db.commit()                                        │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────┐
│  Response                                                     │
│  {                                                            │
│    "status": "success",                                       │
│    "total_records": 150,                                      │
│    "matched_with_ads": 120,                                   │
│    "matched_with_margin": 145,                                │
│    "fully_integrated": 115,                                   │
│    "warnings": []                                             │
│  }                                                            │
└─────────────────────────────────────────────────────────────┘
```

### 2. 대시보드 조회 프로세스

```
┌─────────────────┐
│  사용자          │
│  기간 선택 후    │
│  "분석 조회"     │
└────────┬────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────┐
│  GET /api/metrics?start_date=2024-01-01&end_date=2024-01-31 │
└────────┬────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────┐
│  metrics.get_metrics()                                        │
│                                                               │
│  STEP 1: 데이터베이스 쿼리                                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ query = db.query(IntegratedRecord)                      │ │
│  │         .filter(date >= start_date)                     │ │
│  │         .filter(date <= end_date)                       │ │
│  │         .all()                                          │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  STEP 2: 일별 메트릭 집계                                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ daily_metrics = {}                                      │ │
│  │ For each record:                                        │ │
│  │   date_key = record.date                                │ │
│  │   daily_metrics[date_key] = {                           │ │
│  │     'total_sales': sum(sales_amount),                   │ │
│  │     'total_profit': sum(net_profit),                    │ │
│  │     'ad_cost': sum(ad_cost)                             │ │
│  │   }                                                      │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  STEP 3: 상품별(옵션별) 메트릭 집계 ⭐                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ product_metrics = {}                                    │ │
│  │ For each record:                                        │ │
│  │   option_id = record.option_id  # 옵션별로 그룹화!     │ │
│  │   product_metrics[option_id] = {                        │ │
│  │     'option_id': option_id,                             │ │
│  │     'option_name': option_name,                         │ │
│  │     'product_name': product_name,                       │ │
│  │     'total_sales': sum(sales_amount),                   │ │
│  │     'total_profit': sum(net_profit),                    │ │
│  │     'total_quantity': sum(sales_quantity),              │ │
│  │     'total_ad_cost': sum(ad_cost),  # 광고비 집계 추가 │ │
│  │     'margin_rate': (profit/sales)*100                   │ │
│  │   }                                                      │ │
│  │                                                          │ │
│  │ 필터링:                                                 │ │
│  │   - total_sales > 0 인 레코드만 반환                    │ │
│  │   - 매출 내림차순 정렬                                  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────┐
│  Response (MetricsResponse)                                   │
│  {                                                            │
│    "period": "2024-01-01 to 2024-01-31",                     │
│    "total_sales": 5000000,                                    │
│    "total_profit": 1200000,                                   │
│    "total_ad_cost": 300000,                                   │
│    "avg_margin_rate": 24.5,                                   │
│    "daily_trend": [...],                                      │
│    "by_product": [                                            │
│      {                                                         │
│        "option_id": 123456,                                   │
│        "option_name": "네이비",                               │
│        "product_name": "헤몬팜 키토트랩...",                  │
│        "total_sales": 500000,                                 │
│        "total_profit": 120000,                                │
│        "total_quantity": 50,                                  │
│        "total_ad_cost": 30000,                                │
│        "margin_rate": 24.0                                    │
│      },                                                        │
│      ...                                                       │
│    ]                                                           │
│  }                                                            │
└─────────────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────┐
│  Frontend DashboardPage.jsx                                   │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 1. 요약 카드 (5개)                                      │ │
│  │    - 총 매출, 순이익, 광고비, 이윤율, 총 주문          │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 2. 기간 선택 필터                                       │ │
│  │    - 시작일, 종료일, 분석 조회 버튼                    │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 3. 기간 요약 (4개 카드)                                │ │
│  │    - 기간 매출, 기간 순이익, 기간 광고비, 전체 ROAS   │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 4. 상품별 성과 상세 테이블                              │ │
│  │    컬럼: 상품명(35%) | 옵션(10%) | 매출(13%) |         │ │
│  │          순이익(13%) | 광고비(12%) | 판매량(9%) |      │ │
│  │          이윤율(8%)                                     │ │
│  │                                                          │ │
│  │    - 옵션별로 개별 행 표시 (네이비, 화이트 등 분리)    │ │
│  │    - 매출 기준 내림차순 정렬                            │ │
│  │    - 상위 3개 상품에 #1, #2, #3 뱃지 표시              │ │
│  │    - 이윤율 색상 코드:                                  │ │
│  │      * 30% 이상: 녹색                                   │ │
│  │      * 15~30%: 주황색                                   │ │
│  │      * 15% 미만: 빨간색                                 │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 핵심 컴포넌트

### 1. Database Model (IntegratedRecord)

**파일**: `backend/services/database.py`

**주요 필드**:
```python
class IntegratedRecord:
    # Primary Key
    id: int (auto-increment)
    option_id: int (UNIQUE, INDEXED) ⭐ 핵심 키

    # 기본 정보
    option_name: str          # 옵션명 (예: "네이비", "화이트")
    product_name: str         # 상품명
    date: date                # 데이터 날짜

    # 판매 데이터
    sales_amount: float       # 매출(원)
    sales_quantity: int       # 판매량
    order_count: int          # 주문수
    total_sales: float        # 총 매출
    total_sales_quantity: int # 총 판매수

    # 광고 데이터
    ad_cost: float           # 광고비(원)
    impressions: int         # 노출수
    clicks: int              # 클릭수
    ad_sales_quantity: int   # 광고 판매수량

    # 마진 데이터 (단가 기준)
    cost_price: float        # 도매가 ⭐
    selling_price: float     # 판매가
    margin_amount: float     # 마진액
    margin_rate: float       # 마진율(%)
    fee_rate: float          # 총 수수료율(%)
    fee_amount: float        # 총 수수료액(원/개)
    vat: float               # 부가세(원/개)

    # 계산 필드 (자동 계산)
    total_cost: float        # 총 원가
    net_profit: float        # 순이익 ⭐
    actual_margin_rate: float # 실제 이윤율
    roas: float              # ROAS

    # 메타 데이터
    created_at: datetime
    updated_at: datetime
```

**인덱스**:
- `option_id` (UNIQUE INDEX) - 빠른 검색 및 중복 방지
- `product_name` (INDEX) - 상품명 검색
- `date` (INDEX) - 기간 필터링

### 2. Parser (integrated_parser.py)

**핵심 함수**: `parse_integrated_files()`

**주요 로직**:
1. **3개 파일 동시 파싱** - Pandas read_excel() 사용
2. **컬럼 매핑** - 한글 컬럼명 → 영문 필드명
3. **데이터 타입 변환** - option_id를 int64로 강제 변환
4. **LEFT JOIN 병합** - 판매 데이터 기준으로 광고/마진 데이터 병합
5. **NaN 처리** - 매칭되지 않는 값은 0으로 채움
6. **중복 제거** - drop_duplicates(keep='first')
7. **DB 저장** - UPSERT 패턴 (존재하면 UPDATE, 없으면 INSERT)

**반환값**:
```python
return (
    total_records,      # 총 레코드 수
    matched_with_ads,   # 광고 데이터 매칭 수
    matched_with_margin, # 마진 데이터 매칭 수
    warnings            # 경고 메시지 리스트
)
```

### 3. Metrics Router (metrics.py)

**엔드포인트**: `GET /api/metrics`

**쿼리 파라미터**:
- `start_date`: 시작일 (Optional)
- `end_date`: 종료일 (Optional)
- `product`: 상품명 필터 (Optional, LIKE 검색)

**집계 로직**:
1. **일별 집계** - date를 키로 그룹화
2. **상품별(옵션별) 집계** - **option_id를 키로 그룹화** ⭐
3. **필터링** - total_sales > 0 조건
4. **정렬** - 매출 내림차순

### 4. Dashboard Component (DashboardPage.jsx)

**주요 기능**:
1. **기간 선택** - DatePicker로 start/end date 설정
2. **데이터 조회** - API 호출 및 상태 관리
3. **요약 카드** - 총계 표시
4. **테이블 렌더링** - Material-UI Table 사용
5. **한글화** - 모든 UI 텍스트 한글 표시

**테이블 컬럼 구성**:
```javascript
{
  상품명: 35% (product_name + 순위 뱃지),
  옵션: 10% (option_name Chip),
  매출: 13% (total_sales, 우측 정렬, 굵게),
  순이익: 13% (total_profit, 색상 구분),
  광고비: 12% (total_ad_cost),
  판매량: 9% (total_quantity),
  이윤율: 8% (margin_rate, Chip 색상 코드)
}
```

---

## 계산 로직

### IntegratedRecord.calculate_metrics()

**파일**: `backend/services/database.py:70-99`

```python
def calculate_metrics(self):
    # 1. 단위 원가 계산
    unit_cost = (cost_price or 0) + (fee_amount or 0) + (vat or 0)
    #           └─ 도매가        └─ 수수료(원/개)    └─ 부가세(원/개)

    # 2. 총 원가 계산
    total_cost = unit_cost × sales_quantity

    # 3. 순이익 계산 ⭐⭐⭐
    net_profit = sales_amount - total_cost - (ad_cost or 0) × 1.1
    #            └─ 매출       └─ 총 원가    └─ 광고비 + 부가세(10%)

    # 4. 실제 이윤율 계산
    if sales_amount > 0:
        actual_margin_rate = (net_profit / sales_amount) × 100
    else:
        actual_margin_rate = 0

    # 5. ROAS 계산
    if ad_cost > 0:
        roas = sales_amount / ad_cost
    else:
        roas = 0
```

### 핵심 공식

#### 1. 순이익 (Net Profit)
```
순이익 = 매출 - (도매가 + 수수료 + 부가세) × 판매량 - 광고비 × 1.1
```

**예시**:
- 매출: 500,000원
- 도매가: 8,000원/개
- 수수료: 1,000원/개
- 부가세: 500원/개
- 판매량: 50개
- 광고비: 30,000원

```
단위 원가 = 8,000 + 1,000 + 500 = 9,500원/개
총 원가 = 9,500 × 50 = 475,000원
순이익 = 500,000 - 475,000 - (30,000 × 1.1)
      = 500,000 - 475,000 - 33,000
      = -8,000원 (적자)
```

#### 2. 이윤율 (Margin Rate)
```
이윤율 = (순이익 / 매출) × 100
```

위 예시에서:
```
이윤율 = (-8,000 / 500,000) × 100 = -1.6%
```

#### 3. ROAS (Return on Ad Spend)
```
ROAS = 매출 / 광고비
```

위 예시에서:
```
ROAS = 500,000 / 30,000 = 16.67
```

---

## 주요 수정 이력

### 1. 원가 기준 변경 (한국원가 → 도매가)
**날짜**: 최근 세션
**변경 파일**: `integrated_parser.py:107`

```python
# 이전
'한국원가': 'cost_price'

# 변경 후
'도매가': 'cost_price'
```

**이유**: 사용자가 마진 엑셀 파일에서 도매가 기준으로 계산하도록 수식 수정

### 2. 옵션별 표시 (상품명 그룹 → 옵션 ID 그룹)
**날짜**: 최근 세션
**변경 파일**:
- `models/schemas.py:103-111` - option_id, option_name 필드 추가
- `routers/metrics.py:78` - 그룹화 키 변경
- `frontend/src/pages/DashboardPage.jsx:316-322` - 옵션 컬럼 추가

**Before**:
```python
# product_name으로 그룹화 → 옵션이 합쳐짐
product_name = record.product_name
if product_name not in product_metrics:
    product_metrics[product_name] = {...}
```

**After**:
```python
# option_id로 그룹화 → 옵션별로 분리
option_id = record.option_id
if option_id not in product_metrics:
    product_metrics[option_id] = {
        'option_id': option_id,
        'option_name': record.option_name,
        ...
    }
```

**효과**:
- "헤몬팜 키토트랩" 상품의 "네이비", "화이트" 옵션이 개별 행으로 표시됨
- 각 옵션별 성과를 독립적으로 추적 가능

### 3. 광고비 부가세 포함 계산
**날짜**: 방금 전
**변경 파일**: `database.py:87`

```python
# 이전
self.net_profit = self.sales_amount - self.total_cost - (self.ad_cost or 0)

# 변경 후
self.net_profit = self.sales_amount - self.total_cost - (self.ad_cost or 0) * 1.1
```

**이유**: 광고비에도 부가세 10%가 포함되므로 실제 비용 반영

### 4. 광고비 컬럼 추가
**날짜**: 최근
**변경 파일**:
- `models/schemas.py:110` - total_ad_cost 필드 추가
- `routers/metrics.py:94` - 광고비 집계 로직 추가
- `frontend/src/pages/DashboardPage.jsx:320` - 광고비 컬럼 표시

**효과**: 상품별 광고비 지출 내역을 대시보드에서 직접 확인 가능

### 5. 용어 변경 (마진율 → 이윤율)
**날짜**: 최근
**변경 파일**: `frontend/src/pages/DashboardPage.jsx`

**Before**: "마진율"
**After**: "이윤율"

**위치**:
- 요약 카드 (line 186)
- 테이블 헤더 (line 322)

### 6. 매출 0인 레코드 필터링
**날짜**: 최근
**변경 파일**: `routers/metrics.py:99-103`

```python
# Filter out records with 0 sales
filtered_metrics = [
    metrics for metrics in product_metrics.values()
    if metrics['total_sales'] > 0
]
```

**이유**: 판매가 없는 상품은 대시보드에서 제외하여 가독성 향상

### 7. 중복 처리 방식 변경 (집계 → 첫 번째 유지)
**날짜**: 세션 초반
**변경 파일**: `integrated_parser.py:200`

```python
# 이전: groupby로 집계
# merged_df = merged_df.groupby('option_id').agg(...)

# 변경 후: 첫 번째만 유지
merged_df = merged_df.drop_duplicates(subset=['option_id'], keep='first')
```

**이유**: 사용자가 중복 option_id를 합산하지 않고 첫 번째 레코드만 유지하길 원함

### 8. 차트 제거 (UI 간소화)
**날짜**: 최근
**변경 파일**: `frontend/src/pages/DashboardPage.jsx`

**제거된 차트**:
1. Daily Sales & Profit Trend (ComposedChart)
2. ROAS by Product (BarChart)

**이유**: 대시보드 간소화 및 테이블 집중

---

## 데이터베이스 스키마

### integrated_records 테이블

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | INTEGER | PRIMARY KEY, AUTO_INCREMENT | 레코드 ID |
| option_id | BIGINT | UNIQUE, NOT NULL, INDEXED | 옵션 ID (핵심 키) |
| option_name | VARCHAR | - | 옵션명 |
| product_name | VARCHAR | NOT NULL, INDEXED | 상품명 |
| date | DATE | INDEXED | 데이터 날짜 |
| sales_amount | FLOAT | DEFAULT 0.0 | 매출(원) |
| sales_quantity | INTEGER | DEFAULT 0 | 판매량 |
| order_count | INTEGER | DEFAULT 0 | 주문수 |
| total_sales | FLOAT | DEFAULT 0.0 | 총 매출 |
| total_sales_quantity | INTEGER | DEFAULT 0 | 총 판매수 |
| ad_cost | FLOAT | DEFAULT 0.0 | 광고비 |
| impressions | INTEGER | DEFAULT 0 | 노출수 |
| clicks | INTEGER | DEFAULT 0 | 클릭수 |
| ad_sales_quantity | INTEGER | DEFAULT 0 | 광고 판매수량 |
| cost_price | FLOAT | DEFAULT 0.0 | 도매가 |
| selling_price | FLOAT | DEFAULT 0.0 | 판매가 |
| margin_amount | FLOAT | DEFAULT 0.0 | 마진액 |
| margin_rate | FLOAT | DEFAULT 0.0 | 마진율(%) |
| fee_rate | FLOAT | DEFAULT 0.0 | 수수료율(%) |
| fee_amount | FLOAT | DEFAULT 0.0 | 수수료액(원/개) |
| vat | FLOAT | DEFAULT 0.0 | 부가세(원/개) |
| total_cost | FLOAT | DEFAULT 0.0 | 총 원가 (계산) |
| net_profit | FLOAT | DEFAULT 0.0 | 순이익 (계산) |
| actual_margin_rate | FLOAT | DEFAULT 0.0 | 실제 이윤율 (계산) |
| roas | FLOAT | DEFAULT 0.0 | ROAS (계산) |
| created_at | DATETIME | DEFAULT now() | 생성일시 |
| updated_at | DATETIME | DEFAULT now(), ON UPDATE now() | 수정일시 |

---

## API 엔드포인트

### 1. POST /api/upload/integrated
**설명**: 3개 엑셀 파일 통합 업로드

**Request**:
- Content-Type: multipart/form-data
- Fields:
  - `sales_file`: 판매 데이터 엑셀 파일
  - `ads_file`: 광고 데이터 엑셀 파일
  - `margin_file`: 마진 데이터 엑셀 파일
  - `data_date` (optional): 데이터 날짜 (YYYY-MM-DD)

**Response**:
```json
{
  "status": "success",
  "message": "Successfully processed and integrated 150 records",
  "total_records": 150,
  "matched_with_ads": 120,
  "matched_with_margin": 145,
  "fully_integrated": 115,
  "warnings": []
}
```

### 2. GET /api/metrics
**설명**: 성과 메트릭 조회

**Query Parameters**:
- `start_date` (optional): 시작일 (YYYY-MM-DD)
- `end_date` (optional): 종료일 (YYYY-MM-DD)
- `product` (optional): 상품명 필터 (LIKE 검색)

**Response**:
```json
{
  "period": "2024-01-01 to 2024-01-31",
  "total_sales": 5000000.0,
  "total_profit": 1200000.0,
  "total_ad_cost": 300000.0,
  "avg_margin_rate": 24.5,
  "daily_trend": [
    {
      "date": "2024-01-01",
      "total_sales": 100000.0,
      "total_profit": 25000.0,
      "ad_cost": 5000.0
    }
  ],
  "by_product": [
    {
      "option_id": 123456,
      "option_name": "네이비",
      "product_name": "헤몬팜 키토트랩 모기 퇴치기...",
      "total_sales": 500000.0,
      "total_profit": 120000.0,
      "total_quantity": 50,
      "total_ad_cost": 30000.0,
      "margin_rate": 24.0
    }
  ]
}
```

### 3. GET /api/summary
**설명**: 전체 요약 통계

**Response**:
```json
{
  "total_sales": 10000000.0,
  "total_profit": 2500000.0,
  "total_ad_cost": 500000.0,
  "avg_margin_rate": 25.0,
  "total_orders": 1500,
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-12-31"
  }
}
```

---

## 파일 구조

```
쿠팡자동/
├── backend/
│   ├── app.py                      # FastAPI 메인 앱
│   ├── models/
│   │   └── schemas.py              # Pydantic 스키마
│   ├── routers/
│   │   ├── upload.py               # 파일 업로드 엔드포인트
│   │   ├── metrics.py              # 메트릭 조회 엔드포인트
│   │   └── report.py               # 리포트 엔드포인트
│   ├── services/
│   │   ├── database.py             # DB 모델 및 계산 로직
│   │   ├── integrated_parser.py    # 파일 파싱 및 통합
│   │   └── parser.py               # Legacy parser
│   └── data/
│       └── coupang_integrated.db   # SQLite 데이터베이스
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   └── DashboardPage.jsx   # 대시보드 페이지
│   │   ├── components/             # 재사용 컴포넌트
│   │   ├── App.jsx                 # 메인 앱
│   │   └── main.jsx                # 엔트리 포인트
│   ├── package.json
│   └── vite.config.js
│
└── .serena/
    ├── data_flow_analysis.md       # 옵션 그룹화 문제 분석
    └── complete_workflow_analysis.md  # 전체 작업 흐름 분석 (본 문서)
```

---

## 핵심 개념 정리

### 1. option_id의 중요성
- **유일 키**: 모든 데이터 통합의 기준
- **옵션 구분**: 동일 상품의 다른 옵션(색상, 사이즈 등) 구분
- **인덱싱**: UNIQUE INDEX로 빠른 검색 및 중복 방지
- **그룹화**: 성과 분석 시 option_id 기준으로 그룹화하여 옵션별 분리

### 2. LEFT JOIN 전략
- **기준**: 판매 데이터를 기준으로 설정
- **이유**: 판매가 발생한 상품을 중심으로 광고/마진 데이터 보강
- **NaN 처리**: 매칭되지 않는 값은 0으로 채워 계산 오류 방지

### 3. 계산 시점
- **저장 시**: 파일 업로드 → DB 저장 직전 `calculate_metrics()` 호출
- **장점**: API 조회 시 빠른 응답 (미리 계산된 값 사용)
- **단점**: 공식 변경 시 전체 데이터 재계산 필요 (DB 재업로드)

### 4. 중복 처리 전략
- **현재**: `drop_duplicates(keep='first')` - 첫 번째 레코드만 유지
- **이전**: `groupby().agg()` - 중복 값 합산
- **선택 이유**: 사용자가 중복 option_id를 합산하지 않고 첫 번째만 사용하길 원함

### 5. 필터링 전략
- **DB 레벨**: date 범위, product_name LIKE 검색
- **API 레벨**: total_sales > 0 필터링
- **이유**: 판매가 없는 상품은 성과 분석에서 제외

---

## 트러블슈팅 가이드

### 문제 1: 옵션이 합쳐져서 표시됨
**증상**: "네이비", "화이트" 옵션이 하나의 행으로 합쳐짐

**원인**:
- `metrics.py`에서 product_name으로 그룹화
- ProductMetric 스키마에 option_id/option_name 필드 누락

**해결**:
1. schemas.py에 option_id, option_name 추가
2. metrics.py의 그룹화 키를 option_id로 변경
3. 프론트엔드에 옵션 컬럼 추가

### 문제 2: 광고비가 0으로 표시됨
**증상**: 광고 데이터가 업로드되었는데 대시보드에서 0원으로 표시

**원인**:
- 광고 파일의 option_id와 판매 파일의 option_id가 매칭되지 않음
- 컬럼명 불일치

**해결**:
1. integrated_parser.py의 디버그 로그 확인
2. option_id 데이터 타입 확인 (int64 변환 필수)
3. 엑셀 파일의 컬럼명이 매핑과 일치하는지 확인

### 문제 3: 순이익 계산이 이상함
**증상**: 매출이 높은데 순이익이 마이너스

**원인**:
- 도매가, 수수료, 부가세가 누락됨
- 광고비가 과도하게 높음
- 계산 공식 오류

**해결**:
1. 마진 파일에 필수 컬럼 확인 (도매가, 수수료, 부가세)
2. calculate_metrics() 로직 확인
3. 광고비 × 1.1 계산이 적용되었는지 확인

### 문제 4: 서버 자동 리로드 안됨
**증상**: 코드 변경 후 서버가 자동으로 재시작되지 않음

**원인**:
- Uvicorn --reload 플래그 누락
- 파일 감시 시스템 오류

**해결**:
1. 서버 수동 재시작: 기존 프로세스 kill → 재시작
2. --reload 플래그 확인
3. 필요시 DB 삭제 후 재시작

### 문제 5: DB에 데이터가 없음
**증상**: 파일 업로드 성공했는데 대시보드에서 데이터 없음

**원인**:
- 파싱 중 예외 발생
- option_id가 NaN으로 변환되어 dropna()에서 제거됨
- DB commit 실패

**해결**:
1. 백엔드 로그 확인 (파싱 에러 메시지)
2. option_id 컬럼의 데이터 타입 확인
3. DB 파일 존재 여부 확인
4. 업로드 Response의 warnings 확인

---

## 성능 최적화

### 현재 구현
- **인덱싱**: option_id (UNIQUE), product_name, date에 인덱스 설정
- **미리 계산**: 저장 시점에 순이익, 이윤율, ROAS 계산
- **필터링**: DB 쿼리 레벨에서 date 범위 필터링

### 개선 가능 영역
1. **페이지네이션**: 대량 데이터 시 테이블 페이징 추가
2. **캐싱**: 자주 조회하는 메트릭 Redis 캐싱
3. **Lazy Loading**: 차트 데이터 필요 시에만 로드
4. **배치 처리**: 대량 파일 업로드 시 비동기 처리

---

## 향후 개선 사항

### 1. 업로드 페이지 구현
- 현재 업로드는 별도 도구 필요
- 프론트엔드에 파일 업로드 UI 추가

### 2. 데이터 검증 강화
- 필수 컬럼 누락 시 명확한 에러 메시지
- 데이터 타입 불일치 사전 검증
- option_id 중복 경고

### 3. 히스토리 관리
- 동일 option_id의 일자별 변화 추적
- 과거 데이터 비교 기능

### 4. 엑셀 익스포트
- 대시보드 데이터를 엑셀로 다운로드
- 커스텀 리포트 생성

### 5. 알림 기능
- 이윤율이 특정 수준 이하일 때 알림
- 광고비 대비 매출이 낮을 때 경고

---

## 요약

이 시스템은 **쿠팡 판매 데이터**, **광고 데이터**, **마진 데이터**를 **option_id 기준으로 통합**하여, 각 상품 옵션별 성과를 자동으로 분석하고 대시보드에 시각화하는 웹 애플리케이션입니다.

**핵심 특징**:
- ✅ 3개 엑셀 파일 원클릭 통합
- ✅ 옵션별 분리 표시 (네이비/화이트 등)
- ✅ 광고비 부가세 포함 정확한 순이익 계산
- ✅ 실시간 이윤율 및 ROAS 분석
- ✅ 완전 한글화된 직관적 UI
- ✅ 매출 0인 상품 자동 필터링

**데이터 플로우**:
```
엑셀 업로드 → 파싱 → LEFT JOIN 통합 → DB 저장 → calculate_metrics() → API 조회 → 대시보드 표시
```

**핵심 계산식**:
```
순이익 = 매출 - (도매가 + 수수료 + 부가세) × 판매량 - 광고비 × 1.1
이윤율 = (순이익 / 매출) × 100
ROAS = 매출 / 광고비
```

이 문서는 시스템의 전체 작업 흐름을 이해하고, 문제 발생 시 빠르게 원인을 파악하여 해결하는 데 도움이 됩니다.
