import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# 定义地图大小
map_size = 1000

# 定义灾点类  
class DisasterPoint:  
    def __init__(self, coordinates, severity):  
        self.coordinates = coordinates  # 灾点坐标
        self.severe = severity  # 灾点严重程度
        self.found = 0  # 被多少机器人救援
        self.exist = True  # 灾点是否存在
# 目标点
# 2-5个普通灾点，1个严重灾点，随机生成
num_targets = np.random.randint(2, 5)
target_points = [DisasterPoint((np.random.randint(0, map_size//5)*5, np.random.randint(0, map_size//5)*5), severity) for severity in [False] * num_targets + [True]]

# 搜寻机器人起点：4个从别处（边界）加入增援，3个从中央控制基地出发
search_starts = [(0, np.random.randint(0, map_size//5)*5),
                 (np.random.randint(0, map_size//5)*5, 0),
                 (map_size, np.random.randint(0, map_size//5)*5),
                 (np.random.randint(0, map_size//5)*5, map_size),
                 (0,0),(0,150),(150,0)]

# 机器人运动函数（速度为5）
def move_robot(start, end):
    path = []
    current = start
    while current != end:
        path.append(current)
        next_x = current[0] + 5 * np.sign(end[0] - current[0])
        next_y = current[1] + 5 * np.sign(end[1] - current[1])
        current = (next_x, next_y)
    path.append(end)
    return path

# 巡逻机器人在地图中往返游荡，不具有搜救功能，但却是唯一拥有GPS定位的机器人（所以拥有全部灾区的坐标信息），作用是给搜救机器人汇报灾点
# 巡逻机器人路径
patrol_starts = [(300, 700), (700, 700), (700, 300),(300, 300)]
patrol_path = []
for i in range(len(patrol_starts)):
    next_point = patrol_starts[(i + 1) % len(patrol_starts)]
    patrol_path.extend(move_robot(patrol_starts[i], next_point))
patrol_path.extend(move_robot(patrol_starts[0], patrol_starts[0]))  # 循环四边形路径

# 更新搜寻机器人路线
def update_search_path(start, targets, patrol_path, search_range=50, communication_range1=200, communication_range2=100, severe_rescue_range=200):
    patrol_index = 0
    path = []
    current = start
    right = np.random.choice([-5, 5])
    up = np.random.choice([-5, 5])

    while True:
        path.append(current)
        patrol_position = patrol_path[patrol_index % len(patrol_path)]
        
        # 寻路方式1：通过与巡逻机器人通信（通信范围200），获得最近的灾区相对坐标，如果需要救援，直接前往
        if np.sqrt((current[0] - patrol_position[0])**2 + (current[1] - patrol_position[1])**2) < communication_range1:
            # 获取最近的灾点相对坐标，如果小于3个机器人在救援，就前往（普通灾点）；严重灾点直接前往
            # existing_targets = [t for t in targets if t.exist] 
            # if  existing_targets:
            closest_target = min(targets, key=lambda t: np.sqrt((current[0] - t.coordinates[0])**2 + (current[1] - t.coordinates[1])**2))
            if (((closest_target.found < 3) and (closest_target.severe == False)) or (closest_target.severe == True)):
             x1, y1 = closest_target.coordinates  # 从DisasterPoint实例中获取坐标 
             path.extend(move_robot(current, closest_target.coordinates))
             path.append(target.coordinates) # 到达灾点
             closest_target.found +=1   # 标记灾点被救援+1
             for _ in range(120):  # 模拟停留120个时间步（假设救援时间为120，就需要回基地维修）
              path.append(closest_target.coordinates)
             #target.exist = False # 另一种想法：该灾点救援完成，灾点消失（没有采用）
             patrol_index = 0
             path.extend(move_robot((x1,y1), (0,0))) # 救援结束回中央控制基地
             return path # 下一轮的机器人出发
         
        # 寻路方式2：自行寻找灾点（能看见的范围50），看见了且正在救援的机器人小于3（普通灾点），就前往；严重灾点直接前往
        for target in targets:
         #if target.exist:
            if np.sqrt((current[0] - target.coordinates[0])**2 + (current[1] - target.coordinates[1])**2) < search_range:
                if ((target.found < 3 and target.severe == False) or (target.severe == True)):
                 x2, y2 = target.coordinates  # 从DisasterPoint实例中获取坐标 
                 path.extend(move_robot(current, target.coordinates))
                 path.append(target.coordinates) # 到达灾点
                 target.found +=1   # 标记灾点被救援+1
                 for _ in range(120):  # 模拟停留120个时间步
                  path.append(target.coordinates)
                 #target.exist = False
                 patrol_index = 0
                 path.extend(move_robot((x2,y2), (0,0)))
                 return path
            
        # 寻路方式3：发现严重灾点救援信号（范围200），需要更多机器人救援，立即前往
        for target in targets:
         #if target.exist:
           if np.sqrt((current[0] - target.coordinates[0])**2 + (current[1] - target.coordinates[1])**2) < severe_rescue_range:
              if (target.found > 0) and (target.severe == True):
                 x3, y3 = target.coordinates  # 从DisasterPoint实例中获取坐标 
                 path.extend(move_robot(current, target.coordinates))
                 path.append(target.coordinates) # 到达灾点
                 target.found +=1   # 标记灾点被救援+1
                 for _ in range(250):  # 模拟停留250个时间步（更久）
                  path.append(target.coordinates)
                 #target.exist = False
                 patrol_index = 0
                 path.extend(move_robot((x3,y3), (0,0)))
                 return path
              
        # 寻路方式4：通过与中央控制基地(0,0)通信（通信范围100），获得最远的灾区相对坐标，如果需要救援，直接前往
        if np.sqrt((current[0] - 0)**2 + (current[1] - 0)**2) < communication_range2:
            # 获取最远的灾点相对坐标，如果小于3个机器人在救援，就前往（普通灾点）；严重灾点直接前往
            farthest_target = max(targets, key=lambda t: np.sqrt((current[0] - t.coordinates[0])**2 + (current[1] - t.coordinates[1])**2))
            if (((farthest_target.found < 3) and (farthest_target.severe == False)) or (farthest_target.severe == True)):
             x4, y4 = farthest_target.coordinates  # 从DisasterPoint实例中获取坐标 
             path.extend(move_robot(current, farthest_target.coordinates))
             path.append(target.coordinates) # 到达灾点
             farthest_target.found +=1   # 标记灾点被救援+1
             for _ in range(120):  # 模拟停留120个时间步（假设救援时间为120，就需要回基地维修）
              path.append(farthest_target.coordinates)
             #target.exist = False # 另一种想法：该灾点救援完成，灾点消失（没有采用）
             patrol_index = 0
             path.extend(move_robot((x4,y4), (0,0))) # 救援结束回中央控制基地
             return path # 下一轮的机器人出发

        # 默认出发方式：弹性斜线往返，等待通信信号或救援信号
        next_position = (current[0] + right, current[1] + up)
        if next_position[1] > map_size:
            up = -5
            next_position = (current[0] + right, current[1] + up)
        if next_position[0] > map_size:
            right = -5
            next_position = (current[0] + right, current[1] + up)

        if next_position[1] <= 0:
            up = 5
            next_position = (current[0] + right, current[1] + up)
        if next_position[0] <= 0:
            right = 5
            next_position = (current[0] + right, current[1] + up)

        current = next_position
        patrol_index += 1

# 生成所有路径
search_paths = []
patrol_index = 0

# 初始化界面
fig, ax = plt.subplots()
ax.set_xlim(0, map_size)
ax.set_ylim(0, map_size)

# 实时更新动画
def update(num):
    global patrol_index
    ax.clear()
    ax.set_xlim(0, map_size)
    ax.set_ylim(0, map_size)
    
    # 绘制普通灾点坐标，橙色，大小为5  
    for target in target_points:  
     if (target.severe == False):
      ax.plot(target.coordinates[0], target.coordinates[1], 'o', color='orange', markersize=5)  
    # 绘制严重灾点坐标，红色，大小为8
     if (target.severe == True):
      ax.plot(target.coordinates[0], target.coordinates[1], 'o', color='red', markersize=8)  

    # 更新巡逻机器人位置
    patrol_pos = patrol_path[patrol_index % len(patrol_path)]
    ax.plot(patrol_pos[0], patrol_pos[1], '^', color='green', markersize=3)
    patrol_index += 1

    # 更新搜索机器人位置
    for i in range(len(search_starts)):
        start = search_starts[i]
        if len(search_paths) < len(search_starts):
            path_t= update_search_path(start, target_points, patrol_path)
            # print(path_t)
            search_paths.append(path_t)
        path = search_paths[i]
        idx = num % len(path)
        ax.plot(path[idx][0], path[idx][1], 'o', color='black', markersize=2)

# 创建动画
ani = animation.FuncAnimation(fig, update, frames=1000, interval=50)
plt.show()
