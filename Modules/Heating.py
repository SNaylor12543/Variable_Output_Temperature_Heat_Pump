import numpy as np
from scipy.interpolate import RegularGridInterpolator as Interpolator
import matplotlib.pyplot as plt
import Modules.Data as Data
import math

class Heating_Distribution():
    def __init__(self, data_path, max_heating_required, max_cooling_required):
        self.heating_data_path = data_path + "/Heating.csv"
        self.cooling_data_path = data_path + "/Cooling.csv"

        self.flow_temp_title = "Water Inlet Temp (°C)"
        self.heating_demand_title = "Heating Delivered (kW)"
        self.cooling_demand_title = "Cooling Delivered (kW)"

        # Calculate number of fan coils required to match peak heating demand
        self.fan_coil_count_heating = math.ceil(max_heating_required/np.max(Data.column_from_csv(self.heating_data_path, self.heating_demand_title)))

        # Calculate number of fan coils required to match peak cooling demand
        self.fan_coil_count_cooling = math.ceil(max_cooling_required/np.max(Data.column_from_csv(self.cooling_data_path, self.cooling_demand_title)))
        
        self.fan_coil_count = max(self.fan_coil_count_heating, self.fan_coil_count_cooling)
        print("Number of fan coils required: " + str(self.fan_coil_count))
        
    def interp_flow_temp_heating(self, heating_demand):
        # extract data from .csv file
    
        heating_demand_data = Data.column_from_csv(self.heating_data_path, self.heating_demand_title)
        flow_temp_data = Data.column_from_csv(self.heating_data_path, self.flow_temp_title)
        
        return np.interp(heating_demand, self.fan_coil_count * heating_demand_data, flow_temp_data)

    def interp_flow_temp_cooling(self, cooling_demand):
    
        cooling_demand_data = Data.column_from_csv(self.cooling_data_path, self.cooling_demand_title)
        flow_temp_data = Data.column_from_csv(self.cooling_data_path, self.flow_temp_title)
        
        return np.interp(cooling_demand, self.fan_coil_count * cooling_demand_data, flow_temp_data)

class Const_Temp_Heating_Distribution():
    def __init__(self, max_hydronics_temp):
        # Having this heating distribution system only be able to run at a certain temperature to simulate a "dumb" HP
        # Assumes that the distribution system is large enough to be able to distribute maximum heating requirement
        self.const_hydronics_temp = max_hydronics_temp

    def hydronics_temp(self, Heating_Requirement, room_temp):

        return np.ones(len(Heating_Requirement)) * self.const_hydronics_temp

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
    
    def Calculate_COP(self, output_temp, air_temp, COP_interp_field):
        # Grab COP at a given output temp and outside temp
        
        output_temp, air_temp = np.broadcast_arrays(output_temp, air_temp)
        
        points = np.stack([output_temp.ravel(), air_temp.ravel()], axis = -1)

        return COP_interp_field(points).reshape(output_temp.shape)

class HVAC():
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
    
    def Calculate_EER(self, output_temp, air_temp, EER_interp_field):
        # Grab EER at a given output temp and outside temp
        
        output_temp, air_temp = np.broadcast_arrays(output_temp, air_temp)
        
        points = np.stack([output_temp.ravel(), air_temp.ravel()], axis = -1)

        return EER_interp_field(points).reshape(output_temp.shape)

class HP_Controller():
    def __init__(self, Heat_Pump, Heating_Distribution, max_heat_pump_power, max_HVAC_power):
        self.tool_output_data = "Data/XL-BES-Tool_Output.csv"
        
        self.max_heat_pump_power = max_heat_pump_power
        self.max_HVAC_power = max_HVAC_power
        
        self.HP = Heat_Pump
        self.HD = Heating_Distribution
                  
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
        
        return time_array, heating_demand_array, electricity_demand_array, COP_array, air_temp_array, hydronics_temp_array

class Reverse_HP_Controller():
    def __init__(self, Heat_Pump, HVAC, Heating_Distribution, max_heat_pump_power, max_HVAC_power):
        self.tool_output_data = "Data/XL-BES-Tool_Output.csv"
        
        self.max_heat_pump_power = max_heat_pump_power
        self.max_HVAC_power = max_HVAC_power
        
        self.HVAC = HVAC
        self.HP = Heat_Pump
        self.HD = Heating_Distribution
                  
        self.COP_interp_field = self.HP.interp_init("COP")
        self.EER_interp_field = self.HVAC.interp_init("EER")

    def controller(self):
        # returns electricity demand in kWh!
        
        time_array = Data.column_from_csv(self.tool_output_data, "Hour_simulation")
        air_temp_array = Data.column_from_csv(self.tool_output_data, "External temperture (ºC)")
        # Quick and dirty comparison with GSHP
        # air_temp_array = np.ones(len(air_temp_array)) * 10
        
        inside_temp_array = Data.column_from_csv(self.tool_output_data, "Indoor_temperature.FF_θair(ºC)")

        heating_demand_array = Data.column_from_csv(self.tool_output_data, "Heating_thermal_load(kW)") 
        
        # limit heating demand to max heat pump power
        heating_demand_array = np.clip(heating_demand_array, 0, self.max_heat_pump_power)
        
        heating_hydronics_temp_array = self.HD.interp_flow_temp_heating(heating_demand_array)
        
        COP_array = self.HP.Calculate_COP(heating_hydronics_temp_array, air_temp_array, self.COP_interp_field)
            
        heating_electricity_demand_array = np.divide(heating_demand_array, COP_array)

        # Calculating cooling electricity demand
        cooling_demand_array = Data.column_from_csv(self.tool_output_data, "Cooling_thermal_load(kW)") 

        cooling_hydronics_temp_array = self.HD.interp_flow_temp_cooling(cooling_demand_array)
        
        EER_array = self.HVAC.Calculate_EER(cooling_hydronics_temp_array, air_temp_array, self.EER_interp_field)
            
        cooling_electricity_demand_array = np.divide(cooling_demand_array, EER_array)

        return time_array, air_temp_array, heating_demand_array, heating_electricity_demand_array, heating_hydronics_temp_array, COP_array, cooling_demand_array, cooling_electricity_demand_array, cooling_hydronics_temp_array, EER_array
