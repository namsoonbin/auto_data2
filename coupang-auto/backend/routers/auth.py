# -*- coding: utf-8 -*-
"""
인증 API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
import re

from services.database import get_db
from models.auth import User, Tenant, TenantMembership
from schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    TokenRefresh,
    UserResponse,
    TenantResponse,
    ProfileUpdate,
    ProfileResponse,
    PasswordChange,
    TenantUpdate,
    AccountDelete
)
from auth.jwt import create_access_token, create_refresh_token, verify_token
from auth.password import hash_password, verify_password
from auth.dependencies import get_current_user, get_current_tenant

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    회원가입

    - 새로운 테넌트(쇼핑몰)와 사용자를 생성합니다
    - 첫 사용자는 자동으로 Owner 역할을 받습니다
    """
    # 이메일 중복 확인
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일입니다"
        )

    # 슬러그 유효성 검사
    if not re.match(r'^[a-z0-9-]+$', user_data.tenant_slug):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="슬러그는 영문 소문자, 숫자, 하이픈만 사용할 수 있습니다"
        )

    # 슬러그 중복 확인
    existing_tenant = db.query(Tenant).filter(Tenant.slug == user_data.tenant_slug).first()
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용 중인 슬러그입니다"
        )

    try:
        # 테넌트 생성
        tenant = Tenant(
            id=uuid.uuid4(),
            name=user_data.tenant_name,
            slug=user_data.tenant_slug,
            plan="basic",
            is_active=True
        )
        db.add(tenant)
        db.flush()  # ID 생성을 위해 flush

        # 사용자 생성
        user = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            full_name=user_data.full_name,
            role="owner",  # 첫 사용자는 owner
            is_active=True,
            email_verified=False
        )
        db.add(user)
        db.flush()

        # 멤버십 생성
        membership = TenantMembership(
            user_id=user.id,
            tenant_id=tenant.id,
            role="owner",
            is_active=True
        )
        db.add(membership)

        db.commit()

        # 토큰 생성
        access_token = create_access_token(
            data={"sub": str(user.id), "tenant_id": str(tenant.id), "role": user.role}
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"회원가입 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    로그인

    - 이메일과 비밀번호로 인증합니다
    - 성공 시 액세스 토큰과 리프레시 토큰을 반환합니다
    """
    # 사용자 조회
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자입니다"
        )

    # 테넌트 확인
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if not tenant or not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 테넌트입니다"
        )

    # 토큰 생성
    access_token = create_access_token(
        data={"sub": str(user.id), "tenant_id": str(user.tenant_id), "role": user.role}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )

    # 마지막 로그인 시간 업데이트
    from datetime import datetime
    user.last_login = datetime.now()
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
):
    """
    토큰 갱신

    - 리프레시 토큰을 사용하여 새로운 액세스 토큰을 발급합니다
    """
    # 리프레시 토큰 검증
    payload = verify_token(token_data.refresh_token, token_type="refresh")

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 리프레시 토큰입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다"
        )

    # 사용자 조회
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없거나 비활성화되었습니다"
        )

    # 새 토큰 생성
    access_token = create_access_token(
        data={"sub": str(user.id), "tenant_id": str(user.tenant_id), "role": user.role}
    )
    new_refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    현재 로그인한 사용자 정보 조회
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        tenant_id=str(current_user.tenant_id),
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@router.get("/tenant", response_model=TenantResponse)
async def get_tenant_info(
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    현재 사용자의 테넌트 정보 조회
    """
    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        slug=tenant.slug,
        plan=tenant.plan,
        is_active=tenant.is_active,
        created_at=tenant.created_at
    )


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    """
    프로필 상세 정보 조회

    /me 엔드포인트보다 더 자세한 정보를 반환합니다
    """
    return ProfileResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        role=current_user.role,
        tenant_id=str(current_user.tenant_id),
        is_active=current_user.is_active,
        email_verified=current_user.email_verified,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.put("/profile", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    프로필 정보 수정

    - 이름, 전화번호 등을 수정할 수 있습니다
    - 이메일은 수정할 수 없습니다
    """
    try:
        # 수정할 필드만 업데이트
        if profile_data.full_name is not None:
            current_user.full_name = profile_data.full_name

        if profile_data.phone is not None:
            current_user.phone = profile_data.phone

        from datetime import datetime
        current_user.updated_at = datetime.now()

        db.commit()
        db.refresh(current_user)

        return ProfileResponse(
            id=str(current_user.id),
            email=current_user.email,
            full_name=current_user.full_name,
            phone=current_user.phone,
            role=current_user.role,
            tenant_id=str(current_user.tenant_id),
            is_active=current_user.is_active,
            email_verified=current_user.email_verified,
            created_at=current_user.created_at,
            last_login=current_user.last_login
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"프로필 수정 중 오류가 발생했습니다: {str(e)}"
        )


@router.put("/password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    비밀번호 변경

    - 현재 비밀번호를 확인한 후 새 비밀번호로 변경합니다
    """
    # 현재 비밀번호 확인
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="현재 비밀번호가 올바르지 않습니다"
        )

    # 새 비밀번호와 현재 비밀번호가 같은지 확인
    if password_data.old_password == password_data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="새 비밀번호는 현재 비밀번호와 달라야 합니다"
        )

    try:
        # 비밀번호 변경
        current_user.hashed_password = hash_password(password_data.new_password)

        from datetime import datetime
        current_user.updated_at = datetime.now()

        db.commit()

        return {"message": "비밀번호가 성공적으로 변경되었습니다"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"비밀번호 변경 중 오류가 발생했습니다: {str(e)}"
        )


