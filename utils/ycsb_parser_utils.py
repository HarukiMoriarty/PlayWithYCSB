import os
import re
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

def parse_benchmark_result(file_path, db_name, filename_pattern=None):
    """Parse a YCSB benchmark result file and extract key metrics.
    
    Args:
        file_path: Path to the result file
        db_name: Database name (mongodb, redis, zookeeper, cassandra2-cql)
        filename_pattern: Custom regex pattern for extracting workload and thread info
    """
    metrics = {}
    
    with open(file_path, 'r') as f:
        content = f.read()
        
        # Extract workload and thread count from filename
        filename = os.path.basename(file_path)
        
        if filename_pattern:
            match = re.search(filename_pattern, filename)
        else:
            # Default pattern for most databases
            match = re.search(rf'{db_name}_workload([a-f])_(\d+)threads\.txt', filename)
            
        if match:
            if db_name == 'cassandra2-cql':
                # Cassandra has a different pattern with replication factor
                metrics['workload'] = match.group(2)
                metrics['threads'] = int(match.group(3))
                metrics['rf'] = int(match.group(1))
            else:
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

def collect_all_results(results_dir, db_name, filename_pattern=None):
    """Collect results from all benchmark files in the directory.
    
    Args:
        results_dir: Directory containing result files
        db_name: Database name
        filename_pattern: Custom regex pattern for file matching
    """
    results = []
    
    # Find all result files for the specified database
    if db_name == 'cassandra2-cql':
        # Cassandra has a different file pattern
        result_files = list(Path(results_dir).glob(f'{db_name}_rf*_workload*_*threads.txt'))
    else:
        result_files = list(Path(results_dir).glob(f'{db_name}_workload*_*threads.txt'))
    
    for file_path in result_files:
        try:
            metrics = parse_benchmark_result(file_path, db_name, filename_pattern)
            if metrics:
                results.append(metrics)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    
    return results

def create_throughput_by_workload_chart(results, output_dir, db_name):
    """Create a chart showing throughput by workload and thread count."""
    df = pd.DataFrame(results)
    
    # Group by workload
    workloads = sorted(df['workload'].unique())
    thread_counts = sorted(df['threads'].unique())
    
    # For Cassandra, we might want to separate by replication factor
    if 'rf' in df.columns:
        rf_values = sorted(df['rf'].unique())
        for rf in rf_values:
            rf_df = df[df['rf'] == rf]
            _create_throughput_chart(rf_df, workloads, thread_counts, output_dir, f"{db_name}_rf{rf}")
    else:
        _create_throughput_chart(df, workloads, thread_counts, output_dir, db_name)

