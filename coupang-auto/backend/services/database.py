# -*- coding: utf-8 -*-
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, Boolean, BigInteger, Index, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Database URL setup
# 환경변수에서 DATABASE_URL을 가져오거나, 로컬에서는 SQLite 사용
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    # 로컬 개발 환경: SQLite 사용
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(DB_PATH, exist_ok=True)
    DATABASE_URL = f"sqlite:///{os.path.join(DB_PATH, 'coupang_integrated.db')}"

    # SQLAlchemy engine (SQLite)
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=True
    )
else:
    # 프로덕션 환경: PostgreSQL 사용
    # Render/Supabase에서 제공하는 DATABASE_URL 사용

    # psycopg3 드라이버 사용 (psycopg2 대신)
    # postgresql:// -> postgresql+psycopg://
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
    elif DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)

    # Disable prepared statements to avoid "prepared statement already exists" error
    # This can happen with connection pooling in production environments
    if "?" in DATABASE_URL:
        DATABASE_URL += "&prepared=false"
    else:
        DATABASE_URL += "?prepared=false"

    # SQLAlchemy engine (PostgreSQL)
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # 연결 확인
        pool_size=5,
        max_overflow=10,
        echo=True,
        pool_recycle=3600,  # Recycle connections after 1 hour to avoid stale connections
        connect_args={
            "prepare_threshold": 0,  # Disable prepared statements (psycopg3 option)
            "autocommit": False  # Explicit autocommit setting
        }
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Integrated Table Model

class IntegratedRecord(Base):
    """Integrated sales, ads, and margin data"""
    __tablename__ = "integrated_records"
    __table_args__ = (
        Index('idx_tenant_option_date', 'tenant_id', 'option_id', 'date'),
        UniqueConstraint('tenant_id', 'option_id', 'date', name='uix_tenant_option_date'),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=True, index=True)  # Nullable for migration
    option_id = Column(BigInteger, nullable=False, index=True)

    # Basic info
    option_name = Column(String)
    product_name = Column(String, nullable=False, index=True)
    date = Column(Date, index=True)  # Data date

    # Sales data
    sales_amount = Column(Float, default=0.0)  # Daily sales revenue
    sales_quantity = Column(Integer, default=0)  # Daily quantity
    order_count = Column(Integer, default=0)  # Daily orders
    total_sales = Column(Float, default=0.0)  # Total accumulated sales
    total_sales_quantity = Column(Integer, default=0)  # Total accumulated quantity

    # Advertising data
    ad_cost = Column(Float, default=0.0)  # Ad spend
    impressions = Column(Integer, default=0)  # Ad impressions
    clicks = Column(Integer, default=0)  # Ad clicks
    ad_sales_quantity = Column(Integer, default=0)  # Sales from ads
    conversion_sales = Column(Float, default=0.0)  # 총 전환 매출액 (1일)(원)

    # Margin data (per unit)
    cost_price = Column(Float, default=0.0)  # Cost per unit (Korean cost)
    selling_price = Column(Float, default=0.0)  # Selling price
    margin_amount = Column(Float, default=0.0)  # Margin per unit
    margin_rate = Column(Float, default=0.0)  # Margin rate (%)
    fee_rate = Column(Float, default=0.0)  # Total fee rate (%)
    fee_amount = Column(Float, default=0.0)  # Total fee amount (per unit)
    vat = Column(Float, default=0.0)  # VAT (per unit)

    # Calculated fields (auto-calculated)
    total_cost = Column(Float, default=0.0)  # (cost_price + fee_amount + vat) × sales_quantity
    net_profit = Column(Float, default=0.0)  # sales_amount - total_cost - ad_cost
    actual_margin_rate = Column(Float, default=0.0)  # net_profit / sales_amount × 100
    cost_rate = Column(Float, default=0.0)  # total_cost / sales_amount × 100 (마진율)
    ad_cost_rate = Column(Float, default=0.0)  # (ad_cost × 1.1) / sales_amount × 100 (광고비율)
    roas = Column(Float, default=0.0)  # sales_amount / ad_cost

    # Metadata
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def calculate_metrics(self):
        """Calculate derived metrics

        Formula:
        - Unit cost = Korean cost + Total fee (per unit) + VAT (per unit)
        - Total cost = Unit cost × Sales quantity
        - Net profit = Sales amount - Total cost - Ad cost × 1.1 (광고비 + 부가세)
        - Actual margin rate = (Net profit / Sales amount) × 100
        - ROAS = Sales amount / Ad cost
        """
        # Unit cost per item
        unit_cost = (self.cost_price or 0) + (self.fee_amount or 0) + (self.vat or 0)

        # Total cost for all sold items
        self.total_cost = unit_cost * self.sales_quantity if self.sales_quantity else 0

        # Net profit after all costs (광고비는 부가세 포함하여 1.1 곱함)
        self.net_profit = self.sales_amount - self.total_cost - (self.ad_cost or 0) * 1.1

        # Actual margin rate (%) - 이윤율
        if self.sales_amount > 0:
            self.actual_margin_rate = (self.net_profit / self.sales_amount) * 100
        else:
            self.actual_margin_rate = 0

        # Cost rate (%) - 마진율 = (매출 - 총원가) / 매출액 × 100
        if self.sales_amount > 0:
            self.cost_rate = ((self.sales_amount - self.total_cost) / self.sales_amount) * 100
        else:
            self.cost_rate = 0

        # Ad cost rate (%) - 광고비율 = (광고비 × 1.1) / 매출액 × 100
        if self.sales_amount > 0:
            self.ad_cost_rate = ((self.ad_cost or 0) * 1.1 / self.sales_amount) * 100
        else:
            self.ad_cost_rate = 0

        # ROAS (Return on Ad Spend) - (전환 매출액 / 광고비) × 100
        if self.ad_cost and self.ad_cost > 0:
            self.roas = (self.conversion_sales / self.ad_cost) * 100
        else:
            self.roas = 0


