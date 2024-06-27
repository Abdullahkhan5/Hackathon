Install python 3.11.1 version for the project

Create virtual environment with command
python -m venv {environment_name}

Activate the environment
{environment_name}/Scripts/Activate

Install all the necessary packages with the below commands

!pip install pinecone langchain openai
!pip install -U langchain-community
!pip install unstructured[pdf]
!pip install chromadb
!pip install tiktoken
!pip install langchain_experimental
!pip install sentence-transformers
!pip install --upgrade --quiet  fastembed
!pip install --upgrade --quiet  langchain-google-genai pillow
!pip install --q crewai
!pip install --q -U duckduckgo-search
!pip install --q langchain_google_genai

Run the below command
python app.py