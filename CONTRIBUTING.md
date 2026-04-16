# Contributing to ha-light-controller

Thank you for your interest in contributing! This document provides guidelines
and information for contributors.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/ha-light-controller.git`
3. Create a feature branch from `testing`: `git checkout -b feature/your-feature-name testing`
4. Make your changes
5. Push to your fork: `git push origin feature/your-feature-name`
6. Open a Pull Request against the `testing` branch (not `main`)

## Development Setup

### Prerequisites

- Python 3.13+
- [UV](https://docs.astral.sh/uv/) package manager

### Install UV

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Set up the project

```bash
git clone https://github.com/L3DigitalNet/ha-light-controller.git
cd ha-light-controller
uv venv .venv                   # Create virtual environment
source .venv/bin/activate       # Activate it
make setup                      # Install dependencies + pre-commit hooks
```

### Run tests

```bash
make test         # Run all tests
make test-cov     # Run tests with coverage report
pytest tests/test_controller.py   # Run a specific test file
```

Tests mock the `homeassistant` module — no running Home Assistant instance is needed.

### Quality checks

```bash
make lint         # Ruff linter
make lint-fix     # Lint with auto-fix
make format       # Ruff formatter
make type-check   # mypy type checker
make quality      # All checks at once
make ci           # Full CI simulation
```

## Pull Request Guidelines

- **One concern per PR.** Keep changes focused and reviewable.
- **Write descriptive commit messages.** Explain *what* changed and *why*.
- **Update CHANGELOG.md** for all non-trivial changes.
- **Add tests** for new functionality.
- **Ensure all checks pass** before requesting review: `make ci`

## Home Assistant Constraints

This is a Home Assistant integration. All contributions must follow HA's async requirements:

- **Never use blocking I/O** — no `time.sleep()`, sync `requests`, or blocking file operations
- **All I/O must be async** — use `await`, or `hass.async_add_executor_job()` for unavoidable sync calls
- **Use HA APIs** — `hass.services.async_call`, `hass.states.get`, etc. Never bypass the state machine

## Code Style

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting, and [mypy](https://mypy.readthedocs.io/) for type checking.

- Run `make format` to auto-format code
- Run `make lint` to check for issues (or `make lint-fix` to auto-fix)
- Run `make type-check` to verify types — all new code must pass with 0 errors
- Use modern Python type hints (`list[str]`, `X | None` — not `List`, `Optional`)
- Prefer flat over nested — if nesting exceeds 3 levels, extract a helper

## Reporting Issues

- Use the [issue tracker](https://github.com/L3DigitalNet/ha-light-controller/issues) to report bugs
- Check existing issues before creating a new one
- Use the issue templates when available
- Include steps to reproduce for bug reports

## Security Issues

Please do **not** open public issues for security vulnerabilities. See [SECURITY.md](SECURITY.md) for responsible disclosure instructions.

## License

By contributing, you agree that your contributions will be licensed under the same [MIT License](LICENSE) as the project.

## Questions?

Feel free to open a [GitHub Discussion](https://github.com/L3DigitalNet/ha-light-controller/discussions) or an issue if you have questions about contributing.
