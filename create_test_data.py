"""
Generate realistic test meeting transcripts for chatbot testing
"""
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.rag.chat_engine import MeetingChatEngine

def create_test_transcripts():
    """Generate realistic test meeting transcripts"""
    
    # Sample meetings for different departments
    test_meetings = [
        {
            'title': 'Engineering Sprint Planning - Nov 10',
            'content': '''
Sprint Planning Meeting
Date: November 10, 2025
Attendees: John (Engineering Manager), Sarah (Senior Dev), Mike (Backend Dev), Lisa (Frontend Dev)

John: Let's review our Q4 priorities. We need to focus on the database migration and API gateway.

Sarah: I can lead the API gateway project. I estimate it will take 3 weeks. Target completion: December 1st.

Mike: I'll handle the database migration. We need to migrate from MySQL to PostgreSQL. Deadline is November 30th.

Lisa: I'm working on the new dashboard UI. Should be done by November 25th. I'll need design review by November 20th.

John: Great. Action items:
- Sarah: Create API gateway technical spec by November 15
- Mike: Complete database migration plan by November 12
- Lisa: Submit dashboard mockups for review by November 18
- Team: Code review meeting scheduled for November 22

Budget approved: $75,000 for cloud infrastructure upgrades.
''',
            'timestamp': datetime.now() - timedelta(days=6),
            'source': 'google_drive',
            'department': 'engineering'
        },
        
        {
            'title': 'Sales Team Weekly Sync - Nov 12',
            'content': '''
Sales Weekly Meeting
Date: November 12, 2025
Attendees: Tom (Sales Director), Anna (Account Manager), Brad (Sales Rep)

Tom: Let's review this week's pipeline. We have 5 major deals closing this month.

Anna: Acme Corp deal is at $250,000. They want demo by November 20th. I'm the point of contact.

Brad: TechStart Inc is interested in enterprise package at $180,000. Proposal deadline: November 18th.

Tom: Great work team. Q4 revenue target is $2.5M. We're at 65% currently.

Action Items:
- Anna: Schedule Acme Corp demo for November 20, prepare custom pricing
- Brad: Send TechStart proposal by November 18
- Tom: Review pricing strategy with finance by November 15
- Team: Sales training on new product features scheduled November 22

Next meeting: November 19, 2025
''',
            'timestamp': datetime.now() - timedelta(days=4),
            'source': 'google_drive',
            'department': 'sales'
        },
        
        {
            'title': 'Marketing Campaign Review - Nov 13',
            'content': '''
Marketing Strategy Meeting
Date: November 13, 2025
Team: Emma (Marketing Director), Chris (Content Lead), Rachel (Social Media Manager)

Emma: Let's finalize our Q4 campaign strategy. Holiday campaign launches December 1st.

Chris: Blog content calendar is ready. We'll publish 3 posts per week. First post goes live November 20th.

Rachel: Social media ads are performing well. CTR is up 25%. Budget increase to $15,000 approved for December.

Emma: Excellent. We need to coordinate with sales team for lead generation.

Action Items:
- Chris: Finalize holiday campaign copy by November 25
- Rachel: Create social media content calendar for December by November 22
- Emma: Meet with sales director about lead qualification by November 16
- Team: Campaign launch meeting scheduled for November 28

Influencer partnership budget: $30,000 approved for Q1 2026.
''',
            'timestamp': datetime.now() - timedelta(days=3),
            'source': 'email',
            'department': 'marketing'
        },
        
        {
            'title': 'HR - Q4 Hiring Plan - Nov 11',
            'content': '''
HR Planning Session
Date: November 11, 2025
Participants: David (HR Director), Susan (Recruiter), Mark (Talent Manager)

David: We need to hire 8 new employees by end of Q4. Focus on engineering and sales.

Susan: Engineering roles:
- 2 Senior Engineers - Job posting live November 15
- 1 DevOps Engineer - Interviews start November 20
- 1 Product Manager - Offer to candidate by November 18

Mark: Sales roles:
- 3 Account Executives - First interviews November 22
- 1 Sales Operations Manager - Posting goes live November 14

David: Benefits package review completed. New health insurance starts January 1st.

Action Items:
- Susan: Schedule engineering interviews for November 20-25
- Mark: Finalize sales job descriptions by November 14
- David: Present benefits changes at all-hands on November 30
- Team: Diversity hiring training on November 21

Hiring budget: $500,000 approved for Q4-Q1.
''',
            'timestamp': datetime.now() - timedelta(days=5),
            'source': 'slack',
            'department': 'hr'
        },
        
        {
            'title': 'Finance - Budget Review - Nov 14',
            'content': '''
Q4 Budget Review
Date: November 14, 2025
Attendees: Robert (CFO), Linda (Controller), James (Financial Analyst)

Robert: Q4 financial review. Revenue is on track at $8.2M, expenses at $5.1M.

Linda: Major expenses this quarter:
- Engineering infrastructure: $75,000
- Marketing campaigns: $45,000  
- New hires: $120,000
- Office expansion: $200,000

James: Cash flow projection shows positive trend. We'll close the year at $3.5M profit.

Robert: Board presentation scheduled for December 5th. Need final numbers by December 1st.

Action Items:
- Linda: Prepare Q4 expense report by November 28
- James: Update revenue forecasts by November 20
- Robert: Review department budgets with heads by November 25
- Team: Audit preparation meeting November 29

Q1 2026 budget planning starts December 10th.
''',
            'timestamp': datetime.now() - timedelta(days=2),
            'source': 'google_drive',
            'department': 'finance'
        },
        
        {
            'title': '[CONFIDENTIAL] Executive Leadership Meeting - Nov 15',
            'content': '''
Executive Team Strategy Session
Date: November 15, 2025
Attendees: CEO, CFO, CTO, VP Sales, VP Marketing, VP HR

CEO: Q4 is critical. We need to hit $10M revenue target for the year.

CFO: Financially we're solid. Profit margins at 35%. Cash reserves strong.

CTO: Engineering team delivering well. API platform launches December 15th. This will be a game-changer.

VP Sales: Pipeline is healthy at $4M. Closing 3 major deals by month-end. Need more sales reps.

VP Marketing: Brand awareness up 40% this quarter. Holiday campaign will drive Q1 growth.

VP HR: Hiring 8 people by year-end. Employee satisfaction score is 4.2/5. Need to address remote work policy.

CEO: Action items:
- CFO: Board deck ready by December 1st
- CTO: API platform demo for leadership November 29th
- VP Sales: Close Acme and TechStart deals by November 30th
- VP Marketing: Launch holiday campaign December 1st
- VP HR: Present remote work policy options by November 27th

Next exec meeting: November 29, 2025
Company all-hands: November 30, 2025

[CONFIDENTIAL] Potential acquisition target identified. Legal review in progress.
''',
            'timestamp': datetime.now() - timedelta(days=1),
            'source': 'google_drive',
            'department': 'executive'
        },
        
        {
            'title': 'Product Team Standup - Nov 16',
            'content': '''
Daily Standup - Product Team
Date: November 16, 2025
Team: 8 members present

Alice (PM): Working on roadmap for Q1. Need feedback from engineering by November 22.

Bob (Designer): Dashboard redesign 80% complete. Final mockups ready November 20.

Carol (QA): Found 3 critical bugs in payment module. Need fix by November 18 for release.

Dan (Backend): API endpoints ready. Documentation being written. Done by November 19.

Emily (Frontend): Integration with new API in progress. ETA November 25.

Frank (DevOps): Production deployment scheduled for November 30. Need final testing by November 28.

Action Items:
- Carol: File bug reports in JIRA by end of day
- Dan: Complete API documentation by November 19  
- Alice: Share Q1 roadmap draft by November 22
- Team: Code freeze November 27 for release

Sprint demo: November 23
Release date: December 1
''',
            'timestamp': datetime.now(),
            'source': 'slack',
            'department': 'engineering'
        }
    ]
    
    return test_meetings

