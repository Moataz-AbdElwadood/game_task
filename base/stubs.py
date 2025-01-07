from abc import ABC, abstractmethod

class BuildingType(ABC):
    @abstractmethod
    def requirements_for_level(self, level: int) -> dict:
        """Returns resource and level requirements for a specific building level."""
        pass

    @abstractmethod
    def build_or_upgrade(self, user, level: int):
        """Handles logic for building or upgrading."""
        pass

    @abstractmethod
    def get_building_time(self, level):
        """Returns the building time based on the level."""
        pass