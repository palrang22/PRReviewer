from github import Github
import os


class GitHubMCP:    
    def __init__(self, access_token: str):
        from github import Auth
        auth = Auth.Token(access_token)
        self.github = Github(auth=auth)
        self.tools = self
        print("✅ GitHub MCP 서버 초기화 완료")
    
    def test_connection(self):
        try:
            user = self.github.get_user()
            print(f"👤 연결된 사용자: {user.login}")
            return True
        except Exception as e:
            print(f"❌ 연결 실패: {e}")
            return False
        
    def _register_tools(self):
        # Claude가 사용할 수 있는 도구 목록
        return [
            {
            "name": "get_pull_request",
            "description": "PR 정보와 변경된 파일 diff 조회",
            "input_schema": {
                "type": "object",
                "properties": {
                    "repo": {"type": "string"},
                    "pr_number": {"type": "integer"}
                },
                "required": ["repo", "pr_number"]
            }
            },
            {
                "name": "get_file_content",
                "description": "특정 파일의 전체 내용 조회 (관련 코드 확인용)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "repo": {"type": "string"},
                        "path": {"type": "string", "description": "파일 경로"},
                        "ref": {"type": "string", "description": "브랜치명 (기본: main)"}
                    },
                    "required": ["repo", "path"]
                }
            },
            {
                "name": "search_code",
                "description": "코드베이스 전체에서 패턴 검색 (예: DisposeBag 누락 찾기)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "repo": {"type": "string"},
                        "query": {"type": "string", "description": "검색어"}
                    },
                    "required": ["repo", "query"]
                }
            }
        ]
        
    def get_pull_request(self, repo_name: str, pr_number: int):
        try:
            print(f"🔍 PR 조회 중: {repo_name} #{pr_number}")
            
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            # PR 파일 변경 내역 가져오기
            files = pr.get_files()
            file_changes = []
            
            for file in files:
                file_changes.append({
                    "filename": file.filename,
                    "status": file.status,  # added, modified, deleted
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "patch": file.patch  # diff 내용
                })
            
            result = {
                "number": pr.number,
                "title": pr.title,
                "author": pr.user.login,
                "files": file_changes
            }
            
            print(f"✅ PR 정보 조회 완료: {len(file_changes)}개 파일 변경")
            return result
            
        except Exception as e:
            print(f"❌ PR 조회 실패: {e}")
            return None
        
    def get_file_content(self, repo_name: str, path: str, ref: str = "main"):
        # 파일 전체 내용 조회
        try:
            print(f"📄 파일 조회 중: {path}")
            
            repo = self.github.get_repo(repo_name)
            content = repo.get_contents(path, ref=ref)
            
            result = {
                "path": content.path,
                "content": content.decoded_content.decode('utf-8'),
                "size": content.size
            }
            
            print(f"✅ 파일 조회 완료: {content.size} bytes")
            return result
            
        except Exception as e:
            print(f"❌ 파일 조회 실패: {e}")
            return {"error": str(e)}
    
    def search_code(self, repo_name: str, query: str):
        # 코드 베이스 검색
        try:
            print(f"🔍 코드 검색 중: '{query}'")
            
            # GitHub 검색 쿼리
            search_query = f"{query} repo:{repo_name}"
            results = self.github.search_code(search_query)
            
            matches = []
            for i, result in enumerate(results):
                if i >= 10:  # 최대 10개만
                    break
                matches.append({
                    "path": result.path,
                    "url": result.html_url
                })
            
            print(f"✅ 검색 완료: {len(matches)}개 발견")
            return {
                "query": query,
                "total_count": results.totalCount,
                "matches": matches
            }
            
        except Exception as e:
            print(f"❌ 검색 실패: {e}")
            return {"error": str(e)}
        
    def post_review_comment(self, repo_name: str, pr_number: int, body: str):
        try:
            print(f"💬 GitHub에 코멘트 작성 중...")
            
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            # 코멘트 작성!
            comment = pr.create_issue_comment(body)
            
            print(f"✅ 코멘트 작성 완료!")
            print(f"   링크: {comment.html_url}")
            return comment
            
        except Exception as e:
            print(f"❌ 코멘트 작성 실패: {e}")
            return None


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    token = os.getenv("GITHUB_TOKEN")
    
    if token and token != "여기에_나중에_토큰_붙여넣기":
        mcp = GitHubMCP(token)
        mcp.test_connection()
        
        # PR 조회 테스트
        print("\n" + "="*50)
        repo = os.getenv("GITHUB_REPOSITORY", "palrang/Talet")
        pr_num = int(os.getenv("PR_NUMBER", "1"))
        
        result = mcp.get_pull_request(repo, pr_num)
        
        if result:
            print(f"\n📋 PR 제목: {result['title']}")
            print(f"👤 작성자: {result['author']}")
            print(f"📁 변경 파일 수: {len(result['files'])}")
    else:
        print("⚠️  .env 파일에 GITHUB_TOKEN을 설정해주세요")
