# reinfdata.py - PowerPlay Data Types for Reinforcement

# Valid PowerPlay data types that can be collected for reinforcement
VALID_REINFORCEMENT_DATA_TYPES = {
    "poweremployeedata": "Power Association Data",
    "powerclassifieddata": "Power Classified Data",
    "powerpropagandadata": "Power Political Data"
}

def is_valid_reinf_data(name: str) -> bool:
    """Check if cargo name is a valid Reinforcement data type"""
    return name.lower() in VALID_REINFORCEMENT_DATA_TYPES

def get_reinf_display_name(name: str) -> str:
    """Get human-readable display name for Reinforcement data type"""
    return VALID_REINFORCEMENT_DATA_TYPES.get(name.lower(), name)
