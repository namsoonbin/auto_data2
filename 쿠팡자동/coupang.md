쿠팡 스토어 매출/광고 실적 자동화 웹앱 설계 및 구현
개요 (Introduction)
쿠팡 관련 여러 스토어의 월별 판매 실적, 마진, 광고비 등을 자동으로 집계하는 내부용 웹 애플리케이션을 설계합니다. 기존에는 매월 엑셀로 판매/광고 데이터를 정리하고 수기로 계산해 왔지만, 이를 FastAPI 기반 Python 백엔드와 React 프론트엔드로 구성된 웹 앱으로 자동화합니다. 이 애플리케이션은 다음과 같은 핵심 기능을 갖습니다:
•	엑셀 업로드: 판매 실적 및 광고 비용 엑셀 파일 업로드 (일자별/상품별 데이터 파싱)
•	자동 계산: 업로드된 데이터로부터 판매 수수료, 결제 수수료, 부가세, 광고비, 마진율, 순이익 등을 자동 계산
•	대시보드 조회: 특정 기간별, 스토어별, 상품별 실적을 차트와 표로 시각화
•	리포트 생성: 주간/월간 요약 보고서를 화면 표시 또는 PDF 파일로 생성
•	관리자 전용: 내부 관리자용 웹이므로 별도의 회원가입이나 권한 관리는 불필요
기술 스택은 FastAPI (Python) 백엔드와 React 프론트엔드 조합을 사용하며, Vercel이나 Render 같은 무료 클라우드 환경에 배포하기 적합하도록 설계합니다. 처음 버전에서는 Coupang Open API 대신 엑셀 수기 업로드 방식으로 구현하되, 향후 Open API 연동을 쉽게 확장할 수 있는 구조로 계획합니다.
시스템 아키텍처 및 기술 스택
이 웹 애플리케이션은 RESTful API 백엔드와 싱글 페이지 애플리케이션(SPA) 프론트엔드로 구성됩니다. 두 부분은 분리 배포되어, 프론트엔드는 Vercel과 같은 플랫폼에 정적 파일로 호스팅되고, 백엔드는 Render와 같은 무료 서버 호스팅에 배포됩니다. 이렇게 분리하면 각각의 환경에 최적화하고 독립적으로 확장할 수 있습니다.
•	FastAPI 백엔드: 파일 업로드, 데이터 파싱, 계산 로직, PDF 생성 등을 처리하는 REST API 서버입니다. Uvicorn과 같은 ASGI 서버로 실행되며 JSON 형태로 데이터를 제공합니다. FastAPI는 Python 타입 힌트를 활용한 자동 문서화와 고성능 비동기 처리를 지원하여 적합합니다[1]. 또한 범용 웹 서버이므로, 향후 Coupang Open API와의 연동이나 데이터베이스 연동도 용이합니다.
•	React 프론트엔드: 사용자는 브라우저를 통해 React 앱에 접근하여 파일 업로드 양식, 대시보드 차트/표, 리포트 화면을 인터랙티브하게 이용합니다. React에서는 Fetch/Axios 등을 통해 FastAPI 엔드포인트를 호출하고, 받은 데이터를 시각화합니다. 차트 라이브러리로는 Chart.js (react-chartjs-2)나 Recharts, ApexCharts 등을 활용하여 손쉽게 그래프를 구현할 수 있습니다. UI 구성에는 Material-UI같은 컴포넌트를 써서 빠르게 내부용 대시보드를 구축할 수 있습니다.
두 부분은 CORS 설정을 통해 통신합니다. FastAPI에서 from fastapi.middleware.cors import CORSMiddleware를 사용해 프론트엔드 도메인을 허용하면, React 앱에서 API 호출이 가능해집니다. 또한 인증/권한관리는 생략하므로 복잡한 OAuth나 세션 관리 없이, 배포 시 내부 관리자만 접근 가능한 형태(예: 사설 네트워크 또는 간단한 HTTP Auth 적용)로 운영하면 됩니다.
백엔드 구현 (FastAPI)
백엔드는 FastAPI를 사용하여 주요 기능별로 엔드포인트를 설계하고, 내부 로직은 모듈화하여 유지보수가 쉽도록 합니다. 프로젝트 구조는 다음과 같이 구성합니다:
backend/
├── app.py            # FastAPI 앱 실행 및 라우터 포함
├── routers/          # 각 기능별 API 엔드포인트 정의
│   ├── __init__.py
│   ├── upload.py     # 파일 업로드 관련 엔드포인트 (판매/광고 실적)
│   ├── metrics.py    # 데이터 조회 및 대시보드용 엔드포인트
│   └── report.py     # 리포트(PDF) 생성 엔드포인트
├── services/         # 핵심 로직 (파싱, 계산 등) 모듈
│   ├── __init__.py
│   ├── parser.py     # 엑셀 파싱 및 데이터 로딩
│   └── calculations.py  # 수수료, 마진 등 계산 로직
├── models/
│   ├── __init__.py
│   └── schemas.py    # Pydantic 모델 정의 (요청/응답 스키마)
├── data/
│   └── database.db   # (옵션) SQLite 데이터베이스 또는 데이터 파일
├── requirements.txt  # 필요한 패키지 (FastAPI, pandas 등)
└── Dockerfile        # (배포용) 컨테이너 이미지 빌드 설정
위 구조에서 app.py는 FastAPI 인스턴스를 생성하고 각 router를 include하여 전체 API를 빌드하는 진입점입니다[2]. routers 폴더에는 세부적인 API 엔드포인트들이 모듈 단위로 정의됩니다. 예를 들어 upload.py에는 파일 업로드 및 파싱 관련 /upload 엔드포인트들이 있고, metrics.py에는 실적 조회를 위한 /metrics 엔드포인트, report.py에는 PDF 리포트 생성을 위한 /report 엔드포인트 등이 들어갑니다.
services 폴더는 비즈니스 로직을 담은 모듈로, parser.py에서 엑셀 파일을 읽어들이는 함수와 데이터 저장 함수를 제공하고, calculations.py에서 각종 수치 계산 함수를 제공합니다. models/schemas.py에는 Pydantic의 BaseModel을 사용해 데이터 구조(예: SaleRecord, MetricsResponse 등)를 정의하여 요청 데이터 검증과 응답 JSON 구조를 명시합니다. (예: 기간별 조회 시 요청 파라미터, 응답으로 보내는 요약 실적 데이터 구조 등을 스키마로 정의)
1. 엑셀 파일 업로드 및 파싱
파일 업로드 엔드포인트는 FastAPI의 UploadFile 타입을 사용하여 구현합니다. 예를 들어, 판매 실적 엑셀을 업로드하는 POST /upload/sales 엔드포인트와 광고비 엑셀을 위한 POST /upload/ads 엔드포인트를 마련합니다. 업로드된 파일은 UploadFile.file 속성을 통해 파이썬 파일 객체로 취급할 수 있으며, pandas를 이용하여 DataFrame으로 읽어들입니다[3].
•	엔드포인트 예시 (routers/upload.py):
 	from fastapi import APIRouter, File, UploadFile, HTTPException
