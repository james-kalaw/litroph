#!/bin/bash
# run_pipeline.sh: weekly dbt transformation job for the AWS (EC2) deployment.
# The Lambda scraper loads raw data at Tue 14:00 PHT; schedule this after it, e.g. in `crontab -e`:
#   30 6 * * 2 /bin/bash /home/ubuntu/litroph/run_pipeline.sh >> /home/ubuntu/litroph/pipeline.log 2>&1
# (06:30 UTC = Tue 14:30 PHT; EC2 clocks run in UTC.)
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# dbt reads its connection from DB_* environment variables (transformation/profiles.yml)
set -a
source .env
set +a

source .venv/bin/activate
cd transformation
echo "=== $(date -u '+%Y-%m-%d %H:%M:%S UTC') dbt run ==="
dbt run --profiles-dir .
echo "=== dbt test ==="
dbt test --profiles-dir .
