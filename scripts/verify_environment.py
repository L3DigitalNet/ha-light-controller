#!/usr/bin/env python3
"""Verify that the Home Assistant development environment is properly configured.

This script checks all requirements for HA Light Controller development.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str) -> None:
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")


def print_success(text: str) -> None:
    """Print a success message."""
    print(f"{Colors.GREEN}✓{Colors.RESET} {text}")


def print_error(text: str) -> None:
    """Print an error message."""
    print(f"{Colors.RED}✗{Colors.RESET} {text}")


def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"{Colors.YELLOW}!{Colors.RESET} {text}")


def check_python_version() -> bool:
    """Check if Python version meets requirements."""
    version = sys.version_info
    required_major = 3
    required_minor = 13

    if version.major >= required_major and version.minor >= required_minor:
        print_success(
            f"Python {version.major}.{version.minor}.{version.micro} "
            f"(>= {required_major}.{required_minor} required)"
        )
        return True

    print_error(
        f"Python {version.major}.{version.minor}.{version.micro} "
        f"(>= {required_major}.{required_minor} required)"
    )
    return False


def check_package_installed(package_name: str, import_name: str | None = None) -> bool:
    """Check if a Python package is installed."""
    import_name = import_name or package_name

    if importlib.util.find_spec(import_name) is not None:
        try:
            module = importlib.import_module(import_name)
            version = getattr(module, "__version__", "unknown")
            print_success(f"{package_name} installed (version: {version})")
            return True
        except ImportError:
            print_error(f"{package_name} - import failed")
            return False

    print_error(f"{package_name} - not installed")
    return False


def check_command_available(command: str) -> bool:
    """Check if a command-line tool is available."""
    try:
        result = subprocess.run(
            [command, "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if result.returncode == 0:
            version = result.stdout.strip().split("\n")[0]
            print_success(f"{command} available ({version})")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    print_error(f"{command} - not available")
    return False


def check_directory_exists(path: Path, description: str) -> bool:
    """Check if a directory exists."""
    if path.exists() and path.is_dir():
        print_success(f"{description}: {path}")
        return True

    print_error(f"{description}: {path} - not found")
    return False


def check_file_exists(path: Path, description: str) -> bool:
    """Check if a file exists."""
    if path.exists() and path.is_file():
        print_success(f"{description}: {path}")
        return True

    print_error(f"{description}: {path} - not found")
    return False


def main() -> int:
    """Run all verification checks."""
    import os

    project_root = Path(__file__).parent.parent
    results: dict[str, bool] = {}
    is_ci = os.environ.get("CI") == "true"

    # Python Environment
    print_header("Python Environment")
    results["python_version"] = check_python_version()

    # Virtual environment check - optional in CI
    venv_path = project_root / ".venv"
    if venv_path.exists() and venv_path.is_dir():
        print_success(f"Virtual environment: {venv_path}")
    elif is_ci:
        print_warning(f"Virtual environment: {venv_path} - not found (skipped in CI)")
    else:
        print_warning(f"Virtual environment: {venv_path} - not found (optional)")

    # Core Dependencies
    print_header("Core Dependencies")
    results["homeassistant"] = check_package_installed("homeassistant")
    results["aiohttp"] = check_package_installed("aiohttp")
    results["voluptuous"] = check_package_installed("voluptuous")

    # Testing Framework
    print_header("Testing Framework")
    results["pytest"] = check_package_installed("pytest")
    results["pytest-asyncio"] = check_package_installed(
        "pytest_asyncio", "pytest_asyncio"
    )
    results["pytest-ha"] = check_package_installed(
        "pytest-homeassistant-custom-component",
        "pytest_homeassistant_custom_component",
    )
    results["pytest-cov"] = check_package_installed("pytest-cov", "pytest_cov")

    # Code Quality Tools
    print_header("Code Quality Tools")
    results["ruff"] = check_command_available("ruff")
    results["mypy"] = check_command_available("mypy")
    results["pre-commit"] = check_command_available("pre-commit")

    # Project Structure
    print_header("Project Structure")
    results["custom_components"] = check_directory_exists(
        project_root / "custom_components", "custom_components directory"
    )
    results["tests"] = check_directory_exists(project_root / "tests", "tests directory")
    results["pyproject"] = check_file_exists(
        project_root / "pyproject.toml", "pyproject.toml"
    )
    results["pre-commit-config"] = check_file_exists(
        project_root / ".pre-commit-config.yaml", ".pre-commit-config.yaml"
    )
    # VS Code settings - optional, not required for CI
    vscode_path = project_root / ".vscode" / "settings.json"
    if vscode_path.exists() and vscode_path.is_file():
        print_success(f"VS Code settings: {vscode_path}")
    else:
        print_warning(f"VS Code settings: {vscode_path} - not found (optional)")

    # HA Light Controller Integration
    print_header("HA Light Controller Integration")
    integration_dir = project_root / "custom_components" / "ha_light_controller"
    results["manifest"] = check_file_exists(
        integration_dir / "manifest.json", "manifest.json"
    )
    results["init"] = check_file_exists(integration_dir / "__init__.py", "__init__.py")
    results["const"] = check_file_exists(integration_dir / "const.py", "const.py")
    results["strings"] = check_file_exists(
        integration_dir / "strings.json", "strings.json"
    )
    results["controller"] = check_file_exists(
        integration_dir / "controller.py", "controller.py"
    )
    results["config_flow"] = check_file_exists(
        integration_dir / "config_flow.py", "config_flow.py"
    )

    # Test Structure
    print_header("Test Structure")
    results["test_conftest"] = check_file_exists(
        project_root / "tests" / "conftest.py", "conftest.py"
    )

    # Summary
    print_header("Verification Summary")
    total = len(results)
    passed = sum(results.values())
    failed = total - passed

    print(f"\nTotal checks: {total}")
    print_success(f"Passed: {passed}")
    if failed > 0:
        print_error(f"Failed: {failed}")
    else:
        print_success(f"Failed: {failed}")

    if failed == 0:
        print(f"\n{Colors.BOLD}{Colors.GREEN}✓ All checks passed!{Colors.RESET}")
        print(
            f"{Colors.GREEN}Your development environment is ready for "
            f"HA Light Controller development.{Colors.RESET}"
        )
        return 0

    print(f"\n{Colors.BOLD}{Colors.RED}✗ Some checks failed.{Colors.RESET}")
    print(
        f"{Colors.YELLOW}Please review the errors above and install "
        f"missing dependencies.{Colors.RESET}"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