from services import parser

router = APIRouter()

@router.post("/upload/sales")
async def upload_sales_file(file: UploadFile = File(...)):
    if file.filename.split(".")[-1] not in ["xlsx", "xls", "csv"]:
        raise HTTPException(status_code=400, detail="지원되지 않는 파일 형식입니다.")
    # 업로드 파일을 판다스로 읽기
    data = await parser.parse_sales_file(file)
    return {"status": "success", "records": len(data)}

@router.post("/upload/ads")
async def upload_ads_file(file: UploadFile = File(...)):
    # 유사하게 광고 엑셀 파싱
    data = await parser.parse_ads_file(file)
    return {"status": "success", "records": len(data)}
여기서 parser.parse_sales_file과 parser.parse_ads_file은 services/parser.py에 정의된 엑셀 파싱 함수입니다. UploadFile을 인자로 받아 비동기로 파일 내용을 읽은 뒤, pandas.read_excel() 등을 사용해 DataFrame으로 변환합니다. 예를 들어 parser.py 내 구현은 다음과 같을 것입니다:
import pandas as pd
from io import BytesIO

# (예시) 판매 실적 엑셀 파싱
async def parse_sales_file(upload_file):
    content = await upload_file.read()               # 비동기로 파일 데이터를 읽음 (bytes)
    excel_data = BytesIO(content)
    df = pd.read_excel(excel_data)                   # 판다스로 엑셀 로드
    # 필요한 컬럼 추출 및 가공 (예: Date, Product, Sales, etc.)
    records = df.to_dict(orient="records")
    # TODO: 데이터베이스에 records 저장 or 글로벌 변수에 보관
    upload_file.file.close()                         # 파일 객체 닫기
    return records

async def parse_ads_file(upload_file):
    content = await upload_file.read()
    excel_data = BytesIO(content)
    df = pd.read_excel(excel_data)
    records = df.to_dict(orient="records")
    upload_file.file.close()
    return records
