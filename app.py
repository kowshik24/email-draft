import streamlit as st
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz
import re
import json

# Load environment variables from .env file
load_dotenv()

# Placeholder for actual API clients
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
    st.warning("OpenAI library not found. Please install it: pip install openai")

try:
    import google.generativeai as genai
except ImportError:
    genai = None
    st.warning("Google Generative AI library not found. Please install it: pip install google-generativeai")

try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None
    st.warning("Tavily library not found. Please install it: pip install tavily-python")

try:
    from pydantic import BaseModel, Field
    from typing import List, Optional
except ImportError:
    BaseModel = None
    Field = None
    List = None
    Optional = None
    st.warning("Pydantic library not found. Please install it: pip install pydantic")

# --- LLM API Call Functions ---
def get_openai_response(api_key, prompt_text, model="gpt-4o-mini"): # Model is now passed as arg
    if not OpenAI:
        st.error("OpenAI library is not available.")
        return "OpenAI library error."
    try:
        client = OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.01
        )
        return completion.choices[0].message.content
    except Exception as e:
        st.error(f"OpenAI API Error: {e}")
        return f"Error: {e}"

def get_gemini_response(api_key, prompt_text, model_name="gemini-1.5-flash-latest"): # Model is now passed as arg
    if not genai:
        st.error("Google Generative AI library is not available.")
        return "Google Generative AI library error."
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name) # Use the model_name argument
        response = model.generate_content(prompt_text)
        return response.text
    except Exception as e:
        st.error(f"Gemini API Error: {e}")
        return f"Error: {e}"

def extract_research_areas_from_cv(cv_text):
    """
    Extract research areas and potential departments from CV text.
    """
    research_keywords = {
        'computer_science': ['computer science', 'CS', 'computing', 'software engineering', 'programming'],
        'artificial_intelligence': ['artificial intelligence', 'AI', 'machine learning', 'ML', 'deep learning', 'neural networks'],
        'data_science': ['data science', 'data analytics', 'big data', 'statistics', 'analytics'],
        'cybersecurity': ['cybersecurity', 'security', 'cyber', 'information security', 'network security'],
        'robotics': ['robotics', 'robots', 'automation', 'control systems'],
        'bioinformatics': ['bioinformatics', 'computational biology', 'genomics', 'bio'],
        'electrical_engineering': ['electrical engineering', 'EE', 'electronics', 'circuits'],
        'mechanical_engineering': ['mechanical engineering', 'ME', 'mechanics', 'dynamics'],
        'civil_engineering': ['civil engineering', 'CE', 'structures', 'construction'],
        'mathematics': ['mathematics', 'math', 'applied mathematics', 'statistics'],
        'physics': ['physics', 'applied physics', 'theoretical physics'],
        'chemistry': ['chemistry', 'chemical', 'biochemistry'],
        'biology': ['biology', 'biological', 'biotechnology']
    }
    
    cv_lower = cv_text.lower()
    found_areas = []
    
    for area, keywords in research_keywords.items():
        for keyword in keywords:
            if keyword in cv_lower:
                found_areas.append(area)
                break
    
    return found_areas

def search_professors_with_tavily(university_name, cv_text, tavily_api_key, tavily_params):
    """
    Use Tavily to search for faculty information at a university, then process with LLM.
    This ensures we get up-to-date information rather than relying on LLM training data.
    """
    if not TavilyClient:
        return "Error: Tavily library not available"
    
    try:
        client = TavilyClient(api_key=tavily_api_key)
        
        # Extract research areas from CV to create targeted searches
        research_areas = extract_research_areas_from_cv(cv_text)
        
        # Base faculty search queries
        base_queries = [
            f"{university_name} faculty directory computer science",
            f"{university_name} faculty list computer science department",
            f"{university_name} computer science professors",
            f"{university_name} faculty profiles computer science",
            f"{university_name} department of computer science faculty",
            f"{university_name} computer science faculty research",
            f"{university_name} CS faculty directory",
            f"{university_name} computer science department faculty",
            f"{university_name} faculty computer science research areas",
            f"{university_name} computer science professors research interests"
        ]
        
        # Add research area specific queries
        area_specific_queries = []
        for area in research_areas:
            if area == 'artificial_intelligence':
                area_specific_queries.extend([
                    f"{university_name} AI faculty machine learning",
                    f"{university_name} artificial intelligence professors",
                    f"{university_name} machine learning faculty"
                ])
            elif area == 'data_science':
                area_specific_queries.extend([
                    f"{university_name} data science faculty",
                    f"{university_name} analytics professors",
                    f"{university_name} big data faculty"
                ])
            elif area == 'cybersecurity':
                area_specific_queries.extend([
                    f"{university_name} cybersecurity faculty",
                    f"{university_name} security professors",
                    f"{university_name} information security faculty"
                ])
            elif area == 'robotics':
                area_specific_queries.extend([
                    f"{university_name} robotics faculty",
                    f"{university_name} automation professors",
                    f"{university_name} control systems faculty"
                ])
        
        # Combine all queries
        faculty_search_queries = base_queries + area_specific_queries
        
        all_search_results = []
        
        for query in faculty_search_queries:
            try:
                response = client.search(
                    query=query,
                    search_depth=tavily_params.get("search_depth", "advanced"),
                    max_results=tavily_params.get("max_results", 5),
                    include_raw_content=tavily_params.get("include_raw_content", True),
                    include_answer=tavily_params.get("include_answer", True),
                    time_range=tavily_params.get("time_range", None),
                    include_domains=tavily_params.get("include_domains", None),
                    exclude_domains=tavily_params.get("exclude_domains", None),
                    country=tavily_params.get("country", None)
                )
                
                if response.get('results'):
                    all_search_results.extend(response['results'])
                    
            except Exception as e:
                st.warning(f"Tavily search failed for query '{query}': {e}")
                continue
        
        if not all_search_results:
            return "Error: No faculty information found via Tavily search"
        
        # Extract content from the most relevant results
        extracted_content = []
        # Use more results for better coverage
        for result in all_search_results[:5]:  # Use top 5 results
            try:
                if result.get('url'):
                    # Try to extract content from the URL
                    extract_response = client.extract(
                        urls=[result['url']],
                        extract_depth=tavily_params.get("extract_depth", "advanced"),
                        format="text"
                    )
                    if extract_response.get('content'):
                        extracted_content.append(f"Source: {result['url']}\nContent: {extract_response['content']}")
                    else:
                        # If extraction fails, use the search result content if available
                        if result.get('content'):
                            extracted_content.append(f"Source: {result['url']}\nContent: {result['content']}")
                        elif result.get('raw_content'):
                            extracted_content.append(f"Source: {result['url']}\nContent: {result['raw_content']}")
            except Exception as e:
                st.warning(f"Content extraction failed for {result.get('url', 'unknown URL')}: {e}")
                # Try to use search result content as fallback
                if result.get('content'):
                    extracted_content.append(f"Source: {result.get('url', 'Unknown')}\nContent: {result['content']}")
                elif result.get('raw_content'):
                    extracted_content.append(f"Source: {result.get('url', 'Unknown')}\nContent: {result['raw_content']}")
                continue
        
        if not extracted_content:
            # If no content could be extracted, try to use search result snippets
            fallback_content = []
            for result in all_search_results[:5]:
                if result.get('content'):
                    fallback_content.append(f"Source: {result.get('url', 'Unknown')}\nContent: {result['content']}")
                elif result.get('snippet'):
                    fallback_content.append(f"Source: {result.get('url', 'Unknown')}\nContent: {result['snippet']}")
            
            if fallback_content:
                extracted_content = fallback_content
            else:
                return "Error: Could not extract content from search results"
        
        # Combine all extracted content
        combined_content = "\n\n---\n\n".join(extracted_content)
        
        return {
            "search_results": all_search_results,
            "extracted_content": combined_content,
            "source_urls": [result.get('url', '') for result in all_search_results if result.get('url')]
        }
        
    except Exception as e:
        return f"Error in Tavily search: {e}"

def enhance_professor_info(professors, university_name, tavily_api_key):
    """
    Post-process professor information to add missing links and details.
    """
    if not professors:
        return professors
    
    enhanced_professors = []
    
    for professor in professors:
        enhanced_professor = professor
        
        # If missing Google Scholar or LinkedIn, try to find them
        if not professor.google_scholar or not professor.linkedin:
            additional_info = search_additional_professor_info(professor.name, university_name, tavily_api_key)
            
            if additional_info.get('google_scholar') and not professor.google_scholar:
                enhanced_professor.google_scholar = additional_info['google_scholar']
            
            if additional_info.get('linkedin') and not professor.linkedin:
                enhanced_professor.linkedin = additional_info['linkedin']
        
        enhanced_professors.append(enhanced_professor)
    
    return enhanced_professors

