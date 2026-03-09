from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

embeddings = GoogleGenerativeAIEmbeddings(
    model="text-embedding-005",
    project="project-411429ce-48ab-4ae8-aab",
    location="us-central1"
)

file_path = r"..\docs\APPLE-10k.pdf"
FAISS_INDEX_PATH = (r"..\docs\faiss_index")

def ingest_pdf() :
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200, separators=["\n\n", "\n", " ", ""]
    )

    documents = splitter.split_documents(docs)
    print(f"Going to add {len(documents)} docs in Pinecone")

    vector_store = FAISS.from_documents(documents,embeddings)
    print("*** Loading to vectorstore done ***")

    vector_store.save_local(FAISS_INDEX_PATH)
    print(f"*** FAISS index saved to '{FAISS_INDEX_PATH}' ***")

    return vector_store.as_retriever(
        search_type="similarity", search_kwargs={"k": 4}
    )

if __name__ == '__main__':
    ingest_pdf()