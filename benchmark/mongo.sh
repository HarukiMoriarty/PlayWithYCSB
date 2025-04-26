#!/bin/bash

# Configuration
YCSB_DIR=/home/zyu379/YCSB
DB="mongodb"
MONGODB_URL="mongodb://128.105.145.227,128.105.145.228,128.105.145.229/ycsbdb?replicaSet=rs0"
WORKLOADS=(a b c d e f)
THREADS=(1 4 8 16 32 64)
RESULTS_DIR="results/mongodb"

# Save original working directory
ORIG_DIR=$(pwd)

mkdir -p "$ORIG_DIR/$RESULTS_DIR"

cd $YCSB_DIR

# Run benchmarks
for workload in "${WORKLOADS[@]}"; do
    for thread in "${THREADS[@]}"; do
        echo "Dropping ycsbdb database before loading workload $workload with $thread threads"
        mongosh "$MONGODB_URL" --eval "db.getSiblingDB('ycsbdb').dropDatabase()"

        echo "Loading initial data for workload $workload with $thread threads"
        ./bin/ycsb load $DB -s -P "workloads/workload${workload}" \
            -p "mongodb.url=$MONGODB_URL" \
            -threads $thread

        OUTPUT_FILE="$ORIG_DIR/$RESULTS_DIR/${DB}_workload${workload}_${thread}threads.txt"
        echo "Running workload $workload with $thread threads"
        ./bin/ycsb run $DB -s -P "workloads/workload${workload}" \
            -p "mongodb.url=$MONGODB_URL" \
            -threads $thread > "$OUTPUT_FILE"
    done
done
