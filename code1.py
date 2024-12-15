import pygame
import random
import tkinter as tk
from tkinter import messagebox
import time
import threading
from tkinter import simpledialog
import operator


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

# 加载并缩放star图片
try:
    star_image = pygame.image.load('star.png')
    small_task_image = pygame.image.load('small_task.png')
    big_task_image = pygame.image.load('big_task.png')
    lock_image = pygame.image.load('lock.png')
    open_image = pygame.image.load('open.png')
    light_image = pygame.image.load('light.png')  # 添加light图片加载
    
    new_size = int(cell_size * 0.8)  # 缩小到单元格的80%
    star_image = pygame.transform.scale(star_image, (new_size, new_size))
    small_task_image = pygame.transform.scale(small_task_image, (new_size, new_size))
    big_task_image = pygame.transform.scale(big_task_image, (new_size, new_size))
    lock_image = pygame.transform.scale(lock_image, (new_size, new_size))
    open_image = pygame.transform.scale(open_image, (new_size, new_size))
    light_image = pygame.transform.scale(light_image, (new_size, new_size))  # 缩放light图片
except pygame.error as e:
    print(f"Warning: Could not load image: {e}")
    star_image = None
    small_task_image = None
    big_task_image = None
    lock_image = None
    open_image = None
    light_image = None

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
    pygame.mixer.music.load('bgm.mp3')  # 加载BGM文件
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
blue_squares = []
small_tasks = []  # 存储小任务位置
big_tasks = []  # 存储大任务位置
task_timer = None # 计时器
task_exit_pos = None  # 存储任务迷宫的出口位置
task_maze_order = []  # 记录进入任务迷宫的顺序
current_difficulty = "EASY"  # 默认难度
light_position = None  # 存储light的位置

# 定义状态文本（使用英文作为备选）
MAZE_STATES = {
    "NORMAL": "Normal Maze",  # 如果中文无法显示就用英文
    "TASK": "Task Maze {}"    # 任务迷宫会显示编号
}

# 添加新的全局变量
DIFFICULTY_SETTINGS = {
    "EASY": 5,    # 10x10 迷宫
    "MEDIUM": 10,  # 15x15 迷宫
    "HARD": 15     # 20x20 迷宫
}

# 添加难度相关的配置常量
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

# 添加保存和加载记录的函数
def save_records():
    """保存通关记录到文件"""
    try:
        with open('completion_records.txt', 'w') as f:
            for difficulty, count in COMPLETION_RECORDS.items():
                f.write(f"{difficulty}:{count}\n")
    except Exception as e:
        print(f"Error saving records: {e}")

def load_records():
    """从文件加载通关记录"""
    try:
        with open('completion_records.txt', 'r') as f:
            for line in f:
                difficulty, count = line.strip().split(':')
                COMPLETION_RECORDS[difficulty] = int(count)
    except FileNotFoundError:
        # 如果文件不存在，使用默认值
        pass
    except Exception as e:
        print(f"Error loading records: {e}")

# 生成两个随机蓝色方块
def generate_blue_squares():
    """根据难度生成对应数量的蓝色方块"""
    global blue_squares
    blue_squares = []
    
    # 获取当前难度的配置
    current_difficulty = get_current_difficulty()
    num_stars = DIFFICULTY_CONFIGS[current_difficulty]["stars"]
    
    # 获取可用位置（除起点和终点）
    available_positions = []
    for x in range(cols):
        for y in range(rows):
            if (x, y) != (0, 0) and (x, y) != (cols-1, rows-1):
                available_positions.append((x, y))
    
    # 随机选择位置
    if len(available_positions) >= num_stars:
        selected_positions = random.sample(available_positions, num_stars)
        blue_squares = selected_positions

# 迷宫单元格类
class Cell:
    def __init__(self, x, y): # 初始化方法
        self.x = x
        self.y = y
        self.walls = [True, True, True, True]  # 上右下左
        self.visited = False
        
    def draw(self, screen):
        # 计算实际绘制位置（居中显示）
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
    # 根据相对位置移除墙壁
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
def generate_maze():
    global grid
    stack = []
    current = grid[0][0]
    current.visited = True
    
    while True:
        neighbors = check_neighbors(current)
        if neighbors:
            next_cell = random.choice(neighbors)
            next_cell.visited = True
            stack.append(current)
            remove_walls(current, next_cell)
            current = next_cell
        elif stack:
            current = stack.pop()
        else:
            break
    
    # 重置所有单元格的visited属性，下次生成准备
    for x in range(cols):
        for y in range(rows):
            grid[x][y].visited = False