def search_professors_by_university_enhanced(university_name, cv_text, api_key, model, api_choice, tavily_api_key, tavily_params):
    """
    Enhanced professor search that uses Tavily for initial discovery, then processes with LLM.
    """
    if not BaseModel:
        return "Error: Pydantic not available"
    
    # Step 1: Use Tavily to get up-to-date faculty information
    st.info("🔍 Step 1: Searching for up-to-date faculty information using Tavily...")
    tavily_results = search_professors_with_tavily(university_name, cv_text, tavily_api_key, tavily_params)
    
    if isinstance(tavily_results, str):
        st.error(f"Tavily search failed: {tavily_results}")
        # Fallback to original method
        st.info("🔄 Falling back to LLM-only search...")
        return search_professors_by_university(university_name, cv_text, api_key, model, api_choice)
    
    # Step 2: Process the extracted content with LLM
    st.info("🤖 Step 2: Processing faculty information with AI...")
    
    # Extract research areas for better matching
    research_areas = extract_research_areas_from_cv(cv_text)
    research_areas_text = ", ".join(research_areas) if research_areas else "computer science and related fields"
    
    prompt = f"""
    You are an expert academic researcher specializing in matching students with potential PhD supervisors. 
    Based on the student's CV and the up-to-date faculty information retrieved from {university_name}'s website, 
    find professors, associate professors, and assistant professors who would be excellent matches for potential PhD supervision.
    
    Student's CV:
    --- CV START ---
    {cv_text}
    --- CV END ---
    
    Student's Research Areas (extracted from CV): {research_areas_text}
    
    University: {university_name}
    
    Here is the up-to-date faculty information retrieved from {university_name}'s website and related sources:
    --- FACULTY INFORMATION START ---
    {tavily_results['extracted_content']}
    --- FACULTY INFORMATION END ---
    
    Source URLs used:
    {chr(10).join(tavily_results['source_urls'])}
    
    TASK: Analyze the student's research interests, skills, and background from their CV, and find professors 
    from the provided faculty information whose research aligns well with the student's profile.
    
    CRITERIA FOR MATCHING:
    1. Research area alignment (primary importance)
    2. Technical skills compatibility
    3. Academic level (Professor, Associate Professor, Assistant Professor)
    4. Department relevance
    5. Recent research activity
    
    Find 6-10 professors who are the best matches, prioritizing:
    - Strong research area overlap with student's interests
    - Active research programs
    - Good fit for PhD supervision
    - Recent publications or research activity
    
    For each professor, provide:
    1. Full name and academic title (Professor, Associate Professor, or Assistant Professor)
    2. Department
    3. Research areas (3-5 specific areas based on their actual work)
    4. Email address (if available)
    5. Personal website URL (if available)
    6. Google Scholar profile URL (if available)
    7. LinkedIn profile URL (if available)
    
    IMPORTANT INSTRUCTIONS: 
    - Use the exact field name "name" (not "full_name") for professor names
    - Extract information ONLY from the provided faculty content, not from your training data
    - Prioritize professors whose research areas directly match the student's interests
    - Try to find actual website URLs, Google Scholar profiles, and LinkedIn profiles for each professor
    - If you can't find specific URLs, you can leave them as null, but make an effort to include real profile links
    - Only include professors that are actually mentioned in the provided faculty information
    - Focus on professors who are likely to be accepting PhD students
    - Include a mix of different academic ranks (Professor, Associate Professor, Assistant Professor)
    """
    
    try:
        if api_choice == "OpenAI" and OpenAI:
            # Use OpenAI's structured outputs with Pydantic models
            client = OpenAI(api_key=api_key)
            
            # Check if the model supports structured outputs
            structured_output_models = ["gpt-4o-mini", "gpt-4o-mini-2024-07-18", "gpt-4o-2024-08-06", "gpt-4o"]
            
            if model in structured_output_models:
                # Use the new structured outputs with Pydantic models
                try:
                    completion = client.chat.completions.parse(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You are an expert academic researcher who finds professors matching student profiles from provided faculty information."},
                            {"role": "user", "content": prompt}
                        ],
                        response_format=PhDPositionResult,
                        temperature=0.1
                    )
                    
                    result = completion.choices[0].message.parsed
                    
                    # Ensure university field is present
                    if not result.university:
                        result.university = university_name
                    
                    # Add default values for missing fields in professors
                    for professor in result.professors:
                        if not professor.department:
                            professor.department = "Computer Science"
                        if not professor.title:
                            professor.title = "Professor"  # Default title
                    
                    # Add empty hiring_analysis if not present
                    if not hasattr(result, 'hiring_analysis') or not result.hiring_analysis:
                        result.hiring_analysis = []
                    
                    return result
                    
                except Exception as e:
                    # Fallback to JSON mode if structured outputs fail
                    st.warning(f"Structured outputs failed, falling back to JSON mode: {e}")
            
            # Fallback to JSON mode for older models or if structured outputs fail
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert academic researcher who finds professors matching student profiles from provided faculty information. Return your response in JSON format."},
                    {"role": "user", "content": prompt + "\n\nPlease return your response in JSON format with all required fields including title for each professor."}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            response_text = completion.choices[0].message.content
            data = json.loads(response_text)
            
            # Ensure university field is present
            if "university" not in data:
                data["university"] = university_name
            
            # Add default values for missing fields in professors
            for professor in data.get("professors", []):
                # Handle field name variations
                if "full_name" in professor and "name" not in professor:
                    professor["name"] = professor.pop("full_name")
                
                if "title" not in professor:
                    professor["title"] = "Professor"  # Default title
                if "department" not in professor:
                    professor["department"] = "Computer Science"  # Default department
                if "email" not in professor:
                    professor["email"] = None
                if "website" not in professor:
                    professor["website"] = None
                if "google_scholar" not in professor:
                    professor["google_scholar"] = None
                if "linkedin" not in professor:
                    professor["linkedin"] = None
            
            # Add empty hiring_analysis to match the Pydantic model
            data["hiring_analysis"] = []
            
            return PhDPositionResult(**data)
            
        elif api_choice == "Gemini" and genai:
            # Fallback to regular response for Gemini
            response = get_gemini_response(api_key, prompt, model_name=model)
            
            # Try to extract JSON from the response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end != 0:
                json_str = response[json_start:json_end]
                try:
                    data = json.loads(json_str)
                    # Add default values for missing fields
                    for professor in data.get("professors", []):
                        # Handle field name variations
                        if "full_name" in professor and "name" not in professor:
                            professor["name"] = professor.pop("full_name")
                        
                        if "title" not in professor:
                            professor["title"] = "Professor"
                        if "department" not in professor:
                            professor["department"] = "Computer Science"
                    data["hiring_analysis"] = []
                    return PhDPositionResult(**data)
                except json.JSONDecodeError as e:
                    return f"Error parsing JSON: {e}. Raw response: {response}"
            else:
                return f"Error: No JSON found in response. Raw response: {response}"
        else:
            return "Error: No valid API available"
            
    except Exception as e:
        return f"Error: {e}"

# --- Prompt Engineering Functions ---

def create_email_prompt(cv_text, prof_info, student_name="the applicant"): # Renamed user_name to student_name
    prompt = f"""
        You are an expert academic advisor helping a student draft an email to a professor.
        The email should sound human-written, personalized, concise, and highly professional.
        It should NOT sound like it was written by an AI. Use natural language and a slightly enthusiastic but respectful tone.

        The student's name is: {student_name}.

        Here is the student's CV/Resume:
        --- CV START ---
        {cv_text}
        --- CV END ---

        Here is information about the professor (from their LinkedIn, website, Google Scholar, etc.):
        --- PROFESSOR INFO START ---
        {prof_info}
        --- PROFESSOR INFO END ---

        Based on BOTH the student's CV and the professor's information:
        1. Identify 1-2 key areas of VERY RECENT work or specific projects from the professor's info.
        2. Find specific skills, experiences, or projects from the student's CV that ALIGN STRONGLY with those recent areas of the professor's work.
        3. Draft an initial contact email from the student ({student_name}) to the professor.
        4. The email should:
            a. Clearly state the student's interest in the professor's work, referencing the SPECIFIC recent work/projects you identified.
            b. Briefly (1-2 sentences) mention the student's relevant background/skills from their CV that connect to the professor's work.
            c. Express interest in potential research opportunities (e.g., PhD, postdoc, collaboration, depending on the context implied by the CV - assume PhD applicant if not specified).
            d. Politely request a brief meeting or ask about openings.
            e. Be concise (around 300-350 words).
            f. Have a clear subject line, like "Prospective PhD Applicant - {student_name} - Interest in [Specific Research Area of Professor]".
            g. Ensure the tone is respectful, genuine, and demonstrates that the student has done their homework on the professor's work.
            h. **Crucially, make it sound like a human wrote it, not an AI. Avoid generic phrases. Be specific.**
            i. End the email with a closing like "Sincerely," or "Best regards," followed by the student's name: "{student_name}". Do NOT add any other signature elements like email or links, as these will be appended separately.

        Provide ONLY the drafted email content (Subject + Body including the closing with {student_name}).
    """

    # The "Final Polish" version of the prompt
    # system_prompt = f"""
    # You are an elite academic writing coach and strategist. Your specialty is helping aspiring PhD students craft compelling, authentic, and highly personalized emails to professors that get noticed and receive replies. You are an expert at cutting through the noise and making a genuine intellectual connection.
    
    # Your task is to draft a cold-outreach email from a student to a professor to inquire about PhD opportunities.
    # You will use the provided context and inputs to create a highly tailored email that stands out. Follow these steps carefully:
    
    # **1. CONTEXT & INPUTS:**
    # *   **Student Name:** {student_name}
    # *   **Student's Goal:** "To be considered for a PhD position in your lab."
    # *   **Student's CV/Resume:**
    #     --- CV START ---
    #     {cv_text}
    #     --- CV END ---
    # *   **Professor's Information (Publications, lab website, bio, etc.):**
    #     --- PROFESSOR INFO START ---
    #     {prof_info}
    #     --- PROFESSOR INFO END ---
    
    # **2. YOUR THOUGHT PROCESS (Follow these steps before writing):**
    # *   **Step A - Synthesize the Professor's Focus:** First, analyze the professor's information and identify their *current* research thrust from a recent paper (last 1-2 years).
    # *   **Step B - Find the "Golden Thread":** Next, meticulously scan the student's CV for the **single most compelling project or publication** that creates a direct "bridge" to the professor's current work.
    # *   **Step C - Formulate a Direct Question (CRITICAL STEP):** Based on the "Golden Thread" and the professor's work, formulate a forward-looking, specific research question. This question is the core of the email.
    
    # **3. DRAFTING THE EMAIL (Strict Rules):**
    # Based on your thought process, draft the email following these exact rules:
    
    # *   **Salutation (CRITICAL):** You MUST begin the email body with a formal salutation. Extract the professor's last name from the provided 'Professor's Information' and use it. For example: "Dear Professor Smith,".
    # *   **Subject Line:** Must be specific and connect the two research areas. Example: "Prospective PhD Applicant: [Your Topic] & [Their Topic]" or "Question re: your work on [Their Topic]".
    # *   **Direct Opening:** Start the first paragraph directly with a brief self-introduction (e.g., 'My name is Koshik Debanath...'). **Do NOT use generic pleasantries** like "I hope this finds you well."
    # *   **The Hook:** Immediately reference the professor's *specific* recent paper you identified.
    # *   **The Intellectual Launchpad:** This is the heart of the email.
    #     1.  Briefly (1 sentence) introduce your relevant "Golden Thread" project.
    #     2.  Then, state the direct question you formulated in Step C.
    #     3.  **Crucially, format this question in bold using Markdown (e.g., **"Could your method be adapted to...?"**). This makes it stand out.**
    # *   **State Your Readiness:** Briefly mention that your technical skills (e.g., PyTorch) have prepared you to explore such questions.
    # *   **Confident Call to Action:** Politely and directly ask for a conversation about a potential PhD opportunity. Example: "I have attached my CV and would be grateful for the opportunity to briefly discuss your research and my potential fit."
    # *   **Concise and Confident Tone:** Keep the email around 250 words. The tone should be that of a respectful but confident future colleague.
    
    # **OUTPUT ONLY THE DRAFTED EMAIL CONTENT (Subject + Salutation + Body).**
    # ** Use Sincerely, {student_name} as the closing.**
    # """
    system_prompt = f"""
    You are an elite academic writing coach and strategist. Your specialty is helping aspiring PhD students craft compelling, authentic, and highly personalized cold-outreach emails to professors that get noticed and elicit replies. You optimize for intellectual connection, specificity, and integrity—never fluff or plagiarism.
    
    Your task: Draft a cold email from a student to a professor inquiring about potential PhD opportunities.
    
    ========================
    1. INPUTS
    ========================
    * Student Name: {student_name}
    * Student's Goal: "To be considered for a PhD position in your lab."
    * Student CV/Resume (for selective mining—DO NOT dump): 
    --- CV START ---
    {cv_text}
    --- CV END ---
    * Professor Information (papers, site excerpts, bios, etc.):
    --- PROFESSOR INFO START ---
    {prof_info}
    --- PROFESSOR INFO END ---
    
    ========================
    2. THINKING STEPS (DO THIS BEFORE WRITING)
    ========================
    A. Identify Current Research Thrust:
       From professor info, choose ONE very recent, active, or still-relevant line of work (prefer work within last 1–2 years; if only older material exists, briefly acknowledge that and connect forward).
    
    B. Extract a “Golden Thread” from the student's CV:
       ONE project, paper, system, internship, or research experience that naturally bridges to the professor’s current thrust. Ignore generic achievements, test scores, awards, raw GPA, or unrelated laundry lists.
    
    C. Formulate a Forward-Looking Research Question:
       Based on the bridge, craft ONE precise, intellectually curious, non‑trivial question the student could plausibly explore in the professor's lab. It must:
       * Be specific (not “Can I join your lab?” or “How can I contribute?”).
       * Show you actually processed their work (but WITHOUT copying phrasing).
       * Point to a possible extension, limitation, comparative angle, adaptation, or integration.
       * Be written in the student's own voice—no lifted jargon strings.
       This question will be bolded in the email body using Markdown: **Like this.**
    
    D. Authenticity / Plagiarism Self-Check (CRITICAL):
       * Do NOT copy any contiguous phrase of 7+ words from the professor info.
       * Paraphrase ideas succinctly; avoid unnatural synonym swaps.
       * If a term of art (e.g., “conflict-driven clause learning”) must appear, keep it; that is domain language, not plagiarism.
       * Before producing the final email, mentally scan your draft and ensure no sentence feels like a reconstructed abstract. If risk detected, rewrite more plainly.
    
    E. Decide Length:
       Target ≈ 230–260 words. Extend up to 300 ONLY if the student is making a justified field transition that truly requires brief narrative context (then keep that context tight).
    
    ========================
    3. DRAFTING RULES
    ========================
    OUTPUT MUST INCLUDE ONLY:
    Subject line + Salutation + Body (with closing). No meta commentary.
    
    STRUCTURE & CONSTRAINTS:
    1. Subject Line:
       * Specific. Connect student’s focal area and professor’s current topic.
       * Patterns allowed: 
         - "Prospective PhD: [Student Thread] & Your Work on [Professor Topic]"
         - "Question on your recent work in [Specific Concept]" 
       * Avoid generic subjects (“PhD Inquiry”, “Application”).
    
    2. Salutation:
       * "Dear Professor <LastName>," (extract last name robustly).
       * Never “Hi Dr.” or first names unless ambiguity (then default to Professor).
    
    3. Opening Sentence:
       * Direct self-intro: "My name is {student_name} ..." No pleasantries (e.g., no “I hope this email finds you well.”).
       * Within first 2 sentences, reference the specific recent paper / talk / project (with natural paraphrase, not abstract recreation).
    
    4. Core Paragraph (“Intellectual Launchpad”):
       * 1 sentence: concise description of the Golden Thread project (impact or technique).
       * Immediately follow with the bolded research question (Markdown bold).
       * Ensure the question is exploratory, feasible, and shows you understand constraints or directions in the professor’s domain.
    
    5. Calibration & Motivation:
       * One sentence expressing authentic excitement or curiosity (plain, energetic language > formality bloat).
       * (Optional) If professor’s highlighted work is older, acknowledge and pivot to how the student wants to explore its evolution or adjacent current efforts.
    
    6. Readiness / Skills:
       * Briefly mention ONLY directly relevant technical or research skills (e.g., "experience with PyTorch, SMT tooling experiments, static analysis prototyping"). No lists of test scores, awards, or GPA.
    
    7. Call to Action:
       * Ask (politely, directly) for a brief conversation about fit and whether the professor is taking students this cycle. DO NOT ask for probability of admission.
    
    8. CV Handling:
       * Refer to attached CV or (preferably) a single link if available: e.g., “I’ve linked my CV here.” Do NOT summarize full CV in body.
    
    9. Tone:
       * Concise, confident, collegial, intellectually curious.
       * Avoid flattery inflation (“esteemed,” “renowned,” etc.). Specificity replaces flattery.
       * Absolutely no generic filler: "With due respect," "I am writing this email to...", etc.
    
    10. Closing:
       * Use a single closing line, then: "Sincerely, {student_name}"
    
    ========================
    4. QUALITY GUARDRAILS (ENFORCE)
    ========================
    * No plagiarism (see 2D).
    * No standardized test scores, GPA, or long award lists.
    * No generic claims of being a “hard worker” without context.
    * Only ONE bolded research question.
    * Avoid multiple questions; one well-crafted question is stronger.
    * If unsure about active vs. legacy work, gracefully note: “Although your 2022 paper on X may have evolved, it raised a question for me about …”
    * Keep sentences varied; prefer clarity over ornate style.
    
    ========================
    5. OUTPUT FORMAT
    ========================
    Return ONLY:
    Subject: ...
    Dear Professor <LastName>,
    <Body paragraphs including bolded question>
    Sincerely,
    {student_name}
    
    NO extra commentary, no markdown fences, no analysis.
    
    Proceed now using these instructions.
    """
                                                
    return system_prompt



