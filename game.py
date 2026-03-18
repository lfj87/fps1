from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from random import randint, uniform

app = Ursina()

# ==================== 开始界面 ====================
game_started = False

# 开始界面背景
start_bg = Entity(model='quad', color=color.dark_gray, scale=(100, 100), position=(0, 0, 50))

# 游戏标题
title_text = Text(text='FPS 射击游戏', position=(0, 0.3), scale=4, origin=(0, 0), color=color.yellow)

# 开始按钮
start_button = Button(
    text='开始游戏',
    color=color.blue,
    scale=(0.3, 0.1),
    position=(0, 0),
    text_origin=(0, 0),
    text_color=color.white,
    text_scale=2
)

# 操作说明
instructions = Text(
    text='''
操作说明:
W/A/S/D - 移动
鼠标 - 瞄准
左键 - 射击
R - 换弹夹
空格 - 跳跃
    ''',
    position=(-0.7, -0.3),
    scale=1.5,
    color=color.white,
    origin=(0, 0)
)

# 提示文字
hint_text = Text(text='点击"开始游戏"按钮开始', position=(0, -0.45), scale=1.5, origin=(0, 0), color=color.green)

# ==================== 游戏场景 ====================

# 天空和地面
Sky(enabled=False)
ground = Entity(model='plane', scale=(100, 1, 100), color=color.gray, texture='white_cube', texture_scale=(100, 100), collider='box', enabled=False)

# 玩家（FPS 控制器）
player = FirstPersonController(enabled=False)

# 枪
gun = Entity(parent=camera.ui, model='cube', color=color.black, scale=(0.4, 0.2, 1), position=(0.5, -0.4), rotation=(-5, -5, 0), enabled=False)

# 弹药系统
MAG_SIZE = 20  # 弹夹容量
bullets_in_mag = MAG_SIZE  # 当前子弹数
is_reloading = False  # 是否正在换弹

# 弹药显示
ammo_text = Text(text=f'弹药：{bullets_in_mag}/{MAG_SIZE}', position=(-0.85, 0.45), scale=2, color=color.white, enabled=False)
reload_text = Text(text='按 R 换弹', position=(0, 0), scale=3, color=color.red, origin=(0, 0), enabled=False)

# 子弹列表
bullets = []
BULLET_SPEED = 500  # 子弹速度

def get_muzzle_position():
    """获取枪口的世界坐标位置"""
    muzzle_world_pos = camera.world_position + camera.forward * 1.5
    right = camera.right * 0.3
    down = camera.down * 0.2
    muzzle_world_pos = muzzle_world_pos + right + down
    return muzzle_world_pos

class Bullet(Entity):
    def __init__(self, position, direction, **kwargs):
        super().__init__(
            model='sphere',
            color=color.yellow,
            scale=0.15,
            position=position,
            **kwargs
        )
        self.direction = direction.normalized()
        self.speed = BULLET_SPEED
        self.lifetime = 2
        
    def update(self):
        self.position += self.direction * self.speed * time.dt
        self.lifetime -= time.dt
        
        hit_info = raycast(self.position - self.direction * self.speed * time.dt, 
                          self.direction, 
                          distance=self.speed * time.dt, 
                          ignore=[player, gun, self])
        
        if hit_info.hit:
            if hit_info.entity in targets:
                destroy(hit_info.entity)
                targets.remove(hit_info.entity)
                # 生成新靶子
                create_target()
            destroy(self)
            if self in bullets:
                bullets.remove(self)
            return
        
        if self.lifetime <= 0:
            destroy(self)
            if self in bullets:
                bullets.remove(self)

# 靶子列表
targets = []
TARGET_SIZE_MIN = 1.0
TARGET_SIZE_MAX = 3.0
TARGET_SPEED_MIN = 2
TARGET_SPEED_MAX = 8
MOVE_RANGE_X = 40
MOVE_RANGE_Z = 40

