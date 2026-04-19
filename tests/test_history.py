"""Tests for batchmark.history persistence module."""

import json
import os
import tempfile

import pytest

from batchmark.runner import BenchmarkResult
from batchmark.history import save_results, load_results, list_tags


def make_result(cmd="echo hi", size=100, times=None, exit_code=0):
    return BenchmarkResult(
        command=cmd,
        size=size,
        exit_code=exit_code,
        times=times or [0.1, 0.2, 0.15],
    )


def test_save_and_load_basic():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        results = [make_result(size=10), make_result(size=20)]
        save_results(results, path=path)
        loaded = load_results(path=path)
        assert len(loaded) == 2
        assert loaded[0].size == 10
        assert loaded[1].size == 20
    finally:
        os.unlink(path)


def test_save_appends():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        save_results([make_result(size=1)], path=path)
        save_results([make_result(size=2)], path=path)
        loaded = load_results(path=path)
        assert len(loaded) == 2
    finally:
        os.unlink(path)


def test_load_missing_file():
    loaded = load_results(path="/tmp/__nonexistent_batchmark__.json")
    assert loaded == []


def test_save_and_load_with_tag():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        save_results([make_result(size=1)], path=path, tag="v1")
        save_results([make_result(size=2)], path=path, tag="v2")
        v1 = load_results(path=path, tag="v1")
        v2 = load_results(path=path, tag="v2")
        assert len(v1) == 1 and v1[0].size == 1
        assert len(v2) == 1 and v2[0].size == 2
    finally:
        os.unlink(path)


def test_list_tags():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        save_results([make_result()], path=path, tag="beta")
        save_results([make_result()], path=path, tag="alpha")
        save_results([make_result()], path=path)  # no tag
        tags = list_tags(path=path)
        assert tags == ["alpha", "beta"]
    finally:
        os.unlink(path)


def test_list_tags_missing_file():
    assert list_tags(path="/tmp/__nonexistent_batchmark__.json") == []
