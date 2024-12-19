import pygame
import random
import tkinter as tk
from tkinter import messagebox, simpledialog
import sys
import time
import json
import operator  # 添加这行
import heapq  # 添加到文件顶部的import部分


# 初始化Pygame
pygame.init()
pygame.mixer.init()  # 初始化音频系统

# 屏幕尺寸
MAZE_SIZE = 800  # 迷宫区域大小
INFO_WIDTH = 200  # 信息区域宽度
WIDTH = MAZE_SIZE + INFO_WIDTH
HEIGHT = MAZE_SIZE
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Maze Game by dyh')

# 迷宫参数
cols = rows = 5  # 可以自由设置迷宫大小
cell_size = MAZE_SIZE // max(cols, rows)  # 根据迷宫大小自动计算单元格大小



# 加载缩放图片
try:
    task_door_image = pygame.image.load('task_door.png')
    small_task_image = pygame.image.load('small_task.png')
    big_task_image = pygame.image.load('big_task.png')
    lock_image = pygame.image.load('lock.png')
    open_image = pygame.image.load('open.png')
    bomb_image = pygame.image.load('bomb.png')  # 保存原始图片
    bomb_original = bomb_image  # 保存原始炸弹图片以供后续缩放
    # 统一使用cell_size的80%作为基准大小
    new_size = int(cell_size * 0.8)
    
    # 对所有图片进行统一缩放
    task_door_image = pygame.transform.scale(task_door_image, (new_size, new_size))
    small_task_image = pygame.transform.scale(small_task_image, (new_size, new_size))
    big_task_image = pygame.transform.scale(big_task_image, (new_size, new_size))
    lock_image = pygame.transform.scale(lock_image, (new_size, new_size))
    open_image = pygame.transform.scale(open_image, (new_size, new_size))
    bomb_image = pygame.transform.scale(bomb_image, (new_size, new_size))
    
    # 添加怪物图片加载
    monster_image = pygame.image.load('banli.png')  # 改为加载 .png 文件
    # 将怪物图片缩放到合适大小
    monster_image = pygame.transform.scale(monster_image, (new_size, new_size))
    
except pygame.error as e:
    print(f"Warning: Could not load image: {e}")
    task_door_image = None
    small_task_image = None
    big_task_image = None
    lock_image = None
    open_image = None
    bomb_image = None
    bomb_original = None
    monster_image = None 

# 在加载图片的try-except块后添加音效加载
try:
    enter_sound = pygame.mixer.Sound('enter.mp3')
    unacceptable_sound = pygame.mixer.Sound('unacceptable.mp3')
    coin_sound = pygame.mixer.Sound('coin.mp3')
    success_sound = pygame.mixer.Sound('success.mp3')
    failure_sound = pygame.mixer.Sound('failure.mp3')
    
    # 设置各个音效的音量
    enter_sound.set_volume(1.0)        # 100% 音量
    unacceptable_sound.set_volume(1.0) # 100% 音量
    coin_sound.set_volume(1.0)         # 100% 音量
    success_sound.set_volume(0.7)      # 70% 音量
    failure_sound.set_volume(0.1)      # 降低到 10% 音量

    # 加载并设置BGM
    pygame.mixer.music.load('bgm.mp3')  # BGM文件
    pygame.mixer.music.set_volume(0.3)  # 设置BGM音量为30%
except pygame.error as e:
    print(f"Warning: Could not load sound: {e}")
    enter_sound = None
    unacceptable_sound = None
    coin_sound = None
    success_sound = None
    failure_sound = None

# 初始化中文字体
try:
    GAME_FONT = pygame.font.SysFont('microsoftyaheimicrosoftyaheiui', 24)
except:
    try:
        GAME_FONT = pygame.font.SysFont('simsun', 24)
    except:
        GAME_FONT = pygame.font.SysFont('arial', 24)

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
ORANGE = (255, 165, 0)

# 全局变量
current_maze_type = "NORMAL"
normal_maze_grid = None
task_maze_grid = None
grid = None
player = None
task_doors = []  # 存储任务迷宫入口位置（原 blue_squares）
small_tasks = []  # 存储小任务位置
big_tasks = []  # 存储大任务位置
task_timer = None # 计时器
task_exit_pos = None  # 存储任务迷宫的出口位置
task_maze_order = []  # 记录进入任务迷宫的顺序
task_maze_grids = {}  # 存储每个入口点对应的任务迷宫
current_difficulty = "EASY"  # 默认难度
can_through_wall = False  # 是否可以穿墙
is_fog_active = True  # 是否启用迷雾效果
heart_positions = []  # 存储心形道具的位置
heart_image = None   # 心形道具的图片
DAMAGE_INTERVAL = 7000  # 扣血间隔（毫秒）
last_damage_time = 0    # 上次扣血时间
horns_start_time = 0   # 进入荆棘迷宫的时间
passing_door_positions = []  # 存储传送门位置
passing_door_image = None   # 传送门图片
TELEPORT_COOLDOWN = 1000   # 传送冷却时间(毫秒)
last_teleport_time = 0     # 上次传送时间

# 血条相关常量
MAX_HEALTH = 5  # 最大生命值
current_health = MAX_HEALTH  # 当前生命值

# 定义状态文本（使用英文作为备选）
MAZE_STATES = {
    "NORMAL": "Normal Maze",  # 如果中文无法显示就用英文
    "TASK": "Task Maze #{}",    # 任务迷宫显示编号
    "THORNS": "Thorns Maze"  # 添加新的迷宫类型
}

# 添加难度关的配置
DIFFICULTY_SETTINGS = {
    "EASY": 5,    # 10x10 迷宫
    "MEDIUM": 10,  # 15x15 迷宫
    "HARD": 15     # 20x20 迷宫
}

# 添加难度相关的常量
DIFFICULTY_CONFIGS = {
    "EASY": {
        "stars": 2,
        "small_tasks": 3,
        "big_tasks": 1
    },
    "MEDIUM": {
        "stars": 3,
        "small_tasks": 6,
        "big_tasks": 2
    },
    "HARD": {
        "stars": 4,
        "small_tasks": 9,
        "big_tasks": 3
    }
}

# 在全局变量区域添加通关记录字典
COMPLETION_RECORDS = {
    "EASY": 0,
    "MEDIUM": 0,
    "HARD": 0
}

# 在全局变量区域添加
current_user = None  # 当前登录用户

# 添加用户相关的函数
def load_users():
    """从文件加载用户数据"""
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}  # 如果文件不存在，返回空字典

def save_users(users):
    """保存用户数据到文件"""
    with open('users.json', 'w') as f:
        json.dump(users, f)

def show_login_dialog():
    """显示登录对话框"""
    global current_user
    
    root = tk.Tk()
    root.title("迷宫游戏 - 登录")
    root.geometry("400x300")
    
    # 使用柔和的米色作为背景
    bg_color = '#F5F5F5'  # ���灰白色
    text_color = '#2C3E50'  # 深蓝灰色
    button_bg = '#E8E8E8'  # 浅灰色
    button_fg = '#2C3E50'  # 深蓝灰色
    entry_bg = 'white'  # 纯白色
    title_color = '#34495E'  # 深青灰色
    
    root.configure(bg=bg_color)
    
    users = load_users()
    result = {'username': None}
    
    # 创建主框架
    main_frame = tk.Frame(root, bg=bg_color)
    main_frame.place(relx=0.5, rely=0.5, anchor='center')
    
    # 标题标签
    title_label = tk.Label(main_frame, 
                          text="迷宫探险",
                          font=('微软雅黑', 24, 'bold'),
                          fg=title_color,
                          bg=bg_color)
    title_label.pack(pady=20)
    
    # 用户名输入框架
    entry_frame = tk.Frame(main_frame, bg=bg_color)
    entry_frame.pack(pady=10)
    
    username_label = tk.Label(entry_frame,
                            text="用户名:",
                            font=('微软雅黑', 12),
                            fg=text_color,
                            bg=bg_color)
    username_label.pack(side=tk.LEFT, padx=5)
    
    username_entry = tk.Entry(entry_frame,
                            font=('微软雅黑', 12),
                            width=15,
                            bg=entry_bg)
    username_entry.pack(side=tk.LEFT, padx=5)
    
    # 按钮框架
    button_frame = tk.Frame(main_frame, bg=bg_color)
    button_frame.pack(pady=20)
    
    def create_button(parent, text, command):
        return tk.Button(parent,
                        text=text,
                        font=('微软雅黑', 12),
                        width=8,
                        command=command,
                        bg=button_bg,
                        fg=button_fg,
                        relief='flat',  # 扁平化按钮
                        activebackground='#D0D0D0',  # 鼠标悬停时的颜色
                        activeforeground=button_fg)
    
    def do_login():
        username = username_entry.get()
        if not username:
            messagebox.showerror("错误", "请输入用户名！")
            return
        if username not in users:
            messagebox.showerror("错误", "用户名不存在，请先注册！")
            return
        result['username'] = username
        root.quit()
    
    def do_register():
        username = username_entry.get()
        if not username:
            messagebox.showerror("错误", "请输入用户名！")
            return
        if username in users:
            messagebox.showerror("错误", "用户�����存在！")
            return
        users[username] = {
            "EASY": 0,
            "MEDIUM": 0,
            "HARD": 0
        }
        save_users(users)
        messagebox.showinfo("成功", "注册成功！")
        result['username'] = username
        root.quit()
    
    # 创建登录和注册按钮
    login_btn = create_button(button_frame, "登录", do_login)
    login_btn.pack(side=tk.LEFT, padx=10)
    
    register_btn = create_button(button_frame, "注册", do_register)
    register_btn.pack(side=tk.LEFT, padx=10)
    
    # 将窗口居中显示
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    try:
        root.mainloop()
    except:
        pass
    
    username = result['username']
    
    try:
        root.destroy()
    except:
        pass
    
    return username

# 修改保存记录相关的函数
def save_records():
    """保存通关记录到文件"""
    if not current_user:
        return
    
    users = load_users()
    if current_user in users:
        users[current_user].update(COMPLETION_RECORDS)
        save_users(users)

def load_records():
    """从文件加载通关���录"""
    global COMPLETION_RECORDS
    if not current_user:
        return
    
    users = load_users()
    if current_user in users:
        COMPLETION_RECORDS = users[current_user].copy()

# 生成两个随机蓝色方块
def generate_task_doors():
    """根据难度生成对应数量的任务迷宫入口"""
    global task_doors
    task_doors = []
    
    # 获取当前难度的配置
    current_difficulty = get_current_difficulty()
    num_doors = DIFFICULTY_CONFIGS[current_difficulty]["stars"]
    
    # 获可用位置（除起点和终点）
    available_positions = []
    for x in range(cols):
        for y in range(rows):
            if (x, y) != (0, 0) and (x, y) != (cols-1, rows-1):
                available_positions.append((x, y))
    
    # 随机选择位置
    if len(available_positions) >= num_doors:
        selected_positions = random.sample(available_positions, num_doors)
        task_doors = selected_positions

# 迷宫单元格类
class Cell:
    def __init__(self, x, y): # 初始化方法
        self.x = x
        self.y = y
        self.walls = [True, True, True, True]  # 上右下左
        self.visited = False
        
    def draw(self, screen):
        # 计算实际绘制位置（居��显示）
        offset_x = (MAZE_SIZE - cols * cell_size) // 2
        offset_y = (MAZE_SIZE - rows * cell_size) // 2
        x = offset_x + self.x * cell_size
        y = offset_y + self.y * cell_size
        
        if self.walls[0]:  # 上
            pygame.draw.line(screen, WHITE, (x, y), (x + cell_size, y), 5)
        if self.walls[1]:  # 右
            pygame.draw.line(screen, WHITE, (x + cell_size, y), (x + cell_size, y + cell_size), 5)
        if self.walls[2]:  # 下
            pygame.draw.line(screen, WHITE, (x, y + cell_size), (x + cell_size, y + cell_size), 5)
        if self.walls[3]:  # 左
            pygame.draw.line(screen, WHITE, (x, y), (x, y + cell_size), 5)

# 创建网格
grid = [[Cell(x, y) for y in range(rows)] for x in range(cols)]

# 检查当前单元格未访问邻居
def check_neighbors(cell):
    neighbors = []  # 存储未访问的邻居
    x, y = cell.x, cell.y
    # 检查四个方向的邻居
    if y > 0 and not grid[x][y - 1].visited:  # 上
        neighbors.append(grid[x][y - 1])
    if x < cols - 1 and not grid[x + 1][y].visited:  # 右
        neighbors.append(grid[x + 1][y])
    if y < rows - 1 and not grid[x][y + 1].visited:  # 下
        neighbors.append(grid[x][y + 1])
    if x > 0 and not grid[x - 1][y].visited:  # 左
        neighbors.append(grid[x - 1][y])
    return neighbors

# 移除墙壁
def remove_walls(current, next):
    dx = current.x - next.x
    dy = current.y - next.y
    # 根据相对位置移除墙
    if dx == 1:  # 下一个在左边
        current.walls[3] = False
        next.walls[1] = False
    elif dx == -1:  # 下一个在右边
        current.walls[1] = False
        next.walls[3] = False
    if dy == 1:  # 下一个在上面
        current.walls[0] = False
        next.walls[2] = False
    elif dy == -1:  # 下一个在下面
        current.walls[2] = False
        next.walls[0] = False