def create_sop_latex_prompt(cv_text, prof_info, sop_template, student_name="the applicant", target_program="PhD Program"): # Renamed user_name to student_name
    prompt = f"""
    You are an expert academic advisor helping a student update their Statement of Purpose (SOP) LaTeX template
    to be specifically tailored for a professor and their research.
    The goal is to make the SOP compelling and highlight the student's fit with this specific professor.
    The output MUST be in LaTeX format, and you should try to preserve the original template's structure as much as possible,
    only modifying or adding content where it makes sense to personalize it for the professor.

    The student's name is: {student_name}.

    Student's CV/Resume:
    --- CV START ---
    {cv_text}
    --- CV END ---

    Professor's Information:
    --- PROFESSOR INFO START ---
    {prof_info}
    --- PROFESSOR INFO END ---

    Student's SOP LaTeX Template:
    --- SOP TEMPLATE START ---
    {sop_template}
    --- SOP TEMPLATE END ---

    Instructions:
    1.  Carefully analyze the professor's recent work, research interests, and lab focus from their provided information.
    2.  Identify sections in the SOP template that discuss research interests, future goals, or reasons for choosing a specific program/university. These are prime candidates for customization.
    3.  Look for placeholders in the template (e.g., `%%STUDENT_NAME%%`, `%%PROFESSOR_NAME%%`, `%%UNIVERSITY_NAME%%`, `%%SPECIFIC_RESEARCH_INTEREST_HERE%%`, `%%MENTION_PROFESSOR_WORK_ALIGNMENT%%`). If they exist, fill them appropriately.
        *   Specifically, replace `%%STUDENT_NAME%%` (or common patterns like `\\author{{Your Name}}`) with "{student_name}".
    4.  If no explicit placeholders exist, identify the most relevant paragraphs to modify.
    5.  Integrate how the student's skills, experiences (from CV), and research interests align DIRECTLY with THE SPECIFIC PROFESSOR'S work. Be concrete. Mention specific projects or papers of the professor if relevant and appropriate to weave in naturally.
    6.  Update any mentions of the university or program to be specific, if the template is generic.
    7.  The tone should remain academic, enthusiastic, and professional.
    8.  **Output the complete, updated SOP in LaTeX format.** Ensure all LaTeX syntax from the original template is preserved unless a modification is strictly necessary for content. If you are unsure about complex LaTeX, try to keep changes to the textual content within existing LaTeX commands/environments.

    For example, if the template has:
    `\\author{{%%STUDENT_NAME%%}}`
    Update it to:
    `\\author{{{student_name}}}`

    And if the template has a section like:
    `My primary research interest lies in [General Area]. I am particularly drawn to [University Name] because of its strong program in this field.`
    You might update it to:
    `My primary research interest lies in [Specific Area from Prof's work, e.g., Reinforcement Learning for Robotics]. I am particularly drawn to Professor [Professor's Last Name]'s work on [Specific Project/Paper of Professor] at [University Name], as it directly aligns with my project on [Student's relevant project from CV].`

    Begin the output directly with the LaTeX code (e.g., `\\documentclass{{article}}`). Do not add any preamble like "Here is the updated SOP:".
    """
    return prompt

def create_sop_latex_prompt(cv_text, prof_info, sop_template, student_name="Koshik Debanath", target_program="PhD Program"): # Renamed user_name to student_name
    prompt = f"""
    You are an expert academic advisor helping a student update their Statement of Purpose (SOP) LaTeX template
    to be specifically tailored for a professor and their research.
    The goal is to make the SOP compelling and highlight the student's fit with this specific professor.
    The output MUST be in LaTeX format, and you should try to preserve the original template's structure as much as possible,
    only modifying or adding content where it makes sense to personalize it for the professor.

    The student's name is: {student_name}.

    Student's CV/Resume:
    --- CV START ---
    {cv_text}
    --- CV END ---

    Professor's Information:
    --- PROFESSOR INFO START ---
    {prof_info}
    --- PROFESSOR INFO END ---

    Student's SOP LaTeX Template:
    --- SOP TEMPLATE START ---
    {sop_template}
    --- SOP TEMPLATE END ---

    Instructions:
    1.  Carefully analyze the professor's recent work, research interests, and lab focus from their provided information.
    2.  Identify sections in the SOP template that discuss research interests, future goals, or reasons for choosing a specific program/university. These are prime candidates for customization.
    3.  Look for placeholders in the template (e.g., `%%STUDENT_NAME%%`, `%%PROFESSOR_NAME%%`, `%%UNIVERSITY_NAME%%`, `%%SPECIFIC_RESEARCH_INTEREST_HERE%%`, `%%MENTION_PROFESSOR_WORK_ALIGNMENT%%`). If they exist, fill them appropriately.
        *   Specifically, replace `%%STUDENT_NAME%%` (or common patterns like `\\author{{Your Name}}`) with "{student_name}".
    4.  If no explicit placeholders exist, identify the most relevant paragraphs to modify.
    5.  Integrate how the student's skills, experiences (from CV), and research interests align DIRECTLY with THE SPECIFIC PROFESSOR'S work. Be concrete. Mention specific projects or papers of the professor if relevant and appropriate to weave in naturally.
    6.  Update any mentions of the university or program to be specific, if the template is generic.
    7.  The tone should remain academic, enthusiastic, and professional.
    8.  **Output the complete, updated SOP in LaTeX format.** Ensure all LaTeX syntax from the original template is preserved unless a modification is strictly necessary for content. If you are unsure about complex LaTeX, try to keep changes to the textual content within existing LaTeX commands/environments.

    For example, if the template has:
    `\\author{{%%STUDENT_NAME%%}}`
    Update it to:
    `\\author{{{student_name}}}`

    And if the template has a section like:
    `My primary research interest lies in [General Area]. I am particularly drawn to [University Name] because of its strong program in this field.`
    You might update it to:
    `My primary research interest lies in [Specific Area from Prof's work, e.g., Reinforcement Learning for Robotics]. I am particularly drawn to Professor [Professor's Last Name]'s work on [Specific Project/Paper of Professor] at [University Name], as it directly aligns with my project on [Student's relevant project from CV].`

    Begin the output directly with the LaTeX code (e.g., `\\documentclass{{article}}`). Do not add any preamble like "Here is the updated SOP:".
    """
    return prompt

