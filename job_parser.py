import os
from langchain_google_genai import ChatGoogleGenerativeAI as Gemini
from langchain.output_parsers import ResponseSchema
from langchain.output_parsers import StructuredOutputParser

designation_schema = ResponseSchema(name="Designation",
                             description="Extract the Designation required for the job position")

skills_schema = ResponseSchema(name="Skills",
                             description="Extract the skills which are purely technical \
output them as a comma separated Python list.")

education_level_schema = ResponseSchema(name="Education Level",
                                    description="Extract only the minimum level of education (BS, MS, PHD)")

education_schema = ResponseSchema(name="Education",
                                    description="Extract the education fields required \
and output them as a comma separated Python list.")

response_schemas = [designation_schema,
                    skills_schema,

                    education_schema,

                    education_level_schema]

output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

format_instructions_job = output_parser.get_format_instructions()

job_template = """\
Format the output as JSON with the following keys:
Designation
Skills
Education Level
Education
text: {text}

{format_instructions}
"""

os.environ["GOOGLE_API_KEY"] = 'AIzaSyBdgDJhCDYhOoGo0hj3Qzny3pepFLU6SkQ'
turbo_llm_memory= Gemini(
    model="models/gemini-1.5-pro-latest",
    temperature=0
)