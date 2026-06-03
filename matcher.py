# matcher.py

import re


def clean_text(text):
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"[^a-z0-9+#.\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def match_skills(job_description, skills):
    cleaned_description = clean_text(job_description)

    matched = []
    missing = []

    for skill in skills:
        cleaned_skill = clean_text(skill)

        if cleaned_skill in cleaned_description:
            matched.append(skill)
        else:
            missing.append(skill)

    return matched, missing


def calculate_match_score(matched_skills, total_skills):
    if total_skills == 0:
        return 0

    score = len(matched_skills) / total_skills * 100
    return round(score, 1)


def analyze_job(job_description, skills):
    matched, missing = match_skills(job_description, skills)
    score = calculate_match_score(matched, len(skills))

    return {
        "match_score": score,
        "matched_skills": matched,
        "missing_skills": missing,
    }