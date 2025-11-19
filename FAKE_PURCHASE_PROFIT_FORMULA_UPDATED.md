# 가구매 반영 순이익 계산식 (최종 수정본)

## 📋 개요

가구매(Fake Purchase) 발생 시 **정확한 순이익** 계산을 위한 조정 로직

**최종 업데이트**: 2025-11-19
**주요 변경사항**: 가구매 비용을 광고비에 포함하도록 수정

---

## 🔢 최종 조정 순이익 공식

```python
adjusted_profit = net_profit - sales_deduction + cost_saved - fake_purchase_cost
```

**구성 요소**:

1. `net_profit`: 기본 순이익 (가구매 포함된 원본 데이터 기준)
2. `sales_deduction`: 가구매 매출 차감분
3. `cost_saved`: 발생하지 않은 비용 (비용 절감분)
4. `fake_purchase_cost`: 가구매 서비스 비용 (광고비 성격)

---

## 📊 세부 계산식

### 1. 기본 순이익 (net_profit)

```python
net_profit = sales_amount - total_cost - (ad_cost × 1.1)
```

**where**:
- `total_cost = (cost_price + fee_amount + vat) × sales_quantity`
- `ad_cost × 1.1`: 광고비 + 부가세 10%

### 2. 매출 차감분 (sales_deduction)

```python
sales_deduction = 가구매_수량 × 단가
```

**의미**: 가구매로 인한 허위 매출 제거

### 3. 비용 절감분 (cost_saved)

```python
cost_saved = 가구매_수량 × (도매가 + 수수료 + 부가세)
           = 가구매_수량 × unit_cost
```

**의미**: 물건을 받지 않아 발생하지 않은 비용

### 4. 가구매 서비스 비용 (fake_purchase_cost) ⭐ **신규 추가**

```python
fake_purchase_cost = FakePurchase.total_cost
                   = 가구매_수량 × [(단가 × 12%) + 4,500원]
```

**의미**: 가구매 대행 업체에 지불하는 서비스 비용 (광고비 성격)
**특징**: 부가세 미적용 (1.1 곱하지 않음)

---

## 💰 광고비 조정

### 조정 광고비

```python
adjusted_ad_cost = ad_cost + fake_purchase_cost
```

### 광고비 비율 계산

```python
ad_cost_rate = ((adjusted_ad_cost × 1.1) / adjusted_sales) × 100
             = (((ad_cost + fake_purchase_cost) × 1.1) / adjusted_sales) × 100
```

**주의**: 가구매 비용 자체는 1.1을 곱하지 않지만, 전체 광고비에 대해서는 1.1을 곱함

---

## 📊 구체적 계산 예시

### 시나리오

**판매 기록** (IntegratedRecord):
- 판매 수량: 10개
- 단가: 10,000원
- 매출액: 100,000원
- 도매가: 6,000원
- 수수료: 500원
- 부가세: 500원
- 광고비: 5,000원

**가구매 기록** (FakePurchase):
- 가구매 수량: 1개
- 단가: 10,000원

### 계산 과정

#### 1단계: 기본 순이익

```python
unit_cost = 6,000 + 500 + 500 = 7,000원
total_cost = 7,000 × 10 = 70,000원
net_profit = 100,000 - 70,000 - (5,000 × 1.1)
           = 100,000 - 70,000 - 5,500
           = 24,500원
```

#### 2단계: 가구매 조정값 계산

```python
sales_deduction = 1 × 10,000 = 10,000원
cost_saved = 1 × 7,000 = 7,000원
fake_purchase_cost = (10,000 × 0.12) + 4,500
                   = 1,200 + 4,500
                   = 5,700원
```

#### 3단계: 조정 순이익

```python
adjusted_profit = 24,500 - 10,000 + 7,000 - 5,700
                = 15,800원
```

#### 4단계: 조정 광고비

```python
adjusted_ad_cost = 5,000 + 5,700 = 10,700원
```

#### 5단계: 광고비 비율

```python
adjusted_sales = 100,000 - 10,000 = 90,000원
ad_cost_rate = (10,700 × 1.1 / 90,000) × 100
             = (11,770 / 90,000) × 100
             = 13.08%
```

### 검증

