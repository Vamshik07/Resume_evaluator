import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# Configure Streamlit page
st.set_page_config(
    page_title="Resume Evaluation Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
import os
# Default to local backend; allow override via env (use full URL)
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


# Enhanced Custom CSS
st.markdown("""
<style>
    /* Main styling */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Header styling */
    .main-header {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem 0;
    }
    
    .sub-header {
        font-size: 1.8rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #667eea;
    }
    
    /* Card styling */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
        border-left: 5px solid #667eea;
        margin-bottom: 1rem;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 12px rgba(0, 0, 0, 0.15);
    }
    
    .success-card {
        border-left-color: #28a745;
        background: linear-gradient(135deg, #f0fff4 0%, #c6f6d5 100%);
    }
    
    .warning-card {
        border-left-color: #ffc107;
        background: linear-gradient(135deg, #fffbea 0%, #fef3c7 100%);
    }
    
    .danger-card {
        border-left-color: #dc3545;
        background: linear-gradient(135deg, #fff5f5 0%, #fed7d7 100%);
    }
    
    .info-card {
        border-left-color: #17a2b8;
        background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%);
    }
    
    /* Button styling */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        padding: 0.6rem 1.5rem;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    [data-testid="stSidebar"] .element-container {
        color: white;
    }
    
    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #2c3e50;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 1rem;
        font-weight: 500;
        color: #7f8c8d;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 12px 24px;
        font-weight: 600;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #f8f9fa;
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Alert styling */
    .stAlert {
        border-radius: 8px;
        border-left-width: 5px;
    }
    
    /* File uploader styling */
    [data-testid="stFileUploader"] {
        background-color: white;
        border: 2px dashed #667eea;
        border-radius: 12px;
        padding: 2rem;
    }
    
    /* Progress bar styling */
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Dataframe styling */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

def make_api_request(endpoint, method="GET", data=None, files=None):
    """Make API request with error handling"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            if files:
                response = requests.post(url, data=data, files=files)
            else:
                # For form data (like evaluation endpoint), use data parameter
                response = requests.post(url, data=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            # Check for specific Resume not found error (due to ephemeral server resets)
            if "Resume not found" in response.text:
                st.error("⚠️ Your uploaded resume was not found on the server. The server may have restarted or database was reset. Please upload your resume again.")
                if 'student_resume_id' in st.session_state:
                    del st.session_state.student_resume_id
                st.rerun()
            else:
                st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to API. Please ensure the backend server is running.")
        return None
    except Exception as e:
        st.error(f"Error making API request: {str(e)}")
        return None

def main():
    # Initialize session state
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'
    
    # Show navigation based on role selection
    if st.session_state.user_role is None:
        show_landing_page()
    else:
        show_navigation()
        route_page()

def show_landing_page():
    """Show enhanced landing page with role selection"""
    st.markdown('<h1 class="main-header">🎯 AI Resume Evaluation System</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 3rem;">
        <p style="font-size: 1.3rem; color: #555; margin-bottom: 2rem; line-height: 1.6;">
            Welcome to the <strong>Automated Resume Relevance Check System</strong><br>
            Powered by AI to streamline your recruitment process
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # System features overview
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.07);">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">⚡</div>
            <div style="font-weight: 600; color: #2c3e50;">Fast Processing</div>
            <div style="color: #7f8c8d; font-size: 0.9rem;">2-5 seconds per resume</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.07);">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">🤖</div>
            <div style="font-weight: 600; color: #2c3e50;">AI-Powered</div>
            <div style="color: #7f8c8d; font-size: 0.9rem;">Semantic + keyword matching</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.07);">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">📊</div>
            <div style="font-weight: 600; color: #2c3e50;">Detailed Insights</div>
            <div style="color: #7f8c8d; font-size: 0.9rem;">Scores, gaps & suggestions</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.07);">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">📈</div>
            <div style="font-weight: 600; color: #2c3e50;">Scalable</div>
            <div style="color: #7f8c8d; font-size: 0.9rem;">Handle 1000s of resumes</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Role selection cards
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2.5rem;
            border-radius: 20px;
            color: white;
            text-align: center;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
            margin-bottom: 2rem;
            transition: transform 0.3s ease;
        ">
            <div style="font-size: 4rem; margin-bottom: 1rem;">👔</div>
            <h2 style="margin: 0 0 1rem 0; font-size: 2rem;">Placement Officer</h2>
            <p style="font-size: 1.1rem; margin-bottom: 2rem; opacity: 0.95;">
                Manage job postings and evaluate candidates at scale
            </p>
            <div style="text-align: left; max-width: 400px; margin: 0 auto;">
                <div style="margin: 0.8rem 0; padding-left: 1rem;">✓ Upload job descriptions automatically</div>
                <div style="margin: 0.8rem 0; padding-left: 1rem;">✓ Evaluate multiple resumes instantly</div>
                <div style="margin: 0.8rem 0; padding-left: 1rem;">✓ View rankings & analytics</div>
                <div style="margin: 0.8rem 0; padding-left: 1rem;">✓ Export detailed reports</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Enter as Placement Officer", key="placement_btn", type="primary", use_container_width=True):
            st.session_state.user_role = 'placement_officer'
            st.session_state.current_page = 'dashboard'
            st.rerun()
    
    with col2:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            padding: 2.5rem;
            border-radius: 20px;
            color: white;
            text-align: center;
            box-shadow: 0 10px 30px rgba(245, 87, 108, 0.4);
            margin-bottom: 2rem;
            transition: transform 0.3s ease;
        ">
            <div style="font-size: 4rem; margin-bottom: 1rem;">🎓</div>
            <h2 style="margin: 0 0 1rem 0; font-size: 2rem;">Student</h2>
            <p style="font-size: 1.1rem; margin-bottom: 2rem; opacity: 0.95;">
                Upload resume and get instant feedback on job matches
            </p>
            <div style="text-align: left; max-width: 400px; margin: 0 auto;">
                <div style="margin: 0.8rem 0; padding-left: 1rem;">✓ Upload your resume once</div>
                <div style="margin: 0.8rem 0; padding-left: 1rem;">✓ Apply to multiple jobs</div>
                <div style="margin: 0.8rem 0; padding-left: 1rem;">✓ Get instant relevance scores</div>
                <div style="margin: 0.8rem 0; padding-left: 1rem;">✓ Receive improvement tips</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📝 Enter as Student", key="student_btn", type="primary", use_container_width=True):
            st.session_state.user_role = 'student'
            st.session_state.current_page = 'apply'
            st.rerun()
    
    # Footer
    st.markdown("""
    <div style="text-align: center; margin-top: 4rem; padding: 2.5rem; background: white; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.07);">
        <h3 style="color: #2c3e50; margin-bottom: 1rem;">🤖 Powered by Advanced AI</h3>
        <p style="color: #7f8c8d; line-height: 1.8; max-width: 800px; margin: 0 auto;">
            Our system combines rule-based keyword matching with advanced semantic analysis using 
            Sentence Transformers and optional Google Gemini LLM integration for the most accurate 
            resume evaluations possible.
        </p>
    </div>
    """, unsafe_allow_html=True)

