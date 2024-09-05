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
import multiprocessing as mp                                                                                                
from functools import partial                                                                                               
                                                                                                                            
def process_batch(batch, parser, hg):                                                                                       
    for item in batch:                                                                                                      
        text = f"{item.get('headline', '')}\n\n{item.get('text', '')}"                                                      
        parser.parse_and_add(text, hg)                                                                                      
                                                                                                                            
def process_file(input_file, output_dir, parser, batch_size=100):                                                           
    output_file = Path(output_dir) / f"{input_file.stem}.db"                                                                
    hg = hgraph(str(output_file))                                                                                           
                                                                                                                            
    batch = []                                                                                                              
    with open(input_file, 'r') as f:                                                                                        
        for line in f:                                                                                                      
            data = json.loads(line)                                                                                         
            batch.append(data)                                                                                              
            if len(batch) >= batch_size:                                                                                    
                process_batch(batch, parser, hg)                                                                            
                batch = []                                                                                                  
                                                                                                                            
    if batch:  # Process any remaining items                                                                                
        process_batch(batch, parser, hg)                                                                                    
                                                                                                                            
    hg.close()                                                                                                              
    return str(output_file)                                                                                                 
                                                                                                                            
def add_to_main_db(main_db, db_file):                                                                                       
    source_hg = hgraph(db_file)                                                                                             
    edges = list(source_hg.all())  # Get all edges at once                                                                  
    for edge in edges:                                                                                                      
        main_db.add(edge)                                                                                                   
                                                                                                                            
def process_files(file_list, output_dir, parser):                                                                           
    results = []                                                                                                            
    for file in file_list:                                                                                                  
        db_file = process_file(file, output_dir, parser)                                                                    
        results.append((file, db_file))                                                                                     
    return results                                                                                                          
                                                                                                                            
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
                                                                                                                            
    # Create parser once                                                                                                    
    parser = create_parser(lang='en', parser_class='en_core_web_sm')                                                        
                                                                                                                            
    # Get list of files to process                                                                                          
    files = list(input_path.glob('*.wiki.jsonl'))                                                                           
                                                                                                                            
    # Use multiprocessing to process files                                                                                  
    num_processes = mp.cpu_count()                                                                                          
    pool = mp.Pool(processes=num_processes)                                                                                 
    chunk_size = len(files) // num_processes + 1                                                                            
    file_chunks = [files[i:i+chunk_size] for i in range(0, len(files), chunk_size)]                                         
                                                                                                                            
    process_func = partial(process_files, output_dir=output_path, parser=parser)                                            
    results = pool.map(process_func, file_chunks)                                                                           
                                                                                                                            
    # Flatten results                                                                                                       
    all_results = [item for sublist in results for item in sublist]                                                         
                                                                                                                            
    for file, db_file in all_results:                                                                                       
        print(f"Processed file: {file}")                                                                                    
        print(f"  Created database file: {db_file}")                                                                        
                                                                                                                            
        try:                                                                                                                
            add_to_main_db(main_db, db_file)                                                                                
            print(f"  Added to main database")                                                                              
                                                                                                                            
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
                print(f"  Processed {line_count} lines")                                                                    
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
                                                                                                                            
    lookup_table_file = output_path / f"lookup_table_{timestamp}.pkl"                                                       
    with open(lookup_table_file, 'wb') as f:                                                                                
        pickle.dump(lookup_table, f)                                                                                        
    print(f"Lookup table saved: {lookup_table_file}")                                                                       
                                                                                                                            
    print(f"Total entries in lookup table: {len(lookup_table)}")                                                            
                                                                                                                            
    # Verify the contents of the main database                                                                              
    print("Verifying main database contents...")                                                                            
    main_db = hgraph(str(main_db_file))                                                                                     
    edge_count = sum(1 for _ in main_db.all())                                                                              
    print(f"Total edges in main database: {edge_count}")                                                                    
    main_db.close()                                                                                                         
                                                                                                                            
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
                                                                                                                            
    main(args.input_dir, args.output_dir, args.matches_key, args.headline_key, args.text_key)