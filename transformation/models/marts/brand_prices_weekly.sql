-- brand_prices_weekly.sql
-- Purpose: Individual brand price per fuel type per week.
-- Powers: Streamlit Chart 2 (brand ranking bar chart)
--     	and get_specific_brand_price() lookup in the route optimizer.
 
{{ config(materialized='table') }}
 
SELECT
	week_date,
	brand,
	fuel_display_name,
	fuel_type_slug,
	price_php,
	price_trend,
	weekly_change_php,
	source
 
FROM {{ ref('stg_fuel_prices') }}
 
ORDER BY
	week_date DESC,
	fuel_display_name,
	price_php ASC
