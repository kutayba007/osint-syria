-- OSINT Syria — Fix Row Level Security
-- Run this in Supabase SQL Editor

-- Option 1: Disable RLS (simplest for backend-only access)
ALTER TABLE events DISABLE ROW LEVEL SECURITY;

-- Option 2 (if Option 1 fails): Create permissive policies
-- ALTER TABLE events ENABLE ROW LEVEL SECURITY;
-- 
-- CREATE POLICY "Allow all operations for service role" ON events
--   FOR ALL
--   USING (true)
--   WITH CHECK (true);
