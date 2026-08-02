"""
Helper functions for reading resume files (PDF / DOCX) as plain text,
and for talking to Google Gemini to analyze that text.
"""

import os
import json
import docx
from pypdf import PdfReader
import google.generativeai as genai


def extract_text_from_resume(filepath):
    """Read a .pdf or .docx file and return its plain text content."""
    ext = filepath.rsplit(".", 1)[-1].lower()

    if ext == "pdf":
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

    elif ext == "docx":
        document = docx.Document(filepath)
        return "\n".join(p.text for p in document.paragraphs)

    else:
        raise ValueError("Unsupported file type. Please upload a PDF or DOCX file.")


def analyze_resume_with_gemini(resume_text, job_description=""):
    """
    Sends the resume text (and optional job description) to Gemini and asks
    for an ATS score, missing skills, and improvement suggestions.
    Returns a dict: {ats_score, missing_skills: [...], suggestions: [...]}
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to your environment "
            "before running the analysis."
        )
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel("gemini-2.5-flash")
   
    prompt = f"""
You are an ATS (Applicant Tracking System) resume evaluator.

Resume text:
\"\"\"{resume_text}\"\"\"

Job description (may be empty if not provided):
\"\"\"{job_description}\"\"\"

Analyze the resume and respond ONLY with valid JSON in exactly this shape,
with no markdown formatting, no code fences, and no extra commentary:

{{
  "ats_score": <integer 0-100>,
  "missing_skills": ["skill1", "skill2"],
  "suggestions": ["suggestion1", "suggestion2", "suggestion3"]
}}
"""

    response = model.generate_content(prompt)
    raw_text = response.text.strip()

    # Gemini sometimes wraps JSON in ```json ... ``` even when told not to
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        # Fallback so the app doesn't crash if Gemini returns bad formatting
        result = {
            "ats_score": 0,
            "missing_skills": [],
            "suggestions": ["Could not parse AI response. Please try again."],
        }

    return result
