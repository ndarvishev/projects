# -*- coding: utf-8 -*-
from json import dumps
from unittest import TestCase

from fastapi.testclient import TestClient

from projects.api.main import app
from projects.controllers.utils import uuid_alpha
from projects.database import engine

TEST_CLIENT = TestClient(app)

OPERATOR_ID = str(uuid_alpha())
OPERATOR_ID_2 = str(uuid_alpha())
NAME = "foo"
NAME_2 = "bar"
COPY_NAME = "foobar"
DEPLOYMENT_MOCK_NAME = "Foo Deployment"
DESCRIPTION = "long foo"
PROJECT_ID = str(uuid_alpha())
EXPERIMENT_ID = str(uuid_alpha())
EXPERIMENT_ID_2 = str(uuid_alpha())
DEPLOYMENT_ID = str(uuid_alpha())
DEPLOYMENT_ID_2 = str(uuid_alpha())
TEMPLATE_ID = str(uuid_alpha())
TASK_ID = str(uuid_alpha())
TASK_ID_2 = str(uuid_alpha())
RUN_ID = str(uuid_alpha())
PARAMETERS = {"coef": 0.1, "dataset": "dataset_name.csv"}
POSITION = 0
POSITION_2 = 1
POSITION_X = 0.3
POSITION_Y = 0.5
STATUS = "Pending"
URL = None
IMAGE = "platiagro/platiagro-experiment-image:0.2.0"
COMMANDS = ["CMD"]
COMMANDS_JSON = dumps(COMMANDS)
ARGUMENTS = ["ARG"]
ARGUMENTS_JSON = dumps(ARGUMENTS)
TAGS = ["PREDICTOR"]
CATEGORY = "DEFAULT"
DATA_IN = ""
DATA_OUT = ""
DOCS = ""
TAGS_JSON = dumps(TAGS)
TASKS_JSON = dumps([
    {
        "uuid": OPERATOR_ID,
        "position_x": 0.0,
        "position_y": 0.0,
        "task_id": TASK_ID,
        "dependencies": []
    },
])
PARAMETERS_JSON = dumps(PARAMETERS)
EXPERIMENT_NOTEBOOK_PATH = "Experiment.ipynb"
DEPLOYMENT_NOTEBOOK_PATH = "Deployment.ipynb"
CREATED_AT = "2000-01-01 00:00:00"
CREATED_AT_ISO = "2000-01-01T00:00:00"
UPDATED_AT = "2000-01-01 00:00:00"
UPDATED_AT_ISO = "2000-01-01T00:00:00"

DEPENDENCIES_EMPTY = []
DEPENDENCIES_EMPTY_JSON = dumps(DEPENDENCIES_EMPTY)
DEPENDENCIES_OP_ID = [OPERATOR_ID]
DEPENDENCIES_OP_ID_JSON = dumps(DEPENDENCIES_OP_ID)

TASK_DATASET_ID = str(uuid_alpha())
TASK_DATASET_TAGS = ["DATASETS"]
TASK_DATASET_TAGS_JSON = dumps(TASK_DATASET_TAGS)


