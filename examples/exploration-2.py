from graphbrain import hgraph
from graphbrain.patterns import PatternCounter

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

# # Print total number of unique patterns
# print(f"\nTotal unique patterns: {len(pc.pattern_counts)}")

# Close the hypergraph
hg.close()