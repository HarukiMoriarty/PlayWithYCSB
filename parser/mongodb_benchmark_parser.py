import os
import re
import argparse
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

def parse_mongodb_result(file_path):
    """Parse a MongoDB YCSB benchmark result file and extract key metrics."""
    metrics = {}
    
    with open(file_path, 'r') as f:
        content = f.read()
        
        # Extract workload and thread count from filename
        filename = os.path.basename(file_path)
        match = re.search(r'mongodb_workload([a-f])_(\d+)threads\.txt', filename)
        if match:
            metrics['workload'] = match.group(1)
            metrics['threads'] = int(match.group(2))
        
        # Extract overall throughput
        throughput_match = re.search(r'\[OVERALL\], Throughput\(ops/sec\), ([\d\.]+)', content)
        if throughput_match:
            metrics['throughput'] = float(throughput_match.group(1))
        
        # Extract operation latencies
        operations = ['READ', 'UPDATE', 'INSERT', 'SCAN', 'READ-MODIFY-WRITE']
        for op in operations:
            # Average latency
            avg_lat_match = re.search(rf'\[{op}\], AverageLatency\(us\), ([\d\.]+)', content)
            if avg_lat_match:
                metrics[f'{op.lower()}_avg_latency'] = float(avg_lat_match.group(1))
            
            # 95th percentile latency
            p95_lat_match = re.search(rf'\[{op}\], 95thPercentileLatency\(us\), ([\d\.]+)', content)
            if p95_lat_match:
                metrics[f'{op.lower()}_p95_latency'] = float(p95_lat_match.group(1))
            
            # 99th percentile latency
            p99_lat_match = re.search(rf'\[{op}\], 99thPercentileLatency\(us\), ([\d\.]+)', content)
            if p99_lat_match:
                metrics[f'{op.lower()}_p99_latency'] = float(p99_lat_match.group(1))
            
            # Operation count
            op_count_match = re.search(rf'\[{op}\], Operations, (\d+)', content)
            if op_count_match:
                metrics[f'{op.lower()}_operations'] = int(op_count_match.group(1))
    
    return metrics

def collect_all_results(results_dir):
    """Collect results from all benchmark files in the directory."""
    results = []
    
    # Find all MongoDB result files
    result_files = list(Path(results_dir).glob('mongodb_workload*_*threads.txt'))
    
    for file_path in result_files:
        try:
            result = parse_mongodb_result(file_path)
            if result:  # Only add if we got valid results
                results.append(result)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    
    return results

