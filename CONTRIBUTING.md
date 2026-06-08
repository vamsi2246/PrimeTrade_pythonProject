# Contributing to PrimeTrade Trading Bot

Thank you for your interest in contributing to PrimeTrade! To maintain a production-grade and clean codebase, please review the guidelines below before submitting pull requests.

---

## 💻 Development Workflow

### 1. Set Up Local Environment
Ensure you have Python 3.12 or 3.13 installed. Clone the repository and configure dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Code Style and Conventions
We enforce clean code principles and Python best practices:
- **Type Hints**: All function arguments and return types must be fully annotated.
- **Naming Conventions**: Use `snake_case` for functions, variables, and modules, and `PascalCase` for classes.
- **SOLID Design**: Keep functions under 40 lines. Separate concerns (e.g. keep API code in `client.py` and validation in `validators.py`).
- **Imports**: Organize imports logically (standard library first, then third-party libraries, then local package modules).

### 3. Testing Rules
Every new feature, validation check, or response format requires accompanying tests:
- Create unit tests under the `tests/` directory naming files `test_*.py`.
- Run the full test suite locally before pushing:
  ```bash
  pytest tests/ -v
  ```
- All tests must pass, and code coverage must remain high.

---

## 🔀 Pull Request Process

1. **Create a Feature Branch**: Always create branch names starting with `feature/`, `bugfix/`, or `refactor/` (e.g., `feature/trailing-stop`).
2. **Commit Messages**: Use clear, imperative git commit messages (e.g. `Implement Trailing Stop order validation`). Avoid vague names like `fix` or `update code`.
3. **Open a PR**: Describe your changes in detail, link any related issues, and attach manual validation or log summaries showing that the execution succeeds against the Futures Testnet.

Thank you for contributing to PrimeTrade!
