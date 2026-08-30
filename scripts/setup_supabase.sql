-- ============================================
-- 🇸🇾 OSINT Syria — Supabase Database Setup
-- ============================================
-- Run this SQL in your Supabase SQL Editor
-- (Dashboard → SQL Editor → New Query → Paste & Run)

-- Create the main events table
CREATE TABLE IF NOT EXISTS osint_events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    
    -- Raw data
    raw_text TEXT NOT NULL,
    source_channel TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    
    -- AI-extracted fields
    event_type TEXT DEFAULT 'unknown',
    summary_ar TEXT,
    summary_en TEXT,
    threat_level TEXT DEFAULT 'low',
    confidence FLOAT DEFAULT 0.0,
    
    -- Geocoding
    location_name TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    governorate TEXT,
    city TEXT,
    
    -- Metadata
    media_urls JSONB DEFAULT '[]'::JSONB,
    source_message_id INTEGER,
    raw_entities JSONB,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- === INDEXES for fast queries ===
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON osint_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_threat ON osint_events(threat_level);
CREATE INDEX IF NOT EXISTS idx_events_type ON osint_events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_governorate ON osint_events(governorate);
CREATE INDEX IF NOT EXISTS idx_events_source ON osint_events(source_channel);
CREATE INDEX IF NOT EXISTS idx_events_coords ON osint_events(latitude, longitude) WHERE latitude IS NOT NULL;

-- Composite index for common dashboard queries
CREATE INDEX IF NOT EXISTS idx_events_time_threat ON osint_events(timestamp DESC, threat_level);

-- === ROW LEVEL SECURITY ===
ALTER TABLE osint_events ENABLE ROW LEVEL SECURITY;

-- Allow public read (for the dashboard)
CREATE POLICY "Public read access" ON osint_events
    FOR SELECT USING (true);

-- Allow inserts from the pipeline (using service role key)
CREATE POLICY "Service role insert" ON osint_events
    FOR INSERT WITH CHECK (true);

-- Allow updates (for enrichments)
CREATE POLICY "Service role update" ON osint_events
    FOR UPDATE USING (true);

-- === VIEWS for dashboard analytics ===
CREATE OR REPLACE VIEW events_summary AS
SELECT
    DATE_TRUNC('hour', timestamp) as hour,
    event_type,
    threat_level,
    governorate,
    COUNT(*) as event_count,
    AVG(confidence) as avg_confidence
FROM osint_events
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY 1, 2, 3, 4
ORDER BY 1 DESC;

-- Active threats view
CREATE OR REPLACE VIEW active_threats AS
SELECT *
FROM osint_events
WHERE threat_level IN ('critical', 'high')
    AND timestamp > NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;

-- === FUNCTION to get stats ===
CREATE OR REPLACE FUNCTION get_threat_stats(hours_back INTEGER DEFAULT 24)
RETURNS TABLE (
    threat_level TEXT,
    event_count BIGINT,
    avg_confidence NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.threat_level,
        COUNT(*) as event_count,
        ROUND(AVG(e.confidence)::NUMERIC, 2) as avg_confidence
    FROM osint_events e
    WHERE e.timestamp > NOW() - (hours_back || ' hours')::INTERVAL
    GROUP BY e.threat_level
    ORDER BY event_count DESC;
END;
$$ LANGUAGE plpgsql;

-- === FUNCTION to get map data ===
CREATE OR REPLACE FUNCTION get_map_events(hours_back INTEGER DEFAULT 24)
RETURNS TABLE (
    id UUID,
    event_type TEXT,
    summary_ar TEXT,
    threat_level TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    location_name TEXT,
    governorate TEXT,
    timestamp TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.id,
        e.event_type,
        e.summary_ar,
        e.threat_level,
        e.latitude,
        e.longitude,
        e.location_name,
        e.governorate,
        e.timestamp
    FROM osint_events e
    WHERE e.timestamp > NOW() - (hours_back || ' hours')::INTERVAL
        AND e.latitude IS NOT NULL
        AND e.longitude IS NOT NULL
    ORDER BY e.timestamp DESC;
END;
$$ LANGUAGE plpgsql;

-- Done! ✅
