
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
        for line in f:
            data = json.loads(line)
            text = f"{data.get(headline_key, '')}\n\n{data.get(text_key, '')}"
            
            # Parse and add the text to the hypergraph
            parser.parse_and_add(text, hg)
    
    hg.close()
    return str(output_file), text

@time_function
def add_to_main_db(main_db, db_file):
    source_hg = hgraph(db_file)
    for edge in source_hg.all():
        main_db.add(edge)

@time_function
def main_test(input_dir, output_dir, matches_key, headline_key, text_key):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    main_db_file = output_path / f"main_{timestamp}.db"
    main_db = hgraph(str(main_db_file))
    lookup_table = {}
    errors = []
    
    print(f"Input directory: {input_path}")
    print(f"Output directory: {output_path}")
    print(f"Main database file: {main_db_file}")
    
    for file in input_path.glob('*.wiki.jsonl'):
        print(f"Processing file: {file}")
        try:
            db_file, _ = process_file(file, output_path, matches_key, headline_key, text_key)
            print(f"  Created database file: {db_file}")
            
            add_to_main_db(main_db, db_file)
            print(f"  Added to main database")
            
            start_time = time.time()
            with open(file, 'r') as f:
                line_count = 0
                for line in f:
                    data = json.loads(line)
                    text = f"{data.get(headline_key, '')}\n\n{data.get(text_key, '')}"
                    text_hash = hashlib.sha256(text.encode()).hexdigest()
                    lookup_table[text_hash] = {
                        'metadata': data,
                        'file': str(db_file)
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
    
    print("Closing main database...")
    main_db.close()
    
    start_time = time.time()
    lookup_table_file = output_path / f"lookup_table_{timestamp}.pkl"
    with open(lookup_table_file, 'wb') as f:
        pickle.dump(lookup_table, f)
    end_time = time.time()
    elapsed_time = end_time - start_time
    timing_info['save_lookup_table'] += elapsed_time
    print(f"Lookup table saved: {lookup_table_file} in {elapsed_time:.2f} seconds")
    
    print(f"Total entries in lookup table: {len(lookup_table)}")
    
    # Verify the contents of the main database
    print("Verifying main database contents...")
    start_time = time.time()
    main_db = hgraph(str(main_db_file))
    edge_count = sum(1 for _ in main_db.all())
    main_db.close()
    end_time = time.time()
    elapsed_time = end_time - start_time
    timing_info['verify_main_db'] += elapsed_time
    print(f"Total edges in main database: {edge_count}")
    print(f"Verification completed in {elapsed_time:.2f} seconds")
    
    # Print sorted summary of timing information
    print("\nTiming Summary:")
    sorted_timing = sorted(timing_info.items(), key=lambda x: x[1], reverse=True)
    for func_name, total_time in sorted_timing:
        print(f"{func_name}: {total_time:.2f} seconds")

@time_function
def main(input_dir, output_dir, matches_key, headline_key, text_key):
    main_test(input_dir, output_dir, matches_key, headline_key, text_key)

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
