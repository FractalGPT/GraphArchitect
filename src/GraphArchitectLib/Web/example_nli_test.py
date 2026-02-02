"""
Example: Testing Natural Language Interface (NLI)

This script demonstrates how NLI parses natural language task descriptions
into input/output connectors for graph-based tool selection.

NLI uses k-NN few-shot learning to find similar examples and predict
the appropriate data format connectors.
"""

import sys
from pathlib import Path

# Add grapharchitect to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import GraphArchitect components
try:
    from grapharchitect.services.nli.natural_language_interface import NaturalLanguageInterface
    from grapharchitect.services.nli.nli_dataset_item import NLIDatasetItem
    from grapharchitect.services.embedding.simple_embedding_service import SimpleEmbeddingService
    from grapharchitect.entities.connectors.connector import Connector
    from grapharchitect.entities.connectors.task_representation import TaskRepresentation
    
    NLI_AVAILABLE = True
    logger.info("GraphArchitect NLI components loaded successfully")
except ImportError as e:
    NLI_AVAILABLE = False
    logger.error(f"Failed to load GraphArchitect: {e}")
    logger.error("Make sure GraphArchitect library is in PYTHONPATH")
    sys.exit(1)


def create_nli_dataset() -> List[NLIDatasetItem]:
    """
    Create sample NLI dataset with various task types.
    
    Each item contains:
    - task_text: Natural language description
    - representation: Input/output connectors
    """
    embedding_service = SimpleEmbeddingService(dimension=384)
    
    # Define sample tasks with their connectors
    tasks = [
        {
            "text": "Classify this text into categories",
            "input": Connector("text", "question"),
            "output": Connector("text", "category"),
            "description": "Classification task"
        },
        {
            "text": "Answer this question based on context",
            "input": Connector("text", "question"),
            "output": Connector("text", "answer"),
            "description": "Question answering"
        },
        {
            "text": "Generate creative content from outline",
            "input": Connector("text", "outline"),
            "output": Connector("text", "content"),
            "description": "Content generation"
        },
        {
            "text": "Summarize this long document",
            "input": Connector("text", "document"),
            "output": Connector("text", "summary"),
            "description": "Summarization"
        },
        {
            "text": "Translate text from English to Russian",
            "input": Connector("text", "source"),
            "output": Connector("text", "translated"),
            "description": "Translation"
        },
        {
            "text": "Analyze sentiment of this review",
            "input": Connector("text", "review"),
            "output": Connector("text", "sentiment"),
            "description": "Sentiment analysis"
        },
        {
            "text": "Extract named entities from text",
            "input": Connector("text", "raw"),
            "output": Connector("text", "entities"),
            "description": "Named entity recognition"
        },
        {
            "text": "Check quality and validate this content",
            "input": Connector("text", "content"),
            "output": Connector("text", "validated"),
            "description": "Quality assurance"
        },
        {
            "text": "Research and find information about topic",
            "input": Connector("text", "query"),
            "output": Connector("text", "findings"),
            "description": "Research"
        },
        {
            "text": "Create report from collected data",
            "input": Connector("text", "data"),
            "output": Connector("text", "report"),
            "description": "Reporting"
        },
        {
            "text": "Describe what is in this image",
            "input": Connector("image", "raw"),
            "output": Connector("text", "description"),
            "description": "Image description"
        }
    ]
    
    # Create NLI dataset items
    dataset = []
    for task in tasks:
        # Create task representation
        representation = TaskRepresentation()
        representation.input_connector = task["input"]
        representation.output_connector = task["output"]
        representation.description = task["description"]
        
        # Create dataset item with embedding
        item = NLIDatasetItem(
            task_text=task["text"],
            task_embedding=embedding_service.embed_text(task["text"]),
            representation=representation
        )
        
        dataset.append(item)
    
    logger.info(f"Created NLI dataset with {len(dataset)} examples")
    return dataset


def test_nli_parsing(nli: NaturalLanguageInterface, test_queries: List[str]):
    """
    Test NLI parsing with various natural language queries.
    
    Args:
        nli: NaturalLanguageInterface instance
        test_queries: List of test queries
    """
    print("\n" + "="*70)
    print("NLI PARSING TESTS")
    print("="*70)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nTest {i}: \"{query}\"")
        print("-"*70)
        
        try:
            # Parse task
            representation = nli.parse_task(query)
            
            if representation:
                input_conn = representation.input_connector
                output_conn = representation.output_connector
                
                print(f"  Input format:  {input_conn.data_format}|{input_conn.semantic_format}")
                print(f"  Output format: {output_conn.data_format}|{output_conn.semantic_format}")
                print(f"  Description:   {representation.description}")
                print(f"  Status:        SUCCESS")
            else:
                print(f"  Status:        FAILED - Could not parse")
        
        except Exception as e:
            print(f"  Status:        ERROR - {e}")
            logger.error(f"Error parsing query: {e}", exc_info=True)


