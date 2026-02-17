#!/bin/bash
# Run tests with resource limits

echo "Setting resource limits..."
# Max 2GB virtual memory
ulimit -v 2097152
# Max 2GB resident memory  
ulimit -m 2097152
# Max 60 seconds CPU time
ulimit -t 60

echo "Running safe test..."
cd /root/trendscope
source .venv/bin/activate
python test_combo_safe.py
