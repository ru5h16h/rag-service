from __future__ import annotations

import nox


nox.options.default_venv_backend = "uv|virtualenv"
nox.options.sessions = ["lint", "tests"]


def install_project(session: nox.Session) -> None:
    session.run("uv", "sync", "--extra", "all", external=True)


@nox.session(python="3.11")
def lint(session: nox.Session) -> None:
    install_project(session)
    session.run("uv", "run", "black", "--check", "src", "tests", external=True)
    session.run("uv", "run", "isort", "--check-only", "src", "tests", external=True)
    session.run("uv", "run", "ruff", "check", "src", "tests", external=True)
    session.run("uv", "run", "mypy", "src", external=True)


@nox.session(python="3.11")
def tests(session: nox.Session) -> None:
    install_project(session)
    session.run("uv", "run", "pytest", "tests/", "-m", "not integration", "-v", external=True)


@nox.session(python="3.11")
def tests_integration(session: nox.Session) -> None:
    install_project(session)
    session.run("uv", "run", "pytest", "tests/", "-m", "integration", "-v", external=True)


@nox.session(python="3.11")
def tests_all(session: nox.Session) -> None:
    install_project(session)
    session.run("uv", "run", "pytest", "tests/", "-v", external=True)


@nox.session
def format(session: nox.Session) -> None:
    """Run formatters to fix issues automatically."""
    session.run("uv", "run", "black", "src", "tests", external=True)
    session.run("uv", "run", "isort", "src", "tests", external=True)
