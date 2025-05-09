import streamlit as st
import pandas as pd
import json
import os
import random
from datetime import datetime, timedelta
import anthropic
import time
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="LinkedIn AI Networking Assistant",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to initialize API clients
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

def initialize_linkedin_client():
    client_id = st.session_state.get("LINKEDIN_CLIENT_ID", "")
    client_secret = st.session_state.get("LINKEDIN_CLIENT_SECRET", "")
    redirect_uri = st.session_state.get("LINKEDIN_REDIRECT_URI", "http://localhost:8501/")
    
    if not client_id or not client_secret:
        return None
    
    # LinkedIn client is more complex due to OAuth, but we'll simplify for this demo
    # In a real app, you'd implement the full OAuth flow
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri
    }

# Initialize session state
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.active_tab = "profile"
    st.session_state.linkedin_connections = []
    st.session_state.selected_contact = None
    st.session_state.generated_message = ""
    st.session_state.message_type = "coldOutreach"
    st.session_state.networking_goal = "Career Advancement"
    st.session_state.custom_topic = ""
    st.session_state.recommendations = []
    st.session_state.CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
    st.session_state.LINKEDIN_CLIENT_ID = os.environ.get("LINKEDIN_CLIENT_ID", "")
    st.session_state.LINKEDIN_CLIENT_SECRET = os.environ.get("LINKEDIN_CLIENT_SECRET", "")
    st.session_state.LINKEDIN_REDIRECT_URI = os.environ.get("LINKEDIN_REDIRECT_URI", "http://localhost:8501/")
    st.session_state.linkedin_access_token = ""
    st.session_state.linkedin_connected = False
    st.session_state.user_profile = {
        "name": "Jamie Doe",
        "currentRole": "Software Engineer",
        "industry": "Technology",
        "expertise": "React, Node.js, AI",
        "interests": "Machine Learning, Web Development, Open Source",
        "company": "TechCorp Inc.",
        "location": "San Francisco, CA",
        "headline": "Software Engineer | Full Stack Developer | AI Enthusiast"
    }

# Sample LinkedIn connections data (for demonstration)
sample_connections = [
    {
        "id": "abc123",
        "firstName": "Jordan",
        "lastName": "Smith",
        "role": "Product Manager",
        "industry": "Technology",
        "company": "InnovateTech",
        "expertise": "Product Strategy, UX, Agile",
        "seniority": "Senior",
        "companySize": "Enterprise",
        "companyPrestige": "High",
        "activityLevel": "High",
        "recentProjects": "AI Product Launch, Platform Redesign",
        "keyAchievements": "Grew user base by 200%",
        "recentActivity": {"type": "post", "topic": "AI ethics", "date": (datetime.now() - timedelta(days=3)).isoformat()},
        "mutualConnections": 3,
        "profileUrl": "https://linkedin.com/in/jordan-smith"
    },
    {
        "id": "def456",
        "firstName": "Taylor",
        "lastName": "Wong",
        "role": "Engineering Director",
        "industry": "Software",
        "company": "CodeCorp",
        "expertise": "Cloud Architecture, Microservices, DevOps",
        "seniority": "Director",
        "companySize": "Mid-size",
        "companyPrestige": "Medium",
        "activityLevel": "Medium",
        "recentProjects": "Microservices Migration, CI/CD Pipeline",
        "keyAchievements": "Reduced infrastructure costs by 40%",
        "recentActivity": {"type": "article", "topic": "serverless architecture", "date": (datetime.now() - timedelta(days=10)).isoformat()},
        "mutualConnections": 1,
        "profileUrl": "https://linkedin.com/in/taylor-wong"
    },
    {
        "id": "ghi789",
        "firstName": "Alex",
        "lastName": "Johnson",
        "role": "Marketing Manager",
        "industry": "E-commerce",
        "company": "ShopDirect",
        "expertise": "Growth Marketing, SEO, Analytics",
        "seniority": "Manager",
        "companySize": "Startup",
        "companyPrestige": "Medium",
        "activityLevel": "High",
        "recentProjects": "Influencer Campaign, Content Strategy",
        "keyAchievements": "Doubled conversion rate in 3 months",
        "recentActivity": {"type": "post", "topic": "conversion optimization", "date": (datetime.now() - timedelta(days=5)).isoformat()},
        "mutualConnections": 0,
        "profileUrl": "https://linkedin.com/in/alex-johnson"
    },
    {
        "id": "jkl012",
        "firstName": "Morgan",
        "lastName": "Lee",
        "role": "Data Scientist",
        "industry": "Finance",
        "company": "DataBank",
        "expertise": "Predictive Analytics, Machine Learning, Python",
        "seniority": "Senior",
        "companySize": "Large",
        "companyPrestige": "High",
        "activityLevel": "Medium",
        "recentProjects": "Fraud Detection System, Risk Modeling",
        "keyAchievements": "Reduced false positives by 75%",
        "recentActivity": {"type": "article", "topic": "ML in finance", "date": (datetime.now() - timedelta(days=15)).isoformat()},
        "mutualConnections": 2,
        "profileUrl": "https://linkedin.com/in/morgan-lee"
    },
    {
        "id": "mno345",
        "firstName": "Casey",
        "lastName": "Rivera",
        "role": "UX Designer",
        "industry": "Technology",
        "company": "DesignWorks",
        "expertise": "User Research, Interaction Design, Prototyping",
        "seniority": "Mid Level",
        "companySize": "Agency",
        "companyPrestige": "Medium",
        "activityLevel": "High",
        "recentProjects": "Mobile App Redesign, Design System",
        "keyAchievements": "Increased user engagement by 150%",
        "recentActivity": {"type": "post", "topic": "inclusive design", "date": (datetime.now() - timedelta(days=2)).isoformat()},
        "mutualConnections": 5,
        "profileUrl": "https://linkedin.com/in/casey-rivera"
    }
]

