from github import Github
import os


class GitHubMCP:    
    def __init__(self, access_token: str):
        self.github = Github(access_token)
        print("✅ GitHub MCP 서버 초기화 완료")
    
    def test_connection(self):
        try:
            user = self.github.get_user()
            print(f"👤 연결된 사용자: {user.login}")
            return True
        except Exception as e:
            print(f"❌ 연결 실패: {e}")
            return False
        
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
