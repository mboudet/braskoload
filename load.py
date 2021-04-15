from pathlib import Path
import os
import json

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

def _generate_id(file_name, row, values=[]):

    new_row = "{}_{}".format(file_name, row.replace(" ", "_"))

    if values:
        new_row += "_" + "_".join(values)
    return new_row

def convert_file(file_path, temp_path, subset={}, add_id={}):
    # add_id must be a dict, containing a column name with key "column", and optional list of values added (key "values")
    df = pandas.read_excel(file_path, sheet_name=2)
    if len(df) == 0:
        return False

    if subset:
        index = df.columns.get_loc(subset["column"])
        subdf = df.iloc[:, 0:index+1].copy()
        for col in subset.get("add_columns", []):
            subdf[col] = col
        subdf.to_csv(subset["temp_path"], index=False, sep="\t")
        df.drop(df.iloc[:, 1:index+1], inplace=True, axis=1)

    if add_id:
        new_col = df[add_id['column']].apply(lambda row: _generate_id(add_id["file_name"], row, add_id["values"]))
        new_col += np.arange(len(df)).astype(str)
        df.insert(loc=0, column="tmp_col", value=new_col)

    df.to_csv(temp_path, index=False, sep="\t")
    return True

def upload_asko(asko_client, file_path):
    asko_client.file.upload(file_path=file_path)

def integrate_asko(asko_client, file_name, json_data):
    files = asko_client.file.list()
    file_id = None
    for file in files:
        if file["name"] == file_name:
            file_id = file["id"]
            break
    if file_id:
        asko_client.file.integrate_csv(file_id, columns=json_data["columns"], headers=json_data["headers"])


def main():

    patterns = {
        "Population_description*W.ods": {
            "integration": "templates/population_wild_asko.json",
            "subset": {"column": "Altitude", "integration": "templates/population_base_asko.json", "add_column": True},
            "new_id": {"column": "Population name", "values": ["wild"]}
        },
        "Population_description*L.ods": {
            "integration": "templates/population_lr_asko.json",
            "subset": {"column": "Altitude", "integration": "templates/population_base_asko.json", "add_column": True},
            "new_id": {"column": "Population name", "values": ["landrace"]}
        },
        "Botanical_species*.ods": {
            "integration": "templates/botanical_asko.json",
            "new_id": {"column": "Name@Population", "values": ["botanical"],
            }
        },
        "Pictures*.ods": {
            "integration": "templates/picture_asko.json",
            "new_id": {"column": "name@Population", "values": ["pictures"],
            }
        }
    }

    asko_client = askoclics.AskomicsInstance(url="http://192.168.100.87", api_key="eTH89fmkkWLlcy9UWBVA")

    for pattern, validation_files in patterns.items():
        data = get_files(pattern, "/groups/brassica/db/projects/BrasExplor")
        print(data)
        for path, filename in data.items():
            base_name = filename.replace(".ods", "")
            new_file_name = filename.replace(".ods", ".csv")
            with open(validation_files["integration"]) as datafile:
                asko_data = json.load(datafile)

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

            new_id = validation_files.get("new_id", {})
            if new_id:
                new_id["file_name"] = base_name

            res = convert_file(os.path.join(path, filename), os.path.join("tmp/", new_file_name), subset=subset, add_id=new_id)

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

