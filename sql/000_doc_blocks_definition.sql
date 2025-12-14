-- public.doc_blocks definition

-- Drop table

-- DROP TABLE public.doc_blocks;

CREATE TABLE public.doc_blocks (
	id bigserial NOT NULL,
	doc_id text NULL,
	doc_title text NULL,
	section_title text NULL,
	section_path text NULL,
	block_id text NULL,
	block_type text NULL,
	"content" text NOT NULL,
	metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
	created_at timestamptz DEFAULT now() NOT NULL,
	updated_at timestamptz NULL,
	tsv tsvector NULL,
	CONSTRAINT doc_blocks_pkey PRIMARY KEY (id)
);
CREATE INDEX ix_doc_blocks_blocktype ON public.doc_blocks USING btree (block_type);
CREATE INDEX ix_doc_blocks_docid ON public.doc_blocks USING btree (doc_id);
CREATE INDEX ix_doc_blocks_tsv ON public.doc_blocks USING gin (tsv);
CREATE UNIQUE INDEX ux_doc_blocks_docid_blockid ON public.doc_blocks USING btree (doc_id, block_id);