def create_throughput_by_workload_chart(results, output_dir):
    """Create a chart showing throughput by workload and thread count."""
    df = pd.DataFrame(results)
    
    # Group by workload
    workloads = sorted(df['workload'].unique())
    thread_counts = sorted(df['threads'].unique())
    
    plt.figure(figsize=(12, 6))
    
    # Width of each bar group
    group_width = 0.8
    # Width of each bar within a group
    bar_width = group_width / len(thread_counts)
    
    # Position of each workload group on x-axis
    workload_positions = np.arange(len(workloads))
    
    # Create bars for each thread count within each workload group
    for i, thread_count in enumerate(thread_counts):
        # Filter data for this thread count
        thread_data = df[df['threads'] == thread_count]
        
        # Get throughput values for each workload
        throughputs = []
        for workload in workloads:
            workload_data = thread_data[thread_data['workload'] == workload]
            if not workload_data.empty:
                throughputs.append(workload_data['throughput'].values[0])
            else:
                throughputs.append(0)
        
        # Calculate position for this set of bars
        positions = workload_positions + (i - len(thread_counts)/2 + 0.5) * bar_width
        
        # Plot bars
        plt.bar(positions, throughputs, width=bar_width, label=f'{thread_count} Threads')
    
    # Set chart labels and title
    plt.xlabel('Workload', fontsize=12)
    plt.ylabel('Throughput (ops/sec)', fontsize=12)
    plt.title('MongoDB YCSB Throughput by Workload and Thread Count', fontsize=14)
    
    # Set x-axis ticks to workload names
    plt.xticks(workload_positions, [f'Workload {w.upper()}' for w in workloads])
    
    # Add legend
    plt.legend(title='Thread Count')
    
    # Add grid for better readability
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Save the figure
    output_path = os.path.join(output_dir, 'mongodb_throughput_by_workload.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved throughput chart to {output_path}")

def create_latency_by_thread_chart(results, output_dir):
    """Create a chart showing average latency by workload and thread count."""
    df = pd.DataFrame(results)
    
    # Group by workload
    workloads = sorted(df['workload'].unique())
    thread_counts = sorted(df['threads'].unique())
    
    plt.figure(figsize=(12, 6))
    
    # Width of each bar group
    group_width = 0.8
    # Width of each bar within a group
    bar_width = group_width / len(thread_counts)
    
    # Position of each workload group on x-axis
    workload_positions = np.arange(len(workloads))
    
    # Create bars for each thread count within each workload group
    for i, thread_count in enumerate(thread_counts):
        # Filter data for this thread count
        thread_data = df[df['threads'] == thread_count]
        
        # Get average read latency values for each workload
        latencies = []
        for workload in workloads:
            workload_data = thread_data[thread_data['workload'] == workload]
            if not workload_data.empty and 'read_avg_latency' in workload_data.columns:
                latencies.append(workload_data['read_avg_latency'].values[0])
            else:
                latencies.append(0)
        
        # Calculate position for this set of bars
        positions = workload_positions + (i - len(thread_counts)/2 + 0.5) * bar_width
        
        # Plot bars
        plt.bar(positions, latencies, width=bar_width, label=f'{thread_count} Threads')
    
    # Set chart labels and title
    plt.xlabel('Workload', fontsize=12)
    plt.ylabel('Average Read Latency (μs)', fontsize=12)
    plt.title('MongoDB YCSB Read Latency by Workload and Thread Count', fontsize=14)
    
    # Set x-axis ticks to workload names
    plt.xticks(workload_positions, [f'Workload {w.upper()}' for w in workloads])
    
    # Add legend
    plt.legend(title='Thread Count')
    
    # Add grid for better readability
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Save the figure
    output_path = os.path.join(output_dir, 'mongodb_read_latency_by_workload.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved read latency chart to {output_path}")

def create_p99_latency_chart(results, output_dir):
    """Create a chart showing P99 latency by workload and thread count."""
    df = pd.DataFrame(results)
    
    # Group by workload
    workloads = sorted(df['workload'].unique())
    thread_counts = sorted(df['threads'].unique())
    
    plt.figure(figsize=(12, 6))
    
    # Width of each bar group
    group_width = 0.8
    # Width of each bar within a group
    bar_width = group_width / len(thread_counts)
    
    # Position of each workload group on x-axis
    workload_positions = np.arange(len(workloads))
    
    # Create bars for each thread count within each workload group
    for i, thread_count in enumerate(thread_counts):
        # Filter data for this thread count
        thread_data = df[df['threads'] == thread_count]
        
        # Get P99 read latency values for each workload
        latencies = []
        for workload in workloads:
            workload_data = thread_data[thread_data['workload'] == workload]
            if not workload_data.empty and 'read_p99_latency' in workload_data.columns:
                latencies.append(workload_data['read_p99_latency'].values[0])
            else:
                latencies.append(0)
        
        # Calculate position for this set of bars
        positions = workload_positions + (i - len(thread_counts)/2 + 0.5) * bar_width
        
        # Plot bars
        plt.bar(positions, latencies, width=bar_width, label=f'{thread_count} Threads')
    
    # Set chart labels and title
    plt.xlabel('Workload', fontsize=12)
    plt.ylabel('P99 Read Latency (μs)', fontsize=12)
    plt.title('MongoDB YCSB P99 Read Latency by Workload and Thread Count', fontsize=14)
    
    # Set x-axis ticks to workload names
    plt.xticks(workload_positions, [f'Workload {w.upper()}' for w in workloads])
    
    # Add legend
    plt.legend(title='Thread Count')
    
    # Add grid for better readability
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Save the figure
    output_path = os.path.join(output_dir, 'mongodb_p99_latency_by_workload.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved P99 latency chart to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Parse MongoDB YCSB benchmark results and generate visualizations')
    parser.add_argument('--results-dir', type=str, default='results/mongodb', 
                        help='Directory containing MongoDB YCSB benchmark result files')
    parser.add_argument('--output-dir', type=str, default='charts', 
                        help='Directory to save generated charts')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Collect all benchmark results
    print(f"Collecting benchmark results from {args.results_dir}...")
    results = collect_all_results(args.results_dir)
    print(f"Found {len(results)} benchmark results")
    
    if not results:
        print("No valid benchmark results found. Exiting.")
        return
    
    # Generate charts
    print("Generating charts...")
    create_throughput_by_workload_chart(results, args.output_dir)
    create_latency_by_thread_chart(results, args.output_dir)
    create_p99_latency_chart(results, args.output_dir)
    
    print("Done!")

if __name__ == "__main__":
    main()