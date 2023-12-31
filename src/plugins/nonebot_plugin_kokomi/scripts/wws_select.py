import json
import os
import httpx
import logging
import time
import cv2
import numpy as np
from PIL import Image
import platform
import gc
from httpx import (
    TimeoutException,
    ConnectTimeout,
    ReadTimeout
)
from .config import (
    DOG_TAG,
    REQUEST_TIMEOUT,
    API_URL,
    API_TOKEN,
    PIC_TYPE,
    BOT_VERSON
)
from .data_source import (
    img_to_b64,
    img_to_file,
    pr_info,
    color_box,
    merge_img,
    x_coord,
    add_text
)
from .data_source import (
    font_list,
    clan_color
)

file_path = os.path.dirname(__file__)
isWin = True if platform.system().lower() == 'windows' else False
# 配置日志输出到文件
logging.basicConfig(filename=os.path.join(
    file_path, 'log', 'error.log'), level=logging.ERROR)


def main(
    result: dict,
    aid: str,
    server: str,
    select: str,
    use_pr: bool
):
    text_list = []
    # Id卡
    text_list.append(
        [(158+14, 123+38), result['nickname'], (0, 0, 0), 1, 100])
    text_list.append(
        [(185+14, 237+38), f'{server.upper()} -- {aid}', (163, 163, 163), 1, 45])
    fontStyle = font_list[1][50]
    if result['data']['clans']['clan'] == {}:
        tag = 'None'
        tag_color = (179, 179, 179)
    else:
        tag = '['+result['data']['clans']['clan']['tag']+']'
        tag_color = clan_color[result['data']['clans']['clan']['color']]
    text_list.append(
        [(602+14-150+2, 317+38+2), tag, (255, 255, 255), 1, 50])
    text_list.append(
        [(602+14-150, 317+38), tag, tag_color, 1, 50])
    data_type = 'PVP'
    w = x_coord(data_type, fontStyle)
    text_list.append(
        [(602+14-150, 405+38), data_type, (0, 0, 0), 1, 50])
    # 主要数据
    index = 'pvp'
    if (
        use_pr != True or
        result['data']['pr']['battle_type'][index] == {} or
        result['data']['pr']['battle_type'][index]['value_battles_count'] == 0
    ):
        avg_pr = -1
    else:
        avg_pr = int(result['data']['pr']['battle_type'][index]['personal_rating'] /
                     result['data']['pr']['battle_type'][index]['value_battles_count']) + 1
    pr_data = pr_info(avg_pr)
    pr_png_path = os.path.join(
        file_path, 'png', 'pr', '{}.png'.format(pr_data[0]))
    res_img = cv2.imread(os.path.join(
        file_path, 'png', 'background', 'wws_ships.png'), cv2.IMREAD_UNCHANGED)
    pr_png = cv2.imread(pr_png_path, cv2.IMREAD_UNCHANGED)
    pr_png = cv2.resize(pr_png, None, fx=0.787, fy=0.787)
    x1 = 118+14
    y1 = 590+38
    x2 = x1 + pr_png.shape[1]
    y2 = y1 + pr_png.shape[0]
    res_img = merge_img(res_img, pr_png, y1, y2, x1, x2)
    del pr_png
    text_list.append(
        [(545+100*pr_data[3]+14, 653+38), pr_data[2]+str(pr_data[4]), (255, 255, 255), 1, 35])
    str_pr = '{:,}'.format(int(avg_pr))
    fontStyle = font_list[1][80]
    w = x_coord(str_pr, fontStyle)
    text_list.append(
        [(2270-w+14, 605+38), str_pr, (255, 255, 255), 1, 80])
    x0 = 310+14
    y0 = 823+38
    temp_data = result['data']['pr']['battle_type'][index]
    if temp_data == {} or temp_data['battles_count'] == 0:
        battles_count = '{:,}'.format(0)
        avg_win = '{:.2f}%'.format(0.00)
        avg_wins = 0.00
        avg_damage = '{:,}'.format(0).replace(',', ' ')
        avg_frag = '{:.2f}'.format(0.00)
        avg_xp = '{:,}'.format(0).replace(',', ' ')
    else:
        battles_count = '{:,}'.format(temp_data['battles_count'])
        avg_win = '{:.2f}%'.format(
            temp_data['wins']/temp_data['battles_count']*100)
        avg_wins = temp_data['wins'] / \
            temp_data['battles_count']*100
        avg_damage = '{:,}'.format(int(
            temp_data['damage_dealt']/temp_data['battles_count'])).replace(',', ' ')
        avg_frag = '{:.2f}'.format(
            temp_data['frags']/temp_data['battles_count'])
        avg_xp = '{:,}'.format(int(
            temp_data['original_exp']/temp_data['battles_count'])).replace(',', ' ')
    if (
        use_pr != True or
        temp_data == {} or
        temp_data['value_battles_count'] == 0
    ):
        avg_pr = -1
        avg_n_damage = -1
        avg_n_frag = -1
    else:
        avg_n_damage = temp_data['n_damage_dealt'] / \
            temp_data['battles_count']
        avg_n_frag = temp_data['n_frags'] / \
            temp_data['battles_count']
        avg_pr = temp_data['personal_rating'] / \
            temp_data['battles_count']

    fontStyle = font_list[1][80]
    w = x_coord(battles_count, fontStyle)
    text_list.append(
        [(x0+446*0-w/2, y0), battles_count, (0, 0, 0), 1, 80])
    w = x_coord(avg_win, fontStyle)
    text_list.append(
        [(x0+446*1-w/2, y0), avg_win, color_box(0, avg_wins)[1], 1, 80])
    w = x_coord(avg_damage, fontStyle)
    text_list.append(
        [(x0+446*2-w/2, y0), avg_damage, color_box(1, avg_n_damage)[1], 1, 80])
    w = x_coord(avg_frag, fontStyle)
    text_list.append(
        [(x0+446*3-w/2, y0), avg_frag, color_box(2, avg_n_frag)[1], 1, 80])
    w = x_coord(avg_xp, fontStyle)
    text_list.append(
        [(x0+446*4-w/2, y0), avg_xp, (0, 0, 0), 1, 80])

    # dog_tag
    if DOG_TAG:
        dog_tag_json = open(os.path.join(
            file_path, 'png', 'dog_tags.json'), "r", encoding="utf-8")
        dog_tag_data = json.load(dog_tag_json)
        dog_tag_json.close()
        doll_id = result['dog_tag']['doll_id']
        doll_png = dog_tag_data[str(doll_id)]
        doll_png_path = os.path.join(
            file_path, 'png', 'dogTags', f'{doll_png}.png')
        doll = cv2.imread(doll_png_path, cv2.IMREAD_UNCHANGED)
        doll = cv2.resize(doll, None, fx=0.818, fy=0.818)
        x1 = 1912
        y1 = 131
        x2 = x1 + doll.shape[1]
        y2 = y1 + doll.shape[0]
        res_img = merge_img(res_img, doll, y1, y2, x1, x2)
        if result['dog_tag']['slots'] != {}:
            slots_id = result['dog_tag']['slots']['1']
            slots_png = dog_tag_data[str(slots_id)]
            slots_png_path = os.path.join(
                file_path, 'png', 'dogTags', f'{slots_png}.png')
            slots = cv2.imread(slots_png_path, cv2.IMREAD_UNCHANGED)
            slots = cv2.resize(slots, None, fx=0.818, fy=0.818)
            x1 = 1912
            y1 = 131
            x2 = x1 + slots.shape[1]
            y2 = y1 + slots.shape[0]
            res_img = merge_img(res_img, slots, y1, y2, x1, x2)
            del slots
        del doll
    # 数据总览
    index_list = ['pvp_solo', 'pvp_div2', 'pvp_div3']
    i = 0
    for index in index_list:
        x0 = 0
        y0 = 1592
        temp_data = result['data']['pr']['battle_type'][index]
        if temp_data == {} or temp_data['battles_count'] == 0:
            battles_count = '{:,}'.format(0)
            avg_win = '{:.2f}%'.format(0.00)
            avg_wins = 0.00
            avg_damage = '{:,}'.format(0).replace(',', ' ')
            avg_frag = '{:.2f}'.format(0.00)
            avg_xp = '{:,}'.format(0).replace(',', ' ')
        else:
            battles_count = '{:,}'.format(temp_data['battles_count'])
            avg_win = '{:.2f}%'.format(
                temp_data['wins']/temp_data['battles_count']*100)
            avg_wins = temp_data['wins'] / \
                temp_data['battles_count']*100
            avg_damage = '{:,}'.format(int(
                temp_data['damage_dealt']/temp_data['battles_count'])).replace(',', ' ')
            avg_frag = '{:.2f}'.format(
                temp_data['frags']/temp_data['battles_count'])
            avg_xp = '{:,}'.format(int(
                temp_data['original_exp']/temp_data['battles_count'])).replace(',', ' ')
        if temp_data == {} or temp_data['value_battles_count'] == 0:
            avg_pr = -1
            avg_n_damage = -1
            avg_n_frag = -1
        else:
            avg_n_damage = temp_data['n_damage_dealt'] / \
                temp_data['battles_count']
            avg_n_frag = temp_data['n_frags'] / \
                temp_data['battles_count']
            avg_pr = temp_data['personal_rating'] / \
                temp_data['battles_count']
        str_pr = pr_info(
            avg_pr)[5] + '(+'+str(pr_info(avg_pr)[4])+')'

        fontStyle = font_list[1][50]
        w = x_coord(battles_count, fontStyle)
        text_list.append(
            [(572-w/2+x0, y0+90*i), battles_count, (0, 0, 0), 1, 50])
        w = x_coord(str_pr, fontStyle)
        text_list.append(
            [(937-w/2+x0, y0+90*i), str_pr, pr_info(avg_pr)[1], 1, 50])
        w = x_coord(avg_win, fontStyle)
        text_list.append(
            [(1291-w/2+x0, y0+90*i), avg_win, color_box(0, avg_wins)[1], 1, 50])
        w = x_coord(avg_damage, fontStyle)
        text_list.append(
            [(1595-w/2+x0, y0+90*i), avg_damage, color_box(1, avg_n_damage)[1], 1, 50])
        w = x_coord(avg_frag, fontStyle)
        text_list.append(
            [(1893-w/2+x0, y0+90*i), avg_frag, color_box(2, avg_n_frag)[1], 1, 50])
        w = x_coord(avg_xp, fontStyle)
        text_list.append(
            [(2160-w/2+x0, y0+90*i), avg_xp, (0, 0, 0), 1, 50])
        i += 1

    # 船只数据
    ships_pr_list = {}
    for ship_id, ship_data in result['data']['ships'].items():
        if ship_data['pvp'] == {}:
            ships_pr_list[ship_id] = -1
        else:
            if ship_data['pvp']['value_battles_count'] == 0:
                ships_pr_list[ship_id] = -1
            else:
                ships_pr_list[ship_id] = ship_data['pvp']['personal_rating'] / \
                    ship_data['pvp']['value_battles_count']
    sorts_pr_list = sorted(ships_pr_list.items(),
                           key=lambda x: x[1], reverse=True)
    all_png_path = os.path.join(file_path, 'png', 'ship_preview.jpg')
    all_png = Image.open(all_png_path)
    all_json = open(os.path.join(file_path, 'png', 'ship_preview.json'),
                    "r", encoding="utf-8")
    all_dict = json.load(all_json)
    all_json.close()
    # 中间插一个筛选条件
    # select
    select_tier = f'{select[0]}'
    select_type = f'{select[1]}'
    select_nation = f'{select[2]}'
    select_num = str(len(ships_pr_list))
    fontStyle = font_list[1][55]
    w = x_coord(select_tier, fontStyle)
    text_list.append(
        [(1485-w/2, 1245), select_tier, (0, 0, 0), 1, 55])
    w = x_coord(select_type, fontStyle)
    text_list.append(
        [(985-w/2, 1245), select_type, (0, 0, 0), 1, 55])
    w = x_coord(select_nation, fontStyle)
    text_list.append(
        [(421-w/2, 1245), select_nation, (0, 0, 0), 1, 55])
    w = x_coord(select_num, fontStyle)
    text_list.append(
        [(2010-w/2, 1245), select_num, (0, 0, 0), 1, 55])

    if (isinstance(res_img, np.ndarray)):
        res_img = Image.fromarray(
            cv2.cvtColor(res_img, cv2.COLOR_BGR2RGB))
    i = 0
    for ship_id, ship_pr in sorts_pr_list:
        temp_data = result['data']['ships'][ship_id]['pvp']
        x0 = 0
        y0 = 2101
        if i >= 150:
            overflow_warming = '最多只能显示150条船只的数据'
            w = x_coord(overflow_warming, fontStyle)
            text_list.append(
                [(1214-w/2+x0, y0+90*i), overflow_warming, (160, 160, 160), 1, 50])
            break
        # ship 图片
        if ship_id in all_dict:
            pic_code = all_dict[ship_id]
            x = (pic_code % 10)
            y = int(pic_code / 10)
            ship_png = all_png.crop(
                ((0+517*x), (0+115*y), (517+517*x), (115+115*y)))
            ship_png = ship_png.resize((360, 80))
            res_img.paste(ship_png, (110, 2087+89*i))
        else:
            text_list.append(
                [(110, 2101+108*i), 'Undefined Png', (160, 160, 160), 1, 50])
        # ship 数据
        if temp_data == {} or temp_data['battles_count'] == 0:
            battles_count = '{:,}'.format(0)
            avg_win = '{:.2f}%'.format(0)
            avg_wins = -1
            avg_damage = '{:,}'.format(0)
            avg_frag = '{:.2f}'.format(0)
            avg_xp = '{:,}'.format(0)
            avg_survived = '{:.2f}%'.format(0)
            avg_hit_rate_by_main = '{:.2f}%'.format(0)
        else:
            battles_count = '{:,}'.format(temp_data['battles_count'])
            avg_win = '{:.2f}%'.format(
                temp_data['wins']/temp_data['battles_count']*100)
            avg_wins = temp_data['wins'] / \
                temp_data['battles_count']*100
            avg_damage = '{:,}'.format(int(
                temp_data['damage_dealt']/temp_data['battles_count'])).replace(',', ' ')
            avg_frag = '{:.2f}'.format(
                temp_data['frags']/temp_data['battles_count'])
            avg_xp = '{:,}'.format(
                int(temp_data['original_exp']/temp_data['battles_count'])).replace(',', ' ')
            avg_survived = '{:.2f}%'.format(
                temp_data['survived']/temp_data['battles_count']*100)
            avg_hit_rate_by_main = '{:.2f}%'.format(
                0.00 if temp_data['shots_by_main'] == 0 else temp_data['hits_by_main']/temp_data['shots_by_main']*100)
        if (
            use_pr != True or
            temp_data == {} or
            temp_data['battles_count'] == 0 or
            temp_data['value_battles_count'] == 0
        ):
            avg_pr = -1
            avg_n_damage = -1
            avg_n_frag = -1
        else:
            avg_n_damage = temp_data['n_damage_dealt'] / \
                temp_data['battles_count']
            avg_n_frag = temp_data['n_frags'] / \
                temp_data['battles_count']
            avg_pr = temp_data['personal_rating'] / \
                temp_data['battles_count']

        fontStyle = font_list[1][50]
        str_pr = pr_info(
            avg_pr)[5] + '(+'+str(pr_info(avg_pr)[4])+')'
        w = x_coord(battles_count, fontStyle)
        text_list.append(
            [(551-w/2+x0, y0+89*i), battles_count, (0, 0, 0), 1, 50])
        w = x_coord(str_pr, fontStyle)
        text_list.append(
            [(834-w/2+x0, y0+89*i), str_pr, pr_info(avg_pr)[1], 1, 50])
        w = x_coord(avg_win, fontStyle)
        text_list.append(
            [(1160-w/2+x0, y0+89*i), avg_win, color_box(0, avg_wins)[1], 1, 50])
        w = x_coord(avg_damage, fontStyle)
        text_list.append(
            [(1396-w/2+x0, y0+89*i), avg_damage, color_box(1, avg_n_damage)[1], 1, 50])
        w = x_coord(avg_frag, fontStyle)
        text_list.append(
            [(1596-w/2+x0, y0+89*i), avg_frag, color_box(2, avg_n_frag)[1], 1, 50])
        w = x_coord(avg_xp, fontStyle)
        text_list.append(
            [(1770-w/2+x0, y0+89*i), avg_xp, (0, 0, 0), 1, 50])
        w = x_coord(avg_survived, fontStyle)
        text_list.append(
            [(1978-w/2+x0, y0+89*i), avg_survived, (0, 0, 0), 1, 50])
        w = x_coord(avg_hit_rate_by_main, fontStyle)
        text_list.append(
            [(2209-w/2+x0, y0+89*i), avg_hit_rate_by_main, (0, 0, 0), 1, 50])
        i += 1

    w = x_coord(BOT_VERSON, fontStyle)
    text_list.append(
        [(1214-w/2, 2087+89*(i+1)+14), BOT_VERSON, (174, 174, 174), 1, 50])
    # 图表
    res_img = add_text(text_list, res_img)
    res_img = res_img.crop((0, 0, 2429, 2087+90*(i+2)))
    res_img = res_img.resize((int(2429*0.5), int((2087+90*(i+2))*0.5)))
    del all_png
    return res_img


