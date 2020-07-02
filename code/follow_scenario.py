from code.general_processing import GeneralFunc
from xml.dom.minidom import Document
from lxml import html


class FollowScenario:
    def create_follow_scenario(self, data_dic, gf, path, xodr_path, osgb_path):
        """
        生成场景文件
        :param data_dic: 预读取的数据
        :param gf: GeneralFunc实例
        :param path: 输出路径
        :param xodr_path: 地图文件
        :param osgb_path: 地图数据库文件
        :return: None
        """
        same_lane = list()
        for idx, val in data_dic['objects_range'].items():
            if self.filter_y_range(val[1]):
                same_lane.append(idx)
        obj, min_val = 0.0, 1000
        for idx in same_lane:
            temp = self.follow_objects(data_dic['objects_range'][idx][0])
            if min_val > temp:
                min_val = temp
                obj = idx
        entity = ['Ego', ]
        x_speed = data_dic['objects_speed'][obj][0]
        for i, j in enumerate(x_speed):
            if j == 0:
                x_speed[i] = x_speed[i - 1] + 0.2
        filter_x_list = {'Ego': gf.draw_filter(data_dic['ego_speed'], '', '')}
        init_speed = {'Ego': filter_x_list['Ego'][0]}
        init_position = {'Ego': ['1.4', '-7.2', '0', '0', '0', '0']}
        if obj != 0.0:
            entity.append('Target' + str(obj))
            filter_x_list['Target' + str(obj)] = gf.draw_filter(x_speed, '', '')
            init_x, init_y, sx = gf.cal_init(filter_x_list['Ego'], filter_x_list['Target' + str(obj)],
                                             data_dic['objects_range'][obj][0], data_dic['objects_range'][obj][1])
            init_position['Target' + str(obj)] = [str(1.4 + 40), str(-7.2 + init_y), '0', '0', '0', '0']
            init_speed['Target' + str(obj)] = sx
        kwargs = dict()
        kwargs['out_path'] = path
        kwargs['GF'] = gf
        kwargs['xodr'] = xodr_path
        kwargs['osgb'] = osgb_path
        kwargs['entity'] = entity
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
            for index, val in enumerate(value):
                event_node = GF.create_event(doc, index, key, val)
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
    def follow_objects(x_range_list):
        temp = 0
        length = len(x_range_list)
        while temp < length and x_range_list[temp] == 0:
            temp += 1
        if temp >= length:
            return 1000
        return x_range_list[temp]

    @staticmethod
    def filter_y_range(y_range_list):
        for i in y_range_list:
            if i < -2.2 or i > 2.2:
                return False
        return True


if __name__ == '__main__':
    lc = FollowScenario()
    lane_changer = GeneralFunc()
    data_dic = lane_changer.parse_data('../events_data/events_data/event_s3_2281_fulldata.csv')
    # lane_changer.draw_lane_offset(data_dic['lane_offsets'])
    # lane_changer.draw_filter(data_dic['lane_offsets'], 'ego', 'lane offsets : cm')
    path = 'follow_example.xosc'
    xodr_path = '../Runtime/Tools/RodDistro_6710_Rod4.6.0/DefaultProject/Odr/city_quick_3.xodr'
    osgb_path = '../Runtime/Tools/RodDistro_6710_Rod4.6.0/DefaultProject/Database/city_quick_3.opt.osgb'
    lc.create_follow_scenario(data_dic, lane_changer, path, xodr_path, osgb_path)
    # create_cut_in_scenario(**param)


