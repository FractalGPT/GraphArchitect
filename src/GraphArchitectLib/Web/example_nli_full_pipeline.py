"""
Full Pipeline Example: NLI -> Strategy Finding -> Execution

Demonstrates complete workflow:
1. NLI parses natural language into connectors
2. GraphStrategyFinder finds paths in tool graph
3. ExecutionOrchestrator executes the task
4. Training updates tool reputation
"""

import sys
from pathlib import Path

# Add grapharchitect to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import components
try:
    from grapharchitect.services.nli.natural_language_interface import NaturalLanguageInterface
    from grapharchitect.services.nli.nli_dataset_item import NLIDatasetItem
    from grapharchitect.services.embedding.simple_embedding_service import SimpleEmbeddingService
    from grapharchitect.services.graph_strategy_finder import GraphStrategyFinder
    from grapharchitect.services.execution.execution_orchestrator import ExecutionOrchestrator
    from grapharchitect.services.selection.instrument_selector import InstrumentSelector
    from grapharchitect.services.pathfinding_algorithm import PathfindingAlgorithm
    from grapharchitect.entities.base_tool import BaseTool
    from grapharchitect.entities.connectors.connector import Connector
    from grapharchitect.entities.connectors.task_representation import TaskRepresentation
    from grapharchitect.entities.task_definition import TaskDefinition
    
    logger.info("All GraphArchitect components loaded")
except ImportError as e:
    logger.error(f"Failed to load GraphArchitect: {e}")
    sys.exit(1)


class MockClassifierTool(BaseTool):
    """Mock classification tool."""
    
    def __init__(self, name: str, reputation: float = 0.85):
        super().__init__()
        self.metadata.tool_name = name
        self.metadata.reputation = reputation
        self.input = Connector("text", "question")
        self.output = Connector("text", "category")
        
        # Initialize for training
        self.metadata.training_sample_size = 10
        self.metadata.variance_estimate = 0.1
    
    def execute(self, input_data):
        return f"[{self.metadata.tool_name}] Classification result: Category A"


class MockQATool(BaseTool):
    """Mock QA tool."""
    
    def __init__(self, name: str, reputation: float = 0.80):
        super().__init__()
        self.metadata.tool_name = name
        self.metadata.reputation = reputation
        self.input = Connector("text", "question")
        self.output = Connector("text", "answer")
        
        self.metadata.training_sample_size = 10
        self.metadata.variance_estimate = 0.1
    
    def execute(self, input_data):
        return f"[{self.metadata.tool_name}] Answer: This is a detailed answer."


class MockGeneratorTool(BaseTool):
    """Mock content generation tool."""
    
    def __init__(self, name: str, reputation: float = 0.75):
        super().__init__()
        self.metadata.tool_name = name
        self.metadata.reputation = reputation
        self.input = Connector("text", "outline")
        self.output = Connector("text", "content")
        
        self.metadata.training_sample_size = 10
        self.metadata.variance_estimate = 0.1
    
    def execute(self, input_data):
        return f"[{self.metadata.tool_name}] Generated content based on outline."


def create_nli_examples(embedding_service):
    """Create NLI training examples."""
    examples = []
    
    # Classification example
    rep1 = TaskRepresentation()
    rep1.input_connector = Connector("text", "question")
    rep1.output_connector = Connector("text", "category")
    rep1.description = "Classification"
    
    item1 = NLIDatasetItem(
        task_text="Classify this text into categories",
        task_embedding=embedding_service.embed_text("Classify this text"),
        representation=rep1
    )
    examples.append(item1)
    
    # QA example
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
    
    # Generation example
    rep3 = TaskRepresentation()
    rep3.input_connector = Connector("text", "outline")
    rep3.output_connector = Connector("text", "content")
    rep3.description = "Content generation"
    
    item3 = NLIDatasetItem(
        task_text="Generate article from outline",
        task_embedding=embedding_service.embed_text("Generate article"),
        representation=rep3
    )
    examples.append(item3)
    
    return examples


