from graphbrain import hypergraph
from graphbrain.parsers import create_parser
from graphbrain.processors import names

import sys
import spacy
import graphbrain

def print_versions():
    print(f"Python version: {sys.version}")
    print(f"spaCy version: {spacy.__version__}")

def analyze_text(text):
    # Create a parser
    parser = create_parser(lang='en')
    
    # Parse the text
    parse_result = parser.parse(text)
    
    # Print the parsed result
    print(f"Parsed result: {parse_result}")
    
    # Process each parse in the result
    for parse in parse_result['parses']:
        main_edge = parse['main_edge']
        print(f"\nMain edge: {main_edge}")
        print(f"  Main concepts: {names.main_concepts(main_edge)}")
        print(f"  Connector: {main_edge[0] if len(main_edge) > 0 else 'N/A'}")
        
        # Example of finding specific types of relationships
        if any(concept in str(main_edge).lower() for concept in ['tool', 'material', 'location']):
            print("Relationships involving tools, materials, or locations:")
            print(f"  {main_edge}")
    
    print()

# Example usage
sample_text = """
The carpenter used a hammer to drive nails into the wood in the workshop. 
The chef prepared the ingredients in the kitchen using a sharp knife.
"""

print_versions()

analyze_text(sample_text)
