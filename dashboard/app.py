"""Local-first Germany Student Career Intelligence Platform."""
from pathlib import Path
from html import escape
import sys
import re
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from resume_parser import ResumeParseError, build_profile, extract_text
from career_intelligence import action_plan, match_jobs, profile_strength, skill_gaps

st.set_page_config(page_title="Germany Student Career Intelligence", page_icon=":material/work:", layout="wide")


@st.cache_data(ttl=3600)
def load_market_data():
    base = ROOT / "data"
    return (pd.read_csv(base / "processed" / "jobs_standardized.csv"), pd.read_csv(base / "processed" / "job_skills.csv"), pd.read_csv(base / "processed" / "skill_demand.csv"))


def safe_table(frame, columns, limit=30):
    """PyArrow-free data display for Windows Application Control environments."""
    if frame.empty:
        st.caption("No data is available for this selection.")
        return
    head = "".join(f"<th>{escape(label)}</th>" for key, label in columns)
    rows = []
    for _, row in frame.head(limit).iterrows():
        cells = []
        for key, _ in columns:
            value = "Not available" if pd.isna(row.get(key)) or str(row.get(key)).strip() in {"", "nan"} else str(row.get(key))
            cells.append(f"<td>{escape(value)}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    st.markdown(f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>", unsafe_allow_html=True)


def initialise_state():
    for key, value in {"resume_profile": None, "resume_matches": pd.DataFrame(), "resume_gaps": pd.DataFrame(), "resume_name": ""}.items():
        st.session_state.setdefault(key, value)


def profile_or_none():
    return st.session_state.resume_profile


def render_upload(jobs, job_skills, skills):
    st.title("Understand your career opportunities")
    st.write("Upload your resume to discover suitable German student opportunities, skills detected in your resume, and practical next steps.")
    with st.container(border=True):
        upload = st.file_uploader("Upload your resume", type=["pdf", "docx"], help="PDF or DOCX, maximum 5 MB. Your file is processed locally in memory and is not saved.")
        st.caption("Supported formats: PDF and DOCX · Maximum size: 5 MB · Resume content is not stored or sent to external services.")
        if upload:
            st.success("Resume uploaded successfully", icon=":material/check_circle:")
            if st.button("Analyze my resume", type="primary", icon=":material/manage_search:"):
                try:
                    with st.status("Analyzing your resume", expanded=True) as status:
                        st.write(":material/check: Reading resume")
                        resume_text = extract_text(upload.name, upload.getvalue())
                        st.write(":material/check: Detecting education, experience, and projects")
                        profile = build_profile(resume_text)
                        st.write(":material/check: Detecting and normalizing skills")
                        st.write(":material/check: Comparing with the job market")
                        st.session_state.resume_profile = profile
                        st.session_state.resume_matches = match_jobs(profile, jobs, job_skills)
                        st.session_state.resume_gaps = skill_gaps(st.session_state.resume_matches, profile, skills)
                        st.session_state.resume_name = upload.name
                        status.update(label="Career profile ready", state="complete", expanded=False)
                    st.toast("Your career profile is ready.", icon=":material/check_circle:")
                except ResumeParseError as error:
                    st.error(str(error), icon=":material/error:")
    if profile_or_none() is None:
        st.info("Start with a resume upload. We will only show information detected from your document; missing information is labelled clearly.", icon=":material/info:")
    else:
        st.success("A resume has been analyzed in this browser session. Open My career profile to explore it.", icon=":material/check_circle:")


def require_profile():
    if profile_or_none() is None:
        st.warning("Upload and analyze a resume on Home to unlock personalized results.", icon=":material/upload_file:")
        return False
    return True


def render_profile():
    st.title("My career profile")
    if not require_profile(): return
    profile, matches, gaps = profile_or_none(), st.session_state.resume_matches, st.session_state.resume_gaps
    strength = profile_strength(profile)
    cols = st.columns(4)
    cols[0].metric("Profile strength", f"{strength['Overall profile strength']} / 100", help="An explainable evidence score, not a hiring prediction.")
    cols[1].metric("Suitable opportunities", int((matches.match_score >= 60).sum()) if not matches.empty else 0)
    cols[2].metric("Skills detected", len(profile.skills))
    cols[3].metric("Potential skill gaps", len(gaps))
    st.caption("Profile strength combines technical skills, education, projects, experience, resume completeness, and language information detected in your resume.")
    with st.container(border=True):
        st.subheader("Profile strength breakdown")
        safe_table(pd.DataFrame([{"area": k, "score": v} for k, v in strength.items() if k != "Overall profile strength"]), [("area", "Area"), ("score", "Evidence score")])
    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.subheader("Detected skills")
            if profile.skill_categories:
                for category, values in profile.skill_categories.items(): st.write(f"**{category}:** {', '.join(values)}")
            else: st.caption("No dictionary skills were detected in the resume.")
    with right:
        with st.container(border=True):
            st.subheader("Resume evidence")
            st.write(f"**Education:** {'Detected' if profile.education else 'Not detected from resume'}")
            st.write(f"**Experience:** {'Detected' if profile.experience else 'Not detected from resume'}")
            st.write(f"**Projects:** {'Detected' if profile.projects else 'Not detected from resume'}")
            st.write(f"**Languages:** {', '.join(profile.languages) if profile.languages else 'Not detected from resume'}")
            st.write(f"**Location:** {', '.join(profile.locations) if profile.locations else 'Not detected from resume'}")


