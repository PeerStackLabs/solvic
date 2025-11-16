"""
Quick setup script for Meeting Chatbot
"""
import sys
from pathlib import Path

def setup():
    """Initialize the chatbot system"""
    
    print("\n" + "="*60)
    print("🤖 Meeting Chatbot Setup")
    print("="*60 + "\n")
    
    # Check if config exists
    config_file = Path("config.yml")
    if not config_file.exists():
        print("⚠️  config.yml not found")
        print("   Run: copy config.example.yml config.yml")
        print("   Then edit config.yml with your API keys\n")
        return False
    
    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    print("✅ Created data directory")
    
    # Initialize users
    print("✅ Initializing default users...")
    from src.guardrails.user_manager import UserManager
    user_manager = UserManager()
    
    print(f"   Created {len(user_manager.users)} default users:")
    for user in user_manager.users.values():
        print(f"   - {user.user_id:15} ({user.department.value:12}, {user.access_level.value})")
    
    print("\n" + "="*60)
    print("✅ Setup Complete!")
    print("="*60)
    
    print("\n📋 Next Steps:\n")
    print("1. Configure your API keys in config.yml")
    print("2. Index your transcripts:")
    print("   python src/chat_cli.py --index --hours 168")
    print("\n3. Start the chatbot:")
    print("   Option A: streamlit run src/web/chatbot_app.py")
    print("   Option B: python src/chat_cli.py --chat")
    
    print("\n4. Login with test users:")
    print("   - admin (full access)")
    print("   - eng_manager (engineering manager)")
    print("   - sales_member (sales member)")
    print("   - hr_manager (HR manager)")
    
    print("\n📖 Read CHATBOT_README.md for detailed documentation")
    print()
    
    return True

if __name__ == "__main__":
    try:
        setup()
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        print("   Please check error above and try again\n")
        sys.exit(1)