def show_navigation():
    """Show sidebar navigation based on user role"""
    with st.sidebar:
        # User info
        role_icon = "👔" if st.session_state.user_role == 'placement_officer' else "🎓"
        role_name = "Placement Officer" if st.session_state.user_role == 'placement_officer' else "Student"
        
        st.markdown(f"""
        <div style="background: white; padding: 1.5rem; border-radius: 12px; margin-bottom: 2rem; text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">{role_icon}</div>
            <div style="font-weight: 600; color: #2c3e50; font-size: 1.2rem;">{role_name}</div>
            <div style="color: #7f8c8d; font-size: 0.9rem;">Portal</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation menu based on role
        if st.session_state.user_role == 'placement_officer':
            st.markdown("### 📋 Navigation")
            
            if st.button("🏠 Dashboard", key="nav_dashboard", use_container_width=True):
                st.session_state.current_page = 'dashboard'
                st.rerun()
            
            if st.button("📤 Upload Files", key="nav_upload", use_container_width=True):
                st.session_state.current_page = 'upload'
                st.rerun()
            
            if st.button("🎯 Evaluate Resumes", key="nav_evaluate", use_container_width=True):
                st.session_state.current_page = 'evaluate'
                st.rerun()
            
            if st.button("📊 View Results", key="nav_results", use_container_width=True):
                st.session_state.current_page = 'results'
                st.rerun()
            
            if st.button("🗂️ Manage Data", key="nav_manage", use_container_width=True):
                st.session_state.current_page = 'manage'
                st.rerun()
        
        else:  # Student
            st.markdown("### 📋 Navigation")
            
            if st.button("🎯 Apply for Jobs", key="nav_apply", use_container_width=True):
                st.session_state.current_page = 'apply'
                st.rerun()
            
            if st.button("📊 My Applications", key="nav_my_apps", use_container_width=True):
                st.session_state.current_page = 'my_applications'
                st.rerun()
        
        st.markdown("---")
        
        # Logout button
        if st.button("🚪 Logout", key="nav_logout", use_container_width=True, type="secondary"):
            st.session_state.user_role = None
            st.session_state.current_page = 'home'
            st.rerun()
        
        # Footer info
        st.markdown("---")
        st.markdown("""
        <div style="background: white; padding: 1rem; border-radius: 8px; font-size: 0.85rem; color: #7f8c8d;">
            <div style="margin-bottom: 0.5rem;"><strong>💡 Tips:</strong></div>
            <div>• Upload PDF/DOCX files</div>
            <div>• Max file size: 10MB</div>
            <div>• Results in 2-5 seconds</div>
        </div>
        """, unsafe_allow_html=True)


def route_page():
    """Route to the appropriate page based on current_page state"""
    page = st.session_state.current_page
    
    if st.session_state.user_role == 'placement_officer':
        if page == 'dashboard':
            show_dashboard()
        elif page == 'upload':
            show_upload_page()
        elif page == 'evaluate':
            show_evaluation_page()
        elif page == 'results':
            show_results_page()
        elif page == 'manage':
            show_manage_page()
        else:
            show_dashboard()
    
    elif st.session_state.user_role == 'student':
        if page == 'apply':
            show_student_workflow()
        elif page == 'my_applications':
            show_student_applications()
        else:
            show_student_workflow()


def show_student_applications():
    """Show student's application history"""
    st.markdown('<h2 class="sub-header">📊 My Applications</h2>', unsafe_allow_html=True)
    
    if 'student_resume_id' not in st.session_state:
        st.warning("⚠️ Please upload your resume first to view applications.")
        if st.button("📋 Upload Resume Now"):
            st.session_state.current_page = 'apply'
            st.rerun()
        return
    
    # Get all evaluations for this resume
    resume_id = st.session_state.student_resume_id
    results_response = make_api_request("/results")
    
    if results_response and results_response.get("results"):
        # Filter for this student's resume
        all_results = results_response["results"]
        my_results = [r for r in all_results if r.get("resume_id") == resume_id]
        
        if my_results:
            st.success(f"✅ Found {len(my_results)} applications")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Applications", len(my_results))
            
            with col2:
                high_matches = len([r for r in my_results if r.get("verdict") == "High"])
                st.metric("High Matches", high_matches)
            
            with col3:
                avg_score = sum(r.get("relevance_score", 0) for r in my_results) / len(my_results)
                st.metric("Avg Score", f"{avg_score:.0f}%")
            
            with col4:
                best_score = max(r.get("relevance_score", 0) for r in my_results)
                st.metric("Best Score", f"{best_score}%")
            
            st.markdown("---")
            
            # Display applications
            for i, result in enumerate(sorted(my_results, key=lambda x: x.get("relevance_score", 0), reverse=True)):
                verdict_color = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}
                verdict_emoji = verdict_color.get(result.get("verdict", ""), "⚪")
                
                with st.expander(
                    f"{verdict_emoji} {result.get('job_title', 'Unknown')} - {result.get('company', 'Unknown')} | Score: {result.get('relevance_score', 0)}%",
                    expanded=(i == 0)
                ):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Company:** {result.get('company', 'N/A')}")
                        st.write(f"**Applied:** {result.get('evaluation_date', 'N/A')[:10]}")
                        st.write(f"**Verdict:** {verdict_emoji} {result.get('verdict', 'N/A')}")
                    
                    with col2:
                        score = result.get('relevance_score', 0)
                        if score >= 80:
                            st.success(f"**Score: {score}%** 🎯")
                        elif score >= 60:
                            st.warning(f"**Score: {score}%** ⚡")
                        else:
                            st.error(f"**Score: {score}%** 📈")
                    
                    # Show missing skills if available
                    missing_skills = result.get("missing_skills", [])
                    if missing_skills:
                        st.write("**🎯 Focus Areas:**")
                        for skill in missing_skills[:5]:
                            st.write(f"• {skill}")
                    
                    # Show improvements
                    suggestions = result.get("improvement_suggestions", [])
                    if suggestions:
                        st.write("**💡 Suggestions:**")
                        for suggestion in suggestions[:3]:
                            st.write(f"• {suggestion}")
        else:
            st.info("📭 No applications yet. Start applying for jobs!")
    else:
        st.info("📭 No applications yet. Start applying for jobs!")