**실제 상황**:
- 실제 판매: 9개
- 실제 매출: 90,000원
- 실제 상품 비용: 9 × 7,000 = 63,000원
- 광고비 (부가세 포함): 5,500원
- 가구매 비용: 5,700원
- **실제 순이익**: 90,000 - 63,000 - 5,500 - 5,700 = 15,800원 ✅

**공식 검증 완료!**

---

## 🔧 구현 위치

### 1. adjustment_service.py (라인 122-127)

```python
fake_purchase_adjustments[key] = {
    'sales_deduction': sales_deduction,
    'quantity_deduction': fp.quantity or 0,
    'cost_saved': cost_saved,
    'fake_purchase_cost': fp.total_cost or 0  # ← 신규 추가
}
```

### 2. metrics.py - /metrics 엔드포인트 (라인 121-134)

```python
sales_deduction = adjustment.get('sales_deduction', 0)
quantity_deduction = adjustment.get('quantity_deduction', 0)
cost_saved = adjustment.get('cost_saved', 0)
fake_purchase_cost = adjustment.get('fake_purchase_cost', 0)  # ← 신규

# Apply adjustments
adjusted_sales = record.sales_amount - sales_deduction
adjusted_quantity = record.sales_quantity - quantity_deduction
adjusted_profit = record.net_profit - sales_deduction + cost_saved - fake_purchase_cost
adjusted_ad_cost = record.ad_cost + fake_purchase_cost
adjusted_total_cost = record.total_cost - cost_saved
```

### 3. metrics.py - /metrics/product-trend 엔드포인트 (라인 507-523)

동일한 로직 적용

---

## 📈 변경 이력

### 2025-11-19: 가구매 비용 반영 추가

**변경 사항**:
1. ✅ `fake_purchase_cost` 필드 추가
2. ✅ 순이익 계산 시 가구매 비용 차감
3. ✅ 광고비에 가구매 비용 포함
4. ✅ 광고비 비율 계산에 가구매 비용 반영

**Before**:
```python
adjusted_profit = net_profit - sales_deduction + cost_saved
adjusted_ad_cost = ad_cost
```

**After**:
```python
adjusted_profit = net_profit - sales_deduction + cost_saved - fake_purchase_cost
adjusted_ad_cost = ad_cost + fake_purchase_cost
```

**영향**:
- 순이익이 가구매 비용만큼 더 감소 (정확한 실제 이익 반영)
- 광고비 비율이 증가 (가구매 비용 포함)
- 대시보드 순이익 계산이 실제와 일치

---

## ⚠️ 주의사항

### 1. 가구매 비용과 비용 절감분 구분

**가구매 비용** (`fake_purchase_cost`):
- 가구매 대행 서비스에 **실제로 지불하는 비용**
- 광고비 성격
- 순이익에서 **차감**

**비용 절감분** (`cost_saved`):
- 물건을 받지 않아 **발생하지 않은 상품 원가**
- 순이익에 **더함**

### 2. 부가세 적용

- 광고비 (`ad_cost`): 부가세 10% 적용 (× 1.1)
- 가구매 비용 (`fake_purchase_cost`): 부가세 미적용
- 광고비 비율 계산 시: 전체 광고비(ad_cost + fake_purchase_cost)에 1.1 적용

### 3. 가구매 비용 계산

```python
# FakePurchase.calculate_fake_purchase_cost()
calculated_cost = (unit_price × 0.12) + 4500  # 단위당
total_cost = calculated_cost × quantity        # 총 비용
```

---

## ✅ 최종 공식 요약

### 조정 순이익
```
adjusted_profit = net_profit - sales_deduction + cost_saved - fake_purchase_cost

where:
  net_profit = sales_amount - total_cost - (ad_cost × 1.1)
  sales_deduction = 가구매_수량 × 단가
  cost_saved = 가구매_수량 × (도매가 + 수수료 + 부가세)
  fake_purchase_cost = 가구매_수량 × [(단가 × 12%) + 4,500원]
```

### 조정 광고비
```
adjusted_ad_cost = ad_cost + fake_purchase_cost
```

### 광고비 비율
```
ad_cost_rate = ((adjusted_ad_cost × 1.1) / adjusted_sales) × 100
```

---

**작성일**: 2025-11-19
**버전**: 2.0 (가구매 비용 반영)
