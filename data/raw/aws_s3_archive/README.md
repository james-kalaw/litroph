# AWS S3 raw archive (Version 1)

Every raw payload the AWS Lambda scraper wrote to `s3://litroph-data-lake-james/raw/`
between June 30 and October 27, 2026: 29 files of 54 records each, copied here unchanged
before the AWS deployment was shut down.

File names use the **scrape date**; the `week_date` field inside each record is the price week
GasWatch PH was showing. Some files repeat a week (for example, the July 21 and July 24 runs both
returned the week of July 14, because GasWatch PH did not publish a separate July 21 week).
The warehouse keeps one copy of each week thanks to the `uq_price_per_week` constraint.

Newer raw files are written to `data/raw/` by the GitHub Actions pipeline (Version 2).
