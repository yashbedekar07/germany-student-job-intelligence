"""Extract canonical technical skills from standardized job postings."""
from pathlib import Path
import re
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill_dictionary import SKILL_ALIASES  # noqa: E402

INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "jobs_standardized.csv"
SKILL_DEMAND_OUTPUT = PROJECT_ROOT / "data" / "processed" / "skill_demand.csv"
JOB_SKILLS_OUTPUT = PROJECT_ROOT / "data" / "processed" / "job_skills.csv"
EDUCATION_PATTERNS = (
    r"\b(?:studying|study|student|students|degree|bachelor|master|studium)\b.{0,100}\bdata science\b",
    r"\bdata science\b.{0,100}\b(?:degree|bachelor|master|studium|or similar)\b",
)


def normalize_text(value: object) -> str:
    """Normalize whitespace without changing meaning."""
    return re.sub(r"\s+", " ", str(value or "")).strip()


def phrase_found(text: str, phrase: str) -> bool:
    """Match a phrase at word boundaries, protecting short skills such as R and AI."""
    return bool(re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text, re.IGNORECASE))


def extract_job_skills(df: pd.DataFrame) -> pd.DataFrame:
    """Return one canonical skill row per detected job/skill pair."""
    required = {"job_id", "title", "description"}
    if missing := required - set(df.columns):
        raise ValueError(f"Cannot extract skills; missing columns: {sorted(missing)}")
    records = []
    for row in df.itertuples(index=False):
        title = normalize_text(getattr(row, "title"))
        description = normalize_text(getattr(row, "description"))
        combined = f"{title}. {description}"
        education_only = any(re.search(pattern, description, re.IGNORECASE) for pattern in EDUCATION_PATTERNS)
        for skill, aliases in SKILL_ALIASES.items():
            if skill == "Data Science" and education_only and not phrase_found(title, "data science"):
                continue
            if any(phrase_found(combined, alias) for alias in aliases):
                records.append({"job_id": getattr(row, "job_id"), "skill": skill})
    return pd.DataFrame(records, columns=["job_id", "skill"]).drop_duplicates()


def analyze_skill_demand(job_skills: pd.DataFrame) -> pd.DataFrame:
    """Count distinct jobs mentioning each detected skill."""
    if job_skills.empty:
        return pd.DataFrame(columns=["skill", "job_count"])
    return (job_skills.groupby("skill")["job_id"].nunique().reset_index(name="job_count")
            .sort_values(["job_count", "skill"], ascending=[False, True]).reset_index(drop=True))


def main() -> None:
    """Run extraction and save pipeline artifacts."""
    jobs = pd.read_csv(INPUT_FILE)
    job_skills = extract_job_skills(jobs)
    demand = analyze_skill_demand(job_skills)
    job_skills.to_csv(JOB_SKILLS_OUTPUT, index=False)
    demand.to_csv(SKILL_DEMAND_OUTPUT, index=False)
    print(f"Jobs analyzed: {len(jobs)}\nJob-skill matches: {len(job_skills)}\nSkills detected: {len(demand)}")
    print(f"Saved: {JOB_SKILLS_OUTPUT}\nSaved: {SKILL_DEMAND_OUTPUT}")


if __name__ == "__main__":
    main()