위 예시는 단순화를 위해 DataFrame 전체를 to_dict로 변환하고 바로 반환하지만, 실제로는 파싱한 데이터를 내부 저장해야 합니다. 간단한 구현으로는, 파싱 결과인 records 리스트를 전역 변수나 메모리 객체(예: database = {"sales": [], "ads": []} 딕셔너리)에 누적할 수 있습니다. 그러나 향후 확장성과 여러 기간의 데이터 축적을 고려하면 데이터베이스를 사용하는 것이 바람직합니다. 예를 들어 SQLite를 사용한다면 SaleRecord 테이블과 AdRecord 테이블을 만들고, 각 업로드시 해당 테이블에 레코드를 삽입해두면 이후 조회 쿼리에 활용할 수 있습니다. (FastAPI에서 SQLAlchemy 연동 가능)
참고: UploadFile.file은 실제 Python 파일 객체 (SpooledTemporaryFile)이며, 이것을 Pandas에 직접 전달하여 읽을 수 있습니다[3]. 상기 코드에서는 await upload_file.read()로 바이너리를 얻어 BytesIO 스트림을 만들고 pd.read_excel에 주입하는 방법을 사용했습니다. 또한 파일을 다 읽고 나면 upload_file.file.close()로 리소스를 닫아줍니다.
2. 실적 자동 계산 로직
업로드된 원본 데이터를 저장한 후, 판매 수수료, 부가세, 광고비, 마진율, 순이익 등의 파생 지표를 자동 계산합니다. 계산 로직은 services/calculations.py 모듈에 함수들로 구현해 두고, 조회 요청이 올 때마다 데이터를 가공하거나, 업로드 시점에 계산 필드를 미리 추가할 수 있습니다. 주요 계산 요소는 다음과 같습니다:
•	판매 수수료: 카테고리별로 상이한 기본 수수료율(예: 5~15%)을 적용합니다[4]. 현재 버전에서는 모든 상품에 대해 일괄적인 수수료율 (예: 10%)을 가정하거나, 필요시 엑셀에 카테고리 정보를 추가 입력받아 적용합니다. 판매 가격에 기본 수수료율을 곱해 산출합니다.
•	결제 수수료: 쿠팡은 모든 거래에 대해 약 2.9%의 결제 프로세싱 수수료를 부과합니다[5]. 따라서 판매금액에 2.9%를 곱해 계산합니다.
•	부가세(VAT): 쿠팡에 지불하는 수수료들에 대해 10%의 부가가치세가 추가로 부과됩니다[6]. 즉, (판매수수료 + 결제수수료)의 합계에 10%를 곱해 부가세를 산출합니다.
•	총 플랫폼 수수료: 위의 기본 수수료 + 결제 수수료 + 부가세의 합으로, 거래당 발생하는 전체 수수료 비용입니다. 예를 들어 8,000원에 상품이 판매되었다면 (할인 등 적용 후 최종 결제금액) 기본 수수료 10% 800원, 결제수수료 2.9% 232원, 부가세 103원을 합쳐 총 1,135원의 수수료가 듭니다[5]. 판매자는 8,000원 중 6,865원을 정산받게 됩니다[7].
•	광고비: 업로드된 광고 비용 데이터를 해당 기간/상품별로 합산합니다. 광고비에도 부가세가 붙어 청구되므로 (예: 11% 포함된 금액으로 청구) 필요하면 별도로 세전 금액을 계산할 수 있지만, 여기서는 지출된 광고비 총액을 비용으로 간주합니다.
•	순이익: 특정 기간/상품의 매출총액 - 총 플랫폼 수수료 - 광고비로 계산합니다. (상품 원가나 물류비 등이 있다면 추가로 차감해야 하지만, 요청 범위에는 언급되지 않았으므로 플랫폼 관련 비용만 고려합니다.) 예를 들어 한 상품의 매출이 1,000,000원이고 총 수수료가 150,000원, 광고비가 50,000원이었다면 순이익은 800,000원이 됩니다.
•	마진율: 순이익을 매출액으로 나눈 비율로, %로 표시합니다. 위 예시의 경우 마진율은 80%가 되며, 플랫폼 수수료와 광고비 등을 반영한 이익율을 의미합니다. (만약 상품 원가까지 포함하면 이는 영업이익률 개념이 될 것입니다.)
위 계산 로직을 코드로 작성하면 예를 들어 calculations.py에 다음과 같은 함수들을 둘 수 있습니다:
# services/calculations.py

def calculate_fees_and_profit(record):
    """단일 판매 기록에 대해 수수료 및 이익 계산"""
    price = record["sale_price"]        # 판매금액 (쿠폰/할인 적용 후 최종 결제가)
    commission_rate = 0.10              # 예: 기본 판매 수수료 10%
    payment_fee_rate = 0.029            # 결제 수수료 2.9%
    # 수수료 계산
    commission = price * commission_rate
    payment_fee = price * payment_fee_rate
    vat = (commission + payment_fee) * 0.10
    total_fee = commission + payment_fee + vat   # 총 수수료 비용
    # 광고비 (해당 상품 해당 일자의 광고비 있으면 더함)
    ad_cost = record.get("ad_cost", 0)
    # 순이익 및 마진율
    profit = price - total_fee - ad_cost
    margin_rate = (profit / price * 100) if price > 0 else 0
    # 결과 반환 (필요시 소수점 처리 등)
    return {
        "commission": round(commission),
        "payment_fee": round(payment_fee),
        "vat": round(vat),
        "total_fee": round(total_fee),
        "ad_cost": round(ad_cost),
        "profit": round(profit),
        "margin_rate": round(margin_rate, 2)
    }
