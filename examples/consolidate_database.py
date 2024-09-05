import argparse
import json
import os
from pathlib import Path
from graphbrain import hgraph
from graphbrain.parsers import create_parser
import time
from collections import defaultdict

# Global dictionary to store timing information
timing_info = defaultdict(float)

def time_function(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        timing_info[func.__name__] += elapsed_time
        print(f"[Line {func.__code__.co_firstlineno}] {func.__name__} took {elapsed_time:.2f} seconds")
        return result
    return wrapper

@time_function
def process_jsonl_file(file_path, hg):
    with open(file_path, 'r') as f:
        for line in f:
            data = json.loads(line)
            parsed_edges = data.get('parsed_edges', [])
            for edge_str in parsed_edges:
                edge = hgraph(edge_str)
                hg.add(edge)

@time_function
def consolidate_database(input_dir, output_file):
    input_path = Path(input_dir)
    output_path = Path(output_file)

    # Create the output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize the hypergraph
    hg = hgraph(str(output_path))

    print(f"Input directory: {input_path}")
    print(f"Output file: {output_path}")

    # Process all JSONL files in the input directory
    for file in input_path.glob('*.jsonl'):
        print(f"Processing file: {file}")
        process_jsonl_file(file, hg)

    # Close the hypergraph to ensure all data is written to disk
    hg.close()

    print(f"Consolidated database saved to: {output_path}")

@time_function
def main(input_dir, output_file):
    consolidate_database(input_dir, output_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Consolidate JSONL files into a single GraphBrain database")
    parser.add_argument("input_dir", help="Input directory containing processed JSONL files")
    parser.add_argument("output_file", help="Output file path for the consolidated database")

    args = parser.parse_args()

    start_time = time.time()
    main(args.input_dir, args.output_file)
    end_time = time.time()
    total_time = end_time - start_time

    print("\nTiming Summary:")
    sorted_timing = sorted(timing_info.items(), key=lambda x: x[1], reverse=True)
    for func_name, total_time in sorted_timing:
        print(f"{func_name}: {total_time:.2f} seconds")

    print(f"\nTotal execution time: {total_time:.2f} seconds")
