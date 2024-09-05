
# Alpha Version
#     Reads in directory and produces edges that are also populated into the main database

import argparse
import json
import os
import tempfile
import hashlib
import pickle
import time
from datetime import datetime
from pathlib import Path
from graphbrain import hgraph
from graphbrain.parsers import create_parser
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
def process_file(input_file, output_dir, matches_key, headline_key, text_key):
    output_file = Path(output_dir) / f"{input_file.stem}.db"
    hg = hgraph(str(output_file))
    parser = create_parser(lang='en')
    
    with open(input_file, 'r') as f:
        for line_number, line in enumerate(f, 1):
            try:
                data = json.loads(line)
                text = f"{data.get(headline_key, '')}\n\n{data.get(text_key, '')}"
                
                # Parse and add the text to the hypergraph
                parser.parse_and_add(text, hg)
            except Exception as e:
                print(f"Error processing line {line_number} in file {input_file}: {str(e)}")
                # Optionally, you can log the error or skip the problematic line
                continue
    
    hg.close()
    return str(output_file)

@time_function
def main_process(input_dir, output_dir, matches_key, headline_key, text_key):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    lookup_table = {}
    errors = []
    
    print(f"Input directory: {input_path}")
    print(f"Output directory: {output_path}")
    
    for file in input_path.glob('*.wiki.jsonl'):
        print(f"Processing file: {file}")
        try:
            output_file = process_file(file, output_path, matches_key, headline_key, text_key)
            print(f"  Created output file: {output_file}")
            
            start_time = time.time()
            with open(file, 'r') as f:
                line_count = 0
                for line in f:
                    data = json.loads(line)
                    text = f"{data.get(headline_key, '')}\n\n{data.get(text_key, '')}"
                    text_hash = hashlib.sha256(text.encode()).hexdigest()
                    lookup_table[text_hash] = {
                        'metadata': data,
                        'file': str(output_file)
                    }
                    line_count += 1
            end_time = time.time()
            elapsed_time = end_time - start_time
            timing_info['process_lookup_table'] += elapsed_time
            print(f"  Processed {line_count} lines in {elapsed_time:.2f} seconds")
        except Exception as e:
            print(f"  Error processing file: {e}")
            errors.append({'file': str(file), 'error': str(e)})
    
    if errors:
        error_file = output_path / 'errors.json'
        with open(error_file, 'w') as f:
            json.dump(errors, f, indent=2)
        print(f"Errors encountered. See {error_file}")
    
    start_time = time.time()
    lookup_table_file = output_path / f"lookup_table_{timestamp}.pkl"
    with open(lookup_table_file, 'wb') as f:
        pickle.dump(lookup_table, f)
    end_time = time.time()
    elapsed_time = end_time - start_time
    timing_info['save_lookup_table'] += elapsed_time
    print(f"Lookup table saved: {lookup_table_file} in {elapsed_time:.2f} seconds")
    
    print(f"Total entries in lookup table: {len(lookup_table)}")
    
    # Print sorted summary of timing information
    print("\nTiming Summary:")
    sorted_timing = sorted(timing_info.items(), key=lambda x: x[1], reverse=True)
    for func_name, total_time in sorted_timing:
        print(f"{func_name}: {total_time:.2f} seconds")

@time_function
def main(input_dir, output_dir, matches_key, headline_key, text_key):
    main_process(input_dir, output_dir, matches_key, headline_key, text_key)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process wiki.jsonl files and create graph brain databases")
    parser.add_argument("input_dir", help="Input directory containing *.wiki.jsonl files")
    parser.add_argument("--output_dir", default="out", help="Output directory for databases and lookup table")
    parser.add_argument("--matches_key", default="matches", help="Key for matches in the JSON file")
    parser.add_argument("--headline_key", default="headline", help="Key for headline in the JSON file")
    parser.add_argument("--text_key", default="text", help="Key for text content in the JSON file")
    
    args = parser.parse_args()
    
    start_time = time.time()
    main(args.input_dir, args.output_dir, args.matches_key, args.headline_key, args.text_key)
    end_time = time.time()
    total_time = end_time - start_time
    print(f"\nTotal execution time: {total_time:.2f} seconds")
