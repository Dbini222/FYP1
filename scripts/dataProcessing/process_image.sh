#!/bin/bash
# Wrapper shell script to execute the Python batch script
# Argument 1 is the batch index passed by Condor

BATCH_INDEX=$1

# Ensure the environment is sourced (e.g., Anaconda or virtual environment)
source /vol/bitbucket/db620/venv/bin/activate

# Change to the script directory
cd /vol/bitbucket/db620/FYP/scripts/dataProcessing

# Run the batch processing Python script
python image_processing.py $BATCH_INDEX
