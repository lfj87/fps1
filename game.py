from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from random import randint

app = Ursina()

# 天空和地面
Sky()
ground = Entity(model='plane', scale=(100, 1, 100), color=color.gray, texture='white_cube', texture_scale=(100, 100), collider='box')

# 玩家（FPS 控制器）
player = FirstPersonController(speed=12, position=(0, 2, 0))

# 枪
gun = Entity(parent=camera.ui, model='cube', color=color.black, scale=(0.4, 0.2, 1), position=(0.5, -0.4), rotation=(-5, -5, 0))

# 靶子列表
targets = []

def create_target():
    """随机位置生成靶子"""
    x = randint(-40, 40)
    z = randint(-40, 40)
    target = Entity(model='cube', color=color.red, scale=(2, 2, 0.2), position=(x, 1, z), collider='box')
    targets.append(target)

# 生成 5 个靶子
for _ in range(5):
    create_target()

# 射击逻辑
def input(key):
    if key == 'left mouse down':
        # 枪口后坐力动画
        gun.animate_position((0.5, -0.35), duration=0.05, curve=curve.linear)
        gun.animate_position((0.5, -0.4), duration=0.1, curve=curve.linear)
        
        # 射线检测
        hit_info = raycast(camera.world_position, camera.forward, distance=100)
        if hit_info.hit:
            if hit_info.entity in targets:
                # 击中靶子
                destroy(hit_info.entity)
                targets.remove(hit_info.entity)
                print(f"命中！剩余靶子：{len(targets)}")
                
                # 生成新靶子
                create_target()

# 运行
app.run()
