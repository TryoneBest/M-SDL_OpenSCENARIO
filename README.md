# M-SDL_OpenSCENARIO
## 通用方法 generral_processing
主要是一些处理数据的通用方法，适用于不同场景的数据处理，比如从雷达数据里提取所有车辆的横向
、纵向相对速度。
- parse_data(file_path)：
输入要处理的雷达文件的路径，根据目标id和其他列数据的对应关系提取出所有本车(ego)的速度、其他
所有车的横向及纵向的相对速度、横向及纵向的相对距离。以上数据都做过处理，原本时间间隔
为100ms，为减少数据量，改为1s取一组数据
- draw_graph_speed_x(speed_list)：根据输入的速度列表画对应的x轴速度图，将所有车的速度整合
在一张图上主要是为了研究各个场景目标车的明显特征
- draw_graph_speed_y(speed_list)：与上类似，对应的y轴速度图
- speed_or_range_len(sr_list)：判断列表里的数据长度，过滤掉一些明显不可能的数据
- draw_graph_dis(ego_speed_list, target_list)：根据本车的速度和其他所有车的速度列表计算
x轴和y轴的绝对位移图，也是为了研究特征
- create_*+：生成格式要求的节点，具体看格式样例文件