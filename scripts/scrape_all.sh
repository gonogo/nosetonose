#!/usr/bin/env bash
# Run the full structured scrape (legacy + WordPress + current courses).
set -euo pipefail
cd "$(dirname "$0")"
# shellcheck disable=SC1091
source .venv/bin/activate

scrapy crawl legacy
scrapy crawl wordpress
scrapy crawl courses

echo
echo "Export complete. See data/*.json and data/bodies/"
echo "Next: python scripts/extract_structured.py && python scripts/build_web.py"
echo "Preview: python3 -m http.server --directory web 8080"
echo "  Courses: http://localhost:8080/"
echo "  People:  http://localhost:8080/people.html"
echo "  Other:   http://localhost:8080/other-content.html"
ls -la data/*.json
