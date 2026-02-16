import numpy as np
import pandas as pd

def column_from_csv(File_Path, Column_Name):
    # Extracts data from column with title: Column_Name from csv file in location: File_Path
    # Returns as a numpy array!
    
    df = pd.read_csv(File_Path)
    Column_Data = df[Column_Name].to_numpy()

    return Column_Data.copy()

def field_data_from_csv(File_Path, metric, air_temp, flow_temp):
    
    df = pd.read_csv(File_Path)

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
    COP = pivot.to_numpy()
    
    return flow_temps, air_temps, COP
