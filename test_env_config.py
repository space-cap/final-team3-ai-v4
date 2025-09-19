#!/usr/bin/env python3
"""
.env 파일에서 LLM 설정을 로드하는지 테스트
"""

import os
from dotenv import load_dotenv

def test_env_config():
    """환경 변수 설정 테스트"""
    print(".env 파일에서 LLM 설정 로드 테스트")
    print("=" * 50)

    # .env 파일 로드
    load_dotenv()

    # LLM 환경 변수 확인
    claude_model = os.getenv("CLAUDE_MODEL", "claude-3-5-haiku-latest")
    claude_temperature = float(os.getenv("CLAUDE_TEMPERATURE", "0.3"))
    claude_max_tokens = int(os.getenv("CLAUDE_MAX_TOKENS", "2000"))

    print(f"CLAUDE_MODEL: {claude_model}")
    print(f"CLAUDE_TEMPERATURE: {claude_temperature}")
    print(f"CLAUDE_MAX_TOKENS: {claude_max_tokens}")

    # 임베딩 환경 변수 확인
    embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    embedding_dimension = int(os.getenv("EMBEDDING_DIMENSION", "1536"))
    embedding_provider = os.getenv("EMBEDDING_PROVIDER", "openai")

    print(f"EMBEDDING_MODEL: {embedding_model}")
    print(f"EMBEDDING_DIMENSION: {embedding_dimension}")
    print(f"EMBEDDING_PROVIDER: {embedding_provider}")

    # API 키 확인 (마스킹)
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        masked_key = api_key[:10] + "..." + api_key[-10:] if len(api_key) > 20 else "***"
        print(f"ANTHROPIC_API_KEY: {masked_key}")
    else:
        print("ANTHROPIC_API_KEY: 설정되지 않음")

    print("\n.env 설정이 성공적으로 로드되었습니다!")

    return {
        "llm": {
            "model": claude_model,
            "temperature": claude_temperature,
            "max_tokens": claude_max_tokens,
        },
        "embedding": {
            "model": embedding_model,
            "dimension": embedding_dimension,
            "provider": embedding_provider,
        },
        "api_keys": {
            "anthropic_set": bool(api_key),
            "openai_set": bool(os.getenv("OPENAI_API_KEY"))
        }
    }

if __name__ == "__main__":
    test_env_config()