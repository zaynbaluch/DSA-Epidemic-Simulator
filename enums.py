from enum import Enum

class State(Enum):
    SUSCEPTIBLE = 0
    LATENT = 1
    INF_ASYMP = 2
    INF_SYMP = 3
    HOSPITALIZED = 4
    RECOVERED = 5
    DEAD = 6

class LocationType(Enum):
    HOUSEHOLD = 0
    SCHOOL = 1
    WORKPLACE = 2
    MARKET = 3
    CAFE = 4
    PARK = 5
    HOSPITAL = 6
    CEMETERY = 7
    QUARANTINE = 8

class AgeGroup(Enum):
    CHILD = 0
    ADULT = 1
    SENIOR = 2

class MobilityType(Enum):
    HIGH = 0
    MODERATE = 1
    LOW = 2