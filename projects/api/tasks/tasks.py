# -*- coding: utf-8 -*-
"""Tasks API Router."""
from typing import Optional

from fastapi import APIRouter, Depends

import projects.schemas.task
from projects.controllers import TaskController
from projects.database import Session, session_scope

router = APIRouter(
    prefix="/tasks",
)


@router.get("", response_model=projects.schemas.task.TaskList)
async def handle_list_tasks(page: Optional[int] = None,
                            page_size: Optional[int] = None,
                            order: Optional[str] = None,
                            session: Session = Depends(session_scope)):
    """
    Handles GET requests to /.

    Parameters
    ----------
    page : int
    page_size : int
    order : str
    session : sqlalchemy.orm.session.Session

    Returns
    -------
    projects.schemas.task.TaskList
    """
    task_controller = TaskController(session)
    tasks = task_controller.list_tasks(page=page,
                                       page_size=page_size,
                                       order_by=order)
    return tasks


@router.post("", response_model=projects.schemas.task.Task)
async def handle_post_tasks(task: projects.schemas.task.TaskCreate,
                            session: Session = Depends(session_scope)):
    """
    Handles POST requests to /.

    Parameters
    ----------
    task : projects.schemas.task.TaskCreate
    session : sqlalchemy.orm.session.Session

    Returns
    -------
    projects.schemas.task.Task
    """
    task_controller = TaskController(session)
    task = task_controller.create_task(task=task)
    return task


@router.get("/{task_id}", response_model=projects.schemas.task.Task)
async def handle_get_task(task_id: str,
                          session: Session = Depends(session_scope)):
    """
    Handles GET requests to /<task_id>.

    Parameters
    ----------
    task_id : str
    session : sqlalchemy.orm.session.Session

    Returns
    -------
    projects.schemas.task.Task
    """
    task_controller = TaskController(session)
    task = task_controller.get_task(task_id=task_id)
    return task


@router.patch("/{task_id}", response_model=projects.schemas.task.Task)
async def handle_patch_task(task_id: str,
                            task: projects.schemas.task.TaskUpdate,
                            session: Session = Depends(session_scope)):
    """
    Handles PATCH requests to /<task_id>.

    Parameters
    ----------
    task_id : str
    task : projects.schemas.task.TaskUpdate
    session : sqlalchemy.orm.session.Session

    Returns
    -------
    projects.schemas.task.Task
    """
    task_controller = TaskController(session)
    task = task_controller.update_task(task_id=task_id, task=task)
    return task


@router.delete("/{task_id}")
async def handle_delete_task(task_id: str,
                             session: Session = Depends(session_scope)):
    """
    Handles DELETE requests to /<task_id>.

    Parameters
    ----------
    task_id : str
    session : sqlalchemy.orm.session.Session

    Returns
    -------
    projects.schemas.message.Message
    """
    task_controller = TaskController(session)
    result = task_controller.delete_task(task_id=task_id)
    return result
