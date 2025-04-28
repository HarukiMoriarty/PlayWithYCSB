import argparse
import os
from ycsb_parser_utils import (
    collect_all_results,
    create_throughput_by_workload_chart,
    create_latency_by_thread_chart,
    create_p99_latency_chart
)

def main():
    parser = argparse.ArgumentParser(description='Parse Cassandra YCSB benchmark results and generate visualizations')
    parser.add_argument('--results-dir', type=str, default='results/cassandra2', 
                        help='Directory containing Cassandra YCSB benchmark result files')
    parser.add_argument('--output-dir', type=str, default='charts', 
                        help='Directory to save generated charts')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Cassandra filename pattern: cassandra2-cql_rf1_workloada_4threads.txt
    # Groups: 1=rf, 2=workload, 3=threads
    cassandra_pattern = r'cassandra2-cql_rf(\d+)_workload([a-f])_(\d+)threads\.txt'
    
    # Collect all benchmark results
    print(f"Collecting benchmark results from {args.results_dir}...")
    results = collect_all_results(args.results_dir, 'cassandra2-cql', cassandra_pattern)
    print(f"Found {len(results)} benchmark results")
    
    if not results:
        print("No valid benchmark results found. Exiting.")
        return
    
    # Generate charts
    print("Generating charts...")
    create_throughput_by_workload_chart(results, args.output_dir, 'cassandra2-cql')
    create_latency_by_thread_chart(results, args.output_dir, 'cassandra2-cql')
    create_p99_latency_chart(results, args.output_dir, 'cassandra2-cql')
    
    print("Done!")

if __name__ == "__main__":
    main()
