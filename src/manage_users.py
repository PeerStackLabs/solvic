"""
CLI tool for managing users
"""
import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from guardrails.user_manager import UserManager, Department, AccessLevel

def main():
    parser = argparse.ArgumentParser(description='User Management CLI')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List users
    subparsers.add_parser('list', help='List all users')
    
    # Add user
    add_parser = subparsers.add_parser('add', help='Add a new user')
    add_parser.add_argument('--id', required=True, help='User ID')
    add_parser.add_argument('--name', required=True, help='Full name')
    add_parser.add_argument('--email', required=True, help='Email address')
    add_parser.add_argument('--department', required=True, 
                          choices=[d.value for d in Department],
                          help='Department')
    add_parser.add_argument('--level', required=True,
                          choices=[l.value for l in AccessLevel],
                          help='Access level')
    
    # Update user
    update_parser = subparsers.add_parser('update', help='Update user')
    update_parser.add_argument('--id', required=True, help='User ID')
    update_parser.add_argument('--department', choices=[d.value for d in Department])
    update_parser.add_argument('--level', choices=[l.value for l in AccessLevel])
    
    # Stats
    subparsers.add_parser('stats', help='Show statistics')
    
    args = parser.parse_args()
    
    manager = UserManager()
    
    if args.command == 'list':
        print("\n📋 Users:\n")
        for user in manager.users.values():
            print(f"  {user.user_id:15} | {user.name:20} | {user.department.value:12} | {user.access_level.value:8} | Queries: {user.query_count}")
        print()
    
    elif args.command == 'add':
        user = manager.create_user(
            args.id,
            args.name,
            args.email,
            Department(args.department),
            AccessLevel(args.level)
        )
        print(f"\n✅ Created user: {user.name} ({user.user_id})\n")
    
    elif args.command == 'update':
        kwargs = {}
        if args.department:
            kwargs['department'] = args.department
        if args.level:
            kwargs['level'] = args.level
        
        user = manager.update_user(args.id, **kwargs)
        if user:
            print(f"\n✅ Updated user: {user.name}\n")
        else:
            print(f"\n❌ User not found: {args.id}\n")
    
    elif args.command == 'stats':
        stats = manager.get_stats()
        print("\n📊 Statistics:\n")
        print(f"  Total Users: {stats['total_users']}")
        print(f"  Total Queries: {stats['total_queries']}")
        print(f"\n  By Department:")
        for dept, count in stats['by_department'].items():
            print(f"    {dept:15} : {count}")
        print(f"\n  By Access Level:")
        for level, count in stats['by_access_level'].items():
            print(f"    {level:10} : {count}")
        print()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
