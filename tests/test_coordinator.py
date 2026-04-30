from __future__ import annotations

import threading
import time

from research import coordinator


def _enabled(**overrides):
    enabled = {
        "company_profile": True,
        "seo_keywords": True,
        "competitor": True,
        "social_content": True,
        "swot": True,
    }
    enabled.update(overrides)
    return enabled


def test_company_profile_runs_before_downstream_modules(monkeypatch):
    events = []
    profile = {"company_name": "Acme", "data_limitations": ["profile caveat"]}

    def fake_profile(target_url, llm_complete):
        events.append("profile")
        return profile

    def fake_downstream(name):
        def _run(company_profile, target_url, llm_complete):
            events.append(name)
            assert company_profile is profile
            return {"data_limitations": [f"{name} caveat"]}
        return _run

    monkeypatch.setattr(coordinator, "run_company_profile", fake_profile)
    monkeypatch.setattr(coordinator, "run_seo_keywords", fake_downstream("seo_keywords"))
    monkeypatch.setattr(coordinator, "run_competitors", fake_downstream("competitor"))
    monkeypatch.setattr(coordinator, "run_social_content", fake_downstream("social_content"))
    monkeypatch.setattr(coordinator, "run_swot", lambda **kwargs: {"data_limitations": ["swot caveat"]})

    coordinator.run_all("https://acme.example", lambda *args, **kwargs: "ok", _enabled())

    assert events[0] == "profile"
    assert set(events[1:]) == {"seo_keywords", "competitor", "social_content"}


def test_downstream_modules_run_in_parallel_after_profile(monkeypatch):
    profile_finished = threading.Event()
    started = []
    lock = threading.Lock()

    def fake_profile(target_url, llm_complete):
        profile_finished.set()
        return {"company_name": "Acme"}

    def slow_downstream(name):
        def _run(company_profile, target_url, llm_complete):
            assert profile_finished.is_set()
            with lock:
                started.append((name, time.monotonic()))
            time.sleep(0.05)
            return {"data_limitations": []}
        return _run

    monkeypatch.setattr(coordinator, "run_company_profile", fake_profile)
    monkeypatch.setattr(coordinator, "run_seo_keywords", slow_downstream("seo_keywords"))
    monkeypatch.setattr(coordinator, "run_competitors", slow_downstream("competitor"))
    monkeypatch.setattr(coordinator, "run_social_content", slow_downstream("social_content"))
    monkeypatch.setattr(coordinator, "run_swot", lambda **kwargs: {"data_limitations": []})

    coordinator.run_all("https://acme.example", lambda *args, **kwargs: "ok", _enabled())

    assert {name for name, _ in started} == {"seo_keywords", "competitor", "social_content"}
    start_times = [timestamp for _, timestamp in started]
    assert max(start_times) - min(start_times) < 0.04


def test_swot_receives_all_available_module_outputs(monkeypatch):
    profile = {"company_name": "Acme"}
    seo = {"top_keywords": ["widgets"]}
    competitor = {"competitors": []}
    social = {"platforms": ["LinkedIn"]}
    swot_kwargs = {}

    monkeypatch.setattr(coordinator, "run_company_profile", lambda target_url, llm_complete: profile)
    monkeypatch.setattr(coordinator, "run_seo_keywords", lambda company_profile, target_url, llm_complete: seo)
    monkeypatch.setattr(coordinator, "run_competitors", lambda company_profile, target_url, llm_complete: competitor)
    monkeypatch.setattr(coordinator, "run_social_content", lambda company_profile, target_url, llm_complete: social)

    def fake_swot(**kwargs):
        swot_kwargs.update(kwargs)
        return {"swot": {}, "data_limitations": []}

    monkeypatch.setattr(coordinator, "run_swot", fake_swot)

    coordinator.run_all("https://acme.example", lambda *args, **kwargs: "ok", _enabled())

    assert swot_kwargs["company_profile"] is profile
    assert swot_kwargs["seo_keywords"] is seo
    assert swot_kwargs["competitor"] is competitor
    assert swot_kwargs["social_content"] is social
    assert swot_kwargs["target_url"] == "https://acme.example"


def test_downstream_failure_is_recorded_and_run_continues_to_swot(monkeypatch):
    monkeypatch.setattr(coordinator, "run_company_profile", lambda target_url, llm_complete: {"company_name": "Acme"})
    monkeypatch.setattr(coordinator, "run_seo_keywords", lambda company_profile, target_url, llm_complete: {"data_limitations": ["seo caveat"]})

    def failing_competitor(company_profile, target_url, llm_complete):
        raise RuntimeError("competitor boom")

    monkeypatch.setattr(coordinator, "run_competitors", failing_competitor)
    monkeypatch.setattr(coordinator, "run_social_content", lambda company_profile, target_url, llm_complete: {"data_limitations": []})
    monkeypatch.setattr(coordinator, "run_swot", lambda **kwargs: {"data_limitations": ["swot caveat"]})

    results = coordinator.run_all("https://acme.example", lambda *args, **kwargs: "ok", _enabled())

    assert results["competitor"] == {"error": "competitor boom"}
    assert "competitor" in results["metadata"]["modules_failed"]
    assert "competitor" not in results["metadata"]["modules_skipped"]
    assert "swot" in results["metadata"]["modules_run"]
    assert "seo caveat" in results["metadata"]["data_limitations"]
    assert "swot caveat" in results["metadata"]["data_limitations"]


