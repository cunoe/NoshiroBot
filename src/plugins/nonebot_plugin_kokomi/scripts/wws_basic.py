import json
import os
import httpx
import time
import cv2
import numpy as np
from PIL import Image, ImageDraw
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
    clan_color,
    rank_list,
    rank_color_list
)
import logging

file_path = os.path.dirname(__file__)
# 配置日志输出到文件
logging.basicConfig(filename=os.path.join(
    file_path, 'log', 'error.log'), level=logging.ERROR)


def main(
    result: dict,
    aid: str,
    server: str,
    use_pr: bool
):
    text_list = []
    # Id卡
    text_list.append(
        [(158+14, 123+38), result['nickname'], (0, 0, 0), 1, 100])
    text_list.append(
        [(185+14, 237+38), f'{server.upper()} -- {aid}', (163, 163, 163), 1, 45])

    fontStyle = font_list[1][55]
    if result['data']['clans']['clan'] == {}:
        tag = 'None'
        tag_color = (179, 179, 179)
    else:
        tag = '['+result['data']['clans']['clan']['tag']+']'
        tag_color = clan_color[result['data']['clans']['clan']['color']]
    text_list.append(
        [(602+14-150+2, 317+38+2), tag, (255, 255, 255), 1, 55])
    text_list.append(
        [(602+14-150, 317+38), tag, tag_color, 1, 55])
    creat_time = time.strftime(
        "%Y-%m-%d", time.localtime(result['data']['user']['created_at']))
    w = x_coord(creat_time, fontStyle)
    text_list.append(
        [(602+14-150, 405+38), creat_time, (0, 0, 0), 1, 55])
    #
    if (
        use_pr != True or
        result['data']['pr']['battle_type']['pvp'] == {} or
        result['data']['pr']['battle_type']['pvp']['value_battles_count'] == 0
    ):
        avg_pr = -1
    else:
        avg_pr = int(result['data']['pr']['battle_type']['pvp']['personal_rating'] /
                     result['data']['pr']['battle_type']['pvp']['value_battles_count']) + 1
    pr_data = pr_info(avg_pr)
    pr_png_path = os.path.join(
        file_path, 'png', 'pr', '{}.png'.format(pr_data[0]))
    res_img = cv2.imread(os.path.join(
        file_path, 'png', 'background', 'wws_basic.png'), cv2.IMREAD_UNCHANGED)
    pr_png = cv2.imread(pr_png_path, cv2.IMREAD_UNCHANGED)
    pr_png = cv2.resize(pr_png, None, fx=0.787, fy=0.787)
    x1 = 118+14
    y1 = 590+38
    x2 = x1 + pr_png.shape[1]
    y2 = y1 + pr_png.shape[0]
    res_img = merge_img(res_img, pr_png, y1, y2, x1, x2)
    del pr_png
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

    text_list.append(
        [(545+100*pr_data[3]+14, 653+38), pr_data[2]+str(pr_data[4]), (255, 255, 255), 1, 35])
    str_pr = '{:,}'.format(int(avg_pr))
    fontStyle = font_list[1][80]
    w = x_coord(str_pr, fontStyle)
    text_list.append(
        [(2270-w+14, 605+38), str_pr, (255, 255, 255), 1, 80])
    index = 'pvp'
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
    if temp_data == {} or temp_data['value_battles_count'] == 0 or use_pr != True:
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
    # 数据总览
    i = 0
    for index in ['pvp_solo', 'pvp_div2', 'pvp_div3', 'rank_solo']:
        x0 = 0 + 14
        y0 = 1213+38
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
        if temp_data == {} or temp_data['value_battles_count'] == 0 or use_pr != True:
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

        fontStyle = font_list[1][55]
        w = x_coord(battles_count, fontStyle)
        text_list.append(
            [(572-w/2+x0, y0+90*i), battles_count, (0, 0, 0), 1, 55])
        w = x_coord(str_pr, fontStyle)
        text_list.append(
            [(937-w/2+x0, y0+90*i), str_pr, pr_info(avg_pr)[1], 1, 55])
        w = x_coord(avg_win, fontStyle)
        text_list.append(
            [(1291-w/2+x0, y0+90*i), avg_win, color_box(0, avg_wins)[1], 1, 55])
        w = x_coord(avg_damage, fontStyle)
        text_list.append(
            [(1595-w/2+x0, y0+90*i), avg_damage, color_box(1, avg_n_damage)[1], 1, 55])
        w = x_coord(avg_frag, fontStyle)
        text_list.append(
            [(1893-w/2+x0, y0+90*i), avg_frag, color_box(2, avg_n_frag)[1], 1, 55])
        w = x_coord(avg_xp, fontStyle)
        text_list.append(
            [(2160-w/2+x0, y0+90*i), avg_xp, (0, 0, 0), 1, 55])
        i += 1
    # 排位数据
    i = 0
    for season_stage, season_data in result['data']['season'].items():
        x0 = 0+14
        y0 = 2487+38
        temp_data = season_data
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

        str_rank = rank_list[temp_data['best_season_rank']
                             ] + ' ' + str(temp_data['best_rank'])
        season_stage_str = f'-第 {season_stage[2:]} 赛季'
        text_list.append(
            [(168, 2535+90*i), season_stage_str, (0, 0, 0), 1, 55])
        fontStyle = font_list[1][55]
        w = x_coord(battles_count, fontStyle)
        text_list.append(
            [(572-w/2+x0, y0+90*i), battles_count, (0, 0, 0), 1, 55])
        w = x_coord(str_rank, fontStyle)
        text_list.append(
            [(934-w/2+x0, y0+90*i), str_rank, rank_color_list[temp_data['best_season_rank']], 1, 55])
        w = x_coord(avg_win, fontStyle)
        text_list.append(
            [(1291-w/2+x0, y0+90*i), avg_win, color_box(0, avg_wins)[1], 1, 55])
        w = x_coord(avg_damage, fontStyle)
        text_list.append(
            [(1595-w/2+x0, y0+90*i), avg_damage, (0, 0, 0), 1, 55])
        w = x_coord(avg_frag, fontStyle)
        text_list.append(
            [(1893-w/2+x0, y0+90*i), avg_frag, (0, 0, 0), 1, 55])
        w = x_coord(avg_xp, fontStyle)
        text_list.append(
            [(2160-w/2+x0, y0+90*i), avg_xp, (0, 0, 0), 1, 55])
        i += 1
    # 船只数据
    i = 0
    for index in ['AirCarrier', 'Battleship', 'Cruiser', 'Destroyer', 'Submarine']:
        x0 = 0+14
        y0 = 1805+38
        temp_data = result['data']['pr']['ship_type'][index]
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
        if temp_data == {} or temp_data['value_battles_count'] == 0 or use_pr != True:
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

        fontStyle = font_list[1][55]
        w = x_coord(battles_count, fontStyle)
        text_list.append(
            [(572-w/2+x0, y0+90*i), battles_count, (0, 0, 0), 1, 55])
        w = x_coord(str_pr, fontStyle)
        text_list.append(
            [(937-w/2+x0, y0+90*i), str_pr, pr_info(avg_pr)[1], 1, 55])
        w = x_coord(avg_win, fontStyle)
        text_list.append(
            [(1291-w/2+x0, y0+90*i), avg_win, color_box(0, avg_wins)[1], 1, 55])
        w = x_coord(avg_damage, fontStyle)
        text_list.append(
            [(1595-w/2+x0, y0+90*i), avg_damage, color_box(1, avg_n_damage)[1], 1, 55])
        w = x_coord(avg_frag, fontStyle)
        text_list.append(
            [(1893-w/2+x0, y0+90*i), avg_frag, color_box(2, avg_n_frag)[1], 1, 55])
        w = x_coord(avg_xp, fontStyle)
        text_list.append(
            [(2160-w/2+x0, y0+90*i), avg_xp, (0, 0, 0), 1, 55])
        i += 1
    if (isinstance(res_img, np.ndarray)):
        res_img = Image.fromarray(
            cv2.cvtColor(res_img, cv2.COLOR_BGR2RGB))
    # 图表
    max_num = 0
    num_list = []
    for tier, num in result['data']['pr']['ship_tier'].items():
        if num >= max_num:
            max_num = num
        num_list.append(num)
    max_index = (int(max_num/100) + 1)*100
    i = 0
    for index in num_list:
        pic_len = 500-index/max_index*500
        x1 = 258+129*i+14
        y1 = 2996+int(pic_len)+38
        x2 = 336+129*i+14
        y2 = 3500+38
        tier = ImageDraw.ImageDraw(res_img)
        tier.rectangle(((x1, y1), (x2, y2)),
                       fill=(137, 207, 240), outline=None)
        fontStyle = font_list[1][35]
        w = x_coord(str(index), fontStyle)
        text_list.append(
            [(297-w/2+129*i+14, y1-40), str(index), (0, 0, 0), 1, 35])
        i += 1
    fontStyle = font_list[1][80]
    w = x_coord(BOT_VERSON, fontStyle)
    text_list.append(
        [(1214-w/2, 3740), BOT_VERSON, (174, 174, 174), 1, 80])
    res_img = add_text(text_list, res_img)
    res_img = res_img.resize((1214, 1941))
    return res_img