def render_explorer(jobs, job_skills):
    st.title("Job explorer")
    personal = st.session_state.resume_matches
    data = jobs.merge(personal[["job_id", "match_score", "recommendation", "matched_skills", "missing_skills", "german_requirement"]], on="job_id", how="left") if not personal.empty else jobs.copy()
    if "match_score" not in data:
        data["match_score"] = pd.NA
        data["recommendation"] = ""
        data["matched_skills"] = ""
        data["missing_skills"] = ""
        data["german_requirement"] = "Not detected from current job data"
    with st.form("job_filters"):
        query = st.text_input("Search jobs", placeholder="Python, Data Analyst, Berlin …")
        c1, c2, c3 = st.columns(3)
        city = c1.multiselect("City", sorted(data.location.dropna().astype(str).unique()))
        state = c2.multiselect("State", sorted(data.state.dropna().astype(str).unique()))
        kind = c3.multiselect("Job type", sorted(data.job_type.dropna().astype(str).unique()))
        submitted = st.form_submit_button("Apply filters", icon=":material/filter_list:")
    filtered = data.copy()
    if query: filtered = filtered[filtered.astype(str).apply(lambda x: x.str.contains(re.escape(query), case=False, na=False).any(), axis=1)]
    for column, choices in (("location", city), ("state", state), ("job_type", kind)):
        if choices: filtered = filtered[filtered[column].astype(str).isin(choices)]
    st.caption(f"Showing {len(filtered)} of {len(jobs)} collected opportunities.")
    for _, job in filtered.sort_values("match_score", ascending=False, na_position="last").head(30).iterrows():
        with st.container(border=True):
            st.subheader(str(job.title))
            st.write(f"**{job.company}** · :material/location_on: {job.location}, {job.state} · :material/business_center: {job.job_type}")
            if not pd.isna(job.get("match_score")): st.badge(f"{job.match_score:.0f}% {job.recommendation}", color="green" if job.match_score >= 80 else "orange")
            if "matched_skills" in job and str(job.get("matched_skills", "")).strip(): st.caption(f"Skills detected in resume: {job.matched_skills}")
            with st.expander("Opportunity details", icon=":material/visibility:"):
                st.write(str(job.description)[:2000])
                st.caption(f"German requirement: {job.get('german_requirement', 'Not available in current dataset')} · Salary: {job.get('salary', 'Not available')}")
                url = str(job.get("source_url", ""))
                if url.startswith(("http://", "https://")): st.link_button("View opportunity", url, icon=":material/open_in_new:")
                else: st.caption("No direct source URL is available for this posting.")


def render_matches():
    st.title("My matches")
    if not require_profile(): return
    matches = st.session_state.resume_matches
    threshold = st.slider("Minimum match score", 0, 100, 60)
    shown = matches[matches.match_score >= threshold]
    st.caption("Scores combine skill match (45%), role relevance (36%), domain relevance (9%), and neutral-or-evidence-based location and language relevance (5% each).")
    for _, job in shown.head(25).iterrows():
        with st.container(border=True):
            st.subheader(f"{job.match_score:.0f}% {job.recommendation} — {job.title}")
            st.write(f"**{job.company}** · {job.location}")
            st.write(f"**Why this matches:** Skills detected: {job.matched_skills or 'No listed skills detected'}. Role relevance: {job.role_relevance:.0f}/100. Domain relevance: {job.domain_relevance:.0f}/100.")
            st.write(f"**What may be missing:** {job.missing_skills or 'No detected skill gaps for this job.'} These skills were not detected in your resume; this does not mean you do not have them.")


def render_gaps(skills):
    st.title("Skill gap and action plan")
    if not require_profile(): return
    gaps = st.session_state.resume_gaps
    if gaps.empty:
        st.info("No skill gaps were identified from the detected job skills.", icon=":material/info:"); return
    st.write("These skills were **not detected in your resume** and are prioritized by demand across your relevant opportunities and the wider collected market. This is not a claim about what you know.")
    safe_table(gaps, [("skill", "Skill"), ("resume_status", "Resume"), ("relevant_jobs", "Relevant jobs"), ("market_demand", "Market demand"), ("priority", "Priority")])
    st.subheader("What should I do next?")
    for item in action_plan(gaps):
        with st.container(border=True):
            st.write(f":{'red' if item['priority']=='High' else 'orange'}-badge[{item['priority']} priority] **Improve {item['skill']}**")
            st.caption(item["why"])


def render_market(jobs, skills):
    st.title("Market insights")
    a, b, c = st.columns(3); a.metric("Jobs analyzed", len(jobs)); b.metric("Skills tracked", len(skills)); c.metric("Top skill", skills.iloc[0].skill if not skills.empty else "Not available")
    st.subheader("Most demanded skills")
    st.bar_chart(skills.head(15).set_index("skill")["job_count"])
    left, right = st.columns(2)
    with left:
        st.subheader("Top companies")
        safe_table(jobs.company.value_counts().rename_axis("company").reset_index(name="jobs"), [("company", "Company"), ("jobs", "Jobs")], 12)
    with right:
        st.subheader("Top cities")
        safe_table(jobs.location.value_counts().rename_axis("location").reset_index(name="jobs"), [("location", "City"), ("jobs", "Jobs")], 12)
    st.caption("German-language requirements and salary are not presented as market metrics because the current source lacks reliable structured fields. They are shown only when evidence is available in a job record.")


initialise_state()
jobs, job_skills, skills = load_market_data()
with st.sidebar:
    st.title("Career intelligence")
    page = st.radio("Navigation", ["Home", "My career profile", "Job explorer", "My matches", "Skill gap", "Market insights"], label_visibility="collapsed")
    st.caption("Resume data stays in this browser session. It is processed locally and not saved by this application.")

if page == "Home": render_upload(jobs, job_skills, skills)
elif page == "My career profile": render_profile()
elif page == "Job explorer": render_explorer(jobs, job_skills)
elif page == "My matches": render_matches()
elif page == "Skill gap": render_gaps(skills)
else: render_market(jobs, skills)
