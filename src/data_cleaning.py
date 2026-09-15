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

    # Remove duplicate job IDs
    df = df.drop_duplicates(subset=["job_id"])

    return df


if __name__ == "__main__":
    jobs = pd.read_csv("data/sample_jobs.csv")

    cleaned_jobs = clean_jobs(jobs)

    print("Data Cleaning Complete")
    print("----------------------")
    print(f"Rows: {len(cleaned_jobs)}")
    print(f"Columns: {len(cleaned_jobs.columns)}")
    print("\nData types:")
    print(cleaned_jobs.dtypes)