def get_optimal_sending_time(prof_info):
    my_local_tz = pytz.timezone("Asia/Dhaka")  # Bangladesh Time Zone
    bd_current_time = datetime.now(my_local_tz)
    day = bd_current_time.strftime("%A")  # Get current day of the week
    found_tz = None
    
    system_prompt = f"""
        You are an expert in time zone analysis and optimal email sending strategies.
        Your task is to analyze the provided professor's information and determine the best time to send an email to them, considering their local time zone and typical working hours.
        Here is the professor's information:
        --- PROFESSOR INFO START ---
        {prof_info}
        --- PROFESSOR INFO END ---

        --- MY LOCAL BANGLADESH TIME ZONE ---
        The current time in Bangladesh is {bd_current_time} (Asia/Dhaka).
        The current day is {day}.
        Please analyze the professor's information to identify their local time zone and calculate the optimal time to send an email.

        Instructions:
        1. Identify the professor's local time zone based on their location or any clues in the provided information.
        2. Calculate the current time in that time zone.
        3. Determine the optimal time to send an email, considering typical working hours (e.g., 9 AM to 5 PM) and avoiding weekends.
        4. Return all times in **12-hour format with AM/PM** (e.g., 9:00 AM, 7:30 PM).
        5. Return the current time in both Bangladesh and the professor's local time, as well as the optimal sending time in both time zones.
        6. Consider the weekday and time of day to ensure the email is sent at a time when the professor is likely to be checking their email.
        7. Format the output as a dictionary with keys:
        - 'bd_current_time': current time in Bangladesh (12-hour format with AM/PM),
        - 'prof_current_time': current time in the professor's local time zone (12-hour format with AM/PM),
        - 'optimal_time_bd': optimal sending time in Bangladesh (12-hour format with AM/PM),
        - 'optimal_time_prof': optimal sending time in the professor's local time zone (12-hour format with AM/PM),
        - 'prof_timezone': the professor's identified time zone.
    """

    if not prof_info:
        return "Error: No professor information provided."

    if api_choice == "OpenAI" and OpenAI:
        client = OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model=selected_model,
            messages=[
                {"role": "system", "content": system_prompt.format(prof_info=prof_info)},
                {"role": "user", "content": ""}
            ],
            temperature=0.01
        )
        response = completion.choices[0].message.content.strip()
        return response
    elif api_choice == "Gemini" and genai:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=selected_model)
        response = model.generate_content(system_prompt.format(prof_info=prof_info))
        return response.text.strip()
        

    
def get_professor_suggestions(cv_text, university_name, api_key, model, api_choice):
    prompt = f"""
    You are an expert academic advisor. Based on the student's CV and the specified university, suggest the top 5 professors 
    who would be the best fit for potential research collaboration or PhD supervision.
    
    Student's CV:
    --- CV START ---
    {cv_text}
    --- CV END ---
    
    University: {university_name}
    
    Please analyze the student's research interests, skills, and background from their CV, and suggest 5 professors 
    from {university_name} whose research aligns well with the student's profile.
    
    For each professor, provide:
    1. Full Name and Title
    2. Research Areas (2-3 key areas)
    3. Recent Projects/Papers (1-2 notable ones)
    4. Why they're a good match (based on specific elements from the student's CV)
    5. Department/Lab
    6. Link to their faculty page (if found)
    
    Format the response in a clear, structured way.
    """
    
    if api_choice == "OpenAI" and OpenAI:
        return get_openai_response(api_key, prompt, model=model)
    elif api_choice == "Gemini" and genai:
        return get_gemini_response(api_key, prompt, model_name=model)
    else:
        return "Error: No valid API available"

# --- Pydantic Schemas for PhD Position Finder ---
if BaseModel:
    class ProfessorInfo(BaseModel):
        name: str = Field(..., description="Full name of the professor")
        title: str = Field(default="Professor", description="Academic title (Professor, Associate Professor, Assistant Professor)")
        department: str = Field(default="Computer Science", description="Department or school")
        research_areas: List[str] = Field(..., description="List of research areas")
        email: Optional[str] = Field(None, description="Email address if available")
        website: Optional[str] = Field(None, description="Personal website URL")
        google_scholar: Optional[str] = Field(None, description="Google Scholar profile URL")
        linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
        
        @classmethod
        def model_validate(cls, obj, *args, **kwargs):
            # Handle case where the model returns 'full_name' instead of 'name'
            if isinstance(obj, dict) and 'full_name' in obj and 'name' not in obj:
                obj['name'] = obj.pop('full_name')
            return super().model_validate(obj, *args, **kwargs)
        
    class HiringInfo(BaseModel):
        professor_name: str = Field(..., description="Name of the professor")
        is_hiring: bool = Field(..., description="Whether the professor is currently hiring")
        position_type: Optional[str] = Field(None, description="Type of position (PhD, Postdoc, etc.)")
        details: str = Field(..., description="Detailed information about hiring status")
        sources: List[str] = Field(..., description="List of source URLs")
        last_updated: Optional[str] = Field(None, description="When this information was last updated")
        
    class PhDPositionResult(BaseModel):
        university: str = Field(default="", description="University name")
        professors: List[ProfessorInfo] = Field(..., description="List of professors found")
        hiring_analysis: List[HiringInfo] = Field(default_factory=list, description="Hiring information for each professor")

# --- PhD Position Finder Functions ---
def search_professors_by_university(university_name, cv_text, api_key, model, api_choice):
    """
    Search for professors at a specific university based on the user's CV profile.
    Returns structured data about professors using OpenAI's structured outputs.
    """
    if not BaseModel:
        return "Error: Pydantic not available"
        
    prompt = f"""
    You are an expert academic researcher. Based on the student's CV and the specified university, 
    find professors, associate professors, and assistant professors who would be good matches for potential PhD supervision.
    
    Student's CV:
    --- CV START ---
    {cv_text}
    --- CV END ---
    
    University: {university_name}
    
    Please analyze the student's research interests, skills, and background from their CV, and find professors 
    from {university_name} whose research aligns well with the student's profile.
    
    Find 5-8 professors who are the best matches. For each professor, provide:
    1. Full name and academic title (Professor, Associate Professor, or Assistant Professor)
    2. Department
    3. Research areas (2-4 key areas)
    4. Email address (if available)
    5. Personal website URL (if available)
    6. Google Scholar profile URL (if available)
    7. LinkedIn profile URL (if available)
    
    IMPORTANT: 
    - Use the exact field name "name" (not "full_name") for professor names
    - Try to find actual website URLs, Google Scholar profiles, and LinkedIn profiles for each professor
    - If you can't find specific URLs, you can leave them as null, but make an effort to include real profile links
    """
    
    try:
        if api_choice == "OpenAI" and OpenAI:
            # Use OpenAI's structured outputs with Pydantic models
            client = OpenAI(api_key=api_key)
            
            # Check if the model supports structured outputs
            structured_output_models = ["gpt-4o-mini", "gpt-4o-mini-2024-07-18", "gpt-4o-2024-08-06", "gpt-4o"]
            
            if model in structured_output_models:
                # Use the new structured outputs with Pydantic models
                try:
                    completion = client.chat.completions.parse(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You are an expert academic researcher who finds professors matching student profiles."},
                            {"role": "user", "content": prompt}
                        ],
                        response_format=PhDPositionResult,
                        temperature=0.1
                    )
                    
                    result = completion.choices[0].message.parsed
                    
                    # Ensure university field is present
                    if not result.university:
                        result.university = university_name
                    
                    # Add default values for missing fields in professors
                    for professor in result.professors:
                        if not professor.department:
                            professor.department = "Computer Science"
                        if not professor.title:
                            professor.title = "Professor"  # Default title
                    
                    # Add empty hiring_analysis if not present
                    if not hasattr(result, 'hiring_analysis') or not result.hiring_analysis:
                        result.hiring_analysis = []
                    
                    return result
                    
                except Exception as e:
                    # Fallback to JSON mode if structured outputs fail
                    st.warning(f"Structured outputs failed, falling back to JSON mode: {e}")
            
            # Fallback to JSON mode for older models or if structured outputs fail
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert academic researcher who finds professors matching student profiles. Return your response in JSON format."},
                    {"role": "user", "content": prompt + "\n\nPlease return your response in JSON format with all required fields including title for each professor."}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            response_text = completion.choices[0].message.content
            data = json.loads(response_text)
            
            # Ensure university field is present
            if "university" not in data:
                data["university"] = university_name
            
            # Add default values for missing fields in professors
            for professor in data.get("professors", []):
                # Handle field name variations
                if "full_name" in professor and "name" not in professor:
                    professor["name"] = professor.pop("full_name")
                
                if "title" not in professor:
                    professor["title"] = "Professor"  # Default title
                if "department" not in professor:
                    professor["department"] = "Computer Science"  # Default department
                if "email" not in professor:
                    professor["email"] = None
                if "website" not in professor:
                    professor["website"] = None
                if "google_scholar" not in professor:
                    professor["google_scholar"] = None
                if "linkedin" not in professor:
                    professor["linkedin"] = None
            
            # Add empty hiring_analysis to match the Pydantic model
            data["hiring_analysis"] = []
            
            return PhDPositionResult(**data)
            
        elif api_choice == "Gemini" and genai:
            # Fallback to regular response for Gemini
            response = get_gemini_response(api_key, prompt, model_name=model)
            
            # Try to extract JSON from the response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end != 0:
                json_str = response[json_start:json_end]
                try:
                    data = json.loads(json_str)
                    # Add default values for missing fields
                    for professor in data.get("professors", []):
                        # Handle field name variations
                        if "full_name" in professor and "name" not in professor:
                            professor["name"] = professor.pop("full_name")
                        
                        if "title" not in professor:
                            professor["title"] = "Professor"
                        if "department" not in professor:
                            professor["department"] = "Computer Science"
                    data["hiring_analysis"] = []
                    return PhDPositionResult(**data)
                except json.JSONDecodeError as e:
                    return f"Error parsing JSON: {e}. Raw response: {response}"
            else:
                return f"Error: No JSON found in response. Raw response: {response}"
        else:
            return "Error: No valid API available"
            
    except Exception as e:
        return f"Error: {e}"

