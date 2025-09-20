# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **KakaoTalk Template Generation Service** - an AI-powered system for creating and validating KakaoTalk notification message templates. The system uses Claude AI to generate policy-compliant templates with advanced hybrid search capabilities for policy retrieval and compliance checking.

## Architecture Overview

This is a **production-ready FastAPI service** with:
- **AI-powered template generation** using Claude models
- **Vector database integration** with ChromaDB for policy document storage
- **Hybrid search engine** combining Dense Vector Search + BM25 sparse retrieval
- **Korean NLP processing** with specialized tokenization
- **Compliance checking** with policy validation
- **RESTful API** with comprehensive endpoints

## Repository Structure

### Core Application (`src/`)
- **`src/api/`** - FastAPI application and routes
  - `main.py` - FastAPI app entry point and configuration
  - `routes/templates.py` - Template generation and validation endpoints
  - `models/schemas.py` - Pydantic models for API requests/responses
- **`src/agents/`** - AI agent modules
  - `template_generator.py` - Template generation logic
  - `compliance_checker.py` - Policy compliance validation
  - `request_analyzer.py` - User request analysis
  - `policy_rag.py` - Policy retrieval and RAG system
- **`src/database/`** - Database and storage
  - `vector_store.py` - ChromaDB vector store management
- **`src/search/`** - Advanced search capabilities
  - `hybrid_search.py` - Hybrid search engine (Vector + BM25)
  - `bm25_policy_search.py` - BM25 sparse retrieval implementation
  - `korean_tokenizer.py` - Korean language tokenization
- **`src/utils/`** - Utility modules
  - `llm_client.py` - Claude LLM client wrapper
- **`src/workflow/`** - Workflow orchestration
  - `langgraph_workflow.py` - LangGraph workflow implementation

### Data and Policies (`data/`)
- `kakao_template_vectordb_data.json` - Template database (~530KB)
- `cleaned_policies/` - Policy documents:
  - `audit.md` - Review guidelines and approval criteria
  - `content-guide.md` - Template creation guidelines
  - `white-list.md` - Approved message types
  - `black-list.md` - Prohibited content types
  - `operations.md` - Operational procedures
  - `image.md`, `infotalk.md`, `publictemplate.md` - Additional policies

### Documentation (`docs/`)
- `api_request_examples.md` - API usage examples and request body samples
- Analysis documents and performance reports

### Configuration and Deployment
- `run_server.py` - **Main server launcher** (use this to start the service)
- `.env` - Environment configuration (API keys, database settings)
- `requirements.txt` - Python dependencies

## Development Environment

- **Python 3.9+** with virtual environment in `.venv/`
- **FastAPI** web framework with Uvicorn ASGI server
- **ChromaDB** vector database for policy storage
- **LangChain** for AI orchestration and embeddings
- **Anthropic Claude** as the primary LLM

## Development Commands

**Server Operations:**
```bash
# Start the development server
python run_server.py

# The server will be available at:
# - API docs: http://localhost:8000/docs
# - Health check: http://localhost:8000/health
# - System stats: http://localhost:8000/stats
```

**Virtual Environment Setup:**
```bash
# Activate virtual environment (Windows)
.venv\Scripts\activate

# Activate virtual environment (Unix/macOS)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Environment Configuration:**
Ensure `.env` file contains:
```bash
ANTHROPIC_API_KEY=your_claude_api_key_here
OPENAI_API_KEY=your_openai_api_key_here  # For embeddings
VECTOR_DB_PATH=./chroma_db
HYBRID_SEARCH_ENABLED=true
```

**Testing Commands:**
```bash
# Test the hybrid search system
python test_hybrid_search.py

# Run API client tests
python test_api_client.py

# Test template generation
python test_template_generation.py
```

## API Usage

### Main Endpoints
- **`POST /api/v1/templates/generate`** - Generate new templates
- **`POST /api/v1/templates/validate`** - Validate existing templates
- **`GET /api/v1/templates/examples/{business_type}`** - Get template examples
- **`GET /api/v1/templates/categories`** - List available categories

### Example API Request
```json
{
  "user_request": "온라인 강의 수강 신청이 완료된 후 강의 일정과 접속 방법을 안내하는 메시지",
  "business_type": "교육",
  "service_type": "신청",
  "target_audience": "수강생",
  "tone": "정중한",
  "required_variables": ["수신자명", "강의명", "강의일정"],
  "additional_requirements": "버튼 포함 필요"
}
```

## Technical Features

### Hybrid Search System
- **Dense Vector Search**: OpenAI embeddings with ChromaDB
- **BM25 Sparse Retrieval**: Korean-optimized term matching
- **Score Fusion**: Weighted combination (Vector: 0.7, BM25: 0.3)
- **Korean Tokenization**: KoNLPy integration with fallback patterns

### AI Workflow
1. **Request Analysis** - Parse user requirements
2. **Policy Retrieval** - Hybrid search for relevant policies
3. **Template Generation** - Claude-powered content creation
4. **Compliance Checking** - Multi-layer policy validation
5. **Iterative Refinement** - Auto-improvement based on violations

### Data Processing
- **Template Variables**: `#{변수명}` syntax for dynamic content
- **Metadata Enrichment**: Automatic categorization and tagging
- **Korean Language Support**: Full Unicode and morphological analysis
- **Policy Compliance**: Real-time validation against KakaoTalk guidelines

## Working with Templates

### Template Structure
Templates contain Korean text with:
- **Variables**: `#{수신자명}`, `#{업체명}`, etc.
- **Business Categories**: 교육, 의료, 음식점, 쇼핑몰, 서비스업, 금융
- **Service Types**: 신청, 예약, 주문, 배송, 안내, 확인, 피드백
- **Compliance Metadata**: Approval status, violation flags, scores

### Policy Compliance
- **Information-only messages** (no advertising content)
- **1,000 character limit** for message length
- **Proper variable usage** with `#{변수명}` format
- **Business type appropriateness** validation
- **Tone and manner consistency** checking

## Key Technical Considerations

- **Korean Language Processing**: All content uses Korean with specialized NLP
- **Vector Database**: ChromaDB stores policy embeddings for fast retrieval
- **Hybrid Search**: Combines semantic and keyword-based search
- **Claude Integration**: Uses Anthropic's Claude for high-quality generation
- **Production Ready**: Includes logging, monitoring, and error handling
- **Scalable Architecture**: Modular design with clear separation of concerns

## Important Notes

- **Always activate virtual environment** before development
- **Ensure API keys are configured** in `.env` file
- **Use `run_server.py`** to start the service, not individual modules
- **Policy documents are in Korean** and critical for compliance
- **Template generation requires** both Claude and OpenAI API access
- **ChromaDB directory** (`chroma_db/`) contains the vector database

## Troubleshooting

- **Server won't start**: Check API keys in `.env` file
- **ChromaDB warnings**: Ensure all dependencies are installed via `pip install -r requirements.txt`
- **Unicode errors**: Use UTF-8 encoding for all Korean text files
- **Import errors**: Activate virtual environment before running scripts