from pathlib import Path
import os
import json
import glob
from urllib.parse import quote

import pandas
import numpy as np
import askoclics
import gopublic

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
        filtered_file_dict[head] = {"file": tail, "time": os.path.getctime(latest_file)}
    return filtered_file_dict

def convert_file(file_path, temp_path, entity_dict, subset={}, add_id="", entity_name="", asko_client=None, gopublic_data=None):
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

def get_file_uri(gopublic_data, file_path):
    gopublic_client = gopublic_data['client']
    token = gopublic_client['token']
    base_url = gopublic_client['base_url']
    file_name = os.path.basename(file_path)
    data = gopublic_client.file.search(file_name)
    if data:
        return base_url + data[0]["uri"]

    data = gopublic_client.file.publish(file_path, token=token)
    return return base_url + data["file_id"]


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

def asko_cleanup(asko_client, data):

    datasets = asko_client.dataset.list()
    files = asko_client.file.list()

    names_to_delete = []
    files_to_delete = []
    keys_to_delete = []

    for key, value in data.items():
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
        asko_client.dataset.delete(datasets_to_delete)
    if files_to_delete:
        asko_client.file.delete(files_to_delete)

    if keys_to_delete:
        for key in keys_to_delete:
            data.pop(key, None)
    return data

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

    gopublic_data = {
        "client": gopublic.GopublishInstance(url="", username="", password=""),
        "token": "",
        "base_url": ""
    }

    asko_client = askoclics.AskomicsInstance(url="http://192.168.100.87", api_key="")
    # Cleanup
    files = glob.glob('tmp/*')
    for f in files:
        os.remove(f)

    entity_dict = {}
    for pattern, validation_files in patterns.items():
        data = get_files(pattern, "/groups/brassica/db/projects/BrasExplor")
        data = asko_cleanup(asko_client, data)

        for path, file in data.items():
            filename = file["file"]
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

            res, entity_dict = convert_file(os.path.join(path, filename), os.path.join("tmp/", new_file_name), entity_dict, subset=subset, add_id=new_id, entity_name=entity_name, asko_client=asko_client, gopublic_data=gopublic_data)

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

