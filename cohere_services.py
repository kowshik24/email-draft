from cohere import ClientV2
from dotenv import load_dotenv
import os
load_dotenv()
client = ClientV2(api_key=os.getenv("COHERE_API_KEY"))


cv_text = ""
with open("/home/kowshik/personal_work/email-draft/SOP-Koshik-Debanath.txt", 'r') as file:
    cv_text = file.read()

system_prompt = """
# University Professor Finder - Instructions

You are an expert academic research advisor.  
Your job is to suggest a list of professors at a specified university whose research aligns with my CV and interests.

## Context
- My CV is attached and should be used for all analysis.
- I will provide a university name (and optionally, department or research area).

## Task
When asked, analyze my CV and the named university.  
Suggest a list of **10 professors** whom I should consider emailing for research collaboration, PhD applications, or networking.

For each professor, include:
- Full Name and Title
- Department/Lab
- 2–3 Key Research Areas
- 1–2 Recent Projects or Papers (with brief description or title)
- Why they match my background (reference specific skills/experiences from my CV)
- Link to their faculty/lab page (if available)

**Format output as a clear, numbered list or table.**

## Rules
- Use my CV and the provided university as primary context.
- Prioritize professors whose recent work closely matches my skills, interests, or publications.
- Never output generic matches; always provide specific reasons for each suggestion.
- Output only the requested professor list—don't draft emails or SOPs here.
- If department or research area is specified, narrow suggestions accordingly.
- Be concise, factual, and specific.

## Example Request
- "Suggest 10 professors at MIT for machine learning based on my CV."
- "List 10 best-fit faculty at Stanford University I could email for PhD in computer science."

---

**Always use the latest CV attachment as context. Output only the list of professors with detailed reasoning for each match.**
"""

# JSON schema for structured output
json_schema = {
  "type": "object",
  "properties": {
    "university": {
      "type": "string",
      "description": "The name of the university for professor suggestions."
    },
    "department_or_area": {
      "type": "string",
      "description": "Optional department or research area to filter professors."
    },
    "cv_used": {
      "type": "string",
      "description": "Identifier or filename of the CV used for matching."
    },
    "professor_suggestions": {
      "type": "array",
      "description": "A list of professor suggestions best matching the CV and university input.",
      "items": {
        "type": "object",
        "properties": {
          "full_name_and_title": {
            "type": "string",
            "description": "Full name and academic title of the professor."
          },
          "department_or_lab": {
            "type": "string",
            "description": "Department or lab affiliation."
          },
          "research_areas": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "2–3 key research areas."
          },
          "recent_projects_or_papers": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "title": {
                  "type": "string",
                  "description": "Title of the project or paper."
                },
                "description": {
                  "type": "string",
                  "description": "Brief description (optional)."
                }
              },
              "required": [
                "title"
              ]
            },
            "description": "1–2 recent projects or papers."
          },
          "match_reasoning": {
            "type": "string",
            "description": "Why this professor matches the CV (reference specific skills/experiences)."
          },
          "faculty_page_link": {
            "type": "string",
            "description": "URL to the professor's faculty/lab page (if available)."
          }
        },
        "required": [
          "full_name_and_title",
          "department_or_lab",
          "research_areas",
          "recent_projects_or_papers",
          "match_reasoning"
        ]
      }
    }
  },
  "required": [
    "university",
    "cv_used",
    "professor_suggestions"
  ]
}

def get_answer(query):
    response = client.chat(
        model='command-a-03-2025',
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"Here is my CV: {cv_text}\n\n{query}"
            }
        ],
        response_format={
            "type": "json_object",
            "json_schema": json_schema
        }
    )
    
    return response


if __name__ == "__main__":
    query = "The University of Texas at Arlington"
    print(get_answer(query))