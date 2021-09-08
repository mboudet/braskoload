from pathlib import Path
import os
import json
from urllib.parse import quote

import pandas
import numpy as np


class Datafile():

    def __init__(self, pattern, integration_file, conversion_data, search_folder, temp_folder, askomics_client, gopublish_data={}, data_files={}, subset={}):
        current_args = locals()
        self.pattern = pattern
        self.search_folder = search_folder
        self.data_files = data_files
        self.files = {}
        self.conversion_data = conversion_data
        self.askomics_client = askomics_client
        self.gopublish_data = gopublish_data
        self.files_to_integrate = []
        self.temp_folder = temp_folder

        # Conversion data: Dict with keys:
        # sheet: 0 (optional, default to 0)
        # add_columns: [{"value": ["XXX"], "from_path": ["XXX"]}, "convert":[]]
        # drop_columns: [{column: "XXX", "before": "xxx", "after":xxx}]
        # new_uri: 'base_id_uri'
        # temp_base_name: "xxx"

        with open(integration_file) as datafile:
            self.integration_template = json.load(datafile)
            self.entity = self.integration_template["headers"][0]

        self.files = {}
        self.files_to_integrate = []
        self.latest_entity = False
        self.subdatafile = None

        # Create a subdatafile with current parameters modified
        if subset:
            for key, value in subset.items():
                current_args[key] = value
                current_args.pop('subset', None)
                current_args.pop('self', None)
            self.subdatafile = Datafile(**current_args)

    def get_files(self):
        file_dict = {}
        filtered_file_dict = {}
        for path in Path(self.search_folder).rglob(self.pattern):
            head, tail = os.path.split(path)
            if "Forms" in head:
                continue
            if head not in file_dict:
                file_dict[head] = []
            file_dict[head].append(tail)
        for path, names in file_dict.items():
            latest_file = max([os.path.join(path, name) for name in names], key=os.path.getctime)
            head, tail = os.path.split(latest_file)
            filtered_file_dict[head] = {"file": tail, "time": os.path.getctime(latest_file)}

        self.files = filtered_file_dict

        if self.subdatafile:
            self.subdatafile.get_files()

    def cleanup_askomics(self):
        datasets = self.askomics_client.dataset.list()
        files = self.askomics_client.file.list()

        names_to_delete = []
        files_to_delete = []
        keys_to_delete = []

        for key, value in self.files.items():
            file_name = value["file"].replace(".ods", ".csv")
            for file in files:
                if file["name"] == file_name:
                    if file["date"] < value["time"]:
                        files_to_delete.append(file["id"])
                        names_to_delete.append(file_name)
                        print("Deleting remote obsolete file " + file_name)
                    else:
                        print("Skipping older local file " + file_name)
                        keys_to_delete.append(key)

        datasets_to_delete = [dataset["id"] for dataset in datasets if dataset["name"] in names_to_delete]

        if datasets_to_delete:
            self.askomics_client.dataset.delete(datasets_to_delete)
        if files_to_delete:
            self.askomics_client.file.delete(files_to_delete)

        if keys_to_delete:
            for key in keys_to_delete:
                self.files.pop(key, None)

        if self.subdatafile:
            self.subdatafile.cleanup_askomics()

    def convert_files(self):
        for path, file in self.files.items():
            self._convert_file(path, file['file'])

        if self.subdatafile:
            self.subdatafile.convert_files()

    def upload_files(self):
        for file_path in self.files_to_integrate:
            self.askomics_client.file.upload(file_path=file_path)

        if self.subdatafile:
            self.subdatafile.upload_files()

    def integrate_files(self):
        uploaded_files = set([os.path.basename(file) for file in self.files_to_integrate])
        files = self.askomics_client.file.list()
        file_ids = set()

        for file in files:
            if file["name"] in uploaded_files:
                file_ids.add(file["id"])
        for id in file_ids:
            self.askomics_client.file.integrate_csv(id, columns=self.integration_template["columns"], headers=self.integration_template["headers"])

        if self.subdatafile:
            self.subdatafile.integrate_files()

    def _convert_file(self, file_path, file_name):
        # add_id must be a dict, containing a column name with key "column", and optional list of values added (key "values")
        full_path = os.path.join(file_path, file_name)
        convert_data = self.conversion_data
        df = pandas.read_excel(full_path, sheet_name=convert_data.get("sheet", 0))
        col_to_del = set()
        if len(df) == 0:
            return

        # Remove unnamed column (empty columns not expected)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

        # drop_columns: [{column: "XXX", "before": "xxx", "after":xxx}]
        for column in convert_data.get("drop_columns", []):
            if column.get("column"):
                df = df.drop(column.get("column"), 1)

            if column.get("before") and column.get("after"):
                before_loc = df.columns.get_loc(column.get("before"))
                after_loc = df.columns.get_loc(column.get("after"))
                df = df.loc[:, before_loc:after_loc + 1]
            else:
                if column.get("before"):
                    loc = df.columns.get_loc(column.get("before"))
                    df = df.iloc[:, loc:]
                if column.get("after"):
                    loc = df.columns.get_loc(column.get("after"))
                    df = df.iloc[:, :loc + 1]
            if column.get("between"):
                before_loc = df.columns.get_loc(column.get("between")[0])
                after_loc = df.columns.get_loc(column.get("between")[1])
                df = df.drop(df.iloc[:, before_loc + 1:after_loc], 1)

        added_column = 0
        for col in convert_data.get("add_columns", []):
            value = col.get("value")
            if col.get("from_path"):
                value = file_path.split("/")[col.get("from_path")]
            if col.get("replace"):
                value = value.replace(col.get("replace")[0], col.get("replace")[1])
            if value:
                df["temp_add_column_" + str(added_column)] = value
                added_column += 1

        if convert_data.get("new_uri"):
            if not self.latest_entity:
                self._set_last_entity()
            new_col_id = np.arange(self.latest_entity, len(df) + self.latest_entity)
            df.insert(loc=0, column="tmp_col_id", value=new_col_id)
            df.insert(loc=0, column="tmp_col_uri", value=convert_data.get("new_uri") + "_")

            df["tmp_col_uri"] = df["tmp_col_uri"] + np.arange(self.latest_entity, len(df) + self.latest_entity).astype(str)
            self.latest_entity += len(df)

        for path in self.data_files:
            if path.get("col_base_path"):
                df[path["col"]] = df[[path["col_base_path"], path["col"]]].agg('/'.join, axis=1)
                if path.get("delete_base"):
                    col_to_del.add(path["col_base_path"])
            if path.get("gopublish"):
                base_path = path.get("base_path")
                df[path["col"]] = df[path["col"]].apply(lambda x: self._get_file_uri(self.gopublish_data, base_path, x))

        for col in col_to_del:
            df = df.drop(col, 1)

        base_file_name, file_ext = os.path.splitext(file_name)
        if convert_data.get('append_name'):
            file_name = base_file_name + convert_data.get('append_name') + ".csv"
        else:
            file_name = base_file_name + ".csv"
        new_file_path = os.path.join(self.temp_folder, file_name)

        df.to_csv(new_file_path, index=False, sep="\t")
        self.files_to_integrate.append(new_file_path)

    def _set_last_entity(self):

        config = self.askomics_client.sparql.info()
        entity_name = quote(self.entity)

        graphs = [key for key in config["graphs"]]
        endpoints = [key for key in config["endpoints"]]

        if not (config["graphs"] and config["endpoints"]):
            self.latest_entity = 0
            return

        query = "SELECT DISTINCT MAX(?temp_var_id) as ?output_var\nWHERE {\n"
        query += "?temp_var_uri rdf:type <{}{}> .\n".format(config["namespace_data"], entity_name)
        query += "?temp_var_uri <{}id> ?temp_var_id .\n".format(config["namespace_data"])
        query += "}"

        result = self.askomics_client.sparql.query(query, graphs, endpoints)

        if not result.get("data") or not result["data"][0].get("output_var"):
            self.latest_entity = 0
        else:
            self.latest_entity = int(result["data"][0]["output_var"]) + 1

    def _get_file_uri(self, base_path, file_path):
        gopublic_client = self.gopublish_data['client']
        token = self.gopublish_data['token']
        base_url = self.gopublish_data['base_url']
        file_name = os.path.basename(file_path)
        data = gopublic_client.file.search(file_name)
        if data["files"]:
            return base_url + data["files"][0]["uri"]

        if base_path:
            file_path = os.path.join(base_path, file_path)

        if not os.path.exists(file_path):
            print("Missing file {}".format(file_path))
            return file_path

        data = gopublic_client.file.publish(file_path, token=token)
        return base_url + data["file_id"]
