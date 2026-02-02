import numpy as np
from scipy.interpolate import RegularGridInterpolator as Interpolator
import matplotlib.pyplot as plt
import Modules.Data as Data

class Heating_Distribution():
    def __init__(self, max_heating, max_target_temp, max_hydronics_temp):
        # Assume a mythical hydronic heating distribution system whose thermal resistance is constant across all flow rates and flow temperatures - runs on unicorn blood ig.
        self.thermal_conductance = max_heating / (max_hydronics_temp - max_target_temp)

    def output_temp(self, Heating_Requirement, current_temp):
        # P = U * (hydronics_temp - target_temp)
        
        output_temp = ( Heating_Requirement / self.thermal_conductance ) + current_temp

        return output_temp

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
        
        x, y, z = Data.field_data_from_csv(self.data_path, metric, self.air_temp_name, self.flow_temp_name)

        return Interpolator((x, y), z, method='linear', bounds_error=False, fill_value=None)
    
    def max_hydronics_temp(self):
        # find the maximum hydronics temp the heat pump supports        
        
        return np.max(Data.column_from_csv(self.data_path, "Flow temperature(°C)"))
    
    def Calculate_COP(self, outside_temp, output_temp, COP_interp_field):
        # Grab COP at a given output temp and outside temp

        return COP_interp_field(np.array([output_temp, outside_temp]))

class Controller():
    def __init__(self, Heat_Pump):
        self.HP = Heat_Pump
        
        self.tool_output_data = "Data/XL-BES-Tool_Output.csv"
        self.HD = Heating_Distribution(np.max(Data.column_from_csv(self.tool_output_data, "Heating_thermal_load(kW)")),
                                       np.max(Data.column_from_csv(self.tool_output_data, "Indoor_temperature.Set-point_θair(ºC)")),
                                       self.HP.max_hydronics_temp() )

    def controller(self):

        COP_interp_field = self.HP.interp_init("COP")
        
        time_array = Data.column_from_csv(self.tool_output_data, "Hour_Simulation")
        air_temp_array = Data.column_from_csv(self.tool_output_data, "External temperture (ºC)")
        inside_temp_array = Data.column_from_csv(self.tool_output_data, "Indoor_temperature.FF_θair(ºC)")
        heating_demand_array = Data.column_from_csv(self.tool_output_data, "Heating_thermal_load(kW)") 

        return matrix