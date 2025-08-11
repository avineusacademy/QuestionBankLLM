from langchain.embeddings import HuggingFaceEmbeddings

def get_embedding_function():
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
