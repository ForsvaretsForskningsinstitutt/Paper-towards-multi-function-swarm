import numpy as np

from shapely.geometry import Point, MultiPolygon
from shapely.ops import cascaded_union
class Evaluator(object):
    def __init__(self, parametric=False):
        self._parametric=parametric
    
    def _exploration_fit(self, case, return_components = False):
        
        if case.agents[0].sensors.get("Coverage") is None:
            if return_components:
                return {}
            else:
                return 0.
        
        squares = []
        
        coverage = 0.
        for i in xrange(10):
            for j in xrange(10):                    
                squares.append(case.blackboard["Coverage"][i,j])
                
                if case.blackboard["Coverage"][i,j] > 0:
                    coverage += min(2., float(case.blackboard["Coverage"][i,j]))
                
        coverage = float(coverage)/200.

        squares = sorted(squares)
        num_agents = len(case.agents)
        max_velocity = case.agents[0].platform.max_velocity
        max_time = case.config["config_simulator"]["max_time"]
        max_squares = float(num_agents * max_velocity * max_time) / (100.)

        max_square_median = max_squares/ (10.*10.)

        median_frequency_normalized = float(squares[len(squares)/2]) / max_square_median

        if return_components:
            components = {}
            
            components["median"] = median_frequency_normalized
             
            return components
        else:
            fitness = median_frequency + coverage
            
            return fitness
        
    def _localization_fit(self, case, return_components = False):
        if case.agents[0].sensors.get("Localization") is None:
            if return_components:
                return {}
            else:
                return 0.
            
        location_estimates = []
        
        for agent in case.agents:
            location_estimates.extend(agent.sensors.get("Localization").history)
            
        location_estimate_variance = 0.
        
        actual_position = np.array([200.,200.])
        
        for estimate in location_estimates:
            distance = np.linalg.norm(estimate-actual_position)
            
            location_estimate_variance += distance
            
        location_estimate_variance = location_estimate_variance/len(location_estimates)
        
        if return_components:
            components = {}
            
            components["variance"] = 1./location_estimate_variance
            
            return components
        else:
                
            fitness = 1./location_estimate_variance
            
            return fitness
        
            
    def _network_fit(self, case1, case2, return_components = False):
        if case1.agents[0].sensors.get("Relay") is None:
            if return_components:
                return {}
            else:
                return 0.

        covered_area_avg = 0.
        for case in [case1,case2]:
            
            connection_sets = []

            for agent in case.agents:
                member_of = []
                
                for i,connection_group in enumerate(connection_sets):
                    connected_to = False
                    
                    for connected_agent in agent.sensors.get("Relay").connections:
                        if connected_agent in connection_group:
                            connected_to = True
                    
                    if connected_to:
                        member_of.append((i,connection_group))
                
                if len(member_of) == 0:
                    new_set = set()
                    new_set.add(agent)
                    connection_sets.append(new_set)
                elif len(member_of) == 1:            
                    member_of[0][1].add(agent)
                else:
                    new_set = set()
                    
                    for i,connection_group in member_of:
                        new_set.update(connection_group)
                        
                    member_of.reverse()
                    for i,_ in member_of:
                        connection_sets.pop(i)
                        
                    connection_sets.append(new_set)
                    
            
            largest_set = max(connection_sets, key=lambda s: len(s))
            
            
            polygons = []


            com_range = 0.
            for agent in largest_set:
                x,y = agent.platform.position
                com_range = agent.sensors.get("Relay")._range
                p = Point(x,y).buffer(com_range)
                polygons.append(p)


            covered_area = cascaded_union(MultiPolygon(polygons)).area 
            max_covered_area = (len(case.agents)*3.14*com_range*com_range)/2.0
            covered_area_percentage = covered_area / max_covered_area

            covered_area_avg += covered_area_percentage


        if return_components:
            components = {}
            
            components["covered"] = covered_area_avg/2.0
            
            return components
        else:
            raise Exception("Not properly implemented")
            fitness =  float(len(largest_set))/len(case.agents)

            return fitness
        
    def _base_fit(self, case1, case2, return_components=False):
        
        movement = 0.
        for agent_start, agent_end in zip(case1.agents, case2.agents):
            distance = np.linalg.norm(agent_start.platform.position-agent_end.platform.position)
            movement += min(1., distance/100.)
            
        if return_components:
            components = {}
            
            components["movement"] = movement/len(case1.agents)
            
            return components
        else:
                
            fitness = movement/len(case1.agents)
            
            return 1. + fitness
        
    def post_evaluator_loggers(self, list_of_loggers):
        summed = 1.
        
        for logger in list_of_loggers:
            with logger as open_logger:
                summed *= self._case_evaluator(open_logger._simulation_log)
            
        return summed
        
        
    def post_evaluator_shelves(self, list_of_shelves):
        summed = 1.
        
        for shelve_t in list_of_shelves:
            summed *= self._case_evaluator(shelve_t)
            
        return summed
        
    def _case_evaluator(self, run_log):        
        ticks = sorted(map(int,run_log.keys()))
        
        start_case_id = str(min(ticks))
        end_case_id = str(max(ticks))
        
        start_case = run_log[start_case_id]
        end_case = run_log[end_case_id]
        
        
        fit_base = self._base_fit(start_case, end_case)
        fit_net = self._network_fit(end_case)
        fit_loc = self._localization_fit(end_case)
        fit_exp = self._exploration_fit(end_case)
        
        fitness = fit_base + fit_net + fit_loc + fit_exp
            
        return fitness
        
    def fitness_components(self, list_of_shelves):
        components = {}
        
        for shelve_t in list_of_shelves:
            components[case_name] = self._case_components(shelve_t)
        return components

    def _case_components(self, shelve):
        ticks = sorted(map(int,shelve.keys()))
        
        start_case_id = str(min(ticks))
        middle_case_id = str((max(ticks)-min(ticks))/2)
        end_case_id = str(max(ticks))
        
        start_case = shelve[start_case_id]
        middle_case = shelve[middle_case_id]
        end_case = shelve[end_case_id]
        
        case_name = str(start_case)
        case_component = {}
        
        #case_component["base"] = self._base_fit(start_case, end_case, return_components=True)
        case_component["network"] = self._network_fit(middle_case, end_case, return_components=True)
        #case_component["localization"] = self._localization_fit(end_case, return_components=True)
        case_component["exploration"] = self._exploration_fit(end_case, return_components=True)
        
        return case_component

    def fitness_map_elites(self, list_of_loggers):
        #test_fitness = 1.
        test_fitness = 0.

        import numpy as np

        characteristics = {}
        
        for logger in list_of_loggers:
            with logger as open_logger:
                case_components = self._case_components(open_logger._simulation_log)
                
                for application, application_component in case_components.items():
                    for measure, value in application_component.items():

                        characteristics_name = "_".join([application,measure])
                        if characteristics.get(characteristics_name) is None:
                            characteristics[characteristics_name] = value
                        else:
                            characteristics[characteristics_name] += value

                if not self._parametric:
                    test_fitness += 2./(1.+np.linalg.norm(open_logger._simulation_log['0'].config["platform_templates"]["adv"]["config_behavior"]["weights"]))
                else:
                    test_fitness += 2./(1.+np.linalg.norm(open_logger._simulation_log['0'].config["platform_templates"]["adv"]["config_behavior"]["weights"])+np.linalg.norm(open_logger._simulation_log['0'].config["platform_templates"]["adv"]["config_behavior"]["scale"]))
                

        for key,value in characteristics.items():
            characteristics[key] = value/len(list_of_loggers)

        test_fitness = test_fitness/len(list_of_loggers)

        return test_fitness, characteristics

if __name__=="__main__":
    import shelve, cPickle
    import argparse

    shelve.Pickler = cPickle.Pickler
    shelve.Unpickler = cPickle.Unpickler
                
    def create_parser():
        parser = argparse.ArgumentParser()
        parser.add_argument("filename", nargs=1, type=str)
        return parser

    parser = create_parser()
    args = parser.parse_args()

    eva = Evaluator()

    cases = shelve.open(args.filename[0])
    print   eva._case_components(cases)
    
