from src.schemas.task_loader import load_tasks


def test_load_schema_ablation_tasks():

    tasks = load_tasks(
        "tasks/schema_ablation_tasks.json"
    )

    assert len(tasks) == 5


def test_task_expected_arguments():

    tasks = load_tasks(
        "tasks/schema_ablation_tasks.json"
    )

    assert tasks[0]["expected_arguments"] == {
        "query": "AUTH_FAILURES"
    }

    assert tasks[1]["id"] == "T2"
    assert tasks[1]["expected_arguments"] == {
        "query": "AUTH_FAILURES",
        "status": "open"
    }

    assert tasks[2]["id"] == "T3"
    assert tasks[2]["expected_arguments"] == {
        "query": "AUTH_FAILURES",
        "max_results": 20
    }

    assert tasks[3]["id"] == "T4"
    assert tasks[3]["expected_arguments"] == {
        "query": "AUTH_FAILURES",
        "include_comments": True
    }

    assert tasks[4]["id"] == "T5"
    assert tasks[4]["expected_arguments"] == {
        "query": "AUTH_FAILURES",
        "status": "closed",
        "max_results": 20,
        "include_comments": True
    }