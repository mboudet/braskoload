from pathlib import Path
import os
import json

import pandas
import askoclics

# Get list of files matching pattern, keeping the latest one when there are two in the same folder
def get_files(pattern, root_path):
    file_dict = {}
    filtered_file_dict = {}
    for path in Path('./').rglob(pattern):
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

def _generate_id(row, values=[]):
    new_row = row.replace(" ", "_")
    if values:
        new_row += "_" + "_".join(values)
    return new_row

def convert_file(file_path, temp_path, add_id={}, add_columns=[]):
    # add_id must be a dict, containing a column name with key "column", and optional list of values added (key "values")
    df = pandas.read_excel(file_path, sheet_name=3)
    if add_id:
        new_col = df[add_id['column']].apply(lambda row: _generate_id(row, add_id["values"]))
        df.insert(loc=0, column="tmp_col", value=new_col)
    for col in add_columns:
        df[col] = col

    df.to_csv(temp_path, index=False)

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
        "Population_description*.ods": {
            "integration": "templates/population_asko.json",
            "new_columns": True
        },
        "Botanical_species*.ods": {
            "integration": "templates/botanical_asko.json",
            "new_id" = {"column": "Name@Population", "values": ["botanical"]}
        },
        "Pictures*.ods": {
            "integration": "templates/picture_asko.json"
            "new_id" = {"column": "name@Population", "values": ["pictures"]}
        }
    }

    for pattern, validation_files in patterns.items():
        data = get_files(pattern, "/groups/brassica/db/projects/BrasExplor")
        for path, filename in data.items():
            new_file_name = filename.replace(".ods", ".csv"))
            with open(validation_files["integration"]) as datafile:
                asko_data = json.load(datafile)

            new_columns = []
            if validation_files.get("new_columns"):
                split_path = path.split("/")
                plant_type = split_path[-1].split("_")[0]
                new_columns.append(plant_type)
                species = split_path[-2].replace("_", " ")
                new_columns.append(species)

            new_id = validation_files.get("new_id", {})
            convert_file(os.path.join(path, filename), new_file_name, add_columns=new_columns, add_id=new_ids)


if __name__ == "__main__":
    main()

