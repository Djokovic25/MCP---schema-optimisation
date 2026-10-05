from src.schemas.task_loader import load_tasks


def test_load_pilot_tasks():

    tasks = load_tasks("tasks/pilot_tasks.json")

    assert len(tasks) == 3

    assert tasks[0]["id"] == "T1"
    assert tasks[1]["id"] == "T2"
    assert tasks[2]["id"] == "T3"


def test_task_expected_arguments():

    tasks = load_tasks("tasks/pilot_tasks.json")

    t1 = tasks[0]
    t2 = tasks[1]
    t3 = tasks[2]

    assert t1["expected_arguments"] == {
        "query": "authentication failures",
        "mode": "m7"
    }

    assert t2["expected_arguments"]["limit"] == 20

    assert t3["expected_arguments"]["include_meta"] is True