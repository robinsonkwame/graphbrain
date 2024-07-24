from graphbrain import *

def analyze_text(text):
    # Parse the text
    parser = Parser(lang='en')
    parses = list(parser.parse(text))
    
    # Extract hypergraph
    hg = Hypergraph()
    for parse in parses:
        hg.add(parse['main_edge'])
    
    # Find all edges (relationships)
    edges = list(hg.all())
    
    # Print all edges
    for edge in edges:
        print(f"Edge: {edge}")
        print(f"  Main concepts: {main_concepts(edge)}")
        print(f"  Connector: {edge.connector()}")
        print()

    # Example of finding specific types of relationships
    # This is a simplified example and may need to be adapted based on your specific needs
    tool_material_location_edges = [
        edge for edge in edges 
        if any(concept in str(edge).lower() for concept in ['tool', 'material', 'location'])
    ]
    
    print("Relationships involving tools, materials, or locations:")
    for edge in tool_material_location_edges:
        print(f"  {edge}")

# Example usage
sample_text = """
The carpenter used a hammer to drive nails into the wood in the workshop. 
The chef prepared the ingredients in the kitchen using a sharp knife.
"""

analyze_text(sample_text)
