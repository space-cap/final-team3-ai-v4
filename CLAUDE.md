# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a KakaoTalk template analysis and management system focused on AI-powered template categorization and policy compliance. The project contains Korean language KakaoTalk message templates with associated metadata and policy documents.

## Repository Structure

- `data/` - Contains the main datasets and policy documents
  - `kakao_template_vectordb_data.json` - Large JSON file (~530KB) containing KakaoTalk message templates with structured metadata including categories, approval status, variables, and content analysis
  - `cleaned_policies/` - Directory containing Markdown policy documents for KakaoTalk template guidelines:
    - `audit.md` - Template review guidelines and approval criteria
    - `content-guide.md` - Template creation guidelines and formatting rules
    - `white-list.md` - Approved message types and examples
    - `black-list.md` - Prohibited message types and content
    - `operations.md` - Operational procedures and requirements
    - `image.md`, `infotalk.md`, `publictemplate.md` - Additional policy documents

## Data Format

The main data file contains template objects with:
- `id`: Unique template identifier
- `text`: Template message content (Korean language, supports variables like #{수신자명})
- `metadata`: Rich metadata including:
  - Categories (category_1, category_2)
  - Template codes and approval status
  - Content analysis (length, sentence count, politeness level)
  - Business and service type classifications
  - Variables and button information

## Development Environment

- Python project with virtual environment in `.venv/`
- **IMPORTANT**: Always activate the virtual environment before installing packages or running scripts
- No specific build, test, or dependency management files found
- Data-focused repository primarily containing datasets and documentation

## Development Commands

**Virtual Environment Setup:**
```bash
# Activate virtual environment (Windows)
.venv\Scripts\activate

# Activate virtual environment (Unix/macOS)
source .venv/bin/activate

# Install packages (always use within virtual environment)
pip install <package_name>
```

**Always ensure the virtual environment is activated before:**
- Installing any Python packages with `pip install`
- Running Python scripts
- Working with project dependencies

## Working with Templates

When analyzing or processing templates:
- Templates contain Korean text with variable placeholders using #{variable_name} syntax
- Each template has extensive metadata for categorization and compliance checking
- Policy documents provide context for template approval criteria and content guidelines
- Templates are categorized by business type, service type, and approval status

## Key Considerations

- All template content and policy documents are in Korean
- The dataset appears to be for training or analysis of message template compliance
- Templates follow specific formatting rules and variable naming conventions
- Policy compliance is a critical aspect of template management