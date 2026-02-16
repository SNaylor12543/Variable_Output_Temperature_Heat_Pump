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
    def __init__(self, heating_temp, cooling_temp):
        # Having this heating distribution system only be able to run at a certain temperature to simulate a "dumb" HP
        # Assumes that the distribution system is large enough to be able to distribute maximum heating requirement
        self.heating_hydronics_temp = heating_temp
        self.cooling_hydronics_temp = cooling_temp

    def interp_flow_temp_heating(self, heating_demand):

        return np.ones(len(heating_demand)) * self.heating_hydronics_temp

    def interp_flow_temp_cooling(self, cooling_demand):

        return np.ones(len(cooling_demand)) * self.cooling_hydronics_temp

class Heat_Pump():
    def __init__(self, data_path):
        self.data_path = data_path
        # Define column names of outside air temp and heat pump delivery temp
        self.air_temp_name = "Air temperature(°C)"
        self.flow_temp_name = "Flow temperature(°C)"
        
        self.operational_air_temps, self.max_operational_flow_temp, self.min_operational_flow_temp = self.operating_condition_init()
        
    def interp_init(self, metric):
        # initialise interpolation field for different metrics of heat pump performance
        # x = flow temp
        # y = air temp
        # z = desired metric
        
        x, y, z = Data.field_data_from_csv(self.data_path, metric, self.air_temp_name, self.flow_temp_name)

        return Interpolator((x, y), z, method='linear', bounds_error=False, fill_value=None)
    
    def interp_call(self, output_temp, air_temp, interp_field):
        # Grab COP at a given output temp and outside temp
        
        output_temp, air_temp = np.broadcast_arrays(output_temp, air_temp)
        
        points = np.stack([output_temp.ravel(), air_temp.ravel()], axis = -1)

        return interp_field(points).reshape(output_temp.shape)

    def operating_condition_init(self):

        flow_temp = Data.column_from_csv(self.data_path, self.flow_temp_name)
        air_temp = Data.column_from_csv(self.data_path, self.air_temp_name)
        
        operational_air_temps = np.unique(air_temp)
        
        max_operational_flow_temp = np.zeros(len(operational_air_temps))
        min_operational_flow_temp = np.zeros(len(operational_air_temps))
        
        for i in range(len(operational_air_temps)):
            current_air_temp = operational_air_temps[i]
            indices = [j for j, x in enumerate(air_temp) if x == current_air_temp]
            max_operational_flow_temp[i] = np.max(flow_temp[indices])
            min_operational_flow_temp[i] = np.min(flow_temp[indices])

        return operational_air_temps, max_operational_flow_temp, min_operational_flow_temp

    def operating_conditions_check(self, flow_temp, air_temp):

        # temperature_steps = self.max_operational_air_temp[1] - self.max_operational_air_temp[0]
        # operational_flow_temps = np.interp(air_temp, self.operational_air_temps, self.max_operational_flow_temp)
        
        # out_of_operation_indices = [i for i, x in enumerate(operational_flow_temps - flow_temp) if x < 0] 

        # heat_pump_deliver_temp = flow_temp
        # heat_pump_deliver_temp[out_of_operation_indices] = operational_flow_temps[out_of_operation_indices]
        
        indices = np.digitize(air_temp, self.operational_air_temps) - 1

        indices = np.clip(indices,0, len(self.max_operational_flow_temp) - 1)
        
        operational_flow_temps = self.max_operational_flow_temp[indices]
        
        out_of_operation_indices = [i for i, x in enumerate(operational_flow_temps - flow_temp) if x < 0] 
        
        heat_pump_deliver_temp = flow_temp.copy()
        
        heat_pump_deliver_temp[out_of_operation_indices] = operational_flow_temps[out_of_operation_indices]
        
        return heat_pump_deliver_temp

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
    
    def interp_call(self, output_temp, air_temp, interp_field):
        # Grab EER at a given output temp and outside temp
        
        output_temp, air_temp = np.broadcast_arrays(output_temp, air_temp)
        
        points = np.stack([output_temp.ravel(), air_temp.ravel()], axis = -1)

        return interp_field(points).reshape(output_temp.shape)

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
        
        COP_array = self.HP.interp_call(hydronics_temp_array, air_temp_array, self.COP_interp_field)
            
        electricity_demand_array = np.divide(heating_demand_array, COP_array)
        
        return time_array, heating_demand_array, electricity_demand_array, COP_array, air_temp_array, hydronics_temp_array