이 함수는 하나의 판매 레코드(딕셔너리)에 대해 수수료와 이익을 계산해주며, 조회 시 여러 레코드에 이 함수를 적용하여 총합/평균을 구하거나, 레코드 별로 계산 필드를 추가할 수 있습니다. 예컨대 엑셀 데이터를 파싱할 때 각 행에 대해 calculate_fees_and_profit을 호출하여 그 결과를 record에 합치는 방법도 있습니다.
참고: 실제 쿠팡 수수료는 카테고리에 따라 5~15%로 다양하고, 2025년부터 최종 결제금액 기준으로 계산되며 월별 고정 이용료(매출 100만원 이상 시 5.5만원) 등이 있습니다[4][8]. 본 설계에서는 단순화를 위해 고정 수수료율과 결제수수료만 고려했지만, 향후 카테고리 정보를 입력받아 수수료율을 동적으로 적용하거나 월 고정비용을 기간단위로 차감하는 등의 확장이 가능합니다.
3. 실적 조회 및 대시보드용 API
프론트엔드 대시보드에서 요구하는 특정 기간, 스토어별, 상품별 실적 데이터를 제공하기 위해, /metrics 등의 GET API 엔드포인트를 구현합니다 (routers/metrics.py). 이 엔드포인트는 쿼리 파라미터로 start_date, end_date, store, product 등을 받아 필터링된 데이터를 집계하여 반환합니다.
예를 들어, /metrics?store=ABC&start_date=2023-10-01&end_date=2023-10-31 식의 요청이 오면: 1. 저장된 데이터 중 스토어 "ABC"의 2023년 10월 한달치 기록을 조회합니다. (만약 데이터를 Pandas DataFrame으로 관리하고 있다면 df[(df['store']=='ABC') & (df['date']>=... ) & ...] 필터링을 수행하거나, SQL DB라면 해당 WHERE절로 조회) 2. 필터링된 판매 레코드 리스트에 대해, 매출 합계, 광고비 합계 등을 계산하고, calculate_fees_and_profit 함수를 각 레코드에 적용하여 총 수수료 합계, 총 이익, 평균 마진율 등을 구합니다. 3. 응답 JSON 구조를 만들어 반환합니다. 예를 들어:
{
  "period": {"start": "2023-10-01", "end": "2023-10-31"},
  "store": "ABC",
  "total_sales": 1500000,
  "total_ad_cost": 200000,
  "total_fee": 250000,
  "net_profit": 1050000,
  "avg_margin_rate": 70.0,
  "daily_trend": [ { "date": "2023-10-01", "sales": ..., "profit": ... }, ... ],
  "by_product": [ { "product": "상품A", "sales": ..., "profit": ..., "margin": ... }, ... ]
}
이런 식으로 요약 지표와 함께 일별 추이(daily_trend 리스트)나 상품별 상세(by_product 리스트)를 포함할 수 있습니다. 이는 프론트엔드에서 차트나 표를 구성하는데 활용됩니다.
metrics 엔드포인트 구현 시 Pydantic 응답 모델(schemas.py에 정의)을 사용할 수 있습니다. 예컨대 MetricsResponse 모델을 만들어 위 JSON 필드를 속성으로 정의해두면, FastAPI가 자동으로 문서화하고 스키마를 검증해줍니다. (내부 데이터 가공은 Pandas나 Python으로 하고, 최종적으로 Pydantic 모델에 넣어 리턴)
팁: 기간별 조회는 데이터량이 많아질 경우 집계에 시간이 소요될 수 있습니다. 간단한 실현을 위해 Pandas를 사용했지만, 추후에는 데이터베이스의 집계 함수나 ORM 쿼리로 대체하여 효율을 높일 수 있습니다. 또한 주간/월간 같은 고정 범위 리포트는 미리 계산된 값을 캐싱해둘 수도 있습니다.
4. PDF/리포트 생성 기능
관리자는 웹 화면에서 주간/월간 리포트를 확인하거나, 이를 PDF로 저장할 수 있어야 합니다. 이를 위해 두 가지 접근을 모두 고려합니다:
•	화면 기반 리포트: React 프론트엔드에서 특정 리포트 페이지(또는 대시보드에서 기간 선택 후 "리포트 보기")를 제공하여, 요약 지표와 차트를 한 눈에 볼 수 있는 보고서 화면을 보여줍니다. 이 페이지는 앞서 /metrics API를 호출하여 얻은 데이터를 보기 좋게 배치하며, 브라우저의 인쇄 기능을 통해 PDF로 저장할 수 있도록 프린트 스타일(CSS) 등을 준비할 수 있습니다. 예를 들어, A4 용지에 맞는 레이아웃을 디자인하고 @media print CSS를 적용하면 사용자가 브라우저에서 인쇄(PDF 저장)시 깔끔한 보고서를 얻을 수 있습니다.
•	PDF 다운로드 (서버 생성): FastAPI에서 /report GET 엔드포인트를 구현하여 서버가 즉시 PDF 파일을 생성하고 반환해주는 방법입니다. 이 경우 Python에서 PDF 생성 라이브러리를 사용합니다. 예를 들면 fpdf2 (PyFPDF의 포크)나 xhtml2pdf를 사용할 수 있습니다. xhtml2pdf를 쓰면 HTML+CSS 템플릿을 PDF로 렌더링할 수 있어 편리합니다[9]. fpdf2를 쓰면 파이썬 코드로 직접 PDF를 그릴 수 있습니다. 어떤 방식을 쓰든, FastAPI에서 PDF 바이트 데이터를 HTTP 응답으로 보내주면 됩니다.
•	report.py 엔드포인트 예시 (FPDF2 사용 가정):
 	from fastapi import APIRouter, Response
