#!/usr/bin/env python3
import math
from sympy import symbols, Eq, solve

# 单位为分钟
DAY_TIME = 24 * 60

# --- 歌蒂007相关全局变量 ---

# 中枢每进驻一人, 值即+0.05, 最高0.25
DEFAULT_CENTER_ORIGIN_RECOVER = 0.25
# 根据进驻中枢的所有干员的相关心情恢复技能计算
CENTER_OPERATOR_SKILL_RECOVER = 0.05 * 3
# 控制中枢的全体默认心情消耗速度
DEFAULT_CENTER_MOOD_COST = 1 - DEFAULT_CENTER_ORIGIN_RECOVER - CENTER_OPERATOR_SKILL_RECOVER
# 缓冲时间: 如果并没有在预期时间点执行任务(网络问题, 执行速度问题等), 在该容错时间内, 程序执行并不会影响后续排班准点执行, 单位为min(<=2min)
BUFFER_TIME = 5
# 菲亚梅塔最后一换执行时间: 此班执行后, 后面的一次排班中歌蒂会出现和菲亚梅塔一起休息的情况, 两班之间时间间隔较长, 推荐在 16:00 以后, 可避开在方舟更新维护时间段内换班的情况
FIAMMETTA_LAST_CHANGE_TIME = 16 * 60 + 10

# 菲亚梅塔自身的心情恢复(默认一直在睡觉), 不要改变
FIAMMETTA_RECOVER = 2
# 歌蕾蒂娅的心情消耗, 不要改变, 默认深海5人全在宿舍外
GLADIIA_COST = DEFAULT_CENTER_MOOD_COST + 0.5 * 5
# 歌蕾蒂娅在宿舍的心情恢复速度, 值为 宿舍氛围加成 + 宿管技能加成
GLADIIA_RECOVER = 4 + 0.3
# 默认歌蕾蒂娅的换班次数, 设定为4, 不要改变(后续可能会调整程序逻辑, 但该版本不要改变)
FIAMMETTA_CHANGE_TIME = 4

# --- 整体基建心情相关全局变量 ---

DEFAULT_POWER_MOOD_COST = DEFAULT_MEETING_MOOD_COST = DEFAULT_OFFICE_MOOD_COST = 1 - DEFAULT_CENTER_ORIGIN_RECOVER
DEFAULT_MANUFACTURE_MOOD_COST = DEFAULT_TRADE_MOOD_COST = 1 - DEFAULT_CENTER_ORIGIN_RECOVER - 0.1
# 默认宿管心情恢复速度为0.25
DEFAULT_DORMITORY_MOOD_RECOVER = 4 + 0.25
SPECIAL_OFFICE_PENANCE_MOOD_COST = DEFAULT_OFFICE_MOOD_COST + 0.5
SPECIAL_TRADE_PROVISO_IN_SHAMARE_TEAM_MOOD_COST = DEFAULT_TRADE_MOOD_COST + 0.25

GLADIIA_FIAMMETTA_RATE = GLADIIA_COST / FIAMMETTA_RECOVER

# --- 歌蒂007相关函数 ---

def get_time_added_buffer(time):
    global BUFFER_TIME
    return BUFFER_TIME + time + BUFFER_TIME


