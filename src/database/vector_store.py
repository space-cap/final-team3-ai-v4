"""
Vector Database Manager for KakaoTalk Policy Documents
"""
import os
import json
from typing import List, Dict, Any
import logging
from dotenv import load_dotenv

# Optional ChromaDB import
try:
    import chromadb
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.embeddings import OpenAIEmbeddings
    from langchain.vectorstores import Chroma
    from langchain.document_loaders import TextLoader
    CHROMADB_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] ChromaDB not available: {e}")
    print("[INFO] Vector search features will be disabled")
    CHROMADB_AVAILABLE = False

# .env 파일 로드
load_dotenv()

logger = logging.getLogger(__name__)

class PolicyVectorStore:
    """Vector store for KakaoTalk policy documents using Chroma"""

    def __init__(self, persist_directory: str = None):
        if not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB not available. Vector search features disabled.")
            self.vector_store = None
            return

        # .env에서 설정 로드
        self.persist_directory = persist_directory or os.getenv("VECTOR_DB_PATH", "./chroma_db")

        # 임베딩 모델 설정
        embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        embedding_provider = os.getenv("EMBEDDING_PROVIDER", "openai")

        if embedding_provider.lower() == "openai":
            self.embeddings = OpenAIEmbeddings(
                model=embedding_model,
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )
        else:
            # 기본값으로 OpenAI 사용
            self.embeddings = OpenAIEmbeddings(model=embedding_model)

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        self.vector_store = None
        self._initialize_vector_store()

    def _initialize_vector_store(self):
        """Initialize or load existing vector store"""
        try:
            # Try to load existing vector store
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            logger.info("Loaded existing vector store")
        except Exception as e:
            logger.info(f"Creating new vector store: {e}")
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )

    def load_policy_documents(self, policy_dir: str = "data/cleaned_policies"):
        """Load and process policy documents into vector store"""
        if not CHROMADB_AVAILABLE or not self.vector_store:
            logger.warning("Vector store not available. Skipping policy document loading.")
            return

        if not os.path.exists(policy_dir):
            raise FileNotFoundError(f"Policy directory not found: {policy_dir}")

        documents = []
        for filename in os.listdir(policy_dir):
            if filename.endswith('.md'):
                file_path = os.path.join(policy_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Create document metadata
                    metadata = {
                        'source': filename,
                        'policy_type': self._get_policy_type(filename)
                    }

                    # Split text into chunks
                    chunks = self.text_splitter.split_text(content)

                    for i, chunk in enumerate(chunks):
                        doc_metadata = metadata.copy()
                        doc_metadata['chunk_id'] = i
                        documents.append({
                            'content': chunk,
                            'metadata': doc_metadata
                        })

                    logger.info(f"Loaded {len(chunks)} chunks from {filename}")

                except Exception as e:
                    logger.error(f"Error loading {filename}: {e}")

        # Add documents to vector store
        if documents:
            texts = [doc['content'] for doc in documents]
            metadatas = [doc['metadata'] for doc in documents]

            self.vector_store.add_texts(
                texts=texts,
                metadatas=metadatas
            )
            self.vector_store.persist()
            logger.info(f"Added {len(documents)} document chunks to vector store")

    def _get_policy_type(self, filename: str) -> str:
        """Determine policy type from filename"""
        policy_types = {
            'audit.md': 'review_guidelines',
            'content-guide.md': 'content_guidelines',
            'white-list.md': 'allowed_templates',
            'black-list.md': 'prohibited_templates',
            'operations.md': 'operational_procedures',
            'image.md': 'image_guidelines',
            'infotalk.md': 'infotalk_guidelines',
            'publictemplate.md': 'public_template_guidelines'
        }
        return policy_types.get(filename, 'general')

    def search_relevant_policies(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant policy documents"""
        if not CHROMADB_AVAILABLE or not self.vector_store:
            logger.warning("Vector search not available. Returning empty results.")
            return []

        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)

            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'relevance_score': score
                })

            return formatted_results

        except Exception as e:
            logger.error(f"Error searching policies: {e}")
            return []

    def get_policy_by_type(self, policy_type: str, k: int = 10) -> List[Dict[str, Any]]:
        """Get policies by specific type"""
        if not CHROMADB_AVAILABLE or not self.vector_store:
            logger.warning("Vector search not available. Returning empty results.")
            return []

        try:
            # Filter by metadata
            results = self.vector_store.similarity_search(
                query="",
                k=k,
                filter={"policy_type": policy_type}
            )

            return [
                {
                    'content': doc.page_content,
                    'metadata': doc.metadata
                }
                for doc in results
            ]

        except Exception as e:
            logger.error(f"Error getting policies by type: {e}")
            return []


class TemplateStore:
    """Store for existing approved templates"""

    def __init__(self, template_file: str = "data/kakao_template_vectordb_data.json"):
        self.template_file = template_file
        self.templates = []
        self.load_templates()

    def load_templates(self):
        """Load templates from JSON file"""
        try:
            with open(self.template_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.templates = data.get('templates', [])

            logger.info(f"Loaded {len(self.templates)} templates")

        except Exception as e:
            logger.error(f"Error loading templates: {e}")
            self.templates = []

    def get_templates_by_category(self, category_1: str = None, category_2: str = None) -> List[Dict[str, Any]]:
        """Get templates by category"""
        filtered = self.templates

        if category_1:
            filtered = [t for t in filtered if t['metadata'].get('category_1') == category_1]

        if category_2:
            filtered = [t for t in filtered if t['metadata'].get('category_2') == category_2]

        return filtered

    def get_templates_by_business_type(self, business_type: str) -> List[Dict[str, Any]]:
        """Get templates by business type"""
        return [
            t for t in self.templates
            if t['metadata'].get('business_type') == business_type
        ]

    def get_approved_templates(self) -> List[Dict[str, Any]]:
        """Get only approved templates"""
        return [
            t for t in self.templates
            if t['metadata'].get('approval_status') == 'approved'
        ]

    def find_similar_templates(self, business_type: str, service_type: str, k: int = 5) -> List[Dict[str, Any]]:
        """Find similar templates based on business and service type"""
        filtered = [
            t for t in self.templates
            if (t['metadata'].get('business_type') == business_type or
                t['metadata'].get('service_type') == service_type) and
               t['metadata'].get('approval_status') == 'approved'
        ]

        return filtered[:k]


if __name__ == "__main__":
    # Initialize and test vector store
    vector_store = PolicyVectorStore()

    # Load policy documents
    vector_store.load_policy_documents()

    # Test search
    results = vector_store.search_relevant_policies("알림톡 템플릿 승인 기준")
    print(f"Found {len(results)} relevant policies")

    # Initialize template store
    template_store = TemplateStore()
    print(f"Loaded {len(template_store.templates)} templates")