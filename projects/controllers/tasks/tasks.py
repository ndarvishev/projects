# -*- coding: utf-8 -*-
"""Tasks controller."""
import json
import os
import pkgutil
import re
import tempfile
from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy import asc, desc

from projects import models, schemas
from projects.controllers.utils import uuid_alpha
from projects.exceptions import BadRequest, NotFound
from projects.kubernetes.notebook import copy_file_to_pod, copy_files_in_pod, \
    create_persistent_volume_claim, remove_persistent_volume_claim, \
    update_persistent_volume_claim, set_notebook_metadata

PREFIX = "tasks"
VALID_TAGS = ["DATASETS", "DEFAULT", "DESCRIPTIVE_STATISTICS", "FEATURE_ENGINEERING",
              "PREDICTOR", "COMPUTER_VISION", "NLP"]
DEPLOYMENT_NOTEBOOK = json.loads(pkgutil.get_data("projects", "config/Deployment.ipynb"))
EXPERIMENT_NOTEBOOK = json.loads(pkgutil.get_data("projects", "config/Experiment.ipynb"))

NOT_FOUND = NotFound("The specified task does not exist")


class TaskController:
    def __init__(self, session):
        self.session = session

    def raise_if_task_does_not_exist(self, task_id: str):
        """
        Raises an exception if the specified task does not exist.

        Parameters
        ----------
        task_id : str

        Raises
        ------
        NotFound
        """
        exists = self.session.query(models.Task.uuid) \
            .filter_by(uuid=task_id) \
            .scalar() is not None

        if not exists:
            raise NOT_FOUND

    def list_tasks(self, page: Optional[int] = None, page_size: Optional[int] = None, order_by: str = Optional[str]):
        """
        Lists tasks. Supports pagination, and sorting.

        Parameters
        ----------
        page : int
            The page number. First page is 1.
        page_size : int
            The page size.
        order_by : str
            Order by instruction. Format is "column [asc|desc]".

        Returns
        -------
        projects.schemas.task.TaskList

        Raises
        ------
        BadRequest
            When order_by is invalid.
        """
        query = self.session.query(models.Task)
        query_total = self.session.query(func.count(models.Task.uuid))

        # FIXME Apply filters to the query
        # for column, value in filters.items():
        #     query = query.filter(getattr(models.Task, column).ilike(f"%{value}%"))
        #     query_total = query_total.filter(getattr(models.Task, column).ilike(f"%{value}%"))

        total = query_total.scalar()

        # Default sort is name in ascending order
        if not order_by:
            order_by = "name asc"

        # Sorts records
        try:
            (column, sort) = order_by.split()
            assert sort.lower() in ["asc", "desc"]
            assert column in models.Task.__table__.columns.keys()
        except (AssertionError, ValueError):
            raise BadRequest("Invalid order argument")

        if sort.lower() == "asc":
            query = query.order_by(asc(getattr(models.Task, column)))
        elif sort.lower() == "desc":
            query = query.order_by(desc(getattr(models.Task, column)))

        if page and page_size:
            # Applies pagination
            query = query.limit(page_size).offset((int(page) - 1) * int(page_size))

        tasks = query.all()

        return schemas.TaskList.from_model(tasks, total)

    def create_task(self, task: schemas.TaskCreate):
        """
        Creates a new task in our database and a volume claim in the cluster.

        Parameters
        ----------
        task: projects.schemas.task.TaskCreate

        Returns
        -------
        projects.schemas.task.Task

        Raises
        ------
        BadRequest
            When task attributes are invalid.
        """
        if not isinstance(task.name, str):
            raise BadRequest("name is required")

        has_notebook = task.experiment_notebook or task.deployment_notebook

        if task.copy_from and has_notebook:
            raise BadRequest("Either provide notebooks or a task to copy from")

        if len(task.tags) == 0:
            task.tags = ["DEFAULT"]

        if any(tag not in VALID_TAGS for tag in task.tags):
            valid_str = ",".join(VALID_TAGS)
            raise BadRequest(f"Invalid tag. Choose any of {valid_str}")

        # check if image is a valid docker image
        self.raise_if_invalid_docker_image(task.image)

        check_comp_name = self.session.query(models.Task).filter_by(name=task.name).first()
        if check_comp_name:
            raise BadRequest("a task with that name already exists")

        # creates a task with specified name,
        # but copies notebooks from a source task
        if task.copy_from:
            return self.copy_task(task)

        task_id = str(uuid_alpha())

        # loads a sample notebook if none was sent
        if task.experiment_notebook is None:
            task.experiment_notebook = EXPERIMENT_NOTEBOOK

        if task.deployment_notebook is None:
            task.deployment_notebook = DEPLOYMENT_NOTEBOOK

        # mounts a volume for the task in the notebook server
        create_persistent_volume_claim(name=f"vol-task-{task_id}",
                                       mount_path=f"/home/jovyan/tasks/{task.name}")

        # relative path to the mount_path
        experiment_notebook_path = "Experiment.ipynb"
        deployment_notebook_path = "Deployment.ipynb"

        # copies experiment notebook file to pod
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            json.dump(task.experiment_notebook, f)

        filepath = f.name
        destination_path = f"{task.name}/{experiment_notebook_path}"
        copy_file_to_pod(filepath, destination_path)
        os.remove(filepath)

        # The new task must have its own task_id, experiment_id and operator_id.
        # Notice these values are ignored when a notebook is run in a pipeline.
        # They are only used by JupyterLab interface.
        experiment_id = uuid_alpha()
        operator_id = uuid_alpha()
        set_notebook_metadata(
            notebook_path=destination_path,
            task_id=task_id,
            experiment_id=experiment_id,
            operator_id=operator_id,
        )

        # copies deployment notebook file to pod
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            json.dump(task.deployment_notebook, f)

        filepath = f.name
        destination_path = f"{task.name}/{deployment_notebook_path}"
        copy_file_to_pod(filepath, destination_path)
        os.remove(filepath)
        set_notebook_metadata(
            notebook_path=destination_path,
            task_id=task_id,
            experiment_id=experiment_id,
            operator_id=operator_id,
        )

        # saves task info to the database
        task = models.Task(
            uuid=task_id,
            name=task.name,
            description=task.description,
            tags=task.tags,
            image=task.image,
            commands=task.commands,
            arguments=task.arguments,
            parameters=task.parameters,
            experiment_notebook_path=experiment_notebook_path,
            deployment_notebook_path=deployment_notebook_path,
            is_default=task.is_default,
        )
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)

        return schemas.Task.from_model(task)

    def get_task(self, task_id):
        """
        Details a task from our database.

        Parameters
        ----------
        task_id : str

        Returns
        -------
        projects.schemas.task.Task

        Raises
        ------
        NotFound
            When task_id does not exist.
        """
        task = self.session.query(models.Task).get(task_id)

        if task is None:
            raise NOT_FOUND

        return schemas.Task.from_model(task)

    def update_task(self, task: schemas.TaskUpdate, task_id: str):
        """
        Updates a task in our database/object storage.

        Parameters
        ----------
        task: projects.schemas.task.TaskUpdate
        task_id : str

        Returns
        -------
        task: projects.schemas.task.Task

        Raises
        ------
        NotFound
            When task_id does not exist.
        BadRequest
            When task attributes are invalid.
        """
        self.raise_if_task_does_not_exist(task_id)

        stored_task = self.session.query(models.Task) \
            .filter_by(name=task.name) \
            .first()
        if stored_task and stored_task.uuid != task_id:
            raise BadRequest("a task with that name already exists")

        if task.tags and any(tag not in VALID_TAGS for tag in task.tags):
            valid_str = ",".join(VALID_TAGS)
            raise BadRequest(f"Invalid tag. Choose any of {valid_str}")

        if task.experiment_notebook:
            with tempfile.NamedTemporaryFile("w", delete=False) as f:
                json.dump(task.experiment_notebook, f)

            filepath = f.name
            destination_path = f"{task.name}/{task.experiment_notebook_path}"
            copy_file_to_pod(filepath, destination_path)
            os.remove(filepath)

        if task.deployment_notebook:
            with tempfile.NamedTemporaryFile("w", delete=False) as f:
                json.dump(task.deployment_notebook, f)

            filepath = f.name
            destination_path = f"{task.name}/{task.deployment_notebook_path}"
            copy_file_to_pod(filepath, destination_path)
            os.remove(filepath)

        # checks whether task.name has changed
        stored_task = self.session.query(models.Task.uuid) \
            .filter_by(uuid=task_id)
        if stored_task.name != task.name:
            # update the volume for the task in the notebook server
            update_persistent_volume_claim(
                name=f"vol-task-{task_id}",
                mount_path=f"/home/jovyan/tasks/{task.name}",
            )

        update_data = task.dict(exclude_unset=True)
        del task["experiment_notebook"]
        del task["deployment_notebook"]
        update_data.update({"updated_at": datetime.utcnow()})

        self.session.query(models.Task).filter_by(uuid=task_id).update(update_data)
        self.session.commit()

        task = self.session.query(models.Task).get(task_id)

        return schemas.Task.from_model(task)

    def delete_task(self, task_id: str):
        """
        Delete a task in our database.

        Parameters
        ----------
        task_id : str

        Returns
        -------
        projects.schemas.message.Message

        Raises
        ------
        NotFound
            When task_id does not exist.
        """
        task = self.session.query(models.Task).get(task_id)

        if task is None:
            raise NOT_FOUND

        # remove the volume for the task in the notebook server
        remove_persistent_volume_claim(
            name=f"vol-task-{task_id}",
            mount_path=f"/home/jovyan/tasks/{task.name}",
        )

        self.session.delete(task)

        return schemas.Message(message="Task deleted")

    def copy_task(self, task: schemas.TaskCreate):
        """
        Makes a copy of a task in our database.

        Parameters
        ----------
        task: projects.schemas.task.TaskCreate

        Returns
        -------
        projects.schemas.task.Task

        Raises
        ------
        BadRequest
            When copy_from does not exist.
        """
        stored_task = self.session.query(models.Task).get(task.copy_from)

        if stored_task is None:
            raise BadRequest("source task does not exist")

        task_id = uuid_alpha()
        image = stored_task.image
        commands = stored_task.commands
        arguments = stored_task.arguments
        parameters = stored_task.parameters
        experiment_notebook_path = stored_task.experiment_notebook_path
        deployment_notebook_path = stored_task.deployment_notebook_path

        # mounts a volume for the task in the notebook server
        create_persistent_volume_claim(name=f"vol-task-{task_id}",
                                       mount_path=f"/home/jovyan/tasks/{task.name}")

        # Copies files in the notebook server
        source_path = f"/home/jovyan/tasks/{stored_task.name}/*"
        destination_path = f"/home/jovyan/tasks/{task.name}/"
        copy_files_in_pod(source_path, destination_path)

        experiment_id = uuid_alpha()
        operator_id = uuid_alpha()

        if experiment_notebook_path:
            # Even though we are creating copies, the new task must have
            # its own task_id, experiment_id and operator_id.
            # We don't want to mix models and metrics of different tasks.
            # Notice these values are ignored when a notebook is run in a pipeline.
            # They are only used by JupyterLab interface.
            notebook_path = f"{destination_path}/{experiment_notebook_path}"
            set_notebook_metadata(
                notebook_path=notebook_path,
                task_id=task_id,
                experiment_id=experiment_id,
                operator_id=operator_id,
            )

        if deployment_notebook_path:
            notebook_path = f"{destination_path}/{deployment_notebook_path}"
            set_notebook_metadata(
                notebook_path=notebook_path,
                task_id=task_id,
                experiment_id=experiment_id,
                operator_id=operator_id,
            )

        # saves task info to the database
        task = models.Task(
            uuid=task_id,
            name=task.name,
            description=task.description,
            tags=task.tags,
            image=image,
            commands=commands,
            arguments=arguments,
            parameters=parameters,
            deployment_notebook_path=deployment_notebook_path,
            experiment_notebook_path=experiment_notebook_path,
            is_default=False,
        )
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)

        return schemas.Task.from_model(task)

    def raise_if_invalid_docker_image(self, image):
        """
        Raise an error if a str does not meet the standards for a docker image name.

        Example: (username/organization)/name-of-the-image:tag

        Parameters
        ----------
        image : str or None
            The image name.

        Raises
        ------
        BadRequest
            When a given image is a invalid one.
        """
        pattern = re.compile("[a-z0-9.-]+([/]{1}[a-z0-9.-]+)+([:]{1}[a-z0-9.-]+){0,1}$")

        if image and pattern.match(image) is None:
            raise BadRequest("invalid docker image name")
