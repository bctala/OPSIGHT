"""
OPSIGHT ORM models (Physical Data Design Tables 15–25 and auxiliary tables).
SQLAlchemy 2.0 declarative models for ICS operator behavior monitoring.
"""

from datetime import date, datetime, time
from sqlalchemy import func
from sqlalchemy import String

from sqlalchemy import (
     Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


# ---------------------------------------------------------------------------
# Auxiliary / reference tables (no FKs to other app tables)
# ---------------------------------------------------------------------------


class Crews(Base):
    """Crews: crew groupings (e.g. Crew1, Crew2) for shift assignment."""

    __tablename__ = "crews"

    Crew_ID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    crew_name: Mapped[str] = mapped_column(String(10), nullable=False)
    Created_At: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    operators: Mapped[list["Operators"]] = relationship(
        "Operators", back_populates="crew", foreign_keys="Operators.Crew_ID"
    )
    crew_rotations: Mapped[list["Crew_Rotation"]] = relationship(
        "Crew_Rotation", back_populates="crew"
    )
    shift_instances: Mapped[list["Shift_Instances"]] = relationship(
        "Shift_Instances", back_populates="crew"
    )


class Shift_Definitions(Base):
    """Shift_Definitions: shift types (name, start/end time, duration)."""

    __tablename__ = "shift_definitions"

    shift_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shift_name: Mapped[str] = mapped_column(String(20), nullable=True)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    duration_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    Created_At: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())


    # Relationships
    operators: Mapped[list["Operators"]] = relationship(
        "Operators",
        back_populates="default_shift",
        foreign_keys="Operators.Default_Shift_ID",
    )
    sessions: Mapped[list["Sessions"]] = relationship(
        "Sessions", back_populates="shift_definition", foreign_keys="Sessions.Shift_ID"
    )
    baseline_profiles: Mapped[list["Baseline_Profiles"]] = relationship(
        "Baseline_Profiles",
        back_populates="shift_definition",
        foreign_keys="Baseline_Profiles.Shift_ID",
    )
    shift_instances: Mapped[list["Shift_Instances"]] = relationship(
        "Shift_Instances", back_populates="shift_definition"
    )


# ---------------------------------------------------------------------------
# Users (Table 15)
# ---------------------------------------------------------------------------


class Users(Base):
    """Users: application users (Admin/Analyst) for login and access control."""

    __tablename__ = "Users"

    User_ID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    Username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    Password_Hash: Mapped[str] = mapped_column(String(255), nullable=False)
    Role: Mapped[str] = mapped_column(String(30), nullable=False)
    Email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    Is_Active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    Created_At: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    Last_Login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


# ---------------------------------------------------------------------------
# Operators (Table 16), Crew_Rotation, Shift_Instances
# ---------------------------------------------------------------------------


class Operators(Base):
    """Operators: ICS operators linked to a crew and default shift."""

    __tablename__ = "Operators"

    Operator_ID: Mapped[str] = mapped_column(
        String(10), primary_key=True
    )
    Crew_ID: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("crews.Crew_ID"), nullable=True
    )
    Default_Shift_ID: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("shift_definitions.shift_id"), nullable=True
    )
    Operator_Rank: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    Created_At: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    crew: Mapped["Crews | None"] = relationship(
        "Crews", back_populates="operators", foreign_keys=[Crew_ID]
    )
    default_shift: Mapped["Shift_Definitions | None"] = relationship(
        "Shift_Definitions", back_populates="operators", foreign_keys=[Default_Shift_ID]
    )
    sessions: Mapped[list["Sessions"]] = relationship(
        "Sessions", back_populates="operator"
    )
    events: Mapped[list["Events"]] = relationship(
        "Events", back_populates="operator", foreign_keys="Events.Operator_ID"
    )
    baseline_profiles: Mapped[list["Baseline_Profiles"]] = relationship(
        "Baseline_Profiles", back_populates="operator"
    )


class Crew_Rotation(Base):
    """Crew_Rotation: rotation pattern (on/off days, anchor date) per crew."""

    __tablename__ = "Crew_Rotation"

    Rotation_ID: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    Crew_ID: Mapped[int] = mapped_column(
        Integer, ForeignKey("crews.Crew_ID"), nullable=False
    )
    Anchor_Date: Mapped[date] = mapped_column(Date, nullable=False)
    On_Days: Mapped[int] = mapped_column(Integer, nullable=False)
    Off_Days: Mapped[int] = mapped_column(Integer, nullable=False)
    Created_At: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    crew: Mapped["Crews"] = relationship("Crews", back_populates="crew_rotations")


