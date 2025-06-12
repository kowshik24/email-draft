import streamlit as st
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz
import re

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
    return prompt

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

def get_optimal_sending_time(prof_info):
    # Dictionary of common US state names/abbreviations to timezone
    us_tz_map = {
        'eastern': 'America/New_York',
        'et': 'America/New_York',
        'est': 'America/New_York',
        'ny': 'America/New_York',
        'ma': 'America/New_York',
        'central': 'America/Chicago',
        'ct': 'America/Chicago',
        'cst': 'America/Chicago',
        'mountain': 'America/Denver',
        'mt': 'America/Denver',
        'mst': 'America/Denver',
        'pacific': 'America/Los_Angeles',
        'pt': 'America/Los_Angeles',
        'pst': 'America/Los_Angeles',
        'ca': 'America/Los_Angeles',
    }
    
    # Try to extract location from professor's info
    prof_info_lower = prof_info.lower()
    found_tz = None
    
    # Look for state/timezone mentions in the text
    for key, tz in us_tz_map.items():
        if key in prof_info_lower:
            found_tz = tz
            break
    
    if not found_tz:
        # Default to Eastern Time if no timezone found
        found_tz = 'America/New_York'
    
    # Get current time in Bangladesh
    bd_tz = pytz.timezone('Asia/Dhaka')
    current_bd_time = datetime.now(bd_tz)
    
    # Convert to professor's timezone
    prof_tz = pytz.timezone(found_tz)
    current_prof_time = current_bd_time.astimezone(prof_tz)
    
    # Calculate optimal sending time (next working day between 9 AM and 11 AM)
    optimal_time = current_prof_time.replace(hour=9, minute=30, second=0, microsecond=0)
    
    # If it's already past 11 AM in professor's timezone, move to next working day
    if current_prof_time.hour >= 11:
        optimal_time = optimal_time + timedelta(days=1)
    
    # Skip weekends
    while optimal_time.weekday() in [5, 6]:  # 5 is Saturday, 6 is Sunday
        optimal_time = optimal_time + timedelta(days=1)
    
    # Convert back to Bangladesh time for scheduling
    optimal_time_bd = optimal_time.astimezone(bd_tz)
    
    return {
        'bd_current_time': current_bd_time,
        'prof_current_time': current_prof_time,
        'optimal_time_bd': optimal_time_bd,
        'optimal_time_prof': optimal_time,
        'prof_timezone': found_tz,
    }

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

# --- Streamlit App ---
st.set_page_config(layout="wide")
st.title("👨‍🏫 Professor Outreach Assistant 📧")

# --- Sidebar ---
st.sidebar.header("API Configuration")
api_choice = st.sidebar.selectbox("Select LLM API", ["OpenAI", "Gemini"])
api_key = ""
selected_model = ""

if api_choice == "OpenAI":
    if OpenAI:
        # Attempt to get API key from .env first
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password", help="Store as OPENAI_API_KEY in .env to load automatically.")
        else:
            st.sidebar.caption("OpenAI API Key loaded from .env")

        selected_model = st.sidebar.selectbox(
            "Select OpenAI Model",
            ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo", "gpt-4-turbo-preview", "gpt-4", "gpt-4.1"],
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

        selected_model = st.sidebar.selectbox(
            "Select Gemini Model",
            ["gemini-1.5-flash-latest", "gemini-1.5-pro-latest", "gemini-pro", "gemini-2.5-pro-preview-06-05"], # Common models
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
tabs = st.tabs(["✉️ Email Draft", "👨‍🏫 Professor Suggestions"])

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
                    **Current Time Information:**
                    - Your time (Bangladesh): {timing_info['bd_current_time'].strftime('%I:%M %p, %A, %B %d, %Y')}
                    - Professor's local time: {timing_info['prof_current_time'].strftime('%I:%M %p, %A, %B %d, %Y')} ({timing_info['prof_timezone'].split('/')[-1].replace('_', ' ')})
                    
                    **Recommended Sending Time:**
                    - Your time (Bangladesh): {timing_info['optimal_time_bd'].strftime('%I:%M %p, %A, %B %d, %Y')}
                    - Professor's local time: {timing_info['optimal_time_prof'].strftime('%I:%M %p, %A, %B %d, %Y')}
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
            with st.spinner("Drafting email... Please wait."):
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