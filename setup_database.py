# setup_database_simple.py
import os
import json
import psycopg2
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv('.env')


class SimpleDatabase:
    def __init__(self):
        self.pg_conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432')
        )
        self.qdrant = QdrantClient(path="./data/qdrant_storage")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Databases connected")

    def setup(self):
        # Drop and recreate table
        with self.pg_conn.cursor() as cur:
            cur.execute('DROP TABLE IF EXISTS incidents CASCADE')
            cur.execute('''
                CREATE TABLE incidents (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    description TEXT,
                    tech_stack TEXT,
                    error_type TEXT,
                    root_cause TEXT,
                    solution TEXT[],
                    service TEXT
                )
            ''')
            cur.execute('CREATE INDEX ON incidents(tech_stack)')
            cur.execute('CREATE INDEX ON incidents(error_type)')
            self.pg_conn.commit()

        # Recreate Qdrant
        try:
            self.qdrant.delete_collection("incidents")
        except:
            pass
        self.qdrant.create_collection(
            collection_name="incidents",
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        print("✅ Tables created")

    def import_data(self):
        with open('data/incidents.json') as f:
            incidents = json.load(f)

        # Generate embeddings
        texts = [f"{inc['title']} {inc['description']} {inc['root_cause']}"
                 for inc in incidents]
        embeddings = self.model.encode(texts, show_progress_bar=True)

        # Insert to PostgreSQL
        with self.pg_conn.cursor() as cur:
            for inc in incidents:
                cur.execute('''
                    INSERT INTO incidents VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ''', (inc['id'], inc['title'], inc['description'],
                      inc['tech_stack'], inc['error_type'], inc['root_cause'],
                      inc['solution'], inc['service']))
            self.pg_conn.commit()

        # Insert to Qdrant
        points = [
            PointStruct(
                id=i,
                vector=embeddings[i].tolist(),
                payload={'incident_id': inc['id'], 'tech_stack': inc['tech_stack']}
            )
            for i, inc in enumerate(incidents)
        ]
        self.qdrant.upsert(collection_name="incidents", points=points)

        print(f"✅ Imported {len(incidents)} incidents")


if __name__ == '__main__':
    db = SimpleDatabase()
    db.setup()
    db.import_data()
    print("✅ SETUP COMPLETE!")
