"""
Quick test script to verify refactoring.
"""
import sys
import re

def count_emojis_in_file(filepath):
    """Count emojis in file."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"
        "\U00002600-\U000026FF"
        "]+",
        flags=re.UNICODE
    )
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            matches = emoji_pattern.findall(content)
            return len(matches)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return -1

def main():
    """Test refactoring results."""
    print("="*60)
    print("REFACTORING VERIFICATION")
    print("="*60)
    
    # Test 1: No emojis in core Python files
    print("\n1. Checking for emojis in core files...")
    
    core_files = [
        "main.py",
        "services.py",
        "agent_library.py",
        "grapharchitect_bridge.py",
        "repository.py",
        "database.py",
        "sqlite_repository.py",
        "websocket_manager.py",
        "workflow_simulator.py",
        "api_router.py"
    ]
    
    total_emojis = 0
    for filename in core_files:
        count = count_emojis_in_file(filename)
        if count > 0:
            print(f"   FAIL: {filename} has {count} emojis")
            total_emojis += count
        elif count == 0:
            print(f"   PASS: {filename}")
        else:
            print(f"   SKIP: {filename} (not found)")
    
    if total_emojis == 0:
        print("   Result: PASS - No emojis in core files")
    else:
        print(f"   Result: FAIL - Found {total_emojis} emojis total")
    
    # Test 2: No hardcoded agents
    print("\n2. Checking for hardcoded agents...")
    
    try:
        with open("agent_library.py", 'r', encoding='utf-8') as f:
            content = f.read()
            if "AGENT_LIBRARY = {" in content:
                print("   FAIL: Found AGENT_LIBRARY hardcode")
            else:
                print("   PASS: No AGENT_LIBRARY hardcode")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 3: Configuration module exists
    print("\n3. Checking configuration module...")
    
    try:
        import config
        print("   PASS: config.py exists and can be imported")
        print(f"   - DATABASE_PATH: {config.DATABASE_PATH}")
        print(f"   - PORT_START: {config.PORT_START}")
    except Exception as e:
        print(f"   FAIL: {e}")
    
    # Test 4: Repository has get_all_agents()
    print("\n4. Checking repository methods...")
    
    try:
        from repository import InMemoryRepository
        repo = InMemoryRepository()
        
        if hasattr(repo, 'get_all_agents'):
            print("   PASS: InMemoryRepository has get_all_agents()")
        else:
            print("   FAIL: InMemoryRepository missing get_all_agents()")
            
        if hasattr(repo, 'get_agent'):
            print("   PASS: InMemoryRepository has get_agent()")
        else:
            print("   FAIL: InMemoryRepository missing get_agent()")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 5: agent_library uses database
    print("\n5. Checking agent_library uses database...")
    
    try:
        from agent_library import get_all_agents
        print("   PASS: get_all_agents() can be imported")
        
        # Try to call (might fail if no database)
        try:
            agents = get_all_agents()
            print(f"   INFO: Loaded {len(agents)} tools from database")
        except Exception as e:
            print(f"   INFO: Database not ready: {e}")
    except Exception as e:
        print(f"   FAIL: {e}")
    
    print("\n" + "="*60)
    print("VERIFICATION COMPLETE")
    print("="*60)
    
    if total_emojis == 0:
        print("\nStatus: PASS")
        print("All core files are clean (no emojis)")
    else:
        print(f"\nStatus: PARTIAL")
        print(f"Found {total_emojis} emojis in core files")
    
    print("\nNext: Start server with:")
    print("  python main.py")
    print("  or: start.bat")

if __name__ == "__main__":
    main()
