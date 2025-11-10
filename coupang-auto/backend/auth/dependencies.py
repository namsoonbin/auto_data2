# -*- coding: utf-8 -*-
"""
FastAPI 인증 의존성 함수들
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import uuid

from services.database import get_db
from models.auth import User, Tenant
from auth.jwt import verify_token

# HTTP Bearer 토큰 스킴
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    현재 인증된 사용자 가져오기

    Args:
        credentials: HTTP Bearer 토큰
        db: 데이터베이스 세션

    Returns:
        User 객체

    Raises:
        HTTPException: 인증 실패 시
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 자격 증명을 확인할 수 없습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 토큰 검증
    token = credentials.credentials
    payload = verify_token(token, token_type="access")

    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # 문자열 user_id를 UUID로 변환
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise credentials_exception

    # 사용자 조회
    user = db.query(User).filter(User.id == user_uuid).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자입니다"
        )

    return user


async def get_current_tenant(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Tenant:
    """
    현재 사용자의 테넌트 가져오기

    Args:
        current_user: 현재 인증된 사용자
        db: 데이터베이스 세션

    Returns:
        Tenant 객체

    Raises:
        HTTPException: 테넌트를 찾을 수 없을 때
    """
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()

    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="테넌트를 찾을 수 없습니다"
        )

    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 테넌트입니다"
        )

    return tenant


def check_role(allowed_roles: list[str]):
    """
    역할 기반 접근 제어 (RBAC)

    Args:
        allowed_roles: 허용된 역할 목록 (예: ["owner", "admin"])

    Returns:
        의존성 함수
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"권한이 부족합니다. 필요한 역할: {', '.join(allowed_roles)}"
            )
        return current_user

    return role_checker


# 역할별 의존성
require_owner = check_role(["owner"])
require_admin = check_role(["owner", "admin"])
require_editor = check_role(["owner", "admin", "editor"])
