# -*- coding: utf-8 -*-
"""
Authentication and Multi-tenancy Models
사용자, 테넌트, 멤버십 모델
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from services.database import Base


class Tenant(Base):
    """테넌트 (쇼핑몰/조직) 모델"""
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)  # 쇼핑몰명 (예: "ABC쇼핑몰")
    slug = Column(String, unique=True, nullable=False, index=True)  # URL용 슬러그 (예: "abc-shop")

    # 플랜 정보
    plan = Column(String, default='basic')  # basic, pro, enterprise
    is_active = Column(Boolean, default=True)

    # 메타데이터
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 설정 (JSON 또는 별도 테이블로 확장 가능)
    settings = Column(String, nullable=True)  # JSON string for tenant-specific settings


class User(Base):
    """사용자 모델"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)

    # 인증 정보
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)

    # 사용자 정보
    full_name = Column(String, nullable=True)

    # 역할 (소속된 기본 테넌트에서의 역할)
    role = Column(String, default='viewer')  # owner, admin, editor, viewer

    # 상태
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)

    # 메타데이터
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    last_login = Column(DateTime, nullable=True)

    # 추가 정보
    phone = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)


class TenantMembership(Base):
    """사용자-테넌트 멤버십 (다중 테넌트 소속 지원)"""
    __tablename__ = "tenant_memberships"
    __table_args__ = (
        UniqueConstraint('user_id', 'tenant_id', name='uix_user_tenant'),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)

    # 테넌트별 역할
    role = Column(String, nullable=False)  # owner, admin, editor, viewer

    # 상태
    is_active = Column(Boolean, default=True)

    # 메타데이터
    joined_at = Column(DateTime, default=datetime.now, nullable=False)
    invited_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    invitation_accepted_at = Column(DateTime, nullable=True)
