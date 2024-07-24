from graphbrain import hypergraph
from graphbrain.parsers import create_parser
from graphbrain.processors import names

import sys
import spacy
import graphbrain

def print_versions():
    print(f"Python version: {sys.version}")
    print(f"spaCy version: {spacy.__version__}")

def analyze_text(texts, batch_size=100):
    # Create a parser
    parser = create_parser(lang='en')
    
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
                
                print(
                    f" ... concept: \t{concept}"
                )
                # Example of finding specific types of relationships
                if any(concept in str(main_edge).lower() for concept in ['tool', 'material', 'location']):
                    print("Relationships involving tools, materials, or locations:")
                    print(f"  {main_edge}")
        
        print(f"Finished processing batch {i//batch_size + 1}")

# Example usage
sample_text = [
"The carpenter used a hammer to drive nails into the wood in the workshop. ",
"The carpenter used a hammer to drive nails into the wood in the workshop. ",
"The sun rises in the east and sets in the west every day."
]

print_versions()

analyze_text(sample_text)
