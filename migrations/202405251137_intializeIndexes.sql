-- migrate:up

create extension if not exists pg_trgm;
create index stages_title_gin_idx on competition_schema.stages using gin("title", gin_trgm_ops);
create index stages_date_btree_idx ON competition_schema.stages ("date");

-- migrate:down