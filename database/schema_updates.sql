-- For securely storing API keys and other secrets.
-- In your Supabase dashboard, go to the SQL Editor and run this command.
CREATE TABLE secrets (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  key TEXT NOT NULL UNIQUE,
  value TEXT NOT NULL
);

-- IMPORTANT: Enable Row Level Security (RLS) for the secrets table
-- and ensure that NO policies are created. This makes the table
-- accessible only via the `service_role` key from your backend,
-- and completely inaccessible to the public/anon key on the frontend.
ALTER TABLE secrets ENABLE ROW LEVEL SECURITY;

-- After creating the table, insert your Gemini API key:
-- Go to Table Editor -> secrets -> Insert row
-- key: GEMINI_API_KEY
-- value: your_actual_gemini_api_key_here