import streamlit as st
import pandas as pd
import json
import os
import random
from datetime import datetime, timedelta
import anthropic
import time
from dotenv import load_dotenv
import re
import io

# Load environment variables from .env file if present
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="LinkedIn AI Networking Assistant",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to initialize Claude API client
def initialize_claude_client():
    api_key = st.session_state.get("CLAUDE_API_KEY", "")
    if not api_key:
        return None
    try:
        client = anthropic.Anthropic(api_key=api_key)
        return client
    except Exception as e:
        st.error(f"Error initializing Claude client: {e}")
        return None

# Initialize session state
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.active_tab = "import"
    st.session_state.linkedin_connections = []
    st.session_state.selected_contact = None
    st.session_state.generated_message = ""
    st.session_state.message_type = "coldOutreach"
    st.session_state.networking_goal = "Career Advancement"
    st.session_state.custom_goal = ""
    st.session_state.custom_topic = ""
    st.session_state.recommendations = []
    st.session_state.current_page = 0  # For recommendation pagination
    st.session_state.results_per_page = 5  # Number of recommendations per page
    st.session_state.CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
    st.session_state.profile_uploaded = False
    st.session_state.connections_uploaded = False
    st.session_state.user_profile = {
        "name": "",
        "firstName": "",
        "lastName": "",
        "headline": "",
        "industry": "",
        "summary": "",
        "location": ""
    }

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2rem !important;
        font-weight: 600;
        color: #0A66C2;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem !important;
        font-weight: 500;
        color: #0A66C2;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: white;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        margin-bottom: 1rem;
    }
    .contact-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: white;
        border: 1px solid #E5E7EB;
        margin-bottom: 0.5rem;
        cursor: pointer;
    }
    .contact-card:hover {
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
    }
    .contact-card.selected {
        border: 1px solid #0A66C2;
        background-color: #E8F0FE;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        font-size: 0.75rem;
        font-weight: 500;
        border-radius: 9999px;
    }
    .badge-blue {
        background-color: #E8F0FE;
        color: #0A66C2;
    }
    .badge-green {
        background-color: #D1FAE5;
        color: #065F46;
    }
    .badge-gray {
        background-color: #F3F4F6;
        color: #374151;
    }
    .divider {
        height: 1px;
        background-color: #E5E7EB;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
    }
    .contact-detail {
        margin-bottom: 0.5rem;
    }
    .contact-detail-label {
        font-weight: 600;
        color: #4B5563;
    }
    .message-area {
        border: 1px solid #E5E7EB;
        border-radius: 0.375rem;
        padding: 0.75rem;
        min-height: 200px;
        margin-bottom: 1rem;
        background-color: #F9FAFB;
    }
    .custom-tab {
        padding: 0.5rem 1rem;
        font-weight: 500;
        border-bottom: 2px solid transparent;
        cursor: pointer;
    }
    .custom-tab:hover {
        color: #0A66C2;
    }
    .custom-tab.active {
        color: #0A66C2;
        border-bottom: 2px solid #0A66C2;
    }
    .api-info {
        padding: 0.5rem;
        background-color: #F3F4F6;
        border-radius: 0.375rem;
        font-size: 0.8rem;
        margin-top: 0.5rem;
    }
    .upload-card {
        border: 1px dashed #0A66C2;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin: 1rem 0;
        text-align: center;
    }
    .success-card {
        background-color: #D1FAE5;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Helper Functions for CSV processing
def process_profile_csv(file):
    """Process LinkedIn Profile.csv file with robust error handling"""
    try:
        # Try multiple parsing approaches
        try:
            # First attempt: Standard parsing
            df = pd.read_csv(
                file,
                encoding='utf-8',
                on_bad_lines='warn',
                quotechar='"',
                escapechar='\\',
                low_memory=False,
                skipinitialspace=True
            )
        except Exception as e1:
            # Second attempt: Try with python engine
            try:
                file.seek(0)
                df = pd.read_csv(
                    file,
                    encoding='utf-8',
                    delimiter=',',
                    engine='python',
                    on_bad_lines='skip',
                    quoting=3,  # QUOTE_NONE
                    skipinitialspace=True
                )
            except Exception as e2:
                # Third attempt: Try different encoding
                try:
                    file.seek(0)
                    df = pd.read_csv(
                        file,
                        encoding='latin-1',
                        delimiter=',',
                        engine='python',
                        on_bad_lines='skip'
                    )
                except Exception as e3:
                    # Last attempt: Manual parsing
                    file.seek(0)
                    content = file.read().decode('utf-8', errors='replace')
                    
                    # Try to find key profile fields manually
                    first_name = extract_field(content, "First Name")
                    last_name = extract_field(content, "Last Name")
                    headline = extract_field(content, "Headline")
                    industry = extract_field(content, "Industry")
                    location = extract_field(content, "Geo Location")
                    summary = extract_field(content, "Summary")
                    
                    if first_name or last_name:
                        return {
                            "firstName": first_name,
                            "lastName": last_name,
                            "name": f"{first_name} {last_name}".strip(),
                            "headline": headline,
                            "summary": summary,
                            "industry": industry,
                            "location": location
                        }
                    else:
                        raise Exception("Could not extract profile data from the file")
        
        # Show a preview of the processed data
        with st.expander("Preview of imported profile data"):
            st.write("Profile data preview:")
            st.dataframe(df.head())
        
        # Normalize column names
        df.columns = [col.strip().title() for col in df.columns]
        
        # Map common variations to standard names
        column_mapping = {
            'First': 'First Name',
            'Last': 'Last Name',
            'Geo Location': 'Location',
            'Geo': 'Location',
            'Profile Summary': 'Summary',
            'About': 'Summary'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns and new_col not in df.columns:
                df = df.rename(columns={old_col: new_col})
        
        if len(df) > 0:
            # Extract first row since there should be only one profile
            profile_row = df.iloc[0]
            
            # Safely extract fields
            user_profile = {
                "firstName": str(profile_row.get('First Name', '')) if hasattr(profile_row, 'get') else str(profile_row['First Name']) if 'First Name' in profile_row.index else '',
                "lastName": str(profile_row.get('Last Name', '')) if hasattr(profile_row, 'get') else str(profile_row['Last Name']) if 'Last Name' in profile_row.index else '',
                "headline": str(profile_row.get('Headline', '')) if hasattr(profile_row, 'get') else str(profile_row['Headline']) if 'Headline' in profile_row.index else '',
                "summary": str(profile_row.get('Summary', '')) if hasattr(profile_row, 'get') else str(profile_row['Summary']) if 'Summary' in profile_row.index else '',
                "industry": str(profile_row.get('Industry', '')) if hasattr(profile_row, 'get') else str(profile_row['Industry']) if 'Industry' in profile_row.index else '',
                "location": str(profile_row.get('Location', '')) if hasattr(profile_row, 'get') else str(profile_row['Location']) if 'Location' in profile_row.index else \
                           str(profile_row.get('Geo Location', '')) if hasattr(profile_row, 'get') else str(profile_row['Geo Location']) if 'Geo Location' in profile_row.index else ''
            }
            
            # Ensure name is properly set
            user_profile["name"] = f"{user_profile['firstName']} {user_profile['lastName']}".strip()
            
            return user_profile
        else:
            st.error("Profile CSV file is empty or does not contain valid data")
            return None
            
    except Exception as e:
        st.error(f"Error processing profile CSV: {str(e)}")
        
        # Additional debugging information
        st.expander("Debugging Information").write(f"""
        Error type: {type(e).__name__}
        Error details: {str(e)}
        
        Common issues:
        - CSV file format may not match expected LinkedIn export format
        - Special characters or formatting issues in the file
        - Missing required columns (First Name, Last Name)
        
        Try exporting your profile data again from LinkedIn, or check the file for formatting issues.
        """)
        
        return None

def extract_field(content, field_name):
    """Extract a field from CSV content using regex pattern matching"""
    pattern = re.compile(f"{field_name}[,:]\\s*([^,\\n]+)")
    match = pattern.search(content)
    if match:
        return match.group(1).strip().strip('"')
    return ""

def process_connections_csv(file):
    """Process LinkedIn Connections.csv file with robust error handling"""
    try:
        # Try multiple parsing approaches to handle LinkedIn's inconsistent CSV format
        try:
            # First attempt: Use pandas with more flexible parsing options
            df = pd.read_csv(
                file,
                encoding='utf-8',
                on_bad_lines='warn',  # Don't fail on problematic lines
                quotechar='"',        # Handle quoted fields properly
                escapechar='\\',      # Handle escape sequences
                low_memory=False,     # Avoid mixed type inference issues
                skipinitialspace=True # Skip spaces after delimiter
            )
        except Exception as e1:
            # Second attempt: Try with explicit delimiter and engine
            try:
                # Reset file position
                file.seek(0)
                df = pd.read_csv(
                    file,
                    encoding='utf-8',
                    delimiter=',',
                    engine='python',  # More flexible but slower engine
                    on_bad_lines='skip',
                    quoting=3,  # QUOTE_NONE
                    skipinitialspace=True
                )
            except Exception as e2:
                # Third attempt: Try reading with different encoding
                try:
                    file.seek(0)
                    df = pd.read_csv(
                        file,
                        encoding='latin-1',  # Try alternate encoding
                        delimiter=',', 
                        engine='python',
                        on_bad_lines='skip'
                    )
                except Exception as e3:
                    # Last attempt: Try to manually read and parse the file
                    file.seek(0)
                    content = file.read().decode('utf-8', errors='replace')
                    
                    # Save content to StringIO for pandas to read
                    string_data = io.StringIO(content)
                    
                    # Try to find the header row and parse from there
                    lines = content.split('\n')
                    header_idx = -1
                    
                    # Look for a row that likely contains the header
                    for i, line in enumerate(lines):
                        if 'First Name' in line and 'Last Name' in line and 'Email' in line:
                            header_idx = i
                            break
                    
                    if header_idx >= 0:
                        # Create a new StringIO with just the header and data
                        clean_content = '\n'.join(lines[header_idx:])
                        clean_data = io.StringIO(clean_content)
                        df = pd.read_csv(clean_data, on_bad_lines='skip')
                    else:
                        raise Exception("Could not identify header row in the CSV file")
        
        # Check if we have the minimum required columns
        required_columns = ["First Name", "Last Name"]
        
        # Normalize column names by stripping whitespace and converting to title case
        df.columns = [col.strip().title() for col in df.columns]
        
        # Check for required columns with normalized names
        normalized_required = [col.strip().title() for col in required_columns]
        missing_columns = [col for col in normalized_required if col not in df.columns]
        
        if missing_columns:
            # Try to find columns with similar names
            for missing in missing_columns:
                for col in df.columns:
                    # Check if the column name contains the required name (e.g. "First Name" in "First Name ")
                    if missing.lower() in col.lower():
                        # Rename the column to the standard name
                        df = df.rename(columns={col: missing})
        
        # Recheck after attempted fixes
        missing_columns = [col for col in normalized_required if col not in df.columns]
        if missing_columns:
            st.error(f"CSV file is missing required columns: {', '.join(missing_columns)}")
            st.write("Available columns:", ", ".join(df.columns))
            return []

        # Show a preview of the data
        with st.expander("Preview of imported connections data"):
            st.write("First 5 rows of your connections data:")
            st.dataframe(df.head())
            st.write(f"Total connections found: {len(df)}")
        
        # Map common column variations to standard names
        column_mapping = {
            'First': 'First Name',
            'Last': 'Last Name',
            'E-Mail Address': 'Email Address',
            'Email': 'Email Address',
            'Position Title': 'Position',
            'Company Name': 'Company',
            'Connection Date': 'Connected On'
        }
        
        # Apply column mapping where needed
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns and new_col not in df.columns:
                df = df.rename(columns={old_col: new_col})
        
        # Process the connections
        connections = []
        
        for idx, row in df.iterrows():
            # Define expected columns and their fallbacks with safe accessor
            first_name = row.get('First Name', '') if hasattr(row, 'get') else str(row.get('First Name', '')) if 'First Name' in row.index else ''
            last_name = str(row.get('Last Name', '')) if hasattr(row, 'get') else str(row.get('Last Name', '')) if 'Last Name' in row.index else ''
            
            # Handle various email column names
            email = ''
            for email_col in ['Email Address', 'Email', 'E-Mail Address']:
                if email_col in row.index:
                    email = str(row.get(email_col, ''))
                    break
            
            # Handle various company column names
            company = ''
            for company_col in ['Company', 'Company Name', 'Organization']:
                if company_col in row.index:
                    company = str(row.get(company_col, ''))
                    break
            
            # Handle various position column names
            position = ''
            for position_col in ['Position', 'Position Title', 'Title', 'Headline']:
                if position_col in row.index:
                    position = str(row.get(position_col, ''))
                    break
            
            # Handle various connection date column names
            connected_on = ''
            for date_col in ['Connected On', 'Connection Date', 'Connected']:
                if date_col in row.index:
                    connected_on = str(row.get(date_col, ''))
                    break
            
            # Skip rows with empty first and last name (likely header or malformed rows)
            if not first_name.strip() and not last_name.strip():
                continue
                
            # Create connection object with additional fields for our app
            connection = {
                "id": str(idx),
                "firstName": first_name,
                "lastName": last_name,
                "fullName": f"{first_name} {last_name}".strip(),
                "email": email,
                "company": company,
                "role": position,
                # Generate some additional fields with reasonable defaults
                "industry": extract_industry(company, position),
                "expertise": extract_expertise(position),
                "seniority": extract_seniority(position),
                "companySize": "Unknown",
                "activityLevel": random.choice(["Low", "Medium", "High"]),
                "recentProjects": "",
                "keyAchievements": "",
                "connectedDate": connected_on,
                "mutualConnections": random.randint(0, 5),
            }
            connections.append(connection)
        
        return connections
    except Exception as e:
        st.error(f"Error processing connections CSV: {str(e)}")
        
        # Additional debugging information
        st.expander("Debugging Information").write(f"""
        Error type: {type(e).__name__}
        Error details: {str(e)}
        
        Common issues:
        - CSV file format may not match expected LinkedIn export format
        - Special characters or formatting issues in the file
        - Missing required columns (First Name, Last Name)
        
        Try exporting your connections data again from LinkedIn, or check the file for formatting issues.
        """)
        
        return []

def extract_industry(company, position):
    """Extract likely industry based on company name and position"""
    # This is a very simplified version - in a real app, you would use NLP or a database
    
    # Check for common industry keywords in company and position
    text = (company + " " + position).lower()
    
    if any(tech in text for tech in ["tech", "software", "digital", "app", "data", "it ", "computer", "cyber", "web", "cloud"]):
        return "Technology"
    elif any(fin in text for fin in ["bank", "finance", "capital", "financial", "invest", "asset", "wealth", "insurance"]):
        return "Finance"
    elif any(health in text for health in ["health", "medical", "hospital", "pharma", "biotech", "care", "clinic"]):
        return "Healthcare"
    elif any(edu in text for edu in ["university", "college", "school", "education", "academic", "learning", "teaching"]):
        return "Education"
    elif any(mkt in text for mkt in ["marketing", "advertis", "media", "digital", "brand", "content", "creative"]):
        return "Marketing"
    elif any(retail in text for retail in ["retail", "shop", "store", "ecommerce", "commerce", "consumer"]):
        return "Retail"
    else:
        return "Other"

def extract_expertise(position):
    """Extract expertise areas based on job position"""
    # This is a simplified version - in a real app, you would use more sophisticated NLP
    
    position_lower = position.lower()
    
    # Check for engineering/technical roles
    if any(eng in position_lower for eng in ["engineer", "developer", "architect", "programmer"]):
        if "software" in position_lower or "web" in position_lower:
            return "Software Development, Engineering"
        elif "data" in position_lower:
            return "Data Engineering, Analytics"
        elif "cloud" in position_lower:
            return "Cloud Infrastructure, DevOps"
        else:
            return "Engineering, Technical Development"
    
    # Check for data/analytics roles
    elif any(data in position_lower for data in ["data", "analytics", "analyst", "scientist"]):
        return "Data Analysis, Business Intelligence"
    
    # Check for design roles
    elif any(design in position_lower for design in ["design", "ux", "ui", "user experience"]):
        return "UX/UI Design, Product Design"
    
    # Check for product roles
    elif any(product in position_lower for product in ["product manager", "product owner"]):
        return "Product Management, Strategy"
    
    # Check for marketing roles
    elif any(mkt in position_lower for mkt in ["market", "brand", "content", "seo", "growth"]):
        return "Marketing, Branding, Growth"
    
    # Check for sales roles
    elif any(sales in position_lower for sales in ["sales", "account", "business development"]):
        return "Sales, Business Development"
    
    # Check for management roles
    elif any(mgmt in position_lower for mgmt in ["manager", "director", "head of", "lead"]):
        return "Management, Leadership"
    
    else:
        return "Professional Services"

def extract_seniority(position):
    """Extract seniority level based on job position"""
    position_lower = position.lower()
    
    if any(exec_title in position_lower for exec_title in ["ceo", "cto", "cfo", "coo", "chief", "president", "founder"]):
        return "C-Suite"
    elif any(vp in position_lower for vp in ["vp", "vice president"]):
        return "VP"
    elif any(dir in position_lower for dir in ["director", "head of"]):
        return "Director"
    elif any(mgr in position_lower for mgr in ["manager", "lead", "principal"]):
        return "Manager"
    elif any(senior in position_lower for senior in ["senior", "sr.", "staff"]):
        return "Senior"
    elif any(junior in position_lower for junior in ["junior", "jr.", "associate"]):
        return "Entry Level"
    elif any(intern in position_lower for intern in ["intern", "trainee"]):
        return "Intern"
    else:
        return "Mid Level"

# Helper Functions
def generate_recommendations(count=30):
    """Generate AI-powered contact recommendations"""
    if not st.session_state.linkedin_connections:
        return []
    
    scored_contacts = []
    
    for contact in st.session_state.linkedin_connections:
        # Generate a score based on industry match, seniority, and networking goal
        base_score = 50  # Base score
        
        # Industry match bonus
        if contact.get("industry") == st.session_state.user_profile.get("industry"):
            base_score += 20
        
        # Seniority bonus based on networking goal
        if st.session_state.networking_goal == "Career Advancement" and contact.get("seniority") in ["Senior", "Manager", "Director", "VP"]:
            base_score += 15
        elif st.session_state.networking_goal == "Industry Knowledge" and contact.get("seniority") in ["Senior", "Manager", "Director"]:
            base_score += 15
        elif st.session_state.networking_goal == "Business Development" and contact.get("seniority") in ["Manager", "Director", "VP", "C-Suite"]:
            base_score += 15
        elif st.session_state.networking_goal == "Job Seeking" and contact.get("seniority") in ["Manager", "Director", "VP"]:
            base_score += 20
        
        # Activity level bonus
        if contact.get("activityLevel") == "High":
            base_score += 10
        
        # Mutual connections bonus
        base_score += min(contact.get("mutualConnections", 0) * 3, 15)
        
        # Custom goal bonus (if specified)
        custom_goal = st.session_state.get("custom_goal", "").lower()
        if custom_goal:
            # Check if custom goal terms are present in contact fields
            goal_terms = [term.strip() for term in custom_goal.split() if len(term.strip()) > 3]
            
            for term in goal_terms:
                # Check various fields for the term
                term_found = False
                for field in ["industry", "expertise", "role", "company"]:
                    if term in str(contact.get(field, "")).lower():
                        base_score += 15
                        term_found = True
                        break
                
                if term_found:
                    break  # Only apply bonus once per contact
        
        # Add some randomness
        score = min(max(base_score + random.randint(-5, 5), 40), 95)
        
        # Generate insights based on networking goal
        insights = []
        
        # Common insights for all goals
        if contact.get("industry") == st.session_state.user_profile.get("industry"):
            insights.append(f"Same industry ({contact.get('industry')})")
        
        if contact.get("mutualConnections", 0) > 0:
            insights.append(f"{contact.get('mutualConnections')} mutual connections")
        
        # Goal-specific insights
        if st.session_state.networking_goal == "Career Advancement":
            if contact.get("seniority") in ["Senior", "Manager", "Director", "VP"]:
                insights.append(f"Senior position ({contact.get('seniority')}) for career guidance")
            
            if contact.get("expertise") and st.session_state.user_profile.get("headline") and any(exp in st.session_state.user_profile.get("headline") for exp in contact.get("expertise").split(",")):
                insights.append(f"Shares your expertise in {contact.get('expertise').split(',')[0]}")
        
        elif st.session_state.networking_goal == "Industry Knowledge":
            if contact.get("expertise"):
                expertise = contact.get("expertise").split(",")[0].strip() if "," in contact.get("expertise") else contact.get("expertise")
                insights.append(f"Expert in {expertise}")
        
        elif st.session_state.networking_goal == "Business Development":
            if contact.get("seniority") in ["Manager", "Director", "VP", "C-Suite"]:
                insights.append(f"Decision maker ({contact.get('seniority')})")
            
            if contact.get("companySize") in ["Large", "Enterprise"]:
                insights.append(f"Works at {contact.get('companySize')} company")
        
        elif st.session_state.networking_goal == "Job Seeking":
            if contact.get("seniority") in ["Manager", "Director", "VP"]:
                insights.append(f"Hiring authority ({contact.get('seniority')})")
            
            if contact.get("company"):
                insights.append(f"Works at target company ({contact.get('company')})")
        
        # Custom goal insights
        if custom_goal:
            for field in ["industry", "expertise", "role", "company"]:
                value = contact.get(field, "")
                if value and any(term.lower() in value.lower() for term in goal_terms if len(term) > 3):
                    insights.append(f"Matches your goal: {value}")
                    break
        
        # Fill with more generic insights if needed
        if len(insights) < 2:
            potential_insights = [
                f"Experienced in {contact.get('expertise').split(',')[0] if contact.get('expertise') and ',' in contact.get('expertise') else contact.get('expertise', 'professional skills')}",
                f"Works at {contact.get('company', 'a company')}",
                f"{contact.get('seniority', 'Professional')} level position",
                f"Connected on {contact.get('connectedDate', 'LinkedIn')}"
            ]
            insights.extend(random.sample(potential_insights, min(2, len(potential_insights))))
        
        # Take only the top 3 insights
        insights = insights[:3]
        
        # Determine match strength
        if score >= 80:
            match_strength = "Exceptional Match"
        elif score >= 65:
            match_strength = "Strong Match"
        elif score >= 50:
            match_strength = "Good Match"
        else:
            match_strength = "Moderate Match"
        
        # Create a recommendation object
        recommendation = {
            **contact,
            "score": score,
            "insights": insights,
            "matchStrength": match_strength
        }
        
        scored_contacts.append(recommendation)
    
    # Sort by score and return top recommendations
    return sorted(scored_contacts, key=lambda x: x["score"], reverse=True)[:count]

def generate_conversation_starters(contact):
    """Generate conversation starters for a contact"""
    starters = []
    
    # Get custom goal if set
    custom_goal = st.session_state.get("custom_goal", "").lower()
    
    # Based on custom goal if set
    if custom_goal:
        goal_terms = [term.strip() for term in custom_goal.split() if len(term.strip()) > 3]
        for term in goal_terms:
            for field in ["industry", "expertise", "role", "company"]:
                if contact.get(field) and term in contact.get(field).lower():
                    starters.append(f"I noticed your background in {contact.get(field)}. I'm particularly focused on {custom_goal} right now, and would value your perspective on this area.")
                    break
    
    # Based on connected date
    if contact.get("connectedDate"):
        starters.append(f"We've been connected since {contact.get('connectedDate')}. I've been following your career journey and I'm impressed with your work at {contact.get('company', 'your company')}.")
    
    # Based on shared industry
    if contact.get("industry") == st.session_state.user_profile.get("industry"):
        industry = contact.get("industry")
        industry_topics = {
            "Technology": ["AI advancements", "remote work technologies", "cybersecurity trends"],
            "Finance": ["fintech innovations", "sustainable investing", "regulatory changes"],
            "Retail": ["omnichannel strategies", "customer retention", "logistics optimization"],
            "Healthcare": ["telehealth adoption", "patient experience", "healthcare innovation"]
        }
        topics = industry_topics.get(industry, ["industry innovations", "current challenges", "future trends"])
        topic = random.choice(topics)
        starters.append(f"As fellow professionals in {industry}, I'm curious about your thoughts on {topic}.")
    
    # Based on role/expertise
    if contact.get("role") and contact.get("expertise"):
        expertise = contact.get("expertise").split(",")[0].strip() if "," in contact.get("expertise") else contact.get("expertise")
        starters.append(f"Your experience as a {contact.get('role')} with expertise in {expertise} is impressive. What projects in this area have you found most fulfilling?")
    
    # Based on mutual connections
    if contact.get("mutualConnections", 0) > 0:
        starters.append(f"I noticed we have {contact.get('mutualConnections')} mutual connections. The professional community is smaller than it seems!")
    
    # Add goal-specific starters
    if st.session_state.networking_goal == "Career Advancement":
        starters.append(f"I'm focusing on advancing my career in {contact.get('industry', 'our industry')}. What helped you reach your current position as {contact.get('role', 'a professional')}?")
    
    elif st.session_state.networking_goal == "Industry Knowledge":
        expertise = contact.get("expertise", "professional expertise").split(",")[0].strip() if contact.get("expertise") and "," in contact.get("expertise") else contact.get("expertise", "your field")
        starters.append(f"I'm working to deepen my understanding of {expertise}. What resources or practices have been most valuable for your development in this area?")
    
    elif st.session_state.networking_goal == "Business Development":
        starters.append(f"I'm exploring potential synergies between organizations in our space. Would you be open to discussing how {contact.get('company', 'your company')} approaches partnerships?")
    
    elif st.session_state.networking_goal == "Job Seeking":
        starters.append(f"I'm currently exploring new opportunities in {contact.get('industry', 'our industry')}. Would you have any insights on what {contact.get('company', 'companies in this space')} values most in candidates?")
    
    # Add generic starters if we don't have enough
    generic_starters = [
        "What's the most interesting project you've worked on recently?",
        f"What aspect of your work in {contact.get('industry', 'your field')} do you find most fulfilling?",
        f"How did you first become interested in {contact.get('industry', 'your field')}?",
        f"What's one challenge in {contact.get('industry', 'the industry')} that isn't getting enough attention?",
        f"What skills do you think will be most important for professionals in {contact.get('industry', 'our field')} in the next few years?"
    ]
    
    while len(starters) < 3:
        starter = random.choice(generic_starters)
        if starter not in starters:
            starters.append(starter)
    
    return starters[:3]

def generate_basic_message(contact, template_type="coldOutreach", custom_topic=""):
    """Generate a basic outreach message without using Claude AI"""
    # Create a replacement dictionary
    replacements = {
        "{{firstName}}": contact.get("firstName", ""),
        "{{industry}}": contact.get("industry", "our industry"),
        "{{company}}": contact.get("company", "your company"),
        "{{expertise}}": contact.get("expertise", "your professional expertise").split(",")[0] if contact.get("expertise") and "," in contact.get("expertise") else contact.get("expertise", "your expertise"),
        "{{userRole}}": st.session_state.user_profile.get("headline", "").split(" at ")[0] if " at " in st.session_state.user_profile.get("headline", "") else st.session_state.user_profile.get("headline", "professional"),
        "{{userExpertise}}": extract_expertise_from_headline(st.session_state.user_profile.get("headline", "")),
        "{{userName}}": st.session_state.user_profile.get("name", ""),
        "{{specificTopic}}": custom_topic if custom_topic else f"{contact.get('expertise', 'your expertise').split(',')[0] if contact.get('expertise') and ',' in contact.get('expertise') else contact.get('expertise', 'your field')} in {contact.get('industry', 'the industry')}"
    }
    
    # Add goal-specific replacements
    if st.session_state.networking_goal == "Career Advancement":
        replacements["{{goalContext}}"] = "advancing my career in our industry"
    elif st.session_state.networking_goal == "Industry Knowledge":
        replacements["{{goalContext}}"] = "deepening my knowledge about current trends and best practices"
    elif st.session_state.networking_goal == "Business Development":
        replacements["{{goalContext}}"] = "exploring potential collaboration opportunities"
    elif st.session_state.networking_goal == "Job Seeking":
        replacements["{{goalContext}}"] = "exploring new career opportunities in our field"
    else:
        replacements["{{goalContext}}"] = "expanding my professional network"
    
    # Add custom goal if specified
    custom_goal = st.session_state.get("custom_goal", "")
    if custom_goal:
        replacements["{{customGoal}}"] = custom_goal
        replacements["{{goalContext}}"] = f"{replacements['{{goalContext}}']} with a focus on {custom_goal}"
    
    # Template selection
    templates = {
        "coldOutreach": [
            """Hi {{firstName}},

I hope this message finds you well. I noticed your work in {{industry}} at {{company}}. Your expertise in {{expertise}} particularly caught my attention.

I'm currently a {{userRole}} specializing in {{userExpertise}} and would love to connect to learn more about your experiences with {{specificTopic}}. I'm focused on {{goalContext}} and believe your insights would be valuable.

Would you be open to a brief conversation in the coming weeks? I'd appreciate the opportunity to gain insights from your perspective.

Thanks for considering,
{{userName}}""",
            
            """Hello {{firstName}},

I came across your profile and was impressed by your background in {{expertise}} and your work at {{company}}.

I'm {{userName}}, a {{userRole}} focused on {{userExpertise}}. I'm particularly interested in your experience with {{specificTopic}} as it aligns with my goals around {{goalContext}}.

I'd value the opportunity to exchange ideas with someone of your expertise. Would you be interested in a 15-minute virtual coffee to discuss {{specificTopic}}?

Best regards,
{{userName}}"""
        ],
        "followUp": [
            """Hi {{firstName}},

I hope you're doing well. I wanted to follow up on my previous message about connecting to discuss {{specificTopic}}.

Since then, I've been working on some interesting projects related to {{userExpertise}} which has given me some additional perspective. As I continue focusing on {{goalContext}}, I believe your insights would be especially valuable.

If your schedule permits, I'd still appreciate that brief conversation we discussed. Would you be available for a quick chat in the coming weeks?

All the best,
{{userName}}"""
        ],
        "informationalInterview": [
            """Hi {{firstName}},

I hope this message finds you well. I'm {{userName}}, a {{userRole}} with a background in {{userExpertise}}.

I've been following your career journey in {{industry}} and have been particularly impressed by your work at {{company}}. Your approach to {{specificTopic}} is something I find truly inspiring.

I'm currently {{goalContext}} and would greatly value a 15-20 minute conversation to gain insights from your experience. I'm specifically interested in learning more about {{specificTopic}}.

I understand you must be busy, so I'm happy to work around your schedule. Would you be open to a brief call in the coming weeks?

Thank you for considering my request. I appreciate your time.

Best regards,
{{userName}}"""
        ]
    }
    
    # Get templates for the requested type or default to cold outreach
    selected_templates = templates.get(template_type, templates["coldOutreach"])
    
    # Choose a random template
    template = random.choice(selected_templates)
    
    # Apply all replacements
    for key, value in replacements.items():
        template = template.replace(key, value)
    
    return template

def extract_expertise_from_headline(headline):
    """Extract expertise from LinkedIn headline"""
    if not headline:
        return "professional skills"
    
    # Remove the company part if present
    if " at " in headline:
        headline = headline.split(" at ")[0]
    
    # Common patterns in headlines
    if "|" in headline:
        # Extract skills from pipe-separated format (e.g., "Software Engineer | Python | AWS | Machine Learning")
        parts = [part.strip() for part in headline.split("|")]
        if len(parts) > 1:
            return ", ".join(parts[1:3])  # Take up to 2 skills
    
    if "," in headline:
        # Extract skills from comma-separated format
        parts = [part.strip() for part in headline.split(",")]
        if len(parts) > 1:
            return ", ".join(parts[1:3])  # Take up to 2 skills
    
    # If no structure is found, return the headline as is or a generic expertise
    return headline or "professional skills"

def generate_claude_message(contact, template_type="coldOutreach", custom_topic=""):
    """Generate a message using Claude AI"""
    client = initialize_claude_client()
    
    # If Claude client initialization failed or API key not provided, fall back to basic generation
    if not client:
        return generate_basic_message(contact, template_type, custom_topic)
    
    try:
        # Prepare the prompt
        system_prompt = """You are an expert networking assistant that specializes in crafting personalized, effective LinkedIn outreach messages. 
Your task is to create a tailored networking message based on:
1. The sender's profile
2. The recipient's profile 
3. The type of message (cold outreach, follow-up, informational interview)
4. The networking goal

Craft a message that is:
- Personalized with specific details about the recipient
- Authentic and conversational (not generic or salesy)
- Concise (under 150 words)
- Includes a clear reason for connecting
- Has a specific, low-friction call to action
- Is appropriately professional but friendly
- Avoids clichés and obvious flattery
- Focused more on giving value than asking for something
- Specifically tailored to the stated networking goal
- Appropriate for LinkedIn messaging specifically

Return only the text of the message itself, without any explanation or commentary."""

        # Create a detailed prompt with all the context
        specific_topic = custom_topic if custom_topic else f"{contact.get('expertise', 'your field').split(',')[0] if contact.get('expertise') and ',' in contact.get('expertise') else contact.get('expertise', 'your field')}"
        
        user_prompt = f"""Create a personalized LinkedIn {template_type} message to {contact.get('firstName', '')} {contact.get('lastName', '')}.

RECIPIENT'S PROFILE:
- Name: {contact.get('firstName', '')} {contact.get('lastName', '')}
- Role: {contact.get('role', 'Professional')}
- Company: {contact.get('company', 'their company')}
- Industry: {contact.get('industry', 'their industry')}
- Expertise: {contact.get('expertise', 'their expertise')}
- Seniority: {contact.get('seniority', 'professional')}
- Connected on LinkedIn since: {contact.get('connectedDate', 'some time ago')}
- Mutual Connections: {contact.get('mutualConnections', 0)}

SENDER'S PROFILE:
- Name: {st.session_state.user_profile.get('name', '')}
- Role/Headline: {st.session_state.user_profile.get('headline', '')}
- Industry: {st.session_state.user_profile.get('industry', '')}
- Summary: {st.session_state.user_profile.get('summary', '')[:200] + '...' if st.session_state.user_profile.get('summary') and len(st.session_state.user_profile.get('summary')) > 200 else st.session_state.user_profile.get('summary', '')}

MESSAGE DETAILS:
- Message Type: {template_type}
- Primary Networking Goal: {st.session_state.networking_goal}
- Specific Topic of Interest: {specific_topic}
"""

        # Add custom goal if specified
        if st.session_state.get("custom_goal"):
            user_prompt += f"- Specific Networking Objective: {st.session_state.custom_goal}\n"

        user_prompt += f"\nCreate a personalized {template_type} message based on this information that furthers the networking goal of {st.session_state.networking_goal}"
        
        if st.session_state.get("custom_goal"):
            user_prompt += f" with a focus on the specific objective: {st.session_state.custom_goal}"
        
        user_prompt += "."

        # Send request to Claude
        with st.spinner("Generating personalized message with Claude AI..."):
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
        
        # Extract the message
        message = response.content[0].text
        return message
    
    except Exception as e:
        st.error(f"Error generating message with Claude: {e}")
        # Fall back to basic generation
        return generate_basic_message(contact, template_type, custom_topic)

def analyze_message_with_claude(message, contact):
    """Analyze a message using Claude AI"""
    client = initialize_claude_client()
    
    if not client:
        return {
            "overallScore": 70,
            "strengths": ["Basic message structure"],
            "weaknesses": ["Claude analysis not available - API key not set"],
            "suggestions": ["Set Claude API key for detailed message analysis"],
            "assessment": "Basic message but could be improved with AI analysis"
        }
    
    try:
        system_prompt = """You are an expert LinkedIn networking message analyst. Evaluate the provided LinkedIn outreach message based on:

1. Personalization - Does it show research and include specific details about the recipient?
2. Value proposition - Is it clear why connecting would be beneficial?
3. Authenticity - Does it sound genuine rather than generic or salesy?
4. Call to action - Is there a clear, low-friction next step?
5. Focus - Is it concise (under 150 words) and focused?
6. LinkedIn appropriateness - Is it optimized for LinkedIn specifically?
7. Goal alignment - Does it align with the stated networking goal?

Provide your analysis in JSON format with these fields:
- overallScore: number between 0-100
- strengths: array of strings (2-4 specific strengths)
- weaknesses: array of strings (0-3 specific weaknesses)
- suggestions: array of strings (0-3 specific improvement suggestions)
- assessment: string (1-2 sentence overall assessment)

Return ONLY the JSON object without any additional text or explanation."""

        user_prompt = f"""Analyze this LinkedIn networking outreach message to {contact.get('firstName', '')} {contact.get('lastName', '')}, who is a {contact.get('role', 'professional')} at {contact.get('company', 'their company')} in the {contact.get('industry', 'their industry')} industry:

MESSAGE:
{message}

RECIPIENT CONTEXT:
- Expertise: {contact.get('expertise', 'their expertise')}
- Seniority: {contact.get('seniority', 'professional')}
- Connected On: {contact.get('connectedDate', 'some time ago')}

SENDER GOAL:
- Networking Goal: {st.session_state.networking_goal}

Evaluate this message and provide feedback in the required JSON format."""

        # Send request to Claude
        with st.spinner("Analyzing message with Claude AI..."):
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
        
        # Extract and parse the JSON response
        try:
            analysis_text = response.content[0].text
            # Find JSON content - in case Claude includes any extra text
            import re
            json_match = re.search(r'({[\s\S]*})', analysis_text)
            
            if json_match:
                analysis_json = json.loads(json_match.group(1))
                return analysis_json
            else:
                # If no JSON found, create a simple response
                return {
                    "overallScore": 65,
                    "strengths": ["Message structure is appropriate"],
                    "weaknesses": ["Could not extract detailed analysis"],
                    "suggestions": ["Try again with more specific message content"],
                    "assessment": "Basic networking message that needs refinement"
                }
        
        except json.JSONDecodeError:
            return {
                "overallScore": 60,
                "strengths": ["Message has been drafted"],
                "weaknesses": ["Could not parse Claude analysis"],
                "suggestions": ["Try again with simpler message structure"],
                "assessment": "Message analysis encountered an error"
            }
    
    except Exception as e:
        st.error(f"Error analyzing message with Claude: {e}")
        return {
            "overallScore": 50,
            "strengths": ["Basic message format"],
            "weaknesses": ["Error in Claude analysis", str(e)],
            "suggestions": ["Try again or check API key configuration"],
            "assessment": "Message analysis failed due to an error"
        }

def improve_message_with_claude(message, contact):
    """Improve a message using Claude AI"""
    client = initialize_claude_client()
    
    if not client:
        return message
    
    try:
        system_prompt = """You are an expert LinkedIn networking message editor. Your task is to improve the provided outreach message while keeping its core intent and content.

Focus on enhancing:
1. Personalization - Add specific details about the recipient
2. Value proposition - Clarify why connecting would be beneficial
3. Authenticity - Make it sound more genuine and less generic
4. Call to action - Ensure there's a clear, low-friction next step
5. Conciseness - Keep it under 150 words and focused
6. LinkedIn optimization - Make it specifically tailored for LinkedIn messaging
7. Goal alignment - Ensure it clearly aligns with the stated networking goal

Return ONLY the improved message text without any explanation or commentary about your changes."""

        user_prompt = f"""Improve this LinkedIn networking outreach message to {contact.get('firstName', '')} {contact.get('lastName', '')}, who is a {contact.get('role', 'professional')} at {contact.get('company', 'their company')} in the {contact.get('industry', 'their industry')} industry:

ORIGINAL MESSAGE:
{message}

RECIPIENT DETAILS:
- Expertise: {contact.get('expertise', 'their expertise')}
- Seniority: {contact.get('seniority', 'professional')}
- Connected On: {contact.get('connectedDate', 'some time ago')}
- Mutual Connections: {contact.get('mutualConnections', 0)}
"""

        user_prompt += f"""
SENDER DETAILS:
- Name: {st.session_state.user_profile.get('name', '')}
- Role/Headline: {st.session_state.user_profile.get('headline', '')}
- Industry: {st.session_state.user_profile.get('industry', '')}
- Networking Goal: {st.session_state.networking_goal}

Improve this message while keeping its core intent. Return only the improved message text."""

        # Send request to Claude
        with st.spinner("Improving message with Claude AI..."):
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
        
        # Extract the improved message
        improved_message = response.content[0].text
        return improved_message
    
    except Exception as e:
        st.error(f"Error improving message with Claude: {e}")
        return message

# Sidebar for API key setup and navigation
with st.sidebar:
    st.markdown("<div class='main-header'>🤝 LinkedIn AI Networking Assistant</div>", unsafe_allow_html=True)
    
    # Claude API Key input
    st.markdown("### Claude AI Integration")
    api_key_input = st.text_input(
        "Enter Claude API Key", 
        value=st.session_state.CLAUDE_API_KEY,
        type="password",
        help="Required for advanced message generation and contact analysis"
    )
    
    if api_key_input != st.session_state.CLAUDE_API_KEY:
        st.session_state.CLAUDE_API_KEY = api_key_input
    
    if not st.session_state.CLAUDE_API_KEY:
        st.markdown(
            "<div class='api-info'>Claude API key not set. Basic message templates will be used.</div>",
            unsafe_allow_html=True
        )
    
    # Navigation
    st.markdown("### Navigation")
    
    if st.button("Data Import", key="nav_import"):
        st.session_state.active_tab = "import"
    
    if st.button("My Profile", key="nav_profile"):
        if not st.session_state.profile_uploaded:
            st.warning("Please upload your LinkedIn profile data first")
            st.session_state.active_tab = "import"
        else:
            st.session_state.active_tab = "profile"
    
    if st.button("AI Recommendations", key="nav_recommendations"):
        if not st.session_state.connections_uploaded:
            st.warning("Please upload your LinkedIn connections data first")
            st.session_state.active_tab = "import"
        else:
            st.session_state.active_tab = "recommendations"
    
    if st.button("Message Creator", key="nav_messages"):
        if not st.session_state.selected_contact:
            st.warning("Please select a contact from recommendations first")
            if st.session_state.connections_uploaded:
                st.session_state.active_tab = "recommendations"
            else:
                st.session_state.active_tab = "import"
        else:
            st.session_state.active_tab = "messages"
    
    st.markdown("### Networking Goal")
    goal = st.selectbox(
        "Set your networking goal",
        options=["Career Advancement", "Industry Knowledge", "Business Development", "Job Seeking"],
        index=["Career Advancement", "Industry Knowledge", "Business Development", "Job Seeking"].index(st.session_state.networking_goal)
    )
    
    # Add custom goal text field
    custom_goal = st.text_input(
        "Specific networking objective (optional)",
        value=st.session_state.get("custom_goal", ""),
        placeholder="e.g., Finding mentors in AI, Connecting with potential clients in healthcare",
        help="Describe your specific networking objective to help generate more relevant recommendations and messages"
    )
    
    # Update session state for custom goal
    if "custom_goal" not in st.session_state or custom_goal != st.session_state.custom_goal:
        st.session_state.custom_goal = custom_goal
    
    if goal != st.session_state.networking_goal:
        st.session_state.networking_goal = goal
        # Refresh recommendations when goal changes
        if len(st.session_state.linkedin_connections) > 0:
            st.session_state.recommendations = generate_recommendations(30)  # Generate more recommendations for pagination
            st.session_state.current_page = 0  # Reset to first page
    
    st.markdown("### About")
    st.markdown("""
    This AI Networking Assistant helps you leverage your LinkedIn connections by identifying valuable networking opportunities and crafting personalized outreach messages.
    
    Powered by:
    - Your LinkedIn archive data
    - Claude AI for intelligent message generation
    - Advanced contact analysis algorithms
    - Goal-oriented networking strategies
    """)

# Main Content Area based on active tab
if st.session_state.active_tab == "import":
    st.markdown("<div class='main-header'>Import LinkedIn Data</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("""
    ### How to download your LinkedIn data
    
    1. Go to LinkedIn and log in
    2. Click on your profile picture in the top-right corner
    3. Select **Settings & Privacy**
    4. Go to the **Data privacy** section
    5. Click on **Get a copy of your data**
    6. Select "Want something in particular?"
    7. Check **Connections** and **Profile**
    8. Request archive
    9. LinkedIn will email you when your data is ready to download
    10. Download and unzip the archive
    11. Upload the Profile.csv and Connections.csv files below
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Profile data import
    st.markdown("<div class='sub-header'>Profile Data</div>", unsafe_allow_html=True)
    
    if not st.session_state.profile_uploaded:
        st.markdown("<div class='upload-card'>", unsafe_allow_html=True)
        profile_file = st.file_uploader("Upload your Profile.csv file", type=["csv"], key="profile_upload")
        
        if profile_file is not None:
            # Process the profile CSV
            user_profile = process_profile_csv(profile_file)
            
            if user_profile:
                st.session_state.user_profile = user_profile
                st.session_state.profile_uploaded = True
                st.success(f"Profile data for {user_profile['name']} successfully imported")
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='success-card'>", unsafe_allow_html=True)
        st.markdown(f"✅ **Profile data imported successfully**")
        st.markdown(f"**Name:** {st.session_state.user_profile.get('name', '')}")
        st.markdown(f"**Headline:** {st.session_state.user_profile.get('headline', '')}")
        
        if st.button("Re-upload Profile"):
            st.session_state.profile_uploaded = False
            st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Connections data import
    st.markdown("<div class='sub-header'>Connections Data</div>", unsafe_allow_html=True)
    
    if not st.session_state.connections_uploaded:
        st.markdown("<div class='upload-card'>", unsafe_allow_html=True)
        connections_file = st.file_uploader("Upload your Connections.csv file", type=["csv"], key="connections_upload")
        
        if connections_file is not None:
            # Process the connections CSV
            connections = process_connections_csv(connections_file)
            
            if connections:
                st.session_state.linkedin_connections = connections
                st.session_state.connections_uploaded = True
                
                # Generate initial recommendations
                st.session_state.recommendations = generate_recommendations(5)
                
                st.success(f"Successfully imported {len(connections)} LinkedIn connections")
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='success-card'>", unsafe_allow_html=True)
        st.markdown(f"✅ **Connections data imported successfully**")
        st.markdown(f"**Total Connections:** {len(st.session_state.linkedin_connections)}")
        
        if st.button("Re-upload Connections"):
            st.session_state.connections_uploaded = False
            st.session_state.linkedin_connections = []
            st.session_state.recommendations = []
            st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Next steps
    if st.session_state.profile_uploaded and st.session_state.connections_uploaded:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### Next Steps")
        st.markdown("You've successfully imported your LinkedIn data. Now you can:")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("View Your Profile", key="next_profile"):
                st.session_state.active_tab = "profile"
                st.rerun()
        
        with col2:
            if st.button("See AI Recommendations", key="next_recommendations"):
                st.session_state.active_tab = "recommendations"
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.active_tab == "profile":
    st.markdown("<div class='main-header'>Your LinkedIn Profile</div>", unsafe_allow_html=True)
    
    # Create a card for the profile
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Display profile image
        st.image("https://avatars.githubusercontent.com/u/0", width=150)
    
    with col2:
        # Profile info
        st.markdown(f"### {st.session_state.user_profile.get('name', '')}")
        st.markdown(f"**{st.session_state.user_profile.get('headline', '')}**")
        st.markdown(f"**Industry:** {st.session_state.user_profile.get('industry', '')}")
        st.markdown(f"**Location:** {st.session_state.user_profile.get('location', '')}")
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # Profile summary
    if st.session_state.user_profile.get('summary'):
        st.markdown("### Summary")
        st.markdown(st.session_state.user_profile.get('summary', ''))
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # Connection stats
    st.markdown("### Network Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Connections", len(st.session_state.linkedin_connections))
    
    with col2:
        # Count connections by industry
        industries = {}
        for connection in st.session_state.linkedin_connections:
            industry = connection.get("industry", "Unknown")
            industries[industry] = industries.get(industry, 0) + 1
        
        # Get the most common industry
        most_common_industry = max(industries.items(), key=lambda x: x[1]) if industries else ("None", 0)
        st.metric("Most Common Industry", f"{most_common_industry[0]} ({most_common_industry[1]})")
    
    # Industry breakdown
    if industries:
        st.markdown("### Industry Breakdown")
        
        # Sort industries by count
        sorted_industries = sorted(industries.items(), key=lambda x: x[1], reverse=True)
        
        # Display top 5 industries
        for industry, count in sorted_industries[:5]:
            percentage = (count / len(st.session_state.linkedin_connections)) * 100
            st.markdown(f"**{industry}**: {count} connections ({percentage:.1f}%)")
    
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.active_tab == "recommendations":
    st.markdown("<div class='main-header'>AI-Powered LinkedIn Networking Recommendations</div>", unsafe_allow_html=True)
    
    # Networking goal context
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    
    goal_descriptions = {
        "Career Advancement": "Identifying contacts who can help with your professional growth and advancement",
        "Industry Knowledge": "Finding experts and thought leaders who can provide valuable industry insights",
        "Business Development": "Connecting with potential clients, partners, or collaborators for business opportunities",
        "Job Seeking": "Building relationships with hiring managers, recruiters, and insiders at target companies"
    }
    
    st.markdown(f"### Current Goal: **{st.session_state.networking_goal}**")
    
    # Display custom goal if set
    if st.session_state.get("custom_goal"):
        st.markdown(f"**Specific Objective:** {st.session_state.custom_goal}")
    
    st.markdown(goal_descriptions.get(st.session_state.networking_goal, ""))
    
    # Goal-specific tips
    if st.session_state.networking_goal == "Career Advancement":
        st.markdown("""
        **Tips for Career Advancement Networking:**
        - Focus on connections who are 1-2 levels above your current position
        - Look for potential mentors and advisors in your field
        - Seek out connections at aspirational companies
        """)
    elif st.session_state.networking_goal == "Industry Knowledge":
        st.markdown("""
        **Tips for Industry Knowledge Networking:**
        - Prioritize thought leaders and content creators
        - Look for connections with specialized expertise
        - Consider both experienced veterans and innovative newcomers
        """)
    elif st.session_state.networking_goal == "Business Development":
        st.markdown("""
        **Tips for Business Development Networking:**
        - Focus on decision-makers and gatekeepers
        - Prioritize connections at companies that match your ideal customer profile
        - Look for complementary rather than competitive offerings
        """)
    elif st.session_state.networking_goal == "Job Seeking":
        st.markdown("""
        **Tips for Job Seeking Networking:**
        - Connect with hiring managers and team leads at target companies
        - Prioritize recruiters specialized in your field
        - Look for "bridge" connections who can introduce you to the right people
        """)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Refresh recommendations if needed
    if not st.session_state.recommendations:
        st.session_state.recommendations = generate_recommendations(30)  # Generate more recommendations for pagination
    
    # Display refresh button
    if st.button("Refresh Recommendations"):
        with st.spinner("Generating fresh recommendations..."):
            time.sleep(1)  # Simulate processing time
            st.session_state.recommendations = generate_recommendations(30)
            st.session_state.current_page = 0  # Reset to first page
    
    # Pagination setup
    if "current_page" not in st.session_state:
        st.session_state.current_page = 0
    
    results_per_page = st.session_state.results_per_page
    
    # Determine total number of pages
    total_recommendations = len(st.session_state.recommendations)
    total_pages = max(1, (total_recommendations + results_per_page - 1) // results_per_page)
    
    # Filter recommendations for current page
    start_idx = st.session_state.current_page * results_per_page
    end_idx = min(start_idx + results_per_page, total_recommendations)
    
    current_recommendations = st.session_state.recommendations[start_idx:end_idx] if st.session_state.recommendations else []
    
    # Add pagination controls at the top
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("⬅️ Previous", disabled=st.session_state.current_page == 0):
            st.session_state.current_page = max(0, st.session_state.current_page - 1)
            st.rerun()
    
    with col2:
        if total_recommendations > 0:
            st.markdown(f"<div style='text-align: center;'>Page {st.session_state.current_page + 1} of {total_pages} • Showing {start_idx + 1}-{end_idx} of {total_recommendations} contacts</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='text-align: center;'>No recommendations available</div>", unsafe_allow_html=True)
    
    with col3:
        if st.button("Next ➡️", disabled=st.session_state.current_page >= total_pages - 1):
            st.session_state.current_page = min(total_pages - 1, st.session_state.current_page + 1)
            st.rerun()
    
    # Filter and search
    st.markdown("<div style='padding: 10px 0px;'>", unsafe_allow_html=True)
    search_query = st.text_input("Filter contacts by name, company, role, or expertise:", 
                                 placeholder="Enter keywords to filter results")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Filter recommendations if search query provided
    if search_query:
        filtered_recommendations = []
        for rec in st.session_state.recommendations:
            searchable_text = " ".join([
                str(rec.get("firstName", "")),
                str(rec.get("lastName", "")),
                str(rec.get("company", "")),
                str(rec.get("role", "")),
                str(rec.get("expertise", "")),
                str(rec.get("industry", ""))
            ]).lower()
            
            if search_query.lower() in searchable_text:
                filtered_recommendations.append(rec)
        
        # Update pagination for filtered results
        total_filtered = len(filtered_recommendations)
        total_filtered_pages = max(1, (total_filtered + results_per_page - 1) // results_per_page)
        
        # Reset page if needed
        if st.session_state.current_page >= total_filtered_pages:
            st.session_state.current_page = 0
        
        # Get current page of filtered results
        filtered_start = st.session_state.current_page * results_per_page
        filtered_end = min(filtered_start + results_per_page, total_filtered)
        
        current_recommendations = filtered_recommendations[filtered_start:filtered_end]
        
        # Show filter result stats
        st.markdown(f"<div style='padding: 5px 0px;'><i>Found {total_filtered} contacts matching '{search_query}'</i></div>", unsafe_allow_html=True)
    
    # Create a two-column layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Display recommendations
        if not current_recommendations:
            st.markdown("<div class='card' style='text-align: center; padding: 2rem;'>", unsafe_allow_html=True)
            st.markdown("### No Recommendations Available")
            if search_query:
                st.markdown(f"No contacts match your search for '{search_query}'. Try a different search term or clear the filter.")
            else:
                st.markdown("We couldn't generate any recommendations based on your connections. Try changing your networking goal or refreshing the recommendations.")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            for i, contact in enumerate(current_recommendations):
                is_selected = st.session_state.selected_contact and st.session_state.selected_contact["id"] == contact["id"]
                
                st.markdown(
                    f"<div class='contact-card {'' if not is_selected else 'selected'}' id='contact-{contact['id']}'>",
                    unsafe_allow_html=True
                )
                
                # Contact header with score
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"### {contact.get('firstName', '')} {contact.get('lastName', '')}")
                    if contact.get('role') and contact.get('company'):
                        st.markdown(f"**{contact.get('role', '')}** at **{contact.get('company', '')}**")
                    elif contact.get('role'):
                        st.markdown(f"**{contact.get('role', '')}**")
                    elif contact.get('company'):
                        st.markdown(f"**Works at {contact.get('company', '')}**")
                
                with col_b:
                    st.markdown(
                        f"<div style='text-align: right;'><span class='badge badge-green'>{contact.get('score', 0)}% Match</span></div>",
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        f"<div style='text-align: right;'><small>{contact.get('matchStrength', '')}</small></div>",
                        unsafe_allow_html=True
                    )
                
                # Contact details and insights
                st.markdown("<div style='margin-top: 0.5rem;'>", unsafe_allow_html=True)
                
                # Display badges for industry and expertise
                industry = contact.get('industry', '')
                expertise = contact.get('expertise', '')
                
                badges_html = f"<span class='badge badge-gray'>{industry}</span> " if industry else ""
                
                if expertise:
                    expertise_items = expertise.split(',')[0:2] if ',' in expertise else [expertise]
                    for exp in expertise_items:
                        badges_html += f"<span class='badge badge-blue'>{exp.strip()}</span> "
                
                if badges_html:
                    st.markdown(f"<div>{badges_html}</div>", unsafe_allow_html=True)
                
                # Display insights
                if contact.get('insights'):
                    st.markdown("<div style='margin-top: 0.5rem;'>", unsafe_allow_html=True)
                    for insight in contact.get('insights', []):
                        st.markdown(f"• {insight}")
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # Display connected date
                if contact.get('connectedDate'):
                    st.markdown(f"<div style='margin-top: 0.5rem; font-size: 0.8rem; color: #6B7280;'>Connected on: {contact.get('connectedDate')}</div>", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Action buttons
                col_a, col_b = st.columns([1, 1])
                with col_a:
                    view_button = st.button("View Details", key=f"view_{contact['id']}")
                    if view_button:
                        st.session_state.selected_contact = contact
                
                with col_b:
                    message_button = st.button("Create Message", key=f"message_{contact['id']}")
                    if message_button:
                        st.session_state.selected_contact = contact
                        st.session_state.active_tab = "messages"
                        st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Add pagination controls at the bottom
            st.markdown("<div style='padding: 15px 0px;'>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                if st.button("⬅️ Previous", key="prev_bottom", disabled=st.session_state.current_page == 0):
                    st.session_state.current_page = max(0, st.session_state.current_page - 1)
                    st.rerun()
            
            with col2:
                if search_query:
                    current_page_count = len(current_recommendations)
                    st.markdown(f"<div style='text-align: center;'>Page {st.session_state.current_page + 1} of {total_filtered_pages} • Showing {filtered_start + 1}-{filtered_start + current_page_count} of {total_filtered} filtered contacts</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='text-align: center;'>Page {st.session_state.current_page + 1} of {total_pages} • Showing {start_idx + 1}-{end_idx} of {total_recommendations} contacts</div>", unsafe_allow_html=True)
            
            with col3:
                if search_query:
                    if st.button("Next ➡️", key="next_bottom", disabled=st.session_state.current_page >= total_filtered_pages - 1):
                        st.session_state.current_page = min(total_filtered_pages - 1, st.session_state.current_page + 1)
                        st.rerun()
                else:
                    if st.button("Next ➡️", key="next_bottom", disabled=st.session_state.current_page >= total_pages - 1):
                        st.session_state.current_page = min(total_pages - 1, st.session_state.current_page + 1)
                        st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        # Display selected contact detail
        if st.session_state.selected_contact:
            contact = st.session_state.selected_contact
            
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            
            # Contact header
            st.markdown(f"### {contact.get('firstName', '')} {contact.get('lastName', '')}")
            if contact.get('role') and contact.get('company'):
                st.markdown(f"**{contact.get('role', '')}** at **{contact.get('company', '')}**")
            elif contact.get('role'):
                st.markdown(f"**{contact.get('role', '')}**")
            elif contact.get('company'):
                st.markdown(f"**Works at {contact.get('company', '')}**")
            
            if contact.get('email'):
                st.markdown(f"**Email:** {contact.get('email', '')}")
            
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            
            # Contact details
            if contact.get('industry'):
                st.markdown("<div class='contact-detail'>", unsafe_allow_html=True)
                st.markdown("<span class='contact-detail-label'>Industry:</span>", unsafe_allow_html=True)
                st.markdown(contact.get('industry', ''))
                st.markdown("</div>", unsafe_allow_html=True)
            
            if contact.get('expertise'):
                st.markdown("<div class='contact-detail'>", unsafe_allow_html=True)
                st.markdown("<span class='contact-detail-label'>Expertise:</span>", unsafe_allow_html=True)
                st.markdown(contact.get('expertise', ''))
                st.markdown("</div>", unsafe_allow_html=True)
            
            if contact.get('seniority'):
                st.markdown("<div class='contact-detail'>", unsafe_allow_html=True)
                st.markdown("<span class='contact-detail-label'>Seniority Level:</span>", unsafe_allow_html=True)
                st.markdown(contact.get('seniority', ''))
                st.markdown("</div>", unsafe_allow_html=True)
            
            if contact.get('connectedDate'):
                st.markdown("<div class='contact-detail'>", unsafe_allow_html=True)
                st.markdown("<span class='contact-detail-label'>Connected On:</span>", unsafe_allow_html=True)
                st.markdown(contact.get('connectedDate', ''))
                st.markdown("</div>", unsafe_allow_html=True)
            
            if contact.get("mutualConnections", 0) > 0:
                st.markdown("<div class='contact-detail'>", unsafe_allow_html=True)
                st.markdown("<span class='contact-detail-label'>Mutual Connections:</span>", unsafe_allow_html=True)
                st.markdown(f"{contact.get('mutualConnections')} connections")
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            
            # Generate conversation starters
            st.markdown("### AI-Generated Conversation Starters")
            starters = generate_conversation_starters(contact)
            for starter in starters:
                st.markdown(f"<div class='badge-gray' style='padding: 0.5rem; margin-bottom: 0.5rem; border-radius: 0.25rem;'>{starter}</div>", unsafe_allow_html=True)
            
            # Action buttons
            create_message = st.button("Create LinkedIn Message", key="create_message_detail", type="primary")
            if create_message:
                st.session_state.active_tab = "messages"
                st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='card' style='text-align: center;'>", unsafe_allow_html=True)
            st.markdown("### Contact Details")
            st.markdown("Select a contact to view details")
            st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.active_tab == "messages":
    st.markdown("<div class='main-header'>LinkedIn Message Creator</div>", unsafe_allow_html=True)
    
    # Check if we have a selected contact
    if not st.session_state.selected_contact:
        st.markdown("<div class='card' style='text-align: center; padding: 2rem;'>", unsafe_allow_html=True)
        st.markdown("### No Contact Selected")
        st.markdown("Please select a contact from the recommendations tab to create a personalized LinkedIn message.")
        
        if st.button("Go to Recommendations"):
            st.session_state.active_tab = "recommendations"
            st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        contact = st.session_state.selected_contact
        
        # Create a two-column layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            
            # Contact header
            st.markdown(f"### Creating LinkedIn message for {contact.get('firstName', '')} {contact.get('lastName', '')}")
            if contact.get('role') and contact.get('company'):
                st.markdown(f"**{contact.get('role', '')}** at **{contact.get('company', '')}**")
            elif contact.get('role'):
                st.markdown(f"**{contact.get('role', '')}**")
            elif contact.get('company'):
                st.markdown(f"**Works at {contact.get('company', '')}**")
            
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            
            # Message type selection
            message_type = st.selectbox(
                "Message Type",
                options=["coldOutreach", "followUp", "informationalInterview"],
                format_func=lambda x: {
                    "coldOutreach": "Cold Outreach",
                    "followUp": "Follow-Up",
                    "informationalInterview": "Informational Interview"
                }.get(x, x),
                index=0
            )
            
            if message_type != st.session_state.message_type:
                st.session_state.message_type = message_type
                # Reset message when type changes
                st.session_state.generated_message = ""
            
            # Custom topic
            custom_topic = st.text_input(
                "Specific Topic of Interest (optional)",
                value=st.session_state.custom_topic,
                placeholder=f"e.g., {contact.get('expertise', 'their expertise').split(',')[0] if contact.get('expertise') and ',' in contact.get('expertise') else contact.get('expertise', 'professional')} trends"
            )
            
            if custom_topic != st.session_state.custom_topic:
                st.session_state.custom_topic = custom_topic
            
            # Message generation options
            st.markdown("### Message Generation")
            col_a, col_b = st.columns(2)
            
            with col_a:
                basic_gen = st.button("Generate Basic Template")
                if basic_gen:
                    with st.spinner("Generating basic message..."):
                        st.session_state.generated_message = generate_basic_message(
                            contact, 
                            st.session_state.message_type,
                            st.session_state.custom_topic
                        )
            
            with col_b:
                ai_gen = st.button("Generate with Claude AI", type="primary")
                if ai_gen:
                    # Check if Claude API key is set
                    if not st.session_state.CLAUDE_API_KEY:
                        st.error("Claude API key not set. Please configure it in the sidebar.")
                    else:
                        st.session_state.generated_message = generate_claude_message(
                            contact, 
                            st.session_state.message_type,
                            st.session_state.custom_topic
                        )
            
            # Message text area
            st.markdown("### Your LinkedIn Message")
            message = st.text_area(
                "Edit your message",
                value=st.session_state.generated_message,
                height=300,
                label_visibility="collapsed"
            )
            
            # Update the message in session state
            if message != st.session_state.generated_message:
                st.session_state.generated_message = message
            
            # Analyze and improve buttons
            col_a, col_b = st.columns(2)
            
            with col_a:
                analyze = st.button("Analyze Message")
                if analyze and st.session_state.generated_message:
                    analysis = analyze_message_with_claude(
                        st.session_state.generated_message,
                        contact
                    )
                    
                    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
                    st.markdown("### Message Analysis")
                    
                    # Display score
                    score_color = "green"
                    if analysis["overallScore"] < 60:
                        score_color = "red"
                    elif analysis["overallScore"] < 80:
                        score_color = "orange"
                    
                    st.markdown(
                        f"<div style='text-align: center; margin-bottom: 1rem;'>"
                        f"<h2 style='color: {score_color};'>{analysis['overallScore']}/100</h2>"
                        f"<p>{analysis['assessment']}</p>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                    
                    # Display strengths and weaknesses
                    col_x, col_y = st.columns(2)
                    
                    with col_x:
                        st.markdown("#### Strengths")
                        for strength in analysis["strengths"]:
                            st.markdown(f"✅ {strength}")
                    
                    with col_y:
                        st.markdown("#### Areas for Improvement")
                        if analysis["weaknesses"]:
                            for weakness in analysis["weaknesses"]:
                                st.markdown(f"❌ {weakness}")
                        else:
                            st.markdown("No significant weaknesses identified.")
                    
                    # Display suggestions
                    if analysis["suggestions"]:
                        st.markdown("#### Suggestions")
                        for suggestion in analysis["suggestions"]:
                            st.markdown(f"💡 {suggestion}")
            
            with col_b:
                improve = st.button("Improve with Claude AI")
                if improve and st.session_state.generated_message:
                    # Check if Claude API key is set
                    if not st.session_state.CLAUDE_API_KEY:
                        st.error("Claude API key not set. Please configure it in the sidebar.")
                    else:
                        improved_message = improve_message_with_claude(
                            st.session_state.generated_message,
                            contact
                        )
                        
                        if improved_message != st.session_state.generated_message:
                            st.session_state.generated_message = improved_message
                            st.success("Message improved successfully!")
                            st.rerun()
            
            # LinkedIn send simulation
            if st.session_state.generated_message:
                st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
                
                # LinkedIn usage instructions
                st.markdown("### Send via LinkedIn")
                st.markdown("""
                To send this message on LinkedIn:
                1. Copy the message to your clipboard
                2. Visit your connection's profile on LinkedIn
                3. Click "Message" and paste your personalized message
                """)
                
                col_a, col_b = st.columns([3, 1])
                
                with col_b:
                    copy_button = st.button("📋 Copy to Clipboard")
                    if copy_button:
                        st.write("Message copied to clipboard!")
                        st.write("")  # This is a placeholder for JavaScript (which doesn't work in pure Streamlit)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            
            st.markdown("### Contact Insights")
            
            # Key information about the contact
            if contact.get('industry'):
                st.markdown("<div class='contact-detail'>", unsafe_allow_html=True)
                st.markdown("<span class='contact-detail-label'>Industry:</span>", unsafe_allow_html=True)
                st.markdown(contact.get('industry', ''))
                st.markdown("</div>", unsafe_allow_html=True)
            
            if contact.get('expertise'):
                st.markdown("<div class='contact-detail'>", unsafe_allow_html=True)
                st.markdown("<span class='contact-detail-label'>Expertise:</span>", unsafe_allow_html=True)
                st.markdown(contact.get('expertise', ''))
                st.markdown("</div>", unsafe_allow_html=True)
            
            if contact.get('connectedDate'):
                st.markdown("<div class='contact-detail'>", unsafe_allow_html=True)
                st.markdown("<span class='contact-detail-label'>Connected On:</span>", unsafe_allow_html=True)
                st.markdown(contact.get('connectedDate', ''))
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            
            # Goal-focused messaging tips
            st.markdown("### Tips for Your Networking Goal")
            
            if st.session_state.networking_goal == "Career Advancement":
                st.markdown("""
                **Career Advancement Tips:**
                - Mention specific aspects of their career path you admire
                - Ask for advice rather than opportunities
                - Reference a specific expertise or project of theirs
                - Be clear about your own career aspirations
                """)
            elif st.session_state.networking_goal == "Industry Knowledge":
                st.markdown("""
                **Industry Knowledge Tips:**
                - Reference specific expertise they possess
                - Ask targeted questions about industry trends
                - Mention your own relevant experiences or insights
                - Offer value through your own perspective
                """)
            elif st.session_state.networking_goal == "Business Development":
                st.markdown("""
                **Business Development Tips:**
                - Focus on potential mutual benefits
                - Mention specific complementary aspects of your offerings
                - Be clear but not pushy about potential opportunities
                - Research their business needs before reaching out
                """)
            elif st.session_state.networking_goal == "Job Seeking":
                st.markdown("""
                **Job Seeking Tips:**
                - Focus on relationship-building, not directly asking for a job
                - Show interest in the company culture and values
                - Demonstrate relevant knowledge about their organization
                - Mention specific skills you bring that align with their needs
                """)
            
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            
            # AI-generated conversation starters
            st.markdown("### AI-Generated Conversation Starters")
            starters = generate_conversation_starters(contact)
            for i, starter in enumerate(starters):
                starter_copy = st.button(f"Use This ↩️", key=f"copy_starter_{i}")
                st.markdown(f"<div style='padding: 0.5rem; margin-bottom: 0.5rem; border-radius: 0.25rem; background-color: #F3F4F6;'>{starter}</div>", unsafe_allow_html=True)
                
                if starter_copy:
                    # Insert the starter into the message
                    if not st.session_state.generated_message:
                        st.session_state.generated_message = f"Hi {contact.get('firstName', '')},\n\n{starter}\n\nWould you be open to a brief conversation about this? I'd appreciate your insights.\n\nBest regards,\n{st.session_state.user_profile.get('name', '')}"
                    else:
                        # Try to insert after greeting
                        message_parts = st.session_state.generated_message.split('\n\n')
                        if len(message_parts) > 1:
                            message_parts.insert(1, starter)
                            st.session_state.generated_message = '\n\n'.join(message_parts)
                        else:
                            st.session_state.generated_message += f"\n\n{starter}"
                    
                    st.rerun()
            
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            
            # Message templates
            st.markdown("### Message Templates")
            template_types = {
                "coldOutreach": "Cold Outreach",
                "followUp": "Follow-Up",
                "informationalInterview": "Informational Interview"
            }
            
            for template_type, display_name in template_types.items():
                if st.button(f"Use {display_name} Template", key=f"use_template_{template_type}"):
                    st.session_state.message_type = template_type
                    # Generate a new message with the selected template
                    st.session_state.generated_message = generate_basic_message(
                        contact, 
                        template_type,
                        st.session_state.custom_topic
                    )
                    st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)

# Add footer
st.markdown("""
<div style="text-align: center; margin-top: 2rem; padding: 1rem; border-top: 1px solid #E5E7EB;">
    <p>LinkedIn AI Networking Assistant - Powered by Claude AI</p>
    <p><small>© 2025 All Rights Reserved</small></p>
</div>
""", unsafe_allow_html=True)