async def get_png(
    parameter: list
):
    aid = parameter[0]
    server = parameter[1]
    select = parameter[2]
    use_pr = parameter[3]

    try:
        async with httpx.AsyncClient() as client:
            if parameter[4]:
                url = API_URL + '/user/ships/' + \
                    f'?token={API_TOKEN}&aid={parameter[0]}&server={parameter[1]}&select={parameter[2]}&use_ac=True&ac={parameter[5]}'
            else:
                url = API_URL + '/user/ships/' + \
                    f'?token={API_TOKEN}&aid={parameter[0]}&server={parameter[1]}&select={parameter[2]}'
            res = await client.get(url, timeout=REQUEST_TIMEOUT)
            requset_code = res.status_code
            result = res.json()
            if requset_code == 200:
                pass
            else:
                return {'status': 'info', 'message': '数据接口请求失败'}
        if result['status'] != 'ok':
            return result
        if result['hidden'] == True:
            return {'status': 'info', 'message': '该玩家隐藏战绩'}
        if result['data']['pr']['battle_type']['pvp'] == {}:
            return {'status': 'info', 'message': '该日期范围内没有随机战斗的数据'}
        res_img = main(
            result,
            aid,
            server,
            select,
            use_pr
        )
        res = {'status': 'ok', 'message': 'SUCCESS', 'img': None}
        if PIC_TYPE == 'base64':
            res['img'] = img_to_b64(res_img)
        elif PIC_TYPE == 'file':
            res['img'] = img_to_file(res_img)
        else:
            return {'status': 'info', 'message': '程序内部错误', 'error': 'PIC_TYPE 配置错误!'}
        del res_img
        gc.collect()
        return res
    except (TimeoutException, ConnectTimeout, ReadTimeout):
        return {'status': 'info', 'message': '网络请求超时,请稍后重试'}
    except Exception as e:
        logging.exception(
            f"Time:{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}, Parameter:{parameter}")
        return {'status': 'error', 'message': f'程序内部错误', 'error': str(type(e))}
