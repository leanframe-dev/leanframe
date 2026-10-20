# Copyright 2026 LeanFrame Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import os

import nox

DEFAULT_PYTHON_VERSION = "3.13"
UNIT_TEST_PYTHON_VERSIONS = ["3.11", "3.12", "3.13", "3.14"]
IBIS_VERSIONS = ["11", "12"]

nox.options.default_venv_backend = "uv"
nox.options.sessions = ["lint", "mypy", "unit"]

# Ensure host pyenv shared libraries or Nix Python hook variables do not
# interfere with the Nix-provided Python interpreters used by uv and nox.
for _var in ("PYTHONPATH", "_PYTHON_HOST_PLATFORM", "_PYTHON_SYSCONFIGDATA_NAME"):
    os.environ.pop(_var, None)
if "LD_LIBRARY_PATH" in os.environ:
    os.environ["LD_LIBRARY_PATH"] = os.pathsep.join(
        p
        for p in os.environ["LD_LIBRARY_PATH"].split(os.pathsep)
        if p and ".pyenv" not in p
    )


def _sync_env(session: nox.Session) -> None:
    """Sync locked dependencies into the session's virtual environment."""
    python_arg = (
        f"--python={session.python}"
        if isinstance(session.python, str)
        else f"--python={session.virtualenv.location}"
    )
    session.run_install(
        "uv",
        "sync",
        "--locked",
        "--all-extras",
        "--dev",
        python_arg,
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )


@nox.session(python=DEFAULT_PYTHON_VERSION)
def lint(session: nox.Session) -> None:
    """Run ruff linter."""
    _sync_env(session)
    session.run("ruff", "check", *session.posargs)


@nox.session(python=DEFAULT_PYTHON_VERSION)
def mypy(session: nox.Session) -> None:
    """Run mypy static type checker."""
    _sync_env(session)
    target_paths = session.posargs if session.posargs else ["leanframe", "tests"]
    session.run("mypy", *target_paths)


@nox.session(python=UNIT_TEST_PYTHON_VERSIONS)
@nox.parametrize("ibis", IBIS_VERSIONS)
def unit(session: nox.Session, ibis: str) -> None:
    """Run unit tests against multiple Python and Ibis versions."""
    _sync_env(session)
    session.install(f"ibis-framework[bigquery,duckdb]=={ibis}.*")
    test_paths = (
        session.posargs if session.posargs else [os.path.join("tests", "unit")]
    )
    session.run("pytest", *test_paths)
