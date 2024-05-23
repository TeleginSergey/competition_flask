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
    description TEXT,
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
