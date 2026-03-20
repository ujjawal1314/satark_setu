create table if not exists accounts (
  account_id text primary key,
  name text,
  risk_score int not null default 0,
  status text not null default 'ACTIVE' check (status in ('ACTIVE', 'FROZEN', 'UNDER_REVIEW')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists transactions (
  txn_id text primary key,
  from_account text not null,
  to_account text not null,
  amount numeric(14,2) not null,
  timestamp timestamptz not null default now(),
  status text not null check (status in ('APPROVED', 'BLOCKED')),
  risk_score int not null default 0
);

create table if not exists account_actions (
  id bigint generated always as identity primary key,
  account_id text not null,
  action_type text not null check (action_type in ('FREEZE', 'UNFREEZE')),
  reason text,
  performed_by text,
  timestamp timestamptz not null default now()
);

create index if not exists idx_accounts_status on accounts(status);
create index if not exists idx_transactions_status on transactions(status);
create index if not exists idx_transactions_from_account on transactions(from_account);
create index if not exists idx_actions_account on account_actions(account_id);

create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_accounts_updated_at on accounts;
create trigger trg_accounts_updated_at
before update on accounts
for each row execute function set_updated_at();
