"""
Simple NLI (Natural Language Interface) Test

Demonstrates how NLI converts text into data format connectors.
"""

import sys
from pathlib import Path

# Add grapharchitect to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("="*70)
print("SIMPLE NLI TEST")
print("="*70)
print()

# Step 1: Import NLI components
print("Step 1: Importing NLI components...")
try:
    from grapharchitect.services.nli.natural_language_interface import NaturalLanguageInterface
    from grapharchitect.services.nli.nli_dataset_item import NLIDatasetItem
    from grapharchitect.services.embedding.simple_embedding_service import SimpleEmbeddingService
    from grapharchitect.entities.connectors.connector import Connector
    from grapharchitect.entities.connectors.task_representation import TaskRepresentation
    print("  SUCCESS: All components imported")
except ImportError as e:
    print(f"  ERROR: {e}")
    print("\n  Make sure grapharchitect library is accessible.")
    print("  Add to PYTHONPATH or install as package.")
    sys.exit(1)

print()

# Step 2: Initialize NLI
print("Step 2: Initializing NLI...")
embedding_service = SimpleEmbeddingService(dimension=384)
nli = NaturalLanguageInterface(embedding_service)
print("  SUCCESS: NLI initialized")
print()

# Step 3: Load examples from file (if available)
print("Step 3: Loading NLI examples...")
import json

examples_file = Path(__file__).parent / "data" / "nli_examples.json"

if examples_file.exists():
    with open(examples_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    examples = [NLIDatasetItem(**item) for item in data]
    nli.load_dataset(examples)
    print(f"  SUCCESS: Loaded {len(examples)} examples from file")
else:
    print(f"  WARNING: Examples file not found: {examples_file}")
    print("  Creating minimal dataset manually...")
    
    # Create minimal dataset
    examples = []
    
    # Example 1: Classification
    rep1 = TaskRepresentation()
    rep1.input_connector = Connector("text", "question")
    rep1.output_connector = Connector("text", "category")
    rep1.description = "Text classification"
    
    item1 = NLIDatasetItem(
        task_text="Classify this text",
        task_embedding=embedding_service.embed_text("Classify this text"),
        representation=rep1
    )
    examples.append(item1)
    
    # Example 2: QA
    rep2 = TaskRepresentation()
    rep2.input_connector = Connector("text", "question")
    rep2.output_connector = Connector("text", "answer")
    rep2.description = "Question answering"
    
    item2 = NLIDatasetItem(
        task_text="Answer this question",
        task_embedding=embedding_service.embed_text("Answer this question"),
        representation=rep2
    )
    examples.append(item2)
    
    # Example 3: Generation
    rep3 = TaskRepresentation()
    rep3.input_connector = Connector("text", "outline")
    rep3.output_connector = Connector("text", "content")
    rep3.description = "Content generation"
    
    item3 = NLIDatasetItem(
        task_text="Generate content",
        task_embedding=embedding_service.embed_text("Generate content"),
        representation=rep3
    )
    examples.append(item3)
    
    nli.load_dataset(examples)
    print(f"  SUCCESS: Created {len(examples)} minimal examples")

print()

# Step 4: Test parsing
print("Step 4: Testing NLI parsing...")
print()

test_queries = [
    "Classify this customer request into a category",
    "Answer the user's question about our product",
    "Generate a blog post about AI technology",
    "Find information about machine learning",
    "Check quality of this document"
]

for i, query in enumerate(test_queries, 1):
    print(f"Test {i}: \"{query}\"")
    
    try:
        # Parse the task
        representation = nli.parse_task(query)
        
        if representation:
            input_format = representation.input_connector.format
            output_format = representation.output_connector.format
            
            print(f"  Input:  {input_format}")
            print(f"  Output: {output_format}")
            print(f"  Status: SUCCESS")
        else:
            print(f"  Status: FAILED (no match)")
    
    except Exception as e:
        print(f"  Status: ERROR - {e}")
    
    print()

# Step 5: Detailed analysis
print("Step 5: Detailed analysis of one query...")
print()

detailed_query = "Analyze this text and classify it"
print(f"Query: \"{detailed_query}\"")
print()

try:
    # Get embedding
    query_embedding = embedding_service.embed_text(detailed_query)
    print(f"  Embedding dimension: {len(query_embedding)}")
    
    # Find similar examples
    retriever = nli.retriever
    similar = retriever.retrieve(
        task_text=detailed_query,
        task_embedding=query_embedding,
        k=3,
        available_data_types=None
    )
    
    print(f"  Found {len(similar)} similar examples:")
    print()
    
    for j, item in enumerate(similar, 1):
        print(f"    {j}. \"{item.task_text}\"")
        print(f"       {item.representation.input_connector.format} -> {item.representation.output_connector.format}")
    
    print()
    
    # Parse with NLI
    representation = nli.parse_task(detailed_query)
    
    if representation:
        print(f"  NLI prediction:")
        print(f"    Input:  {representation.input_connector.format}")
        print(f"    Output: {representation.output_connector.format}")
        print()
        print(f"  Explanation:")
        print(f"    NLI used k-NN to find similar tasks,")
        print(f"    then predicted connectors based on best match.")

except Exception as e:
    print(f"  ERROR: {e}")

print()

# Summary
print("="*70)
print("TEST COMPLETE")
print("="*70)
print()
print("NLI successfully converts natural language into structured connectors!")
print()
print("How it works:")
print("  1. Text query is embedded into vector")
print("  2. k-NN finds most similar examples from dataset")
print("  3. Connectors are predicted from best matches")
print("  4. Result used for graph-based tool planning")
print()
print("Next: Use these connectors in GraphStrategyFinder to find tool paths!")
print("="*70)
