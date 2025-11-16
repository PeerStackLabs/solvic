"""
Output guardrails for filtering and sanitizing AI responses
"""
from typing import Dict, List, Set, Optional
import re
from .input_guardrails import Department, AccessLevel, SensitivityLevel

class OutputGuardrails:
    """Filter and sanitize AI responses based on department access"""
    
    def __init__(self):
        # Sensitive information patterns
        self.sensitive_patterns = {
            'salary': r'\$\d+[,\d]*(?:\.\d{2})?(?:\s*(?:k|K|thousand|million|M))?',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'employee_id': r'\bEMP\d{4,}\b',
            'confidential_marker': r'\[CONFIDENTIAL\]|\[RESTRICTED\]|\[INTERNAL ONLY\]'
        }
        
        # Department-specific redaction rules
        self.redaction_rules = {
            Department.ENGINEERING: {
                SensitivityLevel.CONFIDENTIAL: ['salary', 'employee_id'],
                SensitivityLevel.RESTRICTED: ['salary', 'employee_id', 'confidential_marker']
            },
            Department.SALES: {
                SensitivityLevel.CONFIDENTIAL: ['salary', 'employee_id'],
                SensitivityLevel.RESTRICTED: ['salary', 'employee_id', 'confidential_marker']
            },
            Department.MARKETING: {
                SensitivityLevel.CONFIDENTIAL: ['salary', 'employee_id'],
                SensitivityLevel.RESTRICTED: ['salary', 'employee_id', 'confidential_marker']
            },
            Department.HR: {
                SensitivityLevel.CONFIDENTIAL: ['employee_id'],
                SensitivityLevel.RESTRICTED: ['confidential_marker']
            },
            Department.FINANCE: {
                SensitivityLevel.CONFIDENTIAL: ['employee_id'],
                SensitivityLevel.RESTRICTED: []
            }
        }
    
    def filter_response(
        self,
        response: str,
        sources: List[Dict],
        user_department: Department,
        user_access_level: AccessLevel
    ) -> Dict:
        """
        Filter and sanitize AI response based on department access
        
        Returns:
            Dict with 'filtered_response', 'filtered_sources', 'redactions', 'warnings'
        """
        result = {
            'filtered_response': response,
            'filtered_sources': sources.copy(),
            'redactions': [],
            'warnings': [],
            'blocked_content': False
        }
        
        # Filter sources by department access
        filtered_sources = self._filter_sources(sources, user_department, user_access_level)
        result['filtered_sources'] = filtered_sources
        
        if len(filtered_sources) < len(sources):
            removed = len(sources) - len(filtered_sources)
            result['warnings'].append(
                f"🔒 {removed} source(s) removed due to access restrictions"
            )
        
        # Determine content sensitivity
        sensitivity = self._classify_sensitivity(response, sources)
        
        # Check if user can access this sensitivity level
        if not self._can_access_sensitivity(user_access_level, sensitivity):
            result['blocked_content'] = True
            result['filtered_response'] = (
                "⛔ This content is classified as RESTRICTED and requires "
                f"{AccessLevel.MANAGER.value} or higher access level."
            )
            return result
        
        # Redact sensitive information
        redacted = self._redact_sensitive_info(
            response, 
            user_department, 
            sensitivity
        )
        result['filtered_response'] = redacted['content']
        result['redactions'] = redacted['redactions']
        
        # Check for information leakage
        leakage_check = self._check_information_leakage(
            result['filtered_response'],
            user_department
        )
        
        if leakage_check['has_leakage']:
            result['warnings'].extend(leakage_check['warnings'])
            result['filtered_response'] = leakage_check['sanitized']
        
        # Add content warnings
        if sensitivity != SensitivityLevel.PUBLIC:
            result['warnings'].append(
                f"🔐 Content classification: {sensitivity.value.upper()}"
            )
        
        return result
    
    def _filter_sources(
        self,
        sources: List[Dict],
        user_department: Department,
        user_access_level: AccessLevel
    ) -> List[Dict]:
        """Filter sources based on department access"""
        filtered = []
        
        for source in sources:
            # Extract department from source metadata
            source_dept = self._extract_department(source)
            source_sensitivity = self._get_source_sensitivity(source)
            
            # Check access
            if self._can_access_source(
                user_department,
                user_access_level,
                source_dept,
                source_sensitivity
            ):
                filtered.append(source)
        
        return filtered
    
    def _extract_department(self, source: Dict) -> Optional[Department]:
        """Extract department from source metadata"""
        title = source.get('title', '').lower()
        
        # Simple keyword matching
        if any(kw in title for kw in ['engineering', 'dev', 'tech']):
            return Department.ENGINEERING
        elif any(kw in title for kw in ['sales', 'revenue']):
            return Department.SALES
        elif any(kw in title for kw in ['marketing', 'brand']):
            return Department.MARKETING
        elif any(kw in title for kw in ['hr', 'people', 'hiring']):
            return Department.HR
        elif any(kw in title for kw in ['finance', 'budget']):
            return Department.FINANCE
        elif any(kw in title for kw in ['legal', 'compliance']):
            return Department.LEGAL
        
        return None  # Unknown department - allow by default
    
    def _get_source_sensitivity(self, source: Dict) -> SensitivityLevel:
        """Determine sensitivity level of source"""
        title = source.get('title', '').lower()
        
        # Check for explicit markers
        if '[restricted]' in title or '[confidential]' in title:
            return SensitivityLevel.RESTRICTED
        elif '[internal]' in title:
            return SensitivityLevel.CONFIDENTIAL
        
        # Check for sensitive keywords
        sensitive_keywords = ['confidential', 'restricted', 'private', 'executive']
        if any(kw in title for kw in sensitive_keywords):
            return SensitivityLevel.CONFIDENTIAL
        
        return SensitivityLevel.INTERNAL
    
    def _can_access_source(
        self,
        user_dept: Department,
        user_level: AccessLevel,
        source_dept: Optional[Department],
        source_sensitivity: SensitivityLevel
    ) -> bool:
        """Check if user can access a source"""
        # Admins can access everything
        if user_level == AccessLevel.ADMIN:
            return True
        
        # If source department is unknown, allow
        if source_dept is None:
            return True
        
        # Same department access
        if user_dept == source_dept:
            return True
        
        # Managers can access other departments (except restricted)
        if user_level == AccessLevel.MANAGER:
            return source_sensitivity != SensitivityLevel.RESTRICTED
        
        # Members can only access public/internal cross-department
        if user_level == AccessLevel.MEMBER:
            return source_sensitivity in [SensitivityLevel.PUBLIC, SensitivityLevel.INTERNAL]
        
        # Viewers limited to public
        return source_sensitivity == SensitivityLevel.PUBLIC
    
    def _classify_sensitivity(self, response: str, sources: List[Dict]) -> SensitivityLevel:
        """Classify overall sensitivity of response"""
        # Check for explicit markers
        response_lower = response.lower()
        
        if any(marker in response_lower for marker in ['[restricted]', '[confidential]']):
            return SensitivityLevel.RESTRICTED
        
        # Check source sensitivity
        max_source_sensitivity = SensitivityLevel.PUBLIC
        for source in sources:
            source_sens = self._get_source_sensitivity(source)
            if source_sens.value > max_source_sensitivity.value:
                max_source_sensitivity = source_sens
        
        return max_source_sensitivity
    
    def _can_access_sensitivity(
        self,
        user_level: AccessLevel,
        sensitivity: SensitivityLevel
    ) -> bool:
        """Check if user access level can view content sensitivity"""
        access_matrix = {
            AccessLevel.ADMIN: [SensitivityLevel.PUBLIC, SensitivityLevel.INTERNAL, 
                               SensitivityLevel.CONFIDENTIAL, SensitivityLevel.RESTRICTED],
            AccessLevel.MANAGER: [SensitivityLevel.PUBLIC, SensitivityLevel.INTERNAL, 
                                 SensitivityLevel.CONFIDENTIAL],
            AccessLevel.MEMBER: [SensitivityLevel.PUBLIC, SensitivityLevel.INTERNAL],
            AccessLevel.VIEWER: [SensitivityLevel.PUBLIC]
        }
        
        return sensitivity in access_matrix.get(user_level, [])
    
    def _redact_sensitive_info(
        self,
        content: str,
        user_department: Department,
        sensitivity: SensitivityLevel
    ) -> Dict:
        """Redact sensitive information based on department and sensitivity"""
        redactions = []
        redacted_content = content
        
        # Get redaction rules for department/sensitivity
        rules = self.redaction_rules.get(user_department, {})
        patterns_to_redact = rules.get(sensitivity, [])
        
        # Apply redactions
        for pattern_name in patterns_to_redact:
            if pattern_name in self.sensitive_patterns:
                pattern = self.sensitive_patterns[pattern_name]
                matches = re.findall(pattern, redacted_content)
                
                if matches:
                    redactions.append({
                        'type': pattern_name,
                        'count': len(matches)
                    })
                    redacted_content = re.sub(
                        pattern,
                        f'[{pattern_name.upper()}_REDACTED]',
                        redacted_content
                    )
        
        return {
            'content': redacted_content,
            'redactions': redactions
        }
    
    def _check_information_leakage(self, content: str, user_department: Department) -> Dict:
        """Check for potential information leakage"""
        warnings = []
        sanitized = content
        has_leakage = False
        
        # Check for cross-department sensitive info
        leakage_patterns = {
            'financial_data': r'\$\d+[,\d]*(?:\.\d{2})?\s*(?:revenue|profit|loss|budget)',
            'personnel_data': r'(?:fired|terminated|laid off|dismissed)\s+\w+',
            'legal_data': r'(?:lawsuit|litigation|settlement|NDA)',
        }
        
        for leak_type, pattern in leakage_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                # Check if user department should see this
                if not self._is_authorized_for_leak_type(user_department, leak_type):
                    has_leakage = True
                    warnings.append(f"⚠️ {leak_type.replace('_', ' ').title()} detected and redacted")
                    sanitized = re.sub(
                        pattern,
                        '[REDACTED]',
                        sanitized,
                        flags=re.IGNORECASE
                    )
        
        return {
            'has_leakage': has_leakage,
            'warnings': warnings,
            'sanitized': sanitized
        }
    
    def _is_authorized_for_leak_type(self, department: Department, leak_type: str) -> bool:
        """Check if department is authorized to see specific leak types"""
        authorization = {
            'financial_data': [Department.FINANCE, Department.EXECUTIVE],
            'personnel_data': [Department.HR, Department.EXECUTIVE],
            'legal_data': [Department.LEGAL, Department.EXECUTIVE]
        }
        
        return department in authorization.get(leak_type, [])
