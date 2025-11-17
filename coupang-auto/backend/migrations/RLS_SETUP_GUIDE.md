# Supabase RLS (Row Level Security) 설정 가이드

## 📋 개요

11개 테이블에 대한 RLS 활성화 및 보안 정책 설정

**보안 문제**: RLS 없이 public 테이블이 PostgREST API에 노출되어 있음
**해결책**: Tenant 기반 RLS 정책 적용

---

## 🚀 빠른 실행 (3분 완료)

### 1. Supabase Dashboard에서 실행

1. Supabase Dashboard 접속
2. **SQL Editor** 메뉴 이동
3. **New Query** 클릭
4. `enable_rls_security.sql` 파일 내용 복사
5. **Run** 클릭

### 2. 또는 psql로 실행

```bash
psql -h [your-project-ref].supabase.co -U postgres -d postgres -f migrations/enable_rls_security.sql
```

---

## ✅ 적용된 보안 정책

### 1. **Tenant 격리 정책** (8개 테이블)

다음 테이블들은 `tenant_id` 기반으로 완전히 격리됩니다:

- `integrated_records`
- `product_margins`
- `upload_history`
- `fake_purchases`
- `sales_records_legacy`
- `ad_records_legacy`
- `product_master_legacy`
- `audit_logs`

**정책**: 사용자는 자신의 tenant_id에 속한 데이터만 조회/수정/삭제 가능

### 2. **Users 테이블 정책**

- 사용자는 **자신의 정보만** 조회/수정 가능
- 다른 사용자 정보 접근 불가

### 3. **Tenants 테이블 정책**

- 사용자는 **자신이 속한 tenant**만 조회 가능
- Tenant 생성은 애플리케이션 레벨에서만 가능 (SQL 직접 접근 차단)

### 4. **Tenant Memberships 정책**

- 사용자는 **자신의 멤버십만** 조회 가능
- 멤버십 생성/수정/삭제는 애플리케이션 레벨에서만

---

## 🔧 중요: 추가 설정 필요

### ⚠️ JWT Custom Claim 설정

RLS 정책이 작동하려면 **JWT 토큰에 `tenant_id`를 포함**해야 합니다.

#### Option 1: Supabase Auth Hooks (권장)

Supabase Dashboard > Authentication > Hooks에서 설정:

```sql
-- Hook Function: After Sign In
CREATE OR REPLACE FUNCTION public.custom_access_token_hook(event jsonb)
RETURNS jsonb AS $$
DECLARE
  user_tenant_id uuid;
BEGIN
  -- 사용자의 tenant_id 조회
  SELECT tm.tenant_id INTO user_tenant_id
  FROM public.tenant_memberships tm
  WHERE tm.user_id = (event->>'user_id')::uuid
  LIMIT 1;

  -- JWT에 tenant_id 추가
  IF user_tenant_id IS NOT NULL THEN
    event := jsonb_set(
      event,
      '{claims,tenant_id}',
      to_jsonb(user_tenant_id::text)
    );
  END IF;

  RETURN event;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

#### Option 2: Backend에서 Custom Token 발급

Backend API에서 사용자 로그인 시 tenant_id를 토큰에 포함:

```python
# auth/jwt.py 수정 예시
def create_access_token(user_id: UUID, tenant_id: UUID):
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),  # 추가
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
```

---

## 🔍 확인 방법

### 1. RLS 활성화 확인

```sql
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

**예상 결과**: 모든 테이블의 `rowsecurity`가 `true`

### 2. 정책 확인

```sql
SELECT schemaname, tablename, policyname, roles, cmd
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;
```

**예상 결과**: 11개 테이블에 각각 정책이 생성됨

### 3. 실제 테스트

```sql
-- anon 롤로 테스트 (접근 불가해야 함)
SET ROLE anon;
SELECT COUNT(*) FROM public.integrated_records;
-- 예상: 0 rows (RLS로 차단됨)

-- authenticated 롤로 테스트
SET ROLE authenticated;
SET request.jwt.claims = '{"tenant_id": "your-tenant-uuid"}';
SELECT COUNT(*) FROM public.integrated_records;
-- 예상: 해당 tenant의 레코드만 반환

-- 원래대로 복구
RESET ROLE;
```

---

## 🛡️ 보안 아키텍처

### Backend API 사용 (현재 구조)

```
Frontend → Backend API (service_role) → Supabase
                ↓
         tenant_id 필터링
         (코드 레벨)
```

- Backend는 `service_role` 키 사용
- **RLS를 우회**하므로 코드에서 tenant_id 필터링 필수
- 현재 코드에는 이미 구현되어 있음 ✅

### Frontend 직접 접근 (미래 구조)

```
Frontend (authenticated user) → Supabase
                ↓
         RLS 자동 적용
         (JWT tenant_id)
```

- `anon` 또는 `authenticated` 키 사용
- **RLS가 자동 적용**되어 tenant 격리
- JWT에 tenant_id 필수

---

## ⚡ 성능 고려사항

### 1. 인덱스 확인

RLS 정책이 tenant_id를 사용하므로 인덱스 필수:

```sql
-- 이미 Phase 2에서 추가됨
-- 추가 확인:
SELECT tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexdef LIKE '%tenant_id%';
```

### 2. 정책 성능

- `get_current_tenant_id()` 함수는 캐시됨 (빠름)
- Tenant별 쿼리는 인덱스를 사용하므로 성능 저하 없음

---

## 🚨 문제 해결

### "permission denied" 에러 발생

**원인**: RLS 정책에 의해 차단됨

**해결책**:
1. JWT에 올바른 tenant_id가 포함되어 있는지 확인
2. Backend API를 사용한다면 `service_role` 키 사용 확인

### Backend API에서 데이터 조회 안 됨

**확인사항**:
```python
# .env 파일 확인
SUPABASE_SERVICE_ROLE_KEY=eyJ...  # service_role 키 사용 중인지 확인
# NOT: SUPABASE_ANON_KEY
```

**Backend 초기화 확인**:
```python
# database.py
supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY  # ← service_role 사용
)
```

### 특정 테이블만 접근 안 됨

**디버깅**:
```sql
-- 해당 테이블의 정책 확인
SELECT * FROM pg_policies WHERE tablename = 'your_table_name';

-- 정책 비활성화 (임시 테스트)
ALTER TABLE your_table_name DISABLE ROW LEVEL SECURITY;
-- 테스트 후 다시 활성화
ALTER TABLE your_table_name ENABLE ROW LEVEL SECURITY;
```

---

## 📚 참고 자료

- [Supabase RLS 공식 문서](https://supabase.com/docs/guides/auth/row-level-security)
- [PostgreSQL RLS 문서](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Supabase Auth Hooks](https://supabase.com/docs/guides/auth/auth-hooks)

---

## ✨ 완료 체크리스트

- [ ] `enable_rls_security.sql` 실행
- [ ] RLS 활성화 확인 (11개 테이블 모두 `true`)
- [ ] 정책 생성 확인
- [ ] JWT Custom Claim 설정 (Frontend 직접 접근 시)
- [ ] Backend API 정상 작동 확인
- [ ] Supabase Dashboard 경고 사라짐 확인

---

**실행 후 Supabase Dashboard의 "RLS has not been enabled" 경고가 사라집니다!** 🎉
