#!/bin/bash
source .venv/bin/activate
echo "Running Pilot (Resume)..."
python -m experiments.benchmark_runner --mode pilot --resume
echo "Running Full (Resume)..."
python -m experiments.benchmark_runner --mode full --resume
echo "Done!"