def convert_to_definite_time_string(time):
    global FIAMMETTA_LAST_CHANGE_TIME
    hours = int(time // 60) + FIAMMETTA_LAST_CHANGE_TIME // 60
    mins = int(time % 60) + FIAMMETTA_LAST_CHANGE_TIME % 60
    if mins > 60:
        mins -= 60
        hours += 1
    if hours >= 24:
        hours -= 24
    return f"{hours:02d}:{mins:02d}"


def convert_to_hour_string(time):
    hours = int(time // 60)
    mins = int(time % 60)
    return f"{hours:02d}小时{mins:02d}分钟"

def get_next_rest_time(time):
    global BUFFER_TIME, GLADIIA_FIAMMETTA_RATE
    return GLADIIA_FIAMMETTA_RATE * time + BUFFER_TIME

def get_init_rest_time(time):
    global BUFFER_TIME
    return time + BUFFER_TIME

def get_init_x():
    global FIAMMETTA_CHANGE_TIME, DAY_TIME
    x = symbols('x')
    x0 = get_init_rest_time(x)

    x_list = [x0]
    for i in range(FIAMMETTA_CHANGE_TIME - 1):
        x_next = get_next_rest_time(x_list[-1])
        x_list.append(x_next)

    # 构建方程 x0 + x1 + x2 + x3 - 1440 = 0
    eq = Eq(sum(x_list) - DAY_TIME, 0)

    # 求解 x
    solutions = solve(eq, x)
    return solutions[0]

def get_gladiia_work_time(whole_work_and_rest_time, init_theoretical_gladiia_work_time):
    global FIAMMETTA_RECOVER, GLADIIA_RECOVER, GLADIIA_COST, DAY_TIME, GLADIIA_FIAMMETTA_RATE, BUFFER_TIME
    x = symbols('x')
    eq = Eq(GLADIIA_COST * x - GLADIIA_RECOVER * (whole_work_and_rest_time - x),  FIAMMETTA_RECOVER * init_theoretical_gladiia_work_time)
    solutions = solve(eq, x)
    return solutions[0]

def get_gladiia_max_work_time():
    global DAY_TIME, GLADIIA_COST, BUFFER_TIME
    return DAY_TIME / GLADIIA_COST // 1 - BUFFER_TIME

def calculate_all_times():
    global DAY_TIME
    init_theoretical_gladiia_work_time = get_init_x()

    init_gladiia_work_time = get_init_rest_time(init_theoretical_gladiia_work_time)

    second_gladiia_work_time = get_next_rest_time(init_gladiia_work_time)

    third_gladiia_work_time = get_next_rest_time(second_gladiia_work_time)

    init_gladiia_work_time = init_theoretical_gladiia_work_time // 1

    second_gladiia_work_time = second_gladiia_work_time // 1

    third_gladiia_work_time = third_gladiia_work_time // 1

    whole_work_and_rest_time = DAY_TIME - init_gladiia_work_time - second_gladiia_work_time - third_gladiia_work_time

    last_gladiia_work_time = min(get_gladiia_work_time(whole_work_and_rest_time, init_theoretical_gladiia_work_time) // 1 , get_gladiia_max_work_time())

    common_rest_time = whole_work_and_rest_time - last_gladiia_work_time

    return [int(init_gladiia_work_time), int(second_gladiia_work_time), int(third_gladiia_work_time),
            int(last_gladiia_work_time), int(common_rest_time)]


# --- 基建换班一日一换相关函数 ---

def calculate_normal_room_rest_time(mood_cost):
    global DEFAULT_DORMITORY_MOOD_RECOVER, DAY_TIME, BUFFER_TIME
    rest_time = get_time_added_buffer(math.ceil(DAY_TIME * mood_cost / (DEFAULT_DORMITORY_MOOD_RECOVER + mood_cost)))
    return convert_to_hour_string(rest_time)


def main():
    init_gladiia_work_time, second_gladiia_work_time, third_gladiia_work_time, last_gladiia_work_time, common_rest_time = calculate_all_times()

    print(f"一日一休的情况下，各设施至少需要休息如下时间:")
    print(f"控制中枢: {calculate_normal_room_rest_time(DEFAULT_CENTER_MOOD_COST)}")
    print(f"发电站: {calculate_normal_room_rest_time(DEFAULT_POWER_MOOD_COST)}")
    print(f"会客室: {calculate_normal_room_rest_time(DEFAULT_MEETING_MOOD_COST)}")
    print(f"办公室: {calculate_normal_room_rest_time(DEFAULT_OFFICE_MOOD_COST)}")
    print(f"---斥罪: {calculate_normal_room_rest_time(SPECIAL_OFFICE_PENANCE_MOOD_COST)}")

    print(f"制造站: {calculate_normal_room_rest_time(DEFAULT_MANUFACTURE_MOOD_COST)}")
    print(f"贸易站: {calculate_normal_room_rest_time(DEFAULT_TRADE_MOOD_COST)}")
    print(f"--巫恋组但书: {calculate_normal_room_rest_time(SPECIAL_TRADE_PROVISO_IN_SHAMARE_TEAM_MOOD_COST)}")

    print(f"——————————————————————————————————————")

    print(f"153各排班时间点如下:")
    print(
        f"153-SP-01班时间为 {convert_to_definite_time_string(last_gladiia_work_time)}, 本次换班可持续{convert_to_hour_string(common_rest_time)}")
    print(
        f"153-SP-02班时间为 {convert_to_definite_time_string(last_gladiia_work_time + common_rest_time)}, 本次换班可持续{convert_to_hour_string(init_gladiia_work_time)}")
    print(
        f"153-007-01班时间为 {convert_to_definite_time_string(last_gladiia_work_time + common_rest_time + init_gladiia_work_time)}, 本次换班可持续{convert_to_hour_string(second_gladiia_work_time)}")
    print(
        f"153-007-02班时间为 {convert_to_definite_time_string(last_gladiia_work_time + common_rest_time + init_gladiia_work_time + second_gladiia_work_time)}, 本次换班可持续{convert_to_hour_string(third_gladiia_work_time)}")
    print(
        f"153-007-03班时间为 {convert_to_definite_time_string(0)}, 本次换班可持续{convert_to_hour_string(last_gladiia_work_time)}")


if __name__ == "__main__":
    main()
