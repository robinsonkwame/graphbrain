from graphbrain import hgraph, hedge
from graphbrain.parsers import create_parser

# Create a hypergraph and parser
hg = hgraph('example.db')
parser = create_parser(lang='en')

# Define the pattern for part-whole relationships
pattern = hedge('(is/Pd * (of/T */C))')

positive_examples = [
    "The wheel is part of the car.",
    "A chapter is a component of a book.",
    "The heart is an organ within the human body.",
    "The kitchen is a room in the house.",
    "The CPU is an essential element of a computer."
]

negative_examples = [
    "The painted wall shined blue.",
    "Water boils at 100 degrees Celsius.",
    "Dogs are loyal companions.",
    "The Eiffel Tower is located in Paris.",
    "Photosynthesis is a process used by plants to create energy."
]

def process_examples(examples):
    for example in examples:
        parse_results = parser.parse(example)
        edge = parse_results['main_edge']
        matches = hg.match(pattern, edge)
        if matches:
            print(f"Matched: {example}")
            for match in matches:
                print(f"  PART: {match[1]}")
                print(f"  WHOLE: {match[2][1]}")
        else:
            print(f"Did not match: {example}")

print("Processing positive examples:")
process_examples(positive_examples)

print("\nProcessing negative examples:")
process_examples(negative_examples)

# Close the hypergraph when done
hg.close()
