"""
LearnMate AI - Personalized Learning Assistant
A comprehensive educational web application powered by Groq AI API
"""

import os
import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import re

# Import Groq
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="LearnMate AI - Personalized Learning Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI and Black Sidebar
def load_css():
    st.markdown("""
    <style>
    /* Dark Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0f0f0f !important;
        border-right: 1px solid #333333;
    }
    
    /* Sidebar Text & Navigation color overrides for dark mode */
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span {
        color: #f1f1f1 !important;
    }

    /* Main container styling */
    .main-header {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .main-header h1 {
        color: white !important;
        margin: 0;
        font-size: 2.8rem;
        font-weight: 800;
    }
    
    .main-header p {
        color: #e2e8f0 !important;
        margin-top: 0.5rem;
        font-size: 1.1rem;
    }
    
    /* Customizing the Streamlit Radio Buttons in Sidebar */
    div[role="radiogroup"] > label {
        background-color: transparent !important;
    }

    </style>
    """, unsafe_allow_html=True)

# API Key Management
def get_api_key():
    """Retrieve API key from session state or environment"""
    if "groq_api_key" in st.session_state and st.session_state.groq_api_key:
        return st.session_state.groq_api_key
    return os.getenv("GROQ_API_KEY")

def get_groq_client():
    """Initialize Groq API client safely"""
    api_key = get_api_key()
    if not api_key:
        return None
    return Groq(api_key=api_key)

# Initialize session state
def init_session_state():
    """Initialize all session state variables"""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "quiz_questions" not in st.session_state:
        st.session_state.quiz_questions = []
    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}

# Helper function to call Groq API
def call_groq_api(prompt: str, system_prompt: str = "You are a helpful educational assistant.", temperature: float = 0.7) -> Optional[str]:
    """Make API call to Groq with error handling"""
    client = get_groq_client()
    if not client:
        st.error("API Key not provided. Please enter your Groq API Key in the sidebar.")
        return None
        
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=temperature,
            max_tokens=1000
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

# Chatbot feature
def chatbot_feature():
    """Interactive chatbot for academic questions using Streamlit's native chat UI"""
    st.markdown("### 💬 Academic Chatbot")
    st.markdown("Ask me any academic question! I'm here to help explain concepts step-by-step.")
    
    if not get_api_key():
        st.warning("⚠️ Please enter your Groq API Key in the sidebar to start chatting.")
        return

    # Clear chat button aligned to the right
    col1, col2 = st.columns([8, 1])
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    st.divider()

    # Display chat messages from history on app rerun
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input using native st.chat_input
    if prompt := st.chat_input("Type your academic question here..."):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                client = get_groq_client()
                system_prompt = """You are LearnMate AI, a knowledgeable and patient educational assistant. 
                You help students with their academic questions. Provide clear, accurate, and helpful explanations. 
                Use markdown formatting to structure your answers."""
                
                try:
                    # Pass the whole conversation history for context
                    messages = [{"role": "system", "content": system_prompt}] + st.session_state.chat_history
                    
                    chat_completion = client.chat.completions.create(
                        messages=messages,
                        model="llama-3.3-70b-versatile",
                        temperature=0.7,
                        max_tokens=1000
                    )
                    response = chat_completion.choices[0].message.content
                    st.markdown(response)
                    # Add assistant response to chat history
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"Failed to generate response: {str(e)}")

