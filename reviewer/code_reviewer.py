import json
import os
import sys
from anthropic import Anthropic
from dotenv import load_dotenv


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcpServer.github_mcp import GitHubMCP


class CodeReviewer:    
    def __init__(self, github_token: str, anthropic_api_key: str):
        self.github_mcp = GitHubMCP(github_token)
        self.claude = Anthropic(api_key=anthropic_api_key)
        self.model = "claude-sonnet-4-5-20250929"
        
        print("✅ 코드 리뷰어 초기화 완료")
    
    def review_pull_request(self, repo: str, pr_number: int, custom_prompt: str = None):
        """
        PR 리뷰 수행
        
        Args:
            repo: 저장소 이름
            pr_number: PR 번호
            custom_prompt: 커스텀 프롬프트 (None이면 기본값 사용)
        """
        print(f"\n{'='*60}")
        print(f"🔍 PR 리뷰 시작: {repo} #{pr_number}")
        print(f"{'='*60}\n")

        # 프롬프트 결정
        if custom_prompt:
            print("📝 커스텀 프롬프트 사용")
            prompt_content = custom_prompt
        else:
            print("📝 기본 프롬프트 사용")
            prompt_content = """
                You are my iOS development expert colleague.

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
        
        # Claude에게 리뷰 요청
        messages = [
            {
                "role": "user",
                "content": f"""
                    {prompt_content}

                    **Repository**: {repo}
                    **PR Number**: {pr_number}
                    """
            }
        ]
        
        # Claude 실행
        response = self._call_claude_with_tools(messages)
        
        # 콘솔 출력
        print(f"\n{'='*60}")
        print("📝 리뷰 결과:")
        print(f"{'='*60}\n")
        print(response)
        
        # GitHub에 코멘트 작성
        print(f"\n{'='*60}")
        formatted_review = f"""## 🤖 AI Code Review

                            {response}

                            ---
                            *이 리뷰는 Claude + MCP로 자동 생성되었습니다.*  
                            *최종 판단은 개발자가 해주세요!*
                            """
        
        self.github_mcp.post_review_comment(repo, pr_number, formatted_review)
        print(f"{'='*60}\n")
    
        return response
    
    def _call_claude_with_tools(self, messages: list) -> str:
        tools = self.github_mcp._register_tools()
        
        while True:
            response = self.claude.messages.create(
                model=self.model,
                max_tokens=20000,
                tools=tools,
                messages=messages,
                timeout=600.0
            )
            
            if response.stop_reason == "end_turn":
                final_text = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        final_text += block.text
                return final_text
            
            elif response.stop_reason == "tool_use":
                print("🔧 Claude가 GitHub 도구를 사용합니다...")
                
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input
                        
                        print(f"   📌 {tool_name} 호출")

                        # 도구 실행
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

                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
            
            else:
                print(f"⚠️  예상치 못한 종료: {response.stop_reason}")
                break
        
        return "리뷰 생성 실패"


if __name__ == "__main__":
    load_dotenv()
    
    # 환경변수 확인
    github_token = os.getenv("GITHUB_TOKEN")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not github_token or not anthropic_key:
        print("❌ 환경변수가 설정되지 않았습니다")
        print("   - GITHUB_TOKEN")
        print("   - ANTHROPIC_API_KEY")
        exit(1)
    
    repo = os.getenv("GITHUB_REPOSITORY")
    pr_num_str = os.getenv("PR_NUMBER")
    
    if not repo or not pr_num_str:
        print("❌ GitHub 정보가 없습니다")
        print("   - GITHUB_REPOSITORY")
        print("   - PR_NUMBER")
        exit(1)
    
    pr_num = int(pr_num_str)
    
    # 커스텀 프롬프트 로드
    custom_prompt_file = os.getenv("CUSTOM_PROMPT_FILE", ".pr-reviewer.md")
    custom_prompt = None
    
    if os.path.exists(custom_prompt_file):
        print(f"📝 커스텀 프롬프트 파일 발견: {custom_prompt_file}")
        with open(custom_prompt_file, "r", encoding="utf-8") as f:
            custom_prompt = f.read()
    
    # 리뷰 실행 (코멘트 작성은 함수 안에서 처리)
    reviewer = CodeReviewer(github_token, anthropic_key)
    reviewer.review_pull_request(repo, pr_num, custom_prompt)
