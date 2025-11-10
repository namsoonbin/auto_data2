# -*- coding: utf-8 -*-
"""
팀 관리 API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from services.database import get_db
from models.auth import User, Tenant, TenantMembership
from schemas.team import (
    TeamMemberResponse,
    TeamMemberInvite,
    TeamMemberRoleUpdate,
    TeamMembersListResponse
)
from auth.password import hash_password
from auth.dependencies import get_current_user, get_current_tenant

router = APIRouter(prefix="/api/team", tags=["team"])


@router.get("/members", response_model=TeamMembersListResponse)
async def get_team_members(
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    팀원 목록 조회

    현재 테넌트의 모든 팀원을 조회합니다
    """
    # 현재 테넌트의 모든 사용자 조회
    members = db.query(User).filter(
        User.tenant_id == current_tenant.id
    ).order_by(User.created_at).all()

    member_responses = [
        TeamMemberResponse(
            id=str(member.id),
            email=member.email,
            full_name=member.full_name,
            role=member.role,
            is_active=member.is_active,
            created_at=member.created_at,
            last_login=member.last_login
        )
        for member in members
    ]

    return TeamMembersListResponse(
        members=member_responses,
        total=len(member_responses)
    )


@router.post("/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
async def invite_team_member(
    invite_data: TeamMemberInvite,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    팀원 초대

    - Owner 또는 Admin 권한이 필요합니다
    - 새로운 사용자를 현재 테넌트에 추가합니다
    """
    # 권한 확인 (Owner 또는 Admin만)
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="팀원을 초대할 권한이 없습니다"
        )

    # 역할 유효성 검사
    valid_roles = ['admin', 'member']
    if invite_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"유효하지 않은 역할입니다. 가능한 역할: {', '.join(valid_roles)}"
        )

    # 이메일 중복 확인 (전체 시스템)
    existing_user = db.query(User).filter(User.email == invite_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일입니다"
        )

    try:
        # 새 사용자 생성
        new_user = User(
            id=uuid.uuid4(),
            tenant_id=current_tenant.id,
            email=invite_data.email,
            hashed_password=hash_password(invite_data.password),
            full_name=invite_data.full_name,
            role=invite_data.role,
            is_active=True,
            email_verified=False
        )
        db.add(new_user)
        db.flush()

        # 멤버십 생성
        membership = TenantMembership(
            user_id=new_user.id,
            tenant_id=current_tenant.id,
            role=invite_data.role,
            is_active=True
        )
        db.add(membership)

        db.commit()
        db.refresh(new_user)

        return TeamMemberResponse(
            id=str(new_user.id),
            email=new_user.email,
            full_name=new_user.full_name,
            role=new_user.role,
            is_active=new_user.is_active,
            created_at=new_user.created_at,
            last_login=new_user.last_login
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"팀원 초대 중 오류가 발생했습니다: {str(e)}"
        )


@router.put("/members/{user_id}/role", response_model=TeamMemberResponse)
async def update_member_role(
    user_id: str,
    role_data: TeamMemberRoleUpdate,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    팀원 역할 변경

    - Owner만 역할을 변경할 수 있습니다
    - Owner 역할은 변경할 수 없습니다
    """
    # 권한 확인 (Owner만)
    if current_user.role != 'owner':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="팀원의 역할을 변경할 권한이 없습니다"
        )

    # 역할 유효성 검사
    valid_roles = ['owner', 'admin', 'member']
    if role_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"유효하지 않은 역할입니다. 가능한 역할: {', '.join(valid_roles)}"
        )

    # 대상 사용자 조회
    target_user = db.query(User).filter(
        User.id == user_id,
        User.tenant_id == current_tenant.id
    ).first()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )

    # 자기 자신은 변경 불가
    if str(target_user.id) == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자신의 역할은 변경할 수 없습니다"
        )

    # Owner 역할 변경 제한
    if target_user.role == 'owner':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner 역할은 변경할 수 없습니다"
        )

    try:
        # 역할 변경
        target_user.role = role_data.role

        # 멤버십도 업데이트
        membership = db.query(TenantMembership).filter(
            TenantMembership.user_id == target_user.id,
            TenantMembership.tenant_id == current_tenant.id
        ).first()

        if membership:
            membership.role = role_data.role

        from datetime import datetime
        target_user.updated_at = datetime.now()

        db.commit()
        db.refresh(target_user)

        return TeamMemberResponse(
            id=str(target_user.id),
            email=target_user.email,
            full_name=target_user.full_name,
            role=target_user.role,
            is_active=target_user.is_active,
            created_at=target_user.created_at,
            last_login=target_user.last_login
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"역할 변경 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete("/members/{user_id}")
async def remove_team_member(
    user_id: str,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    팀원 제거

    - Owner 또는 Admin 권한이 필요합니다
    - Owner는 제거할 수 없습니다
    - 자기 자신은 제거할 수 없습니다
    """
    # 권한 확인 (Owner 또는 Admin)
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="팀원을 제거할 권한이 없습니다"
        )

    # 대상 사용자 조회
    target_user = db.query(User).filter(
        User.id == user_id,
        User.tenant_id == current_tenant.id
    ).first()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )

    # 자기 자신은 제거 불가
    if str(target_user.id) == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자신을 제거할 수 없습니다"
        )

    # Owner는 제거 불가
    if target_user.role == 'owner':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner는 제거할 수 없습니다"
        )

    # Admin은 Owner만 제거 가능
    if target_user.role == 'admin' and current_user.role != 'owner':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin을 제거할 권한이 없습니다"
        )

    try:
        # 멤버십 삭제
        db.query(TenantMembership).filter(
            TenantMembership.user_id == target_user.id,
            TenantMembership.tenant_id == current_tenant.id
        ).delete()

        # 사용자 삭제
        db.delete(target_user)

        db.commit()

        return {"message": f"{target_user.email}이(가) 팀에서 제거되었습니다"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"팀원 제거 중 오류가 발생했습니다: {str(e)}"
        )
