import os
from graphbrain import hgraph
from graphbrain.patterns import PatternCounter
from graphbrain.hyperedge import Atom

"""
Assume we created a db with the text command, e.g.

    graphbrain txt --infile examples/text/negative.txt --hg examples/text_n.db --lang en
"""

# Open the hypergraph
hg = hgraph('examples/text.db')

# Check database file size
print(f"Database file size: {os.path.getsize('examples/text.db')} bytes")

# Count edges manually
edge_count = sum(1 for _ in hg.all())
primary_edge_count = sum(1 for edge in hg.all() if hg.is_primary(edge))

print(f"Number of edges: {edge_count}")
print(f"Number of primary edges: {primary_edge_count}")

# Print some sample edges
print("\nSample edges:")
for edge in list(hg.all())[:5]:
    print(edge)

# Create a PatternCounter
pc = PatternCounter()

# Count patterns for all primary edges
try:
    for edge in hg.all():
        if hg.is_primary(edge):
            pc.count(edge)
except Exception as e:
    print(f"Error occurred while processing edges: {e}")

print(f"\nTotal number of edges processed: {edge_count}")
print(f"Number of primary edges: {primary_edge_count}")

# Print the top 10 most common patterns
print("\nTop 10 most common patterns:")
for pattern, count in pc.patterns.most_common(10):
    print(f"{pattern}: {count}")

# Print total number of unique patterns
print(f"\nTotal unique patterns: {len(pc.patterns)}")

# Analyze atom types
atom_types = {}
for edge in hg.all():
    if isinstance(edge, Atom):
        atom_type = edge.type()
        atom_types[atom_type] = atom_types.get(atom_type, 0) + 1

print("\nAtom types distribution:")
for atom_type, count in sorted(atom_types.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"{atom_type}: {count}")

# Analyze edge depths
edge_depths = {}
for edge in hg.all():
    depth = edge.depth()
    edge_depths[depth] = edge_depths.get(depth, 0) + 1

print("\nEdge depth distribution:")
for depth, count in sorted(edge_depths.items()):
    print(f"Depth {depth}: {count}")

# Close the hypergraph
hg.close()