# 迷宫生成算法
def generate_maze(maze_grid=None):
    """生成迷宫
    Args:
        maze_grid: 可选的迷宫网格，如果不提供则使用全局的grid
    """
    global grid
    
    # 确定要使用的网格
    target_grid = maze_grid if maze_grid is not None else grid
    
    # 初始化访问记录
    visited = [[False] * rows for _ in range(cols)]
    stack = [(0, 0)]
    visited[0][0] = True
    
    while stack:
        current = stack[-1]
        x, y = current
        
        # 获取未访问的相邻单元格
        neighbors = []
        if y > 0 and not visited[x][y-1]:  # 上
            neighbors.append((x, y-1, 0, 2))
        if x < cols-1 and not visited[x+1][y]:  # 右
            neighbors.append((x+1, y, 1, 3))
        if y < rows-1 and not visited[x][y+1]:  # 下
            neighbors.append((x, y+1, 2, 0))
        if x > 0 and not visited[x-1][y]:  # 左
            neighbors.append((x-1, y, 3, 1))
        
        if neighbors:
            # 随机选择��个相邻单元格
            next_x, next_y, wall, opposite_wall = random.choice(neighbors)
            # 移除当前单元格和选中单元格之间的墙
            target_grid[x][y].walls[wall] = False
            target_grid[next_x][next_y].walls[opposite_wall] = False
            # 标���为已访问并加入栈
            visited[next_x][next_y] = True
            stack.append((next_x, next_y))
        else:
            # 如果没有未访问的相邻单元格���回溯
            stack.pop()
    

# 绘制出
def draw_exit(screen):
    """绘制出口"""
    offset_x = (MAZE_SIZE - cols * cell_size) // 2
    offset_y = (MAZE_SIZE - rows * cell_size) // 2
    
    if current_maze_type == "NORMAL":
        # 普通迷宫的出口在右下角
        x = offset_x + (cols - 1) * cell_size
        y = offset_y + (rows - 1) * cell_size
        
        # 检查是否完成有�����务迷宫
        if check_all_task_mazes_completed():
            if open_image:
                # 计算居中位置
                img_x = x + (cell_size - open_image.get_width()) // 2
                img_y = y + (cell_size - open_image.get_height()) // 2
                screen.blit(open_image, (img_x, img_y))
            else:
                pygame.draw.rect(screen, GREEN, (x, y, cell_size, cell_size))
        else:
            if lock_image:
                # ��算居中位置
                img_x = x + (cell_size - lock_image.get_width()) // 2
                img_y = y + (cell_size - lock_image.get_height()) // 2
                screen.blit(lock_image, (img_x, img_y))
            else:
                pygame.draw.rect(screen, RED, (x, y, cell_size, cell_size))
    elif current_maze_type == "TASK":
        # 任务迷宫的出��
        x = offset_x + task_exit_pos[0] * cell_size
        y = offset_y + task_exit_pos[1] * cell_size
        
        # 检查任务是否完成
        if check_task_completion():
            if open_image:
                # 计算居中位置
                img_x = x + (cell_size - open_image.get_width()) // 2
                img_y = y + (cell_size - open_image.get_height()) // 2
                screen.blit(open_image, (img_x, img_y))
            else:
                pygame.draw.rect(screen, GREEN, (x, y, cell_size, cell_size))
        else:
            if lock_image:
                # 计算居中位置
                img_x = x + (cell_size - lock_image.get_width()) // 2
                img_y = y + (cell_size - lock_image.get_height()) // 2
                screen.blit(lock_image, (img_x, img_y))
    elif current_maze_type == "THORNS":
        # 绘制荆棘迷宫出口
        if thorns_exit_pos:
            x = offset_x + thorns_exit_pos[0] * cell_size + (cell_size - open_image.get_width()) // 2
            y = offset_y + thorns_exit_pos[1] * cell_size + (cell_size - open_image.get_height()) // 2
            if open_image:
                screen.blit(open_image, (x, y))
            else:
                pygame.draw.rect(screen, GREEN, 
                               (offset_x + thorns_exit_pos[0] * cell_size,
                                offset_y + thorns_exit_pos[1] * cell_size,
                                cell_size, cell_size))

# 玩家类
class Player:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.image_right = pygame.image.load('player.png')
        self.image_left = pygame.transform.flip(self.image_right, True, False)
        original_width, original_height = self.image_right.get_size()
        aspect_ratio = original_height / original_width
        new_height = int(cell_size * 0.8)  # 根据新的cell_size计算
        new_width = int(new_height / aspect_ratio)
        self.image_right = pygame.transform.scale(self.image_right, (new_width, new_height))
        self.image_left = pygame.transform.scale(self.image_left, (new_width, new_height))
        self.image_width = new_width
        self.image_height = new_height
        self.facing_right = True
        self.normal_maze_pos = (0, 0)
        self.entry_point = None

    def move(self, direction):
        """移动玩家"""
        new_x, new_y = self.x, self.y
        wall_index = {"UP": 0, "RIGHT": 1, "DOWN": 2, "LEFT": 3}[direction]
        
        # 检查是否可以移动
        if can_through_wall or not grid[self.x][self.y].walls[wall_index]:
            if direction == "UP":
                new_y -= 1
            elif direction == "RIGHT":
                new_x += 1
                self.facing_right = True
            elif direction == "DOWN":
                new_y += 1
            elif direction == "LEFT":
                new_x -= 1
                self.facing_right = False
            
            # 检查新位置是否在迷宫范围内
            if 0 <= new_x < cols and 0 <= new_y < rows:
                self.x = new_x
                self.y = new_y
                return True
        return False

    def draw(self, screen):
        # 计算实际绘制位置（居中显示）
        offset_x = (MAZE_SIZE - cols * cell_size) // 2
        offset_y = (MAZE_SIZE - rows * cell_size) // 2
        x = offset_x + self.x * cell_size + (cell_size - self.image_width) // 2
        y = offset_y + self.y * cell_size + (cell_size - self.image_height) // 2
        # 根据朝向选择使用哪个图像
        screen.blit(self.image_right if self.facing_right else self.image_left, (x, y))

