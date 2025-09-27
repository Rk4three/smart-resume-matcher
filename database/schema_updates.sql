-- For securely storing API keys and other secrets.
CREATE TABLE secrets (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  key TEXT NOT NULL UNIQUE,
  value TEXT NOT NULL
);

-- IMPORTANT: Enable Row Level Security (RLS) for the secrets table
-- and ensure that NO policies are created. This makes the table
-- accessible only via the `service_role` key from your backend.
ALTER TABLE secrets ENABLE ROW LEVEL SECURITY;