# 绘制出
def draw_exit(screen):
    """绘制出口"""
    offset_x = (MAZE_SIZE - cols * cell_size) // 2
    offset_y = (MAZE_SIZE - rows * cell_size) // 2
    
    if current_maze_type == "NORMAL":
        # 普通迷宫的出口在右下角
        x = offset_x + (cols - 1) * cell_size
        y = offset_y + (rows - 1) * cell_size
        
        # 检查是否完成所有任务迷宫
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
                # 计算居中位置
                img_x = x + (cell_size - lock_image.get_width()) // 2
                img_y = y + (cell_size - lock_image.get_height()) // 2
                screen.blit(lock_image, (img_x, img_y))
            else:
                pygame.draw.rect(screen, RED, (x, y, cell_size, cell_size))
    else:
        # 任务迷宫的出口
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
            else:
                pygame.draw.rect(screen, RED, (x, y, cell_size, cell_size))

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
        # 确保玩家不会移动到信息区域
        new_x, new_y = self.x, self.y
        
        if direction == "UP" and self.y > 0 and not grid[self.x][self.y].walls[0]:
            new_y -= 1
        if direction == "RIGHT" and self.x < cols - 1 and not grid[self.x][self.y].walls[1]:
            new_x += 1
            self.facing_right = True
        if direction == "DOWN" and self.y < rows - 1 and not grid[self.x][self.y].walls[2]:
            new_y += 1
        if direction == "LEFT" and self.x > 0 and not grid[self.x][self.y].walls[3]:
            new_x -= 1
            self.facing_right = False
            
        # 检查新位置是否在迷宫区域内
        if new_x * cell_size < MAZE_SIZE and new_y * cell_size < MAZE_SIZE:
            self.x, self.y = new_x, new_y

    def draw(self, screen):
        # 计算实际绘制位置（居中显示）
        offset_x = (MAZE_SIZE - cols * cell_size) // 2
        offset_y = (MAZE_SIZE - rows * cell_size) // 2
        x = offset_x + self.x * cell_size + (cell_size - self.image_width) // 2
        y = offset_y + self.y * cell_size + (cell_size - self.image_height) // 2
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
    global grid, current_maze_type, task_maze_grid, player, blue_squares, task_exit_pos, light_position
    
    # 记录任务迷宫顺序
    entry_pos = (player.x, player.y)
    if entry_pos not in task_maze_order:
        task_maze_order.append(entry_pos)
    
    # 记录进入点
    player.entry_point = (player.x, player.y)
    # 从蓝色方块列表中移除当前入口
    blue_squares.remove((player.x, player.y))
    
    # 创建新的任务迷宫网格
    task_maze_grid = [[Cell(x, y) for y in range(rows)] for x in range(cols)]
    grid = task_maze_grid
    current_maze_type = "TASK"
    
    # 重新生成迷宫
    generate_task_maze()
    
    # 重置玩家位置到起点
    player.x = 0
    player.y = 0
    
    # 随机生成出口位置（不能是起点）
    while True:
        exit_x = random.randint(0, cols-1)
        exit_y = random.randint(0, rows-1)
        if (exit_x, exit_y) != (0, 0):  # 确保出口不在起点
            task_exit_pos = (exit_x, exit_y)
            break
    
    # 在确定出口位置后生成任务位置
    generate_task_positions()
    
    # 如果是第一个任务迷宫，有80%的概率生成light
    if len(task_maze_order) == 1:  # 第一个任务迷宫
        light_position = None  # 重置light位置
        if random.random() < 0.8:  # 80%的概率
            # 获取所有任务位置
            task_positions = [(task.x, task.y) for task in small_tasks]
            if big_tasks:
                task_positions.append((big_tasks[0].x, big_tasks[0].y))
            
            # 随机选择一个位置放置light（不能是起点、终点或任务位置）
            available_positions = [(x, y) for x in range(cols) for y in range(rows)
                                 if (x, y) != (0, 0)  # 不是起点
                                 and (x, y) != task_exit_pos  # 不是终点
                                 and (x, y) not in task_positions]  # 不是任务位置
            
            if available_positions:
                light_position = random.choice(available_positions)
    else:
        light_position = None  # 其他任务迷宫没有light
    
    if enter_sound:
        enter_sound.play()