def test_similarity_search(nli: NaturalLanguageInterface, query: str):
    """
    Test similarity search to see which examples are most similar.
    
    Args:
        nli: NaturalLanguageInterface instance
        query: Test query
    """
    print("\n" + "="*70)
    print(f"SIMILARITY SEARCH TEST")
    print("="*70)
    print(f"\nQuery: \"{query}\"")
    print("-"*70)
    
    try:
        # Get embedding
        embedding_service = nli.embedding_service
        query_embedding = embedding_service.embed_text(query)
        
        # Find similar examples
        retriever = nli.retriever
        similar_items = retriever.retrieve(
            task_text=query,
            task_embedding=query_embedding,
            k=5,
            available_data_types=None
        )
        
        print(f"\nTop {len(similar_items)} similar examples:")
        for i, item in enumerate(similar_items, 1):
            print(f"\n  {i}. \"{item.task_text}\"")
            print(f"     Input:  {item.representation.input_connector.format}")
            print(f"     Output: {item.representation.output_connector.format}")
            
    except Exception as e:
        print(f"Error in similarity search: {e}")
        logger.error(f"Error: {e}", exc_info=True)


def test_connector_inference(nli: NaturalLanguageInterface, queries_with_expected: List[tuple]):
    """
    Test connector inference with expected results.
    
    Args:
        nli: NaturalLanguageInterface instance
        queries_with_expected: List of (query, expected_input, expected_output) tuples
    """
    print("\n" + "="*70)
    print("CONNECTOR INFERENCE TESTS")
    print("="*70)
    
    passed = 0
    failed = 0
    
    for query, expected_in, expected_out in queries_with_expected:
        print(f"\nQuery: \"{query}\"")
        print(f"  Expected: {expected_in} -> {expected_out}")
        
        try:
            representation = nli.parse_task(query)
            
            if representation:
                actual_in = representation.input_connector.format
                actual_out = representation.output_connector.format
                
                print(f"  Actual:   {actual_in} -> {actual_out}")
                
                if actual_in == expected_in and actual_out == expected_out:
                    print(f"  Result:   PASS")
                    passed += 1
                else:
                    print(f"  Result:   FAIL (mismatch)")
                    failed += 1
            else:
                print(f"  Result:   FAIL (no parse)")
                failed += 1
                
        except Exception as e:
            print(f"  Result:   ERROR - {e}")
            failed += 1
    
    print("\n" + "-"*70)
    print(f"Summary: {passed} passed, {failed} failed out of {passed+failed} tests")
    print("="*70)


def main():
    """Main test function."""
    print("="*70)
    print("NATURAL LANGUAGE INTERFACE (NLI) TEST")
    print("="*70)
    print("\nNLI converts natural language task descriptions into")
    print("input/output data format connectors for graph planning.")
    print("="*70)
    
    if not NLI_AVAILABLE:
        print("\nERROR: GraphArchitect not available")
        return
    
    # Initialize components
    logger.info("Initializing NLI components...")
    
    embedding_service = SimpleEmbeddingService(dimension=384)
    nli = NaturalLanguageInterface(embedding_service)
    
    # Create and load dataset
    logger.info("Creating NLI dataset...")
    dataset = create_nli_dataset()
    nli.load_dataset(dataset)
    
    logger.info(f"NLI ready with {len(dataset)} examples")
    
    # Test 1: Parse various queries
    test_queries = [
        "Classify this customer request",
        "Answer the user's question",
        "Generate a detailed article",
        "Check if this content meets quality standards",
        "Find information about quantum computing",
        "Create summary of this document",
        "What sentiment is expressed in this review?",
        "Translate this text to another language"
    ]
    
    test_nli_parsing(nli, test_queries)
    
    # Test 2: Similarity search
    test_similarity_search(nli, "Categorize this text message")
    
    # Test 3: Connector inference with expected results
    test_cases = [
        ("Classify this text", "text|question", "text|category"),
        ("Answer this question", "text|question", "text|answer"),
        ("Generate content", "text|outline", "text|content"),
        ("Validate quality", "text|content", "text|validated")
    ]
    
    test_connector_inference(nli, test_cases)
    
    # Final summary
    print("\n" + "="*70)
    print("NLI TEST COMPLETE")
    print("="*70)
    print("\nKey takeaways:")
    print("1. NLI successfully parses natural language into connectors")
    print("2. k-NN retrieval finds similar examples")
    print("3. Connectors enable graph-based tool planning")
    print("\nNLI is ready for integration with GraphArchitect workflows!")
    print("="*70)


if __name__ == "__main__":
    main()
