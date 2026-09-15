import pandas as pd


INPUT_FILE = "data/raw/jobs_data_science_100.csv"
OUTPUT_FILE = "data/processed/jobs_standardized.csv"


def standardize_jobs(df: pd.DataFrame) -> pd.DataFrame:
    """Convert collected BA job data into the project's standard schema."""

    standardized = pd.DataFrame()

    standardized["job_id"] = df["job_id"].astype(str).str.strip()
    standardized["title"] = df["title"].fillna("").astype(str).str.strip()
    standardized["company"] = df["company"].fillna("").astype(str).str.strip()
    standardized["location"] = df["location"].fillna("").astype(str).str.strip()
    standardized["state"] = df["state"].fillna("").astype(str).str.strip()
    standardized["job_type"] = df["job_type"].fillna("").astype(str).str.strip()
    standardized["description"] = df["description"].fillna("").astype(str).str.strip()

    standardized["salary"] = df["salary"].fillna("").astype(str).str.strip()
    standardized["contract"] = df["contract"].fillna("").astype(str).str.strip()
    standardized["home_office"] = df["home_office"].fillna(False)

    standardized["posted_date"] = pd.to_datetime(
        df["posted_date"],
        errors="coerce"
    )

    standardized["source"] = df["source"].fillna("").astype(str).str.strip()

    standardized = standardized.drop_duplicates(
        subset=["job_id"]
    ).reset_index(drop=True)

    return standardized


def main() -> None:
    """Standardize the collected job dataset."""

    df = pd.read_csv(INPUT_FILE)

    standardized = standardize_jobs(df)

    standardized.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("Job Standardization Complete")
    print("-----------------------------")
    print(f"Input rows: {len(df)}")
    print(f"Output rows: {len(standardized)}")
    print(f"Columns: {len(standardized.columns)}")
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()