#!/bin/bash

# Burmese Corpus Scraper - Run All Sites
# This script runs all configured sites with full scraping and ignores robots.txt
# Edit this file to add/remove sites as needed

echo "🚀 Starting Burmese Corpus Scraper - All Sites"
echo "=============================================="

# List of sites to scrape with their primary categories (edit this list to add/remove sites)
# Format: "site_name:category"
SITES=(
    "voa_burmese:news"
    "bbc_burmese:myanmar" 
    "rfa_burmese:interview"
    "irrawaddy_burmese:news"
    "myanmar_now:news"
    "myanmar_national_portal:news"
    "duwun_news:news"
    "isec_myanmar:blog"
    "foodindustrydirectory:thaifood"
)

# Common parameters for all sites
COMMON_PARAMS="--ignore-robots --log-level INFO"

# Function to run a single site
run_site() {
    local site_config=$1
    
    # Split site:category
    IFS=':' read -ra SITE_PARTS <<< "$site_config"
    local site="${SITE_PARTS[0]}"
    local category="${SITE_PARTS[1]}"
    
    echo ""
    echo "📰 Processing: $site (category: $category)"
    echo "----------------------------------------"
    
    # Run the scraper for this site and category
    python3 -m scraper.main --site "$site" --category "$category" $COMMON_PARAMS
    
    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        echo "✅ $site/$category completed successfully"
    else
        echo "❌ $site/$category failed with exit code $exit_code"
    fi
    
    echo "----------------------------------------"
}

# Main execution
echo "Sites to process: ${#SITES[@]}"
echo "Sites: ${SITES[*]}"
echo ""

# Process each site
for site_config in "${SITES[@]}"; do
    run_site "$site_config"
done

echo ""
echo "🎉 All sites processing completed!"
echo "Check the data/raw/ directory for output files"
echo "Check the logs/ directory for detailed logs"
