from log import logger

class Cargo:
    def __init__(self, name: str, count: int = 1):
        self.name = name
        self.count = count
    
    def add(self, amount: int = 1):
        if amount <= 0:
            logger.error("Cannot add negative or zero amount")
            return
        self.count += amount
    
    def remove(self, amount: int = 1):
        if amount <= 0:
            logger.error("Cannot remove negative or zero amount")
            return
        self.count = max(0, self.count - amount)
    
    def to_dict(self):
        return {
            "name": self.name,
            "count": self.count
        }
    
    @staticmethod
    def from_dict(data: dict):
        return Cargo(
            name=data.get("name", "Unknown"),
            count=data.get("count", 0)
        )
