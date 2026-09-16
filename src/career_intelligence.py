"""Explainable career analytics built from an extracted resume profile and job data."""
from __future__ import annotations
from collections import Counter
from dataclasses import asdict
import re
import pandas as pd

from job_matching import calculate_domain_relevance, calculate_final_score, calculate_recommendation, calculate_role_relevance, calculate_skill_match
from resume_parser import ResumeProfile


def profile_strength(profile: ResumeProfile) -> dict[str, int]:
    """Return evidence-based profile-strength components and an overall score."""
    components = {
        "Technical skills": min(100, len(profile.skills) * 8),
        "Experience": 75 if profile.experience else 0,
        "Projects": 85 if profile.projects else 0,
        "Education": 90 if profile.education else 0,
        "Resume completeness": round(100 * sum(profile.completeness.values()) / len(profile.completeness)),
        "Language information": 100 if profile.languages else 0,
    }
    components["Overall profile strength"] = round(sum(components.values()) / len(components))
    return components


def _language_signal(description: str) -> tuple[bool, str]:
    text = str(description).casefold()
    levels = re.search(r"\b(?:german|deutsch)[^.!]{0,60}\b(?:a[12]|b[12]|c[12])\b", text)
    if levels:
        return True, levels.group(0)
    return (True, "German mentioned") if re.search(r"\b(?:german|deutschkenntnisse)\b", text) else (False, "Not specified")


def match_jobs(profile: ResumeProfile, jobs: pd.DataFrame, job_skills: pd.DataFrame) -> pd.DataFrame:
    """Score jobs with skill, role, domain, optional location, and optional language signals."""
    student_skills = {skill.casefold() for skill in profile.skills}
    rows = []
    for job_id, group in job_skills.groupby("job_id"):
        found = jobs.loc[jobs["job_id"].astype(str) == str(job_id)]
        if found.empty:
            continue
        job, skills = found.iloc[0], group["skill"].tolist()
        skill_score = calculate_skill_match(skills, student_skills)
        target = profile.target_roles[0] if profile.target_roles else "Data Scientist"
        role_score = calculate_role_relevance(job["title"], target)
        domain_score = calculate_domain_relevance(job["title"], skills)
        base = calculate_final_score(skill_score, role_score, domain_score)
        location_score = 100 if profile.locations and str(job.get("location", "")).casefold() in {x.casefold() for x in profile.locations} else 50
        required_german, german_note = _language_signal(job.get("description", ""))
        speaks_german = "German" in profile.languages
        language_score = 100 if not required_german or speaks_german else 50
        # Unknown location/language requirements are neutral, not a penalty.
        final = round(base * .90 + location_score * .05 + language_score * .05, 2)
        required = {str(s).casefold() for s in skills}
        matched = sorted(str(s) for s in profile.skills if s.casefold() in required)
        missing = sorted(str(s) for s in skills if str(s).casefold() not in student_skills)
        row = {"job_id": job_id, "title": job.get("title", ""), "company": job.get("company", ""), "location": job.get("location", ""), "state": job.get("state", ""), "job_type": job.get("job_type", ""), "salary": job.get("salary", ""), "source": job.get("source", ""), "source_url": job.get("source_url", ""), "match_score": final, "recommendation": calculate_recommendation(final), "skill_match": skill_score, "role_relevance": role_score, "domain_relevance": domain_score, "location_relevance": location_score, "language_relevance": language_score, "matched_skills": "; ".join(matched), "missing_skills": "; ".join(missing), "german_requirement": german_note}
        rows.append(row)
    return pd.DataFrame(rows).sort_values("match_score", ascending=False).reset_index(drop=True) if rows else pd.DataFrame()


def skill_gaps(matches: pd.DataFrame, profile: ResumeProfile, skill_demand: pd.DataFrame) -> pd.DataFrame:
    """Prioritize absent-from-resume skills by relevant-match frequency and market demand."""
    relevant = matches[matches["match_score"] >= 60] if not matches.empty else matches
    missing = [item.strip() for value in relevant.get("missing_skills", pd.Series(dtype=str)).dropna() for item in str(value).split(";") if item.strip()]
    counts = Counter(missing)
    demand = skill_demand.set_index("skill")["job_count"].to_dict() if not skill_demand.empty else {}
    max_count, max_demand = max(counts.values(), default=1), max(demand.values(), default=1)
    result = []
    for skill, relevant_count in counts.items():
        score = 100 * (.65 * relevant_count / max_count + .35 * demand.get(skill, 0) / max_demand)
        priority = "High" if score >= 70 else "Medium" if score >= 40 else "Low"
        result.append({"skill": skill, "resume_status": "Not detected in your resume", "relevant_jobs": relevant_count, "market_demand": demand.get(skill, 0), "priority": priority, "priority_score": round(score)})
    return pd.DataFrame(result).sort_values(["priority_score", "market_demand"], ascending=False).reset_index(drop=True) if result else pd.DataFrame()


def action_plan(gaps: pd.DataFrame) -> list[dict[str, str]]:
    """Create bounded, evidence-based next actions rather than employment guarantees."""
    return [{"skill": row.skill, "priority": row.priority, "why": f"{row.skill} was not detected in your resume and appears in {int(row.relevant_jobs)} relevant analyzed opportunities."} for row in gaps.head(3).itertuples()]
