#!/bin/bash

# Ensure we are in the root directory
cd "$(dirname "$0")/.."

echo "Generating TypeScript types from Python models..."

# Check if datamodel-code-generator is installed
if ! command -v datamodel-code-generator &> /dev/null
then
    echo "datamodel-code-generator could not be found. Please install it with 'pip install datamodel-code-generator'"
    exit 1
fi

# Define input and output
INPUT_DIR="apps/api/app/models"
OUTPUT_FILE="apps/web/src/types/schema.ts"

# Check if models directory exists
if [ ! -d "$INPUT_DIR" ]; then
    echo "Directory $INPUT_DIR does not exist. Skipping."
    exit 0
fi

# Generate types
datamodel-code-generator --input "$INPUT_DIR" --output "$OUTPUT_FILE" --input-file-type auto --output-model-type pydantic_v2.BaseModel --use-schema-description --field-constraints

echo "Types generated at $OUTPUT_FILE"
