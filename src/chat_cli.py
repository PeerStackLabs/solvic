"""
Command-line interface for meeting transcript chatbot
"""
import argparse
import yaml
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.chat_engine import MeetingChatEngine
from transcript_sources.google_drive import GoogleDriveSource
from transcript_sources.email import EmailSource
from transcript_sources.slack import SlackSource

def index_transcripts(hours: int = 168):
    """Index transcripts from configured source"""
    print(f"\n🔄 Indexing transcripts from last {hours} hours...\n")
    
    # Load config
    with open('config.yml') as f:
        config = yaml.safe_load(f)
    
    # Initialize chat engine
    chat_engine = MeetingChatEngine()
    
    # Get transcript source
    source_type = config['transcript_source']['type']
    
    if source_type == 'google_drive':
        source = GoogleDriveSource(config['transcript_source'])
    elif source_type == 'email':
        source = EmailSource(config['transcript_source'])
    elif source_type == 'slack':
        source = SlackSource(config['transcript_source'])
    else:
        print(f"❌ Unsupported source: {source_type}")
        return
    
    # Fetch and index
    transcripts = source.fetch_transcripts(hours=hours)
    stats = chat_engine.index_multiple_transcripts(transcripts)
    
    print(f"\n✅ Indexing complete:")
    print(f"   Added: {stats['added']}")
    print(f"   Skipped: {stats['skipped']}")
    print(f"   Errors: {stats['errors']}\n")

def chat_loop():
    """Interactive chat loop"""
    chat_engine = MeetingChatEngine()
    
    print("\n" + "="*60)
    print("🤖 Meeting Assistant - Ask questions about your meetings")
    print("="*60)
    
    # Login
    print("\n🔐 Login")
    user_id = input("Enter your user ID: ").strip()
    
    user = chat_engine.user_manager.get_user(user_id)
    if not user:
        print(f"\n❌ User '{user_id}' not found\n")
        return
    
    print(f"\n✅ Logged in as: {user.name}")
    print(f"   Department: {user.department.value.title()}")
    print(f"   Access Level: {user.access_level.value.title()}\n")
    
    print("Commands: /stats, /history, /clear, /exit\n")
    
    while True:
        try:
            question = input("You: ").strip()
            
            if not question:
                continue
            
            # Handle commands
            if question == '/exit':
                print("\n👋 Goodbye!\n")
                break
            
            elif question == '/stats':
                stats = chat_engine.get_stats()
                print(f"\n📊 Statistics:")
                print(f"   Indexed meetings: {stats['unique_meetings']}")
                print(f"   Total chunks: {stats['total_chunks']}")
                print(f"   Questions asked: {stats['conversation_turns']}\n")
                continue
            
            elif question == '/history':
                history = chat_engine.get_conversation_history()
                print(f"\n📜 Conversation History:\n")
                for i, turn in enumerate(history, 1):
                    print(f"{i}. Q: {turn['question']}")
                    print(f"   A: {turn['answer'][:100]}...")
                    print()
                continue
            
            elif question == '/clear':
                chat_engine.clear_history()
                print("\n🗑️ History cleared\n")
                continue
            
            # Get answer
            print("\n🤔 Thinking...\n")
            response = chat_engine.ask(question, user_id)
            
            # Check if blocked
            if response.get('blocked'):
                print(f"⛔ {response['answer']}\n")
                continue
            
            # Display answer
            print(f"🤖 Assistant: {response['answer']}\n")
            
            # Display warnings
            for warning in response.get('warnings', []):
                print(f"   {warning}")
            
            # Display metadata
            print(f"   Confidence: {response['confidence']} | Sources: {len(response['sources'])} | Risk: {response['risk_score']:.2f}")
            
            # Display sources
            if response['sources']:
                print(f"\n   📄 Sources:")
                for source in response['sources']:
                    print(f"      - {source['title']} ({source['timestamp']})")
            
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")

def main():
    parser = argparse.ArgumentParser(description='Meeting Transcript Chatbot')
    parser.add_argument('--index', action='store_true', help='Index new transcripts')
    parser.add_argument('--hours', type=int, default=168, help='Hours to look back (default: 168)')
    parser.add_argument('--chat', action='store_true', help='Start chat interface')
    
    args = parser.parse_args()
    
    if args.index:
        index_transcripts(args.hours)
    elif args.chat:
        chat_loop()
    else:
        # Default: chat
        chat_loop()

if __name__ == "__main__":
    main()
