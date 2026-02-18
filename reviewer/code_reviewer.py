import json
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
                        You are my iOS development expert colleague.

                        **Repository**: {repo}
                        **PR Number**: {pr_number}

                        **Review Process**:
                        1. Check changes with get_pull_request
                        2. Analyze modified files
                        3. **Only when necessary**, investigate related files:
                        e.g., files with similar patterns
                        4. Consider overall project structure
                        5. Provide suggestions if any, otherwise mention good points
                        6. Follow the important notes below

                        **Important Notes**:
                        - For config files (plist, xcconfig, etc.): brief check only
                        - No unnecessary searches

                        **Available Tools**:
                        - get_pull_request: Retrieve PR information
                        - get_file_content: View complete file contents
                        - search_code: Search codebase

                        **Call tools multiple times if needed for thorough investigation!**

                        **Respond in Korean for the final review.**
                        """
                    }
                ]
        
        # Claude 실행
        response = self._call_claude_with_tools(messages)
        
        print(f"\n{'='*60}")
        print("📝 리뷰 결과:")
        print(f"{'='*60}\n")
        print(response)
        

        print(f"\n{'='*60}")

        formatted_review = f"""## 🤖 AI Code Review

                            {response}

                            ---
                            *이 리뷰는 Claude + MCP로 자동 생성되었습니다.* 
                            """
        
        self.github_mcp.post_review_comment(repo, pr_number, formatted_review)
        print(f"{'='*60}\n")
    
        return response
    
    def _call_claude_with_tools(self, messages: list) -> str:
        # GitHub MCP 도구 등록
        tools = self.github_mcp._register_tools()
        
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

                        # 결과를 Claude에게 다시 전달
                        if tool_name == "get_pull_request":
                            result = self.github_mcp.get_pull_request(
                                tool_input["repo"],
                                tool_input["pr_number"]
                            )
                        elif tool_name == "get_file_content":
                            result = self.github_mcp.get_file_content(
                                tool_input["repo"],
                                tool_input["path"],
                                tool_input.get("ref", "main")
                            )
                        elif tool_name == "search_code":
                            result = self.github_mcp.search_code(
                                tool_input["repo"],
                                tool_input["query"]
                            )
                        else:
                            result = {"error": f"Unknown tool: {tool_name}"}

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result, ensure_ascii=False)
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