def index_test_data():
    """Index test transcripts into the system"""
    print("\n" + "="*60)
    print("🧪 Creating Test Meeting Transcripts")
    print("="*60 + "\n")
    
    # Initialize chat engine
    print("Initializing chat engine...")
    chat_engine = MeetingChatEngine()
    
    # Get test meetings
    meetings = create_test_transcripts()
    print(f"Generated {len(meetings)} test meetings\n")
    
    # Index each meeting
    indexed = 0
    skipped = 0
    for meeting in meetings:
        try:
            if chat_engine.index_transcript(meeting):
                indexed += 1
                print(f"✅ Indexed: {meeting['title']}")
            else:
                skipped += 1
                print(f"⏭️  Skipped: {meeting['title']} (already exists)")
        except Exception as e:
            print(f"❌ Error indexing {meeting['title']}: {e}")
    
    print("\n" + "="*60)
    print(f"📊 Summary")
    print("="*60)
    print(f"  Total meetings: {len(meetings)}")
    print(f"  Newly indexed: {indexed}")
    print(f"  Already existed: {skipped}")
    
    # Show stats
    stats = chat_engine.get_stats()
    print(f"\n📈 Database Stats:")
    print(f"  Unique meetings: {stats['unique_meetings']}")
    print(f"  Total chunks: {stats['total_chunks']}")
    
    print("\n" + "="*60)
    print("✅ Test Data Ready!")
    print("="*60)
    print("\n🚀 Next Steps:")
    print("  1. Open browser to: http://localhost:8502")
    print("  2. Login with: admin")
    print("\n💡 Try These Questions:")
    print('  • "What are all the action items from recent meetings?"')
    print('  • "Who is responsible for the API gateway?"')
    print('  • "What deadlines are coming up this week?"')
    print('  • "What is the Q4 revenue target?"')
    print('  • "Tell me about the database migration"')
    print('  • "What is the marketing budget for December?"')
    print("\n🔒 Test Guardrails (Login as different users):")
    print("  • eng_manager: Can see engineering, limited others")
    print("  • sales_member: Can see sales, blocked from engineering")
    print("  • admin: Can see everything including [CONFIDENTIAL]")
    print()

if __name__ == "__main__":
    try:
        index_test_data()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
