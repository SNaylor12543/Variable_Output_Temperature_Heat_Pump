import numpy as np
import pandas as pd

def column_from_csv(File_Path, Column_Name):
    # Extracts data from column with title: Column_Name from csv file in location: File_Path
    # Returns as a numpy array!
    
    df = pd.read_csv(File_Path)
    Column_Data = df[Column_Name].to_numpy()

    return Column_Data.copy()

def write_to_csv(File_path, Column_name, array):
    
    import pandas as pd

    df = pd.read_csv(File_path)

    df[Column_name] = array

    df.to_csv(File_path, index=False)


def field_data_from_csv(file_path, metric, air_temp, flow_temp):
    
    df = pd.read_csv(file_path)

    pivot = df.pivot(
        index=flow_temp,
        columns=air_temp,
        values=metric
    )

    # Sorts field
    pivot = pivot.sort_index(axis=0).sort_index(axis=1)
    
    # Replace NaN with zero
    pivot = pivot.fillna(0)

    # Extract arrays
    flow_temps = pivot.index.to_numpy()
    air_temps  = pivot.columns.to_numpy()
    metric = pivot.to_numpy()
    
    return flow_temps, air_temps, metric