async def get_png(
    parameter: list,
):
    try:
        async with httpx.AsyncClient() as client:
            if parameter[3]:
                url = API_URL + '/user/basic/' + \
                    f'?token={API_TOKEN}&aid={parameter[0]}&server={parameter[1]}&use_ac=True&ac={parameter[3]}'
            else:
                url = API_URL + '/user/basic/' + \
                    f'?token={API_TOKEN}&aid={parameter[0]}&server={parameter[1]}'
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
        res_img = main(
            result=result,
            aid=parameter[0],
            server=parameter[1],
            use_pr=parameter[2]
        )
        res = {'status': 'ok', 'message': 'SUCCESS', 'img': None}
        if PIC_TYPE == 'base64':
            res['img'] = img_to_b64(res_img)
        elif PIC_TYPE == 'file':
            res['img'] = img_to_file(res_img)
        else:
            return {'status': 'error', 'message': '程序内部错误', 'error': 'PIC_TYPE 配置错误!'}
        del res_img
        gc.collect()
        return res
    except (TimeoutException, ConnectTimeout, ReadTimeout):
        return {'status': 'info', 'message': '网络请求超时,请稍后重试'}
    except Exception as e:
        logging.exception(
            f"Time:{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}, Parameter:{parameter}")
        return {'status': 'error', 'message': f'程序内部错误', 'error': str(type(e))}
