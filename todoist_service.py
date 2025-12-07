import os
from dotenv import load_dotenv
from todoist_api_python.api import TodoistAPI
from todoist_api_python.models import Task

load_dotenv()

api = TodoistAPI(os.getenv("TODOIST_API_TOKEN"))


def get_tasks(filter_query: str | None = None) -> list[Task]:
    """取得待辦事項列表。

    Args:
        filter_query: Todoist filter 語法，例如 "today" 或 "overdue"

    Returns:
        待辦事項列表
    """
    if filter_query:
        paginator = api.get_tasks(filter=filter_query)
    else:
        paginator = api.get_tasks()

    # SDK 回傳 ResultsPaginator，iterate 後是 list[list[Task]]
    tasks = []
    for page in paginator:
        tasks.extend(page)
    return tasks


def get_today_tasks() -> list[Task]:
    """取得今日待辦事項。"""
    return get_tasks(filter_query="today | overdue")


if __name__ == "__main__":
    tasks = get_tasks()
    print(f"共 {len(tasks)} 個待辦事項:\n")
    for task in tasks:
        print(f"- {task.content}")
