import argparse
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from ycsb_parser_utils import collect_all_results

def collect_all_db_results(db_dirs):
    """Collect results from all databases."""
    all_results = {}
    
    # Cassandra pattern
    cassandra_pattern = r'cassandra2-cql_rf(\d+)_workload([a-f])_(\d+)threads\.txt'
    
    # Define databases and their patterns
    db_configs = [
        ('mongodb', db_dirs.get('mongodb', 'results/mongodb'), None),
        ('redis', db_dirs.get('redis', 'results/redis'), None),
        ('cassandra2-cql', db_dirs.get('cassandra', 'results/cassandra2'), cassandra_pattern)
    ]
    
    for db_name, results_dir, pattern in db_configs:
        if os.path.exists(results_dir):
            print(f"Collecting {db_name} results from {results_dir}...")
            results = collect_all_results(results_dir, db_name, pattern)
            if results:
                all_results[db_name] = pd.DataFrame(results)
                print(f"Found {len(results)} {db_name} benchmark results")
            else:
                print(f"No valid {db_name} benchmark results found.")
        else:
            print(f"Skipping {db_name}: directory {results_dir} does not exist")
    
    return all_results

def create_throughput_comparison_chart(all_results, output_dir, thread_count=16):
    """Create a chart comparing throughput across databases for a specific thread count."""
    plt.figure(figsize=(14, 8))
    
    # Get common workloads across all databases
    all_workloads = set()
    for db_name, df in all_results.items():
        if 'workload' in df.columns:
            all_workloads.update(df['workload'].unique())
    
    workloads = sorted(all_workloads)
    
    # Position for each workload group on x-axis
    workload_positions = np.arange(len(workloads))
    
    # Width of each bar group
    group_width = 0.8
    # Number of databases
    num_dbs = len(all_results)
    # Width of each bar within a group
    bar_width = group_width / num_dbs
    
    # Colors for each database
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    # Create bars for each database
    for i, (db_name, df) in enumerate(all_results.items()):
        # For Cassandra, we'll use RF=3 for comparison (or RF=1 if 3 is not available)
        if db_name == 'cassandra2-cql' and 'rf' in df.columns:
            if 3 in df['rf'].values:
                df = df[df['rf'] == 3]
            elif 1 in df['rf'].values:
                df = df[df['rf'] == 1]
        
        # Filter data for the specified thread count
        if 'threads' in df.columns:
            thread_data = df[df['threads'] == thread_count]
        else:
            thread_data = df
        
        # Get throughput values for each workload
        throughputs = []
        for workload in workloads:
            if 'workload' in thread_data.columns:
                workload_data = thread_data[thread_data['workload'] == workload]
                if not workload_data.empty and 'throughput' in workload_data.columns:
                    throughputs.append(workload_data['throughput'].values[0])
                else:
                    throughputs.append(0)
            else:
                throughputs.append(0)
        
        # Calculate position for this set of bars
        positions = workload_positions + (i - num_dbs/2 + 0.5) * bar_width
        
        # Format database name for display
        display_name = db_name
        if db_name == 'cassandra2-cql':
            if 'rf' in df.columns and not df.empty:
                rf = df['rf'].iloc[0]
                display_name = f'Cassandra (RF={rf})'
            else:
                display_name = 'Cassandra'
        
        # Plot bars
        plt.bar(positions, throughputs, width=bar_width, label=display_name, color=colors[i % len(colors)])
    
    # Set chart labels and title
    plt.xlabel('Workload', fontsize=14)
    plt.ylabel('Throughput (ops/sec)', fontsize=14)
    plt.title(f'Database Throughput Comparison ({thread_count} Threads)', fontsize=16)
    
    # Set x-axis ticks to workload names
    plt.xticks(workload_positions, [f'Workload {w.upper()}' for w in workloads], fontsize=12)
    
    # Add legend
    plt.legend(fontsize=12)
    
    # Add grid for better readability
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Save the figure
    output_path = os.path.join(output_dir, f'db_comparison_throughput_{thread_count}threads.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved throughput comparison chart to {output_path}")

def create_latency_comparison_chart(all_results, output_dir, thread_count=16, metric='read_avg_latency'):
    """Create a chart comparing latency across databases for a specific thread count."""
    plt.figure(figsize=(14, 8))
    
    # Get common workloads across all databases
    all_workloads = set()
    for db_name, df in all_results.items():
        if 'workload' in df.columns:
            all_workloads.update(df['workload'].unique())
    
    workloads = sorted(all_workloads)
    
    # Position for each workload group on x-axis
    workload_positions = np.arange(len(workloads))
    
    # Width of each bar group
    group_width = 0.8
    # Number of databases
    num_dbs = len(all_results)
    # Width of each bar within a group
    bar_width = group_width / num_dbs
    
    # Colors for each database
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    # Create bars for each database
    for i, (db_name, df) in enumerate(all_results.items()):
        # For Cassandra, we'll use RF=3 for comparison (or RF=1 if 3 is not available)
        if db_name == 'cassandra2-cql' and 'rf' in df.columns:
            if 3 in df['rf'].values:
                df = df[df['rf'] == 3]
            elif 1 in df['rf'].values:
                df = df[df['rf'] == 1]
        
        # Filter data for the specified thread count
        if 'threads' in df.columns:
            thread_data = df[df['threads'] == thread_count]
        else:
            thread_data = df
        
        # Get latency values for each workload
        latencies = []
        for workload in workloads:
            if 'workload' in thread_data.columns:
                workload_data = thread_data[thread_data['workload'] == workload]
                if not workload_data.empty and metric in workload_data.columns:
                    latencies.append(workload_data[metric].values[0])
                else:
                    latencies.append(0)
            else:
                latencies.append(0)
        
        # Calculate position for this set of bars
        positions = workload_positions + (i - num_dbs/2 + 0.5) * bar_width
        
        # Format database name for display
        display_name = db_name
        if db_name == 'cassandra2-cql':
            if 'rf' in df.columns and not df.empty:
                rf = df['rf'].iloc[0]
                display_name = f'Cassandra (RF={rf})'
            else:
                display_name = 'Cassandra'
        
        # Plot bars
        plt.bar(positions, latencies, width=bar_width, label=display_name, color=colors[i % len(colors)])
    
    # Set chart labels and title
    plt.xlabel('Workload', fontsize=14)
    
    metric_name = "Average Read Latency"
    if metric == 'read_p99_latency':
        metric_name = "P99 Read Latency"
    
    plt.ylabel(f'{metric_name} (μs)', fontsize=14)
    plt.title(f'Database {metric_name} Comparison ({thread_count} Threads)', fontsize=16)
    
    # Set x-axis ticks to workload names
    plt.xticks(workload_positions, [f'Workload {w.upper()}' for w in workloads], fontsize=12)
    
    # Add legend
    plt.legend(fontsize=12)
    
    # Add grid for better readability
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Save the figure
    metric_short = "avg" if metric == 'read_avg_latency' else "p99"
    output_path = os.path.join(output_dir, f'db_comparison_{metric_short}_latency_{thread_count}threads.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved {metric_name} comparison chart to {output_path}")

def create_throughput_scaling_chart(all_results, output_dir, workload='a'):
    """Create a chart showing how throughput scales with thread count for a specific workload."""
    plt.figure(figsize=(12, 8))
    
    # Colors for each database
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    markers = ['o', 's', '^', 'D']
    
    # For each database, plot throughput vs thread count
    for i, (db_name, df) in enumerate(all_results.items()):
        # For Cassandra, we'll use RF=3 for comparison (or RF=1 if 3 is not available)
        if db_name == 'cassandra2-cql' and 'rf' in df.columns:
            if 3 in df['rf'].values:
                df = df[df['rf'] == 3]
            elif 1 in df['rf'].values:
                df = df[df['rf'] == 1]
        
        # Filter data for the specified workload
        if 'workload' in df.columns:
            workload_data = df[df['workload'] == workload]
        else:
            workload_data = df
        
        if not workload_data.empty and 'threads' in workload_data.columns and 'throughput' in workload_data.columns:
            # Group by thread count and calculate mean throughput
            thread_groups = workload_data.groupby('threads')['throughput'].mean().reset_index()
            
            # Sort by thread count
            thread_groups = thread_groups.sort_values('threads')
            
            # Format database name for display
            display_name = db_name
            if db_name == 'cassandra2-cql':
                if 'rf' in df.columns and not df.empty:
                    rf = df['rf'].iloc[0]
                    display_name = f'Cassandra (RF={rf})'
                else:
                    display_name = 'Cassandra'
            
            # Plot line
            plt.plot(thread_groups['threads'], thread_groups['throughput'], 
                     marker=markers[i % len(markers)], markersize=8, 
                     color=colors[i % len(colors)], linewidth=2, 
                     label=display_name)
    
    # Set chart labels and title
    plt.xlabel('Number of Threads', fontsize=22)
    plt.ylabel('Throughput (ops/sec)', fontsize=22)
    plt.title(f'Database Throughput Scaling (Workload {workload.upper()})', fontsize=24)
    
    # Set x-axis to log scale for better visualization
    plt.xscale('log', base=2)
    
    # Add grid
    plt.grid(True, which="both", ls="-", alpha=0.7)
    
    # Add legend
    plt.legend(fontsize=12)
    
    # Save the figure
    output_path = os.path.join(output_dir, f'db_throughput_scaling_workload{workload}.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    
    # Also save as PDF
    pdf_output_path = os.path.join(output_dir, f'db_throughput_scaling_workload{workload}.pdf')
    plt.savefig(pdf_output_path, format='pdf', bbox_inches='tight')
    plt.close()
    
    print(f"Saved throughput scaling chart to {output_path}")

def create_latency_scaling_chart(all_results, output_dir, workload='a', metric='read_avg_latency'):
    """Create a chart showing how latency scales with thread count for a specific workload."""
    plt.figure(figsize=(14, 8))
    
    # Markers and colors for different databases
    markers = ['o', 's', '^', 'D']
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    # For each database, plot latency vs thread count
    for i, (db_name, df) in enumerate(all_results.items()):
        # For Cassandra, we'll use RF=3 for comparison (or RF=1 if 3 is not available)
        if db_name == 'cassandra2-cql' and 'rf' in df.columns:
            if 3 in df['rf'].values:
                df = df[df['rf'] == 3]
            elif 1 in df['rf'].values:
                df = df[df['rf'] == 1]
        
        # Filter data for the specified workload
        if 'workload' in df.columns:
            workload_data = df[df['workload'] == workload]
        else:
            workload_data = df
        
        if not workload_data.empty and 'threads' in workload_data.columns and metric in workload_data.columns:
            # Group by thread count and calculate mean latency
            thread_groups = workload_data.groupby('threads')[metric].mean().reset_index()
            
            # Sort by thread count
            thread_groups = thread_groups.sort_values('threads')
            
            # Format database name for display
            display_name = db_name
            if db_name == 'cassandra2-cql':
                if 'rf' in df.columns and not df.empty:
                    rf = df['rf'].iloc[0]
                    display_name = f'Cassandra (RF={rf})'
                else:
                    display_name = 'Cassandra'
            
            # Plot line
            plt.plot(thread_groups['threads'], thread_groups[metric], 
                     marker=markers[i % len(markers)], markersize=8, 
                     color=colors[i % len(colors)], linewidth=2, 
                     label=display_name)
    
    # Set chart labels and title
    plt.xlabel('Number of Threads', fontsize=22)
    
    metric_name = "Average Read Latency"
    if metric == 'read_p99_latency':
        metric_name = "P99 Read Latency"
    
    plt.ylabel(f'{metric_name} (μs)', fontsize=22)
    plt.title(f'Database {metric_name} Scaling (Workload {workload.upper()})', fontsize=24)
    plt.xticks(fontsize=22)
    plt.yticks(fontsize=22)
    
    # Set x-axis to log scale for better visualization
    plt.xscale('log', base=2)
    
    # Add grid
    plt.grid(True, which="both", ls="-", alpha=0.7)
    
    # Add legend
    plt.legend(fontsize=22)
    
    # Save the figure
    metric_short = "avg" if metric == 'read_avg_latency' else "p99"
    output_path = os.path.join(output_dir, f'db_latency_{metric_short}_scaling_workload{workload}.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    
    # Also save as PDF
    pdf_output_path = os.path.join(output_dir, f'db_latency_{metric_short}_scaling_workload{workload}.pdf')
    plt.savefig(pdf_output_path, format='pdf', bbox_inches='tight')
    plt.close()
    
    print(f"Saved {metric_name} scaling chart to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Compare performance across different databases')
    parser.add_argument('--mongodb-dir', type=str, default='results/mongodb', 
                        help='Directory containing MongoDB YCSB benchmark result files')
    parser.add_argument('--redis-dir', type=str, default='results/redis', 
                        help='Directory containing Redis YCSB benchmark result files')
    parser.add_argument('--cassandra-dir', type=str, default='results/cassandra2', 
                        help='Directory containing Cassandra YCSB benchmark result files')
    parser.add_argument('--output-dir', type=str, default='charts/comparison', 
                        help='Directory to save generated comparison charts')
    parser.add_argument('--threads', type=int, nargs='+', default=[16], 
                        help='Thread counts to use for comparison charts')
    parser.add_argument('--workloads', type=str, nargs='+', default=['a', 'b', 'c'], 
                        help='Workloads to use for thread scaling charts')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Collect results from all databases
    db_dirs = {
        'mongodb': args.mongodb_dir,
        'redis': args.redis_dir,
        'cassandra': args.cassandra_dir
    }
    
    all_results = collect_all_db_results(db_dirs)
    
    if not all_results:
        print("No valid benchmark results found. Exiting.")
        return
    
    # Generate comparison charts for each specified thread count
    for thread_count in args.threads:
        print(f"\nGenerating comparison charts for {thread_count} threads...")
        create_throughput_comparison_chart(all_results, args.output_dir, thread_count)
        create_latency_comparison_chart(all_results, args.output_dir, thread_count, 'read_avg_latency')
        create_latency_comparison_chart(all_results, args.output_dir, thread_count, 'read_p99_latency')
    
    # Generate thread scaling charts for each specified workload
    for workload in args.workloads:
        print(f"\nGenerating scaling charts for workload {workload}...")
        create_throughput_scaling_chart(all_results, args.output_dir, workload)
        create_latency_scaling_chart(all_results, args.output_dir, workload, 'read_avg_latency')
        create_latency_scaling_chart(all_results, args.output_dir, workload, 'read_p99_latency')
    
    print("\nAll comparison charts generated successfully!")

if __name__ == "__main__":
    main()
