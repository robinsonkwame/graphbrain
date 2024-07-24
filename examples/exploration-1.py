from graphbrain import hgraph
from graphbrain.parsers import create_parser
from graphbrain.processors import names
from data_level_0 import examples

import sys
import spacy
import graphbrain
import tempfile
import os

def analyze_text(texts, batch_size=100):
    # Create a parser
    parser = create_parser(lang='en')
    
    # Create a temporary directory for the hypergraph
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, 'example_db')
        
        # Create a hypergraph
        hg = hgraph(f'leveldb://{db_path}')
    
    # Process texts in batches
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        print(f"\nProcessing batch {i//batch_size + 1}")
        
        for text in batch:
            print(f"\nAnalyzing text: {text[:50]}...")  # Print first 50 characters
            # Parse the text
            parse_result = parser.parse(text)
            
            # Process each parse in the result
            for parse in parse_result['parses']:
                main_edge = parse['main_edge']
                
                # Add the main edge to the hypergraph
                hg.add(main_edge)
        
        print(f"Finished processing batch {i//batch_size + 1}")
    
    # Use pattern counter to output kinds of patterns found
    print("\nPattern Analysis:")
    pattern_counts = {}
    for edge in hg.all():
        pattern = edge.type()
        if pattern in pattern_counts:
            pattern_counts[pattern] += 1
        else:
            pattern_counts[pattern] = 1
    
    for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"Pattern '{pattern}': {count} occurrences")
    
    return hg


sample_text = examples

analyze_text(sample_text)