def generate_task_maze():
    global grid
    # 确保所有墙壁都是封闭的
    for x in range(cols):
        for y in range(rows):
            grid[x][y].walls = [True, True, True, True]
            grid[x][y].visited = False
    
    stack = []
    current = grid[0][0]
    current.visited = True
    
    # 使用同的随机种子生成新迷宫
    random.seed()  # 使用系间作为新的随机种子
    
    while True:
        neighbors = check_neighbors(current)
        if neighbors:
            # 增加向右和向下的权重，使迷宫更倾向于这些方向
            weights = []
            for neighbor in neighbors:
                if neighbor.x > current.x or neighbor.y > current.y:
                    weights.append(2)  # 向右或向下的权重更大
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
    global grid, current_maze_type, player
    print("返回普通迷宫")
    
    # 恢复原始迷宫
    grid = normal_maze_grid
    current_maze_type = "NORMAL"
    
    # 将玩家传送回入口位置
    if player.entry_point:
        player.x, player.y = player.entry_point

# 添加显示提示信息的函数
def show_message(screen, message, color=WHITE):
    font = pygame.font.SysFont('Arial', 36)
    text = font.render(message, True, color)
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    
    # 创建一个半透明的背景
    background = pygame.Surface((text_rect.width + 20, text_rect.height + 20))
    background.fill(BLACK)
    background.set_alpha(200)
    background_rect = background.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    
    # 绘制背景和文本
    screen.blit(background, background_rect)
    screen.blit(text, text_rect)
    pygame.display.update()
    pygame.time.delay(2000)  # 显示2秒

# 添加显示消息框函数
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
            # 确保除法结果为整
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
    # 清空现有任务
    small_tasks.clear()
    big_tasks.clear()
    
    # 获取有可用位置（除起点和出口）
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
    root = tk.Tk()
    root.withdraw()
    
    # 生成问题
    question, correct_answer = Task(0, 0).generate_math_question()
    
    if coin_sound:
        coin_sound.play()
    
    try:
        answer = simpledialog.askfloat("数学题", f"{question} = ?", parent=root)
        if answer is not None:  # 用户输入了答案
            if abs(answer - correct_answer) < 0.01:  # 考虑浮点数误差
                if success_sound:
                    success_sound.play()
                return True
            else:
                if failure_sound:
                    failure_sound.play()
                    root.bell()  # 禁用系统声音
                    root.after(1)  # 等待一下以确保声音被禁用
                messagebox.showinfo("结果", f"回答错误！正确答案是 {correct_answer}")
                return False
        else:  # 用户点击取消
            return False
    finally:
        root.destroy()

def relocate_task(task):
    """重新定位单个任务的位置"""
    # 获取所有可用位置（排除起点、出口和其他任务的位置）
    available_positions = []
    occupied_positions = [(0, 0)]  # 起点
    
    # 添加任务迷宫出口到已占用列表
    if task_exit_pos:
        occupied_positions.append(task_exit_pos)
    
    # 添加其他任务的位置到已占用列表
    for small_task in small_tasks:
        if small_task != task:  # 不包括当前任务
            occupied_positions.append((small_task.x, small_task.y))
    if big_tasks and task not in big_tasks:
        occupied_positions.append((big_tasks[0].x, big_tasks[0].y))
    
    # 收集所有可用位置
    for x in range(cols):
        for y in range(rows):
            if (x, y) not in occupied_positions:
                available_positions.append((x, y))
    
    # 随机选择新位置
    if available_positions:
        new_pos = random.choice(available_positions)
        task.x, task.y = new_pos

def show_reaction_task():
    root = tk.Tk()
    root.title("反应测试")
    root.geometry("300x200")
    
    result = {'success': False}
    timer = {'start': None}
    
    def handle_click():
        if timer['start'] is None:
            timer['start'] = time.time()
            button.config(text="再次点击！")
            label.config(text="请在第5秒再次击按钮")
        else:
            end_time = time.time()
            time_diff = end_time - timer['start']
            if 4 <= time_diff <= 6:
                if success_sound:
                    success_sound.play()
                    root.bell()  # 禁用系统声音
                    root.after(1)
                messagebox.showinfo("结果", f"成功！你和第5秒的时间差仅为：{time_diff-5:.3f}秒")
                result['success'] = True
            else:
                if failure_sound:
                    failure_sound.play()
                    root.bell()  # 禁用系统声音
                    root.after(1)
                messagebox.showinfo("结果", f"失败！你和第5秒的时间差为：{time_diff-5:.3f}秒\n需要在1秒范围内")
            root.quit()
    
    label = tk.Label(root, text="点击按钮后，你需要在第5秒再次点击按钮\n若时间差在1秒内算通过", font=('Arial', 12))
    label.pack(pady=20)
    
    button = tk.Button(root, text="点击开始！", command=handle_click)
    button.pack(pady=10)
    
    root.mainloop()
    root.destroy()  # 在mainloop之后销毁窗口
    return result['success']

