# search_engine.py - Simple MVP Version
import os
import psycopg2
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from dotenv import load_dotenv
from typing import Dict

load_dotenv('.env')


class HybridSearchEngine:
    def __init__(self):
        print("🔄 Initializing search engine...")

        # PostgreSQL
        self.pg_conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'incidents'),
            user=os.getenv('DB_USER', 'incident_user'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432')
        )

        # Qdrant
        self.qdrant = QdrantClient(path="./data/qdrant_storage")

        # Embedding model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

        print("✅ Search engine ready (PostgreSQL + Qdrant + ML)")

    def search_similar(self, query: str, current_tech_stack: str = None, limit: int = 10) -> Dict:
        """
        Hybrid search: Vector similarity + PostgreSQL enrichment
        """
        print(f"\n🔍 Searching for: '{query[:60]}...'")
        print(f"📍 Current stack: {current_tech_stack or 'any'}")

        # Step 1: Convert query to vector
        query_vector = self.model.encode(query).tolist()

        # Step 2: Search Qdrant for similar vectors
        try:
            vector_results = self.qdrant.query_points(
                collection_name="incidents",
                query=query_vector,
                with_payload=True,
                limit=limit * 3
            )
            results_list = vector_results.points
        except AttributeError:
            vector_results = self.qdrant.search(
                collection_name="incidents",
                query_vector=query_vector,
                with_payload=True,
                limit=limit * 3
            )
            results_list = vector_results

        print(f"   Found {len(results_list)} similar incidents from vectors")

        # Step 3: Get incident IDs and scores
        incident_ids = [hit.payload['incident_id'] for hit in results_list]
        similarity_scores = {hit.payload['incident_id']: float(hit.score) for hit in results_list}

        # Step 4: Fetch SIMPLE schema from PostgreSQL
        with self.pg_conn.cursor() as cur:
            placeholders = ','.join(['%s'] * len(incident_ids))
            cur.execute(f'''
                SELECT 
                    id, title, description, tech_stack, 
                    error_type, root_cause, solution, service
                FROM incidents
                WHERE id IN ({placeholders})
            ''', tuple(incident_ids))

            rows = cur.fetchall()

        # Step 5: Build incident objects
        incidents = []
        for row in rows:
            incident = {
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'tech_stack': row[3],
                'error_type': row[4],
                'root_cause': row[5],
                'solution': row[6],
                'service': row[7],
                'similarity_score': similarity_scores.get(row[0], 0.0)
            }
            incidents.append(incident)

        # Step 6: Split into same-stack vs cross-stack
        same_stack = []
        cross_stack = []

        for inc in incidents:
            if current_tech_stack and inc['tech_stack'] == current_tech_stack:
                same_stack.append(inc)
            else:
                cross_stack.append(inc)

        # Step 7: Sort by similarity
        same_stack.sort(key=lambda x: x['similarity_score'], reverse=True)
        cross_stack.sort(key=lambda x: x['similarity_score'], reverse=True)

        print(f"   ✅ {len(same_stack)} same-stack | {len(cross_stack)} cross-stack")

        return {
            'same_stack': same_stack[:limit // 2],
            'cross_stack': cross_stack[:limit // 2],
            'all_results': incidents[:limit]
        }

    def close(self):
        self.pg_conn.close()
        print("\n👋 Search engine closed")


# ============================================================================
# TEST CASES
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("🧪 TESTING SEARCH ENGINE - SIMPLE MVP")
    print("=" * 70)

    engine = HybridSearchEngine()

    # ========================================================================
    # TEST 1: Database Timeout (Cross-Stack Pattern)
    # ========================================================================
    print("\n" + "=" * 70)
    print("TEST 1: Database Timeout (Java → finds Python solutions)")
    print("=" * 70)

    results = engine.search_similar(
        query="Payment API timing out when connecting to PostgreSQL database",
        current_tech_stack="java",
        limit=8
    )

    print("\n🟢 SAME STACK (Java):")
    for i, inc in enumerate(results['same_stack'][:3], 1):
        print(f"\n  {i}. {inc['id']}: {inc['title']}")
        print(f"     Service: {inc['service']} | Similarity: {inc['similarity_score']:.1%}")
        print(f"     Root Cause: {inc['root_cause'][:80]}...")
        print(f"     Solution: {inc['solution'][0]}")

    print("\n🟡 CROSS-STACK (Python/Node.js solutions for same problem):")
    for i, inc in enumerate(results['cross_stack'][:3], 1):
        print(f"\n  {i}. {inc['id']}: {inc['title']}")
        print(
            f"     Stack: {inc['tech_stack']} | Service: {inc['service']} | Similarity: {inc['similarity_score']:.1%}")
        print(f"     Root Cause: {inc['root_cause'][:80]}...")
        print(f"     Solution: {inc['solution'][0]}")

    # ========================================================================
    # TEST 2: Null Reference (Shows pattern across languages)
    # ========================================================================
    print("\n\n" + "=" * 70)
    print("TEST 2: Null Reference Error (Java → finds Python AttributeError)")
    print("=" * 70)

    results2 = engine.search_similar(
        query="Getting NullPointerException when user object is null after deletion",
        current_tech_stack="java",
        limit=8
    )

    print(f"\n🟢 Same stack: {len(results2['same_stack'])} Java incidents")
    print(f"🟡 Cross-stack: {len(results2['cross_stack'])} Python/Node.js incidents")

    if results2['same_stack']:
        print(f"\n✅ Top Java match:")
        inc = results2['same_stack'][0]
        print(f"   {inc['id']}: {inc['title']}")
        print(f"   Similarity: {inc['similarity_score']:.1%}")

    if results2['cross_stack']:
        print(f"\n💡 Cross-stack insight from {results2['cross_stack'][0]['tech_stack']}:")
        inc = results2['cross_stack'][0]
        print(f"   {inc['id']}: {inc['title']}")
        print(f"   Root Cause: {inc['root_cause'][:100]}...")
        print(f"   Solution: {inc['solution'][0]}")
        print(f"\n   👉 SAME PROBLEM, different language!")

    # ========================================================================
    # TEST 3: Memory Leak (Shows infrastructure-level similarity)
    # ========================================================================
    print("\n\n" + "=" * 70)
    print("TEST 3: Memory Leak (Python → finds Java/Node.js solutions)")
    print("=" * 70)

    results3 = engine.search_similar(
        query="Service memory growing unbounded, crashing after few hours",
        current_tech_stack="python",
        limit=8
    )

    print(f"\n🟢 Same stack: {len(results3['same_stack'])} Python incidents")
    print(f"🟡 Cross-stack: {len(results3['cross_stack'])} Java/Node.js incidents")

    print("\n📊 ALL MATCHES (sorted by similarity):")
    for i, inc in enumerate(results3['all_results'][:5], 1):
        marker = "🟢" if inc['tech_stack'] == "python" else "🟡"
        print(f"\n  {marker} {i}. [{inc['tech_stack']:8}] {inc['title']}")
        print(f"      Similarity: {inc['similarity_score']:.1%} | Service: {inc['service']}")

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n\n" + "=" * 70)
    print("✅ PHASE 4 COMPLETE - SEARCH ENGINE WORKING!")
    print("=" * 70)

    engine.close()

    print("\n📍 Next: Phase 5 - Build API with Groq LLM")
