from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sentence_transformers import SentenceTransformer
import numpy as np
import json
import nltk
import re
nltk.download('stopwords')

embed_model = SentenceTransformer('Alibaba-NLP/gte-large-en-v1.5', trust_remote_code=True)

def cleaning_data(X_list, resume):
  try:
    Y_list = word_tokenize(resume)
  except:
    resume = ' '.join([item for item in resume if item != ','])
    Y_list = word_tokenize(resume)

  sw = stopwords.words('english')

  X_set = {w for w in X_list if not w in sw}
  Y_set = {w for w in Y_list if not w in sw}

  word_pattern = re.compile(r'^\w+$')

  X_set = {item for item in X_set if word_pattern.match(item)}

  Y_set = {item for item in Y_set if word_pattern.match(item)}

  job = ', '.join(list(X_set))

  resume = ', '.join(list(Y_set))
    
  return job, resume

def embeddings(job, resume):
  embeddings1 = list(embed_model.encode(job))
  embeddings2 = list(embed_model.encode(resume))

  embeddings1 = np.squeeze(np.asarray(embeddings1))

  embeddings2 = np.squeeze(np.asarray(embeddings2))

  dot_product = np.dot(embeddings1, embeddings2)

  magnitude_x = np.sqrt(np.sum(embeddings1**2))
  magnitude_y = np.sqrt(np.sum(embeddings2**2))

  cosine_similarity = dot_product / (magnitude_x * magnitude_y)

  return cosine_similarity

def calculate_el_weightage(X_list, resume):
   try:
    Y_list = word_tokenize(resume)
   except:
    resume = ' '.join([item for item in resume if item != ','])
    Y_list = word_tokenize(resume)

   job_education_level = ', '.join(X_list)

   resume_education_level = ', '.join(Y_list)

   education_level_similarity = 0.01

   try:
     if (job_education_level[0] == 'B' and resume_education_level[0] in ['B', 'M', 'P']) or (job_education_level[0] == 'M' and resume_education_level[0] in ['M', 'P']) or (job_education_level[0] == 'P' and resume_education_level[0] in ['P']):
          education_level_similarity = 1
     elif (job_education_level[0] == 'M' and resume_education_level[0] in ['B']) or  (job_education_level[0] == 'P' and resume_education_level[0] in ['M']):
          education_level_similarity = 0.5
     elif (job_education_level[0] == 'P' and resume_education_level[0] in ['B']):
          education_level_similarity = 0.1
   except Exception:
        education_level_similarity = 0.05

   return education_level_similarity

def calculate_similarities(job_description, responses):

    skills_similarities = []
    education_similarities = []
    education_level_similarities = []

    cleaned_data = job_description.replace("```json", '').replace("'", "").replace('\n', '').replace('\t', '').replace('```', '')

    # Convert the string to a JSON object
    json_data = json.loads(cleaned_data)

    job_designation = json_data.get("Designation", "")
    job_skills = json_data.get("Skills", "")
    job_education = json_data.get("Education", "")
    job_education_level = json_data.get("Education Level", "")

    X_skills_list = word_tokenize(''.join(job_skills))
    X_education_list = word_tokenize(''.join(job_education))
    X_el_list = word_tokenize(''.join(job_education_level))

    candidates_info = []

    for index in range(len(responses)):
        cleaned_data = responses[index].replace("```json", '').replace("'", "").replace('\n', '').replace('\t', '').replace('```', '')

        data_dict = json.loads(cleaned_data)

        candidates_info.append(extract_candidate_info(data_dict))

        print(candidates_info[index])

        resume_skills = candidates_info[index]['Skills']
        resume_education = candidates_info[index]['Education']
        resume_education_level = candidates_info[index]['Education Level']

        job_skills, resume_skills = cleaning_data(X_skills_list, resume_skills)
        job_education, resume_education = cleaning_data(X_education_list, resume_education)

        skills_similarities.append(embeddings(job_skills, resume_skills))
        education_similarities.append(embeddings(job_education, resume_education))
        education_level_similarities.append(calculate_el_weightage(X_el_list, resume_education_level))

    return skills_similarities, education_similarities, education_level_similarities, candidates_info, job_designation

def calculate_avg_similarity(skills_similarities, education_similarities, education_level_similarities):
   avg_similarities = []

   for index in range(len(skills_similarities)):
        avg_similarity = ((skills_similarities[index] + (education_similarities[index] * education_level_similarities[index])) / 2) * 100
        avg_similarities.append(round(avg_similarity, 4))

   return avg_similarities

def extract_candidate_info(data):

    candidate_name = data.get("Name", "")
    candidate_email = data.get("Email", "")
    candidate_skills = data.get("Skills", "")
    candidate_education = data.get("Education", "")
    candidate_education_level = data.get("Education Level", "")

    candidate_info = {
        "Name": candidate_name,
        "Email": candidate_email,
        "Skills": candidate_skills,
        "Education": candidate_education,
        "Education Level": candidate_education_level
    }

    return candidate_info