# -*- coding: utf-8 -*-
"""Experiments Datasets controller."""
import io
from itertools import zip_longest
from typing import Optional

import pandas as pd
from fastapi.responses import StreamingResponse
from platiagro import load_dataset, stat_dataset

from projects import models
from projects.exceptions import NotFound
from projects.kfp.runs import get_latest_run_id


class DatasetController:
    def __init__(self, session):
        self.session = session

    def get_dataset(self, project_id: str, experiment_id: str, run_id: str, operator_id: str,
                    page: Optional[int] = 1, page_size: Optional[int] = 10, accept: Optional[str] = None):
        """
        Get dataset records from a run. Supports pagination.

        Parameters
        ----------
        project_id : str
        experiment_id : str
        run_id : str
            The run_id. If `run_id=latest`, then returns datasets from the latest run_id.
        operator_id : str
        page : int
            The page number. First page is 1.
        page_size : int
            The page size. Default value is 10.
        accept : str
            Whether dataset should be returned as csv file. Default to None.

        Returns
        -------
        list
            A list of dataset records.

        Raises
        ------
        NotFound
            When any of project_id, experiment_id, run_id, or operator_id does not exist.
        """
        if run_id == "latest":
            run_id = get_latest_run_id(experiment_id)

        name = self.get_dataset_name(operator_id, experiment_id)
        metadata = stat_dataset(name=name, operator_id=operator_id)

        if "run_id" not in metadata:
            raise NotFound("The specified run does not contain dataset")

        dataset = load_dataset(name=name, run_id=run_id, operator_id=operator_id)
        content = dataset.values.tolist()
        paged_data = self.data_pagination(page, page_size, content)

        if accept and "text/csv" in accept:
            if page_size == -1:
                content = dataset.to_csv(index=False)
            else:
                df = pd.DataFrame(columns=dataset.columns, data=paged_data)
                content = df.to_csv(index=False)

            return StreamingResponse(
                io.StringIO(content),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={name}"}
            )
        else:
            if page_size == -1:
                data = dataset.to_dict(orient="split")
                return {"columns": data["columns"], "data": data["data"], "total": len(data["data"])}
            else:
                return {"columns": dataset.columns.tolist(), "data": paged_data, "total": len(dataset)}

    def data_pagination(self, page, page_size, content):
        """
        Page records of a dataset.

        Parameters
        ----------
        page : int
        page_size : int
        content : pandas.DataFrame

        Returns
        -------
        list
            A list of dataset records

        Raises
        ------
        NotFound
            When a page does not exist.
        """
        # Splits records into `page_size` size
        split_into_pages = list(list(zip_longest(*(iter(content),) * abs(page_size))))

        try:
            # if the last page is not filled (has the length of page_size), `zip_longest`
            # fills with None values. Remove these values before returning
            paged_data = list(filter(None, split_into_pages[page-1]))
        except IndexError:
            raise NotFound("The specified page does not exist")

        return paged_data

    def get_dataset_name(self, operator_id, experiment_id):
        """
        Get operator's dataset name.

        Parameters
        ----------
        operator_id : str
        experiment_id: str

        Returns
        -------
        str
            The dataset name.

        Raises
        ------
        NotFound
            When a run does not have a dataset.
        """
        operator = self.session.query(models.Operator).get(operator_id)
        dataset_name = operator.parameters.get("dataset")

        if dataset_name is None:
            operators = self.session.query(models.Operator) \
                .filter_by(experiment_id=experiment_id) \
                .filter(models.Operator.uuid != operator_id) \
                .all()

            for operator in operators:
                dataset_name = operator.parameters.get("dataset")
                if dataset_name:
                    break

            if dataset_name is None:
                raise NotFound("No dataset assigned to the run")

        return dataset_name
