# 쿠팡 데이터 통합 시스템 - 옵션별 표시 문제 분석

## 📊 작업 흐름 (Data Flow)

### 1단계: 데이터 업로드 (integrated_parser.py)
```
판매 엑셀 → 광고 엑셀 → 마진 엑셀
     ↓           ↓          ↓
  option_id 기준으로 merge
     ↓
데이터베이스에 저장 (✅ 옵션별로 개별 레코드 저장)
```

**상태**: ✅ 정상
- 각 옵션 ID마다 별도 레코드 생성
- option_name 포함됨

### 2단계: API 데이터 조회 (metrics.py)
```python
# backend/routers/metrics.py:76-105

product_metrics = {}
for record in records:
    product_name = record.product_name  # ⚠️ 문제!
    if product_name not in product_metrics:
        product_metrics[product_name] = {...}

    # product_name으로 그룹화 → 옵션들이 합쳐짐!
    product_metrics[product_name]['total_sales'] += record.sales_amount
    product_metrics[product_name]['total_profit'] += record.net_profit
```

**상태**: ❌ **문제 발견!**
- `product_name`으로만 그룹화
- 같은 상품명을 가진 다른 옵션들이 모두 합쳐짐
- option_id나 option_name을 고려하지 않음

### 3단계: 프론트엔드 표시 (DashboardPage.jsx)
```javascript
// frontend/src/pages/DashboardPage.jsx:389-423

{metrics.by_product.map((product, index) => (
  <TableRow>
    <TableCell>{product.product_name}</TableCell>
    <TableCell>{formatCurrency(product.total_sales)}</TableCell>
    ...
  </TableRow>
))}
```

**상태**: 정상 (API에서 받은 데이터를 그대로 표시)

## 🔍 문제점 요약

### 현재 상황:
1. **DB 저장**: 옵션별로 개별 레코드 ✅
   - 89048355196: 헤몬팜 키토트랩 (옵션1)
   - 89048355197: 헤몬팜 키토트랩 (옵션2)

2. **API 그룹화**: product_name으로만 그룹화 ❌
   - "헤몬팜 키토트랩" → 모든 옵션 합산

3. **화면 표시**: 합쳐진 데이터 표시 ❌
   - "헤몬팜 키토트랩": 총 매출 (모든 옵션 합계)

### 왜 합쳐지는가?
```python
# 예시:
record1: product_name="헤몬팜 키토트랩", option_name="네이비", sales=1000만
record2: product_name="헤몬팜 키토트랩", option_name="화이트", sales=900만

# product_name으로 그룹화하면:
"헤몬팜 키토트랩": sales = 1900만 (합쳐짐!)
```

## 💡 해결 방안

### 옵션 1: 상품명 + 옵션명 조합 (추천)
```python
# product_name + option_name을 키로 사용
key = f"{product_name} - {option_name}"
```

### 옵션 2: 옵션 ID 기준
```python
# option_id를 키로 사용
key = option_id
```

### 옵션 3: 별도 API 엔드포인트 추가
- `/api/metrics/products` - 상품별 합산
- `/api/metrics/options` - 옵션별 개별 표시

## 📝 수정 필요 파일

1. `backend/routers/metrics.py` - API 로직 수정
2. `backend/models/schemas.py` - 스키마에 option_name 추가
3. `frontend/src/pages/DashboardPage.jsx` - 표시 컬럼 추가

## 🎯 기대 효과

수정 후:
```
헤몬팜 키토트랩 - 네이비    1000만원
헤몬팜 키토트랩 - 화이트     900만원
믹서기 - 레드              500만원
믹서기 - 블루              400만원
```