def test_disabled_modules_are_marked_skipped(monkeypatch):
    monkeypatch.setattr(coordinator, "run_company_profile", lambda target_url, llm_complete: {"company_name": "Acme"})
    monkeypatch.setattr(coordinator, "run_seo_keywords", lambda company_profile, target_url, llm_complete: {"data_limitations": []})
    monkeypatch.setattr(coordinator, "run_competitors", lambda company_profile, target_url, llm_complete: {"data_limitations": []})
    monkeypatch.setattr(coordinator, "run_social_content", lambda company_profile, target_url, llm_complete: {"data_limitations": []})
    monkeypatch.setattr(coordinator, "run_swot", lambda **kwargs: {"data_limitations": []})

    results = coordinator.run_all(
        "https://acme.example",
        lambda *args, **kwargs: "ok",
        _enabled(seo_keywords=False, social_content=False, swot=False),
    )

    assert set(results["metadata"]["modules_skipped"]) == {"seo_keywords", "social_content", "swot"}
    assert "seo_keywords" not in results
    assert "social_content" not in results
    assert "swot" not in results


def test_swot_is_skipped_when_company_profile_fails(monkeypatch):
    monkeypatch.setattr(coordinator, "run_company_profile", lambda target_url, llm_complete: (_ for _ in ()).throw(RuntimeError("profile boom")))
    monkeypatch.setattr(coordinator, "run_seo_keywords", lambda company_profile, target_url, llm_complete: {"data_limitations": []})
    monkeypatch.setattr(coordinator, "run_competitors", lambda company_profile, target_url, llm_complete: {"data_limitations": []})
    monkeypatch.setattr(coordinator, "run_social_content", lambda company_profile, target_url, llm_complete: {"data_limitations": []})
    monkeypatch.setattr(coordinator, "run_swot", lambda **kwargs: (_ for _ in ()).throw(AssertionError("should not run")))

    results = coordinator.run_all("https://acme.example", lambda *args, **kwargs: "ok", _enabled())

    assert results["company_profile"] == {"error": "profile boom"}
    assert "company_profile" in results["metadata"]["modules_failed"]
    assert "swot" in results["metadata"]["modules_skipped"]
    assert "swot" not in results


def test_progress_callback_receives_sensible_messages_and_percentages(monkeypatch):
    monkeypatch.setattr(coordinator, "run_company_profile", lambda target_url, llm_complete: {"company_name": "Acme"})
    monkeypatch.setattr(coordinator, "run_seo_keywords", lambda company_profile, target_url, llm_complete: {"data_limitations": []})
    monkeypatch.setattr(coordinator, "run_competitors", lambda company_profile, target_url, llm_complete: {"data_limitations": []})
    monkeypatch.setattr(coordinator, "run_social_content", lambda company_profile, target_url, llm_complete: {"data_limitations": []})
    monkeypatch.setattr(coordinator, "run_swot", lambda **kwargs: {"data_limitations": []})
    progress = []

    coordinator.run_all(
        "https://acme.example",
        lambda *args, **kwargs: "ok",
        _enabled(),
        lambda message, pct: progress.append((message, pct)),
    )

    messages = [message for message, _ in progress]
    percentages = [pct for _, pct in progress]
    assert any("Company Profile" in message for message in messages)
    assert any("SEO Keywords" in message for message in messages)
    assert any("SWOT" in message for message in messages)
    assert percentages[0] >= 0
    assert percentages[-1] == 100.0
    assert percentages == sorted(percentages)


def test_metadata_includes_required_fields_and_provider_model_when_available(monkeypatch):
    def llm_complete(*args, **kwargs):
        return "ok"

    llm_complete.provider = "deepseek"
    llm_complete.model = "deepseek-chat"

    monkeypatch.setattr(coordinator, "run_company_profile", lambda target_url, llm_complete: {"company_name": "Acme", "data_limitations": ["profile caveat"]})
    monkeypatch.setattr(coordinator, "run_seo_keywords", lambda company_profile, target_url, llm_complete: {"data_limitations": []})
    monkeypatch.setattr(coordinator, "run_competitors", lambda company_profile, target_url, llm_complete: {"data_limitations": []})
    monkeypatch.setattr(coordinator, "run_social_content", lambda company_profile, target_url, llm_complete: {"data_limitations": []})
    monkeypatch.setattr(coordinator, "run_swot", lambda **kwargs: {"data_limitations": []})

    results = coordinator.run_all("https://acme.example", llm_complete, _enabled())
    metadata = results["metadata"]

    assert metadata["target_url"] == "https://acme.example"
    assert metadata["timestamp"]
    assert metadata["modules_failed"] == []
    assert metadata["data_limitations"] == ["profile caveat"]
    assert metadata["provider"] == "deepseek"
    assert metadata["model"] == "deepseek-chat"
