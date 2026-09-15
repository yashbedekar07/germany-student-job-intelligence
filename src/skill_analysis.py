import re
import sys

import pandas as pd

sys.path.insert(0, "src")

from skill_dictionary import SKILLS


INPUT_FILE = "data/raw/jobs_data_science.csv"
OUTPUT_FILE = "data/processed/skill_demand.csv"


def skill_found(text: str, skill: str) -> bool:
    """Check whether a skill appears as a meaningful term in the text."""

    pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"

    return bool(
        re.search(
            pattern,
            str(text),
            flags=re.IGNORECASE
        )
    )


def analyze_skill_demand(df: pd.DataFrame) -> pd.DataFrame:
    """Count how many job descriptions mention each skill."""

    results = []

    descriptions = df["description"].fillna("")

    for skill in SKILLS:
        job_count = descriptions.apply(
            lambda text: skill_found(text, skill)
        ).sum()

        if job_count > 0:
            results.append(
                {
                    "skill": skill,
                    "job_count": int(job_count)
                }
            )

    return (
        pd.DataFrame(results)
        .sort_values(
            by="job_count",
            ascending=False
        )
        .reset_index(drop=True)
    )


def main() -> None:
    """Run skill demand analysis and save the results."""

    df = pd.read_csv(INPUT_FILE)

    results = analyze_skill_demand(df)

    results.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("Skill Demand Analysis")
    print("---------------------")
    print(results.to_string(index=False))
    print()
    print(f"Jobs analyzed: {len(df)}")
    print(f"Skills detected: {len(results)}")
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()