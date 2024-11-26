#!/bin/bash

# Load environment variables from .env file
set -a
source .env
set +a

# Verify keys are loaded
echo "Checking environment variables..."
REQUIRED_KEYS=(
    "GOOGLE_API_KEY"
    "GOOGLE_MAPS_API_KEY"
    "GOOGLE_CSE_ID"
    "ASANA_ACCESS_TOKEN"
)

MISSING_KEYS=0
for KEY in "${REQUIRED_KEYS[@]}"; do
    if [ -z "${!KEY}" ]; then
        echo "❌ Missing: $KEY"
        MISSING_KEYS=1
    else
        echo "✅ Found: $KEY"
    fi
done

if [ $MISSING_KEYS -eq 1 ]; then
    echo -e "\n⚠️  Some required keys are missing. Please check .env file."
else
    echo -e "\n✅ All required keys are set!"
fi
