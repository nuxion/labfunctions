from dataclasses import asdict

from nb_workflows.types import NBTask, ProjectData, ScheduleData, WorkflowData

nb_task_simple = NBTask(
    nb_name="test_workflow",
    params={"TIMEOUT": 1},
)

schedule_data = ScheduleData(start_in_min=0, repeat=None, interval="5")

nb_task_schedule = NBTask(
    nb_name="test_workflow",
    params={"TIMEOUT": 1},
    jobid="test_id",
    schedule=schedule_data,
)


wd = WorkflowData(
    jobid="test_id",
    nb_name="test_workflows",
    job_detail=nb_task_schedule.dict(),
    enabled=True,
)

pd = ProjectData(name="test", projectid="asd", username="test")
