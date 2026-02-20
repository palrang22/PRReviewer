# 🤖 PR Reviewer

> AI-powered Pull Request code review using Claude + MCP

Claude와 GitHub MCP를 활용한 자동 PR 코드 리뷰 GitHub Action입니다.

## ✨ 주요 기능

- 🔍 **컨텍스트 인지형 리뷰**: 단순 diff 분석을 넘어 전체 코드베이스 고려
- 🛠️ **MCP 기반**: Claude가 능동적으로 관련 파일 탐색
- 🎯 **실용적 피드백**: 문제점 + 이유 + 개선 제안
- 📝 **커스텀 프롬프트**: 프로젝트별 리뷰 규칙 설정 가능

## 🚀 빠른 시작

### 1. GitHub Secrets 설정

저장소 Settings → Secrets and variables → Actions:
```
Name: ANTHROPIC_API_KEY
Value: sk-ant-your-api-key
```

[Anthropic API Key 발급받기](https://console.anthropic.com/)

### 2. 워크플로우 파일 추가

`.github/workflows/pr-review.yml`:
```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: palrang22/PRReviewer@v1
        with:
          anthropic-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

### 3. 완료!

이제 PR을 생성하면 자동으로 AI 리뷰가 달립니다! 🎉

## 🎨 커스텀 프롬프트 (선택사항)

프로젝트 루트에 `.pr-reviewer.md` 파일 생성:
```markdown
# .pr-reviewer.md

You are an iOS development expert.

**Review Focus:**
- Clean Architecture (3-layer)
- MVVM-C pattern
- RxSwift memory leaks

**Response in Korean.**
```

## 📊 예시

### 리뷰 결과

[PR Review Example](https://github.com/Talet-project/Talet_iOS/pull/32#issuecomment-3920286667)

```markdown
## 🤖 AI Code Review

#### 변경된 내용
Info.plist에 iOS 18 호환성 설정 추가

#### ✅ 긍정적인 점
1. 적절한 임시 조치
2. 최소한의 변경

#### 💡 제안 사항
1. Issue 추적 권장
2. 후속 작업 계획

#### ✨ 결론
LGTM 👍
```

## ⚙️ 고급 설정

### 커스텀 프롬프트 파일 경로 지정
```yaml
- uses: palrang22/PRReviewer@v1
  with:
    anthropic-key: ${{ secrets.ANTHROPIC_API_KEY }}
    custom-prompt-file: 'docs/review-guide.md'
```

## 💰 비용

- PR당 약 $0.05-0.20 (Claude API 사용료)
- 월 50개 PR 기준: $2.5-10

## 🛠️ 개발

### 로컬 테스트
```bash
git clone https://github.com/palrang22/PRReviewer.git
cd PRReviewer

# .env 파일 생성
cat > .env << EOF
GITHUB_TOKEN=ghp_your_token
ANTHROPIC_API_KEY=sk-ant-your_key
GITHUB_REPOSITORY=owner/repo
PR_NUMBER=1
EOF

# 실행
python reviewer/code_reviewer.py
```

## 📝 라이선스

MIT License

## 👤 Author

**팔랑이**
- GitHub: [@palrang22](https://github.com/palrang22)

## 🤝 기여

이슈와 PR 환영합니다!

---

**Made with ❤️ by palrang22**
