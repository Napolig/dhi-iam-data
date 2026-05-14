drop table if exists public.profiles; 

create table public.profiles (
  id uuid primary key references auth.users on delete cascade,
  email text unique not null,
  ownermechanism text not null,
  role text not null default 'mechanism_user',
  approved boolean not null default false,
  created_at timestamptz default now()
);