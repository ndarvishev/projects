# -*- coding: utf-8 -*-
import time
from json import dumps
from unittest import TestCase

from fastapi.testclient import TestClient

from projects.api.main import app
from projects.controllers.utils import uuid_alpha
from projects.database import engine
from projects.kfp import kfp_client

TEST_CLIENT = TestClient(app)

PROJECT_ID = str(uuid_alpha())
NAME = "foo"
CREATED_AT = "2000-01-01 00:00:00"
UPDATED_AT = "2000-01-01 00:00:00"
DESCRIPTION = "Description"
OPERATOR_ID = str(uuid_alpha())
OPERATOR_ID_2 = str(uuid_alpha())
POSITION_X = 0.3
POSITION_Y = 0.5
STATUS = "Pending"
URL = None
PARAMETERS = {"coef": 0.1}
PARAMETERS_JSON = dumps(PARAMETERS)
TASK_ID = str(uuid_alpha())
EXPERIMENT_ID = str(uuid_alpha())
DEPLOYMENT_ID = str(uuid_alpha())
DEPENDENCIES_OP_ID = []
DEPENDENCIES_OP_ID_JSON = dumps(DEPENDENCIES_OP_ID)
IMAGE = "busybox"
TAGS = ["PREDICTOR"]
CATEGORY = "DEFAULT"
DATA_IN = ""
DATA_OUT = ""
DOCS = ""
TAGS_JSON = dumps(TAGS)
EXPERIMENT_NOTEBOOK_PATH = ""
DEPLOYMENT_NOTEBOOK_PATH = ""
EXPERIMENT_NAME = "Experimento 1"


class TestLogs(TestCase):

    def setUp(self):
        self.maxDiff = None

        conn = engine.connect()
        text = (
            f"INSERT INTO projects (uuid, name, description, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s)"
        )
        conn.execute(text, (PROJECT_ID, NAME, DESCRIPTION, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO experiments (uuid, name, project_id, position, is_active, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s)"
        )
        conn.execute(text, (EXPERIMENT_ID, EXPERIMENT_NAME, PROJECT_ID, 0, 1, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO deployments (uuid, name, project_id, experiment_id, position, is_active, status, url, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        conn.execute(text, (DEPLOYMENT_ID, NAME, PROJECT_ID, EXPERIMENT_ID, 0, 1, STATUS, URL, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO tasks (uuid, name, description, image, commands, arguments, category, tags, data_in, data_out, docs, parameters, "
            f"experiment_notebook_path, deployment_notebook_path, cpu_limit, cpu_request, memory_limit, memory_request, "
            f"readiness_probe_initial_delay_seconds, is_default, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        conn.execute(text, (TASK_ID, NAME, DESCRIPTION, IMAGE, None, None, CATEGORY, TAGS_JSON, DATA_IN, DATA_OUT, DOCS, dumps([]),
                            EXPERIMENT_NOTEBOOK_PATH, EXPERIMENT_NOTEBOOK_PATH, "100m", "100m", "1Gi", "1Gi", 300, 0, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO operators (uuid, name, status, status_message, experiment_id, task_id, parameters, position_x, position_y, dependencies, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        conn.execute(text, (OPERATOR_ID, None, "Unset", None, EXPERIMENT_ID, TASK_ID, PARAMETERS_JSON, POSITION_X,
                            POSITION_Y, DEPENDENCIES_OP_ID_JSON, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO operators (uuid, name, status, status_message, deployment_id, task_id, parameters, position_x, position_y, dependencies, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        conn.execute(text, (OPERATOR_ID_2, None, "Unset", None, DEPLOYMENT_ID, TASK_ID, PARAMETERS_JSON,
                            POSITION_X, POSITION_Y, DEPENDENCIES_OP_ID_JSON, CREATED_AT, UPDATED_AT,))
        conn.close()

        # Creates pipelines for log generation
        with open("tests/resources/mocked_experiment.yaml", "r") as file:
            content = file.read()
        content = content.replace("$experimentId", EXPERIMENT_ID)
        content = content.replace("$taskName", NAME)
        content = content.replace("$operatorId", OPERATOR_ID)
        content = content.replace("$image", IMAGE)
        with open("tests/resources/mocked.yaml", "w") as file:
            file.write(content)
        kfp_experiment = kfp_client().create_experiment(name=EXPERIMENT_ID)
        run = kfp_client().run_pipeline(
            experiment_id=kfp_experiment.id,
            job_name=f"experiment-{EXPERIMENT_ID}",
            pipeline_package_path="tests/resources/mocked.yaml",
        )
        # Awaits 120 seconds (for the pipeline to run and complete)
        kfp_client().wait_for_run_completion(run_id=run.id, timeout=120)

        with open("tests/resources/mocked_deployment.yaml", "r") as file:
            content = file.read()
        content = content.replace("$deploymentId", DEPLOYMENT_ID)
        content = content.replace("$taskName", NAME)
        content = content.replace("$operatorId", OPERATOR_ID_2)
        with open("tests/resources/mocked.yaml", "w") as file:
            file.write(content)
        kfp_experiment = kfp_client().create_experiment(name=DEPLOYMENT_ID)
        run = kfp_client().run_pipeline(
            experiment_id=kfp_experiment.id,
            job_name=f"deployment-{DEPLOYMENT_ID}",
            pipeline_package_path="tests/resources/mocked.yaml",
        )
        # Awaits 120 seconds (for the pipeline to run and complete)
        kfp_client().wait_for_run_completion(run_id=run.id, timeout=120)

    def tearDown(self):
        kfp_experiment = kfp_client().get_experiment(experiment_name=EXPERIMENT_ID)
        kfp_client().experiments.delete_experiment(id=kfp_experiment.id)

        kfp_experiment = kfp_client().get_experiment(experiment_name=DEPLOYMENT_ID)
        kfp_client().experiments.delete_experiment(id=kfp_experiment.id)

        conn = engine.connect()
        text = f"DELETE FROM operators WHERE uuid IN ('{OPERATOR_ID}', '{OPERATOR_ID_2}')"
        conn.execute(text)

        text = f"DELETE FROM deployments WHERE uuid = '{DEPLOYMENT_ID}'"
        conn.execute(text)

        text = f"DELETE FROM experiments WHERE uuid = '{EXPERIMENT_ID}'"
        conn.execute(text)

        text = f"DELETE FROM tasks WHERE uuid = '{TASK_ID}'"
        conn.execute(text)

        text = f"DELETE FROM projects WHERE uuid = '{PROJECT_ID}'"
        conn.execute(text)
        conn.close()

    def test_list_logs(self):
        rv = TEST_CLIENT.get(f"/projects/{PROJECT_ID}/experiments/{EXPERIMENT_ID}/runs/latest/logs")
        result = rv.json()
        result_logs = result.get("logs")
        expected = {
            "level": "INFO",
            "title": NAME,
            "message": "hello\nhello",
        }
        # title and created_at are machine-generated
        # we assert they exist, but we don't assert their values
        machine_generated = ["createdAt"]
        for attr in machine_generated:
            self.assertIn(attr, result_logs[0])
            del result_logs[0][attr]
        self.assertDictEqual(expected, result_logs[0])
        self.assertEqual(rv.status_code, 200)

        rv = TEST_CLIENT.get(f"/projects/{PROJECT_ID}/deployments/{DEPLOYMENT_ID}/runs/latest/logs")
        self.assertEqual(rv.status_code, 200)
