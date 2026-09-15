import pandas as pd


REQUIRED_COLUMNS = [
    "job_id",
    "title",
    "company",
    "location",
    "state",
    "job_type",
    "description",
    "salary_min",
    "salary_max",
    "german_requirement",
    "posted_date",
    "source",
    "source_url",
]


def check_data_quality(df: pd.DataFrame) -> None:
    """Check the basic quality of the job dataset."""

    print("Data Quality Report")
    print("-------------------")

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        print(f"Missing columns: {missing_columns}")
    else:
        print("Required columns: OK")

    print(f"Total rows: {len(df)}")
    print(f"Duplicate rows: {df.duplicated().sum()}")
    print(f"Missing values: {df.isna().sum().sum()}")


if __name__ == "__main__":
    jobs = pd.read_csv("data/sample_jobs.csv")
    check_data_quality(jobs)