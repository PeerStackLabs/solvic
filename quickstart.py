"""
Quick Start Script
Run this to test the system after setup
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp.ingest import TranscriptIngestor
from mcp.rag import RAGSystem
from mcp.llm import LMStudioClient


def main():
    print("=" * 60)
    print("ContextIQ Quick Start Test")
    print("=" * 60)
    
    # Test 1: Ingestor
    print("\n1. Testing Transcript Ingestor...")
    try:
        ingestor = TranscriptIngestor()
        new_transcripts = ingestor.get_new_transcripts()
        print(f"   ✓ Found {len(new_transcripts)} new transcript(s)")
        
        if new_transcripts:
            docs = ingestor.ingest_all_new_transcripts()
            print(f"   ✓ Created {len(docs)} chunks")
        else:
            print("   ℹ No new transcripts to process")
            print(f"   ℹ Place .txt files in: {ingestor.transcripts_dir}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    # Test 2: RAG System
    print("\n2. Testing RAG System (ChromaDB)...")
    try:
        rag = RAGSystem()
        stats = rag.get_collection_stats()
        print(f"   ✓ ChromaDB initialized")
        print(f"   ✓ Total documents: {stats['total_documents']}")
        
        # Add documents if we have any
        if new_transcripts:
            docs = ingestor.ingest_all_new_transcripts()
            added = rag.add_documents(docs)
            print(f"   ✓ Added {added} new documents to RAG")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    # Test 3: LM Studio Connection
    print("\n3. Testing LM Studio Connection...")
    try:
        llm = LMStudioClient()
        
        # Try to get models
        models = llm.get_available_models()
        if models:
            print(f"   ✓ LM Studio connected")
            print(f"   ✓ Available models: {', '.join(models)}")
        else:
            print("   ⚠ Connected but no models listed")
        
        # Test generation
        print("   Testing response generation...")
        response = llm.generate_response(
            "Say 'OK' if you can read this.",
            max_tokens=50
        )
        print(f"   ✓ Response: {response[:100]}")
        
    except Exception as e:
        print(f"   ✗ LM Studio connection failed: {e}")
        print("   ℹ Make sure LM Studio is running on http://localhost:1234")
    
    # Test 4: End-to-End Query (if we have data)
    if stats['total_documents'] > 0:
        print("\n4. Testing End-to-End Query...")
        try:
            # Search RAG
            results = rag.query("What is discussed in the transcripts?", n_results=3)
            
            if results["documents"]:
                print(f"   ✓ Found {len(results['documents'])} relevant chunks")
                
                # Build context
                context = rag.build_context_from_results(results, max_chunks=3)
                
                # Generate answer
                answer = llm.answer_with_context(
                    question="What is discussed in the transcripts?",
                    context=context
                )
                
                print(f"   ✓ Generated answer ({len(answer)} chars)")
                print("\n   Answer Preview:")
                print("   " + "-" * 50)
                print("   " + answer[:200] + "...")
                print("   " + "-" * 50)
            else:
                print("   ℹ No documents to query yet")
        except Exception as e:
            print(f"   ✗ Error: {e}")
    else:
        print("\n4. Skipping end-to-end test (no documents in database)")
        print("   ℹ Add .txt files to data/transcripts/ and run again")
    
    # Summary
    print("\n" + "=" * 60)
    print("Quick Start Test Complete!")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. Add transcript .txt files to: data/transcripts/")
    print("2. Start the server: python -m mcp.server")
    print("3. Visit: http://localhost:8000/docs")
    print("4. Test with: curl -X POST http://localhost:8000/ask \\")
    print('              -H "Content-Type: application/json" \\')
    print('              -d \'{"question": "Your question here"}\'')
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
