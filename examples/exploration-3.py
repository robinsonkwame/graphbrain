from graphbrain import hgraph, hedge

# Create a hypergraph from the existing database
hg = hgraph('examples/both.db')

# Complex Pattern with variables
complex_pattern = hedge("""
(is/Pd.sc.|f--3s-/en
  (var */Cc.s PART)
  (var
    (any
      (of/Br.ma/en (var */Cc.s TYPE) (var */Cc.s WHOLE))
      (within/Br.ma/en (var */Cc.s TYPE) (var */Cc.s WHOLE))
      (in/Br.ma/en (var */Cc.s TYPE) (var */Cc.s WHOLE))
    )
    RELATION))
""")

def process_pattern(pattern, version):
    print(f"\nProcessing with {version}:")
    print(f"Pattern: {pattern}")
    
    matches = list(hg.match(pattern))
    
    if matches:
        print(f"Number of matches: {len(matches)}")
        for i, match in enumerate(matches):
            print(f"\nMatch {i + 1}:")
            print(f"  Full match: {match[0]}")
            # Print variable bindings
            for var_dict in match[1]:
                for var, value in var_dict.items():
                    print(f"  {var}: {value}")
    else:
        print("No matches found.")

# Process with complex pattern
process_pattern(complex_pattern, "Complex Pattern")

# Close the hypergraph when done
hg.close()