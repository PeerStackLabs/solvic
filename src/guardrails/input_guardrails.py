"""
Input guardrails for department-wise query filtering and validation
"""
from typing import Dict, List, Optional, Set
from enum import Enum
import re
from datetime import datetime

class Department(Enum):
    """Organization departments"""
    ENGINEERING = "engineering"
    SALES = "sales"
    MARKETING = "marketing"
    HR = "hr"
    FINANCE = "finance"
    LEGAL = "legal"
    OPERATIONS = "operations"
    EXECUTIVE = "executive"
    ALL = "all"  # Admin access

class AccessLevel(Enum):
    """Access levels for users"""
    VIEWER = "viewer"  # Read-only
    MEMBER = "member"  # Department member
    MANAGER = "manager"  # Department manager
    ADMIN = "admin"  # Full access

class SensitivityLevel(Enum):
    """Data sensitivity classification"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

class InputGuardrails:
    """Validate and filter user queries based on department access"""
    
    def __init__(self):
        # Blocked keywords by department
        self.restricted_keywords = {
            Department.ENGINEERING: {
                'blocked': ['salary', 'compensation', 'termination', 'lawsuit'],
                'warning': ['budget', 'layoff', 'acquisition']
            },
            Department.SALES: {
                'blocked': ['engineering roadmap', 'technical debt', 'hr policy'],
                'warning': ['pricing strategy', 'margin']
            },
            Department.MARKETING: {
                'blocked': ['revenue', 'contract terms', 'legal'],
                'warning': ['competitor analysis']
            },
            Department.HR: {
                'blocked': ['technical architecture', 'sales pipeline'],
                'warning': ['performance review', 'disciplinary']
            },
            Department.FINANCE: {
                'blocked': ['product roadmap', 'customer complaints'],
                'warning': []
            }
        }
        
        # PII patterns to detect
        self.pii_patterns = {
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
        }
    
    def validate_query(
        self, 
        query: str, 
        user_department: Department,
        user_access_level: AccessLevel
    ) -> Dict:
        """
        Validate user query against guardrails
        
        Returns:
            Dict with 'allowed', 'reason', 'sanitized_query', 'warnings'
        """
        result = {
            'allowed': True,
            'reason': None,
            'sanitized_query': query,
            'warnings': [],
            'risk_score': 0.0  # Will be converted to percentage in chat_engine
        }
        
        # Check for blocked keywords
        blocked_check = self._check_blocked_keywords(query, user_department)
        if not blocked_check['allowed']:
            result['allowed'] = False
            result['reason'] = blocked_check['reason']
            result['risk_score'] = 1.0
            return result
        
        result['warnings'].extend(blocked_check.get('warnings', []))
        
        # Check for PII exposure
        pii_check = self._check_pii(query)
        if pii_check['found']:
            result['warnings'].append(f"⚠️ PII detected: {', '.join(pii_check['types'])}")
            result['sanitized_query'] = pii_check['sanitized']
            result['risk_score'] += 0.3
        
        # Check for cross-department queries
        cross_dept_check = self._check_cross_department(query, user_department)
        if cross_dept_check['is_cross_department']:
            if user_access_level == AccessLevel.VIEWER:
                result['allowed'] = False
                result['reason'] = "Cross-department queries require member-level access"
                return result
            result['warnings'].append("🔄 Cross-department query detected")
            result['risk_score'] += 0.2
        
        # Check query complexity (potential data mining)
        if self._is_complex_query(query):
            result['warnings'].append("📊 Complex aggregation query detected")
            result['risk_score'] += 0.1
        
        # Final risk assessment
        if result['risk_score'] > 0.7:
            result['warnings'].append("⚠️ High-risk query - will be logged and monitored")
        
        return result
    
    def _check_blocked_keywords(self, query: str, department: Department) -> Dict:
        """Check for department-specific blocked keywords"""
        query_lower = query.lower()
        
        if department not in self.restricted_keywords:
            return {'allowed': True, 'warnings': []}
        
        restrictions = self.restricted_keywords[department]
        
        # Check blocked keywords
        for keyword in restrictions.get('blocked', []):
            if keyword in query_lower:
                return {
                    'allowed': False,
                    'reason': f"Query contains restricted keyword '{keyword}' for {department.value} department"
                }
        
        # Check warning keywords
        warnings = []
        for keyword in restrictions.get('warning', []):
            if keyword in query_lower:
                warnings.append(f"⚠️ Sensitive keyword detected: '{keyword}'")
        
        return {'allowed': True, 'warnings': warnings}
    
    def _check_pii(self, query: str) -> Dict:
        """Detect and sanitize PII in queries"""
        found_pii = []
        sanitized = query
        
        for pii_type, pattern in self.pii_patterns.items():
            if re.search(pattern, query):
                found_pii.append(pii_type)
                sanitized = re.sub(pattern, f'[{pii_type.upper()}_REDACTED]', sanitized)
        
        return {
            'found': len(found_pii) > 0,
            'types': found_pii,
            'sanitized': sanitized
        }
    
    def _check_cross_department(self, query: str, user_department: Department) -> Dict:
        """Detect cross-department queries"""
        department_keywords = {
            Department.ENGINEERING: ['engineering', 'dev', 'technical', 'code', 'architecture'],
            Department.SALES: ['sales', 'revenue', 'deals', 'quota', 'pipeline'],
            Department.MARKETING: ['marketing', 'campaign', 'brand', 'content'],
            Department.HR: ['hr', 'hiring', 'employee', 'recruitment', 'benefits'],
            Department.FINANCE: ['finance', 'budget', 'accounting', 'forecast'],
            Department.LEGAL: ['legal', 'contract', 'compliance', 'regulation']
        }
        
        query_lower = query.lower()
        mentioned_departments = set()
        
        for dept, keywords in department_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                mentioned_departments.add(dept)
        
        is_cross = len(mentioned_departments) > 1 or (
            len(mentioned_departments) == 1 and 
            user_department not in mentioned_departments
        )
        
        return {
            'is_cross_department': is_cross,
            'departments': list(mentioned_departments)
        }
    
    def _is_complex_query(self, query: str) -> bool:
        """Detect complex aggregation queries (potential data mining)"""
        complex_indicators = [
            'all meetings',
            'every',
            'total',
            'summarize everything',
            'list all',
            'show me all',
            'aggregate',
            'count'
        ]
        
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in complex_indicators)
