from graphbrain import hypergraph
from graphbrain.parsers import create_parser
from graphbrain.processors import names

def analyze_text(text):
    # Create a parser
    parser = create_parser(lang='en')
    
    # Parse the text
    parses = parser.parse(text)
    
    # Create a hypergraph
    hg = hypergraph.Hypergraph()
    
    # Add parsed edges to the hypergraph
    for parse in parses:
        hg.add(parse['main_edge'])
    
    # Find all edges (relationships)
    edges = list(hg.all())
    
    # Print all edges
    for edge in edges:
        print(f"Edge: {edge}")
        print(f"  Main concepts: {names.main_concepts(edge)}")
        print(f"  Connector: {edge[0] if len(edge) > 0 else 'N/A'}")
        print()

    # Example of finding specific types of relationships
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
