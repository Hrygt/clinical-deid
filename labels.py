# labels.py

# 25 Core PHI entity types (matching your priority list)
ENTITY_TYPES = [
    # HIPAA Direct Identifiers
    "FIRST_NAME",
    "LAST_NAME", 
    "SSN",
    "MEDICAL_RECORD_NUMBER",
    "HEALTH_PLAN_BENEFICIARY_NUMBER",
    "DATE_OF_BIRTH",
    
    # Contact Info
    "PHONE_NUMBER",
    "FAX_NUMBER",
    "EMAIL",
    "STREET_ADDRESS",
    "CITY",
    "STATE",
    "POSTCODE",
    "COUNTY",
    "COUNTRY",
    
    # Dates/Times
    "DATE",
    "DATE_TIME",
    "TIME",
    
    # Other IDs
    "ACCOUNT_NUMBER",
    "CUSTOMER_ID",
    "EMPLOYEE_ID",
    "UNIQUE_ID",
    "BIOMETRIC_IDENTIFIER",
    "CERTIFICATE_LICENSE_NUMBER",
    
    # Age (quasi-identifier but HIPAA relevant for 89+)
    "AGE",
]

# BILOU tagging scheme
BILOU_TAGS = ["B", "I", "L", "U"]

# Build label mappings
def build_label_maps():
    labels = ["O"]  # Outside tag first
    
    for entity in ENTITY_TYPES:
        for tag in BILOU_TAGS:
            labels.append(f"{tag}-{entity}")
    
    label2id = {label: i for i, label in enumerate(labels)}
    id2label = {i: label for i, label in enumerate(labels)}
    
    return labels, label2id, id2label

LABELS, LABEL2ID, ID2LABEL = build_label_maps()
NUM_LABELS = len(LABELS)  # 101

# Map Nemotron labels to our standardized labels
NEMOTRON_TO_ENTITY = {
    "first_name": "FIRST_NAME",
    "last_name": "LAST_NAME",
    "ssn": "SSN",
    "medical_record_number": "MEDICAL_RECORD_NUMBER",
    "health_plan_beneficiary_number": "HEALTH_PLAN_BENEFICIARY_NUMBER",
    "date_of_birth": "DATE_OF_BIRTH",
    "phone_number": "PHONE_NUMBER",
    "fax_number": "FAX_NUMBER",
    "email": "EMAIL",
    "street_address": "STREET_ADDRESS",
    "city": "CITY",
    "state": "STATE",
    "postcode": "POSTCODE",
    "county": "COUNTY",
    "country": "COUNTRY",
    "date": "DATE",
    "date_time": "DATE_TIME",
    "time": "TIME",
    "account_number": "ACCOUNT_NUMBER",
    "customer_id": "CUSTOMER_ID",
    "employee_id": "EMPLOYEE_ID",
    "unique_id": "UNIQUE_ID",
    "biometric_identifier": "BIOMETRIC_IDENTIFIER",
    "certificate_license_number": "CERTIFICATE_LICENSE_NUMBER",
    "age": "AGE",
}

if __name__ == "__main__":
    print(f"Total labels: {NUM_LABELS}")
    print(f"Entity types: {len(ENTITY_TYPES)}")
    print(f"\nFirst 10 labels: {LABELS[:10]}")
    print(f"Last 10 labels: {LABELS[-10:]}")