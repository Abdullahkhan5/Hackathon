from langchain.document_loaders import DirectoryLoader

def load_docs(directory):
  loader = DirectoryLoader(directory,show_progress=True)
  documents = loader.load()
  return documents