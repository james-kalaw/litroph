-- fuel_prices_weekly.sql
-- Purpose: Weekly mean market price aggregated per fuel type.
-- Powers: Streamlit Chart 1 (price trend line chart)
--     	and the core route cost formula (price_avg per liter).
 
{{ config(materialized='table') }}
 
SELECT
	week_date,
	fuel_display_name,
	fuel_type_slug,
	ROUND(MIN(price_php), 2)	AS price_min,
	ROUND(MAX(price_php), 2)	AS price_max,
	ROUND(AVG(price_php), 2)	AS price_avg,
	COUNT(DISTINCT brand)   	AS brand_count
 
FROM {{ ref('stg_fuel_prices') }}
 
GROUP BY
	week_date,
	fuel_display_name,
	fuel_type_slug
 
ORDER BY week_date DESC, fuel_display_name
