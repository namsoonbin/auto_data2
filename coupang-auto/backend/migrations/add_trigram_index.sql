-- ==========================================
-- Product Name 검색 최적화: Trigram 인덱스 추가
-- ==========================================
-- 목적: LIKE '%검색어%' 패턴 검색 성능 향상
-- 생성일: 2025-11-17
-- ==========================================

-- 1. pg_trgm 확장 활성화
-- ==========================================
-- Trigram 인덱스를 사용하려면 pg_trgm 확장이 필요합니다
-- 이미 설치되어 있으면 무시됩니다

CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 2. Trigram GIN 인덱스 추가
-- ==========================================

-- integrated_records 테이블의 product_name에 trigram 인덱스 추가
-- 기존 B-tree 인덱스는 유지됩니다 (정렬 및 prefix 검색에 유용)
CREATE INDEX IF NOT EXISTS idx_integrated_records_product_name_trgm
ON public.integrated_records
USING gin (product_name gin_trgm_ops);

-- fake_purchases 테이블의 product_name에도 trigram 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_fake_purchases_product_name_trgm
ON public.fake_purchases
USING gin (product_name gin_trgm_ops);

-- ==========================================
-- 완료!
-- ==========================================
--
-- 성능 향상 예상:
-- - LIKE '%검색어%' 쿼리 속도: 10-100배 개선 (데이터 크기에 따라)
-- - 특히 긴 문자열에서 부분 일치 검색 시 효과적
--
-- 확인 방법:
-- SELECT indexname, indexdef
-- FROM pg_indexes
-- WHERE tablename IN ('integrated_records', 'fake_purchases')
--   AND indexname LIKE '%trgm%';
--
-- 쿼리 플랜 확인:
-- EXPLAIN ANALYZE
-- SELECT * FROM integrated_records
-- WHERE product_name LIKE '%검색어%';
-- ==========================================
