# Germany Student Career Intelligence Platform

An explainable, resume-first career intelligence platform for students targeting German Werkstudent roles in Data Science, Analytics, AI, Machine Learning, and Software Engineering.

## Problem and solution

Students need a practical view of employer demand, opportunity locations, their best-fit roles, and the skills worth learning next. Upload a resume to build a local career profile, discover evidence-based matches, see skills detected in the resume, and understand which market-relevant skills were not detected.

## Resume-first workflow

```text
PDF/DOCX resume -> local text extraction -> section and skill detection -> career profile
                                                             |
Job data -> standardization -> skill extraction -> matching -> skill gaps -> action plan
```

PDF and DOCX resumes up to 5 MB are supported. The application processes bytes in memory for the current browser session: it does not save uploaded resumes, log their contents, or send them to external APIs. A missing skill is always described as **not detected in your resume**, never as proof that the student lacks it.

## Key features

- Job Explorer with keyword, location, state, job-type, and match-score filters
- Job market analytics for locations, companies, job types, and home-office flags where supplied
- Canonical skill-demand analysis and skill-gap prioritization
- Personalized, explainable matching and recommendation labels
- Reusable CSV student profile; no profile values are hardcoded into the dashboard
- Resume upload, validation, local PDF/DOCX parsing, structured evidence extraction, and skill categorization
- Explainable profile strength, personalized resume-first matching, skill priorities, and beginner-friendly action plan
- Safe HTML tables instead of `st.dataframe` / `st.table`, avoiding the local PyArrow DLL policy issue

## Architecture

```text
Job Data -> Data Cleaning -> Standardization -> Skill Extraction -> Skill Demand
                                                      |
Student Profile -> Job Matching -> Recommendations -> Streamlit Dashboard
```

## Current dataset and results

The included snapshot is collected from the Bundesagentur fur Arbeit API and contains 89 standardized postings. The current pipeline identifies 37 distinct canonical skills and produces 79 matches for postings with detected skills. It is a market snapshot, not a complete index of all German vacancies. BA records in this snapshot do not include reliable direct job URLs, so the dashboard displays source metadata but never invents apply links.

## Matching methodology

The score is intentionally simple and explainable:

- Skill Match (50%): overlap of profile skills with detected specific technical skills. Broad terms such as Data Science and Cloud are excluded from this percentage; a job with only broad terms receives a conservative 25.
- Role Relevance (40%): title alignment with the selected target role.
- Domain Relevance (10%): title and technical signals for Data/AI/ML.

The saved baseline pipeline uses:

`final_score = 0.50 * skill_match + 0.40 * role_relevance + 0.10 * domain_relevance`

The resume-first dashboard applies those explainable signals at 90% of the final score and adds neutral-or-evidence-based location and language relevance at 5% each. Missing location or job-language information is neutral rather than punitive.

Scores map to Excellent (90–100), Strong (80–89), Good (70–79), Possible (60–69), and Low Match.

## Technologies

Python, Pandas, Requests, Streamlit, pypdf, python-docx, and Git/GitHub.

## Installation (Windows)

```powershell
git clone https://github.com/yashbedekar07/germany-student-job-intelligence.git
cd germany-student-job-intelligence
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run the pipeline and dashboard

```powershell
python src\standardize_jobs.py
python src\skill_analysis.py
python src\job_matching.py
streamlit run dashboard\app.py
```

## Testing

```powershell
python -m pytest -q
```

The test suite covers DOCX extraction, validation and malformed-file handling, profile skill extraction, matching, and the “not detected in your resume” skill-gap language. Streamlit page states are additionally checked with `streamlit.testing.v1.AppTest`.

## Project structure

```text
data/              raw input, processed pipeline artifacts, student profile
src/               collection, cleaning, standardization, extraction, matching, quality checks
dashboard/app.py   Streamlit portfolio dashboard
```

## Future improvements (V2)

- CV upload and parsing
- Semantic matching with embeddings and RAG
- AI career advisor and personalized learning roadmap
- Job alerts, application tracking, and refreshed source data
