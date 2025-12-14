-- embedding 컬럼 추가 (384차원 기준)
ALTER TABLE public.doc_blocks
ADD COLUMN IF NOT EXISTS embedding vector(384);

-- 임베딩 생성/갱신 추적용(선택)
ALTER TABLE public.doc_blocks
ADD COLUMN IF NOT EXISTS embedded_at timestamptz;
