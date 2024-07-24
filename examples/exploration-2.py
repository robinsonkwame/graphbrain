from graphbrain import hgraph
from graphbrain.patterns import PatternCounter
from graphbrain.hyperedge import Atom

# Open the hypergraph
hg = hgraph('examples/text.db')

# Create a PatternCounter
pc = PatternCounter()

# Count patterns for all primary edges
for edge in hg.all():
    if hg.is_primary(edge):
        pc.count(edge)

# Print the top 10 most common patterns
print("Top 10 most common patterns:")
for pattern, count in pc.patterns.most_common(10):
    print(f"{pattern}: {count}")

# Print total number of unique patterns
print(f"\nTotal unique patterns: {len(pc.patterns.counts)}")

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
