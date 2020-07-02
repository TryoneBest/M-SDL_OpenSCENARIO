import matplotlib.pyplot as plt
import math
import pandas as pd
import numpy as np
import datetime
from scipy.signal import savgol_filter


class GeneralFunc:
    @staticmethod
    def cal_init(ego_speed, obj_speed_x, obj_x_range, obj_y_range):
        left = 0
        while left < len(obj_speed_x) and obj_speed_x[left] == 0:
            left += 1
        if left >= len(obj_speed_x):
            return 1000, 1000, 1000
        sum_val = 0
        for j in range(left + 1):
            sum_val += ego_speed[j]
        return sum_val + obj_x_range[left], obj_y_range[left], obj_speed_x[left]

    @staticmethod
    def parse_data(file_path):
        df = pd.read_csv(file_path)
        ego_speed = df.loc[:, 'FOT_Control.Speed']
        lane_offset = df.loc[:, 'Road.Scout.Lane_Offset']
        sms_object = []
        x_velocity = []
        y_velocity = []
        x_range = []
        y_range = []
        for i in range(8):
            temp = str(i)
            sms_object.append(df.loc[:, 'SMS.Object_ID_T' + temp])
            x_velocity.append(df.loc[:, 'SMS.X_Velocity_T' + temp])
            y_velocity.append(df.loc[:, 'SMS.Y_Velocity_T' + temp])
            x_range.append(df.loc[:, 'SMS.X_Range_T' + temp])
            y_range.append(df.loc[:, 'SMS.Y_Range_T' + temp])
        objects = set()
        for i in range(8):
            tag = True
            for j in sms_object[i]:
                if not math.isnan(j):
                    objects.add(j)
                    tag = False
            if tag:
                break
        objects_speed = dict()
        objects_range = dict()
        # print(ego_speed.shape[0])
        for i in objects:
            objects_speed[i] = [[0 for _ in range(ego_speed.shape[0] // 10 + 1)] for _ in range(2)]
            objects_range[i] = [[0 for _ in range(ego_speed.shape[0] // 10 + 1)] for _ in range(2)]
        ego_speed_res = []
        ego_speed_temp = []
        lane_offset_res = []
        for i, j in enumerate(ego_speed):
            if math.isnan(j):
                if i == 0:
                    temp = 1
                    while math.isnan(ego_speed[temp]):
                        temp += 1
                    ego_speed_res.append(ego_speed[temp])
                    continue
                ego_speed_res.append(ego_speed_res[i - 1])
            else:
                ego_speed_res.append(j)
        # print(len(ego_speed_res))
        for i in range(8):
            for m in range(0, ego_speed.shape[0], 10):
                if sms_object[i][m] in objects:
                    objects_speed[sms_object[i][m]][0][m // 10] = x_velocity[i][m] + ego_speed_res[m]
                    objects_speed[sms_object[i][m]][1][m // 10] = y_velocity[i][m]
                    objects_range[sms_object[i][m]][0][m // 10] = x_range[i][m]
                    objects_range[sms_object[i][m]][1][m // 10] = y_range[i][m]
        for i in range(0, ego_speed.shape[0], 10):
            ego_speed_temp.append(ego_speed_res[i])
        for i in range(0, lane_offset.shape[0], 10):
            lane_offset_res.append(lane_offset[i])
        # print(objects_speed.get(140.0, 0))
        res = {
            'ego_speed': ego_speed_temp, 'objects_speed': objects_speed,
            'objects_range': objects_range, 'entity': objects, 'lane_offsets': lane_offset_res
        }
        return res

    @staticmethod
    def draw_graph_speed_x(speed_list):
        count = 0
        length_temp = 0
        for key, value in speed_list.items():
            count += 1
            length_temp = value
            if count:
                break
        x = np.array([i for i in range(len(length_temp[0]))])
        # ego = np.array([0 for _ in range(len(length_temp))])
        plt.ylabel('speed: m/s')
        plt.xlabel('time: s')
        # plt.plot(x, ego)
        for i in speed_list:
            y = np.array(speed_list.get(i)[0])
            plt.plot(x, y)
        plt.show()

    @staticmethod
    def draw_graph_time(any_list, name, y_label):
        y = np.array(any_list)
        x = np.array([i for i in range(len(any_list))])
        plt.ylabel(y_label)
        plt.xlabel('time: s')
        plt.plot(x, y, color='black', label=name, marker='o')
        plt.show()

    @staticmethod
    def draw_filter(any_list, name, y_label):
        svd = 2 * (len(any_list) // 2) - 1
        tnp_smooth = savgol_filter(any_list, svd, 5)
        x = np.array([i for i in range(len(any_list))])
        # plt.plot(x, tnp_smooth*0.5, label=y_label+'拟合', color='red')
        plt.plot(x, tnp_smooth, label=name, color='black')
        plt.ylabel(y_label)
        plt.xlabel('time: s')
        plt.show()
        return tnp_smooth

    @staticmethod
    def draw_graph_speed_y(speed_list):
        count = 0
        length_temp = 0
        for key, value in speed_list.items():
            count += 1
            length_temp = value
            if count:
                break
        x = np.array([i for i in range(len(length_temp[1]))])
        # ego = np.array([0 for _ in range(len(length_temp))])
        plt.ylabel('speed: m/s')
        plt.xlabel('time: s')
        # plt.plot(x, ego)
        for i in speed_list:
            y = np.array(speed_list.get(i)[1])
            plt.plot(x, y)
        plt.show()

    @staticmethod
    def speed_or_range_len(sr_list):
        count = 0
        for i in sr_list:
            if i != 0:
                count += 1
        return count

    def draw_graph_dis(self, ego_speed_list, target_list):
        ego_x_dis = list()
        ego_x_dis.append(ego_speed_list[0])
        for i in range(1, len(ego_speed_list)):
            ego_x_dis.append(ego_x_dis[-1] + ego_speed_list[i])
        for j in target_list:
            range_y = target_list[j][1]
            range_x = target_list[j][0]
            # speed_x = target_list['speed_x']
            # speed_y = target_list['speed_y']
            if self.speed_or_range_len(range_y) <= 2:
                continue
            left = 0
            while range_x[left] == 0:
                left += 1
            right = left
            while right < len(range_x) and range_x[right] != 0:
                right += 1
            right -= 1
            target_x_dis = list()
            target_y_dis = list()
            time_list = [i for i in range(left, right + 1)]
            target_x_dis.append(range_x[left] + ego_x_dis[left])
            target_y_dis.append(range_y[left])
            for i in range(1, right - left + 1):
                # target_x_dis.append(target_x_dis[-1] + speed_x[time_list[i]])
                target_x_dis.append(ego_x_dis[time_list[i]] + range_x[time_list[i]])
                # target_y_dis.append(target_y_dis[-1] + speed_y[time_list[i]])
                target_y_dis.append(range_y[time_list[i]])
            # self.obj_pos[j] = {'x': target_x_dis[0], 'y': target_y_dis[0]}
            plt.plot(target_x_dis, target_y_dis, color='red', label=str(j), marker='*')
        y_ego = [0 for _ in range(len(ego_speed_list))]
        # time_list = [i for i in range(len(ego_speed_list))]
        plt.plot(ego_x_dis, y_ego, color='blue', label='ego', marker='o')
        plt.xlabel('x: m')
        plt.ylabel('y: m')
        # plt.title(title)
        plt.show()

    @staticmethod
    def draw_lane_offset(lane_offsets):
        ti = [_ for _ in range(len(lane_offsets))]
        plt.plot(ti, lane_offsets, color='black')
        plt.xlabel('time: s')
        plt.ylabel('lane offset: cm')
        plt.show()

    @staticmethod
    def create_entities(root, name):
        entity = root.createElement('Object')
        entity.setAttribute('name', name)
        vehicle_node = root.createElement('Vehicle')
        vehicle_node.setAttribute('category', 'car')
        vehicle_node.setAttribute('name', 'Audi_A3_2009_black')
        pdl = root.createElement('ParameterDeclaration')
        vehicle_node.appendChild(pdl)
        performance_node = root.createElement('Performance')
        performance_node.setAttribute('mass', '1560')
        performance_node.setAttribute('maxDeceleration', '9.5')
        performance_node.setAttribute('maxSpeed', '80')
        vehicle_node.appendChild(performance_node)
        bb_node = root.createElement('BoundingBox')
        center_node = root.createElement('Center')
        dimension_node = root.createElement('Dimension')
        center_node.setAttribute('x', '1.317')
        center_node.setAttribute('y', '0')
        center_node.setAttribute('z', '0.7115')
        dimension_node.setAttribute('height', '1.423')
        dimension_node.setAttribute('length', '4.3')
        dimension_node.setAttribute('width', '1.776')
        bb_node.appendChild(center_node)
        bb_node.appendChild(dimension_node)
        vehicle_node.appendChild(bb_node)
        axles_node = root.createElement('Axles')
        front_node = root.createElement('Front')
        rear_node = root.createElement('Rear')
        front_node.setAttribute('maxSteering', '0.48')
        front_node.setAttribute('positionX', '2.591')
        front_node.setAttribute('positionZ', '0.3205')
        front_node.setAttribute('trackWidth', '1.576')
        front_node.setAttribute('wheelDiameter', '0.641')
        axles_node.appendChild(front_node)
        rear_node.setAttribute('maxSteering', '0')
        rear_node.setAttribute('positionX', '0')
        rear_node.setAttribute('positionZ', '0.3205')
        rear_node.setAttribute('trackWidth', '1.576')
        rear_node.setAttribute('wheelDiameter', '0.641')
        axles_node.appendChild(rear_node)
        vehicle_node.appendChild(axles_node)
        properties_node = root.createElement('Properties')
        property_node = root.createElement('Property')
        property_node.setAttribute('name', 'control')
        if name == 'Ego':
            property_node.setAttribute('value', 'external')
        else:
            property_node.setAttribute('value', 'internal')
        properties_node.appendChild(property_node)
        vehicle_node.appendChild(properties_node)
        entity.appendChild(vehicle_node)
        controller = root.createElement('Controller')
        driver_node = root.createElement('Driver')
        driver_node.setAttribute('name', 'DefaultDriver')
        description_node = root.createElement('Description')
        description_node.setAttribute('age', '28')
        description_node.setAttribute('eyeDistance', '0.065')
        description_node.setAttribute('height', '1.8')
        description_node.setAttribute('sex', 'male')
        description_node.setAttribute('weight', '60')
        description_node.appendChild(root.createElement('Properties'))
        driver_node.appendChild(description_node)
        controller.appendChild(driver_node)
        entity.appendChild(controller)
        '''catalog_reference = root.createElement('CatalogReference')
        catalog_reference.setAttribute('catalogName', 'VechicleCatalog')
        if name == 'Ego':
            catalog_reference.setAttribute('entryName', 'AudiA3_red_147kW')
        else:
            catalog_reference.setAttribute('entryName', 'AudiA3_blue_147kW')
        entity.appendChild(catalog_reference)
        controller = root.createElement('Controller')
        catalog_reference = root.createElement('CatalogReference')
        catalog_reference.setAttribute('catalogName', 'DriverCatalog')
        catalog_reference.setAttribute('entryName', 'DefaultDriver')
        controller.appendChild(catalog_reference)
        entity.appendChild(controller)'''
        return entity

    @staticmethod
    def create_header(root, description, revmajor='1', revminor='0', author='renhe xu'):
        file_header = root.createElement('FileHeader')
        file_header.setAttribute('revMajor', revmajor)
        file_header.setAttribute('revMinor', revminor)
        file_header.setAttribute('date', datetime.datetime.now().isoformat())
        file_header.setAttribute('description', 'Scenario - cut in scenario')
        file_header.setAttribute('author', author)
        return file_header

    @staticmethod
    def create_parameter(root):
        par_declare = root.createElement('ParameterDeclaration')
        return par_declare

    @staticmethod
    def create_catalogs(root, **kwargs):
        catalogs = root.createElement('Catalogs')
        catalog_mapping = ['VehicleCatalog', 'DriverCatalog', 'PedestrianCatalog', 'PedestrianControllerCatalog',
                           'MiscObjectCatalog', 'EnvironmentCatalog', 'ManeuverCatalog', 'TrajectoryCatalog',
                           'RouteCatalog']
        catalog_map = {'VehicleCatalog': 'Vehicles', 'DriverCatalog': 'driverCfg.xml', 'MiscObjectCatalog': 'Objects'}
        for catalog in catalog_mapping:
            temp_catalog = root.createElement(catalog)
            directory = root.createElement('Directory')
            if kwargs.get(catalog, 0):
                directory.setAttribute('path', 'Distros/Current/Config/Players/' + kwargs.get(catalog))
            elif catalog_map.get(catalog, 0):
                directory.setAttribute('path', 'Distros/Current/Config/Players/' + catalog_map.get(catalog))
            else:
                directory.setAttribute('path', '')
            temp_catalog.appendChild(directory)
            catalogs.appendChild(temp_catalog)
        return catalogs

    @staticmethod
    def create_road_network(root, xodr, osgb):
        # '../Runtime/Tools/RodDistro_6710_Rod4.6.0/DefaultProject/Odr/city_quick_3.xodr'
        # '../Runtime/Tools/RodDistro_6710_Rod4.6.0/DefaultProject/Database/city_quick_3.opt.osgb'
        road_network = root.createElement('RoadNetwork')
        logics = root.createElement('Logics')
        logics.setAttribute('filepath', xodr)
        scen_graph = root.createElement('SceneGraph')
        scen_graph.setAttribute('filepath', osgb)
        road_network.appendChild(logics)
        road_network.appendChild(scen_graph)
        return road_network

    @staticmethod
    def create_init_story(root, init_pos, init_speed, name):
        private_node = root.createElement('Private')
        private_node.setAttribute('object', name)
        # init speed
        action_node = root.createElement('Action')
        longi_node =root.createElement('Longitudinal')
        speed_node = root.createElement('Speed')
        dynamics_node = root.createElement('Dynamics')
        dynamics_node.setAttribute('shape', 'step')
        target_node = root.createElement('Target')
        abs_node = root.createElement('Absolute')
        abs_node.setAttribute('value', str(init_speed))
        target_node.appendChild(abs_node)
        speed_node.appendChild(target_node)
        speed_node.appendChild(dynamics_node)
        longi_node.appendChild(speed_node)
        action_node.appendChild(longi_node)
        # init speed
        action_node1 = root.createElement('Action')
        pos_node = root.createElement('Position')
        world_node = root.createElement('World')
        world_node.setAttribute('x', init_pos[0])
        world_node.setAttribute('y', init_pos[1])
        world_node.setAttribute('z', init_pos[2])
        world_node.setAttribute('h', init_pos[3])
        world_node.setAttribute('p', init_pos[4])
        world_node.setAttribute('r', init_pos[5])
        pos_node.appendChild(world_node)
        action_node1.appendChild(pos_node)
        private_node.appendChild(action_node)
        private_node.appendChild(action_node1)
        return private_node

    @staticmethod
    def create_action_node(root, param):
        action_node = root.createElement('Action')
        private_node = root.createElement('Private')
        direction_node = root.createElement(param['direction'])
        speed_node = root.createElement('Speed')
        dynamics_node = root.createElement('Dynamics')
        dynamics_node.setAttribute('shape', 'linear')
        dynamics_node.setAttribute('time', '1')
        target_node = root.createElement('Target')
        abs_node = root.createElement('Absolute')
        abs_node.setAttribute('value', str(param['value']))
        target_node.appendChild(abs_node)
        speed_node.appendChild(dynamics_node)
        speed_node.appendChild(target_node)
        direction_node.appendChild(speed_node)
        private_node.appendChild(direction_node)
        action_node.appendChild(private_node)
        return action_node

    @staticmethod
    def create_conditions_node(root, param):
        conditions_node = root.createElement(param['root_name'])
        start_node = None
        if param['root_name'] == 'Conditions':
            start_node = root.createElement('Start')
        condition_group_node = root.createElement('ConditionGroup')
        condition_node = root.createElement('Condition')
        condition_node.setAttribute('name', param['owner'] + 'Condition' + str(param['value']))
        condition_node.setAttribute('delay', '0')
        condition_node.setAttribute('edge', 'rising')
        byvalue_node = root.createElement('ByValue')
        simutime_node = root.createElement('SimulationTime')
        simutime_node.setAttribute('value', str(param['value']))
        simutime_node.setAttribute('rule', param['rule'])
        byvalue_node.appendChild(simutime_node)
        condition_node.appendChild(byvalue_node)
        condition_group_node.appendChild(condition_node)
        if param['root_name'] == 'Conditions':
            start_node.appendChild(condition_group_node)
            conditions_node.appendChild(start_node)
        else:
            conditions_node.appendChild(condition_group_node)
        return conditions_node

    def create_event(self, root, idx, owner, speed):
        event_node = root.createElement('Event')
        event_node.setAttribute('name', owner + 'Event' + str(idx + 1))
        event_node.setAttribute('priority', 'overwrite')
        ac_node = self.create_action_node(root, {'direction': 'Longitudinal', 'value': speed})
        ac_node.setAttribute('name', owner + 'Action' + str(idx + 1))
        event_node.appendChild(ac_node)
        cd_node = self.create_conditions_node(root, {'value': str(idx + 1), 'rule': 'greater_than', 'owner': owner,
                                                     'root_name': 'StartConditions'})
        event_node.appendChild(cd_node)
        return event_node