def search_hiring_info(professor_name, university_name, tavily_api_key):
    """
    Use Tavily to search for hiring information about a specific professor.
    """
    if not TavilyClient:
        return "Error: Tavily not available"
        
    try:
        client = TavilyClient(tavily_api_key)
        
        # Search for hiring information with advanced parameters
        search_query = f"{professor_name} {university_name} hiring PhD students position opening"
        
        # Use advanced search with more parameters for better results
        response = client.search(
            query=search_query,
            search_depth="advanced",
            max_results=10,
            include_raw_content=True,
            chunks_per_source=3
        )
        
        # Extract detailed information from the first result
        detailed_info = ""
        sources = []
        
        if response.get('results'):
            # Get the first result for detailed extraction
            first_result = response['results'][0]
            sources.append(first_result.get('url', ''))
            
            # Extract content from the professor's page
            try:
                extract_response = client.extract(
                    urls=[first_result['url']],
                    extract_depth="advanced",
                    format="text"
                )
                if extract_response.get('results'):
                    detailed_info = extract_response['results'][0].get('raw_content', '')
            except Exception as e:
                detailed_info = f"Could not extract detailed content: {e}"
        
        # Analyze if they're hiring based on the search results
        hiring_keywords = ['hiring', 'position', 'opening', 'accepting', 'seeking', 'recruiting', 'phd student', 'graduate student', 'looking for', 'opportunity']
        not_hiring_keywords = ['not hiring', 'no positions', 'closed', 'filled', 'not accepting', 'no openings']
        
        content_text = ' '.join([result.get('content', '') for result in response.get('results', [])])
        content_lower = content_text.lower()
        
        is_hiring = False
        position_type = None
        
        # Check for hiring indicators
        for keyword in hiring_keywords:
            if keyword in content_lower:
                is_hiring = True
                if 'phd' in keyword or 'graduate' in keyword:
                    position_type = "PhD Student"
                elif 'postdoc' in keyword:
                    position_type = "Postdoc"
                break
        
        # Check for not hiring indicators
        for keyword in not_hiring_keywords:
            if keyword in content_lower:
                is_hiring = False
                break
        
        # Create hiring info object
        hiring_info = HiringInfo(
            professor_name=professor_name,
            is_hiring=is_hiring,
            position_type=position_type,
            details=f"Based on search results: {content_text[:500]}...",
            sources=sources,
            last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        return hiring_info
        
    except Exception as e:
        return f"Error searching for {professor_name}: {e}"

def analyze_all_professors(professors, university_name, tavily_api_key):
    """
    Analyze hiring information for all professors using Tavily.
    """
    if not BaseModel:
        return "Error: Pydantic not available"
        
    hiring_analysis = []
    
    for professor in professors:
        st.info(f"Searching hiring information for {professor.name}...")
        hiring_info = search_hiring_info(professor.name, university_name, tavily_api_key)
        
        if isinstance(hiring_info, HiringInfo):
            hiring_analysis.append(hiring_info)
        else:
            # Create a default hiring info object if there was an error
            hiring_analysis.append(HiringInfo(
                professor_name=professor.name,
                is_hiring=False,
                position_type=None,
                details=f"Error: {hiring_info}",
                sources=[],
                last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
    
    return hiring_analysis

def search_additional_professor_info(professor_name, university_name, tavily_api_key):
    """
    Search for additional professor information from Google Scholar and LinkedIn.
    """
    if not TavilyClient:
        return {}
    
    try:
        client = TavilyClient(api_key=tavily_api_key)
        additional_info = {}
        
        # Search for Google Scholar profile
        try:
            scholar_query = f'"{professor_name}" "{university_name}" site:scholar.google.com'
            scholar_response = client.search(
                query=scholar_query,
                search_depth="basic",
                max_results=3,
                include_raw_content=False
            )
            if scholar_response.get('results'):
                for result in scholar_response['results']:
                    if 'scholar.google.com' in result.get('url', ''):
                        additional_info['google_scholar'] = result['url']
                        break
        except Exception as e:
            st.warning(f"Google Scholar search failed for {professor_name}: {e}")
        
        # Search for LinkedIn profile
        try:
            linkedin_query = f'"{professor_name}" "{university_name}" site:linkedin.com'
            linkedin_response = client.search(
                query=linkedin_query,
                search_depth="basic",
                max_results=3,
                include_raw_content=False
            )
            if linkedin_response.get('results'):
                for result in linkedin_response['results']:
                    if 'linkedin.com/in/' in result.get('url', ''):
                        additional_info['linkedin'] = result['url']
                        break
        except Exception as e:
            st.warning(f"LinkedIn search failed for {professor_name}: {e}")
        
        return additional_info
        
    except Exception as e:
        st.warning(f"Additional info search failed: {e}")
        return {}

# --- Streamlit App ---
st.set_page_config(layout="wide")
st.title("👨‍🏫 Professor Outreach Assistant 📧")

# --- Sidebar ---
st.sidebar.header("API Configuration")
api_choice = st.sidebar.selectbox("Select LLM API", ["OpenAI", "Gemini"])
api_key = ""
selected_model = ""

# Tavily API Key for PhD Position Finder
tavily_api_key = os.getenv("TAVILY_API_KEY")
if not tavily_api_key:
    tavily_api_key = st.sidebar.text_input("Tavily API Key (for PhD Position Finder)", type="password", help="Store as TAVILY_API_KEY in .env to load automatically.")
else:
    st.sidebar.caption("Tavily API Key loaded from .env")

if api_choice == "OpenAI":
    if OpenAI:
        # Attempt to get API key from .env first
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password", help="Store as OPENAI_API_KEY in .env to load automatically.")
        else:
            st.sidebar.caption("OpenAI API Key loaded from .env")
        
        client = OpenAI(api_key=api_key)
        # List of common OpenAI models
        OPENAI_MODELS = client.models.list()
        # """
        # SyncPage[Model](data=[Model(id='gpt-4-0613', created=1686588896, object='model', owned_by='openai'), Model(id='gpt-4', created=1687882411, object='model', owned_by='openai'), Model(id='gpt-3.5-turbo', created=1677610602, object='model', owned_by='openai'), Model(id='o4-mini-deep-research-2025-06-26', created=1750866121, object='model', owned_by='system'), Model(id='o3-pro-2025-06-10', created=1749166761, object='model', owned_by='system'), Model(id='o4-mini-deep-research', created=1749685485, object='model', owned_by='system'), Model(id='o3-deep-research', created=1749840121, object='model', owned_by='system'), Model(id='o3-deep-research-2025-06-26', created=1750865219, object='model', owned_by='system'), Model(id='davinci-002', created=1692634301, object='model', owned_by='system'), Model(id='babbage-002', created=1692634615, object='model', owned_by='system'), Model(id='gpt-3.5-turbo-instruct', created=1692901427, object='model', owned_by='system'), Model(id='gpt-3.5-turbo-instruct-0914', created=1694122472, object='model', owned_by='system'), Model(id='dall-e-3', created=1698785189, object='model', owned_by='system'), Model(id='dall-e-2', created=1698798177, object='model', owned_by='system'), Model(id='gpt-4-1106-preview', created=1698957206, object='model', owned_by='system'), Model(id='gpt-3.5-turbo-1106', created=1698959748, object='model', owned_by='system'), Model(id='tts-1-hd', created=1699046015, object='model', owned_by='system'), Model(id='tts-1-1106', created=1699053241, object='model', owned_by='system'), Model(id='tts-1-hd-1106', created=1699053533, object='model', owned_by='system'), Model(id='text-embedding-3-small', created=1705948997, object='model', owned_by='system'), Model(id='text-embedding-3-large', created=1705953180, object='model', owned_by='system'), Model(id='gpt-4-0125-preview', created=1706037612, object='model', owned_by='system'), Model(id='gpt-4-turbo-preview', created=1706037777, object='model', owned_by='system'), Model(id='gpt-3.5-turbo-0125', created=1706048358, object='model', owned_by='system'), Model(id='gpt-4-turbo', created=1712361441, object='model', owned_by='system'), Model(id='gpt-4-turbo-2024-04-09', created=1712601677, object='model', owned_by='system'), Model(id='gpt-4o', created=1715367049, object='model', owned_by='system'), Model(id='gpt-4o-2024-05-13', created=1715368132, object='model', owned_by='system'), Model(id='gpt-4o-mini-2024-07-18', created=1721172717, object='model', owned_by='system'), Model(id='gpt-4o-mini', created=1721172741, object='model', owned_by='system'), Model(id='gpt-4o-2024-08-06', created=1722814719, object='model', owned_by='system'), Model(id='chatgpt-4o-latest', created=1723515131, object='model', owned_by='system'), Model(id='o1-preview-2024-09-12', created=1725648865, object='model', owned_by='system'), Model(id='o1-preview', created=1725648897, object='model', owned_by='system'), Model(id='o1-mini-2024-09-12', created=1725648979, object='model', owned_by='system'), Model(id='o1-mini', created=1725649008, object='model', owned_by='system'), Model(id='gpt-4o-realtime-preview-2024-10-01', created=1727131766, object='model', owned_by='system'), Model(id='gpt-4o-audio-preview-2024-10-01', created=1727389042, object='model', owned_by='system'), Model(id='gpt-4o-audio-preview', created=1727460443, object='model', owned_by='system'), Model(id='gpt-4o-realtime-preview', created=1727659998, object='model', owned_by='system'), Model(id='omni-moderation-latest', created=1731689265, object='model', owned_by='system'), Model(id='omni-moderation-2024-09-26', created=1732734466, object='model', owned_by='system'), Model(id='gpt-4o-realtime-preview-2024-12-17', created=1733945430, object='model', owned_by='system'), Model(id='gpt-4o-audio-preview-2024-12-17', created=1734034239, object='model', owned_by='system'), Model(id='gpt-4o-mini-realtime-preview-2024-12-17', created=1734112601, object='model', owned_by='system'), Model(id='gpt-4o-mini-audio-preview-2024-12-17', created=1734115920, object='model', owned_by='system'), Model(id='o1-2024-12-17', created=1734326976, object='model', owned_by='system'), Model(id='o1', created=1734375816, object='model', owned_by='system'), Model(id='gpt-4o-mini-realtime-preview', created=1734387380, object='model', owned_by='system'), Model(id='gpt-4o-mini-audio-preview', created=1734387424, object='model', owned_by='system'), Model(id='computer-use-preview', created=1734655677, object='model', owned_by='system'), Model(id='o3-mini', created=1737146383, object='model', owned_by='system'), Model(id='o3-mini-2025-01-31', created=1738010200, object='model', owned_by='system'), Model(id='gpt-4o-2024-11-20', created=1739331543, object='model', owned_by='system'), Model(id='gpt-4.5-preview', created=1740623059, object='model', owned_by='system'), Model(id='gpt-4.5-preview-2025-02-27', created=1740623304, object='model', owned_by='system'), Model(id='computer-use-preview-2025-03-11', created=1741377021, object='model', owned_by='system'), Model(id='gpt-4o-search-preview-2025-03-11', created=1741388170, object='model', owned_by='system'), Model(id='gpt-4o-search-preview', created=1741388720, object='model', owned_by='system'), Model(id='gpt-4o-mini-search-preview-2025-03-11', created=1741390858, object='model', owned_by='system'), Model(id='gpt-4o-mini-search-preview', created=1741391161, object='model', owned_by='system'), Model(id='gpt-4o-transcribe', created=1742068463, object='model', owned_by='system'), Model(id='gpt-4o-mini-transcribe', created=1742068596, object='model', owned_by='system'), Model(id='o1-pro-2025-03-19', created=1742251504, object='model', owned_by='system'), Model(id='o1-pro', created=1742251791, object='model', owned_by='system'), Model(id='gpt-4o-mini-tts', created=1742403959, object='model', owned_by='system'), Model(id='o3-2025-04-16', created=1744133301, object='model', owned_by='system'), Model(id='o4-mini-2025-04-16', created=1744133506, object='model', owned_by='system'), Model(id='o3', created=1744225308, object='model', owned_by='system'), Model(id='o4-mini', created=1744225351, object='model', owned_by='system'), Model(id='gpt-4.1-2025-04-14', created=1744315746, object='model', owned_by='system'), Model(id='gpt-4.1', created=1744316542, object='model', owned_by='system'), Model(id='gpt-4.1-mini-2025-04-14', created=1744317547, object='model', owned_by='system'), Model(id='gpt-4.1-mini', created=1744318173, object='model', owned_by='system'), Model(id='gpt-4.1-nano-2025-04-14', created=1744321025, object='model', owned_by='system'), Model(id='gpt-4.1-nano', created=1744321707, object='model', owned_by='system'), Model(id='gpt-image-1', created=1745517030, object='model', owned_by='system'), Model(id='codex-mini-latest', created=1746673257, object='model', owned_by='system'), Model(id='o3-pro', created=1748475349, object='model', owned_by='system'), Model(id='gpt-4o-realtime-preview-2025-06-03', created=1748907838, object='model', owned_by='system'), Model(id='gpt-4o-audio-preview-2025-06-03', created=1748908498, object='model', owned_by='system'), Model(id='gpt-3.5-turbo-16k', created=1683758102, object='model', owned_by='openai-internal'), Model(id='tts-1', created=1681940951, object='model', owned_by='openai-internal'), Model(id='whisper-1', created=1677532384, object='model', owned_by='openai-internal'), Model(id='text-embedding-ada-002', created=1671217299, object='model', owned_by='openai-internal')], object='list')
        # """

        # Filter models to show only common ones
        common_models = [model.id for model in OPENAI_MODELS.data if "gpt" in model.id.lower() and "latest" not in model.id.lower()]
        common_models = sorted(common_models)  # Sort models alphabetically

        selected_model = st.sidebar.selectbox(
            "Select OpenAI Model",
            common_models,  # Use the filtered list of common models
            # ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo", "gpt-4-turbo-preview", "gpt-4", "gpt-4.1"],
            index=0 # Default to gpt-4o-mini
        )
    else:
        st.sidebar.warning("OpenAI library not loaded.")
elif api_choice == "Gemini":
    if genai:
        # Attempt to get API key from .env first
        api_key = os.getenv("GEMINI_API_KEY") # Ensure you have GEMINI_API_KEY in your .env
        if not api_key:
            api_key = st.sidebar.text_input("Enter your Gemini API Key", type="password", help="Store as GEMINI_API_KEY in .env to load automatically.")
        else:
            st.sidebar.caption("Gemini API Key loaded from .env")


        GEMINI_MODELS = genai.list_models()  # Get available Gemini models
        # Filter models to show only common ones
        common_models = [model.name for model in GEMINI_MODELS if "gemini" in model.name.lower() and "latest" not in model.name]
        common_models = sorted(common_models)  # Sort models alphabetically

        selected_model = st.sidebar.selectbox(
            "Select Gemini Model",
            common_models,  # Use the filtered list of common models
            # ["gemini-1.5-flash-latest", "gemini-1.5-pro-latest", "gemini-pro", "gemini-2.5-pro-preview-06-05", "gemini-2.5-pro-preview-03-25", "gemini-2.5-pro"], # Common models
            index=0 # Default to flash
        )
    else:
        st.sidebar.warning("Gemini library not loaded.")


st.sidebar.header("Your Information")
student_name = st.sidebar.text_input("Your Full Name", "Koshik Debanath")

default_signature = """Koshik Debanath
Email: koshik.debanath@gmail.com
LinkedIn: [Koshik Debanath](https://www.linkedin.com/in/kowshik24/)
Portfolio: [Koshik Debanath](https://kowshik24.github.io/kowshik.github.io/)
GitHub: [Koshik Debanath](https://github.com/kowshik24)"""
email_signature = st.sidebar.text_area("Your Email Signature Block (will be appended)", value=default_signature, height=160)


# CV Input
default_cv_text = ""
try:
    with open("Koshik-Debanath-CV.txt", "r", encoding="utf-8") as f:
        default_cv_text = f.read()
except FileNotFoundError:
    st.sidebar.info("Optional: Create 'Koshik-Debanath-CV.txt' in the same directory to auto-load your CV.")

cv_text = st.sidebar.text_area(
    "Paste your CV/Resume text here",
    value=default_cv_text,
    height=200,
    placeholder="Education, Skills, Projects, Publications..."
)

st.sidebar.header("SOP (Optional)")
draft_sop = st.sidebar.checkbox("Draft/Update SOP in LaTeX?")
sop_template_latex = ""
if draft_sop:
    default_sop_template_latex = ""
    try:
        with open("SOP-Koshik-Debanath.txt", "r", encoding="utf-8") as f:
            default_sop_template_latex = f.read()
    except FileNotFoundError:
        st.sidebar.info("Optional: Create 'SOP-Koshik-Debanath.txt' in the same directory to auto-load your SOP template.")

    sop_template_latex = st.sidebar.text_area(
        "Paste your SOP LaTeX Template",
        value=default_sop_template_latex,
        height=300,
        placeholder="""\\documentclass{article}
\\usepackage{times} % Example package
\\title{Statement of Purpose}
\\author{%%STUDENT_NAME%%} % Use placeholder
\\date{\\today}

\\begin{document}
\\maketitle

\\section*{Introduction}
My journey into the field of ...

\\section*{Research Interests}
I am particularly interested in %%SPECIFIC_RESEARCH_INTEREST_HERE%%.
Professor %%PROFESSOR_NAME%%'s work on %%MENTION_PROFESSOR_WORK_ALIGNMENT%% at %%UNIVERSITY_NAME%% is highly relevant.

\\section*{Why this Program?}
% ...

\\section*{Conclusion}
% ...

\\end{document}
        """
    )

# --- Main Page ---
tabs = st.tabs(["✉️ Email Draft", "👨‍🏫 Professor Suggestions", "🎓 PhD Position Finder", "🤖 Cohere Professor Finder", "🌐 OpenAI Web Search"])

with tabs[0]:
    st.header("Professor's Information")
    prof_info = st.text_area(
        "Paste Professor's Info (LinkedIn post, personal website bio, Google Scholar recent papers summary)",
        height=250,
        placeholder="e.g., Prof. X's recent paper on 'AI in Healthcare' aligns with my project on...' or 'From their website: Prof X leads the Y lab focusing on Z...'"
    )
    
    # Add timing information
    if prof_info:
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("📅 Calculate Optimal Sending Time"):
                timing_info = get_optimal_sending_time(prof_info)
            
                with col2:
                    st.info(f"""
                            {timing_info}
                            """)

    if st.button("🚀 Generate Email Draft", use_container_width=True):
        # Validations
        if not api_key:
            st.error("Please enter your API key in the sidebar or set it in your .env file.")
        elif not student_name:
            st.error("Please enter your name in the sidebar.")
        elif not cv_text:
            st.error("Please paste your CV text in the sidebar.")
        elif not prof_info:
            st.error("Please paste the professor's information.")
        elif draft_sop and not sop_template_latex:
            st.error("Please paste your SOP LaTeX template if you want to draft an SOP.")
        elif not selected_model:
            st.error("Please select a model in the sidebar.")
        else:
            # --- Generate Email ---
            with st.spinner("Drafting email... Please wait. Using model: " + selected_model):
                email_prompt_text = create_email_prompt(cv_text, prof_info, student_name)
                generated_email_body = "" # LLM generates body + closing with name

                if api_choice == "OpenAI" and OpenAI:
                    generated_email_body = get_openai_response(api_key, email_prompt_text, model=selected_model)
                elif api_choice == "Gemini" and genai:
                    generated_email_body = get_gemini_response(api_key, email_prompt_text, model_name=selected_model)
                else:
                    st.error(f"{api_choice} API not available or library not loaded.")

            st.subheader("✉️ Drafted Email")
            if generated_email_body and "Error:" not in generated_email_body :
                # Append the signature block
                final_email_content = generated_email_body
                if email_signature: # Add signature if provided
                     final_email_content += "\n\n--\n" + email_signature # Common signature separator

                st.text_area("Email Content", final_email_content, height=350)
                st.download_button("Download Email (.txt)", final_email_content, "draft_email.txt")
            elif generated_email_body: # Contains an error message from the API call
                st.error(generated_email_body)

            # --- Generate SOP (Optional) ---
            if draft_sop:
                with st.spinner("Updating SOP LaTeX... This might take a moment."):
                    sop_prompt_text = create_sop_latex_prompt(cv_text, prof_info, sop_template_latex, student_name)
                    generated_sop_latex = ""
                    if api_choice == "OpenAI" and OpenAI:
                        generated_sop_latex = get_openai_response(api_key, sop_prompt_text, model=selected_model)
                    elif api_choice == "Gemini" and genai:
                        generated_sop_latex = get_gemini_response(api_key, sop_prompt_text, model_name=selected_model)
                    else:
                        st.error(f"{api_choice} API not available or library not loaded.")


                st.subheader("📄 Drafted SOP (LaTeX)")
                if generated_sop_latex and "Error:" not in generated_sop_latex:
                    # Basic cleaning for LaTeX output
                    cleaned_sop_latex = generated_sop_latex.strip()
                    if cleaned_sop_latex.startswith("```latex"):
                        cleaned_sop_latex = cleaned_sop_latex[7:]
                    if cleaned_sop_latex.endswith("```"):
                        cleaned_sop_latex = cleaned_sop_latex[:-3]
                    cleaned_sop_latex = cleaned_sop_latex.strip()

                    st.text_area("SOP LaTeX Code", cleaned_sop_latex, height=400, key="sop_output")
                    st.download_button("Download SOP (.tex)", cleaned_sop_latex, "draft_sop.tex")
                elif generated_sop_latex: # Contains an error message
                    st.error(generated_sop_latex)

with tabs[1]:
    st.header("Find Matching Professors")
    university_name = st.text_input("Enter University Name", placeholder="e.g., Stanford University")
    
    if cv_text and university_name:
        if st.button("🔍 Find Matching Professors", use_container_width=True):
            with st.spinner("Finding matching professors... This might take a moment."):
                professor_suggestions = get_professor_suggestions(cv_text, university_name, api_key, selected_model, api_choice)
                
                if professor_suggestions and "Error:" not in professor_suggestions:
                    st.success(f"Found potential research matches at {university_name}!")
                    st.markdown(professor_suggestions)
                else:
                    st.error(professor_suggestions or "Failed to generate professor suggestions. Please try again.")
    else:
        if not cv_text:
            st.warning("Please paste your CV in the sidebar first.")
        if not university_name:
            st.warning("Please enter a university name.")

with tabs[2]:
    st.header("🎓 PhD Position Finder")
    st.markdown("""
    This tool helps you find professors at a specific university and analyzes their hiring status using web search.
    
    **How it works:**
    1. Enter a university name
    2. Uses Tavily to search for up-to-date faculty information from university websites
    3. Processes the information with AI to find professors matching your profile
    4. Enhances professor information with additional searches (Google Scholar, LinkedIn)
    5. Uses Tavily again to search for hiring information
    6. Returns structured results with links and details
    
    **Key Features:**
    - Uses real-time web search instead of outdated training data
    - Research area-based targeted searches for better matches
    - Configurable search parameters for better results
    - Comprehensive faculty discovery from university websites
    - Enhanced professor profiles with additional links
    - Smart matching based on CV research interests
    """)
    
    phd_university_name = st.text_input("Enter University Name", placeholder="e.g., New Jersey Institute of Technology", key="phd_university")
    
    # Tavily Search Parameters
    st.markdown("### ⚙️ Tavily Search Parameters")
    with st.expander("Configure Tavily Search Settings", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            search_depth = st.selectbox(
                "Search Depth",
                ["basic", "advanced"],
                index=1,  # Default to advanced
                help="Basic: Faster, less comprehensive. Advanced: Slower, more comprehensive."
            )
            
            max_results = st.slider(
                "Max Results per Query",
                min_value=1,
                max_value=20,
                value=5,
                help="Number of search results to retrieve per query"
            )
            
            include_raw_content = st.checkbox(
                "Include Raw Content",
                value=True,
                help="Include raw HTML content in search results"
            )
            
            include_answer = st.checkbox(
                "Include Answer",
                value=True,
                help="Include AI-generated answer in search results"
            )
        
        with col2:
            time_range = st.selectbox(
                "Time Range",
                ["", "day", "week", "month", "year"],
                index=0,
                help="Filter results by time (empty = no filter)"
            )
            
            extract_depth = st.selectbox(
                "Content Extraction Depth",
                ["basic", "advanced"],
                index=1,  # Default to advanced
                help="Depth of content extraction from URLs"
            )
            
            include_domains = st.text_input(
                "Include Domains (comma-separated)",
                placeholder="e.g., .edu, .ac.uk",
                help="Only search within specified domains"
            )
            
            exclude_domains = st.text_input(
                "Exclude Domains (comma-separated)",
                placeholder="e.g., .gov, .mil",
                help="Exclude results from specified domains"
            )
    
    # Prepare Tavily parameters
    tavily_params = {
        "search_depth": search_depth,
        "max_results": max_results,
        "include_raw_content": include_raw_content,
        "include_answer": include_answer,
        "extract_depth": extract_depth,
        "time_range": time_range if time_range else None,
        "include_domains": [d.strip() for d in include_domains.split(",")] if include_domains else None,
        "exclude_domains": [d.strip() for d in exclude_domains.split(",")] if exclude_domains else None,
        "country": None  # Could add this as a parameter if needed
    }
    
    if cv_text and phd_university_name:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🔍 Find Professors", use_container_width=True):
                if not tavily_api_key:
                    st.error("Please enter your Tavily API key in the sidebar.")
                elif not api_key:
                    st.error("Please enter your LLM API key in the sidebar.")
                else:
                    with st.spinner("Searching for professors... This may take a few minutes."):
                        # Step 1: Find professors using enhanced search with Tavily
                        professors_result = search_professors_by_university_enhanced(phd_university_name, cv_text, api_key, selected_model, api_choice, tavily_api_key, tavily_params)
                        
                        if isinstance(professors_result, PhDPositionResult):
                            # Enhance professor information with additional searches
                            st.info("🔍 Enhancing professor information with additional searches...")
                            professors_result.professors = enhance_professor_info(professors_result.professors, phd_university_name, tavily_api_key)
                            
                            st.session_state.phd_professors = professors_result
                            st.success(f"Found {len(professors_result.professors)} professors at {phd_university_name}!")
                        else:
                            st.error(f"Error finding professors: {professors_result}")
        
        with col2:
            if st.button("🔍 Analyze Hiring Status", use_container_width=True, disabled='phd_professors' not in st.session_state):
                if not tavily_api_key:
                    st.error("Please enter your Tavily API key in the sidebar.")
                elif 'phd_professors' not in st.session_state:
                    st.error("Please find professors first.")
                else:
                    with st.spinner("Analyzing hiring status... This may take several minutes."):
                        # Step 2: Analyze hiring information
                        hiring_analysis = analyze_all_professors(
                            st.session_state.phd_professors.professors, 
                            phd_university_name, 
                            tavily_api_key
                        )
                        
                        if isinstance(hiring_analysis, list):
                            st.session_state.phd_professors.hiring_analysis = hiring_analysis
                            st.success("Hiring analysis completed!")
                        else:
                            st.error(f"Error analyzing hiring status: {hiring_analysis}")
    
    # Display results
    if 'phd_professors' in st.session_state:
        st.subheader("📊 Results")
        
        # Display professors
        st.markdown("### Professors Found")
        
        # Summary of available links
        professors_with_links = sum(1 for p in st.session_state.phd_professors.professors 
                                  if p.website or p.google_scholar or p.linkedin)
        total_professors = len(st.session_state.phd_professors.professors)
        
        st.info(f"📊 **Summary**: {professors_with_links}/{total_professors} professors have profile links available")
        
        # Quick links section
        if professors_with_links > 0:
            st.markdown("#### 🔗 Quick Access Links")
            quick_links_cols = st.columns(min(3, professors_with_links))
            
            link_count = 0
            for i, professor in enumerate(st.session_state.phd_professors.professors):
                if professor.website or professor.google_scholar or professor.linkedin:
                    col_idx = link_count % len(quick_links_cols)
                    with quick_links_cols[col_idx]:
                        st.markdown(f"**{professor.name}**")
                        if professor.website:
                            st.markdown(f"[🌐 Website]({professor.website})")
                        if professor.google_scholar:
                            st.markdown(f"[📚 Scholar]({professor.google_scholar})")
                        if professor.linkedin:
                            st.markdown(f"[💼 LinkedIn]({professor.linkedin})")
                    link_count += 1
            
            st.markdown("---")
        
        for i, professor in enumerate(st.session_state.phd_professors.professors):
            with st.expander(f"👨‍🏫 {professor.name} - {professor.title}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Department:** {professor.department}")
                    st.write(f"**Research Areas:** {', '.join(professor.research_areas)}")
                    if professor.email:
                        st.write(f"**Email:** {professor.email}")
                
                with col2:
                    # Display links prominently
                    links_available = False
                    if professor.website:
                        st.markdown(f"🌐 **[Personal Website]({professor.website})**")
                        links_available = True
                    if professor.google_scholar:
                        st.markdown(f"📚 **[Google Scholar]({professor.google_scholar})**")
                        links_available = True
                    if professor.linkedin:
                        st.markdown(f"💼 **[LinkedIn Profile]({professor.linkedin})**")
                        links_available = True
                    
                    if not links_available:
                        st.info("No profile links available")
        
        # Display hiring analysis
        if hasattr(st.session_state.phd_professors, 'hiring_analysis') and st.session_state.phd_professors.hiring_analysis:
            st.markdown("### 🎯 Hiring Analysis")
            
            # Filter by hiring status
            hiring_professors = [h for h in st.session_state.phd_professors.hiring_analysis if h.is_hiring]
            not_hiring_professors = [h for h in st.session_state.phd_professors.hiring_analysis if not h.is_hiring]
            
            if hiring_professors:
                st.success(f"🎉 {len(hiring_professors)} professors appear to be hiring!")
                for hiring_info in hiring_professors:
                    with st.expander(f"✅ {hiring_info.professor_name} - {hiring_info.position_type or 'Position Available'}"):
                        st.write(f"**Status:** {'🟢 Hiring' if hiring_info.is_hiring else '🔴 Not Hiring'}")
                        if hiring_info.position_type:
                            st.write(f"**Position Type:** {hiring_info.position_type}")
                        st.write(f"**Details:** {hiring_info.details}")
                        if hiring_info.sources:
                            st.write("**Sources:**")
                            for source in hiring_info.sources:
                                st.markdown(f"- [{source}]({source})")
                        st.write(f"**Last Updated:** {hiring_info.last_updated}")
            
            if not_hiring_professors:
                st.info(f"ℹ️ {len(not_hiring_professors)} professors don't appear to be hiring currently")
                for hiring_info in not_hiring_professors:
                    with st.expander(f"❌ {hiring_info.professor_name}"):
                        st.write(f"**Status:** {'🟢 Hiring' if hiring_info.is_hiring else '🔴 Not Hiring'}")
                        st.write(f"**Details:** {hiring_info.details}")
                        if hiring_info.sources:
                            st.write("**Sources:**")
                            for source in hiring_info.sources:
                                st.markdown(f"- [{source}]({source})")
                        st.write(f"**Last Updated:** {hiring_info.last_updated}")
        
        # Download results
        if hasattr(st.session_state.phd_professors, 'hiring_analysis'):
            results_json = st.session_state.phd_professors.model_dump_json(indent=2)
            st.download_button(
                "📥 Download Results (JSON)",
                results_json,
                file_name=f"phd_positions_{phd_university_name.replace(' ', '_')}.json",
                mime="application/json"
            )
    
    else:
        if not cv_text:
            st.warning("Please paste your CV in the sidebar first.")
        if not phd_university_name:
            st.warning("Please enter a university name.")

with tabs[3]:
    st.header("🤖 Cohere Professor Finder")
    st.markdown("""
    This tool uses Cohere's AI to find professors at a specific university based on your CV profile.
    
    **Features:**
    - Uses Cohere's Command model for intelligent professor matching
    - Returns structured JSON data with detailed professor information
    - Includes research areas, recent projects, and match reasoning
    - Provides faculty page links when available
    
    **How it works:**
    1. Enter a university name (and optionally a department/research area)
    2. The AI analyzes your CV and finds professors whose research aligns with your background
    3. Returns detailed information about each professor including why they're a good match
    """)
    
    # Import the cohere service
    try:
        from cohere_services import get_answer
        cohere_available = True
    except ImportError as e:
        st.error(f"Cohere service not available: {e}")
        cohere_available = False
    
    if cohere_available:
        cohere_university = st.text_input("Enter University Name", placeholder="e.g., The University of Texas at Arlington", key="cohere_university")
        
        # Optional department/research area filter
        cohere_department = st.text_input("Department or Research Area (Optional)", placeholder="e.g., Computer Science, Machine Learning", key="cohere_department")
        
        if cv_text and cohere_university:
            if st.button("🔍 Find Professors with Cohere", use_container_width=True):
                with st.spinner("Searching for professors using Cohere AI... This may take a moment."):
                    try:
                        # Construct the query
                        query = cohere_university
                        if cohere_department:
                            query += f" in {cohere_department}"
                        
                        # Get response from Cohere
                        response = get_answer(query)
                        
                        if response and hasattr(response, 'message') and response.message.content:
                            # Parse the JSON response
                            import json
                            content = response.message.content[0].text if hasattr(response.message.content[0], 'text') else str(response.message.content[0])
                            
                            try:
                                data = json.loads(content)
                                
                                # Display the results
                                st.success(f"Found {len(data.get('professor_suggestions', []))} professors at {data.get('university', cohere_university)}!")
                                
                                # Display university and CV info
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.info(f"**University:** {data.get('university', cohere_university)}")
                                with col2:
                                    st.info(f"**CV Used:** {data.get('cv_used', 'Koshik Debanath CV')}")
                                
                                if data.get('department_or_area'):
                                    st.info(f"**Department/Area:** {data['department_or_area']}")
                                
                                # Display professor suggestions
                                st.subheader("👨‍🏫 Professor Suggestions")
                                
                                for i, professor in enumerate(data.get('professor_suggestions', []), 1):
                                    with st.expander(f"{i}. {professor.get('full_name_and_title', 'Professor')}"):
                                        col1, col2 = st.columns([2, 1])
                                        
                                        with col1:
                                            st.write(f"**Department/Lab:** {professor.get('department_or_lab', 'N/A')}")
                                            
                                            # Research areas
                                            research_areas = professor.get('research_areas', [])
                                            if research_areas:
                                                st.write("**Research Areas:**")
                                                for area in research_areas:
                                                    st.write(f"• {area}")
                                            
                                            # Recent projects/papers
                                            recent_projects = professor.get('recent_projects_or_papers', [])
                                            if recent_projects:
                                                st.write("**Recent Projects/Papers:**")
                                                for project in recent_projects:
                                                    title = project.get('title', 'N/A')
                                                    description = project.get('description', '')
                                                    if description:
                                                        st.write(f"• **{title}**: {description}")
                                                    else:
                                                        st.write(f"• {title}")
                                            
                                            # Match reasoning
                                            match_reasoning = professor.get('match_reasoning', '')
                                            if match_reasoning:
                                                st.write("**Why This Match:**")
                                                st.info(match_reasoning)
                                        
                                        with col2:
                                            # Faculty page link
                                            faculty_link = professor.get('faculty_page_link', '')
                                            if faculty_link:
                                                st.markdown(f"🌐 **[Faculty Page]({faculty_link})**")
                                            else:
                                                st.info("No faculty page link available")
                                
                                # Download results
                                st.subheader("📥 Download Results")
                                results_json = json.dumps(data, indent=2)
                                st.download_button(
                                    "Download JSON Results",
                                    results_json,
                                    file_name=f"cohere_professors_{cohere_university.replace(' ', '_')}.json",
                                    mime="application/json"
                                )
                                
                                # Display raw JSON for debugging (collapsible)
                                with st.expander("🔧 Raw JSON Response"):
                                    st.json(data)
                                
                            except json.JSONDecodeError as e:
                                st.error(f"Error parsing JSON response: {e}")
                                st.text("Raw response:")
                                st.text(content)
                        else:
                            st.error("No response received from Cohere service")
                            
                    except Exception as e:
                        st.error(f"Error calling Cohere service: {e}")
        else:
            if not cv_text:
                st.warning("Please paste your CV in the sidebar first.")
            if not cohere_university:
                st.warning("Please enter a university name.")
    else:
        st.error("Cohere service is not available. Please check that cohere_services.py is properly configured.")

with tabs[4]:
    st.header("🌐 OpenAI Web Search Professor Finder")
    st.markdown("""
    This tool uses OpenAI's web search functionality to find professors at universities using real-time web data.
    
    **Features:**
    - Uses OpenAI's web search models (gpt-4o-search-preview, gpt-4o-mini-search-preview)
    - Searches the web for up-to-date faculty information
    - Returns detailed professor information with citations
    - Configurable search parameters for better results
    
    **How it works:**
    1. Enter a university name
    2. Configure web search parameters (optional)
    3. The AI searches the web for current faculty information
    4. Returns professors matching your CV profile with web citations
    """)
    
    # Web search university input
    web_search_university = st.text_input("Enter University Name", placeholder="e.g., Iowa State University", key="web_search_university")
    
    # Web search parameters configuration
    st.markdown("### ⚙️ Web Search Parameters")
    with st.expander("Configure Web Search Settings", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            # Search context size
            search_context_size = st.selectbox(
                "Search Context Size",
                ["medium", "high", "low"],
                index=0,  # Default to medium
                help="High: Most comprehensive context, slower response. Medium: Balanced context and latency. Low: Least context, fastest response."
            )
            
            # User location settings
            st.markdown("#### 📍 User Location (Optional)")
            use_location = st.checkbox("Use location-based search", value=False)
            
            if use_location:
                country = st.text_input("Country Code (2-letter ISO)", placeholder="US", help="e.g., US, GB, CA")
                city = st.text_input("City", placeholder="New York")
                region = st.text_input("Region/State", placeholder="New York")
                timezone = st.text_input("Timezone (IANA)", placeholder="America/New_York", help="e.g., America/New_York, Europe/London")
        
        with col2:
            # Model selection for web search
            web_search_models = ["gpt-4o-search-preview", "gpt-4o-mini-search-preview"]
            selected_web_search_model = st.selectbox(
                "Web Search Model",
                web_search_models,
                index=0,  # Default to gpt-4o-search-preview
                help="Select the OpenAI model with web search capabilities"
            )
            
            # Temperature setting
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.1,
                step=0.1,
                help="Controls randomness in the response (0.0 = deterministic, 1.0 = very random)"
            )
    
    if cv_text and web_search_university:
        if st.button("🔍 Find Professors with Web Search", use_container_width=True):
            if not api_key:
                st.error("Please enter your OpenAI API key in the sidebar.")
            elif api_choice != "OpenAI":
                st.error("This feature requires OpenAI API. Please select OpenAI in the sidebar.")
            else:
                with st.spinner("Searching for professors using OpenAI web search... This may take a moment."):
                    try:
                        # Prepare web search options
                        web_search_options = {
                            "search_context_size": search_context_size
                        }
                        
                        # Add user location if specified
                        if use_location and (country or city or region or timezone):
                            user_location = {"type": "approximate", "approximate": {}}
                            if country:
                                user_location["approximate"]["country"] = country
                            if city:
                                user_location["approximate"]["city"] = city
                            if region:
                                user_location["approximate"]["region"] = region
                            if timezone:
                                user_location["approximate"]["timezone"] = timezone
                            web_search_options["user_location"] = user_location
                        
                        # Create the system prompt based on the test file
                        system_prompt = f"""You are an expert academic researcher. Find professors, associate professors, and assistant professors who would be good matches for potential PhD supervision.
    
    Student's Research Interests:
    --- Research Interests START ---
    Machine Learning, Deep Learning, Generative AI, Large Language Models, Computer Vision, Explainable AI, AI
    --- Research Interests END ---

    Student's Research Objective:
    A highly motivated researcher with extensive experience in Natural Language Processing, Generative AI, and Deep
    Learning, evidenced by multiple peer-reviewed publications. Seeking to pursue a PhD to develop novel multi-modal
    models and explore their applications in complex reasoning and misinformation detection.

    Student's Education:
    --- Education START ---
    Rajshahi University of Engineering & Technology, Rajshahi, Bangladesh(B.Sc. in Computer Science and Engineering CGPA: 3.27 / 4.00)
    Relevant Coursework: Linear Algebra, Data Structures and Algorithms, Object Oriented
    Programming, Discrete Mathematics, Database Management, Applied Statistics & Queuing Theory,
    Digital Image Processing, Neural Network and Fuzzy System, Artificial Intelligence, Data Mining
    --- Education END ---

    Student's Skills:
    --- Skills START ---
    Languages: Python (Expert), C/C++, Java, JavaScript, SQL, MATLAB
    AI/ML Frameworks: PyTorch, TensorFlow, Keras, Scikit-learn, LangChain, Transformers, OpenCV
    AI/ML Expertise: Generative AI (LLMs, RAG, Fine-tuning), NLP, Computer Vision, Deep Learning, Time Series
    Analysis, Prompt Engineering, Explainable AI (XAI), Data Mining
    Tools & Platforms: Git, Docker, FastAPI, Flask, Django, CI/CD, MLOps, Pinecone, MongoDB, MySQL, SQLite
    --- Skills END ---
    
    Student's Publications:
    --- Publications START ---
    Journal Articles:
    • Debanath, Koshik and Aich, Sagor and Srizon, Azmain Yakin, "Bayesian Physics-Informed Neural Networks for
    Parameter Inference and Uncertainty Quantification in Reaction-Diffusion Models of Wound Healing," Under
    review Mathematical Biosciences (July 2025). Preprint available at SSRN or DOI.

    Conferences:
    • K. D. Nath, A. F. M. M. Rahman and M. A. Hossain, "An Attention-Based Deep Learning Approach to Knee
    Injury Classification from MRI Images," 2023 26th International Conference on Computer and Information
    Technology (ICCIT), Cox's Bazar, Bangladesh, 2023, pp. 1-6, doi: 10.1109/ICCIT60459.2023.10441340.
    • K. Debanath, S. Aich and A. Y. Srizon, "Advancing Low-Resource NLP: Contextual Question Answering for
    Bengali Language Using Llama," 2025 International Conference on Electrical, Computer and Communication
    Engineering (ECCE), Chittagong, Bangladesh, 2025, pp. 1-6, doi: 10.1109/ECCE64574.2025.11013841.
    • S. Aich, K. Debanath and A. Y. Srizon, "Distinguishing Between Formal and Colloquial: A Multilingual BERT
    Approach to Bengali Language Classification," 2025 International Conference on Electrical, Computer and
    Communication Engineering (ECCE), Chittagong, Bangladesh, 2025, pp. 1-6, doi:
    10.1109/ECCE64574.2025.11013999
    • K. Debanath, S. Aich and A. Y. Srizon, "Analyzing Bot Activity and Political Discourse in the 2024 U.S.
    Presidential Election: A Machine Learning Approach to Misinformation and Manipulation," Accepted, To appear
    in 2nd International Conference on Next-Generation Computing, IoT and Machine Learning (NCIM-2025).
    • S. Aich, K. Debanath, and A. Y. Srizon, "Distinguishing Human-Written and AI-Generated Text: A
    Comprehensive Study Using Explainable Artificial Intelligence in Text Classification," Accepted, To appear in 2nd
    International Conference on Next-Generation Computing, IoT and Machine Learning (NCIM-2025).
    • K. Debanath, "Physics-Informed Neural Networks for Real-Time Anomaly Detection in Power System Dynamics,"
    Under Review, Submitted to 3rd International Conference on Big Data, IoT and Machine Learning (BIM 2025).
    --- Publications END ---
    
    
    
    University: {web_search_university}
    
    Please analyze the student's research interests, skills, and find professors 
    from {web_search_university} whose research aligns well with the student's profile.
    
    Find 5-8 professors who are the best matches. For each professor, provide:
    1. Full name and academic title (Professor, Associate Professor, or Assistant Professor)
    2. Department
    3. Research areas (2-4 key areas)
    4. Email address (if available)
    5. Personal website URL (if available)
    6. Google Scholar profile URL (if available)
    7. LinkedIn profile URL (if available)
    
    IMPORTANT: 
    - Use the exact field name "name" (not "full_name") for professor names
    - Try to find actual website URLs, Google Scholar profiles, and LinkedIn profiles for each professor
    - If you can't find specific URLs, you can leave them as null, but make an effort to include real profile links
    - Provide your response in a structured format that's easy to read
    - Include web citations where appropriate to show your sources
"""
                        
                        # Create the user query
                        query = f"Find professors from {web_search_university} who are good matches for the student's profile."
                        
                        # Make the API call with web search
                        client = OpenAI(api_key=api_key)
                        completion = client.chat.completions.create(
                            model=selected_web_search_model,
                            web_search_options=web_search_options,
                            messages=[
                                {
                                    "role": "system",
                                    "content": system_prompt,
                                },
                                {
                                    "role": "user",
                                    "content": query,
                                }
                            ]
                            # temperature=temperature
                        )
                        
                        # Get the response
                        response_content = completion.choices[0].message.content
                        
                        # Display the results
                        st.success(f"Found professors at {web_search_university} using web search!")
                        
                        # Display the main response
                        st.subheader("👨‍🏫 Professor Results")
                        st.markdown(response_content)
                        
                        # Display citations if available
                        if hasattr(completion.choices[0].message, 'annotations') and completion.choices[0].message.annotations:
                            st.subheader("📚 Web Citations")
                            for annotation in completion.choices[0].message.annotations:
                                if annotation.type == "url_citation":
                                    citation = annotation.url_citation
                                    st.markdown(f"**Source:** [{citation.title}]({citation.url})")
                                    st.markdown(f"**Cited in response:** Characters {citation.start_index}-{citation.end_index}")
                                    st.markdown("---")
                        
                        # Download results
                        st.subheader("📥 Download Results")
                        results_text = f"University: {web_search_university}\n\n{response_content}"
                        st.download_button(
                            "Download Results (TXT)",
                            results_text,
                            file_name=f"web_search_professors_{web_search_university.replace(' ', '_')}.txt",
                            mime="text/plain"
                        )
                        
                        # Display raw response for debugging (collapsible)
                        with st.expander("🔧 Raw API Response"):
                            st.json({
                                "model": selected_web_search_model,
                                "web_search_options": web_search_options,
                                "response": response_content,
                                "annotations": completion.choices[0].message.annotations if hasattr(completion.choices[0].message, 'annotations') else []
                            })
                        
                    except Exception as e:
                        st.error(f"Error calling OpenAI web search: {e}")
                        st.info("Make sure you're using a web search compatible model and have sufficient API credits.")
    else:
        if not cv_text:
            st.warning("Please paste your CV in the sidebar first.")
        if not web_search_university:
            st.warning("Please enter a university name.")

# --- Footer ---
st.sidebar.markdown("---")
st.sidebar.markdown("Created with Streamlit & LLMs")

# --- Debugging Info (Uncomment to use) ---
# st.sidebar.header("Debugging Info")
# with st.sidebar.expander("Show Debug Info"):
#     st.write("API Key:", api_key)
#     st.write("Selected Model:", selected_model)
#     st.write("Student Name:", student_name)
#     st.write("CV Text (trimmed):", cv_text[:100] + "..." if cv_text else "")
#     st.write("Professor Info (trimmed):", prof_info[:100] + "..." if prof_info else "")
#     st.write("SOP Template (trimmed):", sop_template_latex[:100] + "..." if sop_template_latex else "")