# Quiz generator feature
def quiz_generator():
    """Generate multiple-choice quizzes based on topics"""
    st.markdown("### 📝 Quiz Generator")
    st.markdown("Generate custom quizzes to test your knowledge!")
    
    if not get_api_key():
        st.warning("⚠️ Please enter your Groq API Key in the sidebar to generate a quiz.")
        return

    with st.container(border=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            topic = st.text_input("Enter a topic:", placeholder="e.g., Photosynthesis, World War II")
        with col2:
            num_questions = st.number_input("Questions:", min_value=3, max_value=10, value=5)
        with col3:
            difficulty = st.selectbox("Difficulty:", ["Easy", "Medium", "Hard"])
            
        if st.button("Generate Quiz", type="primary", use_container_width=True):
            if not topic:
                st.warning("Please enter a topic!")
                return
            
            with st.spinner(f"Generating {num_questions} {difficulty} questions about {topic}..."):
                prompt = f"""Generate a {difficulty} difficulty multiple-choice quiz about {topic} with exactly {num_questions} questions.
                Format each question strictly as:
                Q1: [Question text]
                A) [Option 1]
                B) [Option 2]
                C) [Option 3]
                D) [Option 4]
                Answer: [Letter]
                Explanation: [Brief explanation]"""
                
                response = call_groq_api(prompt, "You are an expert quiz creator.", temperature=0.5)
                
                if response:
                    st.session_state.quiz_questions = parse_quiz(response)
                    st.session_state.quiz_answers = {}
                    st.rerun()
    
    # Display quiz
    if st.session_state.quiz_questions:
        st.markdown("---")
        st.markdown(f"### 📋 Your Quiz: {topic.title()}")
        
        score = 0
        user_answers = {}
        
        with st.form("quiz_form"):
            for idx, question in enumerate(st.session_state.quiz_questions):
                st.markdown(f"**{idx + 1}. {question['question']}**")
                user_answers[idx] = st.radio(
                    "Select your answer:",
                    question['options'],
                    key=f"quiz_{idx}",
                    label_visibility="collapsed",
                    index=None
                )
                st.markdown("<br>", unsafe_allow_html=True)
            
            submitted = st.form_submit_button("Submit Quiz", type="primary")
            
            if submitted:
                st.markdown("---")
                st.markdown("### 📊 Results")
                
                for idx, question in enumerate(st.session_state.quiz_questions):
                    user_answer = user_answers.get(idx)
                    
                    if not user_answer:
                        st.warning(f"Question {idx + 1}: Unanswered. Correct answer: {question['correct_answer']}")
                    else:
                        is_correct = user_answer[0] == question['correct_answer']
                        if is_correct:
                            score += 1
                            st.success(f"✅ Question {idx + 1}: Correct!")
                        else:
                            st.error(f"❌ Question {idx + 1}: Incorrect. Correct answer: {question['correct_answer']}")
                    
                    st.info(f"**Explanation:** {question['explanation']}")
                
                st.markdown(f"### 🎯 Final Score: {score}/{len(st.session_state.quiz_questions)}")

def parse_quiz(response: str) -> List[Dict]:
    """Parse quiz response into structured format"""
    questions = []
    lines = response.split('\n')
    current_question = {}
    options = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.match(r'^Q\d+:', line):
            if current_question:
                questions.append(current_question)
            current_question = {'question': line.split(':', 1)[1].strip(), 'options': [], 'correct_answer': '', 'explanation': ''}
            options = []
        elif re.match(r'^[A-D]\)', line):
            options.append(line)
            current_question['options'] = options
        elif line.startswith('Answer:'):
            current_question['correct_answer'] = line.split(':', 1)[1].strip()
        elif line.startswith('Explanation:'):
            current_question['explanation'] = line.split(':', 1)[1].strip()
            
    if current_question:
        questions.append(current_question)
    return questions

# Notes summarizer feature
def notes_summarizer():
    """Summarize study notes"""
    st.markdown("### 📄 Notes Summarizer")
    st.markdown("Paste your lengthy study notes to get a structured, concise summary.")
    
    if not get_api_key():
        st.warning("⚠️ Please enter your Groq API Key in the sidebar.")
        return

    study_notes = st.text_area(
        "Your Notes:",
        height=250,
        placeholder="Paste your study notes here...",
    )
    
    col1, col2 = st.columns([3, 1])
    with col1:
        summary_length = st.select_slider(
            "Summary Target Length:",
            options=["Very Short (Bullet Points)", "Short (1 paragraph)", "Medium (2-3 paragraphs)", "Detailed Breakdown"],
            value="Short (1 paragraph)"
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        submit_btn = st.button("Summarize Notes", type="primary", use_container_width=True)
    
    if submit_btn and study_notes:
        with st.spinner("Analyzing and summarizing your notes..."):
            prompt = f"""Provide a {summary_length} summary of the following study notes. 
            Focus strictly on key concepts, main ideas, and important details.
            
            Notes:
            {study_notes}"""
            
            summary = call_groq_api(prompt, "You are an expert study assistant skilled at creating effective academic summaries.", temperature=0.3)
            
            if summary:
                st.success("Summary Generated Successfully!")
                with st.container(border=True):
                    st.markdown(summary)

# Study recommendations feature
def study_recommendations():
    """Generate personalized study recommendations"""
    st.markdown("### 🎯 Study Recommendations")
    st.markdown("Get customized learning suggestions based on your specific learning style and goals.")
    
    if not get_api_key():
        st.warning("⚠️ Please enter your Groq API Key in the sidebar.")
        return

    with st.container(border=True):
        topic_interest = st.text_input("What topic are you studying?", placeholder="e.g., Organic Chemistry")
        
        col1, col2 = st.columns(2)
        with col1:
            learning_style = st.selectbox("Your Learning Style:", ["Visual", "Auditory", "Reading/Writing", "Kinesthetic", "Mixed"])
        with col2:
            time_available = st.select_slider("Study Time (hours/week):", options=["<5", "5-10", "10-15", "15-20", "20+"])
            
        goals = st.multiselect("Your Learning Goals:", ["Exam Preparation", "Basic Understanding", "Advanced Mastery", "Project Work"])
        
        if st.button("Get Recommendations", type="primary", use_container_width=True):
            if not topic_interest:
                st.warning("Please enter a topic you are studying.")
                return
                
            with st.spinner("Creating your personalized study plan..."):
                prompt = f"""Create a personalized study recommendation for a student studying {topic_interest}.
                Student Profile:
                - Learning Style: {learning_style}
                - Available Study Time: {time_available} hours/week
                - Goals: {', '.join(goals) if goals else 'General learning'}
                
                Provide:
                1. Recommended study schedule
                2. Specific learning resources
                3. Practical exercises
                4. Tips tailored to their learning style"""
                
                recommendations = call_groq_api(prompt, "You are an expert educational advisor.", temperature=0.6)
                
                if recommendations:
                    st.markdown("---")
                    st.markdown("### 📚 Your Personalized Study Plan")
                    st.info(recommendations)

# Sidebar navigation
def sidebar():
    """Create sidebar with navigation and configuration"""
    with st.sidebar:
        st.markdown("<h1 style='text-align: center; font-size: 2rem;'>📚 LearnMate AI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #aaaaaa;'>Your AI Study Assistant</p>", unsafe_allow_html=True)
        st.divider()
        
        # Dynamic API Key Input (if not found in env)
        if not os.getenv("GROQ_API_KEY"):
            st.markdown("#### 🔑 Setup")
            api_key_input = st.text_input("Groq API Key:", type="password", placeholder="gsk_...")
            if api_key_input:
                st.session_state.groq_api_key = api_key_input
            else:
                st.caption("You need a free API key from [Groq Console](https://console.groq.com) to use this app.")
            st.divider()
        
        # Navigation
        st.markdown("#### 🧭 Navigation")
        page = st.radio(
            "Choose a feature:",
            ["💬 Chatbot", "📝 Quiz Generator", "📄 Notes Summarizer", "🎯 Study Recommendations"],
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # Cleaned up About Section
        with st.expander("ℹ️ About LearnMate AI"):
            st.markdown("""
            **Features:**
            - 💬 Academic Chatbot
            - 📝 Custom Quiz Generator
            - 📄 Smart Notes Summarizer
            - 🎯 Personalized Study Plans
            """)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.caption("Made with ❤️ using Streamlit & Groq AI")
        
        return page

# Main app
def main():
    """Main application entry point"""
    load_css()
    init_session_state()
    
    # Refined Header
    st.markdown("""
    <div class="main-header">
        <h1>LearnMate AI</h1>
        <p>Accelerate your learning with personalized AI assistance.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get page from sidebar
    page = sidebar()
    
    # Display selected feature
    if "Chatbot" in page:
        chatbot_feature()
    elif "Quiz" in page:
        quiz_generator()
    elif "Notes" in page:
        notes_summarizer()
    elif "Study" in page:
        study_recommendations()

if __name__ == "__main__":
    main()