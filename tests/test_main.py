"""Tests for the TinyDataset web app with a mocked OpenAI-compatible LLM."""
import importlib
import os
import sys
from unittest import mock

import openai
import pytest
from fastapi.testclient import TestClient

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

XSS_Q = "<script>alert(1)</script>"
XSS_A = 'a" autofocus onfocus="alert(2)'


def _llm_reply(content):
    resp = mock.MagicMock()
    resp.choices[0].message.content = content
    return resp


@pytest.fixture
def app_env(tmp_path, monkeypatch):
    # main.py uses cwd-relative paths and deletes ./qa_data.db on import,
    # so run it from a scratch directory.
    for d in ("templates", "static"):
        os.symlink(os.path.join(ROOT, d), tmp_path / d)
    monkeypatch.chdir(tmp_path)
    fake = mock.MagicMock()
    fake.chat.completions.create.return_value = _llm_reply(
        'Sure: [{"question": "What is [x]?", "answer": "A letter."}]'
    )
    with mock.patch.object(openai, "OpenAI", return_value=fake):
        for name in ("main", "llm_client", "database"):
            sys.modules.pop(name, None)
        main = importlib.import_module("main")
    yield main, TestClient(main.app, raise_server_exceptions=False), fake


def test_generate_qa_returns_parsed_pairs(app_env):
    main, _, fake = app_env
    import llm_client
    assert llm_client.generate_qa("fact") == [
        {"question": "What is [x]?", "answer": "A letter."}
    ]
    fake.chat.completions.create.return_value = _llm_reply("no json here")
    assert llm_client.generate_qa("fact") == []


def test_generate_endpoint_inserts_rows(app_env):
    _, client, _ = app_env
    r = client.post("/generate/", data={"fact": "x is a letter"})
    assert r.status_code == 200
    assert "What is [x]?" in r.text


def test_qa_rows_escape_html(app_env):
    _, client, _ = app_env
    import database
    fact_id = database.insert_fact("f")
    database.insert_qa(fact_id, XSS_Q, XSS_A)
    rows = client.get("/get_qa/").text
    assert XSS_Q not in rows and "&lt;script&gt;" in rows
    edit = client.get("/edit_qa/1").text
    assert XSS_A not in edit and "&quot;" in edit


def test_update_returns_rows(app_env):
    _, client, _ = app_env
    import database
    database.insert_qa(database.insert_fact("f"), "q", "a")
    r = client.put("/update_qa/1", data={"question": "q2", "answer": "a2"})
    assert r.status_code == 200
    assert "q2" in r.text


def test_edit_missing_entry_is_404(app_env):
    _, client, _ = app_env
    assert client.get("/edit_qa/999").status_code == 404
