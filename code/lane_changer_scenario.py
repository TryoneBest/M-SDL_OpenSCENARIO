from code.general_processing import GeneralFunc
from xml.dom.minidom import Document
from lxml import html


class LaneChangerScenario:
    @staticmethod
    def lane_changer(lane_offsets):
        max_val = 0
        index = 0
        for i, j in enumerate(lane_offsets):
            if j > max_val:
                max_val = j
                index = i
        if lane_offsets[index] < 1000:
            return False
        positive = 0
        for i in range(index + 1):
            if lane_offsets[i] > 0:
                positive += 1
        pos_left = positive / (index + 1)
        positive = 0
        for i in range(index + 1, len(lane_offsets)):
            if lane_offsets[i] > 0:
                positive += 1
        pos_right = positive / (len(lane_offsets) + 1 - index)
        if (pos_left < 0.2 and pos_right < 0.2) or (pos_left > 0.8 and pos_right > 0.8):
            return False
        return True

    @staticmethod
    def find_lane_cars(y_range_list, range):
        for i in y_range_list:
            if i < range[0] or i > range[1]:
                return False
        return True

    @staticmethod
    def create_lane_change_action_node(root, param):
        action_node = root.createElement('Action')
        private_node = root.createElement('Private')
        direction_node = root.createElement('Lateral')
        lane_change_node = root.createElement('LaneChange')
        dynamics_node = root.createElement('Dynamics')
        dynamics_node.setAttribute('shape', 'sinusoidal')
        dynamics_node.setAttribute('time', str(param['end'] - param['start']))
        target_node = root.createElement('Target')
        abs_node = root.createElement('Relative')
        abs_node.setAttribute('object', param['obj'])
        abs_node.setAttribute('value', str(param['change_dir']))
        target_node.appendChild(abs_node)
        lane_change_node.appendChild(dynamics_node)
        lane_change_node.appendChild(target_node)
        direction_node.appendChild(lane_change_node)
        private_node.appendChild(direction_node)
        action_node.appendChild(private_node)
        return action_node

    def create_lane_changer_scenario(self, data, gf, out_path, xodr, osgb):
        """
        生成场景文件的主要函数
        :param data: 预读取的数据
        :param gf: GeneralFunc类实例
        :param out_path: 输出路径
        :param xodr: 地图文件
        :param osgb: 地图数据库文件
        :return:
        """
        if not self.lane_changer(data['lane_offsets']):
            return
        filter_lane_offset = gf.draw_filter(data['lane_offsets'], 'ego', 'lane offsets: cm') # 滤波找峰值确定变道事件的区间
        temp, temp1, min_val, max_val = 0, 0, 1000, 0
        for i in range(len(filter_lane_offset)):
            if filter_lane_offset[i] < min_val:
                min_val = filter_lane_offset[i]
                temp = i
            if filter_lane_offset[i] > max_val:
                max_val = filter_lane_offset[i]
                temp1 = i
        left, right = min(temp, temp1), max(temp, temp1)
        if filter_lane_offset[left] < filter_lane_offset[right]: # 确定变道方向
            direction = -1
        else:
            direction = 1
        ego_lane = list()
        el_lane = list()
        if direction == 1: # 筛选符合条件的对象
            for idx, val in data['objects_range'].items():
                if self.find_lane_cars(val[1], (-1.8, 1.8)):
                    ego_lane.append(idx)
                if self.find_lane_cars(val[1], (1.8, 5.4)):
                    el_lane.append(idx)
        else:
            for idx, val in data['objects_range'].items():
                if self.find_lane_cars(val[1], (-1.8, 1.8)):
                    ego_lane.append(idx)
                if self.find_lane_cars(val[1], (-5.4, -1.8)):
                    el_lane.append(idx)
        ego_lane_target = 0.0
        ego_target_init_x, ego_target_init_y, ego_target_init_speed = 1000, 0, 0
        for i in ego_lane:
            x, y, s = gf.cal_init(data['ego_speed'], data['objects_speed'][i][0], data['objects_range'][i][0],
                                  data['objects_range'][i][1])
            if x < ego_target_init_x:
                ego_lane_target, ego_target_init_x, ego_target_init_speed, ego_target_init_y = i, x, s, y
        el_lane_target = 0.0
        el_target_init_x, el_target_init_y, el_target_init_speed = 1000, 0, 0
        for i in el_lane:
            x, y, s = gf.cal_init(data['ego_speed'], data['objects_speed'][i][0], data['objects_range'][i][0],
                                  data['objects_range'][i][1])
            if x < el_target_init_x:
                el_lane_target, el_target_init_x, el_target_init_speed, el_target_init_y = i, x, s, y
        kwargs = dict()
        entity = ['Ego', ]
        x_speed_list = {'Ego': data['ego_speed']}
        y_speed_list = dict()
        x_range_list = dict()
        y_range_list = dict()
        if ego_lane_target != 0.0:
            entity.append('Target' + str(ego_lane_target))
            x_speed_list['Target' + str(ego_lane_target)] = data['objects_speed'][ego_lane_target][0]
            y_speed_list['Target' + str(ego_lane_target)] = data['objects_speed'][ego_lane_target][1]
            x_range_list['Target' + str(ego_lane_target)] = data['objects_range'][ego_lane_target][0]
            y_range_list['Target' + str(ego_lane_target)] = data['objects_range'][ego_lane_target][1]
        if el_lane_target != 0.0:
            entity.append('Target' + str(el_lane_target))
            x_speed_list['Target' + str(el_lane_target)] = data['objects_speed'][el_lane_target][0]
            y_speed_list['Target' + str(el_lane_target)] = data['objects_speed'][el_lane_target][1]
            x_range_list['Target' + str(el_lane_target)] = data['objects_range'][el_lane_target][0]
            y_range_list['Target' + str(el_lane_target)] = data['objects_range'][el_lane_target][1]
        init_position = {'Ego': ['1.4', '-7.2', '0', '0', '0', '0']}
        init_speed = {'Ego': x_speed_list['Ego'][0],
                      'Target' + str(ego_lane_target): ego_target_init_speed,
                      'Target' + str(el_lane_target): el_target_init_speed}
        init_position['Target' + str(ego_lane_target)] = [str(1.4 + ego_target_init_x),
                                                          str(-7.2 + ego_target_init_y),
                                                          '0', '0', '0', '0']
        init_position['Target' + str(el_lane_target)] = [str(1.4 + el_target_init_x),
                                                         str(-7.2 + el_target_init_y),
                                                         '0', '0', '0', '0']
        filter_x_list = dict()
        if ego_lane_target != 0.0:
            filter_x_list['Target' + str(ego_lane_target)] = gf.draw_filter(data['objects_speed'][ego_lane_target][0],
                                                                            '', '')
        if el_lane_target != 0.0:
            filter_x_list['Target' + str(el_lane_target)] = gf.draw_filter(data['objects_speed'][el_lane_target][0], '',
                                                                           '')
        filter_x_list['Ego'] = gf.draw_filter(data['ego_speed'], '', '')
        kwargs['out_path'] = out_path
        kwargs['GF'] = gf
        kwargs['xodr'] = xodr
        kwargs['osgb'] = osgb
        kwargs['entity'] = entity
        kwargs['event'] = {'Ego': (left, right, direction)}
        kwargs['speed'] = filter_x_list
        kwargs['init_speed'] = init_speed
        kwargs['init_pos'] = init_position

        doc = Document()
        GF = kwargs['GF']

        # root node
        root = doc.createElement('OpenSCENARIO')
        doc.appendChild(root)

        # FileHeader
        header = GF.create_header(doc, 'cut in scenario')
        root.appendChild(header)

        # ParameterDeclaration
        pdcl = GF.create_parameter(doc)
        root.appendChild(pdcl)

        # Catalogs
        catalogs = GF.create_catalogs(doc)
        root.appendChild(catalogs)

        # RoadNetworks
        # '../Runtime/Tools/RodDistro_6710_Rod4.6.0/DefaultProject/Odr/city_quick_3.xodr'
        # '../Runtime/Tools/RodDistro_6710_Rod4.6.0/DefaultProject/Database/city_quick_3.opt.osgb'
        rnode = GF.create_road_network(doc, kwargs['xodr'], kwargs['osgb'])
        root.appendChild(rnode)

        # Entities
        entity_list = kwargs['entity']
        enode = doc.createElement('Entities')
        for e in entity_list:
            obj_node = GF.create_entities(doc, e)
            enode.appendChild(obj_node)
        root.appendChild(enode)

        # StoryBoard
        snode = doc.createElement('Storyboard')
        # Init
        init_node = doc.createElement('Init')
        actions_node = doc.createElement('Actions')
        for i in entity_list:
            pr_node = GF.create_init_story(doc, kwargs['init_pos'][i], kwargs['init_speed'][i], i)
            actions_node.appendChild(pr_node)
        init_node.appendChild(actions_node)
        snode.appendChild(init_node)
        # Story
        story_node = doc.createElement('Story')
        story_node.setAttribute('name', 'LaneChangeStory')
        story_node.setAttribute('owner', '')
        act_node = doc.createElement('Act')
        act_node.setAttribute('name', 'LaneChangeAct')
        for key, value in kwargs['speed'].items():
            # Sequence
            seq_node = doc.createElement('Sequence')
            seq_node.setAttribute('name', key + 'Sequence')
            seq_node.setAttribute('numberOfExecutions', '1')
            actors_node = doc.createElement('Actors')
            entity_node = doc.createElement('Entity')
            entity_node.setAttribute('name', key)
            actors_node.appendChild(entity_node)
            seq_node.appendChild(actors_node)
            maneuver_node = doc.createElement('Maneuver')
            maneuver_node.setAttribute('name', key + 'Maneuver')

            left, right, change = kwargs['event'].get(key, (-1, 0, 0))
            if left >= 0:
                for idx in range(0, left):
                    event_node = GF.create_event(doc, idx, key, value[idx])
                    maneuver_node.appendChild(event_node)
                event_node = doc.createElement('Event')
                event_node.setAttribute('name', 'LaneChanger' + str(change))
                event_node.setAttribute('priority', 'overwrite')
                ac_node = self.create_lane_change_action_node(doc, {'start': left, 'end': right, 'change_dir': change,
                                                                    'obj': key})
                ac_node.setAttribute('name', 'LaneChangeAction')
                event_node.appendChild(ac_node)
                scd_node = doc.createElement('StartConditions')
                cg_node = doc.createElement('ConditionGroup')
                cd_node = doc.createElement('Condition')
                cd_node.setAttribute('name', 'LaneChangeCondition')
                cd_node.setAttribute('delay', '0')
                cd_node.setAttribute('edge', 'rising')
                byvalue_node = doc.createElement('ByValue')
                simutime_node = doc.createElement('SimulationTime')
                simutime_node.setAttribute('value', str(left + 1))
                simutime_node.setAttribute('rule', 'greater_than')
                byvalue_node.appendChild(simutime_node)
                cd_node.appendChild(byvalue_node)
                cg_node.appendChild(cd_node)
                scd_node.appendChild(cg_node)
                event_node.appendChild(scd_node)
                maneuver_node.appendChild(event_node)
            for index, val in enumerate(value[right:]):
                event_node = GF.create_event(doc, index + right, key, val)
                maneuver_node.appendChild(event_node)

            seq_node.appendChild(maneuver_node)
            act_node.appendChild(seq_node)
            # Conditions Sequence
        conditions_node = GF.create_conditions_node(doc, {'value': '0', 'rule': 'greater_than', 'owner': '',
                                                          'root_name': 'Conditions'})
        act_node.appendChild(conditions_node)
        story_node.appendChild(act_node)
        snode.appendChild(story_node)

        end_condition_node = doc.createElement('EndConditions')
        snode.appendChild(end_condition_node)

        root.appendChild(snode)

        with open(kwargs['out_path'], 'w') as f:
            doc.writexml(f, indent="\n", addindent="\t", encoding='utf-8')


if __name__ == '__main__':
    lc = LaneChangerScenario()
    lane_changer = GeneralFunc()
    data_dic = lane_changer.parse_data('event_s3_2198_fulldata.csv')
    # lane_changer.draw_lane_offset(data_dic['lane_offsets'])
    # lane_changer.draw_filter(data_dic['lane_offsets'], 'ego', 'lane offsets : cm')
    path = 'lane_changer_example.xosc'
    xodr_path = '../Runtime/Tools/RodDistro_6710_Rod4.6.0/DefaultProject/Odr/city_quick_3.xodr'
    osgb_path = '../Runtime/Tools/RodDistro_6710_Rod4.6.0/DefaultProject/Database/city_quick_3.opt.osgb'
    lc.create_lane_changer_scenario(data_dic, lane_changer, path, xodr_path, osgb_path)
    # create_cut_in_scenario(**param)
