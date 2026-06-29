"""CLI dispatch [v1.1.6] — bake routes to the right source's run() without touching the
network. Sample path still bakes. Unknown/missing source errors out."""

from __future__ import annotations

from pathlib import Path

import pytest

from btb_pipeline import cli


def test_registry_covers_live_sources():
    assert set(cli.SOURCES) == {
        "fec", "committee_link", "members", "acs", "polls", "pollster_ratings",
        "rollcall", "voteview",
    }


def test_bake_one_dispatches_to_that_source(monkeypatch):
    called = []
    monkeypatch.setitem(cli.SOURCES, "members", lambda: called.append("members") or Path("x"))
    assert cli.main(["bake", "members"]) == 0
    assert called == ["members"]


def test_bake_all_runs_every_source(monkeypatch):
    called = []
    for name in list(cli.SOURCES):
        monkeypatch.setitem(cli.SOURCES, name, lambda n=name: called.append(n) or Path("x"))
    assert cli.main(["bake", "all"]) == 0
    assert set(called) == set(cli.SOURCES)


def test_sample_default_bakes(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "bake", lambda *a, **k: tmp_path / "sample.json")
    assert cli.main([]) == 0
    assert "baked" in capsys.readouterr().out


def test_unknown_source_errors():
    with pytest.raises(SystemExit):
        cli.main(["bake", "nope"])


def test_bake_without_source_errors():
    with pytest.raises(SystemExit):
        cli.main(["bake"])
