-- create_raw_tables.sql
-- Purpose: Create the warehouse schemas and the bronze-layer tables that scraper.py loads into.
-- dbt builds everything inside analytical_core, so only the schema is created for it here.
-- Safe to re-run: every statement uses IF NOT EXISTS.

CREATE SCHEMA IF NOT EXISTS raw_ingestion;
CREATE SCHEMA IF NOT EXISTS analytical_core;

-- Brand dimension: one row per gas station brand
CREATE TABLE IF NOT EXISTS raw_ingestion.dim_brands (
    brand_id    SERIAL PRIMARY KEY,
    brand_name  VARCHAR(100) NOT NULL UNIQUE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Price fact: one row per brand x fuel type x week, prices kept as raw strings (e.g. '₱93.85')
CREATE TABLE IF NOT EXISTS raw_ingestion.fact_brand_prices (
    price_id              SERIAL PRIMARY KEY,
    ingestion_run_id      UUID NOT NULL,
    brand_id              INTEGER REFERENCES raw_ingestion.dim_brands (brand_id),
    fuel_display_name     VARCHAR(50) NOT NULL,
    fuel_type_slug        VARCHAR(50) NOT NULL,
    current_price         VARCHAR(20) NOT NULL,
    price_unit            VARCHAR(20) DEFAULT 'PHP_per_liter',
    price_trend           VARCHAR(10),
    weekly_change         VARCHAR(20),
    week_date             DATE NOT NULL,
    extraction_timestamp  TIMESTAMP NOT NULL,
    source                VARCHAR(100),
    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Makes weekly loads idempotent: re-running a week inserts nothing
    CONSTRAINT uq_price_per_week UNIQUE (week_date, brand_id, fuel_type_slug)
);
