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

    temp_folder = "tmp/"

    datafiles = [
        Datafile(
          pattern="Population_description*W.ods",
          integration_file="templates/population_wild_asko.json",
          conversion_data={"sheet": 2, "new_uri": "wild_population", "drop_columns": {"between": ["Population name", "Area (1)"]}},
          search_folder="/groups/brassica/db/projects/BrasExplor",
          temp_folder=temp_folder,
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
          temp_folder=temp_folder,
          askomics_client=asko_client
        ),
        Datafile(
          pattern="Botanical_species*.ods",
          integration_file="templates/botanical_asko.json",
          conversion_data={"sheet": 2, "new_uri": "botanical_density"},
          search_folder="/groups/brassica/db/projects/BrasExplor",
          temp_folder=temp_folder,
          askomics_client=asko_client
        ),
        Datafile(
          pattern="Pictures*.ods",
          integration_file="templates/picture_asko.json",
          conversion_data={"sheet": 2, "new_uri": "picture"},
          search_folder="/groups/brassica/db/projects/BrasExplor",
          temp_folder=temp_folder,
          askomics_client=asko_client
        ),
        Datafile(
          pattern="test_asko.ods",
          integration_file="/home/genouest/genouest/mboudet/test_asko",
          conversion_data={"new_uri": "sequence"},
          search_folder="/groups/brassica/db/projects/BrasExplor",
          temp_folder=temp_folder,
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

    # Cleanup
    files = glob.glob(temp_folder + "*")
    for f in files:
        os.remove(f)

    for datafile in datafiles:
        datafile.get_files()
        datafile.cleanup_askomics()
        datafile.convert_files()
        # datafile.upload_files()
        # datafile.integrate_files()


if __name__ == "__main__":
    main()
