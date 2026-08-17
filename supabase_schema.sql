
-- CHEN212 Mission 01 - Supabase schema
-- Run this once in Supabase SQL Editor.

create table if not exists public.mission_runs (
  run_code text primary key,
  title text,
  is_open boolean default true,
  created_at timestamptz default now()
);

create table if not exists public.mission_sessions (
  session_id text primary key,
  run_code text not null,
  student_name text not null,
  started_at timestamptz default now(),
  completed_at timestamptz,
  current_stage text,
  taught_score integer default 0,
  taught_max integer default 0,
  math_score integer default 0,
  math_max integer default 0,
  chemistry_score integer default 0,
  chemistry_max integer default 0,
  physics_score integer default 0,
  physics_max integer default 0,
  process_score integer default 0,
  process_max integer default 0,
  process_choice text,
  process_reason text,
  desired_info text,
  confidence_math text,
  confidence_chemistry text,
  confidence_physics text,
  confidence_problem_solving text,
  confidence_units text,
  review_topic text
);

create table if not exists public.mission_responses (
  response_id text primary key,
  session_id text not null,
  run_code text not null,
  student_name text not null,
  question_id text not null,
  section text,
  domain text,
  prompt text,
  response_text text,
  response_json text,
  correct_answer text,
  is_correct boolean,
  points numeric default 0,
  max_points numeric default 0,
  created_at timestamptz default now(),
  constraint mission_responses_session_question_unique unique (session_id, question_id)
);

create index if not exists idx_mission_sessions_run on public.mission_sessions(run_code);
create index if not exists idx_mission_responses_run on public.mission_responses(run_code);
create index if not exists idx_mission_responses_session on public.mission_responses(session_id);

-- Recommended: leave Row Level Security enabled with no public policies if you use
-- a server-side Secret key (or legacy service-role key) in Streamlit Secrets. The key must NEVER be committed to GitHub.
alter table public.mission_runs enable row level security;
alter table public.mission_sessions enable row level security;
alter table public.mission_responses enable row level security;