from fpdf import FPDF
from services.calculations import calculate_fees_and_profit
router = APIRouter()

@router.get("/report")
def get_report(store: str = None, start: str = None, end: str = None):
    # 1. 파라미터에 따라 데이터 필터링 및 집계
    data = ...  # store/start/end 기준으로 필터된 레코드 리스트
    summary = ...  # 총합 계산 (매출, 이익 등)
    # 2. FPDF로 PDF 생성
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, txt=f"Report for {store or 'All Stores'}", ln=1)
    pdf.set_font('Helvetica', '', 12)
    pdf.cell(0, 10, txt=f"Period: {start} ~ {end}", ln=1)
    # (요약 수치 및 표 등을 pdf.cell, pdf.multi_cell 등으로 추가)
    # ...
    pdf_output = pdf.output(dest='S').encode('latin1')  # PDF를 bytes로 얻기
    headers = {'Content-Disposition': 'attachment; filename="report.pdf"'}
    return Response(pdf_output, headers=headers, media_type='application/pdf')
 	위 코드에서 pdf.output(dest='S')를 통해 PDF 바이너리를 얻고, Content-Disposition 헤더를 attachment로 설정하여 파일 다운로드 형태로 응답하고 있습니다[10][11]. inline으로 설정하면 브라우저 내 PDF 뷰어로 바로 열리게 할 수도 있습니다[12].
•	만약 xhtml2pdf를 사용한다면, 미리 HTML 템플릿을 만들고 해당 HTML을 PDF로 변환합니다. FastAPI에서는 Jinja2 템플릿을 사용해 HTML을 만들고, 이를 pisa.CreatePDF(html, dest=result_stream) 형태로 PDF 생성한 뒤 스트림을 반환할 수 있습니다[13]. 이 경우에도 Response 또는 StreamingResponse로 PDF 바이트를 반환하면 됩니다.
주의: 무료 호스팅 환경에서는 서버에서 파일 생성 권한이나 메모리가 제한될 수 있습니다. FPDF 같은 경량 패키지를 쓰면 비교적 가볍게 PDF를 만들 수 있고, 소량 데이터 보고서라 큰 문제는 없습니다. 다만 대용량 보고서는 작업 큐나 비동기 백그라운드 작업으로 처리하도록 설계해야 할 수도 있습니다. 또한 회사 내부에서만 쓸 어플리케이션이라면, PDF 생성보다는 화면 보고서로 대체하고 필요할 때 관리자가 직접 인쇄(PDF로 저장)하는 방식도 충분히 고려 가능합니다.
프론트엔드 구현 (React)
프론트엔드는 React로 구현하여, 사용자가 편리하게 엑셀 업로드 및 대시보드를 이용할 수 있는 UI를 제공합니다. 프로젝트 구조는 create-react-app 또는 Next.js 등을 사용해 구성하며 (이 글에서는 CRA 구조 가정), 주요 폴더 구조는 다음과 같습니다:
frontend/
├── src/
│   ├── components/
│   │   ├── UploadForm.jsx       # 파일 업로드 컴포넌트
│   │   ├── Dashboard.jsx       # 대시보드 (차트, 표) 컴포넌트
│   │   ├── ChartCard.jsx       # 개별 차트 컴포넌트 (예: 막대그래프 등)
│   │   └── ReportView.jsx      # 리포트 화면 컴포넌트 (PDF 미리보기 용도)
│   ├── pages/
│   │   ├── HomePage.jsx        # 초기 페이지 (파일 업로드 및 요약)
│   │   └── DashboardPage.jsx   # 대시보드 페이지 (기간/스토어 필터 포함)
│   ├── App.js                  # 라우팅 설정 등
│   └── index.js
├── public/
│   └── index.html
└── package.json
라우팅은 React Router 등을 사용하여 Home (업로드) 페이지와 Dashboard 페이지, 그리고 (선택사항) Report 페이지로 구성합니다. Home에서는 관리자가 매달 받은 엑셀 파일들을 업로드할 수 있고, Dashboard에서는 누적된 데이터를 분석/필터링하여 보여줍니다.
1. 파일 업로드 UI
UploadForm.jsx 컴포넌트에서는 <input type="file"> 요소를 통해 사용자가 엑셀 파일을 선택하고, 업로드 타입(판매 or 광고)을 선택할 수 있도록 합니다 (예: 드롭다운이나 버튼으로 "판매실적 업로드", "광고비 업로드" 구분). 파일 선택 후 업로드 버튼을 누르면, fetch API를 사용해 FastAPI의 /upload/sales 또는 /upload/ads로 POST 요청을 보냅니다. 이때 FormData를 구성하여 파일 바이너리를 전송합니다:
// components/UploadForm.jsx (요약 예시)
import { useState } from 'react';

