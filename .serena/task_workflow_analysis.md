# 쿠팡 판매 데이터 자동화 시스템 분석

## 1. 시스템 아키텍처

Tech Stack:
- Backend: FastAPI (Python)
- Frontend: React (Vite) + Material-UI  
- Database: SQLite
- Data: Pandas (Excel 파싱)

## 2. 데이터 흐름

[3개 Excel] -> [파싱] -> [LEFT JOIN] -> [자동 계산] -> [DB] -> [대시보드]
(판매,광고,마진)  option_id   (순이익,ROAS)

## 3. 파일 파싱

upload.py:
- POST /api/upload/integrated
- 3개 파일 동시 처리
- 파일 형식 검증 (.xlsx, .xls)
- 데이터 날짜 검증

integrated_parser.py:
- Sales: option_id, product_name, sales_amount, sales_quantity, order_count
- Ads: option_id, ad_cost, impressions, clicks  
- Margin: option_id, cost_price, margin_rate, vat, fee_amount

## 4. LEFT JOIN 병합

Step 1: Sales + Ads (LEFT)
Step 2: (Sales + Ads) + Margin (LEFT)

결과: 판매 데이터 기준, 광고/마진 없으면 0
중복 제거: option_id 기준 첫번째

## 5. 계산 로직

순이익 = 매출 - 총비용 - (광고비 × 1.1)
총비용 = (도매가 + 수수료 + VAT) × 판매량
이윤율(%) = (순이익 / 매출) × 100
ROAS = 매출 / 광고비

DB: IntegratedRecord.calculate_metrics() 자동 호출

## 6. API 엔드포인트

/api/metrics - 기간별 지표 (일별 + 옵션별)
/api/metrics/roas - ROAS 분석
/api/metrics/summary - 전체 요약

## 7. Frontend

DashboardPage:
- Summary Cards (5개)
- 날짜 범위 선택
- 상품별 성과 테이블
- 이윤율 색상 표시 (>30% 녹색, >15% 주황, <15% 빨강)

## 8. 최근 변경사항 (2024년 10월)

1. 도매가 기준 명시: cost_price = 한국 도매가
2. 옵션별 분리: option_id, option_name 필드 추가
3. 광고비 부가세: net_profit = sales - cost - (ad_cost × 1.1)
4. 광고 컬럼 확대: impressions, clicks, ad_sales_quantity 추가

## 9. 문제점

- 데이터 무결성: date 미포함, option_id만으로 중복 제거 → 날짜별 데이터 손실
- NULL 처리: 0과 NULL 구별 불가
- 성능: iterrows() 반복, 매번 flush → 느림
- 보안: 파일 검증 부족, 인증 없음
- 에러: 상세 오류 메시지 부족

## 10. 개선 권장

즉시: 날짜 복합키, NULL 처리, 파일 검증, 오류 로깅
1개월: bulk insert, 인증, 인덱싱
3개월: 차트, 내보내기, 리포트 스케줄
6개월: PostgreSQL, 팀협업, 분석 고도화
