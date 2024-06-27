from flask import Flask, request, render_template, redirect, url_for, flash
from loader import load_docs
import os
from langchain.prompts import ChatPromptTemplate
from job_parser import job_template, format_instructions_job, turbo_llm_memory
from resume_parser import resume_template, format_instructions_resume
from embeddings import calculate_similarities, calculate_avg_similarity
import smtplib
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.mime.multipart import MIMEMultipart
from meetings import get_invitations, get_meeting_timings
import random
from crewai_tools import PDFSearchTool
from langchain_community.tools import DuckDuckGoSearchRun
from agents import analyst_agent, interviewer_agent, researcher_agent
from crewai import Crew
from generate_pdf import generate_pdf

job_prompt = ChatPromptTemplate.from_template(template=job_template)
resume_prompt = ChatPromptTemplate.from_template(template=resume_template)

job_description = ""
job_designation = ""
link = ""
documents = []
# sorted_indices = []
sorted_candidates = []
sorted_avg_similarities = []
successful_candidates = []
file_names = []


app = Flask(__name__)
app.secret_key = 'my_secret_key'
# app.config['UPLOAD_FOLDER'] = 'uploads/'

# if not os.path.exists(app.config['UPLOAD_FOLDER']):
#     os.makedirs(app.config['UPLOAD_FOLDER'])

# if not os.path.exists(app.config['UPLOAD_FOLDER'] + '/JD'):
#     os.makedirs(app.config['UPLOAD_FOLDER'] + '/JD')

# if not os.path.exists(app.config['UPLOAD_FOLDER'] + '/Resumes'):
#     os.makedirs(app.config['UPLOAD_FOLDER'] + '/Resumes')

app.config['STATIC_FOLDER'] = 'static/'

if not os.path.exists(app.config['STATIC_FOLDER']):
    os.makedirs(app.config['STATIC_FOLDER'])

if not os.path.exists(app.config['STATIC_FOLDER'] + '/JD'):
    os.makedirs(app.config['STATIC_FOLDER'] + '/JD')

if not os.path.exists(app.config['STATIC_FOLDER'] + '/Resumes'):
    os.makedirs(app.config['STATIC_FOLDER'] + '/Resumes')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    global job_description, documents

    job_description = request.form['jobDescription']
    files = request.files.getlist('files')

    with open(os.path.join(app.config['STATIC_FOLDER'] + '/JD', 'job_description.txt'), 'w') as f:
        f.write(job_description)

    for file in files:
        if file:
            file.save(os.path.join(app.config['STATIC_FOLDER'] + '/Resumes', file.filename))

    documents = load_docs(os.path.join(app.config['STATIC_FOLDER'], 'Resumes'))

    num_documents = len(documents)

    messages = job_prompt.format_messages(text=job_description,
                                format_instructions=format_instructions_job)

    job_description = turbo_llm_memory(messages)

    job_description = job_description.content

    return render_template('load.html', num_documents=num_documents)

@app.route('/analyze', methods=['GET','POST'])
def analyze():
    global documents, job_description, sorted_candidates, sorted_avg_similarities, job_designation, sorted_file_names

    if request.method == 'POST':

        total_responses = []

        for document in documents:
            messages = resume_prompt.format_messages(text=document.page_content,
                                            format_instructions=format_instructions_resume)

            resume_response = turbo_llm_memory(messages)

            total_responses.append(resume_response.content)

            file_names.append(document.metadata['source'][7:].replace('\\', '/'))

        skill_similarity, education_similarity, education_level_similarity, candidates_info, job_designation = calculate_similarities(job_description, total_responses)

        avg_similarity = calculate_avg_similarity(skill_similarity, education_similarity, education_level_similarity)

        sorted_indices = sorted(range(len(avg_similarity)), key=lambda k: avg_similarity[k], reverse=True)

        sorted_avg_similarities = [avg_similarity[i] for i in sorted_indices]
        sorted_candidates = [candidates_info[i] for i in sorted_indices]
        sorted_file_names = [file_names[i] for i in sorted_indices]

        # filtered_indices = [i for i in sorted_indices if avg_similarity[i] >= 50]

        # sorted_avg_similarities = [avg_similarity[i] for i in filtered_indices]
        # sorted_candidates = [candidates_info[i] for i in filtered_indices]
        # sorted_file_names = [file_names[i] for i in filtered_indices]


    return render_template('analyze.html', avg_similarity=sorted_avg_similarities, candidates_info=sorted_candidates, file_names=sorted_file_names)

@app.route('/more_info/<int:candidate_no>', methods=['POST'])
def candidate_details(candidate_no):
    if request.method == 'POST':
        file_name = request.form.get('file_name')
        candidate_info = sorted_candidates[candidate_no]
        return render_template('details.html', candidate_info=candidate_info, file_name=file_name)
    #     return redirect(url_for('candidate_details', candidate_no=candidate_no, file_name=file_name))
    # else:
    #     candidate_info = sorted_candidates[candidate_no]
    #     file_name = request.args.get('file_name', '')
    #     return render_template('details.html', candidate_info=candidate_info, file_name=file_name)

