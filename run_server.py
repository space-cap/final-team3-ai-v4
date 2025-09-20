"""
카카오 알림톡 템플릿 자동 생성 서비스 실행 스크립트
"""
import os
import sys
import uvicorn
from pathlib import Path

# 프로젝트 루트를 Python 패스에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def load_environment():
    """환경 변수 로드"""
    try:
        from dotenv import load_dotenv
        env_file = project_root / ".env"

        if env_file.exists():
            load_dotenv(env_file)
            print(f"[OK] 환경 변수 로드: {env_file}")
        else:
            print("[WARNING] .env 파일이 없습니다. .env.example을 참고하여 생성해주세요.")
    except ImportError:
        print("[WARNING] python-dotenv가 설치되지 않았습니다.")
        print("   pip install python-dotenv로 설치해주세요.")

def check_api_key():
    """API 키 확인"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[ERROR] ANTHROPIC_API_KEY가 설정되지 않았습니다.")
        print("   .env 파일에 ANTHROPIC_API_KEY=your_actual_key_here 를 추가해주세요.")
        return False

    if api_key == "your_claude_api_key_here":
        print("[ERROR] ANTHROPIC_API_KEY가 예시 값으로 설정되어 있습니다.")
        print("   실제 Claude API 키로 변경해주세요.")
        return False

    print("[OK] ANTHROPIC_API_KEY가 설정되어 있습니다.")
    return True

def create_directories():
    """필요한 디렉토리 생성"""
    directories = [
        "logs",
        "chroma_db"
    ]

    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(exist_ok=True)
        print(f"[FOLDER] 디렉토리 생성/확인: {directory}")

def main():
    """메인 실행 함수"""
    print("카카오 알림톡 템플릿 자동 생성 서비스 시작")
    print("=" * 60)

    # 환경 설정
    load_environment()

    # API 키 확인
    if not check_api_key():
        print("\n[ERROR] 서버를 시작할 수 없습니다. API 키를 설정해주세요.")
        return

    # 디렉토리 생성
    create_directories()

    # 서버 설정
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    reload = os.getenv("ENVIRONMENT", "production") == "development"
    log_level = os.getenv("LOG_LEVEL", "info").lower()

    print(f"\n[CONFIG] 서버 설정:")
    print(f"   - 호스트: {host}")
    print(f"   - 포트: {port}")
    print(f"   - 개발 모드: {reload}")
    print(f"   - 로그 레벨: {log_level}")

    print(f"\n[INFO] API 문서: http://localhost:{port}/docs")
    print(f"[INFO] 헬스체크: http://localhost:{port}/health")
    print(f"[INFO] 시스템 통계: http://localhost:{port}/stats")

    print("\n" + "=" * 60)
    print("서버를 시작합니다...")
    print("Ctrl+C로 서버를 중지할 수 있습니다.")
    print("=" * 60)

    try:
        # FastAPI 서버 실행
        uvicorn.run(
            "src.api.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n\n[STOP] 서버가 중지되었습니다.")
    except Exception as e:
        print(f"\n[ERROR] 서버 실행 오류: {e}")

if __name__ == "__main__":
    main()