# CI/CD Setup

## How it works

When you push code to GitHub (main/develop branch):
1. GitHub Actions automatically runs tests: `pytest tests/ -v`
2. Checks code quality: `pylint src/`
3. Checks code style: `flake8 src/`
4. Shows result in Actions tab: ✅ pass or ❌ fail

## Local testing (before push)

```bash
# Run tests
pytest tests/ -v

# Check code quality
pylint src/ --fail-under=7.0

# Check style
flake8 src/
```