def show_placement_officer_interface():
    """Legacy function - now handled by navigation"""
    show_dashboard()


def show_student_interface():
    """Legacy function - now handled by navigation"""
    show_student_workflow()

def show_placement_overview():
    """Legacy function - redirect to main dashboard"""
    show_dashboard()

def show_placement_upload_jd():
    """Show placement officer job description upload"""
    st.header("📄 Upload Job Description")
    st.info("💡 **Fully Automated**: Just upload the job description file - all requirements will be extracted automatically!")
    
    with st.form("placement_upload_jd_form"):
        # File upload
        jd_file = st.file_uploader(
            "Choose a job description file (PDF/DOCX/TXT)",
            type=['pdf', 'docx', 'doc', 'txt'],
            key="placement_jd_file",
            help="The system will automatically extract job title, company, skills, and requirements"
        )
        
        # Submit button
        submitted = st.form_submit_button("🚀 Upload & Auto-Parse Job Description", type="primary")
        
        if submitted and jd_file:
            # Prepare form data - no manual input needed
            form_data = {
                "title": "",  # Will be extracted automatically
                "company": "",  # Will be extracted automatically
                "location": ""  # Will be extracted automatically
            }
            
            files = {"file": (jd_file.name, jd_file.getvalue(), jd_file.type)}
            
            # Make API request
            with st.spinner("🤖 Automatically extracting job requirements..."):
                result = make_api_request("/upload/job-description", "POST", form_data, files)
            
            if result:
                st.success("✅ Job description uploaded and parsed successfully!")
                
                # Show extracted information in a clean format
                if "parsed_data" in result:
                    parsed = result["parsed_data"]
                    
                    # Create a more professional display
                    st.subheader("📋 Job Description Summary")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"**Job Title:** {parsed.get('job_title', 'Not specified')}")
                        st.info(f"**Company:** {parsed.get('company_info', {}).get('name', 'Not specified')}")
                    with col2:
                        st.info(f"**Location:** {parsed.get('company_info', {}).get('location', 'Not specified')}")
                        st.info(f"**Skills Found:** {len(parsed.get('required_skills', []))} skills identified")
                    
                    # Show extracted skills in a better format
                    if parsed.get("required_skills"):
                        st.subheader("🎯 Key Skills Identified")
                        skills = parsed["required_skills"][:15]  # Show first 15 skills
                        if len(parsed["required_skills"]) > 15:
                            skills.append(f"... and {len(parsed['required_skills']) - 15} more")
                        
                        # Display skills as badges
                        skill_cols = st.columns(3)
                        for i, skill in enumerate(skills):
                            with skill_cols[i % 3]:
                                st.success(f"✓ {skill.title()}")
                    
                    # Show responsibilities if available
                    if parsed.get("responsibilities"):
                        st.subheader("📝 Key Responsibilities")
                        for i, resp in enumerate(parsed["responsibilities"][:5], 1):
                            st.write(f"{i}. {resp}")
                    
                    # Show experience requirements
                    if parsed.get("experience_requirements", {}).get("level"):
                        st.subheader("💼 Experience Level")
                        exp_info = parsed["experience_requirements"]
                        if exp_info.get("min_years", 0) > 0:
                            st.write(f"**Level:** {exp_info.get('level', 'Not specified')}")
                            st.write(f"**Experience:** {exp_info.get('min_years', 0)}+ years")

def show_placement_search_resumes():
    """Show placement officer resume search and filter"""
    st.header("🔍 Search & Filter Resumes")
    st.info("🔍 **Search and Filter**: Find matching resumes by job role, score, and location.")
    
    # Get job descriptions for filtering
    jds_response = make_api_request("/job-descriptions")
    jds = jds_response.get("job_descriptions", []) if jds_response else []
    
    if not jds:
        st.warning("⚠️ No job descriptions found. Please upload a job description first.")
        return
    
    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        # Keep objects to avoid brittle string parsing
        jd_options = ["All"] + jds
        jd_filter = st.selectbox(
            "Filter by Job Description",
            jd_options,
            format_func=lambda jd: jd if jd == "All" else f"{jd.get('title', 'Untitled')} - {jd.get('company', 'Unknown')}",
            key="placement_jd_filter"
        )
    
    with col2:
        verdict_filter = st.selectbox(
            "Filter by Verdict",
            ["All", "High", "Medium", "Low"],
            key="placement_verdict_filter"
        )
    
    with col3:
        min_score = st.slider(
            "Minimum Score",
            min_value=0,
            max_value=100,
            value=0,
            key="placement_min_score"
        )
    
    # Get results
    params = {}
    if isinstance(jd_filter, dict):
        params["job_description_id"] = jd_filter.get("id")
    
    if verdict_filter != "All":
        params["verdict"] = verdict_filter
    
    if min_score > 0:
        params["min_score"] = min_score
    
    # Build query string
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    endpoint = f"/results?{query_string}" if query_string else "/results"
    
    results_response = make_api_request(endpoint)
    
    if results_response and results_response.get("results"):
        results = results_response["results"]
        
        # Display results in a table
        st.subheader(f"📋 Matching Resumes ({len(results)} found)")
        
        # Create DataFrame
        df = pd.DataFrame(results)
        
        # Format the DataFrame for display
        display_df = df[["student_name", "job_title", "company", "relevance_score", "verdict", "evaluation_date"]].copy()
        display_df.columns = ["Student", "Job Title", "Company", "Score", "Verdict", "Date"]
        display_df["Score"] = display_df["Score"].astype(str) + "%"
        
        # Color code verdicts
        def color_verdict(val):
            if val == "High":
                return "background-color: #d4edda; color: #155724"
            elif val == "Medium":
                return "background-color: #fff3cd; color: #856404"
            elif val == "Low":
                return "background-color: #f8d7da; color: #721c24"
            return ""
        
        styled_df = display_df.style.applymap(color_verdict, subset=["Verdict"])
        st.dataframe(styled_df, use_container_width=True)
        
        # Download results
        if st.button("📥 Download Results as CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="📊 Download CSV",
                data=csv,
                file_name="placement_resume_results.csv",
                mime="text/csv"
            )
    
    else:
        st.info("No matching resumes found. Try adjusting your filters.")

