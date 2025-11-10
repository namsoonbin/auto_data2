# -*- coding: utf-8 -*-
"""
팀 관리 관련 Pydantic 스키마
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class TeamMemberResponse(BaseModel):
    """팀원 정보 응답 스키마"""
    id: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class TeamMemberInvite(BaseModel):
    """팀원 초대 스키마"""
    email: EmailStr = Field(..., description="초대할 사용자 이메일")
    full_name: str = Field(..., description="사용자 이름")
    role: str = Field(default="member", description="역할 (admin, member)")
    password: str = Field(..., min_length=8, description="초기 비밀번호 (최소 8자)")


class TeamMemberRoleUpdate(BaseModel):
    """팀원 역할 변경 스키마"""
    role: str = Field(..., description="변경할 역할 (owner, admin, member)")


class TeamMembersListResponse(BaseModel):
    """팀원 목록 응답 스키마"""
    members: list[TeamMemberResponse]
    total: int
