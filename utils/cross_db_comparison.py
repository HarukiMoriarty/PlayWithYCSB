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

def create_combined_comparison_chart(all_results, output_dir, thread_count=16):
    """Create a single chart with 5 subplots comparing throughput and latencies across databases."""
    fig, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(1, 5, figsize=(30, 8))
    
    # Get all workloads across all databases
    workloads = set()
    for db_name, df in all_results.items():
        if 'workload' in df.columns:
            workloads.update(df['workload'].unique())
    
    workloads = sorted(list(workloads))
    
    # Number of databases
    num_dbs = len(all_results)
    
    # Width of each bar group
    group_width = 0.8
    # Width of each bar within a group
    bar_width = group_width / num_dbs
    
    # Position of each workload group on x-axis
    workload_positions = np.arange(len(workloads))
    
    # Markers and colors for different databases
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    
    # --- THROUGHPUT SUBPLOT (1) ---
    throughput_values = []
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
        
        throughput_values.extend(throughputs)
        
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
        ax1.bar(positions, throughputs, width=bar_width, label=display_name, color=colors[i % len(colors)])
    
    # Set chart labels and title for throughput
    ax1.set_xlabel('Workload', fontsize=12)
    ax1.set_ylabel('Throughput (ops/sec)', fontsize=12)
    ax1.set_title('Throughput', fontsize=14)
    ax1.set_xticks(workload_positions)
    ax1.set_xticklabels([f'{w.upper()}' for w in workloads])
    ax1.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Set reasonable y-axis limits for throughput
    _set_reasonable_ylim(ax1, throughput_values)
    
    # --- READ AVG LATENCY SUBPLOT (2) ---
    read_avg_values = []
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
        
        # Get read avg latency values for each workload
        latencies = []
        for workload in workloads:
            if 'workload' in thread_data.columns:
                workload_data = thread_data[thread_data['workload'] == workload]
                if not workload_data.empty and 'read_avg_latency' in workload_data.columns:
                    latencies.append(workload_data['read_avg_latency'].values[0])
                else:
                    latencies.append(0)
            else:
                latencies.append(0)
        
        read_avg_values.extend(latencies)
        
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
        ax2.bar(positions, latencies, width=bar_width, label=display_name, color=colors[i % len(colors)])
    
    # Set chart labels and title for read avg latency
    ax2.set_xlabel('Workload', fontsize=12)
    ax2.set_ylabel('Latency (μs)', fontsize=12)
    ax2.set_title('Avg Read Latency', fontsize=14)
    ax2.set_xticks(workload_positions)
    ax2.set_xticklabels([f'{w.upper()}' for w in workloads])
    ax2.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Set reasonable y-axis limits for read avg latency
    _set_reasonable_ylim(ax2, read_avg_values)
    
    # --- READ P99 LATENCY SUBPLOT (3) ---
    read_p99_values = []
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
        
        # Get read p99 latency values for each workload
        latencies = []
        for workload in workloads:
            if 'workload' in thread_data.columns:
                workload_data = thread_data[thread_data['workload'] == workload]
                if not workload_data.empty and 'read_p99_latency' in workload_data.columns:
                    latencies.append(workload_data['read_p99_latency'].values[0])
                else:
                    latencies.append(0)
            else:
                latencies.append(0)
        
        read_p99_values.extend(latencies)
        
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
        ax3.bar(positions, latencies, width=bar_width, label=display_name, color=colors[i % len(colors)])
    
    # Set chart labels and title for read p99 latency
    ax3.set_xlabel('Workload', fontsize=12)
    ax3.set_ylabel('Latency (μs)', fontsize=12)
    ax3.set_title('P99 Read Latency', fontsize=14)
    ax3.set_xticks(workload_positions)
    ax3.set_xticklabels([f'{w.upper()}' for w in workloads])
    ax3.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Set reasonable y-axis limits for read p99 latency
    _set_reasonable_ylim(ax3, read_p99_values)
    
    # --- WRITE AVG LATENCY SUBPLOT (4) ---
    write_avg_values = []
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
        
        # Get write avg latency values for each workload
        latencies = []
        for workload in workloads:
            if 'workload' in thread_data.columns:
                workload_data = thread_data[thread_data['workload'] == workload]
                if not workload_data.empty and 'update_avg_latency' in workload_data.columns:
                    latencies.append(workload_data['update_avg_latency'].values[0])
                else:
                    latencies.append(0)
            else:
                latencies.append(0)
        
        write_avg_values.extend(latencies)
        
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
        ax4.bar(positions, latencies, width=bar_width, label=display_name, color=colors[i % len(colors)])
    
    # Set chart labels and title for write avg latency
    ax4.set_xlabel('Workload', fontsize=12)
    ax4.set_ylabel('Latency (μs)', fontsize=12)
    ax4.set_title('Avg Write Latency', fontsize=14)
    ax4.set_xticks(workload_positions)
    ax4.set_xticklabels([f'{w.upper()}' for w in workloads])
    ax4.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Set reasonable y-axis limits for write avg latency
    _set_reasonable_ylim(ax4, write_avg_values)
    
    # --- WRITE P99 LATENCY SUBPLOT (5) ---
    write_p99_values = []
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
        
        # Get write p99 latency values for each workload
        latencies = []
        for workload in workloads:
            if 'workload' in thread_data.columns:
                workload_data = thread_data[thread_data['workload'] == workload]
                if not workload_data.empty and 'update_p99_latency' in workload_data.columns:
                    latencies.append(workload_data['update_p99_latency'].values[0])
                else:
                    latencies.append(0)
            else:
                latencies.append(0)
        
        write_p99_values.extend(latencies)
        
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
        ax5.bar(positions, latencies, width=bar_width, label=display_name, color=colors[i % len(colors)])
    
    # Set chart labels and title for write p99 latency
    ax5.set_xlabel('Workload', fontsize=12)
    ax5.set_ylabel('Latency (μs)', fontsize=12)
    ax5.set_title('P99 Write Latency', fontsize=14)
    ax5.set_xticks(workload_positions)
    ax5.set_xticklabels([f'{w.upper()}' for w in workloads])
    ax5.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Set reasonable y-axis limits for write p99 latency
    _set_reasonable_ylim(ax5, write_p99_values)
    
    # Add legend (only once for the entire figure)
    handles, labels = ax1.get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.05), 
               fancybox=True, shadow=True, ncol=len(all_results))
    
    # Add overall title
    fig.suptitle(f'Database Comparison - {thread_count} Threads', fontsize=16)
    
    # Adjust layout
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15)  # Make room for the legend
    
    # Save the figure as PDF
    output_path = os.path.join(output_dir, f'db_combined_comparison_{thread_count}threads.pdf')
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    
    # Also save as PNG for quick viewing
    png_output_path = os.path.join(output_dir, f'db_combined_comparison_{thread_count}threads.png')
    plt.savefig(png_output_path, dpi=300, bbox_inches='tight')
    
    plt.close()
    
    print(f"Saved combined comparison chart to {output_path} and {png_output_path}")

