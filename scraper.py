import json
import boto3
import uuid
import re
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
            # CHANGE 1: channel="msedge" removed — Edge is not installed in this
            # container, only Chromium (per Dockerfile: playwright install chromium)
            #
            # CHANGE 2: --disable-web-security replaced with --disable-dev-shm-usage
            # (this was already flagged as FINDING 5 in the notebook — applying it now)
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--single-process'
            ]
        )
        page = browser.new_page()

        try:
            # CHANGE 3: ThreadPoolExecutor wrapper removed — that existed only to
            # solve a Windows + Jupyter event loop conflict that does not exist
            # in this plain Lambda Python process. sync_playwright() runs directly.
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
            # Guard against double-close if browser.close() above already ran
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

    return {
        'statusCode': 200,
        'body': f"SUCCESS: Scraped and uploaded {len(extracted_data)} records to {file_key}"
    }