@app.route('/email', methods=['GET', 'POST'])
def email():
    global job_designation, sorted_candidates, sorted_avg_similarities, sorted_file_names, successful_candidates, link
    if request.method == 'POST':
        sender = request.form['sender']
        link = request.form['calendly']

        successful_emails_count = 0

        password = 'usey wwiv potg lstg'

        subject = f'Interview for {job_designation} at Techlogix'

        recipients = ["fahadabdullah2376@gmail.com", "jawaangs1@gmail.com", "pythondummy377@gmail.com","rcsr377@gmail.com", "sstriker681@gmail.com"]
        # recipients = ["fahadabdullah2376@gmail.com", "jawaangs1@gmail.com", "pythondummy377@gmail.com"]

        for index in range(5):
            candidate_name = sorted_candidates[index]['Name']
            candidate_score = sorted_avg_similarities[index]
            receiver = recipients[index]
            # receiver = random.choice(recipients)
            file_name = sorted_file_names[index]
            
            body = f'''
            Dear {candidate_name},

            Thank you for your interest in the {job_designation} role at Techlogix. We are delighted to have received your application and are currently in the process of reviewing all the submissions.

            Your application has advanced to the next stage of our recruitment process, and we would like to invite you to participate in a short interview with our team.
            Please select a time slot for the interview from the calendly link: {link}
            '''

            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = receiver

            try:
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
                    smtp_server.login(sender, password)
                    smtp_server.sendmail(sender, receiver, msg.as_string())
                successful_emails_count += 1
                successful_candidates.append([candidate_name, receiver, candidate_score, file_name])
            except Exception as e:
                print(f"Error: {e}")

        return render_template('success.html', successful_emails_count=successful_emails_count)
    else:
        return render_template('email.html')
    
@app.route('/meeting_schedule')
def schedule():
    global successful_candidates

    invites, events, invitation_accepted_emails = get_invitations()
    scheduled_timings = get_meeting_timings(invites, events, successful_candidates, invitation_accepted_emails)

    return render_template('schedule.html', scheduled_timings = scheduled_timings)    

@app.route('/questions_mail', methods=['POST'])
def generate_questions():
    candidate_file = request.form['file_name']

    pdf_tool = PDFSearchTool(pdf=f'static/{candidate_file}')

    search_tool = DuckDuckGoSearchRun()

    agent1, task1 = analyst_agent(pdf_tool)
    agent2, task2 = interviewer_agent(pdf_tool)
    agent3, task3 = researcher_agent(pdf_tool, search_tool)

    crew = Crew(
        agents=[agent1, agent2, agent3],
        tasks=[task1, task2, task3],
        verbose=2, # You can set it to 1 or 2 to different logging levels
        )
    
    # Get your crew to work!
    result = crew.kickoff()

    generate_pdf(result)

    sender_email = "fahadabdullah377@gmail.com"
    sender_password = 'usey wwiv potg lstg'
    recipient_email = "rcsr377@gmail.com"
    subject = "Interview Questions"
    body = f'''
            Hi Recuriter,

            Here are the sample questions which you can ask during the interview
            '''


    with open("interview_questions.pdf", "rb") as attachment:
        # Add the attachment to the message
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= interview_questions.pdf",
    )

    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = sender_email
    message['To'] = recipient_email
    html_part = MIMEText(body)
    message.attach(html_part)
    message.attach(part)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        flash('Email Sent Successfully', 'success')

    except Exception as e:
        flash(f'Email not sent due to some error: {e}', 'danger')

    return redirect(url_for('schedule'))

@app.route('/reschedule_interview', methods=['POST'])
def reschedule_interview():
    interview_timing = request.form['interview_timing']
    candidate_name = request.form['candidate_name']
    candidate_email = request.form['candidate_email']

    sender_email = "fahadabdullah377@gmail.com"
    sender_password = 'usey wwiv potg lstg'
    recipient_email = candidate_email
    subject = "Reschedule Interview"
    body = f'''
    Dear {candidate_name},

    I hope this email finds you well. I am writing to inform you that, due to some unfortunate reasong, we need to reschedule the interview initially set for {interview_timing}.

    To facilitate the rescheduling process, please use the following Calendly link to select a new date and time that works best for you:

    {link}

    I apologize for any inconvenience this may cause and appreciate your understanding. We look forward to speaking with you soon.
    '''

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(sender_email, sender_password)
            smtp_server.sendmail(sender_email, recipient_email, msg.as_string())
        flash('Email Sent Successfully', 'success')
    except Exception as e:
        flash(f'Email not sent due to some error: {e}', 'danger')
    

    return redirect(url_for('schedule'))

if __name__ == '__main__':
    app.run(debug=True)
