"""Small, actionable validation checks for standardized job data."""
from pathlib import Path
import pandas as pd

REQUIRED_COLUMNS = {"job_id", "title", "company", "location", "state", "job_type", "description", "posted_date", "source", "source_url"}


def data_quality_report(df: pd.DataFrame) -> dict:
    """Return compact diagnostics suitable for pipeline logs and tests."""
    missing_columns = sorted(REQUIRED_COLUMNS - set(df.columns))
    blank = {column: int(df[column].fillna("").astype(str).str.strip().eq("").sum()) for column in ("job_id", "title", "company") if column in df}
    invalid_dates = int(pd.to_datetime(df["posted_date"], errors="coerce").isna().sum()) if "posted_date" in df else 0
    invalid_ids = blank.get("job_id", 0) + (int(df["job_id"].astype(str).str.lower().eq("nan").sum()) if "job_id" in df else 0)
    return {"rows": len(df), "missing_columns": missing_columns, "duplicate_rows": int(df.duplicated().sum()), "duplicate_job_ids": int(df["job_id"].duplicated().sum()) if "job_id" in df else None, "missing_values": int(df.isna().sum().sum()), "empty_titles": blank.get("title"), "empty_companies": blank.get("company"), "invalid_job_ids": invalid_ids, "invalid_dates": invalid_dates}


def check_data_quality(df: pd.DataFrame) -> dict:
    """Print and return the report for reproducible command-line checks."""
    report = data_quality_report(df)
    print("Data Quality Report")
    for key, value in report.items(): print(f"{key.replace('_', ' ').title()}: {value}")
    return report


if __name__ == "__main__":
    check_data_quality(pd.read_csv(Path(__file__).resolve().parents[1] / "data" / "processed" / "jobs_standardized.csv"))
