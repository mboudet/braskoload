import pandas as pd
import openpyxl

input_file = ""

input_data = {
    "Brassica rapa": {
        "sheet": 1,
        "pop_file": "",
        "input_files": [
            "BrasExplor_emergence_sheet_BR.xlsx",
            "BrasExplor_flowering_sheet.xlsx",
            "BrasExplor_harvest_sheet.xlsx",
            "BrasExplor_leaves_sheet_BR.xlsx",
        ]
    },
    "Brassica oleracea": {
        "sheet": 0,
        "suffix": "BO",
        "input_files": [
            "BrasExplor_emergence_sheet_BO.xlsx",
            "BrasExplor_flowering_sheet.xlsx",
            "BrasExplor_harvest_sheet.xlsx",
            "BrasExplor_leaves_sheet_BO.xlsx",
        ]
    }
}

pop_dict = {}

for key, value in input_data.items():
    pop_dict[key] = {}
    df = pd.read_excel(input_file, value["sheet"], keep_default_na=False)
    for col in df.columns:
        pop_dict[key][col] = df[col].dropna().to_list()
