SKILL_ALIASES = {
    "Python": ("python",), "SQL": ("sql",), "Pandas": ("pandas",), "NumPy": ("numpy",),
    "scikit-learn": ("scikit-learn", "scikit learn", "sklearn"),
    "Machine Learning": ("machine learning", "machine-learning", "ml"),
    "Artificial Intelligence": ("artificial intelligence", "ai"), "Power BI": ("power bi", "powerbi"),
    "Spark": ("spark", "apache spark"), "PySpark": ("pyspark", "py spark"),
    "C#": ("c#", "c sharp"), ".NET": (".net", "dotnet", "dot net"),
    "NLP": ("nlp", "natural language processing"),
}

SKILLS = [
    "Python",
    "SQL",
    "Pandas",
    "NumPy",
    "scikit-learn",
    "Machine Learning",
    "Deep Learning",
    "Computer Vision",
    "Data Science",
    "Data Analytics",
    "Data Engineering",
    "Artificial Intelligence",
    "Generative AI",
    "Large Language Models",
    "RAG",
    "Embeddings",
    "Vector Databases",
    "Fine-Tuning",
    "Data Preparation",
    "Data Labeling",
    "Quality Assurance",
    "OCR",
    "Power BI",
    "Tableau",
    "R",
    "Git",
    "GitLab",
    "Docker",
    "AWS",
    "Azure",
    "Spark",
    "PySpark",
    "Hive",
    "Cloud",
    "FastAPI",
    "Plotly",
    "Statistics",
    "Predictive Analytics",
    "Feature Engineering",
    "Big Data",
    "Data Governance",
    "Excel",
    "Java",
    "C#",
    ".NET"
]

# Add narrow aliases for the remaining canonical skills without expanding scope.
for _skill in SKILLS:
    SKILL_ALIASES.setdefault(_skill, (_skill.lower(),))


def canonical_skill(value: str) -> str:
    """Return the canonical name for a known skill or a clean fallback."""
    normalized = str(value).strip().casefold()
    for skill, aliases in SKILL_ALIASES.items():
        if normalized == skill.casefold() or normalized in aliases:
            return skill
    return str(value).strip()
