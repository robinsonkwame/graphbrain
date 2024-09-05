
import argparse
import json
import os
import tempfile
import hashlib
import pickle
from datetime import datetime
from pathlib import Path
from graphbrain import hgraph
from graphbrain.parsers import create_parser

def process_file(input_file, output_dir, matches_key, headline_key, text_key):
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    text = f"{data.get(headline_key, '')}\n\n{data.get(text_key, '')}"
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_file.write(text)
    
    output_file = Path(output_dir) / f"{input_file.stem}.db"
    
    os.system(f"graphbrain txt --infile {temp_file.name} --hg {output_file} --lang en")
    
    os.unlink(temp_file.name)
    
    return output_file, text

def add_to_main_db(main_db, db_file):
    source_hg = hgraph(db_file)
    for edge in source_hg.all():
        main_db.add(edge)

def main(input_dir, output_dir, matches_key, headline_key, text_key):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    main_db = hgraph()
    lookup_table = {}
    errors = []
    
    for file in input_path.glob('*.wiki.json'):
        try:
            db_file, text = process_file(file, output_path, matches_key, headline_key, text_key)
            add_to_main_db(main_db, db_file)
            
            text_hash = hashlib.sha256(text.encode()).hexdigest()
            with open(file, 'r') as f:
                metadata = json.load(f)
            lookup_table[text_hash] = {
                'metadata': metadata,
                'file': str(db_file)
            }
        except Exception as e:
            errors.append({'file': str(file), 'error': str(e)})
    
    if errors:
        with open(output_path / 'errors.json', 'w') as f:
            json.dump(errors, f, indent=2)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    main_db_file = output_path / f"main_{timestamp}.db"
    main_db.save(main_db_file)
    
    lookup_table_file = output_path / f"lookup_table_{timestamp}.pkl"
    with open(lookup_table_file, 'wb') as f:
        pickle.dump(lookup_table, f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process wiki.json files and create graph brain databases")
    parser.add_argument("input_dir", help="Input directory containing *.wiki.json files")
    parser.add_argument("--output_dir", default="out", help="Output directory for databases and lookup table")
    parser.add_argument("--matches_key", default="matches", help="Key for matches in the JSON file")
    parser.add_argument("--headline_key", default="headline", help="Key for headline in the JSON file")
    parser.add_argument("--text_key", default="text", help="Key for text content in the JSON file")
    
    args = parser.parse_args()
    
    main(args.input_dir, args.output_dir, args.matches_key, args.headline_key, args.text_key)
