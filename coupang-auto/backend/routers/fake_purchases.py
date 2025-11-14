# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from datetime import date, datetime

from models.schemas import (
    FakePurchaseCreate, FakePurchaseUpdate, FakePurchaseResponse,
    FakePurchaseListResponse, BatchDeleteRequest, BatchDeleteResponse
)
from models.auth import User, Tenant
from services.database import get_db, FakePurchase
from auth.dependencies import get_current_user, get_current_tenant

router = APIRouter()


@router.get("/fake-purchases", response_model=FakePurchaseListResponse)
async def get_fake_purchases(
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit number of records"),
    offset: Optional[int] = Query(0, ge=0, description="Offset for pagination"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    product_name: Optional[str] = Query(None, description="Filter by product name (partial match)"),
    option_id: Optional[int] = Query(None, description="Filter by option ID"),
    sort_by: str = Query("date", regex="^(date|created_at|updated_at|option_id|product_name|quantity)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    가구매 목록 조회 with optional filtering and pagination

    Returns:
        - fake_purchases: List of fake purchase records
        - count: Number of records returned
        - total: Total records matching filters
    """
    # Build base query - filter by tenant
    query = db.query(FakePurchase).filter(FakePurchase.tenant_id == current_tenant.id)

    # Apply filters
    if start_date:
        query = query.filter(FakePurchase.date >= start_date)

    if end_date:
        query = query.filter(FakePurchase.date <= end_date)

    if product_name:
        query = query.filter(FakePurchase.product_name.like(f"%{product_name}%"))

    if option_id:
        query = query.filter(FakePurchase.option_id == option_id)

    # Get total count before pagination
    total = query.count()

    # Apply sorting
    sort_column = getattr(FakePurchase, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Apply pagination
    if limit:
        query = query.offset(offset).limit(limit)

    fake_purchases = query.all()

    return FakePurchaseListResponse(
        fake_purchases=fake_purchases,
        count=len(fake_purchases),
        total=total
    )


@router.post("/fake-purchases", response_model=FakePurchaseResponse, status_code=201)
async def create_fake_purchase(
    fake_purchase: FakePurchaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    가구매 레코드 생성

    Validates:
        - option_id, date combination is unique for tenant
        - quantity is non-negative
    """
    # Check if record already exists for this tenant, option_id, and date
    existing = db.query(FakePurchase).filter(
        and_(
            FakePurchase.tenant_id == current_tenant.id,
            FakePurchase.option_id == fake_purchase.option_id,
            FakePurchase.date == fake_purchase.date
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Fake purchase record already exists for option_id {fake_purchase.option_id} on {fake_purchase.date}"
        )

    try:
        # Auto-fill product_name and option_name from integrated_records if not provided
        product_name = fake_purchase.product_name
        option_name = fake_purchase.option_name

        if not product_name or not option_name:
            # Query integrated_records to get product info
            integrated_record = db.query(IntegratedRecord).filter(
                and_(
                    IntegratedRecord.tenant_id == current_tenant.id,
                    IntegratedRecord.option_id == fake_purchase.option_id
                )
            ).first()

            if integrated_record:
                if not product_name:
                    product_name = integrated_record.product_name
                if not option_name:
                    option_name = integrated_record.option_name
            elif not product_name:
                # If no integrated record found and product_name not provided, raise error
                raise HTTPException(
                    status_code=400,
                    detail=f"Option ID {fake_purchase.option_id}에 대한 상품 정보를 찾을 수 없습니다. 상품명을 직접 입력해주세요."
                )

        # Create new record
        new_fake_purchase = FakePurchase(
            tenant_id=current_tenant.id,
            option_id=fake_purchase.option_id,
            product_name=product_name,
            option_name=option_name,
            date=fake_purchase.date,
            quantity=fake_purchase.quantity,
            unit_price=fake_purchase.unit_price,
            notes=fake_purchase.notes,
            created_by=current_user.id
        )

        # Calculate costs
        new_fake_purchase.calculate_fake_purchase_cost()

        db.add(new_fake_purchase)
        db.commit()
        db.refresh(new_fake_purchase)

        return new_fake_purchase

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create fake purchase record: {str(e)}"
        )


@router.get("/fake-purchases/{fake_purchase_id}", response_model=FakePurchaseResponse)
async def get_fake_purchase(
    fake_purchase_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    가구매 레코드 단건 조회
    """
    fake_purchase = db.query(FakePurchase).filter(
        and_(
            FakePurchase.id == fake_purchase_id,
            FakePurchase.tenant_id == current_tenant.id
        )
    ).first()

    if not fake_purchase:
        raise HTTPException(
            status_code=404,
            detail=f"Fake purchase record not found: {fake_purchase_id}"
        )

    return fake_purchase


@router.put("/fake-purchases/{fake_purchase_id}", response_model=FakePurchaseResponse)
async def update_fake_purchase(
    fake_purchase_id: int,
    fake_purchase_update: FakePurchaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    가구매 레코드 수정

    Only provided fields will be updated (partial update)
    """
    # Find existing record
    fake_purchase = db.query(FakePurchase).filter(
        and_(
            FakePurchase.id == fake_purchase_id,
            FakePurchase.tenant_id == current_tenant.id
        )
    ).first()

    if not fake_purchase:
        raise HTTPException(
            status_code=404,
            detail=f"Fake purchase record not found: {fake_purchase_id}"
        )

    try:
        # Update provided fields
        update_data = fake_purchase_update.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(fake_purchase, field, value)

        # Recalculate costs
        fake_purchase.calculate_fake_purchase_cost()

        # Update timestamp
        fake_purchase.updated_at = datetime.now()

        db.commit()
        db.refresh(fake_purchase)

        return fake_purchase

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update fake purchase record: {str(e)}"
        )


@router.delete("/fake-purchases/{fake_purchase_id}")
async def delete_fake_purchase(
    fake_purchase_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    가구매 레코드 삭제
    """
    fake_purchase = db.query(FakePurchase).filter(
        and_(
            FakePurchase.id == fake_purchase_id,
            FakePurchase.tenant_id == current_tenant.id
        )
    ).first()

    if not fake_purchase:
        raise HTTPException(
            status_code=404,
            detail=f"Fake purchase record not found: {fake_purchase_id}"
        )

    try:
        db.delete(fake_purchase)
        db.commit()

        return {
            "message": "Fake purchase record deleted successfully",
            "deleted_id": fake_purchase_id
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete fake purchase record: {str(e)}"
        )


@router.post("/fake-purchases/batch-delete", response_model=BatchDeleteResponse)
async def batch_delete_fake_purchases(
    request: BatchDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    가구매 레코드 일괄 삭제
    """
    try:
        # Query records to delete (ensure tenant ownership)
        records_to_delete = db.query(FakePurchase).filter(
            and_(
                FakePurchase.id.in_(request.ids),
                FakePurchase.tenant_id == current_tenant.id
            )
        ).all()

        deleted_count = len(records_to_delete)

        if deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail="No fake purchase records found with provided IDs"
            )

        # Delete records
        for record in records_to_delete:
            db.delete(record)

        db.commit()

        return BatchDeleteResponse(
            message=f"Successfully deleted {deleted_count} fake purchase records",
            deleted_count=deleted_count
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to batch delete fake purchase records: {str(e)}"
        )


@router.get("/fake-purchases/summary/stats")
async def get_fake_purchase_summary(
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    가구매 통계 요약

    Returns:
        - total_fake_purchases: Total quantity
        - total_cost: Total cost
        - unique_products: Number of unique products
        - date_range: Date range covered
    """
    query = db.query(FakePurchase).filter(FakePurchase.tenant_id == current_tenant.id)

    if start_date:
        query = query.filter(FakePurchase.date >= start_date)

    if end_date:
        query = query.filter(FakePurchase.date <= end_date)

    records = query.all()

    if not records:
        return {
            "total_fake_purchases": 0,
            "total_cost": 0.0,
            "unique_products": 0,
            "date_range": None
        }

    total_quantity = sum(r.quantity for r in records)
    total_cost = sum(r.total_cost for r in records)
    unique_products = len(set(r.option_id for r in records))
    dates = [r.date for r in records]

    return {
        "total_fake_purchases": total_quantity,
        "total_cost": total_cost,
        "unique_products": unique_products,
        "date_range": {
            "start": min(dates),
            "end": max(dates)
        }
    }
