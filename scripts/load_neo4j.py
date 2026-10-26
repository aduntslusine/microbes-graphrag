"""Load data/links.json into a local Neo4j database.

1. Start a local DBMS in Neo4j Desktop and note the password.
2. Use the project .venv (it points outside Documents to avoid iCloud lag).
3. Run: NEO4J_PASSWORD='your-password' python scripts/load_neo4j.py
"""

import json
import os
from pathlib import Path

from neo4j import GraphDatabase

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LINKS_FILE = DATA_DIR / "links.json"
URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
USER = os.environ.get("NEO4J_USER", "neo4j")
PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")

RELATION = {
    "produces": "PRODUCES",
    "consumes": "CONSUMES",
    "converts": "CONVERTS",
}


def load_links(tx, links):
    for link in links:
        rel = RELATION[link["relation"]]
        tx.run(
            f"""
            MERGE (m:Microbe {{name: $microbe}})
            MERGE (c:Metabolite {{name: $metabolite}})
            MERGE (m)-[r:{rel} {{
                pmcid: $pmcid,
                passage_index: $passage_index
            }}]->(c)
            SET r.quote = $quote
            """,
            microbe=link["microbe"],
            metabolite=link["metabolite"],
            pmcid=link["pmcid"],
            passage_index=link["passage_index"],
            quote=link["quote"],
        )


def main():
    links = json.loads(LINKS_FILE.read_text())["links"]
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    with driver.session() as session:
        session.execute_write(load_links, links)
        counts = session.run(
            """
            RETURN
              count { MATCH (m:Microbe) RETURN m } AS microbes,
              count { MATCH (c:Metabolite) RETURN c } AS metabolites,
              count { MATCH ()-[r]->() RETURN r } AS relationships
            """
        ).single()
    driver.close()
    print(f"loaded {len(links)} links from {LINKS_FILE}")
    print(
        f"graph now has {counts['microbes']} microbes, "
        f"{counts['metabolites']} metabolites, "
        f"{counts['relationships']} relationships"
    )


if __name__ == "__main__":
    main()
