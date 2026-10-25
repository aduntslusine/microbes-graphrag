The project explores how gut microbes are connected through metabolites in scientific literature. It extracts evidence-backed relationships into a knowledge graph, finds connections between two microbes, and explains them with citations to the exact supporting passages. When the paper collection contains no supported connection, it says so.

The first version is a small prototype on a few papers, built to learn the stack: retrieval-augmented generation, LLM API calls, FastAPI, Neo4j, and graph algorithms.

To do

- [x] choose papers
  - PMC522113
  - PMC1472403
  - PMC7702098
- [x] fetch those papers and split them into passages for retrieval (`python3 fetch_passages.py`)
- [x] build a small RAG index over the passages (`.venv/bin/python build_index.py`)
- [ ] call an LLM to extract microbe–metabolite links, each tied to a supporting passage
- [ ] load the extracted links into Neo4j
- [ ] expose a FastAPI endpoint that takes two microbes
- [ ] search the graph for a path between them
- [ ] return an explanation with citations, or say that no supported connection was found