# 显示第一次到达终点信息
def show_success(screen):
    """显示成功信息并更新记录"""
    # 更新当前难度的通关记录
    COMPLETION_RECORDS[current_difficulty] += 1
    save_records()  # 保存记录到文件
    
    font = pygame.font.SysFont('Arial', 50)
    text = font.render('SUCCESS!', True, GREEN)
    screen.blit(text, (WIDTH // 2 - 100, HEIGHT // 2 - 25))
    pygame.display.update()
    pygame.time.delay(2000)

def switch_to_task_maze():
    """切换到任务迷宫"""
    global grid, current_maze_type, task_maze_grid, player, task_doors
    global task_exit_pos, bomb_positions, bomb_image, task_maze_grids, task_maze_order
    global is_fog_active, cell_size, bomb_original, monster_image, heart_image, endless_door_pos, endless_door_image
    
    # 保存玩家进入点
    entry_point = (player.x, player.y)
    player.entry_point = entry_point
    
    # 如果这个入口点还没有对应的任务迷宫
    if entry_point not in task_maze_order:
        task_maze_order.append(entry_point)
        
        # 生成新的任务迷宫
        task_maze_grid = [[Cell(x, y) for y in range(rows)] for x in range(cols)]
        generate_maze(task_maze_grid)
        
        # 随机选择出口位置（在边缘）
        edge_positions = []
        for x in range(cols):
            edge_positions.extend([(x, 0), (x, rows-1)])
        for y in range(1, rows-1):
            edge_positions.extend([(0, y), (cols-1, y)])
        edge_positions.remove((0, 0))  # 移除入口位置
        
        task_exit_pos = random.choice(edge_positions)
        task_maze_grids[entry_point] = (task_maze_grid, task_exit_pos)
        
        # 在EASY模式下生成endless_door位置
        if current_difficulty == "EASY":
            generate_endless_door_position()
    else:
        # 使用已存在的任务迷宫
        task_maze_grid, task_exit_pos = task_maze_grids[entry_point]
    
    # 切换到任务迷宫
    grid = task_maze_grid
    current_maze_type = "TASK"
    
    # 重新计算cell_size并调整图片大小
    if current_difficulty == "MEDIUM" and bomb_original:
        new_size = int(cell_size * 0.8)
        bomb_image = pygame.transform.scale(bomb_original, (new_size, new_size))
    
    # 重置迷雾效果
    is_fog_active = False
    
    # 生成任务
    generate_task_positions()
    
    # 在MEDIUM难度下生成炸弹
    if current_difficulty == "MEDIUM" and GAME_SETTINGS['enable_bombs']:
        generate_bomb_positions()
    
    # 在函数末尾添加，在HARD难度下初始化怪物和红心
    if current_difficulty == "HARD":
        try:
            if GAME_SETTINGS['enable_monster']:
                if monster_image is None:

                    monster_image = pygame.image.load('banli.png')
                    new_size = int(cell_size * 0.8)
                    monster_image = pygame.transform.scale(monster_image, (new_size, new_size))
                   
                init_monster()
                
            
            if GAME_SETTINGS['enable_heart']:
                if heart_image is None:
                    
                    heart_original = pygame.image.load('heart.png')
                    new_size = int(cell_size * 0.6)
                    heart_image = pygame.transform.scale(heart_original, (new_size, new_size))
                    
                init_heart()
               
        except pygame.error as e:
            
            monster_image = None
            heart_image = None

def generate_task_maze():
    global grid
    # 确保所有墙壁封闭的
    for x in range(cols):
        for y in range(rows):
            grid[x][y].walls = [True, True, True, True]
            grid[x][y].visited = False
    
    stack = []
    current = grid[0][0]
    current.visited = True
    
    # 使用不同的随机种生成新迷宫
    random.seed()  # 使用系统时间作为新的随机种子
    
    while True:
        neighbors = check_neighbors(current)
        if neighbors:
            # 增加向右和向下的权重，使迷宫更倾向于这些方向
            weights = []
            for neighbor in neighbors:
                if neighbor.x > current.x or neighbor.y > current.y:
                    weights.append(2)  # 向右或向下��������更
                else:
                    weights.append(1)
            next_cell = random.choices(neighbors, weights=weights)[0]
            next_cell.visited = True
            stack.append(current)
            remove_walls(current, next_cell)
            current = next_cell
        elif stack:
            current = stack.pop()
        else:
            break
    
    # 重置visited属性
    for x in range(cols):
        for y in range(rows):
            grid[x][y].visited = False

def return_to_normal_maze():
    """返回普通迷宫"""
    global grid, current_maze_type, player, is_fog_active, task_doors
    
    # 重置迷雾效果
    is_fog_active = False
    
    # 恢复原迷宫
    grid = normal_maze_grid
    current_maze_type = "NORMAL"
    
    # 从task_doors中移除当前入口点
    if player.entry_point and player.entry_point in task_doors:
        task_doors.remove(player.entry_point)
    
    # 玩家传送回入口位置
    if player.entry_point:
        player.x, player.y = player.entry_point

# 添加示提示息的函数
def show_message(screen, message, color=WHITE):
    font = pygame.font.SysFont('Arial', 36)
    text = font.render(message, True, color)
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    
    # 创建个半透明的背景
    background = pygame.Surface((text_rect.width + 20, text_rect.height + 20))
    background.fill(BLACK)
    background.set_alpha(200)
    background_rect = background.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    
    # 绘制背景和文本
    screen.blit(background, background_rect)
    screen.blit(text, text_rect)
    pygame.display.update()
    pygame.time.delay(2000)  # 显示2秒

# 添加显示消息框函
def show_popup_message(message):
    """显示消息框"""
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    messagebox.showinfo("提示", message)
    root.destroy()  # 销毁临时窗口

class Task:
    def __init__(self, x, y, is_big=False):
        self.x = x
        self.y = y
        self.is_big = is_big
        self.completed = False

    def generate_math_question(self):
        # 生成随机四则运算题
        operators = {
            operator.add: '+',
            operator.sub: '-',
            operator.mul: '*',
            operator.truediv: '/'
        }
        op = random.choice(list(operators.keys()))
        if op == operator.truediv:
            # 确保除法结果为��数
            b = random.randint(1, 10)
            a = b * random.randint(1, 10)
        else:
            a = random.randint(1, 20)
            b = random.randint(1, 20)
        
        result = op(a, b)
        question = f"{a} {operators[op]} {b}"
        return question, result

def generate_task_positions():
    global small_tasks, big_tasks
    # 清现有任务
    small_tasks.clear()
    big_tasks.clear()
    
    # 获可用位置（除起点和出口）
    available_positions = []
    for x in range(cols):
        for y in range(rows):
            if (x, y) != (0, 0) and (x, y) != task_exit_pos:
                available_positions.append((x, y))
    
    # 随机选择位置
    total_tasks = DIFFICULTY_CONFIGS[get_current_difficulty()]["small_tasks"] + DIFFICULTY_CONFIGS[get_current_difficulty()]["big_tasks"]
    if len(available_positions) >= total_tasks:
        selected_positions = random.sample(available_positions, total_tasks)
        
        # 创建小任务
        for i in range(DIFFICULTY_CONFIGS[get_current_difficulty()]["small_tasks"]):
            small_tasks.append(Task(selected_positions[i][0], selected_positions[i][1]))
        
        # 创建大任务
        for i in range(DIFFICULTY_CONFIGS[get_current_difficulty()]["big_tasks"]):
            pos_index = DIFFICULTY_CONFIGS[get_current_difficulty()]["small_tasks"] + i
            big_tasks.append(Task(selected_positions[pos_index][0], 
                                selected_positions[pos_index][1], True))

def show_math_task():
    """显示数学任务"""
    global current_health
    
    # 生成数学问题
    question, correct_answer = Task(0, 0).generate_math_question()
    
    # 创建一个临时的根窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    try:
        # 显示问题对话框
        answer = simpledialog.askfloat("数学题", f"{question} = ?", parent=root)
        
        # 处理用户响应
        if answer is None:  # 用户点击取消
            return False
        
        # 检查答案
        if abs(answer - correct_answer) < 0.01:  # 允许小的误差
            messagebox.showinfo("正确", "回答正确！")
            return True
        else:
            messagebox.showinfo("错误", f"正确答案是: {correct_answer}")
            current_health -= 1  # 扣除生命值
            if current_health <= 0:
                messagebox.showinfo("游戏结束", "生命值耗尽！")
                return None  # 表示生命值耗尽
            return False
    finally:
        # 确保窗口被销毁
        try:
            root.destroy()
        except:
            pass

def show_reaction_task():
    """显示反应测试任务"""
    root = tk.Tk()
    root.title("反应测试")
    root.geometry("300x200")
    
    result = {'success': False}
    timer = {'start': None}
    
    def handle_click():
        if timer['start'] is None:
            timer['start'] = time.time()
            button.config(text="再次点击！")
            label.config(text="在第5秒再次点击按钮")
        else:
            end_time = time.time()
            time_diff = end_time - timer['start']
            if 4 <= time_diff <= 6:
                if success_sound:
                    success_sound.play()
                result['success'] = True
                messagebox.showinfo("结果", f"成功！你和第5��的时间差仅为：{time_diff-5:.3f}秒")
            else:
                if failure_sound:
                    failure_sound.play()
                messagebox.showinfo("结果", f"失败！你和第5秒的时间差为：{time_diff-5:.3f}秒\n需要在1秒范围��")
            root.quit()
    
    label = tk.Label(root, text="点击按钮后，你需在第5秒再次点击按钮\n若时间差在1秒内算通过", font=('Arial', 12))
    label.pack(pady=20)
    
    button = tk.Button(root, text="点开始", command=handle_click)
    button.pack(pady=10)
    
    root.mainloop()
    
    success = result['success']
    root.destroy()
    
    return success

def check_task_completion():
    """检查任务完成������况"""
    # 获取当前难度的�����
    current_difficulty = get_current_difficulty()
    required_small_tasks = DIFFICULTY_CONFIGS[current_difficulty]["small_tasks"]
    required_big_tasks = DIFFICULTY_CONFIGS[current_difficulty]["big_tasks"]
    
    # 检查小任务完成数量
    small_tasks_completed = sum(1 for task in small_tasks if task.completed)
    # 检查大任务完成数量
    big_tasks_completed = sum(1 for task in big_tasks if task.completed)
    
    return small_tasks_completed >= required_small_tasks or big_tasks_completed >= required_big_tasks

def show_task_progress():
    """显示任�����������进度"""
    current_difficulty = get_current_difficulty()
    required_small_tasks = DIFFICULTY_CONFIGS[current_difficulty]["small_tasks"]
    required_big_tasks = DIFFICULTY_CONFIGS[current_difficulty]["big_tasks"]
    
    small_tasks_completed = sum(1 for task in small_tasks if task.completed)
    big_tasks_completed = sum(1 for task in big_tasks if task.completed)
    
    if big_tasks_completed >= required_big_tasks or small_tasks_completed >= required_small_tasks:
        show_popup_message("You can exit now!")
    else:
        small_remaining = required_small_tasks - small_tasks_completed
        big_remaining = required_big_tasks - big_tasks_completed
        show_popup_message(f"Need to complete {small_remaining} small tasks\n"
                         f"or {big_remaining} big tasks to exit!")

def handle_task_collision(x, y, last_position):
    """处理任务碰撞"""
    global current_maze_type, current_health, heart_positions, thorn_positions, clear_potion_pos
    
    # 检查是否在荆棘迷宫中到达出口
    if current_maze_type == "THORNS" and (x, y) == thorns_exit_pos:
        return_from_thorns_maze()
        return False
    
    # 在荆棘迷宫中检查心形道具碰撞
    if current_maze_type == "THORNS" and (x, y) in heart_positions:
        if current_health < MAX_HEALTH:
            current_health = min(MAX_HEALTH, current_health + 1)
            if success_sound:
                success_sound.play()
        heart_positions.remove((x, y))
        return False
    
    # 检查清除药水碰撞
    if current_maze_type == "THORNS" and (x, y) == clear_potion_pos:
        thorn_positions.clear()  # 清除所有荆棘
        clear_potion_pos = None  # 移除药水
        if success_sound:
            success_sound.play()
        show_popup_message("所有荆棘已清除！")
        return False
    
    # 检查荆棘碰撞
    if current_maze_type == "THORNS" and (x, y) in thorn_positions:
        if check_thorn_collision():
            if current_health <= 0:
                show_game_over()
                return True
        return False
    
    # 检查是否在任务迷宫中到达出口
    if current_maze_type == "TASK" and (x, y) == task_exit_pos:
        if check_task_completion():  # 修改这里，使用正确的函数名
            current_maze_type = "NORMAL"
            grid = normal_maze_grid
            if current_task_door:
                player.x, player.y = current_task_door
            return True
        else:
            show_incomplete_task_message()
            player.x, player.y = last_position
            return False
    
    # 检查是否碰到任务
    if current_maze_type == "TASK":
        # 检查小任务
        for task in small_tasks:
            if not task.completed and (x, y) == (task.x, task.y):
                return handle_small_task(task)
        
        # 检查大任务
        for task in big_tasks:
            if not task.completed and (x, y) == (task.x, task.y):
                return handle_big_task(task)
    
    # 检查是否在荆棘迷宫中碰到荆棘
    if current_maze_type == "THORNS" and (x, y) in thorn_positions:
        # 检查荆棘碰撞
        if check_thorn_collision():
            # 如果生命值耗尽
            if current_health <= 0:
                show_game_over()
                return True
            # 否则退回上一个位置
            player.x, player.y = last_position
            return False
    
    return False

def draw_tasks():
    """绘制任务方块和炸弹"""
    offset_x = (MAZE_SIZE - cols * cell_size) // 2
    offset_y = (MAZE_SIZE - rows * cell_size) // 2
    
    # 绘制小任务
    for task in small_tasks:
        if not task.completed:
            x = offset_x + task.x * cell_size + (cell_size - small_task_image.get_width()) // 2
            y = offset_y + task.y * cell_size + (cell_size - small_task_image.get_height()) // 2
            if small_task_image:
                screen.blit(small_task_image, (x, y))
            else:
                pygame.draw.rect(screen, ORANGE, (offset_x + task.x * cell_size, 
                                                offset_y + task.y * cell_size, 
                                                cell_size, cell_size))
    
    # 绘制所有大任务
    for task in big_tasks:
        if not task.completed:
            x = offset_x + task.x * cell_size + (cell_size - big_task_image.get_width()) // 2
            y = offset_y + task.y * cell_size + (cell_size - big_task_image.get_height()) // 2
            if big_task_image:
                screen.blit(big_task_image, (x, y))
            else:
                pygame.draw.rect(screen, RED, (offset_x + task.x * cell_size,
                                             offset_y + task.y * cell_size,
                                             cell_size, cell_size))
    
    # 在EASY模式下绘制endless_door
    if current_difficulty == "EASY" and endless_door_pos and endless_door_image:
        x = offset_x + endless_door_pos[0] * cell_size + (cell_size - endless_door_image.get_width()) // 2
        y = offset_y + endless_door_pos[1] * cell_size + (cell_size - endless_door_image.get_height()) // 2
        screen.blit(endless_door_image, (x, y))
    
    # 绘制炸弹
    if current_difficulty == "MEDIUM" and GAME_SETTINGS['enable_bombs']:
        for bomb_pos in bomb_positions:
            x = offset_x + bomb_pos[0] * cell_size + (cell_size - bomb_image.get_width()) // 2
            y = offset_y + bomb_pos[1] * cell_size + (cell_size - bomb_image.get_height()) // 2
            if bomb_image:
                screen.blit(bomb_image, (x, y))


def check_all_task_mazes_completed():
    """检查是否完成了所有任务迷宫"""
    # 检查是否��有未访问蓝色方块
    return len(task_doors) == 0

def show_remaining_tasks():
    """示剩余的任务迷宫数"""
    if unacceptable_sound and len(task_doors) > 0:
        unacceptable_sound.play()
    remaining = len(task_doors)
    if remaining > 0:
        show_popup_message(f"还有{remaining}个任务迷宫需要完成！")
    else:
        show_popup_message("所有任务迷宫已完成，恭喜通关！")

def draw_status_panel():
    """绘制状态面板"""
    # 绘制分隔线
    pygame.draw.line(screen, WHITE, (MAZE_SIZE, 0), (MAZE_SIZE, HEIGHT), 2)
    
    # 使用默认字体
    font = pygame.font.SysFont('arial', 24)
    
    # 获取当前难度配置
    current_difficulty = get_current_difficulty()
    required_stars = DIFFICULTY_CONFIGS[current_difficulty]["stars"]
    required_small_tasks = DIFFICULTY_CONFIGS[current_difficulty]["small_tasks"]
    required_big_tasks = DIFFICULTY_CONFIGS[current_difficulty]["big_tasks"]
    
    if current_maze_type == "NORMAL":
        text = font.render(MAZE_STATES["NORMAL"], True, WHITE)
        text_rect = text.get_rect()
        text_rect.centerx = MAZE_SIZE + INFO_WIDTH//2
        text_rect.y = 50
        screen.blit(text, text_rect)
        
        # 修改这里的显示文本
        remaining_stars = len(task_doors)
        mission_text = font.render(f"Mission remaining: {remaining_stars}/{required_stars}", True, WHITE)
        text_rect = mission_text.get_rect()
        text_rect.centerx = MAZE_SIZE + INFO_WIDTH//2
        text_rect.y = 100
        screen.blit(mission_text, text_rect)
        
    elif current_maze_type == "TASK":
        # 显示当前任务迷宫编号
        entry_pos = player.entry_point
        try:
            task_number = task_maze_order.index(entry_pos) + 1
        except (ValueError, TypeError):
            task_number = len(task_maze_order)  # 如果找不到位置，使用列表长度作为编号
        
        text = font.render(MAZE_STATES["TASK"].format(task_number), True, WHITE)
        text_rect = text.get_rect()
        text_rect.centerx = MAZE_SIZE + INFO_WIDTH//2
        text_rect.y = 50
        screen.blit(text, text_rect)
        
        # 计算已完成的任务数量
        small_tasks_completed = sum(1 for task in small_tasks if task.completed)
        big_tasks_completed = sum(1 for task in big_tasks if task.completed)
        
        if big_tasks_completed >= required_big_tasks or small_tasks_completed >= required_small_tasks:
            task_text = font.render("You can exit now!", True, WHITE)
        else:
            task_text = font.render("Complete either:", True, WHITE)
            screen.blit(task_text, (MAZE_SIZE + INFO_WIDTH//4, 100))
            
            small_remaining = required_small_tasks - small_tasks_completed
            if small_remaining > 0:
                small_text = font.render(f"{small_remaining} small tasks", True, WHITE)
                screen.blit(small_text, (MAZE_SIZE + INFO_WIDTH//4, 130))
            
            big_remaining = required_big_tasks - big_tasks_completed
            if big_remaining > 0:
                big_text = font.render(f"{big_remaining} big tasks", True, WHITE)
                screen.blit(big_text, (MAZE_SIZE + INFO_WIDTH//4, 160))

    # 在状态面板底部绘血条
    health_y = HEIGHT - 50  # 距离底部50像素
    health_x = MAZE_SIZE + 20  # 距离右侧边界20像素
    heart_width = 30  # 心形标宽度
    heart_spacing = 10  # 心形图标间距
    
    for i in range(MAX_HEALTH):
        heart_x = health_x + i * (heart_width + heart_spacing)
        if i < current_health:
            # 绘制红色实心心
            pygame.draw.polygon(screen, (255, 0, 0), [
                (heart_x + heart_width//2, health_y + 5),
                (heart_x + heart_width, health_y + heart_width//2),
                (heart_x + heart_width//2, health_y + heart_width),
                (heart_x, health_y + heart_width//2)
            ])
        else:
            # 绘制灰色空心心形
            pygame.draw.polygon(screen, (128, 128, 128), [
                (heart_x + heart_width//2, health_y + 5),
                (heart_x + heart_width, health_y + heart_width//2),
                (heart_x + heart_width//2, health_y + heart_width),
                (heart_x, health_y + heart_width//2)
            ], 2)

    if current_maze_type == "THORNS":
        text = font.render(MAZE_STATES["THORNS"], True, WHITE)
        text_rect = text.get_rect()
        text_rect.centerx = MAZE_SIZE + INFO_WIDTH//2
        text_rect.y = 50
        screen.blit(text, text_rect)
        
        # 显示提示
        hint_text = font.render("Find the exit to return", True, WHITE)
        text_rect = hint_text.get_rect()
        text_rect.centerx = MAZE_SIZE + INFO_WIDTH//2
        text_rect.y = 100
        screen.blit(hint_text, text_rect)
        
        # 显示倒计时
        current_time = pygame.time.get_ticks()
        time_until_damage = (DAMAGE_INTERVAL - (current_time - last_damage_time)) // 1000
        timer_text = font.render(f"Next damage: {time_until_damage}s", True, RED)
        timer_rect = timer_text.get_rect()
        timer_rect.centerx = MAZE_SIZE + INFO_WIDTH//2
        timer_rect.y = 250
        screen.blit(timer_text, timer_rect)
        
       # 显示提示（分成两行显示）
        hint_text1 = font.render("Auto-deduction", True, WHITE)
        hint_text2 = font.render("every 7 seconds", True, WHITE)
       
        text_rect1 = hint_text1.get_rect()
        text_rect1.centerx = MAZE_SIZE + INFO_WIDTH//2
        text_rect1.y = 150
       
        text_rect2 = hint_text2.get_rect()
        text_rect2.centerx = MAZE_SIZE + INFO_WIDTH//2
        text_rect2.y = 180
       
        screen.blit(hint_text1, text_rect1)
        screen.blit(hint_text2, text_rect2)

def draw_start_menu():
    """绘制开始菜单"""
    # 载并放背景图片适应窗口大小
    try:
        background = pygame.image.load('background.jpg')
        background = pygame.transform.scale(background, (WIDTH, HEIGHT))
        screen.blit(background, (0, 0))
    except pygame.error as e:
        print(f"Warning: Could not load background image: {e}")
        screen.fill(BLACK)  # 如果加载失败则使用黑色背景
    
    font = pygame.font.SysFont('arial', 36)
    title_font = pygame.font.SysFont('arial', 48)
    
    # 绘制半透明的黑色遮罩，使字更容易阅读
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.fill(BLACK)
    overlay.set_alpha(128)  # 设置透明度 (0-255)
    screen.blit(overlay, (0, 0))
    
    # 绘制标题 - 将标题位置改为 HEIGHT//4 使其移
    title = title_font.render("MAZE GAME", True, WHITE)
    title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//4))
    screen.blit(title, title_rect)
    
    # 绘制难度选择
    difficulties = ["EASY", "MEDIUM", "HARD"]
    button_height = 60
    button_width = 200
    spacing = 20
    start_y = HEIGHT//2 - (len(difficulties) * (button_height + spacing))//2
    
    buttons = []
    for i, diff in enumerate(difficulties):
        button_rect = pygame.Rect(WIDTH//2 - button_width//2, 
                                start_y + i * (button_height + spacing),
                                button_width, button_height)
        text = font.render(diff, True, WHITE)
        text_rect = text.get_rect(center=button_rect.center)
        buttons.append((button_rect, text, text_rect, diff))
    
    # 在绘制完按钮后，添加记录显示
    font = pygame.font.SysFont('arial', 24)
    record_y = HEIGHT - 35  # 调整距离底部5像素（标题）
    
    # 绘制记录���题
    title_text = font.render("Completion Records:", True, WHITE)
    screen.blit(title_text, (WIDTH - 350, record_y - 30))  # 距离右边350像素，上移30像���
    
    # 修改显示顺序和间距
    difficulties = ["HARD", "MEDIUM", "EASY"]
    spacing = 20  # 定义固定间距
    current_x = WIDTH - 350  # 起始x坐标
    
    for difficulty in difficulties:
        # 绘制难度名称��冒号
        diff_text = font.render(f"{difficulty}:", True, WHITE)
        screen.blit(diff_text, (current_x, record_y))
        
        # 计算数字的位置（难度名称后面固定间距）
        number_x = current_x + diff_text.get_width() + 5  # 冒号后小间距
        number_text = font.render(str(COMPLETION_RECORDS[difficulty]), True, WHITE)
        screen.blit(number_text, (number_x, record_y))
        
        # 更新下一个难度的起始位置（数字后固定间距）
        current_x = number_x + number_text.get_width() + spacing
    
    # Feedback按钮
    feedback_button_width = 120
    feedback_button_height = 40
    feedback_button_x = 20
    feedback_button_y = HEIGHT - 60
    
    feedback_button_rect = pygame.Rect(feedback_button_x, feedback_button_y, 
                                     feedback_button_width, feedback_button_height)
    
    # Rules按钮
    rules_button_width = 120
    rules_button_height = 40
    rules_button_x = feedback_button_x + feedback_button_width + 20  # Feedback按钮右侧20像���
    rules_button_y = HEIGHT - 60
    
    rules_button_rect = pygame.Rect(rules_button_x, rules_button_y, 
                                   rules_button_width, rules_button_height)
    
    # Leaderboard按钮
    leaderboard_button_width = 120
    leaderboard_button_height = 40
    leaderboard_button_x = rules_button_x + rules_button_width + 20  # Rules按钮右侧20像素
    leaderboard_button_y = HEIGHT - 60
    
    leaderboard_button_rect = pygame.Rect(leaderboard_button_x, leaderboard_button_y, 
                                        leaderboard_button_width, leaderboard_button_height)
    
    # Settings按钮
    settings_button_width = 120
    settings_button_height = 40
    settings_button_x = leaderboard_button_x + leaderboard_button_width + 20  # Leaderboard按钮右侧20像素
    settings_button_y = HEIGHT - 60
    
    settings_button_rect = pygame.Rect(settings_button_x, settings_button_y, 
                                     settings_button_width, settings_button_height)
    
    # 绘制所有按钮
    for button_rect, text, color in [
        (feedback_button_rect, "Feedback", WHITE),
        (rules_button_rect, "Rules", WHITE),
        (leaderboard_button_rect, "Leaderboard", WHITE),
        (settings_button_rect, "Settings", WHITE)
    ]:
        if button_rect.collidepoint(pygame.mouse.get_pos()):
            pygame.draw.rect(screen, (100, 100, 100), button_rect)
        else:
            pygame.draw.rect(screen, (50, 50, 50), button_rect)
        
        pygame.draw.rect(screen, color, button_rect, 2)
        button_text = pygame.font.SysFont('arial', 24).render(text, True, color)
        button_text_rect = button_text.get_rect(center=button_rect.center)
        screen.blit(button_text, button_text_rect)
    
    return buttons, feedback_button_rect, rules_button_rect, leaderboard_button_rect, settings_button_rect

def show_start_menu():
    """显示开始菜单并返回选择的难度"""
    global cols, rows, cell_size, task_door_image, small_task_image, big_task_image, lock_image, open_image, current_difficulty
    
    # 播放菜单BGM
    try:
        pygame.mixer.music.load('bgm_menu.mp3')
        pygame.mixer.music.set_volume(0.3)  # 设置菜单BGM音量
        pygame.mixer.music.play(-1)  # 循环播放
    except pygame.error as e:
        print(f"Warning: Could not play menu BGM: {e}")
    
    buttons, feedback_button_rect, rules_button_rect, leaderboard_button_rect, settings_button_rect = draw_start_menu()
    pygame.display.flip()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # 检查反馈按钮点击
                if feedback_button_rect.collidepoint(mouse_pos):
                    show_feedback_dialog()
                    continue
                    
                # 检查规则按钮点击
                if rules_button_rect.collidepoint(mouse_pos):
                    show_rules_dialog()
                    continue
                
                # 检查排行榜按钮点���
                if leaderboard_button_rect.collidepoint(mouse_pos):
                    show_leaderboard_dialog()
                    continue
                
                # 检查设置按钮点击
                if settings_button_rect.collidepoint(mouse_pos):
                    show_settings_dialog()
                    continue
                
                for button_rect, _, _, difficulty in buttons:
                    if button_rect.collidepoint(mouse_pos):
                        # 停止菜单BGM
                        pygame.mixer.music.stop()
                        
                        # 加载游戏BGM
                        try:
                            pygame.mixer.music.load('bgm.mp3')
                            pygame.mixer.music.set_volume(0.3)
                        except pygame.error as e:
                            print(f"Warning: Could not load game BGM: {e}")
                        
                        # 更新当前难度和其他设置
                        current_difficulty = difficulty
                        cols = rows = DIFFICULTY_SETTINGS[difficulty]
                        cell_size = MAZE_SIZE // max(cols, rows)
                        
                        # 重新调整所有图片大小
                        try:
                            # 加载原始图片
                            original_task_door = pygame.image.load('task_door.png')
                            original_small_task = pygame.image.load('small_task.png')
                            original_big_task = pygame.image.load('big_task.png')
                            original_lock = pygame.image.load('lock.png')
                            original_open = pygame.image.load('open.png')
                            original_bomb = pygame.image.load('bomb.png')
                            
                            # 计算新的大小
                            new_size = int(cell_size * 0.8)
                            
                            # 重新放所���图片
                            task_door_image = pygame.transform.scale(original_task_door, (new_size, new_size))
                            small_task_image = pygame.transform.scale(original_small_task, (new_size, new_size))
                            big_task_image = pygame.transform.scale(original_big_task, (new_size, new_size))
                            lock_image = pygame.transform.scale(original_lock, (new_size, new_size))
                            open_image = pygame.transform.scale(original_open, (new_size, new_size))
                            
                        except pygame.error as e:
                            print(f"Warning: Could not load or scale image: {e}")
                            task_door_image = None
                            small_task_image = None
                            big_task_image = None
                            lock_image = None
                            open_image = None
                            
                        return
        
        # 重新绘制菜单包括背景）
        buttons, feedback_button_rect, rules_button_rect, leaderboard_button_rect, settings_button_rect = draw_start_menu()
        
        # 绘按钮
        for button_rect, text, text_rect, _ in buttons:
            # 检查鼠标悬停
            if button_rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(screen, (100, 100, 100), button_rect)
            else:
                pygame.draw.rect(screen, (50, 50, 50), button_rect)
            pygame.draw.rect(screen, WHITE, button_rect, 2)  # 边框
            screen.blit(text, text_rect)
        
        pygame.display.flip()

def draw_back_button():
    """绘制返回按钮"""
    font = pygame.font.SysFont('arial', 24)
    button_width = 100
    button_height = 40
    button_x = MAZE_SIZE + (INFO_WIDTH - button_width) // 2
    button_y = HEIGHT - 100  # 距底部100像素
    
    button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
    
    # 检查标签悬停
    if button_rect.collidepoint(pygame.mouse.get_pos()):
        pygame.draw.rect(screen, (100, 100, 100), button_rect)
    else:
        pygame.draw.rect(screen, (50, 50, 50), button_rect)
    
    pygame.draw.rect(screen, WHITE, button_rect, 2)  # 边框
    
    # 绘制按钮文本
    text = font.render("BACK", True, WHITE)
    text_rect = text.get_rect(center=button_rect.center)
    screen.blit(text, text_rect)
    
    return button_rect

def show_confirmation_dialog():
    """显示确认对话框"""
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    result = messagebox.askyesno("Confirm", "Return to start menu?")
    root.destroy()
    return result

# 添加新的函数用于寻找路径
def find_path_to_exit():
    """使用BFS找到出口的路"""
    if current_maze_type == "NORMAL":
        target = (cols-1, rows-1)  # 普通迷宫出口
    else:
        target = task_exit_pos  # 任务迷宫出口
    
    start = (player.x, player.y)
    queue = [(start, [start])]
    visited = {start}
    
    while queue:
        (x, y), path = queue.pop(0)
        if (x, y) == target:
            return path
            
        # 检查四个方向
        if y > 0 and not grid[x][y].walls[0] and (x, y-1) not in visited:  # 上
            queue.append(((x, y-1), path + [(x, y-1)]))
            visited.add((x, y-1))
        if x < cols-1 and not grid[x][y].walls[1] and (x+1, y) not in visited:  # 右
            queue.append(((x+1, y), path + [(x+1, y)]))
            visited.add((x+1, y))
        if y < rows-1 and not grid[x][y].walls[2] and (x, y+1) not in visited:  # 下
            queue.append(((x, y+1), path + [(x, y+1)]))
            visited.add((x, y+1))
        if x > 0 and not grid[x][y].walls[3] and (x-1, y) not in visited:  # 左
            queue.append(((x-1, y), path + [(x-1, y)]))
            visited.add((x-1, y))
    
    return None

# 添加自路径动画函数
def auto_path_animation(path):
    """显示自动寻路动画"""
    if not path:
        return
        
    original_pos = (player.x, player.y)
    animation_speed = 100  # 毫秒
    
    # 保存当前位置
    for pos in path:
        player.x, player.y = pos
        
        # 重绘屏幕
        screen.fill(BLACK)
        for x in range(cols):
            for y in range(rows):
                grid[x][y].draw(screen)
        
        # 绘制出口
        draw_exit(screen)
        
        # 绘制玩家
        player.draw(screen)
        
        # 绘制状态面板
        draw_status_panel()
        
        # 绘制返回按钮和自动寻路按钮
        draw_back_button()
        draw_auto_path_button()
        
        pygame.display.flip()
        pygame.time.delay(animation_speed)
    
    # 动画结束后返回原位置
    pygame.time.delay(500)  # 在终点停留半秒
    player.x, player.y = original_pos

# 添加绘制自动寻路按钮的函数
def draw_auto_path_button():
    """绘制自动寻路按钮"""
    font = pygame.font.SysFont('arial', 24)
    button_width = 100
    button_height = 40
    button_x = MAZE_SIZE + (INFO_WIDTH - button_width) // 2
    button_y = HEIGHT - 160  # 在返回按钮下方
    
    button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
    
    # 检查鼠标悬停
    if button_rect.collidepoint(pygame.mouse.get_pos()):
        pygame.draw.rect(screen, (100, 100, 100), button_rect)
    else:
        pygame.draw.rect(screen, (50, 50, 50), button_rect)
    
    pygame.draw.rect(screen, WHITE, button_rect, 2)  # 边框
    
    # 绘制按钮文本
    text = font.render('Auto Path', True, WHITE)
    text_rect = text.get_rect(center=button_rect.center)
    screen.blit(text, text_rect)
    
    return button_rect

def get_current_difficulty():
    """获取当前游戏难度"""
    global current_difficulty
    return current_difficulty

def show_feedback_dialog():
    """显示反馈对话框"""
    root = tk.Tk()
    root.title("问题反馈")
    
    # 设置窗口大小和位置
    window_width = 500
    window_height = 400
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # 创建标签
    tk.Label(root, text="请描述您的问题:", font=('arial', 12)).pack(pady=10)
    
    # 创建文本框
    text_box = tk.Text(root, height=10, width=50, font=('arial', 11))
    text_box.pack(pady=10, padx=20)
    
    def submit_feedback():
        feedback_content = text_box.get("1.0", tk.END).strip()
        
        if not feedback_content:
            messagebox.showwarning("提示", "请输入反馈内容")
            return
        
        # 显示发送中提示
        status_label = tk.Label(root, text="正在发送...", font=('arial', 10))
        status_label.pack(pady=5)
        root.update()
        
        # 模拟发送延迟
        root.after(1000, lambda: [
            messagebox.showinfo("成功", "感谢您的反馈！我们将会尽快处理。"), 
            root.destroy()
        ])
    
    # 创建提交按钮
    submit_btn = tk.Button(root, text="提交反馈", command=submit_feedback, 
                          font=('arial', 11), width=15)
    submit_btn.pack(pady=20)
    
    # 运行窗口
    root.mainloop()

def show_rules_dialog():
    """显示游戏规则对话框"""
    root = tk.Tk()
    root.title("游戏规则")
    
    # 设置窗口大小和位置
    window_width = 600
    window_height = 500
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # 创建文本框
    text_box = tk.Text(root, height=20, width=60, font=('arial', 11))
    text_box.pack(pady=20, padx=20)
    
    # 游戏规则内容
    rules_text = """游戏规则：

1. 基本移动：
   - 使用方向键控制角色移动
   - 在迷宫中寻找出路

2. 双迷宫结构：
   第一层（主迷宫）：
   - 包含通往第二层的蓝色星
   - 必须完成第二层的任务才能通关

3. 任务迷宫：
   - 小任务：数学问题
   - 大任务：计时挑战
   - 完成规定数量的任务才能解锁出口

4. 难度等级：
   简单：
   - 2个星星，3个小任务，1个大任务
   - 完成3个小任务或1个大任务即可

   中等：
   - 3个星星，6个小任务，2个大任务
   - 完成6个小任务或2个大任务即可

   困难：
   - 4个星星，9个小任务，3个大任务
   - 完成9个小任务或3个大任务即可

5. 出口规则：
   - 完成规定任务数前主迷宫出口保持��定
   - 绿色出口表示已锁
   - 红色出口表示需要完成更多任务

6. 游戏提示：
   - 规划迷宫路线
   - 记录已完成的任务
   - 可以使用自动寻路功能
"""
    
    # 插入规文本
    text_box.insert('1.0', rules_text)
    text_box.config(state='disabled')  # 设置为只读
    
    # 创建关闭按钮
    close_btn = tk.Button(root, text="关闭", command=root.destroy, 
                         font=('arial', 11), width=15)
    close_btn.pack(pady=20)
    
    # 运行窗口
    root.mainloop()

def show_author_dialog():
    """显示作者���话框"""
    root = tk.Tk()
    root.withdraw()
    result = messagebox.askyesno("重要提醒", "作者帅不帅？")
    root.destroy()
    return result

# 在全局变量区域添加（注意放在其他全局变量附近）
MAX_HEALTH = 5  # 最大生命值
current_health = MAX_HEALTH  # 当前生命值

# 在Task类定义之添加这些函数
def decrease_health(amount):
    """减少生命值"""
    global current_health
    current_health = max(0, current_health - amount)
    if current_health <= 0:
        show_game_over()
        return True  # 返回True表示生命值耗尽
    return False

def show_game_over():
    """显示游戏结束画面"""
    screen.fill(BLACK)
    font = pygame.font.SysFont('microsoftyaheimicrosoftyaheiui', 50)
    text = font.render('游戏结束！', True, RED)
    text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
    screen.blit(text, text_rect)
    pygame.display.flip()
    pygame.time.delay(2000)  # 显示2秒

def relocate_task(task):
    """重新定位一个任务的位置"""
    # 获取所有可用位置（排除起点、出口和其他任务的位置）
    available_positions = []
    occupied_positions = [(0, 0)]  # 起点
    
    # 添加任务迷宫出口和已占用列表
    if task_exit_pos:
        occupied_positions.append(task_exit_pos)
    
    # 添加其他任务的位置到已占用列表
    for small_task in small_tasks:
        if small_task != task:  # 不包括当前任务
            occupied_positions.append((small_task.x, small_task.y))
    for big_task in big_tasks:
        if big_task != task:  # 不包括当前任务
            occupied_positions.append((big_task.x, big_task.y))
    
    # 收集有位置
    for x in range(cols):
        for y in range(rows):
            if (x, y) not in occupied_positions:
                available_positions.append((x, y))
    
    # 随机选择新位置
    if available_positions:
        new_pos = random.choice(available_positions)
        task.x, task.y = new_pos

def generate_bomb_positions():
    """生成炸弹置"""
    global bomb_positions
    
    # 清空现有炸弹位置
    bomb_positions = []
    
    # 只在MEDIUM难度下生成炸弹
    if current_difficulty != "MEDIUM":
        return
    
    # 获取所有可用位置（排除起点、终点和任务位置）
    available_positions = []
    occupied_positions = [(0, 0)]  # 起点
    
    # 添加出口到已占用位置
    if task_exit_pos:
        occupied_positions.append(task_exit_pos)
    
    # 添加任务位置到已占用列表
    for task in small_tasks:
        occupied_positions.append((task.x, task.y))
    for task in big_tasks:
        occupied_positions.append((task.x, task.y))
    
    # 收集可用位置
    for x in range(cols):
        for y in range(rows):
            if (x, y) not in occupied_positions:
                available_positions.append((x, y))
    
    # 随机选择一个位置放置弹
    if available_positions:
        bomb_pos = random.choice(available_positions)  # 只选择一个位置
        bomb_positions.append(bomb_pos)  # 只添加一个炸弹位置

def show_monster_catch_message():
    """显示被怪物抓到的提示"""
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    messagebox.showinfo("提示", "Oops！你���抓到了！")
    root.destroy()

# 主循环
def main():
    global grid, player, task_doors, small_tasks, big_tasks
    global current_maze_type, normal_maze_grid, task_maze_grid
    global task_exit_pos, task_maze_order, task_maze_grids
    global current_difficulty, current_health
    global grid, normal_maze_grid, player, current_maze_type, task_maze_order
    global can_through_wall, current_health, current_user, screen, task_maze_grids
    global is_fog_active, bomb_image, cell_size, monster_visited_positions, monster_stuck_count
    global player_image, original_player_image  # 添加original_player_image
    global last_damage_time  # 添加这个全局变量
    
    # 初始化last_damage_time
    last_damage_time = pygame.time.get_ticks()
    
    # 初始化怪物相关变量
    monster_stuck_count = 0
    monster_visited_positions.clear()
    
    # 初始化pygame
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("迷宫游戏")
    
    # 加载玩家图像
    try:
        original_player_image = pygame.image.load("player.png")  # 保存原始图像
        original_player_image = pygame.transform.scale(original_player_image, (cell_size - 10, cell_size - 10))
        player_image = original_player_image  # 初始化player_image
    except:
        print("Warning: Could not load player image")
        original_player_image = None
        player_image = None
    
    # 加载并显示背景图片，并调整亮度
    try:
        background_image = pygame.image.load("background.jpg")
        background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))
        
        # 创建一个半透明的黑色遮罩来降低亮度
        dark_surface = pygame.Surface((WIDTH, HEIGHT))
        dark_surface.fill((0, 0, 0))
        dark_surface.set_alpha(128)  # 设置透明度 (0-255)
        
        # 绘制背景和遮罩
        screen.blit(background_image, (0, 0))
        screen.blit(dark_surface, (0, 0))
        pygame.display.flip()
    except:
        print("Warning: Could not load background image")
        screen.fill(BLACK)
        pygame.display.flip()
    
    # 示登录界面
    current_user = show_login_dialog()
    if not current_user:
        return
    
    # 登录后的代码继续使用原来的颜色背景
    screen.fill(BLACK)
    
    # 加载当前用户的通关记录
    load_records()
    
    # 初始化迷雾状态为False
    is_fog_active = False
    
    while True:  # 外层循环���理游���启动
        # 显示开始菜单
        show_start_menu()
        
        # 开始播放BGM
        try:
            pygame.mixer.music.load('bgm.mp3')
            pygame.mixer.music.set_volume(0.3)
        except:
            print("Warning: Could not play BGM")
        
        # 初��化游戏
        grid = [[Cell(x, y) for y in range(rows)] for x in range(cols)]
        normal_maze_grid = grid
        generate_maze()
        generate_task_doors()
        
        # 在这里添加生成传送门
        if current_difficulty == "HARD":
            generate_passing_doors()
            
        player = Player()
        current_maze_type = "NORMAL"
        task_maze_order = []
        can_through_wall = False  # 重置穿墙状态
        
        # 重置生命值
        current_health = MAX_HEALTH
        
        # 游戏循环
        running = True
        while running:
            screen.fill(BLACK)
            pygame.draw.rect(screen, (30, 30, 30), (MAZE_SIZE, 0, INFO_WIDTH, HEIGHT))
            
            # 在这里添加计时器检查
            if current_maze_type == "THORNS":
                current_time = pygame.time.get_ticks()
                if current_time - last_damage_time >= DAMAGE_INTERVAL:
                    current_health = max(0, current_health - 1)
                    last_damage_time = current_time
                    
                    # 播放受伤音效
                    if failure_sound:
                        failure_sound.play()
                    
                    # 闪烁效果
                    flash_screen()
                    
                    # 检查生命值是否耗尽
                    if current_health <= 0:
                        show_game_over()
                        running = False
                        break
            
            # 绘制迷宫网格
            for x in range(cols):
                for y in range(rows):
                    grid[x][y].draw(screen)
            
            # 在这里添加绘制传送门
            if current_maze_type == "NORMAL" and current_difficulty == "HARD":
                draw_passing_doors()
            
            # 绘制出口
            draw_exit(screen)
            
            # 根据不同迷宫类型绘制不同元素
            if current_maze_type == "NORMAL":
                # 绘制任务门
                for (bx, by) in task_doors:
                    offset_x = (MAZE_SIZE - cols * cell_size) // 2
                    offset_y = (MAZE_SIZE - rows * cell_size) // 2
                    if task_door_image:
                        x = offset_x + bx * cell_size + (cell_size - task_door_image.get_width()) // 2
                        y = offset_y + by * cell_size + (cell_size - task_door_image.get_height()) // 2
                        screen.blit(task_door_image, (x, y))
                    else:
                        pygame.draw.rect(screen, BLUE, (offset_x + bx * cell_size, 
                                                      offset_y + by * cell_size, 
                                                      cell_size, cell_size))
            elif current_maze_type == "TASK":
                draw_tasks()
                if current_difficulty == "HARD":
                    if GAME_SETTINGS['enable_heart']:
                        draw_heart()
                    if GAME_SETTINGS['enable_monster']:
                        draw_monster()
            elif current_maze_type == "THORNS":
              
                draw_thorns()  # 确保这行代码被执行
            
            # 绘制玩家（确保在所有其他元素之后绘制）
            player.draw(screen)
            
            # 绘制迷雾效果（如果启用）
            if is_fog_active:
                draw_fog_of_war()
            
            
            # 绘制状态面板
            draw_status_panel()
            
            # 绘制按钮
            draw_back_button()
            draw_auto_path_button()
            if current_maze_type == "TASK":
                draw_task_path_buttons()
            
            pygame.display.flip()
            
            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # 检查返回按钮点击
                    back_button_rect = draw_back_button()
                    if back_button_rect.collidepoint(mouse_pos):
                        if show_confirmation_dialog():
                            running = False
                            break
                    
                    # 检查自动寻路按钮点击
                    auto_path_button_rect = draw_auto_path_button()
                    if auto_path_button_rect.collidepoint(mouse_pos):
                        path = find_path_to_exit()
                        if path:
                            auto_path_animation(path)
                    
                    # 检查任务寻路按钮点击（仅在任务迷宫中）
                    if current_maze_type == "TASK":
                        small_task_button, big_task_button = draw_task_path_buttons()
                        if small_task_button.collidepoint(mouse_pos):
                            path = find_path_to_nearest_small_task()
                            if path:
                                auto_path_animation(path)
                            else:
                                show_popup_message("没有找到未完成的小任务！")
                        elif big_task_button.collidepoint(mouse_pos):
                            path = find_path_to_nearest_big_task()
                            if path:
                                auto_path_animation(path)
                            else:
                                show_popup_message("没有找到未完成的大任务！")
                
                # 只保留这一个键盘事件处理块
                if event.type == pygame.KEYDOWN:
                   
                    last_position = (player.x, player.y)
                    moved = False
                    
                    # 添加Ctrl键检测来触发彩蛋
                    if pygame.key.get_mods() & pygame.KMOD_CTRL:
                        if is_fog_active:
                            # 添加全局变量声明
                            global is_punished
                            
                            # 创建一个临时的Tk窗口
                            root = tk.Tk()
                            root.withdraw()
                            # 显示作者对话框
                            result = messagebox.askyesno("重要提醒", "作者帅不帅？")
                            if result:  # 如果回答是
                                is_fog_active = False
                                is_punished = False  # 重置惩罚状态
                                if success_sound:
                                    success_sound.play()
                                show_popup_message("迷雾消散了！")
                            else:  # 如果回答否
                                is_punished = True  # 设置惩罚状态
                                if failure_sound:
                                    failure_sound.play()
                                show_popup_message("你的视野被进一步限制了！")
                            root.destroy()  # 确保窗口被销毁
                    
                    if event.key == pygame.K_UP:
                        
                        moved = player.move("UP")
                    elif event.key == pygame.K_RIGHT:
                       
                        moved = player.move("RIGHT")
                        if player_image and original_player_image:
                            player_image = original_player_image  # 使用原始图像（朝右）
                    elif event.key == pygame.K_DOWN:
                       
                        moved = player.move("DOWN")
                    elif event.key == pygame.K_LEFT:
                       
                        moved = player.move("LEFT")
                        if player_image and original_player_image:
                            player_image = pygame.transform.flip(original_player_image, True, False)  # 水平翻转
                    elif event.key == pygame.K_SPACE:
                        # 创建一个临时的Tk窗口
                        root = tk.Tk()
                        root.withdraw()
                        # 显示作者对话框
                        result = messagebox.askyesno("��要提���", "作者帅不帅？")
                        if result:  # 如果回答是
                            can_through_wall = not can_through_wall  # 切换穿墙状态
                            # 显示获得穿墙技能的提示
                            messagebox.showinfo("恭喜", "获得穿墙技������")
                        root.destroy()  # 确保窗口被销毁
                       
                    
                    # 移动后的检查
                    if moved:
                        # 在这里添加传送检查
                        if handle_teleport():
                            continue
                            
                        # 检查是否碰到荆棘迷宫门
                        if current_maze_type == "TASK" and (player.x, player.y) == endless_door_pos:
                            switch_to_thorns_maze()
                        # 检查是否碰到任务门
                        elif current_maze_type == "NORMAL" and (player.x, player.y) in task_doors:
                            switch_to_task_maze()
                        # 检查是否到达主迷宫出口
                        elif current_maze_type == "NORMAL" and player.x == cols-1 and player.y == rows-1:
                            if last_position != (cols-1, rows-1):
                                if check_all_task_mazes_completed():
                                    show_success(screen)
                                    running = False
                                    break
                                else:
                                    show_remaining_tasks()
                        # 检查任务碰撞（包括荆棘迷宫出口）
                        elif handle_task_collision(player.x, player.y, last_position):
                            running = False
                            break
            
            # 在绘制所有元素之后，pygame.display.flip()之前添加
            if current_maze_type == "TASK" and current_difficulty == "HARD":
                update_monster()
                draw_monster()
                
                # 检查玩家是否碰到怪物
                if monster_pos and (player.x, player.y) == monster_pos:
                    show_monster_catch_message()  # 添加这行
                    if decrease_health(1):
                        running = False
                        break
                    init_monster()

        # 在游戏结束时停止BGM
        pygame.mixer.music.stop()

def show_leaderboard_dialog():
    """显示排行榜对话框"""
    root = tk.Tk()
    root.title("Leaderboard")
    
    # 设置窗口大小和位置
    window_width = 600
    window_height = 500
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # 创建文本框
    text_box = tk.Text(root, height=20, width=60, font=('arial', 11))
    text_box.pack(pady=20, padx=20)
    
    # 获取所有用户数据
    users = load_users()
    
    # 创建用户得分列表
    user_scores = []
    for username, scores in users.items():
        user_scores.append({
            'username': username,
            'hard': scores['HARD'],
            'medium': scores['MEDIUM'],
            'easy': scores['EASY']
        })
    
    # 按规则排序：优先hard，其次medium，最后easy
    user_scores.sort(key=lambda x: (-x['hard'], -x['medium'], -x['easy']))
    
    # 生成排行榜文本
    leaderboard_text = "Global Leaderboard\n\n"
    for i, score in enumerate(user_scores, 1):
        leaderboard_text += f"{i}. {score['username']}\n"
        leaderboard_text += f"   HARD: {score['hard']} | MEDIUM: {score['medium']} | EASY: {score['easy']}\n\n"
    
    # 插入排行榜文本
    text_box.insert('1.0', leaderboard_text)
    text_box.config(state='disabled')  # 设置为只读
    
    # 创建关闭按钮
    close_btn = tk.Button(root, text="Close", command=root.destroy, 
                         font=('arial', 11), width=15)
    close_btn.pack(pady=20)
    
    # 运行窗口
    root.mainloop()

# 在全局作用域定义 draw_fog_of_war 函数
def draw_fog_of_war():
    """绘制迷雾效果"""
    if not is_fog_active:
        return
    
    # 创建迷雾表面
    fog = pygame.Surface((MAZE_SIZE, MAZE_SIZE), pygame.SRCALPHA)
    fog.fill((0, 0, 0, 250))  # 增加不透明度到250
    
    # 计算迷宫的实际偏移量
    offset_x = (MAZE_SIZE - cols * cell_size) // 2
    offset_y = (MAZE_SIZE - rows * cell_size) // 2
    
    # 根据是否被惩罚决定视野范围
    if is_punished:  # 添加一个全局变量来追踪是否被惩罚
        # 只显示1x1区域
        screen_x = offset_x + player.x * cell_size
        screen_y = offset_y + player.y * cell_size
        transparent_rect = pygame.Rect(screen_x, screen_y, cell_size, cell_size)
        pygame.draw.rect(fog, (0, 0, 0, 0), transparent_rect)
    else:
        # 显示3x3区域
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                target_x = player.x + dx
                target_y = player.y + dy
                if 0 <= target_x < cols and 0 <= target_y < rows:
                    screen_x = offset_x + target_x * cell_size
                    screen_y = offset_y + target_y * cell_size
                    transparent_rect = pygame.Rect(screen_x, screen_y, cell_size, cell_size)
                    pygame.draw.rect(fog, (0, 0, 0, 0), transparent_rect)
    
    # 将迷雾层绘制到屏幕上
    screen.blit(fog, (0, 0))

# 在文件开头的全局变量区域添加
is_punished = False  # 用于追踪是否被惩罚

def handle_big_task(task):
    """处理大任务碰"""
    # 显示反应测试任务
    result = show_reaction_task()  # 修改这里，使用正确的函数名
    
    if result is None:  # 生命值耗尽
        return True
    elif result:
        if coin_sound:
            coin_sound.play()
        task.completed = True
        relocate_task(task)  # 重新定位任务
        return False
    else:
        if failure_sound:
            failure_sound.play()
        if decrease_health(2):  # 修改这里，大任务失败扣2滴血
            return True
        relocate_task(task)  # 任务失败时也重新定位
        return False

def handle_small_task(task):
    """处理小任务碰撞"""
    # 显示数学题任务
    result = show_math_task()
    
    if result is None:  # 生命值耗尽
        return True
    elif result:
        if coin_sound:
            coin_sound.play()
        task.completed = True
        relocate_task(task)  # 重新定位任务
        return False
    else:
        if failure_sound:
            failure_sound.play()
        return False

def show_incomplete_task_message():
    """显示任务未完成提示"""
    current_difficulty = get_current_difficulty()
    required_small_tasks = DIFFICULTY_CONFIGS[current_difficulty]["small_tasks"]
    required_big_tasks = DIFFICULTY_CONFIGS[current_difficulty]["big_tasks"]
    
    small_tasks_completed = sum(1 for task in small_tasks if task.completed)
    big_tasks_completed = sum(1 for task in big_tasks if task.completed)
    
    small_remaining = required_small_tasks - small_tasks_completed
    big_remaining = required_big_tasks - big_tasks_completed
    
    message = f"需要完成以下任务之一才能离开:\n"
    message += f"- 还需完成 {small_remaining} 个小任务\n"
    message += f"- 或完成 {big_remaining} 个大任务"
    
    show_popup_message(message)

# Monster related globals
monster_image = None
monster_pos = None  # 怪物位置
monster_direction = None  # 怪物移动方向
MONSTER_SPEED = 5
last_monster_move = 0  # 上次移动时间
MONSTER_MOVE_DELAY = 1000  # 增加移动延迟到1秒

def init_monster():
    """初始化怪物位置和方向"""
    global monster_pos, monster_direction, last_monster_move
    
    
    # 获取可用位置（排除玩家位置、任务位置和出口）
    available_positions = []
    occupied_positions = [(0, 0), task_exit_pos]  # 添加玩家起始位置和出口
    
    # 添加任务位置
    for task in small_tasks + big_tasks:
        occupied_positions.append((task.x, task.y))
    
    # 收集可用位置
    for x in range(cols):
        for y in range(rows):
            if (x, y) not in occupied_positions:
                available_positions.append((x, y))
    
    if available_positions:
        monster_pos = random.choice(available_positions)
        monster_direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
        last_monster_move = pygame.time.get_ticks()  # 初始化最后移动时间
        
def update_monster():
    """更新怪物位置"""
    global monster_pos, monster_direction, last_monster_move, monster_stuck_count, monster_visited_positions  # 添加所有需要的全局变量
    
    current_time = pygame.time.get_ticks()
    if current_time - last_monster_move < MONSTER_MOVE_DELAY:
        return
    
    if not monster_pos:
        return
    
    def can_move_to(from_pos, to_pos):
        """检查是否以从个位置移动到另一个位置"""
        dx = to_pos[0] - from_pos[0]
        dy = to_pos[1] - from_pos[1]
        
        # 检查墙壁
        if dy == -1:  # 向上
            return not grid[from_pos[0]][from_pos[1]].walls[0]
        elif dx == 1:  # 向右
            return not grid[from_pos[0]][from_pos[1]].walls[1]
        elif dy == 1:  # 向下
            return not grid[from_pos[0]][from_pos[1]].walls[2]
        elif dx == -1:  # 向左
            return not grid[from_pos[0]][from_pos[1]].walls[3]
        return False
    
    def get_available_moves(pos):
        """获取指定位置的所有可用移动方向"""
        moves = []
        for d in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
            new_x = pos[0] + d[0]
            new_y = pos[1] + d[1]
            new_pos = (new_x, new_y)
            if (0 <= new_x < cols and 0 <= new_y < rows and 
                can_move_to(pos, new_pos)):
                moves.append(d)
        return moves
    
    def find_path_to_target(start, target):
        """使用A*算法寻找到目标的路径"""
        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])  # 删除多余的右括号
        
        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}
        
        while frontier:
            current = heapq.heappop(frontier)[1]
            
            if current == target:
                break
                
            for next_move in get_available_moves(current):
                next_pos = (current[0] + next_move[0], current[1] + next_move[1])
                new_cost = cost_so_far[current] + 1
                
                if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                    cost_so_far[next_pos] = new_cost
                    priority = new_cost + heuristic(next_pos, target)
                    heapq.heappush(frontier, (priority, next_pos))
                    came_from[next_pos] = current
        
        # 重建路径
        if target in came_from:
            path = []
            current = target
            while current is not None:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path
        return None
    
    # 获取当前可用移动
    available_moves = get_available_moves(monster_pos)
    
    if not available_moves:
        return
    
    # 计算与玩家的距离
    distance = abs(player.x - monster_pos[0]) + abs(player.y - monster_pos[1])
    
    # 检查是否卡住
    if monster_pos in monster_visited_positions:
        monster_stuck_count += 1
    else:
        monster_stuck_count = 0
        monster_visited_positions.add(monster_pos)
    
    # 如果卡住太久，清除访问记录并重置计数
    if monster_stuck_count > 5:
        monster_visited_positions.clear()
        monster_stuck_count = 0
    
    # 根据距离和状态选择移动策略
    if distance <= 8:  # 接近玩家时
        path = find_path_to_target(monster_pos, (player.x, player.y))
        if path and len(path) > 1:
            # 85%概率沿路径移动
            if random.random() < 0.85:
                next_pos = path[1]
                dx = next_pos[0] - monster_pos[0]
                dy = next_pos[1] - monster_pos[1]
                new_direction = (dx, dy)
                if new_direction in available_moves:
                    monster_direction = new_direction
            else:
                # 随机移动以增加不可预测性
                monster_direction = random.choice(available_moves)
        else:
            monster_direction = random.choice(available_moves)
    else:
        # 探索模式
        unvisited_moves = [m for m in available_moves if 
                          (monster_pos[0] + m[0], monster_pos[1] + m[1]) 
                          not in monster_visited_positions]
        
        if unvisited_moves and random.random() < 0.7:  # 70%概率选择未访问的方向
            monster_direction = random.choice(unvisited_moves)
        else:
            # 30%概率随机移动或当没有访问的方向时
            monster_direction = random.choice(available_moves)
    
    # 更新位置
    new_x = monster_pos[0] + monster_direction[0]
    new_y = monster_pos[1] + monster_direction[1]
    new_pos = (new_x, new_y)
    
    if can_move_to(monster_pos, new_pos):
        monster_pos = new_pos
    
        
        # 定期清除访问记录
        if len(monster_visited_positions) > cols * rows // 3:
            monster_visited_positions.clear()
    
    last_monster_move = current_time

def draw_monster():
    """绘制怪物"""
    if monster_pos and monster_image:
        # 计算实际绘制位置（考虑迷宫偏移）
        offset_x = (MAZE_SIZE - cols * cell_size) // 2
        offset_y = (MAZE_SIZE - rows * cell_size) // 2
        
        # 计算怪物的屏幕坐标
        x = offset_x + monster_pos[0] * cell_size
        y = offset_y + monster_pos[1] * cell_size
        
        # 居中显示怪物图片
        x += (cell_size - monster_image.get_width()) // 2
        y += (cell_size - monster_image.get_height()) // 2
        
      
        screen.blit(monster_image, (x, y))

# 在全局变量区域添加
monster_visited_positions = set()  # 记录怪物访问过的位置
monster_stuck_count = 0

# 在文件开头的全局变量区域添加
player_image = None  # 确保全局变量被定义

# 在全局变量区域添加
heart_image = None
heart_pos = None

def init_heart():
    """初始��红心位置"""
    global heart_pos
    
    # 获取可用位置（排除玩家位置、怪物位置、任务位置和出口）
    available_positions = []
    occupied_positions = [(0, 0), task_exit_pos]  # 添加玩家起始位置和出口
    
    if monster_pos:
        occupied_positions.append(monster_pos)
    
    # 添加��务位置
    for task in small_tasks + big_tasks:
        occupied_positions.append((task.x, task.y))
    
    # 收集可用位置
    for x in range(cols):
        for y in range(rows):
            if (x, y) not in occupied_positions:
                available_positions.append((x, y))
    
    if available_positions:
        heart_pos = random.choice(available_positions)

def draw_heart():
    """绘制红心"""
    global heart_image
    
    if not heart_pos or not heart_image:
        return
        
    # 计算实际绘制位置（考虑迷宫偏移）
    offset_x = (MAZE_SIZE - cols * cell_size) // 2
    offset_y = (MAZE_SIZE - rows * cell_size) // 2
    
    # 计算红心的屏幕坐标
    x = offset_x + heart_pos[0] * cell_size
    y = offset_y + heart_pos[1] * cell_size
    
    # 居中显示红心图片
    x += (cell_size - heart_image.get_width()) // 2
    y += (cell_size - heart_image.get_height()) // 2
    
    screen.blit(heart_image, (x, y))

def check_heart_collision():
    """检查是否吃到红心"""
    global current_health
    
    if heart_pos and (player.x, player.y) == heart_pos:
        if current_health < MAX_HEALTH:
            current_health += 1
            if success_sound:
                success_sound.play()
        init_heart()  # 重新生成红心位置

# 添加全局设置变量
GAME_SETTINGS = {
    'enable_bombs': True,
    'enable_monster': True,
    'enable_heart': True
}

def show_settings_dialog():
    """显示设置对话框"""
    root = tk.Tk()
    root.title("游戏设置")
    
    # ��置窗口大小和位置
    window_width = 400
    window_height = 300
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # 创建变量来存储复选框状态
    bomb_var = tk.BooleanVar(value=GAME_SETTINGS['enable_bombs'])
    monster_var = tk.BooleanVar(value=GAME_SETTINGS['enable_monster'])
    heart_var = tk.BooleanVar(value=GAME_SETTINGS['enable_heart'])
    
    # 创建标题标签
    title_label = tk.Label(root, text="游戏设置", font=('Arial', 16, 'bold'))
    title_label.pack(pady=20)
    
    # 创建设置框架
    frame = tk.Frame(root)
    frame.pack(pady=10)
    
    # 创建复选框
    bomb_cb = tk.Checkbutton(frame, text="启用炸弹 (仅在中等难度生效)", variable=bomb_var, 
                            font=('Arial', 12))
    bomb_cb.pack(pady=5)
    
    monster_cb = tk.Checkbutton(frame, text="启用怪�� (仅在困难难度生效)", variable=monster_var,
                               font=('Arial', 12))
    monster_cb.pack(pady=5)
    
    heart_cb = tk.Checkbutton(frame, text="启用红心 (仅在困难难度生效)", variable=heart_var,
                             font=('Arial', 12))
    heart_cb.pack(pady=5)
    
    def apply_settings():
        # 更新设置
        GAME_SETTINGS['enable_bombs'] = bomb_var.get()
        GAME_SETTINGS['enable_monster'] = monster_var.get()
        GAME_SETTINGS['enable_heart'] = heart_var.get()
        # 显示设置已更新的提示
        messagebox.showinfo("提示", "设置已更新！将在下一局游戏中生效。")
        root.destroy()
    
    # 创建应用按钮
    apply_button = tk.Button(root, text="应用设置", command=apply_settings,
                           font=('Arial', 12))
    apply_button.pack(pady=20)
    
    root.mainloop()

def find_path_to_nearest_small_task():
    """使用BFS找到最近的小任务"""
    start = (player.x, player.y)
    queue = [(start, [start])]
    visited = {start}
    
    # 获取所有未完成的小任务位置
    task_positions = [(task.x, task.y) for task in small_tasks if not task.completed]
    if not task_positions:
        return None
        
    while queue:
        (x, y), path = queue.pop(0)
        # 检查是否到达任意一个小任务位置
        if (x, y) in task_positions:
            return path
            
        # 检查四个方向
        if y > 0 and not grid[x][y].walls[0] and (x, y-1) not in visited:  # 上
            queue.append(((x, y-1), path + [(x, y-1)]))
            visited.add((x, y-1))
        if x < cols-1 and not grid[x][y].walls[1] and (x+1, y) not in visited:  # 右
            queue.append(((x+1, y), path + [(x+1, y)]))
            visited.add((x+1, y))
        if y < rows-1 and not grid[x][y].walls[2] and (x, y+1) not in visited:  # 下
            queue.append(((x, y+1), path + [(x, y+1)]))
            visited.add((x, y+1))
        if x > 0 and not grid[x][y].walls[3] and (x-1, y) not in visited:  # 左
            queue.append(((x-1, y), path + [(x-1, y)]))
            visited.add((x-1, y))
    
    return None

def find_path_to_nearest_big_task():
    """使用BFS找到最近的大任务"""
    start = (player.x, player.y)
    queue = [(start, [start])]
    visited = {start}
    
    # 获取所有未完成的大任务位置
    task_positions = [(task.x, task.y) for task in big_tasks if not task.completed]
    if not task_positions:
        return None
        
    while queue:
        (x, y), path = queue.pop(0)
        # 检查是否到达任意一个大任务位置
        if (x, y) in task_positions:
            return path
            
        # 检查四个方向
        if y > 0 and not grid[x][y].walls[0] and (x, y-1) not in visited:  # 上
            queue.append(((x, y-1), path + [(x, y-1)]))
            visited.add((x, y-1))
        if x < cols-1 and not grid[x][y].walls[1] and (x+1, y) not in visited:  # 右
            queue.append(((x+1, y), path + [(x+1, y)]))
            visited.add((x+1, y))
        if y < rows-1 and not grid[x][y].walls[2] and (x, y+1) not in visited:  # 下
            queue.append(((x, y+1), path + [(x, y+1)]))
            visited.add((x, y+1))
        if x > 0 and not grid[x][y].walls[3] and (x-1, y) not in visited:  # 左
            queue.append(((x-1, y), path + [(x-1, y)]))
            visited.add((x-1, y))
    
    return None

def draw_task_path_buttons():
    """绘制任务寻路按钮"""
    font = pygame.font.SysFont('arial', 24)
    button_width = 120
    button_height = 40
    spacing = 10
    
    # 小任务按钮
    small_button_x = MAZE_SIZE + (INFO_WIDTH - button_width) // 2
    small_button_y = HEIGHT - 220  # 在Auto Path按钮上方
    
    small_button_rect = pygame.Rect(small_button_x, small_button_y, button_width, button_height)
    
    # 检查鼠标悬停
    if small_button_rect.collidepoint(pygame.mouse.get_pos()):
        pygame.draw.rect(screen, (100, 100, 100), small_button_rect)
    else:
        pygame.draw.rect(screen, (50, 50, 50), small_button_rect)
    
    pygame.draw.rect(screen, WHITE, small_button_rect, 2)  # 边框
    
    # 绘制按钮文本
    small_text = font.render('Small Task', True, WHITE)
    small_text_rect = small_text.get_rect(center=small_button_rect.center)
    screen.blit(small_text, small_text_rect)
    
    # 大任务按钮
    big_button_x = MAZE_SIZE + (INFO_WIDTH - button_width) // 2
    big_button_y = small_button_y - button_height - spacing  # 在小任务按钮上方
    
    big_button_rect = pygame.Rect(big_button_x, big_button_y, button_width, button_height)
    
    # 检查鼠标悬停
    if big_button_rect.collidepoint(pygame.mouse.get_pos()):
        pygame.draw.rect(screen, (100, 100, 100), big_button_rect)
    else:
        pygame.draw.rect(screen, (50, 50, 50), big_button_rect)
    
    pygame.draw.rect(screen, WHITE, big_button_rect, 2)  # 边框
    
    # 绘制按钮文本
    big_text = font.render('Big Task', True, WHITE)
    big_text_rect = big_text.get_rect(center=big_button_rect.center)
    screen.blit(big_text, big_text_rect)
    
    return small_button_rect, big_button_rect

# 在全局变量区域添加
endless_door_pos = None
endless_door_image = None

def generate_endless_door_position():
    """生成endless_door的位置"""
    global endless_door_pos, endless_door_image
    
    # 如果已经生成过位置或已经访问过荆棘迷宫，则不再生成
    if endless_door_pos is not None or thorns_maze_visited:
        endless_door_pos = None
        return
    
    # 如果图片还没加载，加载并缩放图片
    if endless_door_image is None:
        try:
            original_endless_door = pygame.image.load('thorns_door.png')
            new_size = int(cell_size * 0.8)
            endless_door_image = pygame.transform.scale(original_endless_door, (new_size, new_size))
        except pygame.error as e:
            print(f"Warning: Could not load thorns_door image: {e}")
            endless_door_image = None
            return
    
    # 获取可用位置（排除起点、出口和任务位置）
    available_positions = []
    occupied_positions = [(0, 0), task_exit_pos]
    
    # 添加任务位置到已占用列表
    for task in small_tasks:
        occupied_positions.append((task.x, task.y))
    for task in big_tasks:
        occupied_positions.append((task.x, task.y))
    
    # 收集可用位置
    for x in range(cols):
        for y in range(rows):
            if (x, y) not in occupied_positions:
                available_positions.append((x, y))
    
    # 随机选择位置
    if available_positions:
        endless_door_pos = random.choice(available_positions)

def generate_thorns_maze():
    """生成荆棘迷宫"""
    global thorns_maze_grid, thorns_exit_pos, grid, thorn_positions
    global thorn_image, cell_size, heart_positions, heart_image
    global clear_potion_pos, clear_potion_image  # 添加清除药水相关变量
    
    # 1. 初始化荆棘迷宫���格
    thorns_maze_grid = [[Cell(x, y) for y in range(rows)] for x in range(cols)]
    
    # 2. 使用改进的深度优先搜索生成迷宫路径
    def generate_paths(x, y):
        stack = [(x, y)]
        visited = {(x, y)}
        
        while stack:
            current = stack[-1]
            x, y = current
            
            # 获取所有未访问的相邻单元格
            neighbors = []
            # 检查四个方向：上、右、下、左
            for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
                next_x, next_y = x + dx, y + dy
                if (0 <= next_x < cols and 0 <= next_y < rows and 
                    (next_x, next_y) not in visited):
                    neighbors.append((next_x, next_y, dx, dy))
            
            if neighbors:
                # 随机选择一个未访问的相邻单元格
                next_x, next_y, dx, dy = random.choice(neighbors)
                
                # 移除当前格子和下一个格子之间的墙
                if dy == -1:  # 向上
                    thorns_maze_grid[x][y].walls[0] = False
                    thorns_maze_grid[next_x][next_y].walls[2] = False
                elif dx == 1:  # 向右
                    thorns_maze_grid[x][y].walls[1] = False
                    thorns_maze_grid[next_x][next_y].walls[3] = False
                elif dy == 1:  # 向下
                    thorns_maze_grid[x][y].walls[2] = False
                    thorns_maze_grid[next_x][next_y].walls[0] = False
                elif dx == -1:  # 向左
                    thorns_maze_grid[x][y].walls[3] = False
                    thorns_maze_grid[next_x][next_y].walls[1] = False
                
                stack.append((next_x, next_y))
                visited.add((next_x, next_y))
            else:
                stack.pop()
    
    # 3. 从起点(0,0)开始生成迷宫
    generate_paths(0, 0)
    
    # 4. 确保没有完全封闭的单元格
    def ensure_connectivity():
        for x in range(cols):
            for y in range(rows):
                # 检查当前单元格是否完全封闭
                if all(thorns_maze_grid[x][y].walls):
                    # 如果是，随机打开一个方向的墙
                    possible_walls = []
                    # 检查四个方向
                    if y > 0:  # 上
                        possible_walls.append(0)
                    if x < cols-1:  # 右
                        possible_walls.append(1)
                    if y < rows-1:  # 下
                        possible_walls.append(2)
                    if x > 0:  # 左
                        possible_walls.append(3)
                    
                    if possible_walls:
                        # 随机选择一个方向打开墙
                        wall_to_remove = random.choice(possible_walls)
                        thorns_maze_grid[x][y].walls[wall_to_remove] = False
                        
                        # 同时打开相邻单元格的对应墙
                        if wall_to_remove == 0:  # 上
                            thorns_maze_grid[x][y-1].walls[2] = False
                        elif wall_to_remove == 1:  # 右
                            thorns_maze_grid[x+1][y].walls[3] = False
                        elif wall_to_remove == 2:  # 下
                            thorns_maze_grid[x][y+1].walls[0] = False
                        elif wall_to_remove == 3:  # 左
                            thorns_maze_grid[x-1][y].walls[1] = False
    
    # 5. 确保迷宫连通性
    ensure_connectivity()
    
    # 6. 生成出口位置（避开起点）
    available_positions = []
    for x in range(cols):
        for y in range(rows):
            if (x, y) != (0, 0):  # 避开起点
                available_positions.append((x, y))
    
    thorns_exit_pos = random.choice(available_positions)
    
    # 7. 将生成的荆棘迷宫设置为当前迷宫
    grid = thorns_maze_grid
    
    # 8. 加载荆棘图片（移到生成位置之前）
    try:
      
        original_thorn = pygame.image.load('thorn.png')
        new_size = int(cell_size * 0.8)
        thorn_image = pygame.transform.scale(original_thorn, (new_size, new_size))
       
    except Exception as e:
     
        thorn_image = None
    
    # 9. 生成荆棘位置
    generate_thorn_positions()
    
    # 加载心形图片
    try:
        original_heart = pygame.image.load('heart.png')
        new_size = int(cell_size * 0.8)
        heart_image = pygame.transform.scale(original_heart, (new_size, new_size))
    except Exception as e:
        print(f"Warning: Could not load heart image: {e}")
        heart_image = None
    
    # 生成荆棘位置
    generate_thorn_positions()
    
    # 生成心形道具位置
    generate_heart_positions()
    
    # 加载清除药水图片
    try:
        original_clear = pygame.image.load('clear.png')
        new_size = int(cell_size * 0.8)
        clear_potion_image = pygame.transform.scale(original_clear, (new_size, new_size))
    except Exception as e:
        print(f"Warning: Could not load clear potion image: {e}")
        clear_potion_image = None
    
    # 生成药水位置
    generate_clear_potion_position()


def generate_thorn_positions():
    """生成荆棘位置"""
    global thorn_positions, thorns_exit_pos

    # 清空现有荆棘位置
    thorn_positions = []
    
    # 获取可用位置（排除起点、出口）
    available_positions = []
    occupied_positions = [(0, 0)]  # 起点
    
    if thorns_exit_pos:
        occupied_positions.append(thorns_exit_pos)
    
    # 收集可用位置
    for x in range(cols):
        for y in range(rows):
            if (x, y) not in occupied_positions:
                available_positions.append((x, y))
    
    # 随机选择位置放置荆棘
    num_thorns = min(7, len(available_positions))
    if available_positions:
        selected_positions = random.sample(available_positions, num_thorns)
        thorn_positions.extend(selected_positions)

def draw_thorns():
    """��制荆��、心形道具和清除药水"""
    global thorn_image, current_maze_type, clear_potion_image
    
    # 计算偏移量
    offset_x = (MAZE_SIZE - cols * cell_size) // 2
    offset_y = (MAZE_SIZE - rows * cell_size) // 2
    
    # 绘制荆棘
    for pos in thorn_positions:
        x = offset_x + pos[0] * cell_size
        y = offset_y + pos[1] * cell_size
        x += (cell_size - thorn_image.get_width()) // 2
        y += (cell_size - thorn_image.get_height()) // 2
        screen.blit(thorn_image, (x, y))
    
    # 绘制心形道具
    draw_hearts()
    
    # 绘制清除药水
    if clear_potion_pos and clear_potion_image:
        x = offset_x + clear_potion_pos[0] * cell_size
        y = offset_y + clear_potion_pos[1] * cell_size
        x += (cell_size - clear_potion_image.get_width()) // 2
        y += (cell_size - clear_potion_image.get_height()) // 2
        screen.blit(clear_potion_image, (x, y))

def switch_to_thorns_maze():
    """切换到荆棘迷宫"""
    global grid, current_maze_type, player, last_damage_time, thorns_start_time
   
    # 保存当前位置作为返回点
    player.entry_point = (player.x, player.y)
    
    # 初始化计时器
    last_damage_time = pygame.time.get_ticks()
    thorns_start_time = last_damage_time
    
    # 生成新的荆棘迷宫
    generate_thorns_maze()
    
    # 设置迷宫类型
    current_maze_type = "THORNS"
  
    # 重置玩家位置到起点
    player.x, player.y = 0, 0

def return_from_thorns_maze():
    """从荆棘迷宫返回任务迷宫"""
    global grid, current_maze_type, player, task_maze_order, thorns_maze_visited
    global endless_door_pos  # 添加这个全局变量
    
    # 标记荆棘迷宫已访问
    thorns_maze_visited = True
    
    # 清除荆棘迷宫入口位置
    endless_door_pos = None
    
    # 恢复任务迷宫
    grid = task_maze_grid
    current_maze_type = "TASK"
    
    # 玩家返回入口点
    if player.entry_point:
        player.x, player.y = player.entry_point
        # 如果entry_point不在task_maze_order中，添加它
        if player.entry_point not in task_maze_order:
            task_maze_order.append(player.entry_point)
        player.entry_point = None  # 清除入口点
    
    # 可以添加一个成功提示（可选）
    show_popup_message("成功通过荆棘迷宫！")

# 全局变量
thorns_maze_grid = None
thorns_exit_pos = None

# 在全局变量区域添加
thorns_maze_visited = False

# 在全局变量区域添加
thorn_positions = []  # 存储荆棘的位置
thorn_image = None   # 荆棘的图片

def check_thorn_collision():
    """检查是否碰到荆棘"""
    global thorn_positions, current_health
    
    current_pos = (player.x, player.y)
    if current_pos in thorn_positions:
        # 扣除生命值
        current_health = max(0, current_health - 1)
        
        # 移除被碰到的荆棘
        thorn_positions.remove(current_pos)
        
        # 播放受伤音效并显示闪烁效果
        if failure_sound:
            failure_sound.play()
        flash_screen()
        
        if current_health <= 0:
            return True
            
    return False

def flash_screen():
    """屏幕闪烁效果"""
    # 创建红色半透明遮罩
    flash = pygame.Surface((WIDTH, HEIGHT))
    flash.fill((255, 0, 0))
    flash.set_alpha(100)
    
    # 绘制遮罩
    screen.blit(flash, (0, 0))
    pygame.display.flip()
    
    # 等待一小段时间
    pygame.time.delay(100)

def generate_heart_positions():
    """生成心形道具位置"""
    global heart_positions, thorns_exit_pos, thorn_positions
    
    # 清空现有心形位置
    heart_positions = []
    
    # 获取可用位置(排除起点、出口、荆棘位置)
    available_positions = []
    occupied_positions = [(0, 0)]  # 起点
    
    if thorns_exit_pos:
        occupied_positions.append(thorns_exit_pos)
    
    # 添加荆棘位置到已占用列表
    occupied_positions.extend(thorn_positions)
    
    # 收集可用位置
    for x in range(cols):
        for y in range(rows):
            if (x, y) not in occupied_positions:
                available_positions.append((x, y))
    
    # 随机选择3个位置放置心形道具
    num_hearts = min(3, len(available_positions))
    if available_positions:
        selected_positions = random.sample(available_positions, num_hearts)
        heart_positions.extend(selected_positions)

def draw_hearts():
    """绘制心形道具"""
    global heart_image
    
    # 计算迷宫的实际偏移量
    offset_x = (MAZE_SIZE - cols * cell_size) // 2
    offset_y = (MAZE_SIZE - rows * cell_size) // 2
    
    for pos in heart_positions:
        # 计算心形道具的屏幕坐标
        x = offset_x + pos[0] * cell_size
        y = offset_y + pos[1] * cell_size
        
        # 居中显示心形图片
        x += (cell_size - heart_image.get_width()) // 2
        y += (cell_size - heart_image.get_height()) // 2
        
        screen.blit(heart_image, (x, y))

def check_thorn_collision():
   """检查是否碰到荆棘或心形道具"""
   global thorn_positions, heart_positions, current_health
   
   current_pos = (player.x, player.y)
   
   # 检查是否碰到心形道具
   if current_pos in heart_positions:
       # 回复生命值(不超过最大值)
       if current_health < MAX_HEALTH:
           current_health = min(MAX_HEALTH, current_health + 1)
           if success_sound:
               success_sound.play()
       # 移除被吃掉的心形道具
       heart_positions.remove(current_pos)
       return False
   
   # 检查是否碰到荆棘
   if current_pos in thorn_positions:
       current_health = max(0, current_health - 1)
       thorn_positions.remove(current_pos)
       if failure_sound:
           failure_sound.play()
       flash_screen()
       
       if current_health <= 0:
           return True
           
   return False

def generate_clear_potion_position():
    """生成清除药水位置"""
    global clear_potion_pos, thorns_exit_pos, thorn_positions, heart_positions
    
    # 获取可用位置(排除起点、出口、荆棘位置和心形道具位置)
    occupied_positions = [(0, 0)]  # 起点
    
    if thorns_exit_pos:
        occupied_positions.append(thorns_exit_pos)
    
    # 添加荆棘和心形道具位置到已占用列表
    occupied_positions.extend(thorn_positions)
    occupied_positions.extend(heart_positions)
    
    # 收集可用位置
    available_positions = []
    for x in range(cols):
        for y in range(rows):
            if (x, y) not in occupied_positions:
                available_positions.append((x, y))
    
    # 随机选择一个位置放置清除药水
    if available_positions:
        clear_potion_pos = random.choice(available_positions)
    else:
        clear_potion_pos = None

def generate_passing_doors():
    """生成传送门位置，确保两个传送门距离尽可能远"""
    global passing_door_positions, passing_door_image
    
    # 清空现有传送门位置
    passing_door_positions = []
    
    # 加载传送门图片
    try:
        original_door = pygame.image.load('passing_door.png')
        new_size = int(cell_size * 0.8)
        passing_door_image = pygame.transform.scale(original_door, (new_size, new_size))
    except pygame.error as e:
        print(f"Warning: Could not load passing door image: {e}")
        passing_door_image = None
        return
    
    # 获取可用位置（排除起点、终点和任务门位置）
    available_positions = []
    occupied_positions = [(0, 0), (cols-1, rows-1)]  # 起点和终点
    occupied_positions.extend(task_doors)  # 任务门位置
    
    # 收集可用位置
    for x in range(cols):
        for y in range(rows):
            if (x, y) not in occupied_positions:
                available_positions.append((x, y))
    
    if len(available_positions) < 2:
        return
        
    # 计算曼哈顿距离
    def manhattan_distance(pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    # 找到距离最远的两个点
    max_distance = 0
    best_pair = None
    
    # 使用堆优化搜索过程
    for i, pos1 in enumerate(available_positions):
        distances = []
        for pos2 in available_positions[i+1:]:
            dist = manhattan_distance(pos1, pos2)
            heapq.heappush(distances, (-dist, pos2))  # 使用负距离来创建最大堆
        
        if distances:
            dist, pos2 = heapq.heappop(distances)  # 获取最远的点
            dist = -dist  # 转换回正距离
            if dist > max_distance:
                max_distance = dist
                best_pair = (pos1, pos2)
    
    if best_pair:
        passing_door_positions.extend(best_pair)
def draw_passing_doors():
   """绘制传送门"""
   if not passing_door_image or current_maze_type != "NORMAL" or current_difficulty != "HARD":
       return
       
   # 计算迷宫的实际偏移量
   offset_x = (MAZE_SIZE - cols * cell_size) // 2
   offset_y = (MAZE_SIZE - rows * cell_size) // 2
   
   for pos in passing_door_positions:
       # 计算传送门的屏幕坐标
       x = offset_x + pos[0] * cell_size
       y = offset_y + pos[1] * cell_size
       
       # 居中显示传送门图片
       x += (cell_size - passing_door_image.get_width()) // 2
       y += (cell_size - passing_door_image.get_height()) // 2
       
       screen.blit(passing_door_image, (x, y))
def handle_teleport():
   """处理传送门传送"""
   global last_teleport_time
   
   if (current_maze_type != "NORMAL" or 
       current_difficulty != "HARD" or 
       len(passing_door_positions) != 2):
       return False
       
   current_pos = (player.x, player.y)
   current_time = pygame.time.get_ticks()
   
   # 检查是否在传送门位置且冷却时间已过
   if (current_pos in passing_door_positions and 
       current_time - last_teleport_time >= TELEPORT_COOLDOWN):
       
       # 确定目标传送门位置
       target_pos = passing_door_positions[1] if current_pos == passing_door_positions[0] else passing_door_positions[0]
       
       # 播放传送音效
       if coin_sound:  # 可以使用现有的音效,或添加新的传送音效
           coin_sound.play()
       
       # 传送玩家
       player.x, player.y = target_pos
       
       # 更新上次传送时间
       last_teleport_time = current_time
       
       # 添加传送特效
       flash_teleport_effect()
       return True
   
   return False
def flash_teleport_effect():
   """传送特效"""
   # 创建蓝色半透明遮罩
   flash = pygame.Surface((WIDTH, HEIGHT))
   flash.fill((0, 0, 255))  # 蓝色
   flash.set_alpha(100)
   
   # 绘制遮罩
   screen.blit(flash, (0, 0))
   pygame.display.flip()
   
   # 等待一小段时间
   pygame.time.delay(100)

if __name__ == "__main__":
    main()