def check_task_completion():
    """检查任务完成情况"""
    # 获取当前难度的配置
    current_difficulty = get_current_difficulty()
    required_small_tasks = DIFFICULTY_CONFIGS[current_difficulty]["small_tasks"]
    required_big_tasks = DIFFICULTY_CONFIGS[current_difficulty]["big_tasks"]
    
    # 检查小任务完成数量
    small_tasks_completed = sum(1 for task in small_tasks if task.completed)
    # 检查大任务完成数量
    big_tasks_completed = sum(1 for task in big_tasks if task.completed)
    
    return small_tasks_completed >= required_small_tasks or big_tasks_completed >= required_big_tasks

def show_task_progress():
    """显示任务进度"""
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
    global small_tasks, big_tasks, player
    
    # 检查是否到达终点
    if (x, y) == task_exit_pos:
        # 只在第一次到达出口时检查（不是从出口位置移动）
        if last_position != task_exit_pos:
            if check_task_completion():
                # 任务已完成，直接返回普通迷宫，不显示提示
                return_to_normal_maze()
                return False
            else:
                # 任务未完成，显示提示
                show_task_progress()
        return False  # 允许移动
    
    # 检查小任务
    for task in small_tasks:
        if (x, y) == (task.x, task.y) and not task.completed:
            if coin_sound:  # 添加触碰音效
                coin_sound.play()
            if show_math_task():
                task.completed = True
            else:
                relocate_task(task)
            return True
            
    # 检查大任务
    if big_tasks and (x, y) == (big_tasks[0].x, big_tasks[0].y) and not big_tasks[0].completed:
        if coin_sound:  # 添加触碰音效
                coin_sound.play()
        if show_reaction_task():
            big_tasks[0].completed = True
        else:
            relocate_task(big_tasks[0])
        return True
    
    return False

def draw_tasks():
    """绘制任务方块"""
    offset_x = (MAZE_SIZE - cols * cell_size) // 2
    offset_y = (MAZE_SIZE - rows * cell_size) // 2
    
    # 绘制light（如果存在）
    if light_position and light_image:
        x = offset_x + light_position[0] * cell_size + (cell_size - light_image.get_width()) // 2
        y = offset_y + light_position[1] * cell_size + (cell_size - light_image.get_height()) // 2
        screen.blit(light_image, (x, y))
    
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
    
    # 绘制大任务
    if big_tasks and not big_tasks[0].completed:
        x = offset_x + big_tasks[0].x * cell_size + (cell_size - big_task_image.get_width()) // 2
        y = offset_y + big_tasks[0].y * cell_size + (cell_size - big_task_image.get_height()) // 2
        if big_task_image:
            screen.blit(big_task_image, (x, y))
        else:
            pygame.draw.rect(screen, RED, (offset_x + big_tasks[0].x * cell_size,
                                         offset_y + big_tasks[0].y * cell_size,
                                         cell_size, cell_size))

def check_all_task_mazes_completed():
    """检查是否完成了所有任务迷宫"""
    # 检查是否还有未访问的蓝色方块
    return len(blue_squares) == 0

def show_remaining_tasks():
    """显示剩余的任务迷宫数"""
    if unacceptable_sound and len(blue_squares) > 0:
        unacceptable_sound.play()
    remaining = len(blue_squares)
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
    
    # 获取当前难度的配置
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
        remaining_stars = len(blue_squares)
        mission_text = font.render(f"Mission remaining: {remaining_stars}/{required_stars}", True, WHITE)
        text_rect = mission_text.get_rect()
        text_rect.centerx = MAZE_SIZE + INFO_WIDTH//2
        text_rect.y = 100
        screen.blit(mission_text, text_rect)
        
    elif current_maze_type == "TASK":
        # 显示当前任务迷宫编号
        entry_pos = player.entry_point
        task_number = task_maze_order.index(entry_pos) + 1
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

