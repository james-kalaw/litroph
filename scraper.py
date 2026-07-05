import os
import json
import boto3
import uuid
import re
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def generate_fuel_slug(display_name):
    """Converts a display name like 'Prem Diesel' into a machine-readable slug 'prem-diesel'."""
    slug = display_name.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    return re.sub(r'[\s-]+', '-', slug)


def lambda_handler(event, context):
    print("Initializing AWS S3 client...")
    s3_client = boto3.client('s3')
    bucket_name = 'litroph-data-lake-james'

    # 1. Generate Global Run Metadata
    ingestion_run_id = str(uuid.uuid4())
    extraction_timestamp = datetime.now().isoformat()
    short_date = datetime.now().strftime('%Y-%m-%d')
    data_source = "gaswatchph.com"
    price_unit = "PHP_per_liter"

    extracted_data = []

    # 2. Run Playwright in Headless Linux Mode
    print("Launching headless Chromium...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--single-process'
            ]
        )
        page = browser.new_page()

        try:
            print("Navigating to target domain...")
            page.goto("https://gaswatchph.com", wait_until="domcontentloaded", timeout=60000)

            print("Waiting for live data table to render (skipping skeleton rows)...")
            page.wait_for_selector("tr:not(.skeleton-row)", timeout=15000)

            html = page.content()
            print("Page content captured. Closing browser early to free memory...")
            browser.close()

            # 3. Parse the captured HTML with BeautifulSoup
            soup_prices = BeautifulSoup(html, 'html.parser')
            table = soup_prices.find('table', class_='brand-summary-table')
            page_text = soup_prices.get_text(separator=' ')

            # 4. ISO 8601 Date Parsing Matrix
            date_match = re.search(
                r'(?:Week of|As of)\s+([A-Za-z]+\s+\d{1,2}(?:\s*[-–]\s*\d{1,2})?,\s+\d{4})',
                page_text
            )
            if date_match:
                active_week_str = date_match.group(1).strip()
                try:
                    if "-" in active_week_str or "–" in active_week_str:
                        clean_str = re.sub(r'\s*[-–]\s*\d+', '', active_week_str)
                        parsed_date = datetime.strptime(clean_str, "%B %d, %Y")
                    else:
                        parsed_date = datetime.strptime(active_week_str, "%B %d, %Y")
                    week_date_iso = parsed_date.strftime("%Y-%m-%d")
                    print(f"Successfully synchronized with database cycle: '{week_date_iso}'")
                except ValueError:
                    week_date_iso = datetime.now().strftime("%Y-%m-%d")
                    print("Warning: Date parse failed. Falling back to execution timestamp.")
            else:
                week_date_iso = datetime.now().strftime("%Y-%m-%d")
                print("Warning: Date banner not located. Falling back to execution timestamp.")

            # 5. Extract Brand x Fuel Type Price Records
            if table:
                headers = [th.text.strip() for th in table.find('thead').find_all('th')]
                tbody = table.find('tbody', id='brandSummaryBody')

                if tbody:
                    for row in tbody.find_all('tr'):
                        cells = row.find_all('td')

                        if len(cells) == len(headers):
                            brand_name = cells[0].text.strip()

                            for i in range(2, len(cells)):
                                fuel_type = headers[i]
                                raw_cell_text = cells[i].text.strip()

                                if raw_cell_text and "N/A" not in raw_cell_text.upper():
                                    match = re.match(
                                        r'^([\d\.]+)(?:([↓↑])\s*([\+\-]?[\d\.]+))?',
                                        raw_cell_text
                                    )

                                    if match:
                                        base_price = match.group(1)
                                        arrow = match.group(2)
                                        change_val = match.group(3)

                                        direction = "STABLE"
                                        if arrow == "↓":
                                            direction = "DOWN"
                                        elif arrow == "↑":
                                            direction = "UP"

                                        clean_change = abs(float(change_val)) if change_val else 0.0

                                        extracted_data.append({
                                            "ingestion_run_id": ingestion_run_id,
                                            "extraction_timestamp": extraction_timestamp,
                                            "source": data_source,
                                            "week_date": week_date_iso,
                                            "brand": brand_name,
                                            "fuel_display_name": fuel_type,
                                            "fuel_type_slug": generate_fuel_slug(fuel_type),
                                            "current_price": f"₱{base_price}",
                                            "price_unit": price_unit,
                                            "price_trend": direction,
                                            "weekly_change": f"₱{clean_change:.2f}"
                                        })

            print(f"Extraction complete: {len(extracted_data)} records parsed from table.")

        except Exception as e:
            print(f"CRITICAL ERROR during scraping execution: {str(e)}")
            raise e
        finally:
            try:
                browser.close()
            except Exception:
                pass

    # 6. The QA Validation Gate
    print("Executing QA Gate verification...")
    if not extracted_data:
        raise ValueError("QA Gate Failed: No data extracted. Aborting S3 stream to prevent empty files.")

    print(f"QA Passed. Successfully extracted {len(extracted_data)} structured records.")

    # 7. Stream Directly to AWS S3 Data Lake
    file_key = f"raw/fuel_prices_{short_date}.json"
    print(f"Streaming payload to s3://{bucket_name}/{file_key}...")

    s3_client.put_object(
        Bucket=bucket_name,
        Key=file_key,
        Body=json.dumps(extracted_data, ensure_ascii=False),
        ContentType='application/json'
    )
    print(f"Successfully archived raw payload to S3: {file_key}")

    
    # 8. RELATIONAL RDS DATA WAREHOUSE INGESTION BRIDGE (PHASE 3)
    try:
        print("Connecting to RDS PostgreSQL instance...")
        conn = psycopg2.connect(
            host=os.environ['DB_HOST'],
            database=os.environ['DB_NAME'],
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD'],
            port=os.environ['DB_PORT']
        )
        print("Connected to RDS. Beginning transactional database ingestion loop...")
        
        with conn.cursor() as cur:
            # Step A: Batch UPSERT unique brands in ONE query
            unique_brands = list({item['brand'] for item in extracted_data})
            execute_values(cur,
                """
                INSERT INTO raw_ingestion.dim_brands (brand_name)
                VALUES %s
                ON CONFLICT (brand_name) DO NOTHING;
                """,
                [(b,) for b in unique_brands]
            )
            
            # Step B: Fetch ALL brand_id mappings in ONE query into a lookup dictionary
            cur.execute(
                "SELECT brand_name, brand_id FROM raw_ingestion.dim_brands WHERE brand_name = ANY(%s);",
                (unique_brands,)
            )
            brand_map = {row[0]: row[1] for row in cur.fetchall()}
            
            # Step C: Batch INSERT all transactional fact rows in ONE execute_values call
            execute_values(cur,
                """
                INSERT INTO raw_ingestion.fact_brand_prices (
                    ingestion_run_id, brand_id, fuel_display_name, fuel_type_slug,
                    current_price, price_unit, price_trend, weekly_change,
                    week_date, extraction_timestamp, source
                )
                VALUES %s
                ON CONFLICT ON CONSTRAINT uq_price_per_week DO NOTHING;
                """,
                [
                    (
                        item['ingestion_run_id'],
                        brand_map[item['brand']],
                        item['fuel_display_name'],
                        item['fuel_type_slug'],
                        item['current_price'],
                        item['price_unit'],
                        item['price_trend'],
                        item['weekly_change'],
                        item['week_date'],
                        item['extraction_timestamp'],
                        item['source']
                    )
                    for item in extracted_data
                ]
            )
            
            # Commit the transactions only if all batch steps cleared successfully
            conn.commit()
            print(f"Relational ingestion complete. Loaded {len(extracted_data)} records into RDS.")
            
    except Exception as db_err:
        if 'conn' in locals() and conn:
            conn.rollback()
        print(f"Database ingestion crashed. Rolling back transactions. Error: {str(db_err)}")
        raise db_err
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            print("Database connection cleanly closed.")

    return {
        'statusCode': 200,
        'body': f"SUCCESS: Scraped, archived to S3, and cleanly batched {len(extracted_data)} records into RDS PostgreSQL warehouse."
    }