from __future__ import annotations

import os
import tempfile

import pytest

from tach.extension import get_project_imports


# Utility function to create temporary files with content
def create_temp_file(directory, filename, content):
    filepath = os.path.join(directory, filename)
    with open(filepath, "w") as f:
        f.write(content)
    return filepath


@pytest.fixture
def temp_project():
    with tempfile.TemporaryDirectory() as project_root:
        # Creating some sample Python files in a nested structure
        os.makedirs(os.path.join(project_root, "a", "b"), exist_ok=True)
        os.makedirs(os.path.join(project_root, "d"), exist_ok=True)
        os.makedirs(os.path.join(project_root, "local", "g"), exist_ok=True)
        os.makedirs(os.path.join(project_root, "parent"), exist_ok=True)

        file1_content = """
import os
from local.file2 import b
"""
        file2_content = """
from ..file1 import y
"""
        file3_content = """
if TYPE_CHECKING:
    from local.file2 import c
"""
        file4_content = """
# tach-ignore
from a.b import c
# tach-ignore d.e.f
from d.e import f

import file3
"""

        create_temp_file(project_root, "file1.py", file1_content)
        create_temp_file(project_root, "local/file2.py", file2_content)
        create_temp_file(project_root, "file3.py", file3_content)
        create_temp_file(project_root, "file4.py", file4_content)

        yield project_root


def test_regular_imports(temp_project):
    result = get_project_imports(
        temp_project, "file1.py", ignore_type_checking_imports=True
    )
    expected = [("local.file2.b", 3)]
    assert result == expected


def test_relative_imports(temp_project):
    result = get_project_imports(
        temp_project, "local/file2.py", ignore_type_checking_imports=True
    )
    expected = [("file1.y", 2)]
    assert result == expected


def test_ignore_type_checking_imports(temp_project):
    result = get_project_imports(
        temp_project, "file3.py", ignore_type_checking_imports=True
    )
    expected = []
    assert result == expected


def test_include_type_checking_imports(temp_project):
    result = get_project_imports(
        temp_project, "file3.py", ignore_type_checking_imports=False
    )
    expected = [("local.file2.c", 3)]
    assert result == expected


def test_mixed_imports(temp_project):
    mixed_content = """
import sys
if TYPE_CHECKING:
    from .file2 import c
from ..file1 import x
"""
    create_temp_file(temp_project, "local/file4.py", mixed_content)
    result = get_project_imports(
        temp_project, "local/file4.py", ignore_type_checking_imports=True
    )
    expected = [("file1.x", 5)]
    assert result == expected

    result = get_project_imports(
        temp_project, "local/file4.py", ignore_type_checking_imports=False
    )
    expected = [("local.file2.c", 4), ("file1.x", 5)]
    assert result == expected


def test_external_imports(temp_project):
    external_content = """
import os
from external_module import something
"""
    create_temp_file(temp_project, "file5.py", external_content)
    result = get_project_imports(
        temp_project, "file5.py", ignore_type_checking_imports=True
    )
    expected = []  # 'os' and 'external_module' are not within the project root
    assert result == expected


def test_external_and_internal_imports(temp_project):
    mixed_content = """
import os
from file1 import c
from external_module import something
"""
    create_temp_file(temp_project, "file6.py", mixed_content)
    result = get_project_imports(
        temp_project, "file6.py", ignore_type_checking_imports=True
    )
    expected = [
        ("file1.c", 3),
    ]
    assert result == expected


def test_ignored_imports(temp_project):
    result = get_project_imports(
        temp_project, "file4.py", ignore_type_checking_imports=True
    )
    expected = [("file3", 7)]
    assert result == expected