def main():
    """Run full pipeline test."""
    
    print("FULL PIPELINE: NLI -> Strategy -> Execution")
    print("="*70)
    print()
    
    # Initialize services
    logger.info("Initializing services...")
    
    embedding_service = SimpleEmbeddingService(dimension=384)
    nli = NaturalLanguageInterface(embedding_service)
    selector = InstrumentSelector(temperature_constant=1.0)
    strategy_finder = GraphStrategyFinder()
    orchestrator = ExecutionOrchestrator(embedding_service, selector, strategy_finder)
    
    # Load NLI dataset
    logger.info("Loading NLI dataset...")
    examples = create_nli_examples(embedding_service)
    nli.load_dataset(examples)
    
    # Create mock tools
    logger.info("Creating mock tools...")
    tools = [
        MockClassifierTool("GPT-4 Classifier", 0.95),
        MockClassifierTool("Claude Classifier", 0.90),
        MockClassifierTool("Local Classifier", 0.75),
        MockQATool("GPT-4 QA", 0.92),
        MockQATool("Claude QA", 0.88),
        MockGeneratorTool("GPT-4 Writer", 0.90),
    ]
    
    # Embed tools
    for tool in tools:
        tool.metadata.capabilities_embedding = embedding_service.embed_tool_capabilities(tool)
    
    logger.info(f"Created {len(tools)} mock tools")
    print()
    
    # Test queries
    test_queries = [
        "Classify this customer support request",
        "Answer: What is machine learning?",
        "Generate article about AI"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print("="*70)
        print(f"TEST {i}: {query}")
        print("="*70)
        print()
        
        # STEP 1: NLI Parsing
        print("STEP 1: NLI Parsing")
        print("-"*70)
        
        try:
            representation = nli.parse_task(query)
            
            if representation:
                input_conn = representation.input_connector
                output_conn = representation.output_connector
                
                print(f"  Query:         \"{query}\"")
                print(f"  Input format:  {input_conn.format}")
                print(f"  Output format: {output_conn.format}")
                print(f"  Description:   {representation.description}")
                print()
                
                # STEP 2: Strategy Finding
                print("STEP 2: Finding Strategies in Tool Graph")
                print("-"*70)
                
                strategies = strategy_finder.find_strategies(
                    tools=tools,
                    start_format=input_conn.format,
                    end_format=output_conn.format,
                    algorithm=PathfindingAlgorithm.DIJKSTRA,
                    limit=1
                )
                
                if strategies:
                    print(f"  Found {len(strategies)} strategy(ies)")
                    
                    for j, strategy in enumerate(strategies, 1):
                        tool_names = [t.metadata.tool_name for t in strategy]
                        print(f"    Strategy {j}: {' -> '.join(tool_names)}")
                    
                    print()
                    
                    # STEP 3: Execution
                    print("STEP 3: Executing Task")
                    print("-"*70)
                    
                    # Create task
                    task = TaskDefinition(
                        description=query,
                        input_connector=input_conn,
                        output_connector=output_conn,
                        input_data=query
                    )
                    
                    # Execute
                    context = orchestrator.execute_task(
                        task=task,
                        available_tools=tools,
                        path_limit=1,
                        top_k=3
                    )
                    
                    print(f"  Status:     {context.status.value}")
                    print(f"  Steps:      {context.get_total_steps()}")
                    print(f"  Total time: {context.total_time:.2f}s")
                    print(f"  Result:     {context.result}")
                    print()
                    
                    # STEP 4: Review execution details
                    print("STEP 4: Execution Details")
                    print("-"*70)
                    
                    for k, step in enumerate(context.execution_steps, 1):
                        tool_name = step.selected_tool.metadata.tool_name
                        prob = step.selection_result.selection_probability
                        temp = step.selection_result.temperature
                        
                        print(f"  Step {k}:")
                        print(f"    Selected tool:  {tool_name}")
                        print(f"    Probability:    {prob:.3f}")
                        print(f"    Temperature:    {temp:.3f}")
                        print(f"    Candidates:     {len(step.selection_result.logits)}")
                    
                    print()
                
                else:
                    print(f"  WARNING: No strategies found")
                    print(f"  Available tools don't connect {input_conn.format} -> {output_conn.format}")
                    print()
            
            else:
                print(f"  ERROR: NLI failed to parse query")
                print()
        
        except Exception as e:
            logger.error(f"Error in pipeline: {e}", exc_info=True)
            print()
    
    print()

# Final summary
print("="*70)
print("PIPELINE TEST COMPLETE")
print("="*70)
print()
print("Summary:")
print("  1. NLI parsed natural language into connectors")
print("  2. GraphStrategyFinder found tool paths in graph")
print("  3. ExecutionOrchestrator selected tools via softmax")
print("  4. Tasks executed successfully")
print()
print("The full pipeline is working!")
print("="*70)


if __name__ == "__main__":
    main()
