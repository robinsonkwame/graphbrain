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
    parse = parser.parse(text)
    
    # Print the parsed edge
    print(f"Parsed edge: {parse}")
    print(f"  Main concepts: {names.main_concepts(parse)}")
    print(f"  Connector: {parse[0] if len(parse) > 0 else 'N/A'}")
    print()

    # Example of finding specific types of relationships
    if any(concept in str(parse).lower() for concept in ['tool', 'material', 'location']):
        print("Relationships involving tools, materials, or locations:")
        print(f"  {parse}")

# Example usage
sample_text = """
The carpenter used a hammer to drive nails into the wood in the workshop. 
The chef prepared the ingredients in the kitchen using a sharp knife.
"""

print_versions()

analyze_text(sample_text)
