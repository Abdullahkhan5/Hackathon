from flask import Flask, request, render_template, redirect, url_for
from loader import load_docs
import os
from langchain.prompts import ChatPromptTemplate
from job_parser import job_template, format_instructions_job, turbo_llm_memory
from resume_parser import resume_template, format_instructions_resume
from embeddings import calculate_similarities, calculate_avg_similarity
import smtplib
from email.mime.text import MIMEText
from meetings import get_invitations, get_meeting_timings

job_prompt = ChatPromptTemplate.from_template(template=job_template)
resume_prompt = ChatPromptTemplate.from_template(template=resume_template)

job_description = ""
job_designation = ""
documents = []
sorted_candidates = []
sorted_avg_similarities = []
successful_candidates = []


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

if not os.path.exists(app.config['UPLOAD_FOLDER'] + '/JD'):
    os.makedirs(app.config['UPLOAD_FOLDER'] + '/JD')

if not os.path.exists(app.config['UPLOAD_FOLDER'] + '/Resumes'):
    os.makedirs(app.config['UPLOAD_FOLDER'] + '/Resumes')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    global job_description, documents

    job_description = request.form['jobDescription']
    files = request.files.getlist('files')

    with open(os.path.join(app.config['UPLOAD_FOLDER'] + '/JD', 'job_description.txt'), 'w') as f:
        f.write(job_description)

    for file in files:
        if file:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + '/Resumes', file.filename))

    documents = load_docs(os.path.join(app.config['UPLOAD_FOLDER'], 'Resumes'))

    num_documents = len(documents)

    messages = job_prompt.format_messages(text=job_description,
                                format_instructions=format_instructions_job)

    job_description = turbo_llm_memory(messages)

    job_description = job_description.content

    return render_template('load.html', num_documents=num_documents)

@app.route('/analyze', methods=['GET','POST'])
def analyze():
    global documents, job_description, sorted_candidates, sorted_avg_similarities, job_designation

    if request.method == 'POST':

        total_responses = []

        for document in documents:
            messages = resume_prompt.format_messages(text=document.page_content,
                                            format_instructions=format_instructions_resume)

            resume_response = turbo_llm_memory(messages)

            total_responses.append(resume_response.content)

        skill_similarity, education_similarity, education_level_similarity, candidates_info, job_designation = calculate_similarities(job_description, total_responses)

        avg_similarity = calculate_avg_similarity(skill_similarity, education_similarity, education_level_similarity)

        sorted_indices = sorted(range(len(avg_similarity)), key=lambda k: avg_similarity[k], reverse=True)

        sorted_avg_similarities = [avg_similarity[i] for i in sorted_indices]
        sorted_candidates = [candidates_info[i] for i in sorted_indices]

    return render_template('analyze.html', avg_similarity=sorted_avg_similarities, candidates_info=sorted_candidates)

@app.route('/more_info/<int:candidate_no>', methods=['GET','POST'])
def candidate_details(candidate_no):
    if request.method == 'POST':
        return redirect(url_for('candidate_details', candidate_no=candidate_no))
    else:
        candidate_info = sorted_candidates[candidate_no]
        print(candidate_no, candidate_info)
        return render_template('details.html', candidate_info=candidate_info)

@app.route('/email', methods=['GET', 'POST'])
def email():
    global job_designation, sorted_candidates, sorted_avg_similarities, successful_candidates
    if request.method == 'POST':
        sender = request.form['sender']
        link = request.form['calendly']

        successful_emails_count = 0

        password = 'usey wwiv potg lstg'

        subject = f'Interview for {job_designation} at Techlogix'

        # recipients = ["fahadabdullah2376@gmail.com", "jawaangs1@gmail.com", "pythondummy377@gmail.com","rcsr377@gmail.com", "sstriker681@gmail.com"]
        recipients = ["fahadabdullah2376@gmail.com", "jawaangs1@gmail.com", "pythondummy377@gmail.com"]

        for index in range(len(sorted_candidates)):
            candidate_name = sorted_candidates[index]['Name']
            candidate_score = sorted_avg_similarities[index]
            receiver = recipients[index]
            # receiver = random.choice(recipients)
            
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
                successful_candidates.append([candidate_name, receiver, candidate_score])
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

if __name__ == '__main__':
    app.run(debug=True)
