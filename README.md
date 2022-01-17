# braskoload

## Configuration
The configuration needs to be filled out in braskoload.conf

## Requirements

Relies on the [askoclic](https://github.com/askomics/askoclics) CLI [for Askomics](https://github.com/askomics/flaskomics)
Relies on [checkcel](https://github.com/mboudet/checkcel)
Optional requirement on gopublic (https://github.com/mboudet/gopublic) for loading data in [Gopublish](https://github.com/mboudet/golink) / [Golink](https://github.com/mboudet/golink)

## Parameters

Parameters are in the load.py file
(TODO : Better management?)

`datafiles` need to be a list of `Datafile`

### Datafile

A datafile has several properties

* pattern = A rglob pattern for matching the files
* validation_file (optional) = the checkcel template for this type of files
* integration_file = the askoclics template for integration
* sheet = the sheet to load in the tabulated file
* conversion_data = a dict for converting the loaded data (see after)
* search_folder = the folder where to search for files
* subset = Whether to extract a subset of the datafile
* data_files = Manage files (extracting paths for a column for instance, and if a gopublic link should be created)


## Launching
python load.py
