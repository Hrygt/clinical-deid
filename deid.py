# deid.py

from faker import Faker
from datetime import datetime, timedelta
import random
import re

class ClinicalDeidentifier:
    def __init__(self, seed=None):
        self.fake = Faker()
        if seed:
            Faker.seed(seed)
            random.seed(seed)
        
        # Cache for within-document consistency
        self._cache = {}
        self._date_shift = None
    
    def reset_cache(self):
        """Call between documents."""
        self._cache = {}
        self._date_shift = random.randint(-365, -1)
    
    def _get_cached(self, original, entity_type, generator_fn):
        """Consistent replacement within a document."""
        key = f"{entity_type}:{original}"
        if key not in self._cache:
            self._cache[key] = generator_fn()
        return self._cache[key]
    
    def replace(self, text, entity_type):
        """Replace detected PHI with fake data."""
        
        if entity_type == "FIRST_NAME":
            return self._get_cached(text, entity_type, self.fake.first_name)
        
        elif entity_type == "LAST_NAME":
            return self._get_cached(text, entity_type, self.fake.last_name)
        
        elif entity_type == "DATE":
            return self._shift_date(text)
        
        elif entity_type == "DATE_OF_BIRTH":
            return self._shift_date(text)
        
        elif entity_type == "DATE_TIME":
            return self._shift_date(text, include_time=True)
        
        elif entity_type == "TIME":
            return text  # Keep time, per HIPAA Safe Harbor
        
        elif entity_type == "AGE":
            return self._generalize_age(text)
        
        elif entity_type == "SSN":
            return "[SSN]"
        
        elif entity_type == "MEDICAL_RECORD_NUMBER":
            return self._get_cached(text, entity_type, 
                lambda: f"MRN-{self.fake.random_number(digits=8)}")
        
        elif entity_type == "PHONE_NUMBER":
            return "[PHONE]"
        
        elif entity_type == "FAX_NUMBER":
            return "[FAX]"
        
        elif entity_type == "EMAIL":
            return self._get_cached(text, entity_type, self.fake.email)
        
        elif entity_type == "STREET_ADDRESS":
            return "[ADDRESS]"
        
        elif entity_type == "CITY":
            return "[CITY]"
        
        elif entity_type == "COUNTY":
            return "[COUNTY]"
        
        elif entity_type == "STATE":
            return text  # State is allowed per HIPAA
        
        elif entity_type == "POSTCODE":
            return self._generalize_zip(text)
        
        elif entity_type == "COUNTRY":
            return text  # Country is allowed
        
        elif entity_type in ["ACCOUNT_NUMBER", "CUSTOMER_ID", "EMPLOYEE_ID", 
                            "UNIQUE_ID", "BIOMETRIC_IDENTIFIER", 
                            "CERTIFICATE_LICENSE_NUMBER", 
                            "HEALTH_PLAN_BENEFICIARY_NUMBER"]:
            return f"[{entity_type}]"
        
        else:
            return "[REDACTED]"
    
    def _shift_date(self, text, include_time=False):
        """Shift date by consistent random offset."""
        if self._date_shift is None:
            self._date_shift = random.randint(-365, -1)
        
        # Try common date formats
        formats = [
            "%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", 
            "%B %d, %Y", "%b %d, %Y", "%d %B %Y"
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(text.strip(), fmt)
                shifted = dt + timedelta(days=self._date_shift)
                return shifted.strftime(fmt)
            except ValueError:
                continue
        
        # Couldn't parse - return generic
        return "[DATE]"
    
    def _generalize_age(self, text):
        """HIPAA requires 89+ to be generalized."""
        try:
            age = int(re.search(r'\d+', text).group())
            if age >= 89:
                return "89+"
            return text  # Keep ages under 89
        except:
            return text
    
    def _generalize_zip(self, text):
        """Keep first 3 digits if population >20K, else mask."""
        # Simplified - in production, check census data
        if len(text) >= 3:
            return text[:3] + "XX"
        return "[ZIP]"