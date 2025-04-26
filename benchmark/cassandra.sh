#!/bin/bash

# Configuration
YCSB_DIR=/home/zyu379/YCSB
DB="cassandra2-cql"
HOSTS="128.105.144.87,128.105.144.78,128.105.144.101"
KEYSPACE="ycsb"
WORKLOADS=(a b c d e f)
THREADS=(1 4 8 16 32 64)
REPLICATION_FACTORS=(1 3)
RESULTS_DIR="results/cassandra2/"

# Save original working directory
ORIG_DIR=$(pwd)

mkdir -p "$ORIG_DIR/$RESULTS_DIR"

cd $YCSB_DIR

# Run benchmarks
for rf in "${REPLICATION_FACTORS[@]}"; do
    for workload in "${WORKLOADS[@]}"; do
        for thread in "${THREADS[@]}"; do
            echo "Resetting keyspace for workload $workload with $thread threads and replication factor $rf"
            cqlsh 128.105.144.87 -e "
            DROP KEYSPACE IF EXISTS $KEYSPACE;
            CREATE KEYSPACE $KEYSPACE WITH REPLICATION = {
                'class': 'SimpleStrategy', 
                'replication_factor': $rf
            };
            
            USE $KEYSPACE;

            CREATE TABLE usertable (
                y_id varchar PRIMARY KEY,
                field0 varchar,
                field1 varchar,
                field2 varchar,
                field3 varchar,
                field4 varchar,
                field5 varchar,
                field6 varchar,
                field7 varchar,
                field8 varchar,
                field9 varchar
            );"

            echo "Loading initial data for workload $workload"
            ./bin/ycsb load $DB -s -P "workloads/workload${workload}" \
                -p hosts=$HOSTS \
                -p cassandra.keyspace=$KEYSPACE \
                -threads $thread

            OUTPUT_FILE="$ORIG_DIR/$RESULTS_DIR/${DB}_rf${rf}_workload${workload}_${thread}threads.txt"
            echo "Running workload $workload with $thread threads and replication factor $rf"
            ./bin/ycsb run $DB -s -P "workloads/workload${workload}" \
                -p hosts=$HOSTS \
                -p cassandra.keyspace=$KEYSPACE \
                -threads $thread > "$OUTPUT_FILE"
        done
    done
done