# Product Margin Model

class ProductMargin(Base):
    """Product margin master data"""
    __tablename__ = "product_margins"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'option_id', name='uix_tenant_option'),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=True, index=True)  # Nullable for migration
    option_id = Column(BigInteger, nullable=False, index=True)
    product_name = Column(String, nullable=False, index=True)
    option_name = Column(String)

    # Margin data
    cost_price = Column(Float, default=0.0)  # 도매가
    selling_price = Column(Float, default=0.0)  # 판매가
    margin_amount = Column(Float, default=0.0)  # 판매마진 (DEPRECATED - not used in calculations)
    margin_rate = Column(Float, default=0.0)  # 마진율(%)
    fee_rate = Column(Float, default=0.0)  # 총 수수료(%)
    fee_amount = Column(Float, default=0.0)  # 총 수수료(원)
    vat = Column(Float, default=0.0)  # 부가세

    # Metadata
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    notes = Column(String)  # User notes


# Upload History Model

class UploadHistory(Base):
    """Track file upload history"""
    __tablename__ = "upload_history"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=True, index=True)  # Nullable for migration
    uploaded_at = Column(DateTime, default=datetime.now, nullable=False, index=True)

    # File information
    sales_filename = Column(String, nullable=False)
    ads_filename = Column(String, nullable=False)
    margin_filename = Column(String, nullable=False)
    data_date = Column(Date)  # The date the data represents

    # Integration results
    total_records = Column(Integer, default=0)
    matched_with_ads = Column(Integer, default=0)
    matched_with_margin = Column(Integer, default=0)
    fully_integrated = Column(Integer, default=0)

    # Status
    status = Column(String, default='success')  # 'success' or 'error'
    error_message = Column(String, nullable=True)


# Fake Purchase Model

class FakePurchase(Base):
    """가구매 관리 테이블 - 가짜 구매 데이터 추적"""
    __tablename__ = "fake_purchases"
    __table_args__ = (
        Index('idx_fake_tenant_option_date', 'tenant_id', 'option_id', 'date'),
        UniqueConstraint('tenant_id', 'option_id', 'date', name='uix_fake_tenant_option_date'),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)

    # 상품 정보
    option_id = Column(BigInteger, nullable=False, index=True)
    product_name = Column(String, nullable=False, index=True)
    option_name = Column(String, nullable=True)
    date = Column(Date, nullable=False, index=True)

    # 가구매 정보
    quantity = Column(Integer, nullable=False, default=0)  # 가구매 개수
    unit_price = Column(Float, nullable=True, default=0.0)  # 상품 단가 (참고용)

    # 계산된 비용
    # 가구매 비용 = (상품가격 × 20.5%) + 4500원
    calculated_cost = Column(Float, nullable=True, default=0.0)  # 단위당 가구매 비용
    total_cost = Column(Float, nullable=True, default=0.0)  # 총 가구매 비용 (calculated_cost × quantity)

    # 메모
    notes = Column(String, nullable=True)

    # 메타데이터
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)

    def calculate_fake_purchase_cost(self):
        """가구매 비용 계산

        Formula:
        - 단위당 비용 = (상품가격 × 12%) + 4500원
        - 총 비용 = 단위당 비용 × 가구매 개수
        """
        if self.unit_price and self.quantity:
            # 수수료 12% + 고정비용 4500원
            self.calculated_cost = (self.unit_price * 0.12) + 4500
            self.total_cost = self.calculated_cost * self.quantity
        else:
            self.calculated_cost = 0
            self.total_cost = 0


# Backup: Keep old tables for reference (optional)

class SalesRecord(Base):
    """Legacy sales records table"""
    __tablename__ = "sales_records_legacy"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    store = Column(String, nullable=False, index=True)
    product_name = Column(String, nullable=False)

    quantity = Column(Integer, default=0)
    sale_price = Column(Float, default=0.0)
    cost_price = Column(Float, default=0.0)
    shipping_cost = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.now)


class AdRecord(Base):
    """Legacy ad records table"""
    __tablename__ = "ad_records_legacy"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    store = Column(String, nullable=False, index=True)
    product_name = Column(String, nullable=False)

    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    ad_cost = Column(Float, default=0.0)
    conversion_sales = Column(Float, default=0.0)  # 총 전환 매출액 (1일)(원)

    created_at = Column(DateTime, default=datetime.now)


class ProductMaster(Base):
    """Legacy product master table"""
    __tablename__ = "product_master_legacy"

    id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String, unique=True, nullable=False, index=True)
    product_name = Column(String, nullable=False)

    cost_price = Column(Float, default=0.0)
    commission_rate = Column(Float, default=0.10)
    exchange_rate = Column(Float, default=1.0)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# Database initialization

async def init_db():
    """Create database tables"""
    print("=" * 50)
    print("Starting database initialization...")
    print(f"Database URL: {DATABASE_URL[:50]}...")  # 앞부분만 출력 (보안)

    # Import all models to register them with Base.metadata
    from models.auth import User, Tenant, TenantMembership
    from models.audit import AuditLog

    print(f"Registered tables: {list(Base.metadata.tables.keys())}")
    print("Creating tables...")

    try:
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully!")
        print("=" * 50)
    except Exception as e:
        print(f"Error creating tables: {e}")
        print("=" * 50)
        raise


async def close_db():
    """Close database connection"""
    engine.dispose()


def get_db():
    """Get database session (FastAPI Dependency)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session():
    """Get session for regular functions"""
    return SessionLocal()