class Shift_Instances(Base):
    """Shift_Instances: concrete shift occurrences for a crew and shift definition."""

    __tablename__ = "shift_instances"

    shift_instance_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    crew_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("crews.Crew_ID"), nullable=False
    )
    shift_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("shift_definitions.shift_id"), nullable=False
    )
    shift_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    shift_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    Created_At: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    crew: Mapped["Crews"] = relationship("Crews", back_populates="shift_instances")
    shift_definition: Mapped["Shift_Definitions"] = relationship(
        "Shift_Definitions", back_populates="shift_instances"
    )
    sessions: Mapped[list["Sessions"]] = relationship(
        "Sessions", back_populates="shift_instance"
    )


# ---------------------------------------------------------------------------
# Sessions (Table 18)
# ---------------------------------------------------------------------------


class Sessions(Base):
    """Sessions: operator work session within a shift instance."""

    __tablename__ = "Sessions"
    __table_args__ = (
    Index("ix_sessions_operator_start", "Operator_ID", "Session_Start"),
    Index("ix_sessions_shift_start", "Shift_ID", "Session_Start"),
)

    Session_ID: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    shift_instance_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("shift_instances.shift_instance_id"),
        nullable=True,
    )
    Operator_ID: Mapped[str] = mapped_column(
        String(10), ForeignKey("Operators.Operator_ID"), nullable=False
    )
    Shift_ID: Mapped[int] = mapped_column(
        Integer, ForeignKey("shift_definitions.shift_id"), nullable=False
    )
    Session_Start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    Session_End: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    Inactivity_Threshold_Min: Mapped[int] = mapped_column(Integer, nullable=False)
    Created_At: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    shift_instance: Mapped["Shift_Instances | None"] = relationship(
        "Shift_Instances", back_populates="sessions"
    )
    operator: Mapped["Operators"] = relationship(
        "Operators", back_populates="sessions", foreign_keys=[Operator_ID]
    )
    shift_definition: Mapped["Shift_Definitions"] = relationship(
        "Shift_Definitions", back_populates="sessions", foreign_keys=[Shift_ID]
    )
    events: Mapped[list["Events"]] = relationship(
    "Events", back_populates="session", cascade="all, delete-orphan"
    )

    session_features: Mapped["Session_Features | None"] = relationship(
        "Session_Features", back_populates="session", uselist=False, cascade="all, delete-orphan"
    )

    alerts: Mapped[list["Alerts"]] = relationship(
        "Alerts", back_populates="session", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# Events (Table 19)
# ---------------------------------------------------------------------------


class Events(Base):
    """Events: ICS command/response events within a session (Modbus/process metrics)."""

    __tablename__ = "Events"
    __table_args__ = (
    Index("ix_events_session_time", "Session_ID", "Timestamp"),
    Index("ix_events_operator_time", "Operator_ID", "Timestamp"),
    Index("ix_events_address_fc", "Address", "FunctionCode"),
)

    Event_ID: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    Session_ID: Mapped[int] = mapped_column(
        Integer, ForeignKey("Sessions.Session_ID"), nullable=False
    )
    Operator_ID: Mapped[str] = mapped_column(
    String(10), ForeignKey("Operators.Operator_ID"), nullable=False
)
    Timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    TimeInterval: Mapped[float] = mapped_column(Float, nullable=False)
    Address: Mapped[str] = mapped_column(String(20), nullable=False)
    FunctionCode: Mapped[str] = mapped_column(String(10), nullable=False)
    CommandResponse: Mapped[str] = mapped_column(String(20), nullable=False)
    ControlMode: Mapped[str] = mapped_column(String(20), nullable=False)
    ControlScheme: Mapped[str] = mapped_column(String(50), nullable=False)
    CRC: Mapped[int] = mapped_column(Integer, nullable=False)
    DataLength: Mapped[int] = mapped_column(Integer, nullable=False)
    InvalidFunctionCode: Mapped[str] = mapped_column(String(5), nullable=False)
    InvalidDataLength: Mapped[str] = mapped_column(String(5), nullable=False)
    PumpState: Mapped[str] = mapped_column(String(20), nullable=False)
    SolenoidState: Mapped[str] = mapped_column(String(20), nullable=False)
    SetPoint: Mapped[float] = mapped_column(Float, nullable=False)
    PipelinePSI: Mapped[float] = mapped_column(Float, nullable=False)
    PIDCycleTime: Mapped[float] = mapped_column(Float, nullable=False)
    PIDDeadband: Mapped[float] = mapped_column(Float, nullable=False)
    PIDGain: Mapped[float] = mapped_column(Float, nullable=False)
    PIDRate: Mapped[float] = mapped_column(Float, nullable=False)
    PIDReset: Mapped[float] = mapped_column(Float, nullable=False)
    deltaSetPoint: Mapped[float] = mapped_column(Float, nullable=False)
    deltaPipelinePSI: Mapped[float] = mapped_column(Float, nullable=False)
    deltaPIDCycleTime: Mapped[float] = mapped_column(Float, nullable=False)
    deltaPIDDeadband: Mapped[float] = mapped_column(Float, nullable=False)
    deltaPIDGain: Mapped[float] = mapped_column(Float, nullable=False)
    deltaPIDRate: Mapped[float] = mapped_column(Float, nullable=False)
    deltaPIDReset: Mapped[float] = mapped_column(Float, nullable=False)
    Label: Mapped[str] = mapped_column(String(20), nullable=False)

    session: Mapped["Sessions"] = relationship(
        "Sessions", back_populates="events", foreign_keys=[Session_ID]
    )
    operator: Mapped["Operators"] = relationship(
        "Operators", back_populates="events", foreign_keys=[Operator_ID]
    )
    detections: Mapped[list["Detection"]] = relationship(
    "Detection", back_populates="event"
    )
    alerts: Mapped[list["Alerts"]] = relationship(
    "Alerts", back_populates="event", cascade="all, delete-orphan"
    )



# ---------------------------------------------------------------------------
# Session_Features (Table 20) — 1:1 with Sessions
# ---------------------------------------------------------------------------


class Session_Features(Base):
    """Session_Features: aggregated behavioral features per session (1:1 with Sessions)."""

    __tablename__ = "Session_Features"

    Session_features_ID: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    Session_ID: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Sessions.Session_ID"),
        unique=True,
        nullable=False,
    )
    Created_At: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    Command_Frequency: Mapped[float] = mapped_column(Float, nullable=False)
    Inter_Command_Mean: Mapped[float] = mapped_column(Float, nullable=False)
    Inter_Command_Std: Mapped[float] = mapped_column(Float, nullable=False)
    Command_Burst_Rate: Mapped[float] = mapped_column(Float, nullable=False)
    Control_Mode_Change_Rate: Mapped[float] = mapped_column(Float, nullable=False)
    High_Risk_Command_Ratio: Mapped[float] = mapped_column(Float, nullable=False)
    Invalid_Command_Rate: Mapped[float] = mapped_column(Float, nullable=False)
    Pump_State_Change_Rate: Mapped[float] = mapped_column(Float, nullable=False)
    SetPoint_Shock_Event_Rate: Mapped[float] = mapped_column(Float, nullable=False)
    PID_Modification_Rate: Mapped[float] = mapped_column(Float, nullable=False)
    Command_Entropy: Mapped[float] = mapped_column(Float, nullable=False)
    Process_Command_Correlation: Mapped[float] = mapped_column(Float, nullable=False)

    session: Mapped["Sessions"] = relationship(
        "Sessions", back_populates="session_features"
    )