class MovingTarget(Entity):
    """可移动的靶子"""
    def __init__(self, position, size, **kwargs):
        super().__init__(
            model='cube',
            color=color.red,
            scale=(size, size, 0.2),
            position=position,
            collider='box',
            **kwargs
        )
        self.size = size
        self.move_direction = Vec3(randint(-1, 1), 0, randint(-1, 1)).normalized()
        self.move_speed = uniform(TARGET_SPEED_MIN, TARGET_SPEED_MAX)
        self.x_range = (-MOVE_RANGE_X, MOVE_RANGE_X)
        self.z_range = (-MOVE_RANGE_Z, MOVE_RANGE_Z)
        
    def update(self):
        self.position += self.move_direction * self.move_speed * time.dt
        
        if self.position.x < self.x_range[0] or self.position.x > self.x_range[1]:
            self.move_direction = Vec3(-self.move_direction.x, 0, self.move_direction.z)
            self.position.x = max(self.x_range[0], min(self.position.x, self.x_range[1]))
        
        if self.position.z < self.z_range[0] or self.position.z > self.z_range[1]:
            self.move_direction = Vec3(self.move_direction.x, 0, -self.move_direction.z)
            self.position.z = max(self.z_range[0], min(self.position.z, self.z_range[1]))

def create_target():
    """随机位置、随机大小生成移动靶子"""
    x = randint(-MOVE_RANGE_X, MOVE_RANGE_X)
    z = randint(-MOVE_RANGE_Z, MOVE_RANGE_Z)
    size = uniform(TARGET_SIZE_MIN, TARGET_SIZE_MAX)
    target = MovingTarget(position=(x, 1, z), size=size)
    targets.append(target)

def start_game():
    """开始游戏"""
    global game_started, bullets_in_mag
    
    if game_started:
        return
    
    game_started = True
    
    # 隐藏开始界面
    start_bg.enabled = False
    title_text.enabled = False
    start_button.enabled = False
    instructions.enabled = False
    hint_text.enabled = False
    
    # 显示游戏场景
    Sky(enabled=True)
    ground.enabled = True
    player.enabled = True
    gun.enabled = True
    ammo_text.enabled = True
    
    # 重置弹药
    bullets_in_mag = MAG_SIZE
    ammo_text.text = f'弹药：{bullets_in_mag}/{MAG_SIZE}'
    
    # 生成靶子
    for _ in range(5):
        create_target()
    
    # 锁定鼠标
    window.exit_button.visible = False
    application.pause_on_focus_lost = False

def reload():
    """换弹夹"""
    global bullets_in_mag, is_reloading
    
    if is_reloading:
        return
    
    if bullets_in_mag == MAG_SIZE:
        return
    
    is_reloading = True
    reload_text.enabled = True
    
    gun.animate_rotation((-45, -5, 0), duration=0.5, curve=curve.linear)
    invoke(finish_reload, delay=1.5)

def finish_reload():
    """完成换弹"""
    global bullets_in_mag, is_reloading
    
    bullets_in_mag = MAG_SIZE
    is_reloading = False
    reload_text.enabled = False
    
    gun.animate_rotation((-5, -5, 0), duration=0.3, curve=curve.linear)
    ammo_text.text = f'弹药：{bullets_in_mag}/{MAG_SIZE}'

# 输入处理
def input(key):
    global bullets_in_mag
    
    if not game_started:
        return
    
    if key == 'r':
        reload()
        return
    
    if key == 'left mouse down':
        if is_reloading:
            return
        
        if bullets_in_mag <= 0:
            ammo_text.color = color.red
            invoke(setattr, ammo_text, 'color', color.white, delay=0.3)
            return
        
        bullets_in_mag -= 1
        ammo_text.text = f'弹药：{bullets_in_mag}/{MAG_SIZE}'
        
        gun.animate_position((0.5, -0.35), duration=0.05, curve=curve.linear)
        gun.animate_position((0.5, -0.4), duration=0.1, curve=curve.linear)
        
        muzzle_pos = get_muzzle_position()
        bullet = Bullet(position=muzzle_pos, direction=camera.forward)
        bullets.append(bullet)

# 开始按钮点击事件
start_button.on_click = start_game

# 运行
app.run()
