# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field


# Sales Record Schemas
class SalesRecordBase(BaseModel):
    date: date
    store: str
    product_name: str
    quantity: int = Field(ge=0)
    sale_price: float = Field(ge=0)
    cost_price: float = Field(default=0.0, ge=0)
    shipping_cost: float = Field(default=0.0, ge=0)


class SalesRecordCreate(SalesRecordBase):
    pass


class SalesRecordResponse(SalesRecordBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Ad Record Schemas
class AdRecordBase(BaseModel):
    date: date
    store: str
    product_name: str
    impressions: int = Field(default=0, ge=0)
    clicks: int = Field(default=0, ge=0)
    conversions: int = Field(default=0, ge=0)
    ad_cost: float = Field(default=0.0, ge=0)


class AdRecordCreate(AdRecordBase):
    pass


class AdRecordResponse(AdRecordBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Product Master Schemas
class ProductMasterBase(BaseModel):
    product_code: str
    product_name: str
    cost_price: float = Field(default=0.0, ge=0)
    commission_rate: Optional[float] = Field(default=None, ge=0, le=100)
    exchange_rate: Optional[float] = Field(default=None, ge=0)


class ProductMasterCreate(ProductMasterBase):
    pass


class ProductMasterResponse(ProductMasterBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Upload Response
class UploadResponse(BaseModel):
    status: str = Field(description="success or error")
    message: str
    records: int = Field(default=0, ge=0)
    errors: List[str] = Field(default_factory=list)


# Integrated Upload Response
class IntegratedUploadResponse(BaseModel):
    status: str = Field(description="success or error")
    message: str
    total_records: int = Field(default=0, ge=0)
    matched_with_ads: int = Field(default=0, ge=0)
    matched_with_margin: int = Field(default=0, ge=0)
    fully_integrated: int = Field(default=0, ge=0)
    warnings: List[str] = Field(default_factory=list)


# Metrics Schemas
class DailyMetric(BaseModel):
    date: date
    total_sales: float
    total_profit: float
    ad_cost: float
    total_quantity: int
    margin_rate: float


class ProductMetric(BaseModel):
    option_id: int
    option_name: str
    product_name: str
    total_sales: float
    total_profit: float
    total_quantity: int
    total_ad_cost: float
    margin_rate: float
    cost_rate: float
    ad_cost_rate: float


class MetricsResponse(BaseModel):
    period: str
    total_sales: float
    total_profit: float
    total_ad_cost: float
    total_quantity: int
    avg_margin_rate: float
    daily_trend: List[DailyMetric]
    by_product: List[ProductMetric]


class SummaryResponse(BaseModel):
    total_sales: float
    total_profit: float
    total_ad_cost: float
    avg_margin_rate: float
    total_quantity: int
    unique_products: int
    date_range: str


# Report Request Schemas
class WeeklyReportRequest(BaseModel):
    start_date: date
    end_date: date
    store: Optional[str] = None


class MonthlyReportRequest(BaseModel):
    year: int = Field(ge=2020, le=2100)
    month: int = Field(ge=1, le=12)
    store: Optional[str] = None


# Product Margin Schemas
class MarginBase(BaseModel):
    """Base schema for margin data

    Required fields for accurate profit calculation:
    - cost_price: Cost per unit (필수)
    - fee_amount: Total fee amount (필수)
    - vat: VAT amount (필수)
    """
    option_id: int = Field(..., description="Product option ID")
    product_name: str = Field(..., min_length=1, description="Product name")
    option_name: Optional[str] = Field(None, description="Option name")
    cost_price: float = Field(..., gt=0, description="Cost price (도매가) - REQUIRED for profit calculation")
    selling_price: float = Field(default=0.0, ge=0, description="Selling price (판매가)")
    margin_rate: float = Field(default=0.0, description="Margin rate % (마진율)")
    fee_rate: float = Field(default=0.0, ge=0, le=100, description="Fee rate % (총 수수료%)")
    fee_amount: float = Field(..., ge=0, description="Fee amount (총 수수료원) - REQUIRED for profit calculation")
    vat: float = Field(..., ge=0, description="VAT (부가세) - REQUIRED for profit calculation")
    notes: Optional[str] = Field(None, max_length=500, description="Notes")


class MarginCreate(MarginBase):
    """Schema for creating new margin record"""
    pass


class MarginUpdate(BaseModel):
    """Schema for updating margin record (all fields optional)"""
    product_name: Optional[str] = Field(None, min_length=1)
    option_name: Optional[str] = None
    cost_price: Optional[float] = Field(None, ge=0)
    selling_price: Optional[float] = Field(None, ge=0)
    margin_rate: Optional[float] = None
    fee_rate: Optional[float] = Field(None, ge=0, le=100)
    fee_amount: Optional[float] = Field(None, ge=0)
    vat: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=500)


class MarginResponse(MarginBase):
    """Schema for margin record response"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MarginListResponse(BaseModel):
    """Schema for list of margins with metadata"""
    margins: List[MarginResponse]
    count: int
    total: int = Field(description="Total records in database")


class UnmatchedProduct(BaseModel):
    """Schema for products without margin data"""
    option_id: int
    product_name: str
    option_name: Optional[str]
    sales_amount: float
    sales_quantity: int


class UnmatchedProductsResponse(BaseModel):
    """Schema for unmatched products list"""
    unmatched_products: List[UnmatchedProduct]
    count: int


# Batch Delete Request
class BatchDeleteRequest(BaseModel):
    """Schema for batch delete request"""
    ids: List[int] = Field(..., min_items=1, description="List of record IDs to delete")


class BatchDeleteResponse(BaseModel):
    """Schema for batch delete response"""
    message: str
    deleted_count: int


# Fake Purchase Schemas

class FakePurchaseBase(BaseModel):
    """Base schema for fake purchase data"""
    option_id: int
    product_name: Optional[str] = None  # 자동으로 채워질 수 있음
    option_name: Optional[str] = None
    date: date
    quantity: int = Field(ge=0)
    unit_price: float = Field(default=0.0, ge=0)
    notes: Optional[str] = None


class FakePurchaseCreate(FakePurchaseBase):
    """Schema for creating new fake purchase record"""
    pass


class FakePurchaseUpdate(BaseModel):
    """Schema for updating fake purchase record (all fields optional)"""
    quantity: Optional[int] = Field(None, ge=0)
    unit_price: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None


class FakePurchaseResponse(FakePurchaseBase):
    """Schema for fake purchase record response"""
    id: int
    calculated_cost: float = Field(description="Calculated cost per unit: (price × 12%) + 4500")
    total_cost: float = Field(description="Total cost: calculated_cost × quantity")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FakePurchaseListResponse(BaseModel):
    """Schema for list of fake purchases with metadata"""
    fake_purchases: List[FakePurchaseResponse]
    count: int
    total: int = Field(description="Total records in database")


class FakePurchaseAdjustment(BaseModel):
    """Schema for metrics adjustment due to fake purchases"""
    total_fake_purchases: int = Field(description="Total number of fake purchases")
    sales_deduction: float = Field(description="Sales amount deducted")
    ad_cost_addition: float = Field(description="Ad cost added (fake purchase costs)")
    adjusted_total_sales: float = Field(description="Adjusted total sales")
    adjusted_total_profit: float = Field(description="Adjusted net profit")
    adjusted_total_ad_cost: float = Field(description="Adjusted ad cost")
