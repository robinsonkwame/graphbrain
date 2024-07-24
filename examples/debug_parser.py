import sys
from graphbrain import hgraph
from graphbrain.parsers import create_parser
from graphbrain.readers.txt import TxtReader

def main():
    infile = 'examples/text/positive.txt'
    hg_file = 'examples/debug_text.db'
    lang = 'en'

    print(f"Processing file: {infile}")
    print(f"Output hypergraph: {hg_file}")
    print(f"Language: {lang}")

    hg = hgraph(hg_file)
    parser = create_parser(lang=lang, lemmas=True)

    reader = TxtReader(infile, hg=hg, lang=lang, parser=parser)
    
    print("\nReading file contents:")
    with open(infile, 'r') as f:
        print(f.read())

    print("\nParsing and adding to hypergraph:")
    reader.read()

    print("\nHypergraph contents:")
    for edge in hg.all():
        print(edge)

    print(f"\nTotal edges in hypergraph: {sum(1 for _ in hg.all())}")

    hg.close()

if __name__ == "__main__":
    main()