class Reverse_HP_Controller():
    def __init__(self, Heat_Pump, HP_count, HVAC, Heating_Distribution, max_heat_pump_power, max_HVAC_power):
        self.tool_output_data = "Data/XL-BES-Tool_Output.csv"
        
        self.HP_count = HP_count
        
        self.max_heat_pump_power = max_heat_pump_power
        self.max_HVAC_power = max_HVAC_power
        
        self.HVAC = HVAC
        self.HP = Heat_Pump
        self.HD = Heating_Distribution
                  
        self.COP_interp_field = self.HP.interp_init("COP")
        self.HP_capacity_interp_field = self.HP.interp_init("Heating capacity (kW)")

        self.EER_interp_field = self.HVAC.interp_init("EER")

    def controller(self):
        # returns electricity demand in kWh!
        
        time_array = Data.column_from_csv(self.tool_output_data, "Hour_simulation")
        air_temp_array = Data.column_from_csv(self.tool_output_data, "External temperture (ºC)")

        heating_demand_array = Data.column_from_csv(self.tool_output_data, "Heating_thermal_load(kW)") 
        
        # limit heating demand to max heat pump power
        heating_demand_array = np.clip(heating_demand_array, 0, self.max_heat_pump_power)
        
        heating_hydronics_temp_array = self.HD.interp_flow_temp_heating(heating_demand_array)
        
        HP_deliver_temp = self.HP.operating_conditions_check(heating_hydronics_temp_array, air_temp_array)
        
        HP_capacity = self.HP_count * self.HP.interp_call(HP_deliver_temp, air_temp_array, self.HP_capacity_interp_field)

        COP_array = self.HP.interp_call(HP_deliver_temp, air_temp_array, self.COP_interp_field)

        HP_heating_delivery = heating_demand_array.copy()
        
        out_of_operation_indices = [i for i, x in enumerate(HP_capacity - heating_demand_array) if x < 0]

        HP_heating_delivery[out_of_operation_indices] = HP_capacity[out_of_operation_indices]
            
        HP_heating_electricity_demand_array = np.divide(HP_heating_delivery, COP_array)
        
        # calculate heating required by the electric boiler assuming a COP of 1
        
        electric_boiler_power = np.clip(heating_demand_array - HP_heating_delivery, 0, None)
        
        # summing both heating powers
        
        heating_electricity_demand_array = HP_heating_electricity_demand_array + electric_boiler_power

        # Calculating cooling electricity demand
        cooling_demand_array = Data.column_from_csv(self.tool_output_data, "Cooling_thermal_load(kW)") 

        cooling_demand_array = np.clip(cooling_demand_array, 0, self.max_HVAC_power)

        cooling_hydronics_temp_array = self.HD.interp_flow_temp_cooling(cooling_demand_array)
        
        EER_array = self.HVAC.interp_call(cooling_hydronics_temp_array, air_temp_array, self.EER_interp_field)
            
        cooling_electricity_demand_array = np.divide(cooling_demand_array, EER_array)
        
        # grabbing heating capacity for each hour
        
        heating_capacity_array = self.HP.interp_call(heating_hydronics_temp_array, air_temp_array, self.HP_capacity_interp_field)
        
        heat_pump_count = np.max(np.divide(heating_demand_array, heating_capacity_array))
        print("Requires " + str(heat_pump_count) + " heat pumps")

        return time_array, air_temp_array, heating_demand_array, heating_electricity_demand_array, heating_hydronics_temp_array, HP_deliver_temp, HP_heating_delivery, HP_heating_electricity_demand_array, COP_array, electric_boiler_power, cooling_demand_array, cooling_electricity_demand_array, cooling_hydronics_temp_array, EER_array