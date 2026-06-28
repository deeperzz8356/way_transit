from langchain_core.documents import Document
# pyrefly: ignore [missing-import]
from langchain_community.vectorstores import Chroma
# We will use a mock embedding function for testing without API calls if needed, or use HuggingFace embeddings
from langchain_core.embeddings.fake import FakeEmbeddings

def get_tourist_retriever():
    """Initializes a simple Chroma vector store with some dummy tourist data."""
    embeddings = FakeEmbeddings(size=1536)
    
    docs = [
        Document(page_content="The Gateway of India is a famous arch monument built during the 20th century in Mumbai.", metadata={"source": "tourism_guide"}),
        Document(page_content="Marine Drive is a 3.6-kilometre-long Promenade along the Netaji Subhash Chandra Bose Road in Mumbai.", metadata={"source": "tourism_guide"}),
        Document(page_content="Chhatrapati Shivaji Maharaj Terminus is a historic railway station and a UNESCO World Heritage Site.", metadata={"source": "tourism_guide"})
    ]
    
    vectorstore = Chroma.from_documents(documents=docs, embedding=embeddings)
    return vectorstore.as_retriever()

def retrieve_tourist_info(query: str) -> str:
    retriever = get_tourist_retriever()
    docs = retriever.invoke(query)
    return "\n".join([doc.page_content for doc in docs])
