# umdata.py - PowerPlay Data Types for Undermining

# Valid PowerPlay data types that can be collected for undermining
VALID_UNDERMINING_DATA_TYPES = {
    "poweremployeedata": "Power Association Data",
    "powerclassifieddata": "Power Classified Data",
    "powerfinancialrecords": "Power Industrial Data",
    "powerpropagandadata": "Power Political Data",
    "powerresearchdata": "Power Research Data"
}

def is_valid_um_data(name: str) -> bool:
    """Check if cargo name is a valid Undermining data type"""
    return name.lower() in VALID_UNDERMINING_DATA_TYPES

def get_um_display_name(name: str) -> str:
    """Get human-readable display name for Undermining data type"""
    return VALID_UNDERMINING_DATA_TYPES.get(name.lower(), name)