def _create_throughput_chart(df, workloads, thread_counts, output_dir, chart_name):
    """Helper function to create throughput chart."""
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
    plt.xlabel('Workload', fontsize=20)
    plt.ylabel('Throughput (ops/sec)', fontsize=20)
    plt.title(f'{chart_name.capitalize()} YCSB Throughput by Workload and Thread Count', fontsize=22)
    
    # Set x-axis ticks to workload names
    plt.xticks(workload_positions, [f'Workload {w.upper()}' for w in workloads])
    
    # Add legend
    plt.legend(title='Thread Count', fontsize=20)
    
    # Add grid for better readability
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Save the figure
    output_path = os.path.join(output_dir, f'{chart_name}_throughput_by_workload.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved throughput chart to {output_path}")

def create_latency_by_thread_chart(results, output_dir, db_name):
    """Create a chart showing average read latency by workload and thread count."""
    df = pd.DataFrame(results)
    
    # Group by workload
    workloads = sorted(df['workload'].unique())
    thread_counts = sorted(df['threads'].unique())
    
    # For Cassandra, we might want to separate by replication factor
    if 'rf' in df.columns:
        rf_values = sorted(df['rf'].unique())
        for rf in rf_values:
            rf_df = df[df['rf'] == rf]
            _create_latency_chart(rf_df, workloads, thread_counts, output_dir, f"{db_name}_rf{rf}")
    else:
        _create_latency_chart(df, workloads, thread_counts, output_dir, db_name)

def _create_latency_chart(df, workloads, thread_counts, output_dir, chart_name):
    """Helper function to create latency chart."""
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
    plt.xlabel('Workload', fontsize=20)
    plt.ylabel('Average Read Latency (μs)', fontsize=20)
    plt.title(f'{chart_name.capitalize()} YCSB Average Read Latency by Workload and Thread Count', fontsize=22)
    
    # Set x-axis ticks to workload names
    plt.xticks(workload_positions, [f'Workload {w.upper()}' for w in workloads])
    
    # Add legend
    plt.legend(title='Thread Count', fontsize=20)
    
    # Add grid for better readability
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Save the figure
    output_path = os.path.join(output_dir, f'{chart_name}_avg_latency_by_workload.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved average latency chart to {output_path}")

def create_p99_latency_chart(results, output_dir, db_name):
    """Create a chart showing P99 latency by workload and thread count."""
    df = pd.DataFrame(results)
    
    # Group by workload
    workloads = sorted(df['workload'].unique())
    thread_counts = sorted(df['threads'].unique())
    
    # For Cassandra, we might want to separate by replication factor
    if 'rf' in df.columns:
        rf_values = sorted(df['rf'].unique())
        for rf in rf_values:
            rf_df = df[df['rf'] == rf]
            _create_p99_latency_chart(rf_df, workloads, thread_counts, output_dir, f"{db_name}_rf{rf}")
    else:
        _create_p99_latency_chart(df, workloads, thread_counts, output_dir, db_name)

def _create_p99_latency_chart(df, workloads, thread_counts, output_dir, chart_name):
    """Helper function to create P99 latency chart."""
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
    plt.xlabel('Workload', fontsize=20)
    plt.ylabel('P99 Read Latency (μs)', fontsize=20)
    plt.title(f'{chart_name.capitalize()} YCSB P99 Read Latency by Workload and Thread Count', fontsize=22)
    
    # Set x-axis ticks to workload names
    plt.xticks(workload_positions, [f'Workload {w.upper()}' for w in workloads])
    
    # Add legend
    plt.legend(title='Thread Count', fontsize=20)
    
    # Add grid for better readability
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Save the figure
    output_path = os.path.join(output_dir, f'{chart_name}_p99_latency_by_workload.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved P99 latency chart to {output_path}")

def create_combined_performance_chart(results, output_dir, db_name):
    """Create a single figure with throughput, read/write latencies charts side by side.
    
    Args:
        results: List of benchmark result dictionaries
        output_dir: Directory to save the chart
        db_name: Database name for chart title
    """
    df = pd.DataFrame(results)
    
    # Group by workload
    workloads = sorted(df['workload'].unique())
    thread_counts = sorted(df['threads'].unique())
    
    # For Cassandra, we might want to separate by replication factor
    if 'rf' in df.columns:
        rf_values = sorted(df['rf'].unique())
        for rf in rf_values:
            rf_df = df[df['rf'] == rf]
            _create_combined_performance_chart(rf_df, workloads, thread_counts, output_dir, f"{db_name}_rf{rf}")
    else:
        _create_combined_performance_chart(df, workloads, thread_counts, output_dir, db_name)

def _create_combined_performance_chart(df, workloads, thread_counts, output_dir, chart_name):
    """Helper function to create combined performance chart with five subplots side by side."""
    # Create a figure with 5 subplots side by side
    fig, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(1, 5, figsize=(30, 8))
    
    # Width of each bar group
    group_width = 0.8
    # Width of each bar within a group
    bar_width = group_width / len(thread_counts)
    
    # Position of each workload group on x-axis
    workload_positions = np.arange(len(workloads))
    
    # Colors for different thread counts
    colors = plt.cm.viridis(np.linspace(0, 0.9, len(thread_counts)))
    
    # Create throughput subplot (first)
    throughput_values = []
    for i, thread_count in enumerate(thread_counts):
        # Filter data for this thread count
        thread_data = df[df['threads'] == thread_count]
        
        # Get throughput values for each workload
        throughputs = []
        for workload in workloads:
            workload_data = thread_data[thread_data['workload'] == workload]
            if not workload_data.empty and 'throughput' in workload_data.columns:
                throughputs.append(workload_data['throughput'].values[0])
            else:
                throughputs.append(0)
        
        throughput_values.extend(throughputs)
        
        # Calculate position for this set of bars
        positions = workload_positions + (i - len(thread_counts)/2 + 0.5) * bar_width
        
        # Plot bars
        ax1.bar(positions, throughputs, width=bar_width, label=f'{thread_count} Threads', color=colors[i])
    
    # Set chart labels and title for throughput
    ax1.set_xlabel('Workload', fontsize=20)
    ax1.set_ylabel('Throughput (ops/sec)', fontsize=20)
    ax1.set_title(f'Throughput', fontsize=22)
    ax1.set_xticks(workload_positions)
    ax1.set_xticklabels([f'{w.upper()}' for w in workloads], fontsize=20)
    ax1.tick_params(axis='both', which='major', labelsize=20)
    ax1.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Set reasonable y-axis limits for throughput
    _set_reasonable_ylim(ax1, throughput_values)
    
    # Create average read latency subplot (second)
    read_avg_values = []
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
        
        read_avg_values.extend(latencies)
        
        # Calculate position for this set of bars
        positions = workload_positions + (i - len(thread_counts)/2 + 0.5) * bar_width
        
        # Plot bars
        ax2.bar(positions, latencies, width=bar_width, label=f'{thread_count} Threads', color=colors[i])
    
    # Set chart labels and title for avg read latency
    ax2.set_xlabel('Workload', fontsize=20)
    ax2.set_ylabel('Latency (μs)', fontsize=20)
    ax2.set_title(f'Avg Read Latency', fontsize=22)
    ax2.set_xticks(workload_positions)
    ax2.set_xticklabels([f'{w.upper()}' for w in workloads], fontsize=20)
    ax2.tick_params(axis='both', which='major', labelsize=20)
    ax2.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Set reasonable y-axis limits for read avg latency
    _set_reasonable_ylim(ax2, read_avg_values)
    
    # Create P99 read latency subplot (third)
    read_p99_values = []
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
        
        read_p99_values.extend(latencies)
        
        # Calculate position for this set of bars
        positions = workload_positions + (i - len(thread_counts)/2 + 0.5) * bar_width
        
        # Plot bars
        ax3.bar(positions, latencies, width=bar_width, label=f'{thread_count} Threads', color=colors[i])
    
    # Set chart labels and title for P99 read latency
    ax3.set_xlabel('Workload', fontsize=20)
    ax3.set_ylabel('Latency (μs)', fontsize=20)
    ax3.set_title(f'P99 Read Latency', fontsize=22)
    ax3.set_xticks(workload_positions)
    ax3.set_xticklabels([f'{w.upper()}' for w in workloads], fontsize=20)
    ax3.tick_params(axis='both', which='major', labelsize=20)
    ax3.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Set reasonable y-axis limits for read p99 latency
    _set_reasonable_ylim(ax3, read_p99_values)
    
    # Create average write latency subplot (fourth)
    write_avg_values = []
    for i, thread_count in enumerate(thread_counts):
        # Filter data for this thread count
        thread_data = df[df['threads'] == thread_count]
        
        # Get average write latency values for each workload
        latencies = []
        for workload in workloads:
            workload_data = thread_data[thread_data['workload'] == workload]
            if not workload_data.empty and 'update_avg_latency' in workload_data.columns:
                latencies.append(workload_data['update_avg_latency'].values[0])
            else:
                latencies.append(0)
        
        write_avg_values.extend(latencies)
        
        # Calculate position for this set of bars
        positions = workload_positions + (i - len(thread_counts)/2 + 0.5) * bar_width
        
        # Plot bars
        ax4.bar(positions, latencies, width=bar_width, label=f'{thread_count} Threads', color=colors[i])
    
    # Set chart labels and title for avg write latency
    ax4.set_xlabel('Workload', fontsize=20)
    ax4.set_ylabel('Latency (μs)', fontsize=20)
    ax4.set_title(f'Avg Write Latency', fontsize=22)
    ax4.set_xticks(workload_positions)
    ax4.set_xticklabels([f'{w.upper()}' for w in workloads], fontsize=20)
    ax4.tick_params(axis='both', which='major', labelsize=20)
    ax4.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Set reasonable y-axis limits for write avg latency
    _set_reasonable_ylim(ax4, write_avg_values)
    
    # Create P99 write latency subplot (fifth)
    write_p99_values = []
    for i, thread_count in enumerate(thread_counts):
        # Filter data for this thread count
        thread_data = df[df['threads'] == thread_count]
        
        # Get P99 write latency values for each workload
        latencies = []
        for workload in workloads:
            workload_data = thread_data[thread_data['workload'] == workload]
            if not workload_data.empty and 'update_p99_latency' in workload_data.columns:
                latencies.append(workload_data['update_p99_latency'].values[0])
            else:
                latencies.append(0)
        
        write_p99_values.extend(latencies)
        
        # Calculate position for this set of bars
        positions = workload_positions + (i - len(thread_counts)/2 + 0.5) * bar_width
        
        # Plot bars
        ax5.bar(positions, latencies, width=bar_width, label=f'{thread_count} Threads', color=colors[i])
    
    # Set chart labels and title for P99 write latency
    ax5.set_xlabel('Workload', fontsize=20)
    ax5.set_ylabel('Latency (μs)', fontsize=20)
    ax5.set_title(f'P99 Write Latency', fontsize=22)
    ax5.set_xticks(workload_positions)
    ax5.set_xticklabels([f'{w.upper()}' for w in workloads], fontsize=20)
    ax5.tick_params(axis='both', which='major', labelsize=20)
    ax5.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Set reasonable y-axis limits for write p99 latency
    _set_reasonable_ylim(ax5, write_p99_values)
    
    # Add legend (only once for the entire figure)
    handles, labels = ax1.get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.05), 
               fancybox=True, shadow=True, ncol=len(thread_counts), fontsize=20)
    
    # Add overall title
    fig.suptitle(f'{chart_name.capitalize()} YCSB Performance Metrics', fontsize=26)
    
    # Adjust layout
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15)  # Make room for the legend
    
    # Save the figure as PDF
    output_path = os.path.join(output_dir, f'{chart_name}_combined_performance.pdf')
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    
    # Also save as PNG for quick viewing
    png_output_path = os.path.join(output_dir, f'{chart_name}_combined_performance.png')
    plt.savefig(png_output_path, dpi=300, bbox_inches='tight')
    
    plt.close()
    
    print(f"Saved combined performance chart to {output_path} and {png_output_path}")

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
                        fontsize=18)