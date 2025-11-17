-- ==========================================
-- Supabase RLS (Row Level Security) 활성화
-- ==========================================
-- 목적: PostgREST API를 통한 무단 접근 차단
-- 생성일: 2025-11-17
-- ==========================================

-- 1. 모든 테이블에 RLS 활성화
-- ==========================================

ALTER TABLE public.integrated_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.product_margins ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.upload_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fake_purchases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sales_records_legacy ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ad_records_legacy ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.product_master_legacy ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tenant_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- 2. 기존 정책 삭제 (재실행 시 중복 방지)
-- ==========================================

DROP POLICY IF EXISTS "tenant_isolation_policy" ON public.integrated_records;
DROP POLICY IF EXISTS "tenant_isolation_policy" ON public.product_margins;
DROP POLICY IF EXISTS "tenant_isolation_policy" ON public.upload_history;
DROP POLICY IF EXISTS "tenant_isolation_policy" ON public.fake_purchases;
DROP POLICY IF EXISTS "tenant_isolation_policy" ON public.sales_records_legacy;
DROP POLICY IF EXISTS "tenant_isolation_policy" ON public.ad_records_legacy;
DROP POLICY IF EXISTS "tenant_isolation_policy" ON public.product_master_legacy;
DROP POLICY IF EXISTS "legacy_read_only" ON public.sales_records_legacy;
DROP POLICY IF EXISTS "legacy_read_only" ON public.ad_records_legacy;
DROP POLICY IF EXISTS "legacy_read_only" ON public.product_master_legacy;
DROP POLICY IF EXISTS "tenant_isolation_policy" ON public.audit_logs;

DROP POLICY IF EXISTS "users_own_data" ON public.users;
DROP POLICY IF EXISTS "tenants_own_data" ON public.tenants;
DROP POLICY IF EXISTS "membership_access" ON public.tenant_memberships;

-- 3. 헬퍼 함수: 현재 사용자의 tenant_id 가져오기
-- ==========================================

CREATE OR REPLACE FUNCTION public.get_current_tenant_id()
RETURNS UUID AS $$
BEGIN
  -- JWT 토큰의 app_metadata에서 tenant_id 추출
  -- Supabase Auth에서 설정한 custom claim 사용
  RETURN (current_setting('request.jwt.claims', true)::json->>'tenant_id')::UUID;
EXCEPTION
  WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 4. 헬퍼 함수: 현재 사용자 ID 가져오기
-- ==========================================

CREATE OR REPLACE FUNCTION public.get_current_user_id()
RETURNS UUID AS $$
BEGIN
  -- Supabase Auth의 auth.uid() 사용
  RETURN auth.uid();
EXCEPTION
  WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 5. Tenant 격리 정책 (tenant_id 기반 테이블)
-- ==========================================

-- integrated_records: tenant만 자신의 데이터 접근
CREATE POLICY "tenant_isolation_policy" ON public.integrated_records
  FOR ALL
  USING (tenant_id = get_current_tenant_id());

-- product_margins: tenant만 자신의 데이터 접근
CREATE POLICY "tenant_isolation_policy" ON public.product_margins
  FOR ALL
  USING (tenant_id = get_current_tenant_id());

-- upload_history: tenant만 자신의 데이터 접근
CREATE POLICY "tenant_isolation_policy" ON public.upload_history
  FOR ALL
  USING (tenant_id = get_current_tenant_id());

-- fake_purchases: tenant만 자신의 데이터 접근
CREATE POLICY "tenant_isolation_policy" ON public.fake_purchases
  FOR ALL
  USING (tenant_id = get_current_tenant_id());

-- sales_records_legacy: Legacy 테이블 (tenant_id 없음)
-- 옵션 1: 모든 접근 차단 (권장)
CREATE POLICY "legacy_read_only" ON public.sales_records_legacy
  FOR SELECT
  USING (false);  -- 모든 SELECT 차단

-- 옵션 2: service_role만 접근 가능하도록 (Backend API만)
-- 이미 service_role은 RLS를 우회하므로 별도 정책 불필요

-- ad_records_legacy: Legacy 테이블 (tenant_id 없음)
CREATE POLICY "legacy_read_only" ON public.ad_records_legacy
  FOR SELECT
  USING (false);  -- 모든 SELECT 차단

-- product_master_legacy: Legacy 테이블 (tenant_id 없음)
CREATE POLICY "legacy_read_only" ON public.product_master_legacy
  FOR SELECT
  USING (false);  -- 모든 SELECT 차단

-- audit_logs: tenant만 자신의 로그 접근
CREATE POLICY "tenant_isolation_policy" ON public.audit_logs
  FOR ALL
  USING (tenant_id = get_current_tenant_id());

-- 6. Users 테이블 정책
-- ==========================================

-- 사용자는 자신의 정보만 조회/수정 가능
CREATE POLICY "users_own_data" ON public.users
  FOR ALL
  USING (id = get_current_user_id());

-- 7. Tenants 테이블 정책
-- ==========================================

-- 사용자는 자신이 속한 tenant 정보만 조회 가능
CREATE POLICY "tenants_own_data" ON public.tenants
  FOR SELECT
  USING (
    id IN (
      SELECT tenant_id
      FROM public.tenant_memberships
      WHERE user_id = get_current_user_id()
    )
  );

-- Tenant 생성은 제한 (애플리케이션 레벨에서만)
CREATE POLICY "tenants_create_restricted" ON public.tenants
  FOR INSERT
  WITH CHECK (false);

-- 8. Tenant Memberships 테이블 정책
-- ==========================================

-- 사용자는 자신의 멤버십만 조회 가능
CREATE POLICY "membership_access" ON public.tenant_memberships
  FOR SELECT
  USING (user_id = get_current_user_id());

-- 멤버십 생성/수정/삭제는 제한 (애플리케이션 레벨에서만)
CREATE POLICY "membership_modify_restricted" ON public.tenant_memberships
  FOR INSERT
  WITH CHECK (false);

-- 9. 서비스 롤에 대한 바이패스 (Backend API용)
-- ==========================================

-- Backend API는 service_role key를 사용하므로 RLS를 우회할 수 있습니다.
-- 이는 Supabase의 기본 동작이며, 별도 설정 불필요합니다.

-- 참고: service_role은 모든 RLS를 무시하고 전체 접근 권한을 가집니다.
-- Backend에서 tenant_id 기반 필터링을 직접 구현해야 합니다.

-- 10. 권한 부여 (필요 시)
-- ==========================================

-- anon 롤: 인증되지 않은 사용자 (일반적으로 접근 불가)
-- authenticated 롤: 인증된 사용자 (RLS 정책에 따라 접근)

GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;

-- ==========================================
-- 완료!
-- ==========================================
--
-- 실행 방법:
-- 1. Supabase Dashboard > SQL Editor에서 실행
-- 2. 또는 psql로 실행: psql -h [host] -U postgres -d postgres -f enable_rls_security.sql
--
-- 확인 방법:
-- SELECT tablename, rowsecurity
-- FROM pg_tables
-- WHERE schemaname = 'public';
--
-- 정책 확인:
-- SELECT * FROM pg_policies WHERE schemaname = 'public';
-- ==========================================
