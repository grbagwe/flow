""" Definitions of transfer classes and composition and randomization functions
"""
from copy import deepcopy
import numpy as np

from flow.core.params import InFlows
from examples.exp_configs.rl.multiagent.multiagent_i210 import VEH_PER_HOUR_BASE_119257914, VEH_PER_HOUR_BASE_27414345, VEH_PER_HOUR_BASE_27414342

def make_inflows(penetration_rate=0.1, flow_rate_coef=1.0, departSpeed=20):
    inflow = InFlows()
    # main highway
    assert penetration_rate < 1.0, "your penetration rate is over 100%"
    assert penetration_rate > 0.0, "your penetration rate should be above zero"

    inflow_119257914 = dict(veh_type="human",
        edge="119257914",
        vehs_per_hour=VEH_PER_HOUR_BASE_119257914 * penetration_rate * flow_rate_coef,
        # probability=1.0,
        departLane="random",
        departSpeed=departSpeed)

    inflow_27414345 = dict(veh_type="human",
        edge="27414345",
        vehs_per_hour=VEH_PER_HOUR_BASE_27414345 * penetration_rate * flow_rate_coef,
        departLane="random",
        departSpeed=departSpeed)

    inflow_27414342 = dict(veh_type="human",
        edge="27414342#0",
        vehs_per_hour=VEH_PER_HOUR_BASE_27414342 * penetration_rate * flow_rate_coef,
        departLane="random",
        departSpeed=departSpeed)

    inflow_119257914_av =  dict(veh_type="av",
        edge="119257914",
        vehs_per_hour=int(VEH_PER_HOUR_BASE_119257914 * penetration_rate * flow_rate_coef),
        # probability=1.0,
        departLane="random",
        departSpeed=departSpeed)

    all_inflow_defs = (inflow_119257914, inflow_27414345, inflow_27414342, inflow_119257914_av)

    for inflow_def in all_inflow_defs:
        inflow.add(**inflow_def)
    
    return inflow



class BaseTransfer:
    def __init__(self):
        self.transfer_str = "Base"
        pass

    def flow_params_modifier_fn(self, flow_params, clone_params=True):
        """Returns modified flow_params
        
        Arguments:
            flow_params {[flow_params_dictionary]} -- [flow_params]
        """
        if clone_params:
            flow_params = deepcopy(flow_params)

        return flow_params

    def env_modifier_fn(self, env):
        """ Modifies the env before rollouts are run
        
        Arguments:
            env {[I210MultiEnv]} -- [Env to modify]
        """
        pass


class InflowTransfer(BaseTransfer):
    """ Modifies the inflow of i210 env
    """
    def __init__(self, penetration_rate=0.1, flow_rate_coef=1.0, departSpeed=20):
        super(InflowTransfer, self).__init__()
        self.penetration_rate = penetration_rate
        self.flow_rate_coef = flow_rate_coef
        self.departSpeed = departSpeed

        self.transfer_str = "{:0.2f}_pen_{:0.2f}_flow_rate_coef_{:0.2f}_depspeed".format(penetration_rate, flow_rate_coef, departSpeed)

    def flow_params_modifier_fn(self, flow_params, clone_params=True):
        if clone_params:
            flow_params = deepcopy(flow_params)

        flow_params['net'].inflows = make_inflows(self.penetration_rate, self.flow_rate_coef, self.departSpeed)
        
        return flow_params

def inflows_range(penetration_rates=0.1, flow_rate_coefs=1.0, departSpeeds=20):
    if not hasattr(penetration_rates, '__iter__'):
        penetration_rates = [penetration_rates]
    if not hasattr(flow_rate_coefs, '__iter__'):
        flow_rate_coefs = [flow_rate_coefs]
    if not hasattr(departSpeeds, '__iter__'):
        departSpeeds = [departSpeeds]

    for departSpeed in departSpeeds:
        for penetration_rate in penetration_rates:
            for flow_rate_coef in flow_rate_coefs:
                yield InflowTransfer(penetration_rate=penetration_rate, flow_rate_coef=flow_rate_coef, departSpeed=departSpeed)
