#!/bin/bash

# Configuration
YCSB_DIR=/home/zyu379/YCSB
DB="zookeeper"
ZK_CONNECT_STRING="128.105.145.213:2181,128.105.145.217:2181,128.105.145.209:2181/benchmark"
WORKLOAD="b"
THREADS=(1 4 8 16 32 64)
RESULTS_DIR="results/zookeeper"

# Save original working directory
ORIG_DIR=$(pwd)

mkdir -p "$ORIG_DIR/$RESULTS_DIR"

cd $YCSB_DIR

# Load initial data once
echo "Loading initial data for workload $WORKLOAD"
./bin/ycsb load $DB -s -P "workloads/workload${WORKLOAD}" \
    -p "zookeeper.connectString=$ZK_CONNECT_STRING" \
    -threads 1

# Run benchmarks
for thread in "${THREADS[@]}"; do
    OUTPUT_FILE="$ORIG_DIR/$RESULTS_DIR/${DB}_workload${WORKLOAD}_${thread}threads.txt"
    echo "Running workload $WORKLOAD with $thread threads"
    ./bin/ycsb run $DB -s -P "workloads/workload${WORKLOAD}" \
        -p "zookeeper.connectString=$ZK_CONNECT_STRING" \
        -threads $thread > "$OUTPUT_FILE"
done