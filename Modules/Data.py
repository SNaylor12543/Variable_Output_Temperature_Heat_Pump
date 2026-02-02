import numpy as np
import pandas as pd

def column_from_csv(File_Path, Column_Name):
    # Extracts data from column with title: Column_Name from csv file in location: File_Path
    
    df = pd.read_csv(File_Path)
    Column_Data = df[Column_Name].to_numpy()

    return Column_Data