def draw_start_menu():
    """绘制开始菜单"""
    # 加载并缩放背景图片以适应窗口大小
    try:
        background = pygame.image.load('background.jpg')
        background = pygame.transform.scale(background, (WIDTH, HEIGHT))
        screen.blit(background, (0, 0))
    except pygame.error as e:
        print(f"Warning: Could not load background image: {e}")
        screen.fill(BLACK)  # 如果加载失败则使用黑色背景
    
    font = pygame.font.SysFont('arial', 36)
    title_font = pygame.font.SysFont('arial', 48)
    
    # 绘制半透明的黑色遮罩，使文字更容易阅读
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.fill(BLACK)
    overlay.set_alpha(128)  # 设置透明度 (0-255)
    screen.blit(overlay, (0, 0))
    
    # 绘制标题 - 将标题位置改为 HEIGHT//4 使其上移
    title = title_font.render("MAZE GAME", True, WHITE)
    title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//4))
    screen.blit(title, title_rect)
    
    # 绘制难度选项
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
    record_y = HEIGHT - 35  # 调整到距离底部5像素（标题）
    
    # 绘制记录标题
    title_text = font.render("Completion Records:", True, WHITE)
    screen.blit(title_text, (WIDTH - 350, record_y - 30))  # 距离右边350像素，上移30像素
    
    # 在标题下方横向显示所有记录，确保最后一行距离底部5像素
    for i, difficulty in enumerate(["EASY", "MEDIUM", "HARD"]):
        record_text = font.render(f"{difficulty}: {COMPLETION_RECORDS[difficulty]}", True, WHITE)
        screen.blit(record_text, (WIDTH - 350 + i * 100, record_y))  # 与标题左对齐，最终距离底部5像素
    
    return buttons

def show_start_menu():
    """显示开始菜单并返回选择的难度"""
    global cols, rows, cell_size, star_image, small_task_image, big_task_image, lock_image, open_image, current_difficulty
    
    # 播放菜单BGM
    try:
        pygame.mixer.music.load('bgm_menu.mp3')
        pygame.mixer.music.set_volume(0.3)  # 设置菜单BGM音量
        pygame.mixer.music.play(-1)  # 循环播放
    except pygame.error as e:
        print(f"Warning: Could not play menu BGM: {e}")
    
    buttons = draw_start_menu()
    pygame.display.flip()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
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
                            original_star = pygame.image.load('star.png')
                            original_small_task = pygame.image.load('small_task.png')
                            original_big_task = pygame.image.load('big_task.png')
                            original_lock = pygame.image.load('lock.png')
                            original_open = pygame.image.load('open.png')
                            
                            new_size = int(cell_size * 0.8)  # 缩小到单元格的80%
                            star_image = pygame.transform.scale(original_star, (new_size, new_size))
                            small_task_image = pygame.transform.scale(original_small_task, (new_size, new_size))
                            big_task_image = pygame.transform.scale(original_big_task, (new_size, new_size))
                            lock_image = pygame.transform.scale(original_lock, (new_size, new_size))
                            open_image = pygame.transform.scale(original_open, (new_size, new_size))
                        except pygame.error as e:
                            print(f"Warning: Could not load image: {e}")
                            star_image = None
                            small_task_image = None
                            big_task_image = None
                            lock_image = None
                            open_image = None
                            
                        return
        
        # 重新绘菜单（包括背景）
        buttons = draw_start_menu()
        
        # 绘制按钮
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
    button_y = HEIGHT - 100  # 距离底部100像素
    
    button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
    
    # 检查鼠标悬停
    if button_rect.collidepoint(pygame.mouse.get_pos()):
        pygame.draw.rect(screen, (100, 100, 100), button_rect)
    else:
        pygame.draw.rect(screen, (50, 50, 50), button_rect)
    
    pygame.draw.rect(screen, WHITE, button_rect, 2)  # 边框
    
    # 绘制文本
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

# 添加新的函数用于寻找路
def find_path_to_exit():
    """使用BFS寻找到出口的路径"""
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

# 添加自动寻路动画函数
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
        
        # 绘制返回钮和自动寻路按钮
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
    button_y = HEIGHT - 160  # 在返回按钮上方
    
    button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
    
    # 检查鼠标悬停
    if button_rect.collidepoint(pygame.mouse.get_pos()):
        pygame.draw.rect(screen, (100, 100, 100), button_rect)
    else:
        pygame.draw.rect(screen, (50, 50, 50), button_rect)
    
    pygame.draw.rect(screen, WHITE, button_rect, 2)  # 边框
    
    # 绘制按钮本
    text = font.render('Auto Path', True, WHITE)
    text_rect = text.get_rect(center=button_rect.center)
    screen.blit(text, text_rect)
    
    return button_rect

