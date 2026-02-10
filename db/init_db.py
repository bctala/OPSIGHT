"""
Creates all OPSIGHT tables in the database. Run after configuring DATABASE_URL.
Alembic can be used later for versioned migrations; this script only creates tables.
"""

from db.database import engine
from db.models import (
    Alert_CTI_Links,
    Alerts,
    Baseline_Profiles,
    Crew_Rotation,
    Crews,
    CTI_Objects,
    Detection,
    Events,
    Operators,
    Session_Features,
    Sessions,
    Shift_Definitions,
    Shift_Instances,
    Users,
)

# Import models so they are registered with Base.metadata
__all__ = [
    "Users",
    "Operators",
    "Crews",
    "Shift_Definitions",
    "Crew_Rotation",
    "Shift_Instances",
    "Sessions",
    "Events",
    "Session_Features",
    "Baseline_Profiles",
    "Detection",
    "Alerts",
    "CTI_Objects",
    "Alert_CTI_Links",
]


def init_db() -> None:
    """Create all tables defined in the ORM models."""
    from db.database import Base

    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("DB initialized")
