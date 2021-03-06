from pidplatform import PIDPlatform

import numpy as np
#import tinyarray as ta
ta = np

def vec_norm(vec):
    return np.sqrt(ta.dot(vec, vec)) 

class Quadcopter(PIDPlatform):
    def __init__(self, agent, config):
        super(Quadcopter, self).__init__(agent, config)
        
        self._dt = config["interval"]
        
    def step(self, current_time, case):
        event = (current_time+self._dt, self.step)
        result_events = [event]
        self._controller_update()
        
        events = super(Quadcopter,self).step(current_time, case)
        result_events.extend(events)
        return result_events