@router.put("/tenant", response_model=TenantResponse)
async def update_tenant(
    tenant_data: TenantUpdate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    테넌트 정보 수정

    - Owner 또는 Admin 권한이 필요합니다
    - 테넌트 이름을 수정할 수 있습니다
    - Slug는 보안상 수정할 수 없습니다
    """
    # 권한 확인 (Owner 또는 Admin만 수정 가능)
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="테넌트 정보를 수정할 권한이 없습니다"
        )

    try:
        # 테넌트 이름 수정
        current_tenant.name = tenant_data.name

        from datetime import datetime
        current_tenant.updated_at = datetime.now()

        db.commit()
        db.refresh(current_tenant)

        return TenantResponse(
            id=str(current_tenant.id),
            name=current_tenant.name,
            slug=current_tenant.slug,
            plan=current_tenant.plan,
            is_active=current_tenant.is_active,
            created_at=current_tenant.created_at
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"테넌트 정보 수정 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete("/account")
async def delete_account(
    delete_data: AccountDelete,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    계정 삭제

    - 비밀번호를 확인한 후 계정을 삭제합니다
    - Owner인 경우: 테넌트와 모든 관련 데이터가 함께 삭제됩니다
    - 일반 사용자인 경우: 해당 사용자 계정만 삭제됩니다

    경고: 이 작업은 되돌릴 수 없습니다!
    """
    # 비밀번호 확인
    if not verify_password(delete_data.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호가 올바르지 않습니다"
        )

    try:
        # Owner인 경우 테넌트의 모든 데이터 삭제
        if current_user.role == 'owner':
            # 1. IntegratedRecord 삭제
            from services.database import IntegratedRecord, ProductMargin
            db.query(IntegratedRecord).filter(
                IntegratedRecord.tenant_id == current_tenant.id
            ).delete()

            # 2. ProductMargin 삭제
            db.query(ProductMargin).filter(
                ProductMargin.tenant_id == current_tenant.id
            ).delete()

            # 3. 다른 멤버들의 멤버십 삭제
            db.query(TenantMembership).filter(
                TenantMembership.tenant_id == current_tenant.id
            ).delete()

            # 4. 테넌트의 다른 사용자들 삭제
            db.query(User).filter(
                User.tenant_id == current_tenant.id,
                User.id != current_user.id
            ).delete()

            # 5. 현재 사용자 삭제
            db.delete(current_user)

            # 6. 테넌트 삭제
            db.delete(current_tenant)

            db.commit()
            return {
                "message": "계정과 테넌트가 성공적으로 삭제되었습니다",
                "deleted_type": "tenant_and_account"
            }

        else:
            # 일반 사용자인 경우 본인 계정만 삭제
            # 1. 멤버십 삭제
            db.query(TenantMembership).filter(
                TenantMembership.user_id == current_user.id
            ).delete()

            # 2. 사용자 삭제
            db.delete(current_user)

            db.commit()
            return {
                "message": "계정이 성공적으로 삭제되었습니다",
                "deleted_type": "account_only"
            }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"계정 삭제 중 오류가 발생했습니다: {str(e)}"
        )