def show_student_workflow():
    """Show student workflow - Apply for jobs using resume"""
    st.header("📝 Apply for Jobs")
    st.info("🎓 **Apply for Jobs**: Upload your resume and apply for available job positions. Get instant evaluation feedback!")
    
    # Step 1: Upload Resume (if not already uploaded)
    if 'student_resume_id' not in st.session_state:
        st.subheader("📋 Step 1: Upload Your Resume")
        
        with st.form("student_upload_form"):
            # File upload
            resume_file = st.file_uploader(
                "Choose your resume file (PDF/DOCX)",
                type=['pdf', 'docx', 'doc'],
                key="student_resume_file",
                help="The system will automatically extract your name, contact info, skills, and experience"
            )
            
            # Submit button
            submitted = st.form_submit_button("🚀 Upload Resume", type="primary")
            
            if submitted and resume_file:
                # Prepare form data - no manual input needed
                form_data = {
                    "student_name": "",  # Will be extracted automatically
                    "student_email": ""  # Will be extracted automatically
                }
                
                files = {"file": (resume_file.name, resume_file.getvalue(), resume_file.type)}
                
                # Make API request
                with st.spinner("🤖 Automatically extracting resume information..."):
                    result = make_api_request("/upload/resume", "POST", form_data, files)
                
                if result:
                    st.success("✅ Resume uploaded successfully!")
                    
                    # Show extracted information briefly
                    if "parsed_data" in result:
                        parsed = result["parsed_data"]
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Student Name", parsed.get("contact_info", {}).get("name", "Not detected"))
                            st.metric("Email", parsed.get("contact_info", {}).get("email", "Not detected"))
                        with col2:
                            st.metric("Skills Found", len(parsed.get("skills", [])))
                            st.metric("Experience Entries", len(parsed.get("experience", [])))
                    
                    # Store resume ID for job applications
                    st.session_state.student_resume_id = result.get("resume_id")
                    st.rerun()
    else:
        col1, col2 = st.columns([5, 1])
        with col1:
            st.success("✅ Resume uploaded! Ready to apply for jobs.")
        with col2:
            if st.button("🔄 Re-upload", use_container_width=True):
                if 'student_resume_id' in st.session_state:
                    del st.session_state.student_resume_id
                st.rerun()
    
    # Step 2: Browse and Apply for Jobs
    if 'student_resume_id' in st.session_state:
        st.subheader("🎯 Step 2: Browse Available Jobs")
        
        # Debug info removed for cleaner UI
        
        # Get job descriptions
        jds_response = make_api_request("/job-descriptions")
        jds = jds_response.get("job_descriptions", []) if jds_response else []
        
        if jds:
            st.write(f"**Found {len(jds)} available job positions:**")
            
            # Display jobs in cards
            for i, jd in enumerate(jds):
                with st.expander(f"📋 {jd['title']} - {jd['company']}", expanded=False):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Company:** {jd['company']}")
                        st.write(f"**Location:** {jd.get('location', 'Not specified')}")
                        st.write(f"**Posted:** {jd.get('created_at', 'Recently')}")
                        
                        # Show job description preview
                        if jd.get('description'):
                            description_preview = jd['description'][:200] + "..." if len(jd['description']) > 200 else jd['description']
                            st.write(f"**Description:** {description_preview}")
                    
                    with col2:
                        # Apply button for this job
                        if st.button(f"🎯 Apply for this Job", key=f"apply_{jd['id']}", type="primary"):
                            # Check if resume is uploaded
                            if 'student_resume_id' not in st.session_state:
                                st.error("❌ Please upload your resume first before applying for jobs.")
                                return
                            
                            # Make evaluation request
                            form_data = {
                                "resume_id": st.session_state.student_resume_id,
                                "job_description_id": jd['id']
                            }
                            
                            # Remove debug info for cleaner UI
                            
                            with st.spinner("🤖 Evaluating your application..."):
                                result = make_api_request("/evaluate", "POST", form_data)
                            
                            if result and "analysis" in result:
                                analysis = result["analysis"]
                                
                                # Show application results
                                st.success("🎉 Application submitted successfully!")
                                
                                # Create a professional results display
                                st.subheader("📊 Evaluation Results")
                                
                                # Score and verdict in a better layout
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    score = analysis['relevance_score']
                                    if score >= 80:
                                        st.success(f"**Relevance Score: {score}/100** 🎯")
                                    elif score >= 60:
                                        st.warning(f"**Relevance Score: {score}/100** ⚡")
                                    else:
                                        st.error(f"**Relevance Score: {score}/100** 📈")
                                
                                with col2:
                                    verdict = analysis['verdict']
                                    if verdict == "High":
                                        st.success(f"**Verdict: {verdict}** 🟢")
                                    elif verdict == "Medium":
                                        st.warning(f"**Verdict: {verdict}** 🟡")
                                    else:
                                        st.error(f"**Verdict: {verdict}** 🔴")
                                
                                with col3:
                                    st.metric("Match Quality", f"{analysis['score_breakdown']['hard_match_score']:.1f}/10")
                                
                                # Missing elements
                                st.subheader("🎯 Gap Analysis")
                                missing = analysis.get("missing_elements", {})
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if missing.get("skills"):
                                        st.warning("**Missing Skills:**")
                                        for skill in missing["skills"][:5]:  # Show top 5
                                            st.write(f"🔸 {skill.title()}")
                                        if len(missing["skills"]) > 5:
                                            st.write(f"... and {len(missing['skills']) - 5} more skills")
                                    else:
                                        st.success("✅ **No missing skills identified**")
                                
                                with col2:
                                    if missing.get("certifications"):
                                        st.warning("**Missing Certifications:**")
                                        for cert in missing["certifications"][:3]:  # Show top 3
                                            st.write(f"🔸 {cert.title()}")
                                        if len(missing["certifications"]) > 3:
                                            st.write(f"... and {len(missing['certifications']) - 3} more certifications")
                                    else:
                                        st.success("✅ **No missing certifications identified**")
                                
                                # Improvement suggestions
                                st.subheader("💡 Personalized Improvement Suggestions")
                                suggestions = analysis.get("improvement_suggestions", [])
                                if suggestions:
                                    for i, suggestion in enumerate(suggestions[:5], 1):  # Show top 5
                                        st.info(f"**{i}.** {suggestion}")
                                    if len(suggestions) > 5:
                                        st.write(f"... and {len(suggestions) - 5} more suggestions")
                                else:
                                    st.info("🎯 **Great job!** No specific improvement suggestions at this time.")
                                
                                # Strengths
                                strengths = analysis.get("strengths", [])
                                if strengths:
                                    st.subheader("💪 Your Key Strengths")
                                    for i, strength in enumerate(strengths[:3], 1):  # Show top 3
                                        st.success(f"**{i}.** {strength}")
                                    if len(strengths) > 3:
                                        st.write(f"... and {len(strengths) - 3} more strengths")
                                
                                # Download results
                                st.subheader("📥 Download Application Report")
                                if st.button("📊 Download Report", key=f"download_{jd['id']}"):
                                    # Create report data
                                    report_data = {
                                        "Job Title": jd['title'],
                                        "Company": jd['company'],
                                        "Student Name": analysis.get("student_name", "Unknown"),
                                        "Relevance Score": analysis["relevance_score"],
                                        "Verdict": analysis["verdict"],
                                        "Missing Skills": "; ".join(missing.get("skills", [])[:5]),
                                        "Missing Certifications": "; ".join(missing.get("certifications", [])[:3]),
                                        "Improvement Suggestions": "; ".join(suggestions[:3])
                                    }
                                    
                                    import pandas as pd
                                    df = pd.DataFrame([report_data])
                                    csv = df.to_csv(index=False)
                                    
                                    st.download_button(
                                        label="📥 Download Report",
                                        data=csv,
                                        file_name=f"application_report_{jd['title'].replace(' ', '_')}.csv",
                                        mime="text/csv"
                                    )
                            else:
                                st.error("❌ Failed to evaluate application. Please try again.")
        else:
            st.warning("⚠️ No job positions available at the moment. Please check back later.")

