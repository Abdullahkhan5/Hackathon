import os
from langchain_community.chat_models import ChatOpenAI
from crewai import Agent, Task

from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

llm = ChatOpenAI(
    temperature=0,
    model_name='gpt-3.5-turbo'
)

def analyst_agent(pdf_tool):
    agent = Agent(
    role='Resume Evaluation AI',
    goal="""Determine the experience level of job candidates (fresh, experienced, senior) based on their resumes.
    Note that if professional position/role is not mentioned than dont consider adding that experience""",
    backstory="""Designed to streamline the hiring process by quickly categorizing candidates based on their resume content.""",
    verbose=True,
    allow_delegation=True,
    llm = llm,
    tools=[
            pdf_tool
        ]
    )

    # Create tasks for your agents
    task = Task(
    description="""Conduct a comprehensive analysis of the candidate resume and
    determine the experience level of job candidates (fresh, experienced, senior)
    Extract the Years of Experience (If not explicitly mentioned),
    Sum up the total durations to estimate the years of experience.

    Consider these things while determining the experience level of the candidates:
    - Note that internship experience is not considered.
    - Candidate having 3 year or less than 3 year experience is considered as fresh
    - Candidate having more than 4 years of experience is considered as experienced
    - Candidate having more than 7 years of experience is considered as senior
    """,
    expected_output="Your final answer MUST be a sentence telling the years of experience and the experience level of the candidate",
    agent=agent
    )


    return agent, task

def interviewer_agent(pdf_tool):
    agent = Agent(
    role='Interview Question Generator',
    goal="Generate tailored interview questions based on the candidate's experience level.",
    backstory="""Created to ensure interviews are appropriately challenging and relevant for each candidate's experience.""",
    verbose=True,
    allow_delegation=True,
    llm = llm,
    tools=[pdf_tool]
    )

    task = Task(
    description="""Based on the candidate's experience level from the analyst agent, generate tailored interview questions using the following guidelines:

    1. For Fresh Candidates:
    - Ask general questions for the candidate to introduce themselves.
    - Inquire about their Final Year Project (FYP) technicalities in detail.
    - Allow the candidate to mention any other relevant projects.
    - Discuss counter related technologies candidates have mentioned and ask them which one they think is better and why?
    - Pose entry-level questions related to the technical concepts of the following:
        - Object-Oriented Programming (OOP)
        - Data Structures
        - Databases
        - Candidate area of expertise if any

    2. For Candidates with Specific Experience:
    - Discuss their latest job position and role.
    - Pose questions tailored to the position being interviewed, ranging from basic to advanced based on experience.
    - Ask about the candidate's strategic perspective on why they are applying for this position and their expectations from Techlogix.
    - Depending on the candidate:
        - Explore past managerial/leadership experiences.
        - Inquire about tough challenges faced in the past and how they were resolved.
        - Discuss expectations regarding remote work or office environment.""",
    expected_output="Your final answer MUST contain 12 - 15 technical + behavorial questions and pass them to next agent",
    agent=agent
    )

    return agent, task

def researcher_agent(pdf_tool, search_tool):
    agent = Agent(
    role='Technical Questions Researcher',
    goal="""Anlayze the candidate level of experience from the interviewer agent and
    if the candidate is fresh level experience
    - then search internet for technical concepts related to OOP, Data Structures and Databases generate atleast 2 questions from each of them
    - also search internet for technologies used in the FYP/Final Year Project and generate atleast 2 questions related to them
    if the candidate is experienced
    - then generate technical questions related to the technologies/projects/skills mentioned in the document
    """,
    backstory="""Designed to create technical interview questions for candidate hiring process""",
    verbose=True,
    allow_delegation=True,
    llm = llm,  #using google gemini pro API
    tools=[
            search_tool, pdf_tool
        ]
    )

    task = Task(
    description="""Conduct a comprehensive analysis of the technical concepts mentioned in the document
    And generate questions related to their concepts them from the internet
    """,
    expected_output="""Your final answer MUST contain 1-2 behavorial questions from the interviewer agent, 1-2 questions related to their past job experiences if any and 7-8 technical questions
    Questions should be divided by sections use ### delimeter to separate sections""",
    agent=agent
    )

    return agent, task