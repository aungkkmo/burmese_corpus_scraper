#!/bin/bash

# Burmese Corpus Scraper - Advanced All Sites Runner
# This script runs all configured sites with category support and better error handling
# Usage: ./run_all_sites_advanced.sh [max_pages]

echo "🚀 Starting Burmese Corpus Scraper - All Sites (Advanced)"
echo "=========================================================="

# Get max pages from command line argument (default: unlimited)
MAX_PAGES=${1:-""}
if [ -n "$MAX_PAGES" ]; then
    MAX_PAGES_PARAM="--max-pages $MAX_PAGES"
    echo "📄 Max pages per site: $MAX_PAGES"
else
    MAX_PAGES_PARAM=""
    echo "📄 Max pages per site: unlimited"
fi

# Site configurations: site_name:category1,category2,category3
# Edit this array to add/remove sites and their categories
declare -A SITE_CONFIGS=(
    ["voa_burmese"]="news"
    ["bbc_burmese"]="earthquake,myanmar,article,interview,trade"
    ["rfa_burmese"]="interview,talkshow,multimedia"
    ["irrawaddy_burmese"]="news,article,business,opinion,lifestyle,women_in_media,laborrights,election_2020"
    ["myanmar_now"]="news,in_depth,opinion,multimedia"
    ["myanmar_national_portal"]="news"
    ["duwun_news"]="news"
    ["isec_myanmar"]="blog"
)

# Common parameters for all sites
COMMON_PARAMS="--ignore-robots --log-level INFO $MAX_PAGES_PARAM"

# Counters
TOTAL_SITES=0
SUCCESSFUL_SITES=0
FAILED_SITES=0

# Function to run a single site with all its categories
run_site() {
    local site=$1
    local categories=$2
    
    echo ""
    echo "📰 Processing: $site"
    echo "📂 Categories: $categories"
    echo "----------------------------------------"
    
    # Convert comma-separated categories to array
    IFS=',' read -ra CATEGORY_ARRAY <<< "$categories"
    
    local site_success=true
    
    # Run each category for this site
    for category in "${CATEGORY_ARRAY[@]}"; do
        echo "  🔹 Category: $category"
        
        # Run the scraper for this site and category
        python3 -m scraper.main --site "$site" --category "$category" $COMMON_PARAMS
        
        local exit_code=$?
        if [ $exit_code -eq 0 ]; then
            echo "  ✅ $site/$category completed successfully"
        else
            echo "  ❌ $site/$category failed with exit code $exit_code"
            site_success=false
        fi
    done
    
    if [ "$site_success" = true ]; then
        echo "✅ $site completed successfully (all categories)"
        ((SUCCESSFUL_SITES++))
    else
        echo "⚠️  $site completed with some failures"
        ((FAILED_SITES++))
    fi
    
    ((TOTAL_SITES++))
    echo "----------------------------------------"
}

# Main execution
echo "Sites configured: ${#SITE_CONFIGS[@]}"
echo ""

# Process each site
for site in "${!SITE_CONFIGS[@]}"; do
    run_site "$site" "${SITE_CONFIGS[$site]}"
done

echo ""
echo "🎉 All sites processing completed!"
echo "📊 Summary:"
echo "   Total sites: $TOTAL_SITES"
echo "   Successful: $SUCCESSFUL_SITES"
echo "   Failed: $FAILED_SITES"
echo ""
echo "📁 Check the data/raw/ directory for output files"
echo "📋 Check the logs/ directory for detailed logs"
