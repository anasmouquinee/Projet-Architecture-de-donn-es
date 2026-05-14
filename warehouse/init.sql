-- SQL Schema

-- Article Table
CREATE TABLE IF NOT EXISTS articles (
    id              SERIAL PRIMARY KEY,
    title           TEXT NOT NULL,
    author          TEXT,
    published_date  TIMESTAMP,
    category        TEXT,
    content_preview TEXT,                -- Content Preview
    source          VARCHAR(50) NOT NULL,
    url             TEXT UNIQUE NOT NULL,
    language        VARCHAR(10),
    quality_score   SMALLINT DEFAULT 0,  -- Quality Score
    scraped_at      TIMESTAMP NOT NULL,
    loaded_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily Stats
CREATE TABLE IF NOT EXISTS daily_stats (
    id              SERIAL PRIMARY KEY,
    stat_date       DATE NOT NULL,
    source          VARCHAR(50) NOT NULL,
    category        TEXT,
    country         VARCHAR(50),
    article_count   INTEGER DEFAULT 0,
    UNIQUE(stat_date, source, category)
);

-- Top Keywords
CREATE TABLE IF NOT EXISTS top_keywords (
    id              SERIAL PRIMARY KEY,
    stat_date       DATE NOT NULL,
    keyword         TEXT NOT NULL,
    frequency       INTEGER DEFAULT 0,
    source          VARCHAR(50),
    UNIQUE(stat_date, keyword, source)
);

-- Source Stats
CREATE TABLE IF NOT EXISTS source_stats (
    id                  SERIAL PRIMARY KEY,
    source              VARCHAR(50) UNIQUE NOT NULL,
    country             VARCHAR(50),
    total_articles      INTEGER DEFAULT 0,
    avg_daily_articles  NUMERIC(10,2) DEFAULT 0,
    last_scraped_at     TIMESTAMP
);

-- Database Indices
CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
CREATE INDEX IF NOT EXISTS idx_articles_date ON articles(published_date);
CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category);
CREATE INDEX IF NOT EXISTS idx_articles_language ON articles(language);
CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(stat_date);
CREATE INDEX IF NOT EXISTS idx_top_keywords_date ON top_keywords(stat_date);
