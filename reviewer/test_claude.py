import os
from anthropic import Anthropic
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# Claude API 클라이언트 생성
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# 간단한 메시지 전송
print("🤖 Claude에게 메시지 전송 중...")

response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=100,
    messages=[
        {
            "role": "user",
            "content": "안녕! 간단히 자기소개해줘"
        }
    ]
)

# 응답 출력
print("\n✅ Claude 응답:")
print(response.content[0].text)