# Load sample connections if empty
if len(st.session_state.linkedin_connections) == 0:
    st.session_state.linkedin_connections = sample_connections

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
    .linkedin-button>button {
        background-color: #0A66C2 !important;
        color: white !important;
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
</style>
""", unsafe_allow_html=True)

# API Functions for LinkedIn Integration
def get_linkedin_auth_url():
    """Generate LinkedIn OAuth URL"""
    client_id = st.session_state.LINKEDIN_CLIENT_ID
    redirect_uri = st.session_state.LINKEDIN_REDIRECT_URI
    scopes = "r_liteprofile,r_emailaddress,r_1st_connections_size"
    
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scopes,
        "state": "random_state_string"  # In a real app, use a secure random string
    }
    
    return f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"

def exchange_code_for_token(code):
    """Exchange authorization code for access token"""
    # In a real app, this would make an actual API call
    # This is simulated for demo purposes
    
    # Simulate successful token exchange
    return {
        "access_token": "simulated_access_token",
        "expires_in": 3600,
        "refresh_token": "simulated_refresh_token"
    }

def get_linkedin_profile(access_token):
    """Get user's LinkedIn profile"""
    # In a real app, this would make an actual API call
    # This is simulated for demo purposes
    
    # Return simulated profile data
    if "linkedin_profile" not in st.session_state:
        # Create a default profile first time
        st.session_state.linkedin_profile = {
            "id": "user123",
            "firstName": st.session_state.user_profile["name"].split()[0],
            "lastName": st.session_state.user_profile["name"].split()[-1] if len(st.session_state.user_profile["name"].split()) > 1 else "",
            "headline": st.session_state.user_profile["headline"],
            "industryName": st.session_state.user_profile["industry"],
            "location": st.session_state.user_profile["location"],
            "positions": [
                {
                    "title": st.session_state.user_profile["currentRole"],
                    "companyName": st.session_state.user_profile["company"]
                }
            ]
        }
    
    return st.session_state.linkedin_profile

def get_linkedin_connections(access_token):
    """Get user's LinkedIn connections"""
    # In a real app, this would make an actual API call
    # This is simulated for demo purposes
    
    # For demo, we'll use our sample connections
    return sample_connections

# Helper Functions
def generate_recommendations(count=5):
    """Generate AI-powered contact recommendations"""
    # In a real app, this would use more sophisticated algorithms
    # We'll simulate this with random scores and insights based on networking goal
    
    scored_contacts = []
    
    for contact in st.session_state.linkedin_connections:
        # Generate a score based on industry match, seniority, and networking goal
        base_score = 50  # Base score
        
        # Industry match bonus
        if contact["industry"] == st.session_state.user_profile["industry"]:
            base_score += 20
        
        # Seniority bonus based on networking goal
        if st.session_state.networking_goal == "Career Advancement" and contact["seniority"] in ["Senior", "Manager", "Director", "VP"]:
            base_score += 15
        elif st.session_state.networking_goal == "Industry Knowledge" and contact["seniority"] in ["Senior", "Manager", "Director"]:
            base_score += 15
        elif st.session_state.networking_goal == "Business Development" and contact["seniority"] in ["Manager", "Director", "VP", "C-Suite"]:
            base_score += 15
        elif st.session_state.networking_goal == "Job Seeking" and contact["seniority"] in ["Manager", "Director", "VP"]:
            base_score += 20
        
        # Activity level bonus
        if contact["activityLevel"] == "High":
            base_score += 10
        
        # Mutual connections bonus
        base_score += min(contact["mutualConnections"] * 3, 15)
        
        # Add some randomness
        score = min(max(base_score + random.randint(-5, 5), 40), 95)
        
        # Generate insights based on networking goal
        insights = []
        
        # Common insights for all goals
        if contact["industry"] == st.session_state.user_profile["industry"]:
            insights.append(f"Same industry ({contact['industry']})")
        
        if contact["mutualConnections"] > 0:
            insights.append(f"{contact['mutualConnections']} mutual connections")
        
        # Goal-specific insights
        if st.session_state.networking_goal == "Career Advancement":
            if contact["seniority"] in ["Senior", "Manager", "Director", "VP"]:
                insights.append(f"Senior position ({contact['seniority']}) for career guidance")
            
            if "expertise" in contact and st.session_state.user_profile["expertise"] in contact["expertise"]:
                insights.append(f"Shares your expertise in {st.session_state.user_profile['expertise'].split(',')[0]}")
        
        elif st.session_state.networking_goal == "Industry Knowledge":
            if "expertise" in contact:
                expertise = contact["expertise"].split(",")[0].strip() if "," in contact["expertise"] else contact["expertise"]
                insights.append(f"Expert in {expertise}")
            
            if "recentActivity" in contact and contact["recentActivity"]["type"] == "article":
                insights.append(f"Creates content about {contact['recentActivity']['topic']}")
        
        elif st.session_state.networking_goal == "Business Development":
            if contact["seniority"] in ["Manager", "Director", "VP", "C-Suite"]:
                insights.append(f"Decision maker ({contact['seniority']})")
            
            if contact["companySize"] in ["Large", "Enterprise"]:
                insights.append(f"Works at {contact['companySize']} company")
        
        elif st.session_state.networking_goal == "Job Seeking":
            if contact["seniority"] in ["Manager", "Director", "VP"]:
                insights.append(f"Hiring authority ({contact['seniority']})")
            
            if contact["company"]:
                insights.append(f"Works at target company ({contact['company']})")
        
        # Fill with more generic insights if needed
        if len(insights) < 2:
            potential_insights = [
                f"Experienced in {contact['expertise'].split(',')[0] if ',' in contact['expertise'] else contact['expertise']}",
                f"Works at {contact['company']} ({contact['companySize']})",
                f"{contact['seniority']} level professional",
                f"Achievement: {contact['keyAchievements']}"
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
    
    # Based on recent activity
    if "recentActivity" in contact and contact["recentActivity"]:
        if contact["recentActivity"]["type"] == "post":
            starters.append(f"I noticed your recent post about {contact['recentActivity']['topic']}. What sparked your interest in this area?")
        elif contact["recentActivity"]["type"] == "article":
            starters.append(f"I read your article on {contact['recentActivity']['topic']}. Your perspective was thought-provoking.")
    
    # Based on career achievements
    if "keyAchievements" in contact and contact["keyAchievements"]:
        starters.append(f"Your achievement in {contact['keyAchievements']} is impressive. I'd love to hear more about your approach.")
    
    # Based on shared industry
    if contact["industry"] == st.session_state.user_profile["industry"]:
        industry = contact["industry"]
        industry_topics = {
            "Technology": ["AI advancements", "remote work technologies", "cybersecurity trends"],
            "Finance": ["fintech innovations", "sustainable investing", "regulatory changes"],
            "E-commerce": ["omnichannel strategies", "customer retention", "logistics optimization"],
            "Software": ["cloud architecture", "no-code platforms", "developer experience"]
        }
        topics = industry_topics.get(industry, ["industry innovations", "current challenges", "future trends"])
        topic = random.choice(topics)
        starters.append(f"As fellow professionals in {industry}, I'm curious about your thoughts on {topic}.")
    
    # Based on recent projects
    if "recentProjects" in contact and contact["recentProjects"]:
        projects = contact["recentProjects"].split(",")
        project = projects[0].strip()
        starters.append(f"I found your work on {project} interesting. What inspired you to take on that project?")
    
    # Based on mutual connections
    if contact["mutualConnections"] > 0:
        starters.append(f"I noticed we have {contact['mutualConnections']} shared connections. The industry community is smaller than it seems!")
    
    # Add goal-specific starters
    if st.session_state.networking_goal == "Career Advancement":
        starters.append(f"I'm focusing on advancing my career in {contact['industry']}. What helped you reach your current position as {contact['role']}?")
    
    elif st.session_state.networking_goal == "Industry Knowledge":
        expertise = contact["expertise"].split(",")[0].strip() if "," in contact["expertise"] else contact["expertise"]
        starters.append(f"I'm working to deepen my understanding of {expertise}. What resources or practices have been most valuable for your development in this area?")
    
    elif st.session_state.networking_goal == "Business Development":
        starters.append(f"I'm exploring potential synergies between organizations in our space. Would you be open to discussing how {contact['company']} approaches partnerships?")
    
    elif st.session_state.networking_goal == "Job Seeking":
        starters.append(f"I'm currently exploring new opportunities in {contact['industry']}. Would you have any insights on what {contact['company']} values most in candidates?")
    
    # Add generic starters if we don't have enough
    generic_starters = [
        "What's the most interesting project you've worked on recently?",
        f"What aspect of your work in {contact['industry']} do you find most fulfilling?",
        f"How did you first become interested in {contact['industry']}?",
        f"What's one challenge in {contact['industry']} that isn't getting enough attention?",
        f"What skills do you think will be most important for professionals in {contact['industry']} in the next few years?"
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
        "{{firstName}}": contact["firstName"],
        "{{industry}}": contact["industry"],
        "{{company}}": contact["company"],
        "{{expertise}}": contact["expertise"].split(",")[0] if "," in contact["expertise"] else contact["expertise"],
        "{{userRole}}": st.session_state.user_profile["currentRole"],
        "{{userExpertise}}": st.session_state.user_profile["expertise"],
        "{{userName}}": st.session_state.user_profile["name"],
        "{{specificTopic}}": custom_topic if custom_topic else f"{contact['expertise'].split(',')[0] if ',' in contact['expertise'] else contact['expertise']} in {contact['industry']}"
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
        specific_topic = custom_topic if custom_topic else f"{contact['expertise'].split(',')[0] if ',' in contact['expertise'] else contact['expertise']}"
        
        user_prompt = f"""Create a personalized LinkedIn {template_type} message to {contact['firstName']} {contact['lastName']}.

RECIPIENT'S PROFILE:
- Name: {contact['firstName']} {contact['lastName']}
- Role: {contact['role']}
- Company: {contact['company']}
- Industry: {contact['industry']}
- Expertise: {contact['expertise']}
- Seniority: {contact['seniority']}
- Recent Projects: {contact['recentProjects']}
- Key Achievements: {contact['keyAchievements']}
- Mutual Connections: {contact['mutualConnections']}
"""

        if "recentActivity" in contact and contact["recentActivity"]:
            user_prompt += f"- Recent Activity: {contact['recentActivity']['type']} about {contact['recentActivity']['topic']}\n"

        user_prompt += f"""
SENDER'S PROFILE:
- Name: {st.session_state.user_profile['name']}
- Role: {st.session_state.user_profile['currentRole']}
- Industry: {st.session_state.user_profile['industry']}
- Expertise: {st.session_state.user_profile['expertise']}
- Company: {st.session_state.user_profile['company']}
- Headline: {st.session_state.user_profile['headline']}

MESSAGE DETAILS:
- Message Type: {template_type}
- Networking Goal: {st.session_state.networking_goal}
- Specific Topic of Interest: {specific_topic}

Create a personalized {template_type} message based on this information that furthers the networking goal of {st.session_state.networking_goal}."""

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

        user_prompt = f"""Analyze this LinkedIn networking outreach message to {contact['firstName']} {contact['lastName']}, who is a {contact['role']} at {contact['company']} in the {contact['industry']} industry:

MESSAGE:
{message}

RECIPIENT CONTEXT:
- Expertise: {contact['expertise']}
- Seniority: {contact['seniority']}
- Recent Projects: {contact['recentProjects']}

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

        user_prompt = f"""Improve this LinkedIn networking outreach message to {contact['firstName']} {contact['lastName']}, who is a {contact['role']} at {contact['company']} in the {contact['industry']} industry:

ORIGINAL MESSAGE:
{message}

RECIPIENT DETAILS:
- Expertise: {contact['expertise']}
- Seniority: {contact['seniority']}
- Recent Projects: {contact['recentProjects']}
- Key Achievements: {contact['keyAchievements']}
"""

        if "recentActivity" in contact and contact["recentActivity"]:
            user_prompt += f"- Recent Activity: {contact['recentActivity']['type']} about {contact['recentActivity']['topic']}\n"

        user_prompt += f"""
SENDER DETAILS:
- Name: {st.session_state.user_profile['name']}
- Role: {st.session_state.user_profile['currentRole']}
- Expertise: {st.session_state.user_profile['expertise']}
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
    
    # LinkedIn API Setup
    st.markdown("### LinkedIn API Configuration")
    linkedin_client_id = st.text_input(
        "LinkedIn Client ID", 
        value=st.session_state.LINKEDIN_CLIENT_ID,
        type="password",
        help="Required for LinkedIn profile and connections access"
    )
    
    if linkedin_client_id != st.session_state.LINKEDIN_CLIENT_ID:
        st.session_state.LINKEDIN_CLIENT_ID = linkedin_client_id
    
    linkedin_client_secret = st.text_input(
        "LinkedIn Client Secret", 
        value=st.session_state.LINKEDIN_CLIENT_SECRET,
        type="password",
        help="Required for LinkedIn authentication"
    )
    
    if linkedin_client_secret != st.session_state.LINKEDIN_CLIENT_SECRET:
        st.session_state.LINKEDIN_CLIENT_SECRET = linkedin_client_secret
    
    # Only show redirect URI if client ID and secret are provided
    if st.session_state.LINKEDIN_CLIENT_ID and st.session_state.LINKEDIN_CLIENT_SECRET:
        linkedin_redirect_uri = st.text_input(
            "LinkedIn Redirect URI", 
            value=st.session_state.LINKEDIN_REDIRECT_URI,
            help="The callback URL for OAuth authentication"
        )
        
        if linkedin_redirect_uri != st.session_state.LINKEDIN_REDIRECT_URI:
            st.session_state.LINKEDIN_REDIRECT_URI = linkedin_redirect_uri
    
    # API info
    if not st.session_state.LINKEDIN_CLIENT_ID or not st.session_state.LINKEDIN_CLIENT_SECRET:
        st.markdown(
            "<div class='api-info'>LinkedIn API credentials required for full functionality. "
            "For demo purposes, sample connections will be used.</div>",
            unsafe_allow_html=True
        )
    
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
    
    # LinkedIn Connect button
    st.markdown("### LinkedIn Connection")
    
    linkedin_client = initialize_linkedin_client()
    
    if not linkedin_client:
        st.warning("Configure LinkedIn API credentials to connect your account.")
    else:
        if not st.session_state.linkedin_connected:
            linkedin_connect = st.button("Connect to LinkedIn", key="linkedin_connect")
            
            if linkedin_connect:
                # In a real app, this would redirect to LinkedIn OAuth
                # For demo, we'll simulate successful connection
                st.session_state.linkedin_connected = True
                st.session_state.linkedin_access_token = "simulated_access_token"
                st.success("Connected to LinkedIn (simulated for demo)")
                
                # Get profile and connections
                st.session_state.user_profile = get_linkedin_profile(st.session_state.linkedin_access_token)
                st.session_state.linkedin_connections = get_linkedin_connections(st.session_state.linkedin_access_token)
                
                # Refresh recommendations
                st.session_state.recommendations = generate_recommendations(5)
                st.rerun()
        else:
            st.success("Connected to LinkedIn")
            linkedin_disconnect = st.button("Disconnect", key="linkedin_disconnect")
            
            if linkedin_disconnect:
                st.session_state.linkedin_connected = False
                st.session_state.linkedin_access_token = ""
                st.rerun()
    
    # Navigation
    st.markdown("### Navigation")
    
    if st.button("My Profile", key="nav_profile"):
        st.session_state.active_tab = "profile"
    
    if st.button("AI Recommendations", key="nav_recommendations"):
        st.session_state.active_tab = "recommendations"
    
    if st.button("Message Creator", key="nav_messages"):
        st.session_state.active_tab = "messages"
    
    st.markdown("### Networking Goal")
    goal = st.selectbox(
        "Set your networking goal",
        options=["Career Advancement", "Industry Knowledge", "Business Development", "Job Seeking"],
        index=["Career Advancement", "Industry Knowledge", "Business Development", "Job Seeking"].index(st.session_state.networking_goal)
    )
    
    if goal != st.session_state.networking_goal:
        st.session_state.networking_goal = goal
        # Refresh recommendations when goal changes
        if len(st.session_state.linkedin_connections) > 0:
            st.session_state.recommendations = generate_recommendations(5)
    
    st.markdown("### About")
    st.markdown("""
    This AI Networking Assistant helps you leverage your LinkedIn network by identifying valuable connections and crafting personalized outreach messages.
    
    Powered by:
    - LinkedIn API for profile and connections data
    - Claude AI for intelligent message generation
    - Advanced contact analysis algorithms
    - Goal-oriented networking strategies
    """)

# Main Content Area based on active tab
if st.session_state.active_tab == "profile":
    st.markdown("<div class='main-header'>Your LinkedIn Profile</div>", unsafe_allow_html=True)
    
    # Create a card for the profile
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Display profile image
        st.image("https://avatars.githubusercontent.com/u/0", width=150)
    
    with col2:
        # Profile info
        st.markdown(f"### {st.session_state.user_profile['name']}")
        st.markdown(f"**{st.session_state.user_profile['headline']}**")
        st.markdown(f"**Current Role:** {st.session_state.user_profile['currentRole']} at {st.session_state.user_profile['company']}")
        st.markdown(f"**Industry:** {st.session_state.user_profile['industry']}")
        st.markdown(f"**Location:** {st.session_state.user_profile['location']}")
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # Profile form
    with st.form("profile_form"):
        st.markdown("### Edit Your Profile")
        st.markdown("*Note: In a real app, this would sync with your LinkedIn profile*")
        
        name = st.text_input("Full Name", value=st.session_state.user_profile["name"])
        headline = st.text_input("Headline", value=st.session_state.user_profile["headline"])
        
        col1, col2 = st.columns(2)
        with col1:
            current_role = st.text_input("Current Role", value=st.session_state.user_profile["currentRole"])
            industry = st.text_input("Industry", value=st.session_state.user_profile["industry"])
        
        with col2:
            company = st.text_input("Company", value=st.session_state.user_profile["company"])
            location = st.text_input("Location", value=st.session_state.user_profile["location"])
        
        expertise = st.text_input("Expertise (comma separated)", value=st.session_state.user_profile["expertise"])
        interests = st.text_area("Professional Interests", value=st.session_state.user_profile["interests"])
        
        submit = st.form_submit_button("Update Profile")
        
        if submit:
            st.session_state.user_profile = {
                "name": name,
                "headline": headline,
                "currentRole": current_role,
                "industry": industry,
                "company": company,
                "location": location,
                "expertise": expertise,
                "interests": interests
            }
            st.success("Profile updated successfully!")
            
            # Update LinkedIn profile simulation
            if st.session_state.linkedin_connected:
                st.session_state.linkedin_profile["firstName"] = name.split()[0]
                st.session_state.linkedin_profile["lastName"] = name.split()[-1] if len(name.split()) > 1 else ""
                st.session_state.linkedin_profile["headline"] = headline
                st.session_state.linkedin_profile["industryName"] = industry
                st.session_state.linkedin_profile["location"] = location
                st.session_state.linkedin_profile["positions"][0]["title"] = current_role
                st.session_state.linkedin_profile["positions"][0]["companyName"] = company
            
            # Refresh recommendations when profile changes
            if len(st.session_state.linkedin_connections) > 0:
                st.session_state.recommendations = generate_recommendations(5)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # LinkedIn connection status
    st.markdown("<div class='sub-header'>LinkedIn Connection Status</div>", unsafe_allow_html=True)
    
    if st.session_state.linkedin_connected:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.success("Your LinkedIn account is connected!")
        
        # Display connection stats
        st.markdown(f"**Connections:** {len(st.session_state.linkedin_connections)}")
        
        # Industries represented in connections
        industries = {}
        for connection in st.session_state.linkedin_connections:
            industry = connection.get("industry", "Unknown")
            industries[industry] = industries.get(industry, 0) + 1
        
        st.markdown("**Industries in your network:**")
        for industry, count in industries.items():
            st.markdown(f"- {industry}: {count} connections")
        
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.warning("Your LinkedIn account is not connected.")
        st.markdown("""
        To connect your LinkedIn account:
        1. Configure your LinkedIn API credentials in the sidebar
        2. Click the "Connect to LinkedIn" button
        
        For demo purposes, sample connections data is being used.
        """)
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
        st.session_state.recommendations = generate_recommendations(5)
    
    # Display refresh button
    if st.button("Refresh Recommendations"):
        with st.spinner("Generating fresh recommendations..."):
            time.sleep(1)  # Simulate processing time
            st.session_state.recommendations = generate_recommendations(5)
    
    # Create a two-column layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Display recommendations
        for i, contact in enumerate(st.session_state.recommendations):
            is_selected = st.session_state.selected_contact and st.session_state.selected_contact["id"] == contact["id"]
            
            st.markdown(
                f"<div class='contact-card {'' if not is_selected else 'selected'}' id='contact-{contact['id']}'>",
                unsafe_allow_html=True
            )
            
            # Contact header with score
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.markdown(f"### {contact['firstName']} {contact['lastName']}")
                st.markdown(f"**{contact['role']}** at **{contact['company']}**")
            
            with col_b:
                st.markdown(
                    f"<div style='text-align: right;'><span class='badge badge-green'>{contact['score']}% Match</span></div>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<div style='text-align: right;'><small>{contact['matchStrength']}</small></div>",
                    unsafe_allow_html=True
                )
            
            # Contact details and insights
            st.markdown("<div style='margin-top: 0.5rem;'>", unsafe_allow_html=True)
            
            # Display badges for industry and expertise
            expertise_items = contact['expertise'].split(',')[0:2] if ',' in contact['expertise'] else [contact['expertise']]
            badges_html = f"<span class='badge badge-gray'>{contact['industry']}</span> "
            for exp in expertise_items:
                badges_html += f"<span class='badge badge-blue'>{exp.strip()}</span> "
            
            st.markdown(f"<div>{badges_html}</div>", unsafe_allow_html=True)
            
            # Display insights
            st.markdown("<div style='margin-top: 0.5rem;'>", unsafe_allow_html=True)
            for insight in contact['insights']:
                st.markdown(f"• {insight}")
            st.markdown("</div>", unsafe_allow_html=True)

# Add footer
st.markdown("""
<div style="text-align: center; margin-top: 2rem; padding: 1rem; border-top: 1px solid #E5E7EB;">
    <p>LinkedIn AI Networking Assistant - Powered by Claude AI</p>
    <p><small>© 2025 All Rights Reserved</small></p>
</div>
""", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Action buttons
            col_a, col_b = st.columns([1, 1])
            with col_a:
                view_button = st.button("View Profile", key=f"view_{contact['id']}")
                if view_button:
                    st.session_state.selected_contact = contact
            
            with col_b:
                message_button = st.button("Create Message", key=f"message_{contact['id']}")
                if message_button:
                    st.session_state.selected_contact = contact
                    st.session_state.active_tab = "messages"
                    st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        # Display selected contact detail
        if st.session_state.selected_contact:
            contact = st.session_state.selected_contact
            
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            
            # Contact header
            st.markdown(f"### {contact['firstName']} {contact['lastName']}")
            st.markdown(f"**{contact['role']}** at **{contact['company']}**")
            
            # LinkedIn profile link
            if "profileUrl" in contact:
                st.markdown(f"[View LinkedIn Profile]({contact['profileUrl']})")
            
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            
            # Contact details
            st.markdown("<div class='contact-detail'>", unsafe_allow_html=True)
            st.markdown("<span class='contact-detail-label'>Industry:</span>", unsafe_allow_html=True)
            st.markdown(contact['industry'])
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='contact-detail'>", unsafe_allow_html=True)
            st.markdown("<span class='contact-detail-label'>Expertise:</span>", unsafe_allow_html=True)
            st.markdown(contact['expertise'])
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='contact-detail'>", unsafe_allow_html=True)
            st.markdown("<span class='contact-detail-label'>Recent Projects:</span>", unsafe_allow_html=True)
            st.markdown(contact['recentProjects'])
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='contact-detail'>", unsafe_allow_html=True)
            st.markdown("<span class='contact-detail-label'>Key Achievements:</span>", unsafe_allow_html=True)
            st.markdown(contact['keyAchievements'])
            st.markdown("</div>", unsafe_allow_html=True)
            
            if contact["mutualConnections"] > 0:
                st.markdown("<div class='contact-detail'>", unsafe_allow_html=True)
                st.markdown("<span class='contact-detail-label'>Mutual Connections:</span>", unsafe_allow_html=True)
                st.markdown(f"{contact['mutualConnections']} connections")
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
            
            view_on_linkedin = st.button("View on LinkedIn", key="view_on_linkedin")
            if view_on_linkedin and "profileUrl" in contact:
                # In a real app, this would open the LinkedIn profile
                st.markdown(f"<script>window.open('{contact['profileUrl']}', '_blank');</script>", unsafe_allow_html=True)
                st.info(f"Opening {contact['firstName']}'s LinkedIn profile...")
            
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
            st.markdown(f"### Creating LinkedIn message for {contact['firstName']} {contact['lastName']}")
            st.markdown(f"**{contact['role']}** at **{contact['company']}**")
            
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
                placeholder=f"e.g., {contact['expertise'].split(',')[0] if ',' in contact['expertise'] else contact['expertise']} trends"
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
                2. Visit the contact's LinkedIn profile
                3. Click "Message" and paste your personalized message
                """)
                
                col_a, col_b = st.columns([3, 1])
                
                with col_b:
                    copy_button = st.button("📋 Copy to Clipboard")
                    if copy_button:
                        st.write("Message copied to clipboard!")
                        st.write("")  # This is a placeholder for JavaScript (which doesn't work in pure Streamlit)
                
                with col_a:
                    if "profileUrl" in contact:
                        linkedin_button = st.button("Open LinkedIn Profile", type="primary")
                        if linkedin_button:
                            # In a real app, this would open the URL
                            st.info(f"Opening {contact['firstName']}'s LinkedIn profile...")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            
            st.markdown("### Contact Insights")
            
            # Key information about the contact
            st.markdown("<div class='contact-detail'>", unsafe_allow_html=True)
            st.markdown("<span class='contact-detail-label'>Industry:</span>", unsafe_allow_html=True)
            st.markdown(contact['industry'])
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='contact-detail'>", unsafe_allow_html=True)
            st.markdown("<span class='contact-detail-label'>Expertise:</span>", unsafe_allow_html=True)
            st.markdown(contact['expertise'])
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='contact-detail'>", unsafe_allow_html=True)
            st.markdown("<span class='contact-detail-label'>Recent Projects:</span>", unsafe_allow_html=True)
            st.markdown(contact['recentProjects'])
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            
            # Goal-focused messaging tips
            st.markdown("### Tips for Your Networking Goal")
            
            if st.session_state.networking_goal == "Career Advancement":
                st.markdown("""
                **Career Advancement Tips:**
                - Mention specific aspects of their career path you admire
                - Ask for advice rather than opportunities
                - Reference a specific achievement or project that impressed you
                - Be clear about your own career aspirations
                """)
            elif st.session_state.networking_goal == "Industry Knowledge":
                st.markdown("""
                **Industry Knowledge Tips:**
                - Reference specific content they've created or projects they've worked on
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
                        st.session_state.generated_message = f"Hi {contact['firstName']},\n\n{starter}\n\nWould you be open to a brief conversation about this? I'd appreciate your insights.\n\nBest regards,\n{st.session_state.user_profile['name']}"
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
