# encoding=utf-8
from intervals import Interval
from general_processing import GeneralFunc
from xml.dom.minidom import Document
from lxml import html

# init ego pos: x:1.4 y: -7.2
DIRECTION = 5.3


class CutInScenario:
    def __init__(self):
        """line_map = dict()
        line_map['left'] = (-1.8, -5.4)
        line_map['mid'] = (-1.8, 1.8)
        line_map['right'] = (1.8, 5.4)"""
        self.lane_map = {
            'pre_left': Interval((-9.0, -5.4)),
            'left': Interval((-5.4, -1.8)),
            'mid': Interval((-1.8, 1.8)),
            'right': Interval((1.8, 5.4)),
            'after_right': Interval((5.4, 9.0))
        }
        self.test = Interval((-1, 1))
        self.ego_pos_init = 'mid'
        self.left_lane = self.lane_map['left']
        self.mid_lane = self.lane_map['mid']
        self.right_lane = self.lane_map['right']
        self.obj_pos = dict()

    def define_ego_pos(self, objects_range, objects_speed):
        left, right = 0.0, 0.0
        for i in objects_range:
            if objects_range[i][1][0] in self.lane_map['left']:
                left = i
                break
        for i in objects_range:
            if objects_range[i][1][0] in self.lane_map['right']:
                right = i
                break
        if right == 0.0:
            self.ego_pos_init = 'right'
            self.left_lane = self.lane_map['pre_left']
            self.mid_lane = self.lane_map['left']
            self.right_lane = self.lane_map['mid']
            return
        if left == 0.0:
            self.ego_pos_init = 'left'
            self.left_lane = self.lane_map['mid']
            self.mid_lane = self.lane_map['right']
            self.right_lane = self.lane_map['after_right']
            return
        for j in objects_speed[left][0]:
            if j < 0:
                self.ego_pos_init = 'left'
                self.left_lane = self.lane_map['mid']
                self.mid_lane = self.lane_map['right']
                self.right_lane = self.lane_map['after_right']
                return

    def objects_filter_lane(self, objects_range):
        object_range_x = dict()
        object_range_y = dict()
        map_lane = ('left', 'mid', 'right')
        for i in map_lane:
            object_range_x[i] = dict()
            object_range_y[i] = dict()
        for i in objects_range:
            temp = 0
            length = len(objects_range[i][1])
            while temp < length and objects_range[i][1][temp] == 0:
                temp += 1
            if temp == length:
                continue
            if objects_range[i][1][temp] in self.left_lane:
                object_range_y['left'][i] = objects_range[i][1]
                object_range_x['left'][i] = objects_range[i][0]
            elif objects_range[i][1][temp] in self.mid_lane:
                object_range_y['mid'][i] = objects_range[i][1]
                object_range_x['mid'][i] = objects_range[i][0]
            elif objects_range[i][1][temp] in self.right_lane:
                object_range_y['right'][i] = objects_range[i][1]
                object_range_x['right'][i] = objects_range[i][0]
        return [object_range_x, object_range_y]

    @staticmethod
    def find_liner_min(l, index, tag):
        length = len(l)
        if tag == 'up':
            current, nex = index, index + 1
            while nex < length:
                if l[nex] == 0:
                    return current
                if l[nex] >= l[current]:
                    return current
                nex, current = nex + 1, current + 1
            return nex
        else:
            current, nex = index, index - 1
            while nex >= 0:
                if l[nex] == 0:
                    return current
                if l[nex] >= l[current]:
                    return current
                nex, current = nex - 1, current - 1
            return 0

    @staticmethod
    def find_liner_max(l, index, tag):
        length = len(l)
        if tag == 'up':
            current, nex = index, index + 1
            while nex < length:
                if l[nex] == 0:
                    return current
                if l[nex] <= l[current]:
                    return current
                nex, current = nex + 1, current + 1
            return nex
        else:
            current, nex = index, index - 1
            while nex >= 0:
                if l[nex] == 0:
                    return current
                if l[nex] <= l[current]:
                    return current
                nex, current = nex - 1, current - 1
            return 0

    def lane_change(self, object_range_y):
        # lane width = 3.6m
        lane_changer = dict()
        lane_mapping = {'left': self.left_lane, 'mid': self.mid_lane, 'right': self.right_lane}
        for lane in object_range_y:
            for obj in object_range_y[lane]:
                for t, range_y in enumerate(object_range_y[lane][obj]):
                    if range_y == 0:
                        continue
                    if range_y not in lane_mapping[lane]:
                        if range_y < object_range_y[lane][obj][t - 1]:
                            left = self.find_liner_max(object_range_y[lane][obj], t, 'down')
                            right = self.find_liner_min(object_range_y[lane][obj], t, 'up')
                            # lane_changer[obj] = lane_changer.get(obj, []).append((left, right))
                        else:
                            left = self.find_liner_min(object_range_y[lane][obj], t, 'down')
                            right = self.find_liner_max(object_range_y[lane][obj], t, 'up')
                        if obj in lane_changer:
                            lane_changer[obj].append((left, right))
                        else:
                            lane_changer[obj] = [(left, right)]
                        break
        print(lane_changer)
        return lane_changer

    @staticmethod
    def target_filter(objects_range):
        # target_left_hand = list()
        target_right_hand = list()
        res = dict()
        for obj in objects_range:
            i = 0
            while objects_range[obj][1][i] == 0:
                i += 1
            left = i
            length = len(objects_range[obj][1])
            while i < length and objects_range[obj][1][i] != 0:
                i += 1
            right = i
            res[obj] = objects_range[obj][1][left: right]
        for obj in res:
            for i, j in enumerate(res[obj]):
                if abs(j) > 2.2:
                    for index, range_y in enumerate(res[obj]):
                        if abs(range_y) < 1.2:
                            if index > i:
                                target_right_hand.append(obj)
                                '''for count in range(1, 4):
                                    if abs(res[obj][1][index + count]) > 1.2:
                                        target_right_hand.pop()
                                        break'''
                                break
                    break
        return target_right_hand

    @staticmethod
    def find_action(y_range_list):
        i = 0
        while y_range_list[i] == 0:
            i += 1
        left_temp = i
        length = len(y_range_list)
        while i < length and y_range_list[i] != 0:
            i += 1
            if i < length and y_range_list[i] == 0:
                for j in range(i + 1, length):
                    if y_range_list[j] != 0:
                        i = j
                        break
        res = y_range_list[left_temp: i]
        tag = True
        if res[0] < 0:
            direction = 1
        else:
            direction = -1
        left, right = 0, 0
        min_val = 1000
        for i, j in enumerate(res):
            if tag and abs(j) < 2.2:
                left = i
                tag = not tag
            if not tag and abs(j) > 2.2:
                tag = not tag
            if abs(j) < min_val:
                min_val = abs(j)
                right = i
        return left - 1, right, direction

    @staticmethod
    def create_cut_in_action_node(root, param):
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

    def create_cut_in_scenario(self, gf, path, xodr_path, osgb_path, data_dic):
        lane_changer = self.target_filter(data_dic['objects_range'])
        actions = dict()
        kwargs = dict()
        # print(lane_changer)
        for i in lane_changer:
            action = self.find_action(data_dic['objects_range'][i][1])
            actions['Target' + str(i)] = action
        kwargs['out_path'] = path
        kwargs['GF'] = gf
        kwargs['xodr'] = xodr_path
        kwargs['osgb'] = osgb_path
        entity = ['Ego', ]
        x_speed_list = {'Ego': data_dic['ego_speed']}
        y_speed_list = dict()
        x_range_list = dict()
        y_range_list = dict()
        for i in lane_changer:
            entity.append('Target' + str(i))
            # x_speed_list['Target' + str(i)] = cutin.del_tail_zero(data_dic['objects_speed'][i][0])
            x_speed_list['Target' + str(i)] = data_dic['objects_speed'][i][0]
            y_speed_list['Target' + str(i)] = data_dic['objects_speed'][i][1]
            x_range_list['Target' + str(i)] = data_dic['objects_range'][i][0]
            y_range_list['Target' + str(i)] = data_dic['objects_range'][i][1]
        init_position = {'Ego': ['1.4', '-7.2', '0', '0', '0', '0']}
        init_speed = {'Ego': x_speed_list['Ego'][0]}
        filter_x_list = {'Ego': gf.draw_filter(x_speed_list['Ego'], '', '')}
        for i in entity:
            if i == 'Ego':
                continue
            init_x, init_y, sx = gf.cal_init(x_speed_list['Ego'], x_speed_list[i], x_range_list[i], y_range_list[i])
            init_position[i] = [str(1.4 + init_x), str(-7.2 + init_y), '0', '0', '0', '0']
            init_speed[i] = sx
            gf.draw_graph_time(x_speed_list[i], i, 'speed: m/s')
            filter_x_list[i] = gf.draw_filter(x_speed_list[i], i, 'speed: m/s')
        kwargs['entity'] = entity
        kwargs['event'] = actions
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
        story_node.setAttribute('name', 'CutInStory')
        story_node.setAttribute('owner', '')
        act_node = doc.createElement('Act')
        act_node.setAttribute('name', 'CutInAct')
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
                ac_node = self.create_cut_in_action_node(doc, {'start': left, 'end': right, 'change_dir': change,
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

    @staticmethod
    def validate(xml_path, xsd_path):
        etree = html.etree
        xmlschema_doc = etree.parse(xsd_path)
        xmlschema = etree.XMLSchema(xmlschema_doc)

        xml_doc = etree.parse(xml_path)
        result = xmlschema.validate(xml_doc)

        if not result:
            print(xmlschema.error_log)
        else:
            print('Congratulations! Schema validation has been passed!')

    @staticmethod
    def del_tail_zero(speed_list):
        temp = list()
        for idx, val in enumerate(speed_list):
            if val == 0:
                temp.append(speed_list[idx - 1])
            else:
                temp.append(val)
        return temp


if __name__ == '__main__':
    cutin = CutInScenario()
    GF = GeneralFunc()
    data = GF.parse_data('event_3.csv')
    for i, val in data['objects_speed'].items():

    out_path = 'cutin_example.xosc'
    xodr = '../Runtime/Tools/RodDistro_6710_Rod4.6.0/DefaultProject/Odr/city_quick_3.xodr'
    osgb = '../Runtime/Tools/RodDistro_6710_Rod4.6.0/DefaultProject/Database/city_quick_3.opt.osgb'
    cutin.create_cut_in_scenario(GF, out_path, xodr, osgb, data)
    cutin.validate('cutin_example.xosc', 'OpenSCENARIO_v0.9.1.xsd')
    # print(actions)
    # create_cut_in_scenario(**param)
