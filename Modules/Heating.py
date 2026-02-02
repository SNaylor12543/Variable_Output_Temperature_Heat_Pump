import numpy as np
import matplotlib.pyplot as plt

class Heating_Distribution():
    def __init__(max_heating, max_hydronics_temp, target_temp):
        self.target_temp = target_temp
        self.thermal_resistance = max_heating / (max_hydronics_temp - target_temp)

    def output_temp(Heating_Requirement):
        # P = U * (hydronics_temp - target_temp)
        
        return ( Heating_Requirement / self.thermal_resistance ) + self.target_temp