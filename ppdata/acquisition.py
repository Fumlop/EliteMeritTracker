# acqdata.py - PowerPlay Data Types for Acquisition

# All PowerPlay data types work for acquisition (in neutral systems)
VALID_ACQUISITION_DATA_TYPES = {
    "poweremployeedata": "Power Association Data",
    "powerclassifieddata": "Power Classified Data",
    "powerfinancialrecords": "Power Industrial Data",
    "powerpropagandadata": "Power Political Data",
    "powerresearchdata": "Power Research Data"
}

def is_valid_acq_data(name: str) -> bool:
    """Check if cargo name is a valid Acquisition data type"""
    return name.lower() in VALID_ACQUISITION_DATA_TYPES

def get_acq_display_name(name: str) -> str:
    """Get human-readable display name for Acquisition data type"""
    return VALID_ACQUISITION_DATA_TYPES.get(name.lower(), name)
