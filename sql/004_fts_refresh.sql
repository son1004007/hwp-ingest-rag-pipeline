ALTER TABLE public.doc_blocks
ADD COLUMN IF NOT EXISTS tsv tsvector;

UPDATE public.doc_blocks
SET tsv = to_tsvector('simple', coalesce(content,''));

CREATE INDEX IF NOT EXISTS ix_doc_blocks_tsv
ON public.doc_blocks USING GIN (tsv);
