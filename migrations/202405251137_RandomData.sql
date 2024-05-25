-- migrate:up


INSERT INTO competition_schema.stages (title, date)
SELECT
    'stages_' || chr(trunc(65 + random() * 26)::int) || chr(trunc(65 + random() * 26)::int) || '_' || row_number() OVER () || '_' || uuid_generate_v4(),
    current_date + (random() * 30)::int
FROM generate_series(1, 100000);


-- migrate:down