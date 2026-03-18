from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from random import randint, uniform
import urllib.request
import os

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
ground = Entity(model='plane', scale=(100, 1, 100), color=color.rgb(80, 80, 80), texture='white_cube', texture_scale=(100, 100), collider='box', enabled=False)

# 玩家（FPS 控制器）- 速度保持 12 不变
player = FirstPersonController(enabled=False, speed=12)

# 弹药系统
MAG_SIZE = 20  # 弹夹容量
bullets_in_mag = MAG_SIZE  # 当前子弹数
is_reloading = False  # 是否正在换弹

# 子弹列表
bullets = []
BULLET_SPEED = 500  # 子弹速度

# 弹药显示 - 左下角
ammo_text = Text(text=f'弹药：{bullets_in_mag}/{MAG_SIZE}', position=(-0.85, -0.45), scale=2, color=color.white, enabled=False)
reload_text = Text(text='按 R 换弹', position=(0, 0), scale=3, color=color.red, origin=(0, 0), enabled=False)

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
                          ignore=[player, gun_group, self])
        
        if hit_info.hit:
            if hit_info.entity in targets or hit_info.entity in target_bullseyes:
                # 找到并销毁靶子
                for t in targets:
                    if hit_info.entity == t or hit_info.entity == t.bullseye:
                        destroy(t)
                        targets.remove(t)
                        break
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
    """可移动的靶子 - 立着的圆形靶子"""
    def __init__(self, position, size, **kwargs):
        # 创建靶子主体（立着的圆盘）
        super().__init__(
            model='circle',  # 2D 圆形
            color=color.rgb(220, 50, 50),  # 鲜艳的红色
            scale=(size, size),
            position=position,
            collider='box',
            **kwargs
        )
        self.size = size
        self.move_direction = Vec3(randint(-1, 1), 0, randint(-1, 1)).normalized()
        self.move_speed = uniform(TARGET_SPEED_MIN, TARGET_SPEED_MAX)
        self.x_range = (-MOVE_RANGE_X, MOVE_RANGE_X)
        self.z_range = (-MOVE_RANGE_Z, MOVE_RANGE_Z)
        
        # 靶子支架（柱子）
        self.stand = Entity(parent=self, model='cube', color=color.rgb(100, 100, 100), 
                           scale=(0.2, 1, 0.2), position=(0, -0.5 - size/2, 0))
        
        # 靶心（白色）
        self.bullseye = Entity(parent=self, model='circle', color=color.white, 
                              scale=(size * 0.3, size * 0.3), position=(0, 0, 0.01))
        
        # 外圈（白色环）
        self.outer_ring = Entity(parent=self, model='ring', color=color.white, 
                                scale=(size * 0.7, size * 0.7), position=(0, 0, 0.02))
        
        # 设置 Y 轴旋转，让靶子面向玩家
        self.look_at(Vec3(0, 1, 0))
        
    def update(self):
        self.position += self.move_direction * self.move_speed * time.dt
        
        if self.position.x < self.x_range[0] or self.position.x > self.x_range[1]:
            self.move_direction = Vec3(-self.move_direction.x, 0, self.move_direction.z)
            self.position.x = max(self.x_range[0], min(self.position.x, self.x_range[1]))
        
        if self.position.z < self.z_range[0] or self.position.z > self.z_range[1]:
            self.move_direction = Vec3(self.move_direction.x, 0, -self.move_direction.z)
            self.position.z = max(self.z_range[0], min(self.position.z, self.z_range[1]))

# 枪模型组（用多个形状组合成更像枪的样子）
gun_group = Entity(parent=camera.ui, enabled=False)

# 枪身主体
gun_body = Entity(parent=gun_group, model='cube', color=color.rgb(60, 60, 60), 
                  scale=(0.15, 0.12, 0.8), position=(0.4, -0.35, 0))
# 枪管
gun_barrel = Entity(parent=gun_group, model='cube', color=color.rgb(40, 40, 40), 
                    scale=(0.06, 0.06, 0.4), position=(0.4, -0.32, 0.6))
# 握把
gun_grip = Entity(parent=gun_group, model='cube', color=color.rgb(50, 40, 30), 
                  scale=(0.1, 0.15, 0.12), position=(0.4, -0.48, -0.2))
# 弹夹
gun_mag = Entity(parent=gun_group, model='cube', color=color.rgb(30, 30, 30), 
                 scale=(0.08, 0.2, 0.1), position=(0.4, -0.55, 0.1))

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
    gun_group.enabled = True
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
    
    # 换弹动画 - 枪口向下
    gun_group.animate_rotation((-30, 0, 0), duration=0.5, curve=curve.linear)
    invoke(finish_reload, delay=1.5)

def finish_reload():
    """完成换弹"""
    global bullets_in_mag, is_reloading
    
    bullets_in_mag = MAG_SIZE
    is_reloading = False
    reload_text.enabled = False
    
    # 枪口恢复
    gun_group.animate_rotation((0, 0, 0), duration=0.3, curve=curve.linear)
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
        
        # 枪口后坐力动画
        gun_group.animate_position((0.4, -0.3, 0), duration=0.05, curve=curve.linear)
        gun_group.animate_position((0.4, -0.35, 0), duration=0.1, curve=curve.linear)
        
        # 获取枪口世界位置
        muzzle_pos = get_muzzle_position()
        
        # 创建子弹（从枪口位置发射）
        bullet = Bullet(position=muzzle_pos, direction=camera.forward)
        bullets.append(bullet)

# 开始按钮点击事件
start_button.on_click = start_game

# 运行
app.run()
