from langchain.output_parsers import ResponseSchema
from langchain.output_parsers import StructuredOutputParser

skills_schema = ResponseSchema(name="Skills",
                             description="Extract the skills which are purely technical\
output them as a comma separated Python list.")

name_schema = ResponseSchema(name="Name",
                                    description="Extract the name, and remember that a name does not contain delimeters or numbers inside it")

email_schema = ResponseSchema(name="Email",
                                    description="Extract the email")

education_level_schema = ResponseSchema(name="Education Level",
                                    description="Extract only the candidate highest level of education degree from either one of these(Associate, Diploma, BS, MS, PHD)")

education_schema = ResponseSchema(name="Education",
                                    description="Extract the education fields candidate has studied \
and output them as a comma separated Python list.")

response_schemas = [skills_schema,
                    email_schema,

                    name_schema,

                    education_level_schema,

                    education_schema]

output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

format_instructions_resume = output_parser.get_format_instructions()

resume_template = """\
Format the output as JSON with the following keys:
Name
Skills
Email
Education Level
Education
text: {text}

{format_instructions}
"""