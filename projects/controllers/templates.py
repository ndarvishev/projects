# -*- coding: utf-8 -*-
"""Templates controller."""
import re
from datetime import datetime

from sqlalchemy.exc import InvalidRequestError, ProgrammingError
from werkzeug.exceptions import BadRequest, NotFound

from projects.controllers.utils import raise_if_experiment_does_not_exist, uuid_alpha
from projects.database import db_session
from projects.models import Template, Operator


def list_templates():
    """
    Lists all templates from our database.

    Returns
    -------
    list
        A list of all templates sorted by name in natural sort order.
    """
    templates = db_session.query(Template) \
        .all()
    # sort the list in place, using natural sort
    templates.sort(key=lambda o: [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", o.name)])
    return [template.as_dict() for template in templates]


def order_operators_by_dependencies(operators_ordered, operator):
    """
    Order operators by dependencies.

    Parameters
    ----------
    operators_ordered : list
    operator : dict
    """
    uuid = operator.uuid
    dependencies = operator.dependencies
    if uuid not in operators_ordered:
        if len(dependencies) == 0:
            operators_ordered.append(uuid)
        else:
            check = True
            for d in dependencies:
                if d not in operators_ordered:
                    check = False
            if check:
                operators_ordered.append(uuid)


def create_template(name=None, experiment_id=None, **kwargs):
    """
    Creates a new template in our database.

    Parameters
    ----------
    name : str
    experiment_id : str
    **kwargs
        Arbitrary keyword arguments.

    Returns
    -------
    dict
        The template attributes.

    Raises
    ------
    BadRequest
        When name is not a str instance.
        When the `**kwargs` (template attributes) are invalid.
    """
    if not isinstance(name, str):
        raise BadRequest("name is required")

    if not isinstance(experiment_id, str):
        raise BadRequest("experimentId is required")

    try:
        raise_if_experiment_does_not_exist(experiment_id)
    except NotFound as e:
        raise BadRequest(e.description)

    operators = db_session.query(Operator) \
        .filter_by(experiment_id=experiment_id) \
        .all()

    # order operators by dependencies
    operators_ordered = []
    while len(operators) != len(operators_ordered):
        for operator in operators:
            order_operators_by_dependencies(operators_ordered, operator)

    # JSON array order of elements are preserved, so there is no need to save positions
    tasks = []
    for uuid in operators_ordered:
        operator = next((op for op in operators if op.uuid == uuid), None)
        task = {
            "uuid": operator.uuid,
            "task_id": operator.task_id,
            "dependencies": operator.dependencies,
            "position_x": operator.position_x,
            "position_y": operator.position_y,
        }
        tasks.append(task)

    template = Template(uuid=uuid_alpha(), name=name, tasks=tasks)
    db_session.add(template)
    db_session.commit()
    return template.as_dict()


def get_template(template_id):
    """
    Details a template from our database.

    Parameters
    ----------
    template_id : str

    Returns
    -------
    dict
        The template attributes.

    Raises
    ------
    NotFound
        When project_id does not exist.
    """
    template = Template.query.get(template_id)

    if template is None:
        raise NotFound("The specified template does not exist")

    return template.as_dict()


def update_template(template_id, **kwargs):
    """
    Updates a template in our database.

    Parameters
    ----------
    template_id : str
    **kwargs:
        Arbitrary keyword arguments.

    Returns
    -------
    dict
        The template attributes.

    Raises
    ------
    NotFound
        When project_id does not exist.
    BadRequest
        When the `**kwargs` (template attributes) are invalid.
    """
    template = Template.query.get(template_id)

    if template is None:
        raise NotFound("The specified template does not exist")

    data = {"updated_at": datetime.utcnow()}
    data.update(kwargs)

    try:
        db_session.query(Template).filter_by(uuid=template_id).update(data)
        db_session.commit()
    except (InvalidRequestError, ProgrammingError) as e:
        raise BadRequest(str(e))

    return template.as_dict()


def delete_template(template_id):
    """
    Delete a template in our database.

    Parameters
    ----------
    template_id : str

    Returns
    -------
    dict
        The deletion result.

    Raises
    ------
    NotFound
        When project_id does not exist.
    """
    template = Template.query.get(template_id)

    if template is None:
        raise NotFound("The specified template does not exist")

    db_session.delete(template)
    db_session.commit()

    return {"message": "Template deleted"}
