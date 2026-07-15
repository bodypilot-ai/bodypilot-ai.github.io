-- ============================================================
-- physician_scores：医生盲评（一行 = 一位评审 × 一个病例 × 一份报告 A/B）
-- 6维配对评测（2026-07-15）。整段粘到 Supabase → SQL Editor 运行即可（可重复跑）。
-- 项目：wmacfrwnkaobqebzdnze
-- ============================================================

-- 1) 表不存在则按新 schema 建（已存在则跳过，不覆盖旧数据）
create table if not exists public.physician_scores (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz default now(),
  rater_id text not null,
  rater_name text,
  rater_years numeric,
  batch text,
  case_code text not null,
  candidate_label text not null,
  dim_correctness int,
  dim_consistency int,
  dim_personalization int,
  dim_actionability int,
  dim_safety int,
  dim_clarity int,
  dim_appropriateness int,          -- 旧列，本轮不用，留空
  unsafe_flag boolean default false,
  preference text,
  comment text
);

-- 2) 表已存在（旧 schema）时补齐本轮新增列
alter table public.physician_scores add column if not exists rater_name text;
alter table public.physician_scores add column if not exists rater_years numeric;
alter table public.physician_scores add column if not exists batch text;
alter table public.physician_scores add column if not exists dim_correctness int;
alter table public.physician_scores add column if not exists dim_consistency int;
alter table public.physician_scores add column if not exists preference text;

-- 3) RLS：只允许匿名 insert（沿用旧策略；不开 select，别人读不到分）
alter table public.physician_scores enable row level security;
drop policy if exists "anon_insert_only" on public.physician_scores;
create policy "anon_insert_only" on public.physician_scores
  for insert to anon with check (true);

-- ------------------------------------------------------------
-- 网页发的字段：rater_id, batch, case_code(=C01..C30), candidate_label(A/B),
--   dim_correctness, dim_consistency, dim_personalization, dim_actionability,
--   dim_safety, dim_clarity, unsafe_flag, preference, comment
-- 普通 insert；评审多次提交会多插行，分析时按 created_at 取每
--   (rater_id, case_code, candidate_label) 最新一行去重（建议评审最后一次性提交）。
-- ------------------------------------------------------------
