-- accounts are the core entity everything else references
CREATE TABLE IF NOT EXISTS accounts (
    id VARCHAR PRIMARY KEY,
    username VARCHAR NOT NULL,
    follower_count INTEGER DEFAULT 0,
    following_count INTEGER DEFAULT 0,
    post_count INTEGER DEFAULT 0,
    risk_score FLOAT DEFAULT 0.0,
    status VARCHAR DEFAULT 'clean',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- every raw event from the simulator lands here
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR REFERENCES accounts(id),
    event_type VARCHAR NOT NULL,
    target_id VARCHAR,
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- every detection result from any layer lands here
CREATE TABLE IF NOT EXISTS flags (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR REFERENCES accounts(id),
    source VARCHAR NOT NULL,
    reason TEXT NOT NULL,
    score FLOAT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ml snapshots stored so we can track behaviour drift over time
CREATE TABLE IF NOT EXISTS feature_vectors (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR REFERENCES accounts(id),
    features JSONB NOT NULL,
    captured_at TIMESTAMPTZ DEFAULT NOW()
);

-- index on account_id and timestamp since we query by these constantly
CREATE INDEX IF NOT EXISTS idx_events_account_id ON events(account_id);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_flags_account_id ON flags(account_id);
CREATE INDEX IF NOT EXISTS idx_flags_score ON flags(score);