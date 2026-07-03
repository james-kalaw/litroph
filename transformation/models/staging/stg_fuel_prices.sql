-- stg_fuel_prices.sql
-- Purpose: Clean and type-cast all raw ingestion data.
-- Strips peso symbols from price strings, casts VARCHAR to NUMERIC,
-- and joins the brand dimension table to resolve brand names.
-- This view is always fresh -- it reflects whatever is in fact_brand_prices right now.
 
{{ config(materialized='view') }}
 
SELECT
	f.ingestion_run_id::UUID                      	AS ingestion_run_id,
	f.extraction_timestamp::TIMESTAMP             	AS extraction_timestamp,
	f.week_date::DATE                             	AS week_date,
	f.source,
	b.brand_name                                  	AS brand,
	f.fuel_display_name,
	f.fuel_type_slug,
 
	-- Core cleaning: strip peso symbol and cast to numeric
	REPLACE(f.current_price,  '₱', '')::NUMERIC(8,2)  AS price_php,
 
	f.price_unit,
	f.price_trend,
 
	-- Strip peso symbol from weekly change value
	REPLACE(f.weekly_change, '₱', '')::NUMERIC(8,2)   AS weekly_change_php,
 
	f.created_at                                  	AS ingested_at
 
FROM raw_ingestion.fact_brand_prices f
LEFT JOIN raw_ingestion.dim_brands b
	ON f.brand_id = b.brand_id
 
WHERE f.current_price IS NOT NULL
  AND f.current_price != ''