# ---------------------------------------------------------------------------
# Baseline_Profiles (Table 21)
# ---------------------------------------------------------------------------


class Baseline_Profiles(Base):
    """Baseline_Profiles: operator baseline (and optional shift) for anomaly detection."""

    __tablename__ = "Baseline_Profiles"
    __table_args__ = (
    UniqueConstraint("Operator_ID", "Shift_ID", "Baseline_Version", name="uq_baseline_operator_shift_version"),
    Index("ix_baseline_operator_shift", "Operator_ID", "Shift_ID"),
    )

    Baseline_ID: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    Operator_ID: Mapped[str] = mapped_column(
        String(10), ForeignKey("Operators.Operator_ID"), nullable=False
    )
    Shift_ID: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("shift_definitions.shift_id"), nullable=True
    )
    Baseline_Version: Mapped[str] = mapped_column(String(20), nullable=False)
    Trained_From: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    Trained_To: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    Profile_JSON: Mapped[str] = mapped_column(Text, nullable=False)
    Created_At: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    operator: Mapped["Operators"] = relationship(
        "Operators", back_populates="baseline_profiles"
    )
    shift_definition: Mapped["Shift_Definitions | None"] = relationship(
        "Shift_Definitions", back_populates="baseline_profiles", foreign_keys=[Shift_ID]
    )
    detections: Mapped[list["Detection"]] = relationship(
        "Detection", back_populates="baseline_profile"
    )


# ---------------------------------------------------------------------------
# Detection (Table 22) — 1:1 with Events
# ---------------------------------------------------------------------------


