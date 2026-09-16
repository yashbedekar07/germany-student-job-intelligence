import pandas as pd


JOBS_FILE = "data/processed/jobs_standardized.csv"
JOB_SKILLS_FILE = "data/processed/job_skills.csv"
PROFILE_FILE = "data/student_profile.csv"
OUTPUT_FILE = "data/processed/job_matches.csv"


def load_student_profile():
    """Load the student profile."""

    profile = pd.read_csv(PROFILE_FILE).iloc[0]

    skills = {
        skill.strip().lower()
        for skill in str(profile["skills"]).split(";")
        if skill.strip()
    }

    return profile, skills


def calculate_match(job_id, job_skills, student_skills):
    """Calculate a more realistic skill match percentage."""

    general_skills = {
        "data science",
        "data analytics",
        "artificial intelligence",
        "cloud",
        "big data"
    }

    required_skills = {
        skill.lower()
        for skill in job_skills
    }

    if not required_skills:
        return 0.0

    specific_skills = required_skills - general_skills

    # If the job only contains general skills,
    # do not allow a misleading 100% match.
    if not specific_skills:
        return 25.0

    matched_skills = specific_skills.intersection(student_skills)

    return round(
        len(matched_skills) / len(specific_skills) * 100,
        2
    )


def main():
    """Create job matching results."""

    jobs = pd.read_csv(JOBS_FILE)
    job_skills = pd.read_csv(JOB_SKILLS_FILE)

    _, student_skills = load_student_profile()

    results = []

    for job_id, group in job_skills.groupby("job_id"):

        skills = group["skill"].tolist()

        required_skills = {
            skill.lower()
            for skill in skills
        }

        matched = required_skills.intersection(student_skills)
        missing = required_skills - student_skills

        match_score = calculate_match(
            job_id,
            skills,
            student_skills
        )

        results.append({
            "job_id": job_id,
            "match_score": match_score,
            "matched_skills": "; ".join(sorted(matched)),
            "missing_skills": "; ".join(sorted(missing))
        })

    matches = pd.DataFrame(results)

    matches = matches.merge(
        jobs[
            [
                "job_id",
                "title",
                "company",
                "location",
                "state"
            ]
        ],
        on="job_id",
        how="left"
    )

    matches = matches[
        [
            "job_id",
            "title",
            "company",
            "location",
            "state",
            "match_score",
            "matched_skills",
            "missing_skills"
        ]
    ]

    matches = matches.sort_values(
        by="match_score",
        ascending=False
    ).reset_index(drop=True)

    matches.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("Student Job Matching")
    print("--------------------")
    print(f"Jobs matched: {len(matches)}")
    print()
    print(matches.head(10).to_string(index=False))
    print()
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()