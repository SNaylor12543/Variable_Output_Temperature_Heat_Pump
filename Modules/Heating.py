import numpy as np
from scipy.interpolate import RegularGridInterpolator as Interpolator
import matplotlib.pyplot as plt
import Modules.Data as Data

class Const_Temp_Heating_Distribution():
    def __init__(self, max_heating, max_target_temp, max_hydronics_temp):
        # Assume a mythical hydronic heating distribution system whose thermal resistance is constant across all flow rates and flow temperatures - runs on unicorn blood ig.
        self.thermal_conductance = max_heating / (max_hydronics_temp - max_target_temp)

    def hydronics_temp(self, Heating_Requirement, room_temp):
        # P = U * (hydronics_temp - room_temp)
        
        hydronics_temp = ( Heating_Requirement / self.thermal_conductance ) + room_temp

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
        
        x, y, z = Data.field_data_from_csv(self.data_path, metric, self.air_temp_name, self.flow_temp_name)

        return Interpolator((x, y), z, method='linear', bounds_error=False, fill_value=None)
    
    def max_hydronics_temp(self):
        # find the maximum hydronics temp the heat pump supports        
        
        return np.max(Data.column_from_csv(self.data_path, "Flow temperature(°C)"))
    
    def Calculate_COP(self, output_temp, air_temp, COP_interp_field):
        # Grab COP at a given output temp and outside temp
        
        output_temp, air_temp = np.broadcast_arrays(output_temp, air_temp)
        
        points = np.stack([output_temp.ravel(), air_temp.ravel()], axis = -1)

        return COP_interp_field(points).reshape(output_temp.shape)

class HP_Controller():
    def __init__(self, Heat_Pump, Heating_Distribution, max_heat_pump_power):
        self.tool_output_data = "Data/XL-BES-Tool_Output.csv"
        
        self.max_heat_pump_power = max_heat_pump_power
        
        self.HP = Heat_Pump
        self.HD = Heating_Distribution(np.max(Data.column_from_csv(self.tool_output_data, "Heating_thermal_load(kW)")),
                                       np.max(Data.column_from_csv(self.tool_output_data, "Indoor_temperature.Set-point_θair(ºC)")),
                                       self.HP.max_hydronics_temp())

        self.COP_interp_field = self.HP.interp_init("COP")

    def controller(self):
        # returns electricity demand in kWh!
        
        time_array = Data.column_from_csv(self.tool_output_data, "Hour_simulation")
        air_temp_array = Data.column_from_csv(self.tool_output_data, "External temperture (ºC)")
        # air_temp_array = np.ones(len(air_temp_array)) * 10
        inside_temp_array = Data.column_from_csv(self.tool_output_data, "Indoor_temperature.FF_θair(ºC)")
        heating_demand_array = Data.column_from_csv(self.tool_output_data, "Heating_thermal_load(kW)") 
        
        # limit heating demand to max heat pump power
        heating_demand_array = np.clip(heating_demand_array, 0, self.max_heat_pump_power)
        
        hydronics_temp_array = self.HD.hydronics_temp(heating_demand_array, inside_temp_array)
        
        COP_array = self.HP.Calculate_COP(hydronics_temp_array, air_temp_array, self.COP_interp_field)
            
        electricity_demand_array = np.divide(heating_demand_array, COP_array)
        
        return time_array, heating_demand_array, electricity_demand_array, COP_array