def show_dashboard():
    """Show enhanced main dashboard with statistics and charts"""
    st.markdown('<h2 class="sub-header">🏠 Dashboard Overview</h2>', unsafe_allow_html=True)
    
    # Welcome message
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; border-radius: 12px; margin-bottom: 2rem;">
        <h3 style="margin: 0 0 0.5rem 0;">👋 Welcome to your Dashboard!</h3>
        <p style="margin: 0; opacity: 0.9;">Track your recruitment process with real-time analytics and insights.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get dashboard statistics
    stats = make_api_request("/dashboard/stats")
    
    if stats:
        # Display key metrics with enhanced cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card success-card">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📋</div>
                <div style="font-size: 2rem; font-weight: 700; color: #2c3e50; margin-bottom: 0.3rem;">{stats["total_resumes"]}</div>
                <div style="color: #7f8c8d; font-weight: 500;">Total Resumes</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card info-card">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📄</div>
                <div style="font-size: 2rem; font-weight: 700; color: #2c3e50; margin-bottom: 0.3rem;">{stats["total_job_descriptions"]}</div>
                <div style="color: #7f8c8d; font-weight: 500;">Job Descriptions</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card warning-card">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🎯</div>
                <div style="font-size: 2rem; font-weight: 700; color: #2c3e50; margin-bottom: 0.3rem;">{stats["total_evaluations"]}</div>
                <div style="color: #7f8c8d; font-weight: 500;">Total Evaluations</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            avg_score = stats["average_scores"]["relevance_score"]
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: #667eea;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📊</div>
                <div style="font-size: 2rem; font-weight: 700; color: #2c3e50; margin-bottom: 0.3rem;">{avg_score:.1f}%</div>
                <div style="color: #7f8c8d; font-weight: 500;">Avg Score</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Charts section
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Verdict Distribution")
            verdict_data = stats["verdict_distribution"]
            
            if verdict_data:
                fig = px.pie(
                    values=list(verdict_data.values()),
                    names=list(verdict_data.keys()),
                    color_discrete_map={
                        "High": "#28a745",
                        "Medium": "#ffc107", 
                        "Low": "#dc3545"
                    },
                    hole=0.4
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(
                    showlegend=True,
                    height=350,
                    margin=dict(t=0, b=0, l=0, r=0)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No evaluation data available yet.")
        
        with col2:
            st.markdown("### 📈 Match Score Breakdown")
            score_data = {
                'Score Type': ['Hard Match', 'Semantic Match'],
                'Average Score': [
                    stats['average_scores']['hard_match_score'],
                    stats['average_scores']['semantic_match_score']
                ]
            }
            fig = px.bar(
                score_data,
                x='Score Type',
                y='Average Score',
                color='Score Type',
                color_discrete_map={
                    'Hard Match': '#667eea',
                    'Semantic Match': '#764ba2'
                }
            )
            fig.update_layout(
                showlegend=False,
                height=350,
                margin=dict(t=0, b=0, l=0, r=0),
                yaxis_range=[0, 1]
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📤 Upload Files", use_container_width=True):
                st.session_state.current_page = 'upload'
                st.rerun()
        
        with col2:
            if st.button("🎯 Evaluate Resumes", use_container_width=True):
                st.session_state.current_page = 'evaluate'
                st.rerun()
        
        with col3:
            if st.button("📊 View Results", use_container_width=True):
                st.session_state.current_page = 'results'
                st.rerun()
        
        with col4:
            if st.button("🗂️ Manage Data", use_container_width=True):
                st.session_state.current_page = 'manage'
                st.rerun()
    
    else:
        st.error("❌ Could not load dashboard statistics. Please check your API connection.")
        st.info("💡 Make sure the backend server is running on: " + API_BASE_URL)

def show_upload_page():
    """Show enhanced file upload page"""
    st.markdown('<h2 class="sub-header">📤 Upload Files</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: #e8f4fd; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #17a2b8; margin-bottom: 2rem;">
        <strong>💡 Fully Automated Extraction</strong><br>
        Just upload your files - our AI will automatically extract all relevant information!
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for different upload types
    tab1, tab2 = st.tabs(["📄 Job Description", "📋 Resume"])
    
    with tab1:
        st.markdown("#### Upload Job Description")
        st.caption("For Placement Team: Upload JD and the system will extract requirements automatically")
        
        with st.form("upload_jd_form", clear_on_submit=True):
            jd_file = st.file_uploader(
                "Drop your job description file here",
                type=['pdf', 'docx', 'doc', 'txt'],
                key="jd_file",
                help="Supported formats: PDF, DOCX, TXT (Max 10MB)"
            )
            
            col1, col2 = st.columns([3, 1])
            with col2:
                submitted = st.form_submit_button("🚀 Upload & Parse", type="primary", use_container_width=True)
            
            if submitted and jd_file:
                form_data = {"title": "", "company": "", "location": ""}
                files = {"file": (jd_file.name, jd_file.getvalue(), jd_file.type)}
                
                with st.spinner("🤖 Analyzing job description..."):
                    result = make_api_request("/upload/job-description", "POST", form_data, files)
                
                if result:
                    st.success("✅ Job description uploaded successfully!")
                    
                    if "parsed_data" in result:
                        parsed = result["parsed_data"]
                        
                        st.markdown("#### 📋 Extracted Information")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown(f"""
                            <div class="metric-card">
                                <strong>Job Title:</strong><br>
                                <span style="font-size: 1.2rem; color: #667eea;">{parsed.get('job_title', 'Not detected')}</span>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown(f"""
                            <div class="metric-card">
                                <strong>Company:</strong><br>
                                <span style="font-size: 1.2rem; color: #667eea;">{parsed.get('company_info', {}).get('name', 'Not detected')}</span>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown(f"""
                            <div class="metric-card">
                                <strong>Location:</strong><br>
                                <span style="font-size: 1.2rem; color: #667eea;">{parsed.get('company_info', {}).get('location', 'Not detected')}</span>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown(f"""
                            <div class="metric-card success-card">
                                <strong>Skills Found:</strong><br>
                                <span style="font-size: 1.5rem; font-weight: 700;">{len(parsed.get('required_skills', []))}</span>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        if parsed.get("required_skills"):
                            st.markdown("#### 🎯 Key Skills Identified")
                            skills = parsed["required_skills"][:12]
                            
                            cols = st.columns(4)
                            for i, skill in enumerate(skills):
                                with cols[i % 4]:
                                    st.markdown(f"""
                                    <div style="background: #667eea; color: white; padding: 0.5rem 1rem; border-radius: 20px; text-align: center; margin: 0.3rem 0; font-size: 0.9rem;">
                                        {skill.title()}
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            if len(parsed["required_skills"]) > 12:
                                st.caption(f"... and {len(parsed['required_skills']) - 12} more skills")
    
    with tab2:
        st.markdown("#### Upload Resume")
        st.caption("For Students: Upload resume and the system will extract all information automatically")
        
        with st.form("upload_resume_form", clear_on_submit=True):
            resume_file = st.file_uploader(
                "Drop your resume file here",
                type=['pdf', 'docx', 'doc'],
                key="resume_file",
                help="Supported formats: PDF, DOCX (Max 10MB)"
            )
            
            col1, col2 = st.columns([3, 1])
            with col2:
                submitted = st.form_submit_button("🚀 Upload & Parse", type="primary", use_container_width=True)
            
            if submitted and resume_file:
                form_data = {"student_name": "", "student_email": ""}
                files = {"file": (resume_file.name, resume_file.getvalue(), resume_file.type)}
                
                with st.spinner("🤖 Analyzing resume..."):
                    result = make_api_request("/upload/resume", "POST", form_data, files)
                
                if result:
                    st.success("✅ Resume uploaded successfully!")
                    
                    if "parsed_data" in result:
                        parsed = result["parsed_data"]
                        
                        st.markdown("#### 📋 Extracted Information")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown(f"""
                            <div class="metric-card">
                                <strong>Name:</strong><br>
                                <span style="font-size: 1.2rem; color: #667eea;">{parsed.get('contact_info', {}).get('name', 'Not detected')}</span>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown(f"""
                            <div class="metric-card">
                                <strong>Email:</strong><br>
                                <span style="font-size: 1rem; color: #667eea;">{parsed.get('contact_info', {}).get('email', 'Not detected')}</span>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown(f"""
                            <div class="metric-card success-card">
                                <strong>Skills Found:</strong><br>
                                <span style="font-size: 1.5rem; font-weight: 700;">{len(parsed.get('skills', []))}</span>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown(f"""
                            <div class="metric-card info-card">
                                <strong>Experience:</strong><br>
                                <span style="font-size: 1.5rem; font-weight: 700;">{len(parsed.get('experience', []))}</span>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        if parsed.get("skills"):
                            st.markdown("#### 🛠️ Extracted Skills")
                            skills = parsed["skills"][:12]
                            
                            cols = st.columns(4)
                            for i, skill in enumerate(skills):
                                with cols[i % 4]:
                                    st.markdown(f"""
                                    <div style="background: #f093fb; color: white; padding: 0.5rem 1rem; border-radius: 20px; text-align: center; margin: 0.3rem 0; font-size: 0.9rem;">
                                        {skill.title()}
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            if len(parsed["skills"]) > 12:
                                st.caption(f"... and {len(parsed['skills']) - 12} more skills")

def show_evaluation_page():
    """Show evaluation page - matches exact workflow"""
    st.header("🎯 Evaluate Resumes")
    st.info("**Automated Evaluation**: Select a job description and resumes to evaluate. The system will automatically generate relevance scores, verdicts, and improvement suggestions.")
    
    # Get job descriptions and resumes
    jds_response = make_api_request("/job-descriptions")
    resumes_response = make_api_request("/resumes")
    
    if not jds_response or not resumes_response:
        st.error("Could not load data. Please upload job descriptions and resumes first.")
        return
    
    jds = jds_response.get("job_descriptions", [])
    resumes = resumes_response.get("resumes", [])
    
    if not jds:
        st.warning("⚠️ No job descriptions found. Please upload a job description first.")
        return
    
    if not resumes:
        st.warning("⚠️ No resumes found. Please upload resumes first.")
        return
    
    # Step 1: Select Job Description
    st.subheader("📄 Step 1: Select Job Description")
    jd_options = [f"{jd['title']} - {jd['company']} (ID: {jd['id']})" for jd in jds]
    selected_jd = st.selectbox("Choose a job description to evaluate against:", jd_options)
    
    if selected_jd:
        jd_id = int(selected_jd.split("ID: ")[1].split(")")[0])
        selected_jd_data = next(jd for jd in jds if jd['id'] == jd_id)
        
        # Show job description details
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Job Title", selected_jd_data['title'])
        with col2:
            st.metric("Company", selected_jd_data['company'])
        with col3:
            st.metric("Location", selected_jd_data['location'])
        
        # Step 2: Select Resumes to Evaluate
        st.subheader("📋 Step 2: Select Resumes to Evaluate")
        
        # Multi-select for resumes
        resume_options = [f"{resume['student_name']} - {resume['filename']} (ID: {resume['id']})" for resume in resumes]
        selected_resumes = st.multiselect(
            "Choose resumes to evaluate (you can select multiple):",
            resume_options,
            help="Select one or more resumes to evaluate against the job description"
        )
        
        if selected_resumes:
            # Step 3: Run Evaluation
            st.subheader("🚀 Step 3: Run Automated Evaluation")
            
            if st.button("🎯 Start Evaluation", type="primary"):
                evaluation_results = []
                
                # Progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, selected_resume in enumerate(selected_resumes):
                    resume_id = int(selected_resume.split("ID: ")[1].split(")")[0])
                    resume_name = selected_resume.split(" - ")[0]
                    
                    status_text.text(f"Evaluating {resume_name}...")
                    
                    # Make evaluation request
                    form_data = {
                        "resume_id": resume_id,
                        "job_description_id": jd_id
                    }
                    
                    result = make_api_request("/evaluate", "POST", form_data)
                    
                    if result and "analysis" in result:
                        evaluation_results.append({
                            "resume_name": resume_name,
                            "resume_id": resume_id,
                            "analysis": result["analysis"]
                        })
                    
                    # Update progress
                    progress_bar.progress((i + 1) / len(selected_resumes))
                
                status_text.text("✅ Evaluation completed!")
                
                # Step 4: Show Results
                if evaluation_results:
                    st.subheader("📊 Step 4: Evaluation Results")
                    
                    # Sort by relevance score
                    evaluation_results.sort(key=lambda x: x["analysis"]["relevance_score"], reverse=True)
                    
                    # Show summary
                    st.success(f"✅ Successfully evaluated {len(evaluation_results)} resumes!")
                    
                    # Display results
                    for i, result in enumerate(evaluation_results):
                        analysis = result["analysis"]
                        
                        # Create expandable section for each result
                        with st.expander(f"#{i+1} {result['resume_name']} - Score: {analysis['relevance_score']}/100 - {analysis['verdict']} Fit", expanded=(i==0)):
                            
                            # Score and verdict
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Relevance Score", f"{analysis['relevance_score']}/100")
                            with col2:
                                verdict_color = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}
                                st.metric("Verdict", f"{verdict_color.get(analysis['verdict'], '⚪')} {analysis['verdict']}")
                            with col3:
                                st.metric("Hard Match", f"{analysis['score_breakdown']['hard_match_score']:.2f}")
                            with col4:
                                st.metric("Semantic Match", f"{analysis['score_breakdown']['semantic_match_score']:.2f}")
                            
                            # Missing elements
                            st.subheader("🎯 Gap Analysis")
                            missing = analysis.get("missing_elements", {})
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if missing.get("skills"):
                                    st.write("**Missing Skills:**")
                                    for skill in missing["skills"][:5]:  # Show top 5
                                        st.write(f"• {skill}")
                                else:
                                    st.write("✅ **No missing skills identified**")
                            
                            with col2:
                                if missing.get("certifications"):
                                    st.write("**Missing Certifications:**")
                                    for cert in missing["certifications"][:3]:  # Show top 3
                                        st.write(f"• {cert}")
                                else:
                                    st.write("✅ **No missing certifications identified**")
                            
                            # Improvement suggestions
                            st.subheader("💡 Personalized Improvement Suggestions")
                            suggestions = analysis.get("improvement_suggestions", [])
                            if suggestions:
                                for suggestion in suggestions[:3]:  # Show top 3
                                    st.write(f"• {suggestion}")
                            else:
                                st.write("No specific suggestions available.")
                            
                            # Strengths
                            strengths = analysis.get("strengths", [])
                            if strengths:
                                st.subheader("💪 Key Strengths")
                                for strength in strengths[:3]:  # Show top 3
                                    st.write(f"• {strength}")
                    
                    # Download results
                    st.subheader("📥 Download Results")
                    if st.button("📊 Export Results to CSV"):
                        # Create CSV data
                        csv_data = []
                        for result in evaluation_results:
                            analysis = result["analysis"]
                            csv_data.append({
                                "Student Name": result["resume_name"],
                                "Relevance Score": analysis["relevance_score"],
                                "Verdict": analysis["verdict"],
                                "Missing Skills": "; ".join(analysis.get("missing_elements", {}).get("skills", [])[:5]),
                                "Improvement Suggestions": "; ".join(analysis.get("improvement_suggestions", [])[:3])
                            })
                        
                        import pandas as pd
                        df = pd.DataFrame(csv_data)
                        csv = df.to_csv(index=False)
                        
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv,
                            file_name=f"evaluation_results_{selected_jd_data['title'].replace(' ', '_')}.csv",
                            mime="text/csv"
                        )

def show_results_page():
    """Show evaluation results page"""
    st.header("📊 Evaluation Results")
    
    # Get job descriptions for filtering
    jds_response = make_api_request("/job-descriptions")
    jds = jds_response.get("job_descriptions", []) if jds_response else []
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        jd_options = ["All"] + jds
        jd_filter = st.selectbox(
            "Filter by Job Description",
            jd_options,
            format_func=lambda jd: jd if jd == "All" else f"{jd.get('title', 'Untitled')} - {jd.get('company', 'Unknown')}",
            key="jd_filter"
        )
    
    with col2:
        verdict_filter = st.selectbox(
            "Filter by Verdict",
            ["All", "High", "Medium", "Low"],
            key="verdict_filter"
        )
    
    with col3:
        min_score = st.slider(
            "Minimum Score",
            min_value=0,
            max_value=100,
            value=0,
            key="min_score"
        )
    
    # Get results
    params = {}
    if isinstance(jd_filter, dict):
        params["job_description_id"] = jd_filter.get("id")
    
    if verdict_filter != "All":
        params["verdict"] = verdict_filter
    
    if min_score > 0:
        params["min_score"] = min_score
    
    # Build query string
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    endpoint = f"/results?{query_string}" if query_string else "/results"
    
    results_response = make_api_request(endpoint)
    
    if results_response and results_response.get("results"):
        results = results_response["results"]
        
        # Display results in a table
        st.subheader(f"📋 Results ({len(results)} found)")
        
        # Create DataFrame
        df = pd.DataFrame(results)
        
        # Format the DataFrame for display
        display_df = df[["student_name", "job_title", "company", "relevance_score", "verdict", "evaluation_date"]].copy()
        display_df.columns = ["Student", "Job Title", "Company", "Score", "Verdict", "Date"]
        display_df["Score"] = display_df["Score"].astype(str) + "%"
        
        # Color code verdicts
        def color_verdict(val):
            if val == "High":
                return "background-color: #d4edda; color: #155724"
            elif val == "Medium":
                return "background-color: #fff3cd; color: #856404"
            elif val == "Low":
                return "background-color: #f8d7da; color: #721c24"
            return ""
        
        styled_df = display_df.style.applymap(color_verdict, subset=["Verdict"])
        st.dataframe(styled_df, use_container_width=True)
        
        # Detailed view
        st.subheader("🔍 Detailed Analysis")
        
        selected_idx = st.selectbox(
            "Select a result to view details",
            range(len(results)),
            format_func=lambda x: f"{results[x]['student_name']} - {results[x]['job_title']} ({results[x]['relevance_score']}%)"
        )
        
        if selected_idx is not None:
            selected_result = results[selected_idx]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Relevance Score", f"{selected_result['relevance_score']}%")
                st.metric("Verdict", selected_result['verdict'])
                st.metric("Hard Match Score", f"{selected_result['hard_match_score']:.2f}")
                st.metric("Semantic Match Score", f"{selected_result['semantic_match_score']:.2f}")
            
            with col2:
                st.subheader("Missing Skills")
                missing_skills = selected_result.get("missing_skills", [])
                if missing_skills:
                    for skill in missing_skills[:5]:  # Show top 5
                        st.write(f"• {skill}")
                else:
                    st.write("No missing skills identified")
                
                st.subheader("Improvement Suggestions")
                suggestions = selected_result.get("improvement_suggestions", [])
                if suggestions:
                    for suggestion in suggestions[:3]:  # Show top 3
                        st.write(f"• {suggestion}")
                else:
                    st.write("No suggestions available")
    
    else:
        st.info("No evaluation results found. Upload some resumes and job descriptions to get started.")

def show_manage_page():
    """Show data management page"""
    st.header("🗂️ Data Management")
    
    # Create tabs
    tab1, tab2 = st.tabs(["📋 Resumes", "📄 Job Descriptions"])
    
    with tab1:
        st.subheader("Uploaded Resumes")
        
        resumes_response = make_api_request("/resumes")
        if resumes_response and resumes_response.get("resumes"):
            resumes = resumes_response["resumes"]
            
            # Create DataFrame
            df = pd.DataFrame(resumes)
            df["upload_date"] = pd.to_datetime(df["upload_date"]).dt.strftime("%Y-%m-%d %H:%M")
            
            # Display table
            st.dataframe(df, use_container_width=True)
            
            # Summary statistics
            st.subheader("📊 Resume Statistics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Resumes", len(resumes))
            
            with col2:
                unique_skills = set()
                for resume in resumes:
                    unique_skills.update(resume.get("skills", []))
                st.metric("Unique Skills", len(unique_skills))
            
            with col3:
                recent_uploads = len([r for r in resumes if pd.to_datetime(r["upload_date"]) > datetime.now() - timedelta(days=7)])
                st.metric("Uploads (Last 7 days)", recent_uploads)
        
        else:
            st.info("No resumes uploaded yet.")
    
    with tab2:
        st.subheader("Uploaded Job Descriptions")
        
        jds_response = make_api_request("/job-descriptions")
        if jds_response and jds_response.get("job_descriptions"):
            jds = jds_response["job_descriptions"]
            
            # Create DataFrame
            df = pd.DataFrame(jds)
            df["upload_date"] = pd.to_datetime(df["upload_date"]).dt.strftime("%Y-%m-%d %H:%M")
            
            # Display table
            st.dataframe(df, use_container_width=True)
            
            # Summary statistics
            st.subheader("📊 Job Description Statistics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Job Descriptions", len(jds))
            
            with col2:
                unique_companies = len(set(jd["company"] for jd in jds if jd["company"]))
                st.metric("Unique Companies", unique_companies)
            
            with col3:
                recent_uploads = len([jd for jd in jds if pd.to_datetime(jd["upload_date"]) > datetime.now() - timedelta(days=7)])
                st.metric("Uploads (Last 7 days)", recent_uploads)
        
        else:
            st.info("No job descriptions uploaded yet.")

if __name__ == "__main__":
    main()
