
import pandas as pd


def clean_jobs(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize job posting data."""

    df = df.copy()

    # Standardize text fields
    text_columns = [
        "title",
        "company",
        "location",
        "state",
        "job_type",
        "description",
        "german_requirement",
        "source",
    ]

    for column in text_columns:
        df[column] = df[column].fillna("").astype(str).str.strip()

    # Convert salary fields to numeric values
    df["salary_min"] = pd.to_numeric(df["salary_min"], errors="coerce")
    df["salary_max"] = pd.to_numeric(df["salary_max"], errors="coerce")

    # Convert date field
    df["posted_date"] = pd.to_datetime(
        df["posted_date"],
        errors="coerce"
    )

    # Convert job ID to string
    df["job_id"] = df["job_id"].astype(str).str.strip()

    # Remove duplicate job IDs
    df = df.drop_duplicates(subset=["job_id"])

    return df


if __name__ == "__main__":
    input_file = "data/raw/jobs_raw.csv"
    output_file = "data/processed/jobs_cleaned.csv"

    jobs = pd.read_csv(input_file)

    cleaned_jobs = clean_jobs(jobs)

    cleaned_jobs.to_csv(output_file, index=False)

    print("Data Cleaning Complete")
    print("----------------------")
    print(f"Input rows: {len(jobs)}")
    print(f"Output rows: {len(cleaned_jobs)}")
    print(f"Saved to: {output_file}")