function UploadForm({ type }) {
  const [file, setFile] = useState(null);
  const handleFileChange = (e) => setFile(e.target.files[0]);

  const handleUpload = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    const endpoint = type === "sales" ? "/upload/sales" : "/upload/ads";
    try {
      const res = await fetch(endpoint, {
        method: "POST",
        body: formData
      });
      const result = await res.json();
      if (res.ok) {
        alert(`${type === "sales" ? "판매" : "광고"} 파일 업로드 성공: ${result.records}건 처리됨`);
      } else {
        alert("업로드 실패: " + result.detail);
      }
    } catch (err) {
      console.error("Upload error", err);
    }
  };

  return (
    <div>
      <h3>{type === "sales" ? "판매 실적 업로드" : "광고비 업로드"}</h3>
      <input type="file" accept=".xlsx, .xls, .csv" onChange={handleFileChange} />
      <button onClick={handleUpload}>업로드</button>
    </div>
  );
}
위 컴포넌트는 간단히 파일 하나를 전송하지만, 필요에 따라 여러 파일 동시 업로드도 구현할 수 있습니다. (FastAPI에서도 UploadFile을 리스트로 받아들이면 다중 파일을 처리 가능) 업로드가 성공하면 서버는 파싱 후 "status": "success"를 응답하므로, 이를 통해 사용자에게 성공 메시지를 띄우거나 다음 액션(예: 대시보드로 이동)으로 유도합니다.
주의: 프론트엔드에서 업로드 요청을 보낼 때 백엔드 URL은 절대경로로 호출해야 합니다 (예: https://my-api.onrender.com/upload/sales). 개발 단계에서는 프록시 설정을 하거나 CORS를 활성화한 채로 포트 간 통신을 합니다. 배포 시에는 프론트엔드 설정에 API 서버 URL을 환경변수로 넣어 빌드하는 방식을 사용할 수 있습니다.
2. 대시보드 UI (차트 & 표 시각화)
DashboardPage.jsx는 필터 폼과 Dashboard 컴포넌트로 구성됩니다. 필터 폼에서는 날짜 범위 선택(주간/월간 등)과 스토어 또는 상품 선택을 위한 입력을 제공합니다. 사용자가 필터를 적용하면, 앞서 만든 /metrics API를 호출하여 해당 범위의 데이터를 가져옵니다. 예를 들어:
// pages/DashboardPage.jsx (일부 발췌)
import { useState, useEffect } from 'react';
import Dashboard from '../components/Dashboard';

function DashboardPage() {
  const [filter, setFilter] = useState({ store: null, product: null, range: 'month' });
  const [metrics, setMetrics] = useState(null);

  const fetchMetrics = async () => {
    const params = new URLSearchParams();
    if (filter.store) params.append("store", filter.store);
    if (filter.product) params.append("product", filter.product);
    // 예: range가 'month'이면 최근 한달, 구체적 날짜 선택 시 start, end 설정 등
    params.append("start_date", "2023-10-01");
    params.append("end_date", "2023-10-31");
    const res = await fetch(`/metrics?${params.toString()}`);
    const data = await res.json();
    setMetrics(data);
  };

  useEffect(() => { fetchMetrics(); }, [filter]);

  return (
    <div>
      {/* 필터 UI (스토어 선택, 상품 선택, 기간 선택 등) */}
      <Dashboard data={metrics} />
    </div>
  );
}
Dashboard.jsx 컴포넌트에서는 props.data로 전달된 metrics 데이터를 받아 여러 개의 차트와 표를 렌더링합니다. 예를 들면: - 요약 박스: 총 매출, 순이익, 마진율 등을 큰 글씨로 표시. - 기간별 추이 차트: daily_trend 데이터를 활용해 라인 차트 (일자별 매출 또는 이익). - 상품별 실적 차트: by_product 데이터를 활용해 막대 차트 (상품별 매출 비교). - 상세 표: by_product 리스트나 daily_trend 리스트를 표로 나열하여 자세한 수치 확인.
차트는 앞서 언급한 React 차트 라이브러리를 이용합니다. 예를 들어 ChartCard.jsx를 만들어 Chart.js를 래핑하면, Dashboard.jsx에서 <ChartCard type="bar" data={...} /> 형태로 재사용이 가능합니다. 예시: Chart.js (react-chartjs-2)로 막대그래프를 보여주는 컴포넌트.
// components/ChartCard.jsx (예시 - Chart.js 사용 가정)
import { Bar } from 'react-chartjs-2';

function ChartCard({ title, labels, values }) {
  const data = {
    labels,
    datasets: [{
      label: title,
      data: values,
      backgroundColor: 'rgba(54, 162, 235, 0.5)'
    }]
  };
  const options = { plugins: { legend: { display: false } } };
  return (
    <div className="chart-card">
      <h4>{title}</h4>
      <Bar data={data} options={options} />
    </div>
  );
}
이를 이용해 Dashboard.jsx에서는, 예를 들어 상품별 매출 차트를 그릴 때:
<ChartCard 
  title="상품별 매출" 
  labels={data.by_product.map(item => item.product)} 
  values={data.by_product.map(item => item.sales)} 
/>
와 같이 사용할 수 있습니다. 표(Table)는 기본 <table> 혹은 Ant Design, Material-UI의 표 컴포넌트를 활용합니다. 상품별 상세 목록을 표로 표시하고, 총합 행을 하단에 추가하는 등의 형태를 취합니다.
전체적으로 대시보드 UI는 관리자가 한눈에 실적을 파악할 수 있도록 직관적으로 구성합니다. 예를 들어 색상으로 상승/하락 추이를 표시하거나, 전월 대비 증감 같은 추가 정보도 계산하여 보여줄 수 있습니다 (이 경우 백엔드에서 전월 데이터를 같이 보내주거나, 프론트에서 두 번 호출하여 비교).
3. 리포트 UI 및 PDF 다운로드
만약 리포트 화면을 별도로 두는 경우, ReportView.jsx 컴포넌트에서 특정 기간의 요약 내용을 정리된 형태(예: 표로 요약된 핵심 지표, 주요 상품 Top 5, 차트 축소판 등)로 보여줍니다. 화면 레이아웃은 A4 용지 비율에 맞춰 만들고, "PDF로 저장" 버튼을 제공하여 누르면 앞서 구현한 /report API를 호출, 반환된 PDF 파일을 브라우저에서 다운로드하도록 할 수 있습니다.
예를 들어 <a href="/report?start=2023-10-01&end=2023-10-31" target="_blank">PDF 다운로드</a> 형식의 링크를 제공하거나, fetch로 받아 blob 처리 후 URL.createObjectURL로 다운로드 트리거를 할 수 있습니다. 서버 생성 PDF 방식을 사용하면 정해진 포맷의 보고서를 정확히 전달할 수 있고, 화면 인쇄 방식은 사용자의 환경에 영향받을 수 있지만 개발이 단순합니다. 두 가지 방식은 필요에 따라 병행 구현할 수 있습니다.
확장성과 배포 고려사항
•	Coupang Open API 연동: 현재는 수동으로 받은 엑셀을 업로드하지만, 구조를 잘 분리해두면 Coupang Open API 클라이언트를 붙여 자동으로 데이터를 가져오도록 확장할 수 있습니다. 예를 들어 services/parser.py에서 현재는 엑셀 파싱을 하지만, 추후 services/coupang_api.py를 만들어 Open API로부터 주문 및 정산 데이터를 주기적으로 가져오는 기능을 추가하고, 동일한 데이터 저장 로직에 넣으면 됩니다. FastAPI의 BackgroundTasks나 스케줄러(lib) 등을 활용하면 일정 주기마다 데이터 동기화도 가능합니다.
•	데이터베이스: 내부 관리용이라 처음엔 데이터량이 작겠지만, 월별 데이터가 쌓이면 통계 처리에 DB가 유용합니다. SQLite를 시작으로, 필요시 PostgreSQL 같은 RDB로 마이그레이션할 수 있습니다. SQLAlchemy ORM을 도입해두면 DB 변경에도 코드 수정을 최소화할 수 있습니다. FastAPI 스타터 키트에서 자주 쓰는 구조처럼 database.py 모듈을 따로 만들어 DB 세팅과 세션 관리함수를 제공해도 좋습니다.
•	배포: React 앱은 정적 사이트로 Vercel이나 GitHub Pages에 올릴 수 있고, FastAPI는 Render, Railway, Deta Space 등 무료 옵션을 활용할 수 있습니다. Dockerfile을 작성해두면 배포 서비스에서 이미지를 빌드해 배포하기 쉽습니다. 예를 들어 Render에 배포할 땐 이 저장소를 연결하고 해당 Dockerfile로 배포하면 됩니다. 또한 환경변수로 데이터베이스 URL이나 CORS 도메인 등을 주입해 환경별 설정이 가능하게 합니다.
•	코드 관리: 프론트엔드와 백엔드를 분리된 레포지토리로 관리하거나, 하나의 모노레포 내에 /frontend, /backend 디렉토리로 관리할 수 있습니다. 내부용이라고 해도 형상관리는 중요하므로 Git을 통해 버전을 관리하고, 필요한 경우 CI/CD 파이프라인을 구성해 자동 배포하도록 설정합니다.
•	테스트: FastAPI는 pytest 등으로 API 테스트를 작성하기 쉽습니다. 주요 계산 로직 (calculations.py)에 대해 단위 테스트를 작성해두면 추후 수수료 정책 변화 등에 대응하기 수월합니다. 예컨대 특정 가상의 판매데이터에 대한 수수료/마진 계산 결과가 기대값과 일치하는지 테스트합니다.
•	UI/UX 개선: 내부 관리자분들이 쓰기 편하도록 UI에도 신경씁니다. 예를 들어, 업로드 후 자동으로 대시보드가 새로고침되고, 기간 선택을 최근 업로드한 달로 기본 설정하거나, 오류 발생 시 명확한 메시지 표시 등 사용성 개선을 합니다. 또한 차트나 표에서 값에 원(\₩) 표시나 세 자리 콤마 등 서식을 적용하고, 다운로드 받은 PDF 보고서에도 회사 로고나 작성일 등의 부가 정보를 포함하면 실무 활용도가 높아집니다.
맺음말
요약하면, 이 내부용 웹앱은 백엔드의 강력한 데이터 처리 능력과 프론트엔드의 편리한 시각화를 결합하여, 쿠팡 스토어들의 매출·광고 데이터를 효율적으로 관리하게 해줍니다. 처음에는 엑셀 업로드로 시작하지만, 모듈화된 아키텍처 덕분에 추후 API 연동, 기능 확장, 사용자 증가에도 견딜 수 있습니다. FastAPI와 React의 조합은 개발 생산성도 높고 배포도 용이하므로, 작은 사내툴부터 시작해 점차 발전시켜 나갈 수 있을 것으로 기대됩니다. 필요한 전체 코드 구조와 예시를 위와 같이 구축하여 목표 기능을 구현할 수 있습니다. 필요한 경우 추후 기능 추가(예: 실시간 대시보드, 알림 등)도 이 구조 위에 무리 없이 추가 가능합니다.
사용자는 이제 일일이 엑셀을 다루지 않고 웹 대시보드와 자동 계산된 리포트를 통해 신속하게 비즈니스 의사결정을 할 수 있게 될 것입니다.
________________________________________
[1] [2] FastAPI Best Practices: A Condensed Guide with Examples - DEV Community
https://dev.to/devasservice/fastapi-best-practices-a-condensed-guide-with-examples-3pa5
[3] python - How to upload a CSV file in FastAPI and convert it into a Pandas Dataframe? - Stack Overflow
https://stackoverflow.com/questions/71477787/how-to-upload-a-csv-file-in-fastapi-and-convert-it-into-a-pandas-dataframe
[4] [5] [6] [7] [8] 2025 쿠팡 판매 수수료 완전정리 OSC • OSC 오에스씨ㆍ쿠팡광고파트너
https://oscsnm.com/coupang-selling-fee-2025/
[9] [13]  Generate Elegant PDFs with FastAPI: A Step-by-Step Guide | by Ramesh Kannan s | Medium
https://medium.com/@rameshkannanyt0078/generate-elegant-pdfs-with-fastapi-a-step-by-step-guide-7fa386f922bd
[10] [11] [12] python - How to generate and return a PDF file from in-memory buffer using FastAPI? - Stack Overflow
https://stackoverflow.com/questions/76195784/how-to-generate-and-return-a-pdf-file-from-in-memory-buffer-using-fastapi
