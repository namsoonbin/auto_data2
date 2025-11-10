# -*- coding: utf-8 -*-
"""
JWT Token 생성 및 검증
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import os

# JWT 설정
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-please-change-in-production-12345678")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Access Token 생성

    Args:
        data: 토큰에 포함할 데이터 (user_id, tenant_id 등)
        expires_delta: 만료 시간 (기본값: 30분)

    Returns:
        JWT 토큰 문자열
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Refresh Token 생성

    Args:
        data: 토큰에 포함할 데이터 (user_id만 포함)
        expires_delta: 만료 시간 (기본값: 7일)

    Returns:
        JWT 토큰 문자열
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """
    JWT 토큰 검증

    Args:
        token: JWT 토큰 문자열
        token_type: 토큰 타입 ("access" 또는 "refresh")

    Returns:
        토큰이 유효하면 payload 딕셔너리, 그렇지 않으면 None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # 토큰 타입 확인
        if payload.get("type") != token_type:
            return None

        return payload
    except JWTError:
        return None
