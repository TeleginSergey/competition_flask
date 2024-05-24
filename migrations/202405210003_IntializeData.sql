-- migrate:up


CREATE SCHEMA competition_schema;

SET search_path TO public, competition_schema;

CREATE EXTENSION "uuid-ossp";

CREATE TABLE IF NOT EXISTS competition_schema.competitions (
    id uuid primary key default uuid_generate_v4(),
    title TEXT NOT NULL,
    date_of_start DATE,
    date_of_end DATE
);

CREATE TABLE IF NOT EXISTS competition_schema.sports
    (id uuid primary key default uuid_generate_v4(), 
    title TEXT NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS competition_schema.competition_sport 
    (id uuid primary key default uuid_generate_v4(), 
    competition_id uuid references competition_schema.competitions,
    sport_id uuid references competition_schema.sports
);

CREATE UNIQUE INDEX competition_sport_idx ON competition_schema.competition_sport (competition_id, sport_id);

CREATE TABLE IF NOT EXISTS competition_schema.stages 
    (id uuid primary key default uuid_generate_v4(), 
    title text not null, 
    date DATE,
    place TEXT,
    competition_sport_id uuid references competition_schema.competition_sport
);

-- Вставка данных в таблицу competitions
INSERT INTO competition_schema.competitions (title, date_of_start, date_of_end)
VALUES ('Competition 1', '2024-06-01', '2024-06-10'),
('Summer Games 2024', '2024-07-15', '2024-08-10');

-- Вставка данных в таблицу sports
INSERT INTO competition_schema.sports (title, description)
VALUES ('Sport 1', 'Description for Sport 1'),
('Swimming', 'Competitive swimming sport');

-- Связывание между competitions и sports через competition_sport
INSERT INTO competition_schema.competition_sport (competition_id, sport_id)
SELECT c.id, s.id
FROM competition_schema.competitions c
CROSS JOIN competition_schema.sports s
WHERE c.title = 'Competition 1' AND s.title = 'Sport 1';

INSERT INTO competition_schema.competition_sport (competition_id, sport_id)
SELECT c.id, s.id
FROM competition_schema.competitions c
CROSS JOIN competition_schema.sports s
WHERE c.title = 'Summer Games 2024' AND s.title = 'Swimming';

-- Вставка данных в таблицу stages и связывание с competition_sport
INSERT INTO competition_schema.stages (title, date, place, competition_sport_id)
SELECT 'Stage 1', '2024-06-05', 'Stage Place 1', cs.id
FROM competition_schema.competition_sport cs
JOIN competition_schema.competitions c ON cs.competition_id = c.id
JOIN competition_schema.sports s ON cs.sport_id = s.id
WHERE c.title = 'Competition 1' AND s.title = 'Sport 1';

INSERT INTO competition_schema.stages (title, date, place, competition_sport_id)
SELECT 'Swimming Preliminaries', '2024-08-01', 'Aquatics Center', cs.id
FROM competition_schema.competition_sport cs
JOIN competition_schema.competitions c ON cs.competition_id = c.id
JOIN competition_schema.sports s ON cs.sport_id = s.id
WHERE c.title = 'Summer Games 2024' AND s.title = 'Swimming';

INSERT INTO competition_schema.stages (title, date, place, competition_sport_id)
SELECT 'Swimming Finals', '2024-08-10', 'Aquatics Center', cs.id
FROM competition_schema.competition_sport cs
JOIN competition_schema.competitions c ON cs.competition_id = c.id
JOIN competition_schema.sports s ON cs.sport_id = s.id
WHERE c.title = 'Summer Games 2024' AND s.title = 'Swimming';


-- migrate:down