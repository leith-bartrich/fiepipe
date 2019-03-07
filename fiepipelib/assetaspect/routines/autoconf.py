from enum import Enum


class AutoConfigurationResult(Enum):
    NO_CHANGES = 1 #complete.  no changes made.
    CHANGES_MADE = 2 #complete.  changes were made.
    UNCLEAR = 3 #complete.  unclear if changes were made.
    INTERVENTION_REQUIRED = 4 #incomplete.  user intervention required.