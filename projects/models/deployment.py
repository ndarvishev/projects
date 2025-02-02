# -*- coding: utf-8 -*-
"""Deployment model."""
from datetime import datetime
from warnings import warn

from sqlalchemy import Boolean, Column, DateTime, event, \
    Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import expression

from projects.controllers.deployments.runs import RunController
from projects.database import Base
from projects.exceptions import NotFound
from projects.models.monitoring import Monitoring
from projects.models.operator import Operator

CASCADE = "all, delete-orphan"


class Deployment(Base):
    __tablename__ = "deployments"
    uuid = Column(String(255), primary_key=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    experiment_id = Column(String(255), ForeignKey("experiments.uuid"), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=expression.true())
    name = Column(Text, nullable=False)
    operators = relationship("Operator",
                             primaryjoin=uuid == Operator.deployment_id,
                             lazy="joined",
                             cascade=CASCADE)
    monitorings = relationship("Monitoring",
                               primaryjoin=uuid == Monitoring.deployment_id,
                               cascade=CASCADE)
    position = Column(Integer, nullable=False, default=-1)
    status = Column(String(255), nullable=False, default="Pending")
    url = Column(String(255), nullable=True)
    deployed_at = Column(DateTime, nullable=True)
    project_id = Column(String(255), ForeignKey("projects.uuid"), nullable=False, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


@event.listens_for(Deployment, "after_delete")
def undeploy(_mapper, connection, target):
    try:
        RunController(connection).terminate_run(deployment_id=target.uuid)
    except NotFound as e:
        warn(e.message)
