from graphbrain.readers.txt import TxtReader
from graphbrain.parsers import create_parser
from data_level_0 import examples

def analyze_text(texts):
    # Create a parser
    parser = create_parser(lang='en')
    
    # Create a TxtReader
    reader = TxtReader(parser=parser, lang='en')
    
    # Process texts
    edges = []
    for text in texts:
        print(f"\nAnalyzing text: {text[:50]}...")  # Print first 50 characters
        # Parse the text
        parses = reader.read_text(text)
        edges.extend(parses)
    
    # Use pattern counter to output kinds of patterns found
    print("\nPattern Analysis:")
    pattern_counts = {}
    for edge in edges:
        pattern = edge.type()
        if pattern in pattern_counts:
            pattern_counts[pattern] += 1
        else:
            pattern_counts[pattern] = 1
    
    for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"Pattern '{pattern}': {count} occurrences")
    
    return edges

sample_text = examples

analyze_text(sample_text)
