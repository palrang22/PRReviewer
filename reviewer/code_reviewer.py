import os
import sys
from anthropic import Anthropic
from dotenv import load_dotenv

# 상위 폴더에서 모듈 import 가능하게
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcpServer.github_mcp import GitHubMCP


class CodeReviewer:    
    def __init__(self, github_token: str, anthropic_api_key: str):
        self.github_mcp = GitHubMCP(github_token)
        self.claude = Anthropic(api_key=anthropic_api_key)
        self.model = "claude-sonnet-4-5-20250929"
        
        print("✅ 코드 리뷰어 초기화 완료")
    
    def review_pull_request(self, repo: str, pr_number: int):
        print(f"\n{'='*60}")
        print(f"🔍 PR 리뷰 시작: {repo} #{pr_number}")
        print(f"{'='*60}\n")
        
        # Claude에게 리뷰 요청
        messages = [
            {
                "role": "user",
                "content": f"""
                    당신은 iOS 개발 전문가입니다.
                    아래 PR을 리뷰해주세요.

                    **저장소**: {repo}
                    **PR 번호**: {pr_number}

                    **진행 방법**:
                    1. get_pull_request 도구로 PR 정보 조회
                    2. 변경된 코드 분석
                    3. 리뷰 작성

                    간단히 요약해서 알려주세요.
                    """
            }
        ]
        
        # Claude 실행
        response = self._call_claude_with_tools(messages)
        
        print(f"\n{'='*60}")
        print("📝 리뷰 결과:")
        print(f"{'='*60}\n")
        print(response)
        
        return response
    
    def _call_claude_with_tools(self, messages: list) -> str:
        # GitHub MCP 도구 등록
        tools = self.github_mcp.tools
        
        # 대화 루프 시작
        while True:
            response = self.claude.messages.create(
                model=self.model,
                max_tokens=2000,
                tools=tools,  # 도구 제공
                messages=messages
            )
            
            if response.stop_reason == "end_turn":
                # 최종 답변
                final_text = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        final_text += block.text
                return final_text
            
            elif response.stop_reason == "tool_use":
                # Claude가 도구 사용 요청
                print("🔧 Claude가 GitHub 도구를 사용합니다...")
                
                # 도구 실행
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input
                        
                        print(f"   📌 {tool_name} 호출")
                        
                        # GitHub MCP로 도구 실행
                        result = self.github_mcp.get_pull_request(
                            tool_input["repo"],
                            tool_input["pr_number"]
                        )
                        
                        # 결과를 Claude에게 다시 전달
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result)
                        })
                
                # 대화 히스토리 업데이트
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
            
            else:
                print(f"⚠️  예상치 못한 종료: {response.stop_reason}")
                break
        
        return "리뷰 생성 실패"


# 테스트 코드
if __name__ == "__main__":
    load_dotenv()
    
    github_token = os.getenv("GITHUB_TOKEN")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not github_token or not anthropic_key:
        print("❌ .env 파일에 토큰을 설정해주세요")
        exit(1)
    
    # 리뷰어 생성
    reviewer = CodeReviewer(github_token, anthropic_key)
    
    # .env에서 설정 가져오기
    repo = os.getenv("GITHUB_REPOSITORY", "Talet-project/Talet_iOS")
    pr_num = int(os.getenv("PR_NUMBER", "32"))
    
    # 리뷰 실행!
    reviewer.review_pull_request(repo, pr_num)