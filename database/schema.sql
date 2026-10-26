-- NIGHT ROUNDS: database for anonymous gameplay statistics (Supabase / PostgreSQL)
-- Run once in the Supabase SQL Editor to recreate the database from scratch.

-- One row per game played
create table public.runs (
    run_id         uuid primary key,
    player_id      uuid not null,
    game_version   text not null check (char_length(game_version) <= 16),
    language       text not null check (language in ('en', 'fr')),
    mode           text not null check (mode in ('exploration', 'survival')),
    difficulty     text not null check (difficulty in ('easy', 'normal', 'hard')),
    started_at     timestamptz not null,
    duration_s     integer not null check (duration_s between 0 and 86400),
    outcome        text not null check (outcome in ('won', 'caught', 'quit')),
    steps_done     text[] not null default '{}' check (cardinality(steps_done) <= 10),
    documents_read smallint not null default 0 check (documents_read between 0 and 50),
    hides          smallint not null default 0 check (hides between 0 and 1000),
    map_opens      smallint not null default 0 check (map_opens between 0 and 1000),
    received_at    timestamptz not null default now()
);

-- One row per thing that happened during a game
create table public.events (
    id       bigint generated always as identity primary key,
    run_id   uuid not null references public.runs (run_id) on delete cascade,
    kind     text not null check (kind in ('caught', 'item', 'hide', 'document', 'objective', 'map')),
    detail   text check (char_length(detail) <= 32),
    at_s     integer not null check (at_s between 0 and 86400),
    cell_row smallint check (cell_row between 0 and 200),
    cell_col smallint check (cell_col between 0 and 200)
);

-- Security: the game may only ADD rows, never read, change or delete them
alter table public.runs enable row level security;
alter table public.events enable row level security;

create policy "game can insert runs"
    on public.runs for insert to anon with check (true);

create policy "game can insert events"
    on public.events for insert to anon with check (true);

-- Table privileges: without them, the policies above are never reached (error 401)
grant insert on public.runs, public.events to anon;
grant usage on all sequences in schema public to anon;