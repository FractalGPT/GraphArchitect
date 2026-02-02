"""
Agent library - loads agents from database.
No hardcoded agents, all data comes from SQLite database.
"""
import logging
from typing import List, Optional
from models import Agent
from repository import get_repository

logger = logging.getLogger(__name__)


def get_all_agents(use_db: bool = True) -> List[Agent]:
    """
    Get all agents from database.
    
    Args:
        use_db: If True, load from database. If False, return empty list.
        
    Returns:
        List of Agent objects from database.
    """
    if not use_db:
        logger.warning("Database disabled, returning empty agent list")
        return []
    
    try:
        repo = get_repository()
        agents = repo.get_all_agents()
        
        if not agents:
            logger.warning("No agents found in database. Run: python db_manager.py load_agents")
            return []
        
        logger.info(f"Loaded {len(agents)} agents from database")
        return agents
        
    except Exception as e:
        logger.error(f"Failed to load agents from database: {e}")
        return []


def get_agent(agent_id: str) -> Optional[Agent]:
    """
    Get specific agent by ID from database.
    
    Args:
        agent_id: Agent identifier
        
    Returns:
        Agent object if found, None otherwise.
    """
    try:
        repo = get_repository()
        agent = repo.get_agent(agent_id)
        
        if not agent:
            logger.warning(f"Agent not found: {agent_id}")
        
        return agent
        
    except Exception as e:
        logger.error(f"Failed to get agent {agent_id}: {e}")
        return None


def get_agents_by_type(agent_type: str) -> List[Agent]:
    """
    Get all agents of specific type from database.
    
    Args:
        agent_type: Type of agents (e.g., 'classification', 'content_generation')
        
    Returns:
        List of Agent objects matching the type.
    """
    try:
        all_agents = get_all_agents()
        filtered = [agent for agent in all_agents if agent.type == agent_type]
        
        logger.info(f"Found {len(filtered)} agents of type '{agent_type}'")
        return filtered
        
    except Exception as e:
        logger.error(f"Failed to filter agents by type {agent_type}: {e}")
        return []


def get_agents_by_capability(capability: str) -> List[Agent]:
    """
    Get all agents with specific capability from database.
    
    Args:
        capability: Capability name
        
    Returns:
        List of Agent objects with the capability.
    """
    try:
        all_agents = get_all_agents()
        filtered = [
            agent for agent in all_agents 
            if capability in agent.capabilities
        ]
        
        logger.info(f"Found {len(filtered)} agents with capability '{capability}'")
        return filtered
        
    except Exception as e:
        logger.error(f"Failed to filter agents by capability {capability}: {e}")
        return []


def count_agents() -> int:
    """
    Count total number of agents in database.
    
    Returns:
        Number of agents.
    """
    try:
        agents = get_all_agents()
        return len(agents)
    except Exception:
        return 0
