# Contributing to Torii ⛩️

Thank you for your interest in contributing! Every contribution — bug fixes, docs, examples, or new features — helps make the MCP ecosystem better for everyone.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Ways to Contribute](#ways-to-contribute)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Running Tests](#running-tests)
- [Code Style](#code-style)
- [Making Changes](#making-changes)
- [Submitting a Pull Request](#submitting-a-pull-request)

---

## Code of Conduct

Be kind, be respectful, be constructive. We're all here to build something great together.

---

## Ways to Contribute

- 🐛 **Bug reports** — Found something broken? Open an issue
- 💡 **Feature requests** — Have an idea? We'd love to hear it
- 📝 **Documentation** — Improve guides, fix typos, add examples
- 🔧 **Code** — Fix bugs, implement features, improve performance
- 🧪 **Tests** — Add coverage for existing or new functionality
- 🌍 **Examples** — Share real-world `torii.config.yaml` examples

---

## Development Setup

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Clone & Install

```bash
git clone https://github.com/sarabala1979/Torii.git
cd Torii

# Using uv (recommended)
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Or using pip
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

### Verify Setup

```bash
torii --help
torii validate --config examples/torii.config.yaml
```

---

## Project Structure

```
Torii/
├── torii/                  # Main package
│   ├── api/                # REST API → MCP tool converter
│   │   └── converter.py
│   ├── mcp/                # MCP aggregator & gateway
│   │   ├── aggregator.py   # Upstream MCP server connections
│   │   └── gateway.py      # Core Torii MCP server
│   ├── workflow/           # Workflow engine
│   │   └── engine.py
│   ├── config/             # Config parsing & Pydantic models
│   │   └── models.py
│   └── cli.py              # Typer CLI
├── tests/
│   ├── unit/               # Fast isolated unit tests
│   └── integration/        # Tests against real services
├── examples/               # Example torii.config.yaml files
├── docs/                   # Documentation
└── pyproject.toml          # Project metadata & dependencies
```

---

## Running Tests

```bash
# All tests with coverage
pytest

# Unit tests only (fast, no network)
pytest tests/unit/ -v

# Single file
pytest tests/unit/test_config.py -v

# With HTML coverage report
pytest --cov=torii --cov-report=html
open htmlcov/index.html
```

---

## Code Style

Torii uses [Ruff](https://github.com/astral-sh/ruff) for linting/formatting and [mypy](https://mypy-lang.org/) for type checking.

```bash
# Format
ruff format .

# Lint
ruff check .

# Auto-fix
ruff check --fix .

# Type check
mypy torii/
```

Install pre-commit hooks to run these automatically:

```bash
pip install pre-commit
pre-commit install
```

---

## Making Changes

1. **Fork** the repo and create a branch from `main`
2. **Name your branch** descriptively: `feat/openapi-import`, `fix/auth-header`
3. **Write tests** for any new behavior
4. **Run the full test suite** before submitting
5. **Update docs** if your change affects behavior or config

### Commit Message Format

```
<type>(<scope>): <short description>

Types: feat | fix | docs | test | refactor | chore

Examples:
  feat(api): add OpenAPI spec auto-import
  fix(mcp): handle reconnection on server timeout
  docs(config): add OAuth2 example
```

---

## Submitting a Pull Request

1. Open a PR against `main`
2. Fill out the PR template
3. Link related issues with `Closes #123`

**Checklist:**
- [ ] `pytest` passes
- [ ] `ruff check .` passes
- [ ] `mypy torii/` passes
- [ ] Docs updated if needed
- [ ] `CHANGELOG.md` updated for significant changes

---

Thank you for contributing to Torii! ⛩️
