"""
hands_free/hands_free_state.py
State machine for Hands-Free Mode.
"""
from enum import Enum, auto

class HandsFreeState(Enum):
    INACTIVE          = auto()
    STARTING          = auto()
    CALIBRATING       = auto()
    ACTIVE            = auto()
    PAUSED            = auto()
    LOCKED            = auto()
    CAMERA_UNAVAILABLE = auto()
    ERROR             = auto()
    STOPPING          = auto()
    EMERGENCY_STOPPED = auto()

# Valid state transitions
VALID_TRANSITIONS = {
    HandsFreeState.INACTIVE:           {HandsFreeState.STARTING, HandsFreeState.CAMERA_UNAVAILABLE},
    HandsFreeState.STARTING:           {HandsFreeState.CALIBRATING, HandsFreeState.ACTIVE, HandsFreeState.CAMERA_UNAVAILABLE, HandsFreeState.ERROR, HandsFreeState.INACTIVE},
    HandsFreeState.CALIBRATING:        {HandsFreeState.ACTIVE, HandsFreeState.ERROR, HandsFreeState.STOPPING, HandsFreeState.EMERGENCY_STOPPED},
    HandsFreeState.ACTIVE:             {HandsFreeState.PAUSED, HandsFreeState.LOCKED, HandsFreeState.STOPPING, HandsFreeState.ERROR, HandsFreeState.EMERGENCY_STOPPED},
    HandsFreeState.PAUSED:             {HandsFreeState.ACTIVE, HandsFreeState.STOPPING, HandsFreeState.EMERGENCY_STOPPED, HandsFreeState.LOCKED},
    HandsFreeState.LOCKED:             {HandsFreeState.ACTIVE, HandsFreeState.PAUSED, HandsFreeState.STOPPING, HandsFreeState.EMERGENCY_STOPPED},
    HandsFreeState.CAMERA_UNAVAILABLE: {HandsFreeState.INACTIVE, HandsFreeState.STARTING},
    HandsFreeState.ERROR:              {HandsFreeState.INACTIVE, HandsFreeState.STOPPING},
    HandsFreeState.STOPPING:           {HandsFreeState.INACTIVE},
    HandsFreeState.EMERGENCY_STOPPED:  {HandsFreeState.INACTIVE},
}

def can_transition(current: HandsFreeState, target: HandsFreeState) -> bool:
    return target in VALID_TRANSITIONS.get(current, set())
