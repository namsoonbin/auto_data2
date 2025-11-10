# -*- coding: utf-8 -*-
"""
인증 API 테스트 스크립트
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_register():
    """회원가입 테스트"""
    print("=== 회원가입 테스트 ===")

    data = {
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "테스트 사용자",
        "tenant_name": "테스트 쇼핑몰",
        "tenant_slug": "test-shop"
    }

    response = requests.post(f"{BASE_URL}/api/auth/register", json=data)
    print(f"상태 코드: {response.status_code}")
    print(f"응답: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    if response.status_code == 201:
        return response.json()
    return None

def test_login():
    """로그인 테스트"""
    print("\n=== 로그인 테스트 ===")

    data = {
        "email": "test@example.com",
        "password": "testpass123"
    }

    response = requests.post(f"{BASE_URL}/api/auth/login", json=data)
    print(f"상태 코드: {response.status_code}")
    print(f"응답: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    if response.status_code == 200:
        return response.json()
    return None

def test_get_me(access_token):
    """사용자 정보 조회 테스트"""
    print("\n=== 사용자 정보 조회 테스트 ===")

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    print(f"상태 코드: {response.status_code}")
    print(f"응답: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_get_tenant(access_token):
    """테넌트 정보 조회 테스트"""
    print("\n=== 테넌트 정보 조회 테스트 ===")

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(f"{BASE_URL}/api/auth/tenant", headers=headers)
    print(f"상태 코드: {response.status_code}")
    print(f"응답: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    # 회원가입
    register_result = test_register()

    if register_result:
        access_token = register_result.get("access_token")

        # 사용자 정보 조회
        test_get_me(access_token)

        # 테넌트 정보 조회
        test_get_tenant(access_token)

    # 로그인
    login_result = test_login()

    if login_result:
        access_token = login_result.get("access_token")

        # 다시 사용자 정보 조회
        test_get_me(access_token)

    print("\n✅ 테스트 완료!")