class Detection(Base):
    """Detection: anomaly detection result for a single event (model score, threshold)."""

    __tablename__ = "Detection"
    __table_args__ = (
    UniqueConstraint("Event_ID", "Baseline_ID", "Model_Type", name="uq_detection_event_baseline_model"),
    Index("ix_detection_event_id", "Event_ID"),
    Index("ix_detection_baseline_time", "Baseline_ID", "Detection_Time"),
)

    Detection_ID: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    Event_ID: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Events.Event_ID"),
        nullable=False,
    )
    Baseline_ID: Mapped[int] = mapped_column(
        Integer, ForeignKey("Baseline_Profiles.Baseline_ID"), nullable=False
    )
    Model_Type: Mapped[str] = mapped_column(String(30), nullable=False)
    Anomaly_Score: Mapped[float] = mapped_column(Float, nullable=False)
    Threshold: Mapped[float] = mapped_column(Float, nullable=False)
    Evidence_JSON: Mapped[str] = mapped_column(Text, nullable=False)
    Predicted_Label: Mapped[str] = mapped_column(String(15), nullable=False)
    Detection_Time: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    event: Mapped["Events"] = relationship(
    "Events", back_populates="detections", foreign_keys=[Event_ID]
    )
    baseline_profile: Mapped["Baseline_Profiles"] = relationship(
        "Baseline_Profiles", back_populates="detections"
    )
    alerts: Mapped[list["Alerts"]] = relationship(
    "Alerts", back_populates="detection", cascade="all, delete-orphan"
    )



# ---------------------------------------------------------------------------
# Alerts (Table 23)
# ---------------------------------------------------------------------------


class Alerts(Base):
    """Alerts: security/operational alerts linked to an event and session."""

    __tablename__ = "Alerts"
    __table_args__ = (
    Index("ix_alerts_time_severity", "Alert_Time", "Severity"),
    Index("ix_alerts_detection_id", "Detection_ID"),
)

    Alert_ID: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    Event_ID: Mapped[int] = mapped_column(
        Integer, ForeignKey("Events.Event_ID"), nullable=False
    )
    Session_ID: Mapped[int] = mapped_column(
        Integer, ForeignKey("Sessions.Session_ID"), nullable=False
    )
    Detection_ID: Mapped[int] = mapped_column(
    Integer, ForeignKey("Detection.Detection_ID"), nullable=False
)
    Alert_Time: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    Severity: Mapped[int] = mapped_column(Integer, nullable=False)
    Alert_Category: Mapped[str] = mapped_column(String(30), nullable=False)
    Alert_Description: Mapped[str] = mapped_column(String(500), nullable=False)

    event: Mapped["Events"] = relationship(
        "Events", back_populates="alerts", foreign_keys=[Event_ID]
    )
    session: Mapped["Sessions"] = relationship(
        "Sessions", back_populates="alerts", foreign_keys=[Session_ID]
    )
    cti_links: Mapped[list["Alert_CTI_Links"]] = relationship(
    "Alert_CTI_Links", back_populates="alert", cascade="all, delete-orphan"
    )
    detection: Mapped["Detection"] = relationship(
    "Detection", back_populates="alerts", foreign_keys=[Detection_ID]
    )


# ---------------------------------------------------------------------------
# CTI_Objects (Table 24)
# ---------------------------------------------------------------------------


class CTI_Objects(Base):
    """CTI_Objects: threat intelligence objects (TTPs, IOCs, rules)."""

    __tablename__ = "CTI_Objects"

    CTI_ID: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    CTI_Type: Mapped[str] = mapped_column(String(30), nullable=False)
    CTI_Name: Mapped[str] = mapped_column(String(150), nullable=False)
    External_ID: Mapped[str | None] = mapped_column(String(50), nullable=True)
    Rule: Mapped[str | None] = mapped_column(String(500), nullable=True)
    Confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    Created_At: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    alert_links: Mapped[list["Alert_CTI_Links"]] = relationship(
        "Alert_CTI_Links", back_populates="cti_object"
    )


# ---------------------------------------------------------------------------
# Alert_CTI_Links (Table 25) — composite PK
# ---------------------------------------------------------------------------


class Alert_CTI_Links(Base):
    """Alert_CTI_Links: many-to-many link between Alerts and CTI_Objects."""

    __tablename__ = "Alert_CTI_Links"

    Alert_ID: Mapped[int] = mapped_column(
        Integer, ForeignKey("Alerts.Alert_ID"), primary_key=True, nullable=False
    )
    CTI_ID: Mapped[int] = mapped_column(
        Integer, ForeignKey("CTI_Objects.CTI_ID"), primary_key=True, nullable=False
    )
    Match_Reason: Mapped[str | None] = mapped_column(String(250), nullable=True)
    Link_Created_At: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    alert: Mapped["Alerts"] = relationship(
        "Alerts", back_populates="cti_links", foreign_keys=[Alert_ID]
    )
    cti_object: Mapped["CTI_Objects"] = relationship(
        "CTI_Objects", back_populates="alert_links", foreign_keys=[CTI_ID]
    )
