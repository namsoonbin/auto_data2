# -*- coding: utf-8 -*-
"""
가구매 조정 서비스

가구매(Fake Purchase) 데이터를 기반으로 실제 매출 및 비용 조정을 처리하는 서비스
"""
from typing import Dict, List, Optional, Tuple
from datetime import date
from uuid import UUID
import logging

from sqlalchemy.orm import Session
from services.database import IntegratedRecord, FakePurchase

logger = logging.getLogger(__name__)


def build_fake_purchase_adjustments(
    db: Session,
    tenant_id: UUID,
    records: List[IntegratedRecord],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    product: Optional[str] = None,
    option_id: Optional[int] = None,
    include_adjustment: bool = False,
    exact_match: bool = False
) -> Tuple[Dict[Tuple[date, int], Tuple[float, float, float]], Dict[Tuple[date, int], Dict[str, float]]]:
    """
    가구매 조정 정보 생성

    Args:
        db: Database session
        tenant_id: 테넌트 ID
        records: IntegratedRecord 레코드 리스트
        start_date: 시작 날짜 필터
        end_date: 종료 날짜 필터
        product: 상품명 필터 (부분 일치 또는 정확히 일치)
        option_id: 옵션 ID 필터
        include_adjustment: 가구매 조정 포함 여부
        exact_match: True이면 product를 정확히 일치, False이면 부분 일치 (LIKE)

    Returns:
        Tuple of:
        - unit_cost_map: {(date, option_id): (cost_price, fee_amount, vat)}
        - fake_purchase_adjustments: {(date, option_id): {
            'sales_deduction': float,
            'quantity_deduction': int,
            'cost_saved': float
          }}

    Logic:
        1. IntegratedRecord에서 단위당 비용 정보 추출 (도매가, 수수료, 부가세)
        2. 가구매 데이터 조회 (조건에 맞게 필터링)
        3. 각 가구매 건에 대해:
           - sales_deduction: 가구매 수량 × 단가 (매출 차감분)
           - quantity_deduction: 가구매 수량 (수량 차감분)
           - cost_saved: 가구매 수량 × (도매가 + 수수료 + 부가세)
             → 가구매는 실제로 비용이 발생하지 않았으므로 절감된 비용
    """
    # IntegratedRecord에서 단위당 비용 정보를 미리 조회
    unit_cost_map = {}  # {(date, option_id): (cost_price, fee_amount, vat)}

    for record in records:
        key = (record.date, record.option_id)
        new_value = (record.cost_price or 0, record.fee_amount or 0, record.vat or 0)

        # 중복 감지 및 로깅
        if key in unit_cost_map:
            logger.warning(
                f"중복 레코드 발견: date={record.date}, option_id={record.option_id}, "
                f"tenant_id={record.tenant_id}, 기존 비용={unit_cost_map[key]}, 새 비용={new_value}"
            )

        unit_cost_map[key] = new_value

    # 가구매 조정 정보 초기화
    fake_purchase_adjustments = {}  # {(date, option_id): {sales_deduction, quantity_deduction, cost_saved}}

    if not include_adjustment:
        return unit_cost_map, fake_purchase_adjustments

    # Query fake purchases for the same date range
    fake_query = db.query(FakePurchase).filter(FakePurchase.tenant_id == tenant_id)

    if start_date:
        fake_query = fake_query.filter(FakePurchase.date >= start_date)
    if end_date:
        fake_query = fake_query.filter(FakePurchase.date <= end_date)
    if product:
        if exact_match:
            fake_query = fake_query.filter(FakePurchase.product_name == product)
        else:
            fake_query = fake_query.filter(FakePurchase.product_name.like(f"%{product}%"))
    if option_id:
        fake_query = fake_query.filter(FakePurchase.option_id == option_id)

    fake_purchases = fake_query.all()

    # Build adjustments dictionary
    for fp in fake_purchases:
        key = (fp.date, fp.option_id)

        # Calculate sales deduction (quantity × unit_price)
        sales_deduction = (fp.quantity or 0) * (fp.unit_price or 0)

        # Calculate cost saved (가구매는 실제로 비용이 발생하지 않았으므로)
        # 비용 절감 = 가구매 수량 × (도매가 + 수수료 + 부가세)
        cost_saved = 0
        if key in unit_cost_map:
            cost_price, fee_amount, vat = unit_cost_map[key]
            unit_cost = cost_price + fee_amount + vat
            cost_saved = (fp.quantity or 0) * unit_cost
        else:
            # 가구매가 존재하지 않는 IntegratedRecord를 참조
            logger.warning(
                f"FakePurchase가 존재하지 않는 레코드 참조: date={fp.date}, "
                f"option_id={fp.option_id}, product_name={fp.product_name}"
            )

        fake_purchase_adjustments[key] = {
            'sales_deduction': sales_deduction,
            'quantity_deduction': fp.quantity or 0,
            'cost_saved': cost_saved  # 실제로 지불하지 않은 비용 (이익에 더해져야 함)
        }

    return unit_cost_map, fake_purchase_adjustments


def apply_fake_purchase_adjustment(
    net_profit: float,
    total_cost: float,
    adjustment: Dict[str, float]
) -> Tuple[float, float]:
    """
    단일 레코드에 가구매 조정 적용

    Args:
        net_profit: 원래 순이익
        total_cost: 원래 총 비용
        adjustment: 가구매 조정 정보 {sales_deduction, quantity_deduction, cost_saved}

    Returns:
        Tuple of (adjusted_profit, adjusted_total_cost)

    Logic:
        - adjusted_profit = net_profit - sales_deduction + cost_saved
          → 매출 감소분 차감, 비용 절감분 추가
        - adjusted_total_cost = total_cost - cost_saved
          → 실제로 지불하지 않은 비용 제외
    """
    sales_deduction = adjustment.get('sales_deduction', 0)
    cost_saved = adjustment.get('cost_saved', 0)

    # 순이익 조정:
    # - 매출 감소: 가구매로 인한 허위 매출 차감
    # + 비용 절감: 실제로 물건을 받지 않았으므로 cost_saved 만큼 이익 증가
    adjusted_profit = net_profit - sales_deduction + cost_saved

    # 총 비용 조정: 실제로 지불하지 않은 비용 제외
    adjusted_total_cost = total_cost - cost_saved

    return adjusted_profit, adjusted_total_cost
