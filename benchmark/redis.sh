#!/bin/bash

# Configuration
YCSB_DIR=/home/zyu379/YCSB
DB="redis"
REDIS_HOST="128.105.145.184"
REDIS_PORT="6379"
WORKLOADS=(a b c d e f)
THREADS=(1 4 8 16 32 64)
RESULTS_DIR="results/redis"

# Save original working directory
ORIG_DIR=$(pwd)

mkdir -p "$ORIG_DIR/$RESULTS_DIR"

cd $YCSB_DIR

# Run benchmarks
for workload in "${WORKLOADS[@]}"; do
    for thread in "${THREADS[@]}"; do
        echo "Flushing Redis data before loading workload $workload with $thread threads"
        redis-cli -h $REDIS_HOST -p $REDIS_PORT FLUSHALL

        echo "Loading initial data for workload $workload with $thread threads"
        ./bin/ycsb load $DB -s -P "workloads/workload${workload}" \
            -p "redis.host=$REDIS_HOST" \
            -p "redis.port=$REDIS_PORT" \
            -threads $thread

        OUTPUT_FILE="$ORIG_DIR/$RESULTS_DIR/${DB}_workload${workload}_${thread}threads.txt"
        echo "Running workload $workload with $thread threads"
        ./bin/ycsb run $DB -s -P "workloads/workload${workload}" \
            -p "redis.host=$REDIS_HOST" \
            -p "redis.port=$REDIS_PORT" \
            -threads $thread > "$OUTPUT_FILE"
    done
done