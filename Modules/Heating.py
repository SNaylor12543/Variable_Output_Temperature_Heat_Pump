import numpy as np
from scipy.interpolate import RegularGridInterpolator as Interpolator
import matplotlib.pyplot as plt
import Modules.Data as Data

class Heating_Distribution():
    def __init__(self, max_heating, target_temp, output_temp_array):
        self.target_temp = target_temp
        self.allowed_hydronics_temp = output_temp_array

        max_hydronics_temp = np.max(allowed_hydronics_temp)
        self.thermal_conductance = max_heating / (max_hydronics_temp - self.target_temp)

    def output_temp(self, Heating_Requirement):
        # P = U * (hydronics_temp - target_temp)
        
        hydronics_temp = ( Heating_Requirement / self.thermal_conductance ) + self.target_temp

        return hydronics_temp

class Heat_Pump():
    def __init__(self, data_path):
        self.data_path = data_path
        # Define column names of outside air temp and heat pump delivery temp
        self.air_temp_name = "Air temperature(°C)"
        self.flow_temp_name = "Flow temperature(°C)"
        
    def interp_init(self, metric):
        # initialise interpolation field for different metrics of heat pump performance
        # x = flow temp
        # y = air temp
        # z = desired metric
        
        # x = Data.column_from_csv(self.data_path, self.flow_temp_name)
        # y = Data.column_from_csv(self.data_path, self.air_temp_name)
        # z = Data.column_from_csv(self.data_path, metric)
        
        x, y, z = Data.field_data_from_csv(self.data_path, metric, self.air_temp_name, self.flow_temp_name)

        return Interpolator((x, y), z, method='linear', bounds_error=False, fill_value=None)
    
    def Calculate_COP(self, outside_temp, output_temp, COP_interp_field):
        # Grab COP at a given output temp and outside temp

        return COP_interp_field(np.array([output_temp, outside_temp]))

class Controller():
    def __init__(self, Heating_Distribution_System, Heat_Pump):
        self.HD = Heating_Distribution_System
        self.HP = Heat_Pump

    def controller(self):

        COP_interp_field = self.HP.interp_init("COP")
        
        time_array = Data.column_from_csv("Data/XL-BES-Tool_Output.csv")

        return matrix