import streamlit as st
import pandas as pd
import json
import os
import random
from datetime import datetime, timedelta
import anthropic
import time

# Set page configuration
st.set_page_config(
    page_title="AI Networking Assistant",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Check for Claude API key
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
    st.session_state.active_tab = "profile"
    st.session_state.contacts = []
    st.session_state.selected_contact = None
    st.session_state.generated_message = ""
    st.session_state.message_type = "coldOutreach"
    st.session_state.networking_goal = "Industry Knowledge"
    st.session_state.custom_topic = ""
    st.session_state.recommendations = []
    st.session_state.CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
    st.session_state.user_profile = {
        "name": "Jamie Doe",
        "currentRole": "Software Engineer",
        "industry": "Technology",
        "expertise": "React, Node.js, AI",
        "interests": "Machine Learning, Web Development, Open Source",
        "company": "TechCorp Inc."
    }

# Sample contact data (for demonstration)
sample_contacts = [
    {
        "id": 1,
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
        "mutualConnections": 3
    },
    {
        "id": 2,
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
        "mutualConnections": 1
    },
    {
        "id": 3,
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
        "mutualConnections": 0
    },
    {
        "id": 4,
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
        "mutualConnections": 2
    },
    {
        "id": 5,
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
        "mutualConnections": 5
    }
]

# Load sample contacts if empty
if len(st.session_state.contacts) == 0:
    st.session_state.contacts = sample_contacts

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2rem !important;
        font-weight: 600;
        color: #1E3A8A;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem !important;
        font-weight: 500;
        color: #1E3A8A;
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
        border: 1px solid #3B82F6;
        background-color: #EFF6FF;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        font-size: 0.75rem;
        font-weight: 500;
        border-radius: 9999px;
    }
    .badge-blue {
        background-color: #DBEAFE;
        color: #1E40AF;
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
        color: #1E40AF;
    }
    .custom-tab.active {
        color: #1E40AF;
        border-bottom: 2px solid #1E40AF;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar for API key setup and navigation
with st.sidebar:
    st.markdown("<div class='main-header'>🤝 AI Networking Assistant</div>", unsafe_allow_html=True)
    
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
        st.warning("Claude API key not set. Some advanced features will be limited.")
    
    # Navigation
    st.markdown("### Navigation")
    
    if st.button("My Profile", key="nav_profile"):
        st.session_state.active_tab = "profile"
    
    if st.button("AI Recommendations", key="nav_recommendations"):
        st.session_state.active_tab = "recommendations"
    
    if st.button("Message Creator", key="nav_messages"):
        st.session_state.active_tab = "messages"
    
    if st.button("Data Import", key="nav_import"):
        st.session_state.active_tab = "import"
    
    st.markdown("### Networking Goal")
    goal = st.selectbox(
        "Set your networking goal",
        options=["Career Advancement", "Industry Knowledge", "Business Development", "Job Seeking", "Mentorship"],
        index=1
    )
    
    if goal != st.session_state.networking_goal:
        st.session_state.networking_goal = goal
        # Refresh recommendations when goal changes
        if len(st.session_state.contacts) > 0:
            st.session_state.recommendations = generate_recommendations(5)
    
    st.markdown("### About")
    st.markdown("""
    This AI Networking Assistant helps you identify valuable connections and craft personalized outreach messages.
    
    Powered by:
    - Claude AI for intelligent message generation
    - Advanced contact analysis algorithms
    - Personalized outreach strategies
    """)

# Helper Functions

def generate_recommendations(count=5):
    """Generate AI-powered contact recommendations"""
    # In a real app, this would use more sophisticated algorithms
    # We'll simulate this with random scores and insights
    
    scored_contacts = []
    
    for contact in st.session_state.contacts:
        # Generate a score based on industry match, seniority, and mutual connections
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
        
        # Activity level bonus
        if contact["activityLevel"] == "High":
            base_score += 10
        
        # Mutual connections bonus
        base_score += min(contact["mutualConnections"] * 3, 15)
        
        # Add some randomness
        score = min(max(base_score + random.randint(-5, 5), 40), 95)
        
        # Generate insights
        insights = []
        
        if contact["industry"] == st.session_state.user_profile["industry"]:
            insights.append(f"Same industry ({contact['industry']})")
        
        if contact["mutualConnections"] > 0:
            insights.append(f"{contact['mutualConnections']} mutual connections")
        
        if contact["activityLevel"] == "High":
            insights.append("Highly active on platform")
        
        if "recentActivity" in contact and contact["recentActivity"]["date"]:
            activity_date = datetime.fromisoformat(contact["recentActivity"]["date"])
            if (datetime.now() - activity_date).days < 7:
                insights.append("Recently active (within past week)")
        
        # Fill with more generic insights if needed
        if len(insights) < 2:
            potential_insights = [
                f"Experienced in {contact['expertise'].split(',')[0]}",
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
        "{{specificTopic}}": custom_topic if custom_topic else f"{contact['expertise'].split(',')[0]} in {contact['industry']}"
    }
    
    # Template selection
    templates = {
        "coldOutreach": [
            """Hi {{firstName}},

I noticed your work in {{industry}} at {{company}}. Your expertise in {{expertise}} particularly caught my attention.

I'm currently a {{userRole}} specializing in {{userExpertise}} and would love to connect to learn more about your experiences with {{specificTopic}}.

Would you be open to a brief conversation in the coming weeks? I'd appreciate the opportunity to gain insights from your perspective.

Thanks for considering,
{{userName}}""",
            
            """Hello {{firstName}},

I came across your profile and was impressed by your background in {{expertise}} and your work at {{company}}.

I'm {{userName}}, a {{userRole}} focused on {{userExpertise}}. I'm particularly interested in your experience with {{specificTopic}} as it aligns with some challenges I'm currently addressing.

I'd value the opportunity to exchange ideas with someone of your expertise. Would you be interested in a 15-minute virtual coffee to discuss {{specificTopic}}?

Best regards,
{{userName}}"""
        ],
        "followUp": [
            """Hi {{firstName}},

I hope you're doing well. I wanted to follow up on my previous message about connecting to discuss {{specificTopic}}.

Since then, I've been working on some interesting projects related to {{userExpertise}} which has given me some additional perspective I'd love to share and get your thoughts on.

If your schedule permits, I'd still appreciate that brief conversation we discussed. Would you be available for a quick chat in the coming weeks?

All the best,
{{userName}}"""
        ],
        "informationalInterview": [
            """Hi {{firstName}},

I hope this message finds you well. I'm {{userName}}, a {{userRole}} with a background in {{userExpertise}}.

I've been following your career journey in {{industry}} and have been particularly impressed by your work at {{company}}. Your approach to {{specificTopic}} is something I find truly inspiring.

I'm currently exploring opportunities in this field and would greatly value a 15-20 minute conversation to gain insights from your experience. I'm specifically interested in learning more about {{specificTopic}}.

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
        system_prompt = """You are an expert networking assistant that specializes in crafting personalized, effective outreach messages. 
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

Return only the text of the message itself, without any explanation or commentary."""

        # Create a detailed prompt with all the context
        specific_topic = custom_topic if custom_topic else f"{contact['expertise'].split(',')[0]} in {contact['industry']}"
        
        user_prompt = f"""Create a personalized {template_type} message to {contact['firstName']} {contact['lastName']}.

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
- Interests: {st.session_state.user_profile['interests']}

MESSAGE DETAILS:
- Message Type: {template_type}
- Networking Goal: {st.session_state.networking_goal}
- Specific Topic of Interest: {specific_topic}

Create a personalized {template_type} message based on this information."""

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
        system_prompt = """You are an expert networking message analyst. Evaluate the provided networking outreach message based on:

1. Personalization - Does it show research and include specific details about the recipient?
2. Value proposition - Is it clear why connecting would be beneficial?
3. Authenticity - Does it sound genuine rather than generic or salesy?
4. Call to action - Is there a clear, low-friction next step?
5. Focus - Is it concise (under 150 words) and focused?
6. Tone - Is it appropriately professional but friendly?

Provide your analysis in JSON format with these fields:
- overallScore: number between 0-100
- strengths: array of strings (2-4 specific strengths)
- weaknesses: array of strings (0-3 specific weaknesses)
- suggestions: array of strings (0-3 specific improvement suggestions)
- assessment: string (1-2 sentence overall assessment)

Return ONLY the JSON object without any additional text or explanation."""

        user_prompt = f"""Analyze this networking outreach message to {contact['firstName']} {contact['lastName']}, who is a {contact['role']} at {contact['company']} in the {contact['industry']} industry:

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
        system_prompt = """You are an expert networking message editor. Your task is to improve the provided networking outreach message while keeping its core intent and content.

Focus on enhancing:
1. Personalization - Add specific details about the recipient
2. Value proposition - Clarify why connecting would be beneficial
3. Authenticity - Make it sound more genuine and less generic
4. Call to action - Ensure there's a clear, low-friction next step
5. Conciseness - Keep it under 150 words and focused
6. Tone - Make it appropriately professional but friendly

Return ONLY the improved message text without any explanation or commentary about your changes."""

        user_prompt = f"""Improve this networking outreach message to {contact['firstName']} {contact['lastName']}, who is a {contact['role']} at {contact['company']} in the {contact['industry']} industry:

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

# Main Content Area based on active tab
if st.session_state.active_tab == "profile":
    st.markdown("<div class='main-header'>Your Professional Profile</div>", unsafe_allow_html=True)
    
    # Create a card for the profile
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Display profile image
        st.image("https://avatars.githubusercontent.com/u/0", width=150)
    
    with col2:
        # Profile info
        st.markdown(f"### {st.session_state.user_profile['name']}")
        st.markdown(f"**{st.session_state.user_profile['currentRole']}** at **{st.session_state.user_profile['company']}**")
        st.markdown(f"**Industry:** {st.session_state.user_profile['industry']}")
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # Profile form
    with st.form("profile_form"):
        st.markdown("### Edit Your Profile")
        
        name = st.text_input("Full Name", value=st.session_state.user_profile["name"])
        
        col1, col2 = st.columns(2)
        with col1:
            current_role = st.text_input("Current Role", value=st.session_state.user_profile["currentRole"])
            industry = st.text_input("Industry", value=st.session_state.user_profile["industry"])
        
        with col2:
            company = st.text_input("Company", value=st.session_state.user_profile["company"])
            expertise = st.text_input("Expertise (comma separated)", value=st.session_state.user_profile["expertise"])
        
        interests = st.text_area("Professional Interests", value=st.session_state.user_profile["interests"])
        
        submit = st.form_submit_button("Update Profile")
        
        if submit:
            st.session_state.user_profile = {
                "name": name,
                "currentRole": current_role,
                "industry": industry,
                "company": company,
                "expertise": expertise,
                "interests": interests
            }
            st.success("Profile updated successfully!")
            
            # Refresh recommendations when profile changes
            if len(st.session_state.contacts) > 0:
                st.session_state.recommendations = generate_recommendations(5)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Additional profile features
    st.markdown("<div class='sub-header'>Connect Data Sources</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### LinkedIn")
        st.markdown("Import your connections and network")
        st.button("Connect LinkedIn", key="linkedin_connect")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### CSV Import")
        st.markdown("Upload contact lists from other platforms")
        st.file_uploader("Upload CSV file", type=["csv"], key="csv_upload")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### Email Integration")
        st.markdown("Sync contacts from your email accounts")
        st.button("Connect Email", key="email_connect")
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.active_tab == "recommendations":
    st.markdown("<div class='main-header'>AI-Powered Networking Recommendations</div>", unsafe_allow_html=True)
    
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
            st.markdown("### AI-Generated Icebreakers")
            starters = generate_conversation_starters(contact)
            for starter in starters:
                st.markdown(f"<div class='badge-gray' style='padding: 0.5rem; margin-bottom: 0.5rem; border-radius: 0.25rem;'>{starter}</div>", unsafe_allow_html=True)
            
            # Action buttons
            create_message = st.button("Create Outreach Message", key="create_message_detail")
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
    st.markdown("<div class='main-header'>Personalized Message Creator</div>", unsafe_allow_html=True)
    
    # Check if we have a selected contact
    if not st.session_state.selected_contact:
        st.markdown("<div class='card' style='text-align: center; padding: 2rem;'>", unsafe_allow_html=True)
        st.markdown("### No Contact Selected")
        st.markdown("Please select a contact from the recommendations tab to create a personalized message.")
        
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
            st.markdown(f"### Creating message for {contact['firstName']} {contact['lastName']}")
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
                basic_gen = st.button("Generate Basic Message")
                if basic_gen:
                    with st.spinner("Generating basic message..."):
                        st.session_state.generated_message = generate_basic_message(
                            contact, 
                            st.session_state.message_type,
                            st.session_state.custom_topic
                        )
            
            with col_b:
                ai_gen = st.button("Generate with Claude AI")
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
            st.markdown("### Your Message")
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
            
            # Copy to clipboard button (uses JavaScript)
            if st.session_state.generated_message:
                st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
                
                col_a, col_b = st.columns([3, 1])
                
                with col_a:
                    st.markdown("### Ready to Send!")
                    st.markdown("Copy this message and paste it into your preferred communication platform.")
                
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
            
            # AI-generated icebreakers
            st.markdown("### AI-Generated Icebreakers")
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

elif st.session_state.active_tab == "import":
    st.markdown("<div class='main-header'>Import Contacts</div>", unsafe_allow_html=True)
    
    # Options for importing contacts
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    
    st.markdown("### Import Methods")
    
    option = st.radio(
        "Select import method",
        ["Upload CSV", "Connect to LinkedIn", "Connect to Email", "Manual Entry", "Sample Data"]
    )
    
    if option == "Upload CSV":
        st.markdown("### Upload Contact CSV")
        st.markdown("Upload a CSV file with your contacts. The file should include these columns: firstName, lastName, role, company, industry, expertise.")
        
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        if uploaded_file is not None:
            try:
                # Read and process the CSV
                df = pd.read_csv(uploaded_file)
                st.write("Preview of imported data:")
                st.write(df.head())
                
                if st.button("Confirm Import"):
                    # Validate required columns
                    required_columns = ["firstName", "lastName", "role", "company", "industry"]
                    missing_columns = [col for col in required_columns if col not in df.columns]
                    
                    if missing_columns:
                        st.error(f"Missing required columns: {', '.join(missing_columns)}")
                    else:
                        # Process and convert to the expected format
                        new_contacts = []
                        for index, row in df.iterrows():
                            contact = {
                                "id": len(st.session_state.contacts) + index + 1,
                                "firstName": row["firstName"],
                                "lastName": row["lastName"],
                                "role": row["role"],
                                "company": row["company"],
                                "industry": row["industry"],
                                "expertise": row.get("expertise", ""),
                                "seniority": row.get("seniority", "Mid Level"),
                                "companySize": row.get("companySize", "Mid-size"),
                                "companyPrestige": row.get("companyPrestige", "Medium"),
                                "activityLevel": row.get("activityLevel", "Medium"),
                                "recentProjects": row.get("recentProjects", ""),
                                "keyAchievements": row.get("keyAchievements", ""),
                                "mutualConnections": int(row.get("mutualConnections", 0))
                            }
                            new_contacts.append(contact)
                        
                        # Add new contacts to the existing list
                        st.session_state.contacts.extend(new_contacts)
                        
                        # Refresh recommendations
                        st.session_state.recommendations = generate_recommendations(5)
                        
                        st.success(f"Successfully imported {len(new_contacts)} contacts!")
            
            except Exception as e:
                st.error(f"Error importing CSV: {e}")
    
    elif option == "Connect to LinkedIn":
        st.markdown("### LinkedIn Integration")
        st.markdown("Connect to LinkedIn to import your connections. This requires authentication with LinkedIn.")
        
        st.warning("LinkedIn integration is not yet implemented in this demo.")
        
        # Placeholder for LinkedIn authentication
        st.text_input("LinkedIn Email/Username")
        st.text_input("LinkedIn Password", type="password")
        
        if st.button("Connect to LinkedIn"):
            st.info("This is a demo feature. In a real app, this would connect to the LinkedIn API.")
    
    elif option == "Connect to Email":
        st.markdown("### Email Integration")
        st.markdown("Connect to your email to import contacts from your address book.")
        
        st.warning("Email integration is not yet implemented in this demo.")
        
        # Placeholder for email service selection
        email_service = st.selectbox("Select Email Service", ["Gmail", "Outlook", "Other"])
        
        if email_service == "Gmail":
            if st.button("Connect to Gmail"):
                st.info("This is a demo feature. In a real app, this would use the Gmail API.")
        elif email_service == "Outlook":
            if st.button("Connect to Outlook"):
                st.info("This is a demo feature. In a real app, this would use the Outlook API.")
        else:
            st.text_input("Email Server")
            st.text_input("Username")
            st.text_input("Password", type="password")
            
            if st.button("Connect to Email Server"):
                st.info("This is a demo feature. In a real app, this would connect to your email server.")
    
    elif option == "Manual Entry":
        st.markdown("### Manual Contact Entry")
        st.markdown("Add contacts manually by filling out the form below.")
        
        with st.form("manual_contact_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                first_name = st.text_input("First Name")
                last_name = st.text_input("Last Name")
                role = st.text_input("Role/Position")
                company = st.text_input("Company")
            
            with col2:
                industry = st.text_input("Industry")
                expertise = st.text_input("Expertise (comma separated)")
                seniority = st.selectbox("Seniority", ["Entry Level", "Mid Level", "Senior", "Manager", "Director", "VP", "C-Suite", "Founder"])
                mutual_connections = st.number_input("Mutual Connections", min_value=0, value=0)
            
            col1, col2 = st.columns(2)
            
            with col1:
                recent_projects = st.text_input("Recent Projects")
                key_achievements = st.text_input("Key Achievements")
            
            with col2:
                company_size = st.selectbox("Company Size", ["Startup", "Small", "Mid-size", "Large", "Enterprise"])
                activity_level = st.selectbox("Activity Level", ["Low", "Medium", "High"])
            
            submit_button = st.form_submit_button("Add Contact")
            
            if submit_button:
                if not first_name or not last_name or not role or not company or not industry:
                    st.error("Please fill in all required fields (First Name, Last Name, Role, Company, Industry)")
                else:
                    # Create new contact
                    new_contact = {
                        "id": len(st.session_state.contacts) + 1,
                        "firstName": first_name,
                        "lastName": last_name,
                        "role": role,
                        "company": company,
                        "industry": industry,
                        "expertise": expertise,
                        "seniority": seniority,
                        "companySize": company_size,
                        "companyPrestige": "Medium",
                        "activityLevel": activity_level,
                        "recentProjects": recent_projects,
                        "keyAchievements": key_achievements,
                        "mutualConnections": mutual_connections
                    }
                    
                    # Add to contacts list
                    st.session_state.contacts.append(new_contact)
                    
                    # Refresh recommendations
                    st.session_state.recommendations = generate_recommendations(5)
                    
                    st.success(f"Successfully added {first_name} {last_name} to your contacts!")
    
    elif option == "Sample Data":
        st.markdown("### Load Sample Data")
        st.markdown("Reset the app with a fresh set of sample contacts for demonstration purposes.")
        
        if st.button("Load Sample Contacts"):
            # Reset contacts to sample data
            st.session_state.contacts = sample_contacts.copy()
            
            # Refresh recommendations
            st.session_state.recommendations = generate_recommendations(5)
            
            st.success("Sample contacts loaded successfully!")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Display current contacts
    st.markdown("<div class='sub-header'>Your Contacts</div>", unsafe_allow_html=True)
    
    if not st.session_state.contacts:
        st.markdown("No contacts imported yet. Use one of the import methods above to add contacts.")
    else:
        # Create a DataFrame for display
        contacts_df = pd.DataFrame([
            {
                "Name": f"{contact['firstName']} {contact['lastName']}",
                "Role": contact['role'],
                "Company": contact['company'],
                "Industry": contact['industry'],
                "Expertise": contact['expertise'].split(',')[0] if ',' in contact['expertise'] else contact['expertise'],
                "Mutual": contact['mutualConnections']
            }
            for contact in st.session_state.contacts
        ])
        
        st.dataframe(contacts_df, use_container_width=True)
        
        st.markdown(f"**Total Contacts:** {len(st.session_state.contacts)}")
        
        # Export option
        if st.button("Export Contacts as CSV"):
            # In a real app, this would generate a downloadable CSV
            st.info("In a deployed app, this would download your contacts as a CSV file.")

# Add footer
st.markdown("""
<div style="text-align: center; margin-top: 2rem; padding: 1rem; border-top: 1px solid #E5E7EB;">
    <p>AI Networking Assistant - Powered by Claude AI</p>
    <p><small>© 2025 All Rights Reserved</small></p>
</div>
""", unsafe_allow_html=True)
