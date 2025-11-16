"""
User management and authentication for department-wise access control
"""
from typing import Dict, Optional, List
import json
from pathlib import Path
from datetime import datetime
from .input_guardrails import Department, AccessLevel

class User:
    """User model with department and access level"""
    
    def __init__(
        self,
        user_id: str,
        name: str,
        email: str,
        department: Department,
        access_level: AccessLevel,
        additional_departments: Optional[List[Department]] = None
    ):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.department = department
        self.access_level = access_level
        self.additional_departments = additional_departments or []
        self.created_at = datetime.now()
        self.query_count = 0
        self.last_query = None
    
    def to_dict(self) -> Dict:
        """Convert user to dictionary"""
        return {
            'user_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'department': self.department.value,
            'access_level': self.access_level.value,
            'additional_departments': [d.value for d in self.additional_departments],
            'created_at': self.created_at.isoformat(),
            'query_count': self.query_count,
            'last_query': self.last_query.isoformat() if self.last_query else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        """Create user from dictionary"""
        user = cls(
            user_id=data['user_id'],
            name=data['name'],
            email=data['email'],
            department=Department(data['department']),
            access_level=AccessLevel(data['access_level']),
            additional_departments=[Department(d) for d in data.get('additional_departments', [])]
        )
        user.query_count = data.get('query_count', 0)
        if data.get('last_query'):
            user.last_query = datetime.fromisoformat(data['last_query'])
        return user

class UserManager:
    """Manage users and their permissions"""
    
    def __init__(self, users_file: str = "./data/users.json"):
        self.users_file = Path(users_file)
        self.users: Dict[str, User] = {}
        self._load_users()
    
    def _load_users(self):
        """Load users from file"""
        if self.users_file.exists():
            with open(self.users_file, 'r') as f:
                data = json.load(f)
                for user_data in data.get('users', []):
                    user = User.from_dict(user_data)
                    self.users[user.user_id] = user
        else:
            # Create default admin user
            self._create_default_users()
    
    def _save_users(self):
        """Save users to file"""
        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.users_file, 'w') as f:
            json.dump({
                'users': [user.to_dict() for user in self.users.values()]
            }, f, indent=2)
    
    def _create_default_users(self):
        """Create default users for testing"""
        default_users = [
            User(
                user_id="admin",
                name="Admin User",
                email="admin@company.com",
                department=Department.EXECUTIVE,
                access_level=AccessLevel.ADMIN
            ),
            User(
                user_id="eng_manager",
                name="Engineering Manager",
                email="eng.manager@company.com",
                department=Department.ENGINEERING,
                access_level=AccessLevel.MANAGER
            ),
            User(
                user_id="sales_member",
                name="Sales Member",
                email="sales@company.com",
                department=Department.SALES,
                access_level=AccessLevel.MEMBER
            ),
            User(
                user_id="hr_manager",
                name="HR Manager",
                email="hr@company.com",
                department=Department.HR,
                access_level=AccessLevel.MANAGER
            )
        ]
        
        for user in default_users:
            self.users[user.user_id] = user
        
        self._save_users()
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    def create_user(
        self,
        user_id: str,
        name: str,
        email: str,
        department: Department,
        access_level: AccessLevel,
        additional_departments: Optional[List[Department]] = None
    ) -> User:
        """Create a new user"""
        user = User(user_id, name, email, department, access_level, additional_departments)
        self.users[user_id] = user
        self._save_users()
        return user
    
    def update_user(
        self,
        user_id: str,
        **kwargs
    ) -> Optional[User]:
        """Update user attributes"""
        user = self.users.get(user_id)
        if not user:
            return None
        
        if 'department' in kwargs:
            user.department = Department(kwargs['department'])
        if 'access_level' in kwargs:
            user.access_level = AccessLevel(kwargs['access_level'])
        if 'additional_departments' in kwargs:
            user.additional_departments = [Department(d) for d in kwargs['additional_departments']]
        
        self._save_users()
        return user
    
    def record_query(self, user_id: str):
        """Record that user made a query"""
        user = self.users.get(user_id)
        if user:
            user.query_count += 1
            user.last_query = datetime.now()
            self._save_users()
    
    def get_department_users(self, department: Department) -> List[User]:
        """Get all users in a department"""
        return [
            user for user in self.users.values()
            if user.department == department or department in user.additional_departments
        ]
    
    def get_stats(self) -> Dict:
        """Get user statistics"""
        return {
            'total_users': len(self.users),
            'by_department': {
                dept.value: len(self.get_department_users(dept))
                for dept in Department
            },
            'by_access_level': {
                level.value: len([u for u in self.users.values() if u.access_level == level])
                for level in AccessLevel
            },
            'total_queries': sum(u.query_count for u in self.users.values())
        }