class TestDeployments(TestCase):
    def setUp(self):
        self.maxDiff = None

        conn = engine.connect()
        text = (
            f"INSERT INTO projects (uuid, name, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s)"
        )
        conn.execute(text, (PROJECT_ID, NAME, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO experiments (uuid, name, project_id, position, is_active, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s)"
        )
        conn.execute(text, (EXPERIMENT_ID, NAME, PROJECT_ID, POSITION, 1, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO experiments (uuid, name, project_id, position, is_active, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s)"
        )
        conn.execute(text, (EXPERIMENT_ID_2, NAME_2, PROJECT_ID, POSITION_2, 1, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO deployments (uuid, name, project_id, experiment_id, position, is_active, status, url, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        conn.execute(text, (DEPLOYMENT_ID, NAME, PROJECT_ID, EXPERIMENT_ID, POSITION, 1, STATUS, URL, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO deployments (uuid, name, project_id, experiment_id, position, is_active, status, url, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        conn.execute(text, (DEPLOYMENT_ID_2, NAME_2, PROJECT_ID, EXPERIMENT_ID, POSITION, 1, STATUS, URL, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO tasks (uuid, name, description, image, commands, arguments, category, "
            f"tags, data_in, data_out, docs, parameters, experiment_notebook_path, "
            f"deployment_notebook_path, cpu_limit, cpu_request, memory_limit, memory_request, "
            f"readiness_probe_initial_delay_seconds, is_default, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        conn.execute(text, (TASK_ID, NAME, DESCRIPTION, IMAGE, COMMANDS_JSON, ARGUMENTS_JSON, CATEGORY, TAGS_JSON, DATA_IN, DATA_OUT, DOCS,
                            dumps([]), EXPERIMENT_NOTEBOOK_PATH, DEPLOYMENT_NOTEBOOK_PATH, "100m", "100m", "1Gi", "1Gi", 300, 0, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO tasks (uuid, name, description, image, commands, arguments, category, "
            f"tags, data_in, data_out, docs, parameters, experiment_notebook_path, "
            f"deployment_notebook_path, cpu_limit, cpu_request, memory_limit, memory_request, "
            f"readiness_probe_initial_delay_seconds, is_default, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        conn.execute(text, (TASK_ID_2, NAME, DESCRIPTION, IMAGE, COMMANDS_JSON, ARGUMENTS_JSON, CATEGORY, TAGS_JSON, DATA_IN, DATA_OUT, DOCS, dumps([]),
                            EXPERIMENT_NOTEBOOK_PATH, DEPLOYMENT_NOTEBOOK_PATH, "100m", "100m", "1Gi", "1Gi", 300, 0, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO tasks (uuid, name, description, image, commands, arguments, category, "
            f"tags, data_in, data_out, docs, parameters, experiment_notebook_path, "
            f"deployment_notebook_path, cpu_limit, cpu_request, memory_limit, memory_request, "
            f"readiness_probe_initial_delay_seconds, is_default, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )

        conn.execute(text, (TASK_DATASET_ID, NAME, DESCRIPTION, IMAGE, COMMANDS_JSON, ARGUMENTS_JSON, CATEGORY, TASK_DATASET_TAGS_JSON, DATA_IN, DATA_OUT, DOCS, dumps([]),
                            EXPERIMENT_NOTEBOOK_PATH, DEPLOYMENT_NOTEBOOK_PATH, "100m", "100m", "1Gi", "1Gi", 300, 0, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO operators (uuid, name, status, status_message, deployment_id, task_id, parameters, position_x, position_y, dependencies, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        conn.execute(text, (OPERATOR_ID, None, "Unset", None, DEPLOYMENT_ID, TASK_ID, PARAMETERS_JSON, POSITION_X,
                            POSITION_Y, DEPENDENCIES_EMPTY_JSON, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO operators (uuid, name, status, status_message, experiment_id, task_id, parameters, position_x, position_y, dependencies, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        conn.execute(text, (OPERATOR_ID_2, None, "Unset", None, EXPERIMENT_ID_2, TASK_ID, PARAMETERS_JSON,
                            POSITION_X, POSITION_Y, DEPENDENCIES_EMPTY_JSON, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO templates (uuid, name, tasks, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s)"
        )
        conn.execute(text, (TEMPLATE_ID, NAME, TASKS_JSON, CREATED_AT, UPDATED_AT,))

        conn.close()

    def tearDown(self):
        conn = engine.connect()

        text = f"DELETE FROM templates WHERE uuid = '{TEMPLATE_ID}'"
        conn.execute(text)

        text = f"DELETE FROM operators WHERE experiment_id in" \
               f"(SELECT uuid FROM experiments where project_id = '{PROJECT_ID}')"
        conn.execute(text)

        text = f"DELETE FROM operators WHERE deployment_id in" \
               f"(SELECT uuid FROM deployments where project_id = '{PROJECT_ID}')"
        conn.execute(text)

        text = f"DELETE FROM tasks WHERE uuid IN ('{TASK_ID}', '{TASK_DATASET_ID}', '{TASK_ID_2}')"
        conn.execute(text)

        text = f"DELETE FROM deployments WHERE project_id = '{PROJECT_ID}'"
        conn.execute(text)

        text = f"DELETE FROM deployments WHERE name = '{DEPLOYMENT_MOCK_NAME}'"
        conn.execute(text)

        text = f"DELETE FROM experiments WHERE project_id = '{PROJECT_ID}'"
        conn.execute(text)

        text = f"DELETE FROM projects WHERE uuid = '{PROJECT_ID}'"
        conn.execute(text)
        conn.close()

    def test_list_deployments(self):
        rv = TEST_CLIENT.get(f"/projects/foo/deployments")
        result = rv.json()
        expected = {"message": "The specified project does not exist"}
        self.assertEqual(rv.status_code, 404)

        rv = TEST_CLIENT.get(f"/projects/{PROJECT_ID}/deployments")
        result = rv.json()
        self.assertIsInstance(result["deployments"], list)
        self.assertIsInstance(result["total"], int)
        self.assertEqual(rv.status_code, 200)

    def test_create_deployment(self):
        rv = TEST_CLIENT.post(f"/projects/foo/deployments", json={})
        result = rv.json()
        expected = {"message": "The specified project does not exist"}
        self.assertEqual(rv.status_code, 404)

        rv = TEST_CLIENT.post(f"/projects/{PROJECT_ID}/deployments", json={
            "templateId": "mock",
        })
        result = rv.json()
        expected = {"message": "templateId is not implemented yet"}
        self.assertIsInstance(result, dict)
        self.assertEqual(rv.status_code, 404)

        rv = TEST_CLIENT.post(f"/projects/{PROJECT_ID}/deployments", json={
            "copyFrom": "unk",
        })
        result = rv.json()
        expected = {"message": "source deployment does not exist"}
        self.assertEqual(rv.status_code, 400)

        rv = TEST_CLIENT.post(f"/projects/{PROJECT_ID}/deployments", json={
            "experiments": [],
        })
        result = rv.json()
        expected = {"message": "experiments were not specified"}
        self.assertIsInstance(result, dict)
        self.assertEqual(rv.status_code, 400)

        rv = TEST_CLIENT.post(f"/projects/{PROJECT_ID}/deployments", json={
            "experiments": ["unk"],
        })
        result = rv.json()
        expected = {"message": "some experiments do not exist"}
        self.assertIsInstance(result, dict)
        self.assertEqual(rv.status_code, 400)

        rv = TEST_CLIENT.post(f"/projects/{PROJECT_ID}/deployments", json={
            "experiments": [EXPERIMENT_ID_2],
        })
        result = rv.json()["deployments"]
        self.assertIsInstance(result, list)
        self.assertIn("operators", result[0])
        operator = result[0]["operators"][0]
        self.assertEqual(TASK_ID, operator["taskId"])

        rv = TEST_CLIENT.post(f"/projects/{PROJECT_ID}/deployments", json={
            "templateId": TEMPLATE_ID
        })
        result = rv.json()["deployments"]
        self.assertIsInstance(result, list)
        self.assertIn("operators", result[0])
        operator = result[0]["operators"][0]
        self.assertEqual(TASK_ID, operator["taskId"])

        rv = TEST_CLIENT.post(f"/projects/{PROJECT_ID}/deployments", json={
            "copyFrom": DEPLOYMENT_ID,
        })
        result = rv.json()
        expected = {"message": "name is required to duplicate deployment"}
        self.assertEqual(rv.status_code, 400)

        rv = TEST_CLIENT.post(f"/projects/{PROJECT_ID}/deployments", json={
            "copyFrom": DEPLOYMENT_ID,
            "name": NAME,
        })
        result = rv.json()
        expected = {"message": "a deployment with that name already exists"}
        self.assertEqual(rv.status_code, 400)

        rv = TEST_CLIENT.post(f"/projects/{PROJECT_ID}/deployments", json={
            "copyFrom": DEPLOYMENT_ID,
            "name": COPY_NAME,
        })
        result = rv.json()["deployments"]
        self.assertIsInstance(result, list)
        self.assertEqual(COPY_NAME, result[0]["name"])
        self.assertIn("operators", result[0])
        operator = result[0]["operators"][0]
        self.assertEqual(TASK_ID, operator["taskId"])

    def test_get_deployment(self):
        rv = TEST_CLIENT.get(f"/projects/foo/deployments/{DEPLOYMENT_ID}")
        result = rv.json()
        expected = {"message": "The specified project does not exist"}
        self.assertEqual(rv.status_code, 404)

        rv = TEST_CLIENT.get(f"/projects/foo/deployments/foo-bar")
        result = rv.json()
        expected = {"message": "The specified deployment does not exist"}
        self.assertEqual(rv.status_code, 404)

        rv = TEST_CLIENT.get(f"/projects/{PROJECT_ID}/deployments/{DEPLOYMENT_ID}")
        result = rv.json()
        self.assertIsInstance(result, dict)
        self.assertEqual(rv.status_code, 200)

    def test_delete_deployment(self):
        rv = TEST_CLIENT.get(f"/projects/foo/deployments/{DEPLOYMENT_ID}")
        result = rv.json()
        expected = {"message": "The specified project does not exist"}
        self.assertEqual(rv.status_code, 404)

        rv = TEST_CLIENT.delete(f"/projects/{PROJECT_ID}/deployments/buz-qux")
        result = rv.json()
        expected = {"message": "The specified deployment does not exist"}
        self.assertDictEqual(expected, result)
        self.assertEqual(rv.status_code, 404)

        rv = TEST_CLIENT.delete(f"/projects/{PROJECT_ID}/deployments/{DEPLOYMENT_ID}")
        result = rv.json()
        expected = {"message": "Deployment deleted"}
        self.assertDictEqual(expected, result)
        self.assertEqual(rv.status_code, 200)

    def test_update_deployment(self):
        rv = TEST_CLIENT.patch(f"/projects/foo/deployments/{DEPLOYMENT_ID}", json={})
        result = rv.json()
        expected = {"message": "The specified project does not exist"}
        self.assertEqual(rv.status_code, 404)

        rv = TEST_CLIENT.patch(f"/projects/{PROJECT_ID}/deployments/buz-qux", json={})
        result = rv.json()
        expected = {"message": "The specified deployment does not exist"}
        self.assertDictEqual(expected, result)
        self.assertEqual(rv.status_code, 404)

        rv = TEST_CLIENT.patch(f"/projects/{PROJECT_ID}/deployments/{DEPLOYMENT_ID_2}", json={"name": NAME})
        result = rv.json()
        expected = {"message": "a deployment with that name already exists"}
        self.assertDictEqual(expected, result)
        self.assertEqual(rv.status_code, 400)

        rv = TEST_CLIENT.patch(f"/projects/{PROJECT_ID}/deployments/{DEPLOYMENT_ID}", json={"name": "Foo Bar"})
        result = rv.json()
        self.assertIsInstance(result, dict)
        self.assertEqual(rv.status_code, 200)
