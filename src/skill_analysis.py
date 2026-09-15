import re
import sys

import pandas as pd

sys.path.insert(0, "src")

from skill_dictionary import SKILLS


INPUT_FILE = "data/processed/jobs_standardized.csv"
SKILL_DEMAND_OUTPUT = "data/processed/skill_demand.csv"
JOB_SKILLS_OUTPUT = "data/processed/job_skills.csv"


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


def extract_job_skills(df: pd.DataFrame) -> pd.DataFrame:
    """Extract detected skills for every job."""

    results = []

    for _, row in df.iterrows():

        description = row["description"]

        for skill in SKILLS:

            if skill_found(description, skill):
                results.append(
                    {
                        "job_id": row["job_id"],
                        "skill": skill
                    }
                )

    return pd.DataFrame(results)


def analyze_skill_demand(job_skills: pd.DataFrame) -> pd.DataFrame:
    """Count how many jobs mention each skill."""

    results = (
        job_skills
        .groupby("skill")["job_id"]
        .nunique()
        .reset_index(name="job_count")
        .sort_values(
            by="job_count",
            ascending=False
        )
        .reset_index(drop=True)
    )

    return results


def main() -> None:
    """Extract job skills and calculate skill demand."""

    df = pd.read_csv(INPUT_FILE)

    job_skills = extract_job_skills(df)

    job_skills.to_csv(
        JOB_SKILLS_OUTPUT,
        index=False
    )

    skill_demand = analyze_skill_demand(job_skills)

    skill_demand.to_csv(
        SKILL_DEMAND_OUTPUT,
        index=False
    )

    print("Job Skill Analysis")
    print("------------------")
    print(f"Jobs analyzed: {len(df)}")
    print(f"Job-skill matches: {len(job_skills)}")
    print(f"Skills detected: {len(skill_demand)}")
    print()
    print(skill_demand.to_string(index=False))
    print()
    print(f"Saved: {JOB_SKILLS_OUTPUT}")
    print(f"Saved: {SKILL_DEMAND_OUTPUT}")


if __name__ == "__main__":
    main()