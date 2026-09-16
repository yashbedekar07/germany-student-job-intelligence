"""Explainable student-to-job matching for the processed pipeline."""
from pathlib import Path
import re
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill_dictionary import canonical_skill  # noqa: E402

JOBS_FILE = ROOT / "data" / "processed" / "jobs_standardized.csv"
JOB_SKILLS_FILE = ROOT / "data" / "processed" / "job_skills.csv"
PROFILE_FILE = ROOT / "data" / "student_profile.csv"
OUTPUT_FILE = ROOT / "data" / "processed" / "job_matches.csv"
GENERAL_SKILLS = {"data science", "data analytics", "artificial intelligence", "cloud", "big data"}


def _normalise_skills(values) -> set[str]:
    return {canonical_skill(value).casefold() for value in values if str(value).strip() and str(value).lower() != "nan"}


def load_student_profile(path: Path = PROFILE_FILE):
    """Load the first reusable profile row and normalized skills."""
    profile = pd.read_csv(path).iloc[0]
    return profile, _normalise_skills(str(profile.get("skills", "")).split(";"))


def calculate_skill_match(job_skills, student_skills) -> float:
    """Percentage of specific detected skills owned by the student (general terms excluded)."""
    required = _normalise_skills(job_skills)
    specific = required - GENERAL_SKILLS
    if not required:
        return 0.0
    if not specific:
        return 25.0  # Prevent an undetected generic job from looking like a perfect fit.
    return round(100 * len(specific & student_skills) / len(specific), 2)


def calculate_role_relevance(title, target_role) -> float:
    """Use conservative, explainable title signals for Data/AI career relevance."""
    title = str(title).casefold()
    target = str(target_role).casefold()
    if target not in {"data scientist", "data science"}:
        return 50.0
    signals = ((100, ("data scientist",)), (95, ("data science",)),
               (92, ("machine learning", "ai engineer", "artificial intelligence", "generative ai", "\bai\b", "\bki\b")),
               (85, ("data analyst", "data analytics", "analytics engineer", "analytics")),
               (75, ("data engineer", "data engineering", "business intelligence", "power bi")))
    for score, terms in signals:
        if any(re.search(term, title) if term.startswith("\\b") else term in title for term in terms):
            return float(score)
    return 50.0


def calculate_domain_relevance(title, job_skills) -> float:
    """Score technical data/AI signals without letting duplicate title terms inflate results."""
    title = str(title).casefold()
    title_score = 40 if any(term in title for term in ("data scientist", "machine learning", "artificial intelligence", "data engineer")) else 0
    if not title_score and any(term in title for term in ("data analyst", "analytics", "\bai\b", "\bki\b")):
        title_score = 30
    skills = _normalise_skills(job_skills)
    strong = {"machine learning", "deep learning", "artificial intelligence", "generative ai", "large language models", "rag", "embeddings", "scikit-learn", "data engineering"}
    medium = {"python", "pandas", "numpy", "statistics", "power bi", "tableau", "sql", "pyspark", "spark"}
    return round(min(100, title_score + 10 * len(skills & strong) + 4 * len(skills & medium)), 2)


def calculate_final_score(skill_match, role_relevance, domain_relevance) -> float:
    """Weighted score: skill match 50%, role relevance 40%, domain relevance 10%."""
    return round(skill_match * 0.50 + role_relevance * 0.40 + domain_relevance * 0.10, 2)


def calculate_recommendation(score) -> str:
    for threshold, label in ((90, "Excellent Match"), (80, "Strong Match"), (70, "Good Match"), (60, "Possible Match")):
        if score >= threshold:
            return label
    return "Low Match"


def generate_match_reason(skill_match, role_relevance, domain_relevance, matched_skills, missing_skills) -> str:
    """Generate a short, grammatical and evidence-based match explanation."""
    parts = ["You match most of the required technical skills." if skill_match >= 90 else
             "You have a strong portion of the required technical skills." if skill_match >= 70 else
             "You have several relevant technical skills, but there are gaps." if skill_match >= 50 else
             "Your current technical skill overlap is limited."]
    parts.append("The job title is directly aligned with Data Science." if role_relevance >= 95 else
                 "The job title is strongly related to AI or Machine Learning." if role_relevance >= 90 else
                 "The job title is strongly related to Data Analytics." if role_relevance >= 80 else
                 "The job has some Data Engineering or Business Intelligence relevance." if role_relevance >= 70 else
                 "The job title is not directly aligned with your target role.")
    if domain_relevance >= 60:
        parts.append("The job has a strong Data/AI/ML technical focus.")
    elif domain_relevance >= 40:
        parts.append("The job contains some Data/AI/ML elements.")
    if matched_skills:
        parts.append(f"Matched skills: {matched_skills}.")
    if missing_skills:
        parts.append(f"Skills to improve: {missing_skills}.")
    return " ".join(parts)


def main() -> None:
    """Create and save personalized match results, including useful job metadata."""
    jobs, job_skills = pd.read_csv(JOBS_FILE), pd.read_csv(JOB_SKILLS_FILE)
    profile, student_skills = load_student_profile()
    results = []
    for job_id, group in job_skills.groupby("job_id"):
        job_row = jobs.loc[jobs["job_id"].astype(str) == str(job_id)]
        if job_row.empty:
            continue
        job, skills = job_row.iloc[0], group["skill"].tolist()
        required = _normalise_skills(skills)
        matched, missing = required & student_skills, required - student_skills
        skill_score = calculate_skill_match(skills, student_skills)
        role_score = calculate_role_relevance(job["title"], profile.get("target_role", ""))
        domain_score = calculate_domain_relevance(job["title"], skills)
        score = calculate_final_score(skill_score, role_score, domain_score)
        matched_text = "; ".join(sorted(canonical_skill(s) for s in matched))
        missing_text = "; ".join(sorted(canonical_skill(s) for s in missing))
        record = {"job_id": job_id, "skill_match": skill_score, "role_relevance": role_score,
                  "domain_relevance": domain_score, "match_score": score,
                  "recommendation": calculate_recommendation(score), "matched_skills": matched_text,
                  "missing_skills": missing_text,
                  "match_reason": generate_match_reason(skill_score, role_score, domain_score, matched_text, missing_text)}
        for column in ("title", "company", "location", "state", "job_type", "posted_date", "salary", "source", "source_url"):
            if column in jobs.columns:
                record[column] = job[column]
        results.append(record)
    matches = pd.DataFrame(results).sort_values("match_score", ascending=False).reset_index(drop=True) if results else pd.DataFrame()
    matches.to_csv(OUTPUT_FILE, index=False)
    print(f"Target role: {profile.get('target_role', '')}\nJobs matched: {len(matches)}\nSaved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
