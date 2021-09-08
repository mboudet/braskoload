import os
import json
import glob

import askoclics
import gopublic

import configparser

from braskolib.datafile import Datafile


def main():

    config = configparser.ConfigParser()
    config.read("braskoload.conf")

    gopublish_data = {
        "client": gopublic.GopublishInstance(url=config['gopublish']['url'], proxy_username=config['gopublish'].get('proxy_username'), proxy_password=config['gopublish'].get('proxy_password')),
        "token": config['gopublish']['token'],
        "base_url": config['gopublish']['base_url']
    }

    asko_client = askoclics.AskomicsInstance(url=config['askomics']['url'], api_key=config['askomics']['api_key'], proxy_username=config['askomics'].get('proxy_username'), proxy_password=config['askomics'].get('proxy_password'))

    temp_folder = config['main']['temp_folder']

    datafiles = [
        Datafile(
          pattern="[!Forms]*/Population*W*.*",
          integration_file="templates/askomics/population_wild_asko.json",
          conversion_data={"sheet": 2, "new_uri": "wild_population", "drop_columns": [{"between": ["Population name", "Area (1)"]}]},
          search_folder="/groups/brassica/db/projects/BrasExplor",
          temp_folder=temp_folder,
          askomics_client=asko_client,
          subset={
            "integration_file": "templates/askomics/population_base_asko.json",
            "conversion_data": {
                "sheet": 2,
                "append_name": "_base",
                "add_columns": [{"from_path": -2, "replace": ["_", " "]}, {"from_path": -3}],
                "drop_columns": [{"after": "Altitude"}]
            }
          }
        ),
        Datafile(
          pattern="'[!Forms]*/Population*L*.*'",
          integration_file="templates/askomics/population_lr_asko.json",
          conversion_data={"sheet": 2, "new_uri": "landrace_population", "drop_columns": [{"between": ["Population name", "Area (1)"]}]},
          search_folder="/groups/brassica/db/projects/BrasExplor",
          temp_folder=temp_folder,
          askomics_client=asko_client,
          subset={
            "integration_file": "templates/askomics/population_base_asko.json",
            "conversion_data": {
                "sheet": 2,
                "append_name": "_base",
                "add_columns": [{"from_path": -2, "replace": ["_", " "]}, {"from_path": -3}],
                "drop_columns": [{"after": "Altitude"}]
            }
          }
        ),
        Datafile(
          pattern="Botanical_species*.ods",
          integration_file="templates/askomics/botanical_asko.json",
          conversion_data={"sheet": 2, "new_uri": "botanical_density"},
          search_folder="/groups/brassica/db/projects/BrasExplor",
          temp_folder=temp_folder,
          askomics_client=asko_client
        ),
        Datafile(
          pattern="Pictures*.ods",
          integration_file="templates/askomics/picture_asko.json",
          conversion_data={"sheet": 2, "new_uri": "picture"},
          search_folder="/groups/brassica/db/projects/BrasExplor",
          temp_folder=temp_folder,
          askomics_client=asko_client
        ),
        Datafile(
          pattern="test_asko.ods",
          integration_file="templates/askomics/sequence_asko.json",
          conversion_data={"new_uri": "sequence"},
          search_folder="/home/genouest/genouest/mboudet/test_asko",
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
        datafile.upload_files()
        datafile.integrate_files()


if __name__ == "__main__":
    main()
