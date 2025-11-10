# -*- coding: utf-8 -*-
"""
인증 관련 Pydantic 스키마
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class TenantCreate(BaseModel):
    """테넌트 생성 스키마"""
    name: str = Field(..., description="쇼핑몰/조직 이름")
    slug: str = Field(..., description="URL 슬러그 (영문소문자, 숫자, 하이픈만 가능)")


class UserRegister(BaseModel):
    """회원가입 스키마"""
    email: EmailStr = Field(..., description="이메일 주소")
    password: str = Field(..., min_length=8, description="비밀번호 (최소 8자)")
    full_name: Optional[str] = Field(None, description="사용자 이름")
    tenant_name: str = Field(..., description="쇼핑몰/조직 이름")
    tenant_slug: str = Field(..., description="URL 슬러그")


class UserLogin(BaseModel):
    """로그인 스키마"""
    email: EmailStr = Field(..., description="이메일 주소")
    password: str = Field(..., description="비밀번호")


class TokenResponse(BaseModel):
    """토큰 응답 스키마"""
    access_token: str = Field(..., description="액세스 토큰")
    refresh_token: str = Field(..., description="리프레시 토큰")
    token_type: str = Field(default="bearer", description="토큰 타입")


class TokenRefresh(BaseModel):
    """토큰 갱신 스키마"""
    refresh_token: str = Field(..., description="리프레시 토큰")


class UserResponse(BaseModel):
    """사용자 응답 스키마"""
    id: str
    email: str
    full_name: Optional[str]
    role: str
    tenant_id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TenantResponse(BaseModel):
    """테넌트 응답 스키마"""
    id: str
    name: str
    slug: str
    plan: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    """프로필 수정 스키마"""
    full_name: Optional[str] = Field(None, description="사용자 이름")
    phone: Optional[str] = Field(None, description="전화번호")


class PasswordChange(BaseModel):
    """비밀번호 변경 스키마"""
    old_password: str = Field(..., description="현재 비밀번호")
    new_password: str = Field(..., min_length=8, description="새 비밀번호 (최소 8자)")


class ProfileResponse(BaseModel):
    """프로필 응답 스키마"""
    id: str
    email: str
    full_name: Optional[str]
    phone: Optional[str]
    role: str
    tenant_id: str
    is_active: bool
    email_verified: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class TenantUpdate(BaseModel):
    """테넌트 수정 스키마"""
    name: str = Field(..., description="쇼핑몰/조직 이름")
    # slug는 변경 불가 (URL에 영향을 주므로)


class AccountDelete(BaseModel):
    """계정 삭제 스키마"""
    password: str = Field(..., description="비밀번호 확인")
