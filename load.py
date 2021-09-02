import os
import json
import glob

import askoclics
import gopublic

from braskoload.braskolib.datafile import Datafile


def main():

    gopublish_data = {
        "client": gopublic.GopublishInstance(url="", username="", password=""),
        "token": "",
        "base_url": ""
    }

    asko_client = askoclics.AskomicsInstance(url="http://192.168.100.87", api_key="")

    datasets = [
        Datafile(
          pattern="Population_description*W.ods",
          integration_file="templates/population_wild_asko.json",
          conversion_data={"sheet": 2, "new_uri": "wild_population", "drop_columns": {"after": "Population name", "before": "Area (1)"}},
          search_folder="/groups/brassica/db/projects/BrasExplor",
          temp_folder="tmp/",
          askomics_client=asko_client,
          subset={
            "integration_file": "templates/population_base_asko.json",
            "conversion_data": {
                "replace_name": [".csv", "_base.csv"],
                "add_columns": [{"from_path": -2, "convert": ["_", " "]}, {"from_path": -3}],
                "drop_columns": {"after": "Altitude"}
            }
          }
        ),
        Datafile(
          pattern="Population_description*L.ods",
          integration_file="templates/population_lr_asko.json",
          conversion_data={"sheet": 2, "new_uri": "landrace_population"},
          search_folder="/groups/brassica/db/projects/BrasExplor",
          temp_folder="tmp/",
          askomics_client=asko_client
        ),
        Datafile(
          pattern="Botanical_species*.ods",
          integration_file="templates/botanical_asko.json",
          conversion_data={"sheet": 2, "new_uri": "botanical_density"},
          search_folder="/groups/brassica/db/projects/BrasExplor",
          temp_folder="tmp/",
          askomics_client=asko_client
        ),
        Datafile(
          pattern="Pictures*.ods",
          integration_file="templates/picture_asko.json",
          conversion_data={"sheet": 2, "new_uri": "picture"},
          search_folder="/groups/brassica/db/projects/BrasExplor",
          temp_folder="tmp/",
          askomics_client=asko_client
        ),
        Datafile(
          pattern="test_asko.ods",
          integration_file="/home/genouest/genouest/mboudet/test_asko",
          conversion_data={"new_uri": "sequence"},
          search_folder="/groups/brassica/db/projects/BrasExplor",
          temp_folder="tmp/",
          askomics_client=asko_client,
          gopublish_data=gopublish_data,
          data_files=[{
            "col": "Nom fichier read R1",
            "col_base_path": "Chemin stockage séquences bulks sur Genouest",
            "delete_base": True,
            "gopublish": True
            }, {
            "col": "Nom fichier read R2",
            "col_base_path": "Chemin stockage séquences bulks sur Genouest",
            "delete_base": True,
            "gopublish": True
          }]
        )
    ]

    patterns = {
        "Population_description*W.ods": {
            "sheet": 2,
            "integration": "templates/population_wild_asko.json",
            "subset": {"column": "Altitude", "integration": "templates/population_base_asko.json", "add_column": True},
            "new_id": "wild_population"
        },
        "Population_description*L.ods": {
            "sheet": 2,
            "integration": "templates/population_lr_asko.json",
            "subset": {"column": "Altitude", "integration": "templates/population_base_asko.json", "add_column": True},
            "new_id": "landrace_population"
        },
        "Botanical_species*.ods": {
            "sheet": 2,
            "integration": "templates/botanical_asko.json",
            "new_id": "botanical_density"
        },
        "Pictures*.ods": {
            "sheet": 2,
            "integration": "templates/picture_asko.json",
            "new_id": "picture"
        },
        "test_asko.ods": {
            "sheet": 0,
            "integration": "templates/sequence_asko.json",
            "new_id": "sequence",
            "paths": [{"col": "Nom fichier read R1", "base": "Chemin stockage séquences bulks sur Genouest", "delete_base": True, "generate_uri": True}, {"col": "Nom fichier read R2", "base": "Chemin stockage séquences bulks sur Genouest", "delete_base": True}]
        }
    }

    # Cleanup
    files = glob.glob('tmp/*')
    for f in files:
        os.remove(f)

    entity_dict = {}
    for pattern, validation_files in patterns.items():
        if pattern == "test_asko.ods":
            data = get_files(pattern, "/home/genouest/genouest/mboudet/test_asko")
        else:
            data = get_files(pattern, "/groups/brassica/db/projects/BrasExplor")

        data = asko_cleanup(asko_client, data)

        for path, file in data.items():
            filename = file["file"]
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

            paths = validation_files.get("paths", [])
            sheet = validation_files.get("sheet", 0)

            new_id = validation_files.get("new_id", "")

            res, entity_dict = convert_file(os.path.join(path, filename), os.path.join("tmp/", new_file_name), entity_dict, subset=subset, add_id=new_id, entity_name=entity_name, asko_client=asko_client, gopublic_data=gopublic_data, paths=paths, sheet=sheet)

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
