# load_data.py
import argparse
import pandas as pd
from sqlalchemy.exc import IntegrityError

from db.database import SessionLocal
from db.models import Events, Sessions, Operators

EVENTS_COLS = [
    "Session_ID",
    "Operator_ID",
    "Timestamp",
    "TimeInterval",
    "Address",
    "FunctionCode",
    "CommandResponse",
    "ControlMode",
    "ControlScheme",
    "CRC",
    "DataLength",
    "InvalidFunctionCode",
    "InvalidDataLength",
    "PumpState",
    "SolenoidState",
    "SetPoint",
    "PipelinePSI",
    "PIDCycleTime",
    "PIDDeadband",
    "PIDGain",
    "PIDRate",
    "PIDReset",
    "deltaSetPoint",
    "deltaPipelinePSI",
    "deltaPIDCycleTime",
    "deltaPIDDeadband",
    "deltaPIDGain",
    "deltaPIDRate",
    "deltaPIDReset",
    "Label",
    # we keep Shift only to build Sessions (not inserted into Events)
    "Shift",
]

SHIFT_MAP = {"DAY": 1, "NIGHT": 2}  # must match shift_definitions.shift_id


def ensure_operators(db, operator_ids: list[str]) -> None:
    if not operator_ids:
        return
    existing = set(
        oid for (oid,) in db.query(Operators.Operator_ID)
        .filter(Operators.Operator_ID.in_(operator_ids)).all()
    )
    missing = [oid for oid in operator_ids if oid not in existing]
    if missing:
        rows = [{"Operator_ID": oid, "Operator_Rank": True} for oid in missing]
        db.bulk_insert_mappings(Operators, rows)
        db.commit()


def ensure_sessions(db, df: pd.DataFrame) -> None:
    """
    Create Sessions rows (one per Session_ID) using:
      Operator_ID (first), Shift_ID(from Shift), Session_Start/End(min/max Timestamp),
      Inactivity_Threshold_Min(default 10)
    """
    sess = (
        df.groupby("Session_ID", as_index=False)
          .agg(
              Operator_ID=("Operator_ID", "first"),
              Shift=("Shift", "first"),
              Session_Start=("Timestamp", "min"),
              Session_End=("Timestamp", "max"),
          )
    )

    sess["Shift_ID"] = (
        sess["Shift"].astype(str).str.strip().str.upper().map(SHIFT_MAP)
    )
    if sess["Shift_ID"].isna().any():
        bad = sess[sess["Shift_ID"].isna()][["Shift"]].head(10)
        raise ValueError(f"Unrecognized Shift values (update SHIFT_MAP). Examples:\n{bad}")

    sess["Inactivity_Threshold_Min"] = 10

    session_ids = sess["Session_ID"].astype(int).tolist()
    existing = set(
        sid for (sid,) in db.query(Sessions.Session_ID)
        .filter(Sessions.Session_ID.in_(session_ids)).all()
    )

    to_insert = sess[~sess["Session_ID"].isin(existing)].copy()
    if not to_insert.empty:
        rows = to_insert[[
            "Session_ID", "Operator_ID", "Shift_ID",
            "Session_Start", "Session_End", "Inactivity_Threshold_Min"
        ]].to_dict("records")
        db.bulk_insert_mappings(Sessions, rows)
        db.commit()


def load_events_csv(csv_path: str, chunksize: int = 50_000) -> None:
    db = SessionLocal()
    total_inserted = 0

    try:
        for chunk in pd.read_csv(csv_path, chunksize=chunksize):
            # clean headers
            chunk.columns = (
                chunk.columns.astype(str)
                .str.replace("\ufeff", "", regex=False)
                .str.strip()
            )

            keep = [c for c in EVENTS_COLS if c in chunk.columns]
            df = chunk[keep].copy()

            # required for sessions + events
            required = ["Session_ID", "Operator_ID", "Timestamp", "Shift"]
            miss = [c for c in required if c not in df.columns]
            if miss:
                raise ValueError(f"CSV missing required columns: {miss}")

            # types
            df["Session_ID"] = pd.to_numeric(df["Session_ID"], errors="coerce").astype("Int64")
            df["Operator_ID"] = df["Operator_ID"].astype(str).str.strip()

            # full datetime parse
            df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

            # clean strings
            if "Label" in df.columns:
                df["Label"] = df["Label"].astype(str).str.strip()

            # prevent varchar length issues (adjust if your DB uses different sizes)
            MAXLEN = {
                "Address": 50,
                "CommandResponse": 50,
                "ControlMode": 50,
                "ControlScheme": 100,  # SolenoidControlScheme > 20
                "PumpState": 50,
                "SolenoidState": 50,
                "Label": 50,
                "FunctionCode": 10,
                "InvalidFunctionCode": 5,
                "InvalidDataLength": 5,
            }
            for col, mx in MAXLEN.items():
                if col in df.columns:
                    df[col] = df[col].astype(str).str.slice(0, mx)

            # drop bad rows
            df = df.dropna(subset=["Session_ID", "Operator_ID", "Timestamp"])

            # 1) ensure Operators exist
            ensure_operators(db, df["Operator_ID"].unique().tolist())

            # 2) ensure Sessions exist
            ensure_sessions(db, df)

            # 3) insert Events (exclude Shift)
            event_df = df[[c for c in EVENTS_COLS if c in df.columns and c != "Shift"]].copy()
            event_df = event_df.where(pd.notnull(event_df), None)

            records = event_df.to_dict(orient="records")
            db.bulk_insert_mappings(Events, records)
            db.commit()

            total_inserted += len(records)
            print(f"Inserted {len(records):,} events (total: {total_inserted:,})")

        print(f"\nDone. Total inserted into Events: {total_inserted:,}")

    except IntegrityError as e:
        db.rollback()
        print("\nIntegrityError:", e)
        raise
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--chunksize", type=int, default=50_000)
    args = parser.parse_args()
    load_events_csv(args.csv, chunksize=args.chunksize)


if __name__ == "__main__":
    main()
