import tempfile
from graphbrain.readers.txt import TxtReader
from graphbrain.parsers import create_parser
from data_level_0 import examples

def analyze_text(texts):
    # Create a parser
    parser = create_parser(lang='en')
    
    # Process texts
    edges = []
    for text in texts:
        print(f"\nAnalyzing text: {text[:50]}...")  # Print first 50 characters
        
        # Create a temporary file for the text
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False) as temp_file:
            temp_file.write(text)
            temp_file_path = temp_file.name
        
        # Create a TxtReader for this text
        reader = TxtReader(infile=temp_file_path, parser=parser, lang='en')
        
        # Parse the text
        parses = reader.read()
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
