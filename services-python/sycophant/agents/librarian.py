import os
import sys
import json
import ast
import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

# Setup Paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from routing.gateway import InferenceGateway

class Librarian:
    """
    The Semantic Indexer of DEAN-OS v5.1.
    Uses Nemotron 340B to perform 'Neural Zipping' on large legacy codebases,
    extracting Functional Pointer Graphs (FPG) to save to the Mnemosyne Vector DB.
    """
    def __init__(self, project_id: str = "default"):
        self.project_id = project_id

        # Load the embedding model (same one used by Mnemosyne)
        print("[LIBRARIAN] Loading Neural Embedding Model (all-MiniLM-L6-v2)...")
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')

        # Connect directly to the local Qdrant DB container
        qdrant_host = os.getenv("QDRANT_HOST", "127.0.0.1")
        self.db_client = QdrantClient(host=qdrant_host, port=6333)
        self.collection_name = "daen_docs"

        # Ensure the collection exists
        if not self.db_client.collection_exists(self.collection_name):
            self.db_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )

    def process_workspace(self, workspace_dir: str):
        """Scans a directory, extracts semantic graphs, and saves to the vector DB."""
        print(f"[LIBRARIAN] 📚 Initiating Neural Zip on workspace: {workspace_dir}")

        # [SMART FILTER] Ignore virtual environments and standard junk
        IGNORE_DIRS = {
            '__pycache__', 'venv', 'env', '.venv', '.env',
            'node_modules', 'site-packages', 'dist', 'build',
            '.git', '.vscode', '.idea'
        }

        for root, dirs, files in os.walk(workspace_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in IGNORE_DIRS]
            for file in files:
                if file.endswith(".py") and not file.startswith("."):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, workspace_dir).replace("\\", "/")

                    self._zip_and_store_file(file_path, rel_path)

    def _zip_and_store_file(self, file_path: str, rel_path: str):
        """Sends raw code to Nemotron, gets the FPG JSON, and vectorizes it."""
        print(f"[LIBRARIAN] Zipping {rel_path}...")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()

            # Skip empty files
            if not source_code.strip():
                return

            system_prompt = (
                "You are the DEAN-OS Neural Zipper. Your job is to read raw source code and extract a "
                "'Functional Pointer Graph' (FPG). This is a semantic summary of what the code does, "
                "intended to be stored in a Vector Database for future AI agents to query.\n\n"
                "CRITICAL RULES:\n"
                "1. Extract the class names, function signatures, and a 1-sentence summary of their purpose.\n"
                "2. DO NOT output the implementation logic.\n"
                "3. Output strictly as a JSON array of objects.\n"
                "4. No markdown formatting. No backticks."
            )

            user_prompt = (
                f"FILE: {rel_path}\n"
                f"CODE:\n{source_code}\n\n"
                f"Extract the FPG JSON:"
            )

            gateway = InferenceGateway()
            # [ROUTING] Explicitly route to Nemotron for large context ingestion
            response = gateway.generate(
                system=system_prompt,
                prompt=user_prompt,
                task_type="INGEST"
            )

            raw_json = response['response'].strip()

            try:
                fpg_data = json.loads(raw_json)

                # We save each function/class as its own point in the vector DB
                points = []
                # Use a simple hash of the file path + function name for a deterministic ID
                for item in fpg_data:
                    # Create a semantic text block that the AI can actually search against
                    semantic_text = f"File: {rel_path}. Entity: {item.get('name', 'unknown')}. Signature: {item.get('signature', '')}. Purpose: {item.get('purpose', '')}"

                    # Convert to math vector
                    vector = self.encoder.encode(semantic_text).tolist()

                    point_id = abs(hash(semantic_text)) % (10 ** 8) # Qdrant IDs need to be positive integers or UUIDs

                    points.append(PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={
                            "source": rel_path,
                            "text": semantic_text,
                            "project_id": self.project_id
                        }
                    ))

                if points:
                    self.db_client.upsert(collection_name=self.collection_name, points=points)
                    print(f"[LIBRARIAN] ✅ Saved {len(points)} semantic vectors for {rel_path}.")

            except json.JSONDecodeError as e:
                print(f"[LIBRARIAN ⚠️] Nemotron failed to output valid JSON for {rel_path}. Skipping. Error: {e}")

        except Exception as e:
            print(f"[LIBRARIAN ❌] Failed to zip {rel_path}: {e}")
