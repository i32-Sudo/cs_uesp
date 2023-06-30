from pyray import *
from pymem import *
from pymem.process import *
from pymem.pattern import *
from helpers import *
import requests
import numpy as np


exc_name = 'csgo.exe'
exc_title = 'Counter-Strike: Global Offensive - Direct3D 9'
pm = pymem.Pymem(exc_name)
clientModule = module_from_name(pm.process_handle, "client.dll").lpBaseOfDll
engineModule = module_from_name(pm.process_handle, "engine.dll").lpBaseOfDll
debug = bool(False)

class Offsets:
    def update():
        try:
            print("Downloading Offsets...")
            # Credits to https://github.com/frk1/hazedumper
            haze = requests.get(
                "https://raw.githubusercontent.com/frk1/hazedumper/master/csgo.json"
            ).json()

            [setattr(Offsets, k, v) for k, v in haze["signatures"].items()]
            [setattr(Offsets, k, v) for k, v in haze["netvars"].items()]
        except:
            sys.exit("Unable to fetch Hazedumper's Offsets")

class localPlayer:
    def __init__(self, mem : any, addr : any, module : any):
        self.addr = addr
        self.mem = mem
        self.module = module
    def flags(self):
        self.health = pm.read_int(self.addr + Offsets.m_iHealth)
        self.armor = pm.read_int(self.addr + Offsets.m_ArmorValue)
        self.team = pm.read_int(self.addr + Offsets.m_iTeamNum)

class entity:
    def __init__(self, mem, addr, module):
        self.wts = None # To Be Filled
        self.addr = addr
        self.mem = mem
        self.module = module
        self.health = pm.read_int(self.addr + Offsets.m_iHealth)
        self.armor = pm.read_int(self.addr + Offsets.m_ArmorValue)
        self.team = pm.read_int(self.addr + Offsets.m_iTeamNum)
        self.bone_base = pm.read_int(self.addr + Offsets.m_dwBoneMatrix)
    def bone_pos(self, bone_id):
        return Vec3(
            pm.read_float(self.bone_base + 0x30 * bone_id + 0x0C),
            pm.read_float(self.bone_base + 0x30 * bone_id + 0x1C),
            pm.read_float(self.bone_base + 0x30 * bone_id + 0x2C),
        )

def init():
    win = get_window_info(exc_title)
    set_trace_log_level(5)
    set_target_fps(0)
    set_config_flags(ConfigFlags.FLAG_WINDOW_UNDECORATED)
    set_config_flags(ConfigFlags.FLAG_WINDOW_MOUSE_PASSTHROUGH)
    set_config_flags(ConfigFlags.FLAG_WINDOW_TRANSPARENT)
    set_config_flags(ConfigFlags.FLAG_WINDOW_TOPMOST)
    init_window(win[2], win[3], "")
    set_window_position(win[0], win[1])

def update_window_pos(exec_title):
    win = get_window_info(exec_title)
    set_window_position(win[0], win[1])

def calculate_mid_vec(pass1, pass2):
    if pass1 > pass2:
        return pass1 - pass2
    else:
        return pass2 - pass1

def draw_custom_box_2d(BLeft, BRight, Top, Thickness=1, Filled=False, Color=RED):
    draw_line_ex(Vector2(int(BLeft[0]), int(BLeft[1])), Vector2(int(BLeft[0]), int(Top[1])), Thickness, Color) # Left Line
    draw_line_ex(Vector2(int(BRight[0]), int(BRight[1])), Vector2(int(BRight[0]), int(Top[1])), Thickness, Color) # Right Line

    draw_line_ex(Vector2(int(BLeft[0]), int(Top[1])), Vector2(int(BRight[0]), int(Top[1])), Thickness, Color) # Top
    draw_line_ex(Vector2(int(BLeft[0]), int(BLeft[1])), Vector2(int(BRight[0]), int(BRight[1])), Thickness, Color) # Bottom

def Main():
    font = load_font_ex("fonts\\Arial_Bold.ttf", 16, None, 3260)
    while not window_should_close():
        clear_background(BLANK)
        if (is_window_active(exc_title)):
            begin_drawing()
            update_window_pos(exec_title=exc_title)
            draw_fps(0, 250)
            for i in range(1, 32):
                try:
                    entity_addr = pm.read_int(clientModule + Offsets.dwEntityList + i * 0x10)
                    local_addr = pm.read_int(clientModule + Offsets.dwLocalPlayer)
                    if entity_addr:
                        local_class = entity(mem=pm, addr=local_addr, module=clientModule)
                        entity_class = entity(mem=pm, addr=entity_addr, module=clientModule)
                        if entity_class.health > 0:
                            viewMatrix = VecMem.read_4x4(addr=clientModule + Offsets.dwViewMatrix, pm=pm)

                            ConnectedPoints = [
                                '8|7|6|5|3', # Head->TopChest->MiddleChest->LowerChest

                                '7|38|64|39|62|50', # TopChest->LeftArm->Lefthnad
                                '7|10|35|36|11|34|12|14', #TopChest->RightArm->RightHand

                                '3|72|77|78|73|74|75', # LowerChest->Leg Left
                                '3|65|70|71|66|67|68', # LowerChest->Leg Right
                            ]

                            # Skeleton ESP #
                            for x in ConnectedPoints:
                                expanded = x.split(sep='|')
                                for i in range(len(expanded) - 1):  # Iterate up to len(expanded) - 1
                                    bone1 = worldToScreen(viewMatrix, entity_class.bone_pos(bone_id=int(expanded[i])), 1)
                                    bone2 = worldToScreen(viewMatrix, entity_class.bone_pos(bone_id=int(expanded[i + 1])), 1)
                                    draw_line(int(bone1[0]), int(bone1[1]), int(bone2[0]), int(bone2[1]), WHITE)

                            # Box ESP #
                            try:
                                HeadPos = worldToScreen(viewMatrix, entity_class.bone_pos(bone_id=8), 1)    
                                LeftFoot = worldToScreen(viewMatrix, entity_class.bone_pos(bone_id=75), 1)
                                RightFoot = worldToScreen(viewMatrix, entity_class.bone_pos(bone_id=67), 1)       
                                if HeadPos != None and LeftFoot != None and RightFoot != None:
                                    draw_custom_box_2d(LeftFoot, RightFoot, HeadPos, 1, False, BLUE if entity_class.team == local_class.team else RED)
                                    # Health Bar #
                                    if entity_class.health > 75:
                                        health_color = GREEN
                                    elif entity_class.health > 50 and entity_class.health < 75:
                                        health_color = YELLOW
                                    elif entity_class.health > 25 and entity_class.health < 50:
                                        health_color = RED
                                    elif entity_class.health > 1 and entity_class.health < 25:
                                        health_color = BLACK
                                    draw_line(int(LeftFoot[0])-5, int(LeftFoot[1]), int(LeftFoot[0])-5, int(HeadPos[1]), health_color)
                            except Exception as e:
                                if debug==True:
                                    print(e)
                except Exception as e:
                    if debug==True:
                        print(e)
            end_drawing()
        else:
            end_drawing()

if __name__=="__main__":
    Offsets.update()
    init()
    Main()