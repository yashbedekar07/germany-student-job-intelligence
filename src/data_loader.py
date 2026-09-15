import pandas as pd


def load_jobs(file_path: str) -> pd.DataFrame:
    """Load job postings from a CSV file."""
    df = pd.read_csv(file_path)
    return df


if __name__ == "__main__":
    jobs = load_jobs("data/sample_jobs.csv")

    print("Germany Student Job Intelligence")
    print("--------------------------------")
    print(f"Rows: {len(jobs)}")
    print(f"Columns: {len(jobs.columns)}")
    print("\nColumns:")
    print(jobs.columns.tolist())