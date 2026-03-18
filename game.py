from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from random import randint, uniform

app = Ursina()

# 天空和地面
Sky()
ground = Entity(model='plane', scale=(100, 1, 100), color=color.gray, texture='white_cube', texture_scale=(100, 100), collider='box')

# 玩家（FPS 控制器）
player = FirstPersonController(speed=12, position=(0, 2, 0))

# 枪
gun = Entity(parent=camera.ui, model='cube', color=color.black, scale=(0.4, 0.2, 1), position=(0.5, -0.4), rotation=(-5, -5, 0))

# 枪口位置标记（用于计算子弹发射点）
muzzle_flash = Entity(parent=camera.ui, model='quad', color=color.yellow, scale=0.1, position=(0.5, -0.3, 2), enabled=False)

# 弹药系统
MAG_SIZE = 20  # 弹夹容量
bullets_in_mag = MAG_SIZE  # 当前子弹数
is_reloading = False  # 是否正在换弹

# 弹药显示
ammo_text = Text(text=f'弹药：{bullets_in_mag}/{MAG_SIZE}', position=(-0.85, 0.45), scale=2, color=color.white)
reload_text = Text(text='按 R 换弹', position=(0, 0), scale=3, color=color.red, origin=(0, 0))
reload_text.enabled = False

# 子弹列表
bullets = []
BULLET_SPEED = 500  # 子弹速度（原速度 10 倍）

def get_muzzle_position():
    """获取枪口的世界坐标位置"""
    # 从摄像机世界位置发射
    muzzle_world_pos = camera.world_position + camera.forward * 1.5
    
    # 加上枪的横向偏移（右下方）
    right = camera.right * 0.3  # 向右偏移
    down = camera.down * 0.2    # 向下偏移
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
        self.lifetime = 2  # 子弹存活时间（秒）
        
    def update(self):
        # 子弹向前飞行
        self.position += self.direction * self.speed * time.dt
        self.lifetime -= time.dt
        
        # 碰撞检测 - 使用 raycast 从上一帧位置到当前位置
        hit_info = raycast(self.position - self.direction * self.speed * time.dt, 
                          self.direction, 
                          distance=self.speed * time.dt, 
                          ignore=[player, gun, self])
        
        if hit_info.hit:
            if hit_info.entity in targets:
                # 击中靶子
                destroy(hit_info.entity)
                targets.remove(hit_info.entity)
                print(f"命中！剩余靶子：{len(targets)}")
                # 生成新靶子
                create_target()
            # 子弹消失
            destroy(self)
            if self in bullets:
                bullets.remove(self)
            return
        
        # 超时销毁
        if self.lifetime <= 0:
            destroy(self)
            if self in bullets:
                bullets.remove(self)

# 靶子列表
targets = []

# 靶子大小范围
TARGET_SIZE_MIN = 1.0   # 最小边长
TARGET_SIZE_MAX = 3.0   # 最大边长

# 靶子移动速度范围
TARGET_SPEED_MIN = 2    # 最小速度
TARGET_SPEED_MAX = 8    # 最大速度

# 靶子移动范围
MOVE_RANGE_X = 40       # X 轴移动范围 ±40
MOVE_RANGE_Z = 40       # Z 轴移动范围 ±40

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
        # 随机移动方向
        self.move_direction = Vec3(
            randint(-1, 1),
            0,
            randint(-1, 1)
        ).normalized()
        # 随机移动速度
        self.move_speed = uniform(TARGET_SPEED_MIN, TARGET_SPEED_MAX)
        # 移动范围限制
        self.x_range = (-MOVE_RANGE_X, MOVE_RANGE_X)
        self.z_range = (-MOVE_RANGE_Z, MOVE_RANGE_Z)
        
    def update(self):
        # 移动靶子
        self.position += self.move_direction * self.move_speed * time.dt
        
        # 边界检测 - 碰到边界就反向
        if self.position.x < self.x_range[0] or self.position.x > self.x_range[1]:
            self.move_direction = Vec3(-self.move_direction.x, 0, self.move_direction.z)
            self.position.x = max(self.x_range[0], min(self.position.x, self.x_range[1]))
        
        if self.position.z < self.z_range[0] or self.position.z > self.z_range[1]:
            self.move_direction = Vec3(self.move_direction.x, 0, -self.move_direction.z)
            self.position.z = max(self.z_range[0], min(self.position.z, self.z_range[1]))

def create_target():
    """随机位置、随机大小生成移动靶子"""
    # 随机位置
    x = randint(-MOVE_RANGE_X, MOVE_RANGE_X)
    z = randint(-MOVE_RANGE_Z, MOVE_RANGE_Z)
    
    # 随机大小（1.0 - 3.0 之间）
    size = uniform(TARGET_SIZE_MIN, TARGET_SIZE_MAX)
    
    # 创建移动靶子
    target = MovingTarget(position=(x, 1, z), size=size)
    targets.append(target)

# 生成 5 个靶子
for _ in range(5):
    create_target()

def reload():
    """换弹夹"""
    global bullets_in_mag, is_reloading
    
    if is_reloading:
        return
    
    if bullets_in_mag == MAG_SIZE:
        return  # 弹夹已满
    
    is_reloading = True
    reload_text.enabled = True
    
    # 换弹动画 - 枪口向下
    gun.animate_rotation((-45, -5, 0), duration=0.5, curve=curve.linear)
    
    # 1.5 秒后换弹完成
    invoke(finish_reload, delay=1.5)

def finish_reload():
    """完成换弹"""
    global bullets_in_mag, is_reloading
    
    bullets_in_mag = MAG_SIZE
    is_reloading = False
    reload_text.enabled = False
    
    # 枪口恢复
    gun.animate_rotation((-5, -5, 0), duration=0.3, curve=curve.linear)
    
    # 更新弹药显示
    ammo_text.text = f'弹药：{bullets_in_mag}/{MAG_SIZE}'

# 射击逻辑
def input(key):
    global bullets_in_mag
    
    if key == 'r':
        reload()
        return
    
    if key == 'left mouse down':
        if is_reloading:
            return  # 换弹中不能射击
        
        if bullets_in_mag <= 0:
            # 空弹夹提示
            ammo_text.color = color.red
            invoke(setattr, ammo_text, 'color', color.white, delay=0.3)
            return
        
        # 消耗子弹
        bullets_in_mag -= 1
        ammo_text.text = f'弹药：{bullets_in_mag}/{MAG_SIZE}'
        
        # 枪口后坐力动画
        gun.animate_position((0.5, -0.35), duration=0.05, curve=curve.linear)
        gun.animate_position((0.5, -0.4), duration=0.1, curve=curve.linear)
        
        # 获取枪口世界位置
        muzzle_pos = get_muzzle_position()
        
        # 创建子弹（从枪口位置发射）
        bullet = Bullet(position=muzzle_pos, direction=camera.forward)
        bullets.append(bullet)

# 运行
app.run()