def get_current_difficulty():
    """取当前游戏难度"""
    global current_difficulty
    return current_difficulty

# 主循环
def main():
    global grid, normal_maze_grid, player, current_maze_type, task_maze_order
    
    # 加载通关记录
    load_records()
    
    while True:  # 外层循环处理游戏重启
        # 显示开始菜单
        show_start_menu()
        
        # 开始播放BGM
        try:
            pygame.mixer.music.play(-1)  # -1表示无限循环播放
        except:
            print("Warning: Could not play BGM")
        
        # 初始化游戏
        grid = [[Cell(x, y) for y in range(rows)] for x in range(cols)]
        normal_maze_grid = grid
        generate_maze()
        generate_blue_squares()
        player = Player()
        current_maze_type = "NORMAL"
        task_maze_order = []
        
        # 游戏主循环
        running = True
        while running:
            screen.fill(BLACK)
            pygame.draw.rect(screen, (30, 30, 30), (MAZE_SIZE, 0, INFO_WIDTH, HEIGHT))
            
            # 绘制游戏元素
            for x in range(cols):
                for y in range(rows):
                    grid[x][y].draw(screen)
            
            draw_exit(screen)
            
            if current_maze_type == "NORMAL":
                for (bx, by) in blue_squares:
                    offset_x = (MAZE_SIZE - cols * cell_size) // 2
                    offset_y = (MAZE_SIZE - rows * cell_size) // 2
                    if star_image:
                        # 计算居中位置
                        x = offset_x + bx * cell_size + (cell_size - star_image.get_width()) // 2
                        y = offset_y + by * cell_size + (cell_size - star_image.get_height()) // 2
                        screen.blit(star_image, (x, y))
                    else:
                        # 如果图片加载失败,使用蓝色方块作为后备
                        pygame.draw.rect(screen, BLUE, (offset_x + bx * cell_size, 
                                                      offset_y + by * cell_size, 
                                                      cell_size, cell_size))
            elif current_maze_type == "TASK":
                draw_tasks()
            
            player.draw(screen)
            draw_status_panel()
            
            # 添加这两行，确保绘制两个按钮
            draw_auto_path_button()  # 先绘制自动寻路按钮
            draw_back_button()       # 再绘制返回按钮
            
            pygame.display.flip()
            
            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # 检查是否点击了Back按钮
                    back_button_rect = draw_back_button()
                    if back_button_rect.collidepoint(event.pos):
                        if show_confirmation_dialog():
                            running = False
                            break
                
                    # 检查自动寻路按钮点击
                    auto_path_button_rect = draw_auto_path_button()
                    if auto_path_button_rect.collidepoint(event.pos):
                        path = find_path_to_exit()
                        if path:
                            auto_path_animation(path)
                
                # 处理键盘事件
                if event.type == pygame.KEYDOWN:
                    last_position = (player.x, player.y)
                    if event.key == pygame.K_UP:
                        player.move("UP")
                    if event.key == pygame.K_RIGHT:
                        player.move("RIGHT")
                    if event.key == pygame.K_DOWN:
                        player.move("DOWN")
                    if event.key == pygame.K_LEFT:
                        player.move("LEFT")
                    
                    # 检查是否到达蓝色方块（普通迷宫中）
                    if current_maze_type == "NORMAL" and (player.x, player.y) in blue_squares:
                        switch_to_task_maze()
                    
                    # 检查是否到达终点
                    if current_maze_type == "NORMAL" and player.x == cols-1 and player.y == rows-1:
                        # 只在第一次到达终点时检查
                        if last_position != (cols-1, rows-1):
                            if check_all_task_mazes_completed():
                                show_success(screen)
                                running = False
                                break
                            else:
                                show_remaining_tasks()
                    
                    # 在任务迷宫中处理任务碰撞
                    if current_maze_type == "TASK":
                        if handle_task_collision(player.x, player.y, last_position):
                            # 只有在任务未完成时才回到上一个位置
                            if not check_task_completion():
                                player.x, player.y = last_position
            
            # ... 其他游戏逻辑代码 ...

        # 在游戏结束时停止BGM
        pygame.mixer.music.stop()

if __name__ == "__main__":
    main()
