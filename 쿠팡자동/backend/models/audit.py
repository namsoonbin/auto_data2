# -*- coding: utf-8 -*-
"""
Audit Log Model
감사 로그 모델 - 중요 작업 추적
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime

from services.database import Base


class AuditLog(Base):
    """감사 로그 - 중요 작업 추적"""
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index('idx_audit_tenant_user', 'tenant_id', 'user_id'),
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_action', 'action'),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)

    # 작업 정보
    action = Column(String, nullable=False)  # upload_sales, delete_data, export_report, etc.
    resource_type = Column(String, nullable=True)  # sales_record, margin, user, etc.
    resource_id = Column(String, nullable=True)  # ID of the affected resource

    # 상세 정보
    description = Column(String, nullable=True)  # Human-readable description
    additional_data = Column(String, nullable=True)  # JSON string with additional details

    # 요청 정보
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    # 결과
    status = Column(String, default='success')  # success, failure, partial
    error_message = Column(String, nullable=True)

    # 타임스탬프
    timestamp = Column(DateTime, default=datetime.now, nullable=False, index=True)
