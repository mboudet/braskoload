from pathlib import Path
import os
import json
import glob
from urllib.parse import quote

import pandas
import numpy as np
import askoclics

# Get list of files matching pattern, keeping the latest one when there are two in the same folder
def get_files(pattern, root_path):
    file_dict = {}
    filtered_file_dict = {}
    for path in Path(root_path).rglob(pattern):
        head, tail = os.path.split(path)
        if "Forms" in head:
            continue
        if not head in file_dict:
            file_dict[head] = []
        file_dict[head].append(tail)
    for path, names in file_dict.items():
        latest_file = max([os.path.join(path, name) for name in names], key=os.path.getctime)
        head, tail = os.path.split(latest_file)
        filtered_file_dict[head] = tail
    return filtered_file_dict

def convert_file(file_path, temp_path, entity_dict, subset={}, add_id="", entity_name="", asko_client=None):
    # add_id must be a dict, containing a column name with key "column", and optional list of values added (key "values")
    df = pandas.read_excel(file_path, sheet_name=2)
    if len(df) == 0:
        return False, entity_dict

    if subset:
        index = df.columns.get_loc(subset["column"])
        subdf = df.iloc[:, 0:index+1].copy()
        for col in subset.get("add_columns", []):
            subdf[col] = col
        subdf.to_csv(subset["temp_path"], index=False, sep="\t")
        df.drop(df.iloc[:, 1:index+1], inplace=True, axis=1)

    if add_id:
        if not add_id in entity_dict:
            entity_dict[add_id] = get_current_uri(asko_client, entity_name)

        new_col_id = np.arange(entity_dict[add_id], len(df) + entity_dict[add_id])
        df.insert(loc=0, column="tmp_col_id", value=new_col_id)
        df.insert(loc=0, column="tmp_col_uri", value=add_id + "_")

        df["tmp_col_uri"] = df["tmp_col_uri"] + np.arange(entity_dict[add_id], len(df) + entity_dict[add_id]).astype(str)
        entity_dict[add_id] += len(df)

    df.to_csv(temp_path, index=False, sep="\t")
    return True, entity_dict

def get_current_uri(asko_client, entity_name):

    config = asko_client.sparql.info()
    entity_name = quote(entity_name)

    graphs = [key for key in config["graphs"]]
    endpoints = [key for key in config["endpoints"]] 

    if not (config["graphs"] and config["endpoints"]):
        return 0

    query = "SELECT DISTINCT MAX(?temp_var_id) as ?output_var\nWHERE {\n"
    query += "?temp_var_uri rdf:type <{}{}> .\n".format(config["namespace_data"], entity_name)
    query += "?temp_var_uri <{}id> ?temp_var_id .\n".format(config["namespace_data"])
    query += "}"

    result = asko_client.sparql.query(query, graphs, endpoints)

    if not result.get("data") or not result["data"][0].get("output_var"):
        return 0
    else:
        return int(result["data"][0]["output_var"]) + 1


def upload_asko(asko_client, file_path):
    asko_client.file.upload(file_path=file_path)

def integrate_asko(asko_client, file_name, json_data):
    files = asko_client.file.list()
    file_id = None
    
    for file in files:
        if file["name"] == file_name:
            if not file_id:
                file_id = file["id"]
            if file_id and file_id < file["id"]:
                file_id = file["id"]
    if file_id:
        asko_client.file.integrate_csv(file_id, columns=json_data["columns"], headers=json_data["headers"])

def cleanup(asko_client):
    files = glob.glob('tmp/*')
    for f in files:
        os.remove(f)

    datasets = [dataset['id'] for dataset in asko_client.dataset.list()]
    files = [file['id'] for file in asko_client.file.list()]

    if datasets:
        asko_client.dataset.delete(datasets)
    if files:
        asko_client.file.delete(files)


def main():

    patterns = {
        "Population_description*W.ods": {
            "integration": "templates/population_wild_asko.json",
            "subset": {"column": "Altitude", "integration": "templates/population_base_asko.json", "add_column": True},
            "new_id": "wild_population"
        },
        "Population_description*L.ods": {
            "integration": "templates/population_lr_asko.json",
            "subset": {"column": "Altitude", "integration": "templates/population_base_asko.json", "add_column": True},
            "new_id": "landrace_population"
        },
        "Botanical_species*.ods": {
            "integration": "templates/botanical_asko.json",
            "new_id": "botanical_density"
        },
        "Pictures*.ods": {
            "integration": "templates/picture_asko.json",
            "new_id": "picture"
        }
    }

    asko_client = askoclics.AskomicsInstance(url="http://192.168.100.87", api_key="D3mUETv2KM9C94UEsyXr")
    cleanup(asko_client)

    entity_dict = {}
    for pattern, validation_files in patterns.items():
        data = get_files(pattern, "/groups/brassica/db/projects/BrasExplor")
        for path, filename in data.items():
            base_name = filename.replace(".ods", "")
            new_file_name = filename.replace(".ods", ".csv")
            with open(validation_files["integration"]) as datafile:
                asko_data = json.load(datafile)
                entity_name = asko_data["headers"][0]

            subset = {}
            if validation_files.get("subset"):
                subset = validation_files.get("subset")
                new_columns = []
                split_path = path.split("/")
                species = split_path[-2].replace("_", " ")
                new_columns.append(species)
                partner = split_path[-3]
                new_columns.append(partner)
                subset["add_columns"] = new_columns
                subset["temp_path"] = os.path.join("tmp/", new_file_name.replace(".csv", "_base.csv"))

            new_id = validation_files.get("new_id", "")

            res, entity_dict = convert_file(os.path.join(path, filename), os.path.join("tmp/", new_file_name), entity_dict, subset=subset, add_id=new_id, entity_name=entity_name, asko_client=asko_client)

            if res:
                if subset:
                    with open(subset["integration"]) as datafile:
                        subset_data = json.load(datafile)
                    upload_asko(asko_client, subset["temp_path"])
                    integrate_asko(asko_client, new_file_name.replace(".csv", "_base.csv"), subset_data)

                upload_asko(asko_client, os.path.join("tmp/", new_file_name))
                integrate_asko(asko_client, new_file_name, asko_data)

if __name__ == "__main__":
    main()

