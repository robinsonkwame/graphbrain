from graphbrain import hedge
from graphbrain.patterns import match_pattern

# Assuming you have a function to parse text into hyperedges
def parse_text(text):
    # Implementation depends on your specific parser
    pass

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
    "The Eiffel Tower is not located in Paris.",
    "Photosynthesis is a process used by plants to create energy."
]

for example in positive_examples + negative_examples:
    edge = parse_text(example)
    matches = match_pattern(edge, pattern)
    if matches:
        print(f"Matched: {example}")
        for match in matches:
            print(f"  PART: {match['PART']}")
            print(f"  WHOLE: {match['WHOLE']}")
    else:
        print(f"Did not match: {example}")