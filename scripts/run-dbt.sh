#!/bin/bash

# Simple DBT runner script that handles protobuf errors gracefully
set +e  # Don't exit on errors

echo "🔄 Running DBT models for Insurance Data Platform..."

cd "$(dirname "$0")/../dbt"

# Function to run DBT command and extract meaningful output
run_dbt_command() {
    local cmd="$1"
    local description="$2"
    
    echo "📦 $description..."
    
    # Run the command and capture meaningful output
    ../insurance-env/bin/dbt $cmd --profiles-dir profiles 2>&1 | \
        grep -E "(Running with dbt|Registered adapter|Found [0-9]+ models|START sql|OK created|ERROR creating|SKIP|Finished running|Done\.|Database Error|Compilation Error)" | \
        grep -v "TypeError\|including_default_value_fields\|MessageToJson" || true
        
    echo ""
}

# Install dependencies
run_dbt_command "deps" "Installing DBT package dependencies"

# Run models
run_dbt_command "run" "Running DBT models"

echo "✅ DBT execution completed!"
echo ""
echo "🔍 To debug issues:"
echo "   cd dbt && ../insurance-env/bin/dbt debug --profiles-dir profiles"
echo ""
echo "📊 To view results:"
echo "   - Check PostgreSQL: docker exec insurance-postgres psql -U insurance_user -d insurance_db"
echo "   - List staging views: \\dt staging.*"
echo "   - Query data: SELECT * FROM staging.stg_customers LIMIT 5;"