def _set_reasonable_ylim(ax, values):
    """Set reasonable y-axis limits to handle outliers.
    
    This function sets the y-axis limits to show the majority of the data clearly
    while preventing extreme outliers from compressing the visualization of other values.
    """
    # Remove zeros and sort values
    non_zero_values = [v for v in values if v > 0]
    if not non_zero_values:
        return
    
    # Sort values
    sorted_values = sorted(non_zero_values)
    
    # Calculate percentiles
    if len(sorted_values) >= 4:
        # Use 95th percentile if we have enough data points
        p95 = sorted_values[int(0.95 * len(sorted_values))]
        
        # Find the maximum non-outlier value (1.5 times the 95th percentile)
        max_reasonable = p95 * 1.5
        
        # Set y-axis limit to the maximum reasonable value
        current_ymax = ax.get_ylim()[1]
        if max_reasonable < current_ymax:
            ax.set_ylim(0, max_reasonable)
            
            # Add a text annotation indicating truncation
            if max(sorted_values) > max_reasonable:
                ax.text(0.98, 0.98, f"* Y-axis truncated\n  Max value: {int(max(sorted_values))}", 
                        transform=ax.transAxes, ha='right', va='top', 
                        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.7),
                        fontsize=10)

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
        create_combined_comparison_chart(all_results, args.output_dir, thread_count)
    
    print("\nAll comparison charts generated successfully!")

if __name__ == "__main__":
    main()
