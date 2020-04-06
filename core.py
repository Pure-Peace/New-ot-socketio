# -*- coding: utf-8 -*-
'''
otsu.fun - SSWA Core

@version: 0.1
@author: PurePeace
@time: 2020-01-07

@describe: core is heart!!!
'''

import utils
import requests
import otsocketio


# verify user authorization information
def authorizeGuard(needLevel):
    def wrapper(func):
        def haha(*args, **kw):
            authorize = kw.pop('authorization')
            re, status = authorizer(authorize.get('osuid'), authorize.get('otsuToken'))
            if status == 1:
                data = re.get('data')
                if data != None and data.get('userLevel') >= needLevel:
                    if authorize.get('path') not in data.get('cantUse'):
                        ret = func(*args,**kw)
                        return ret
            return None, '访问被拒绝啦', '鉴权', -1
        return haha
    return wrapper


def authorizer(osuid, token):
    re, status = None, -1
    if osuid not in (None, '') and token not in (None, ''):
        headers = {'osuid': osuid, 'X-OtsuToken': token}
        resp = requests.post(f'http://{baseApi}:9529/loginStatusChecker',headers=headers)
        if resp.status_code == 200:
            re = resp.json()
            if re.get('status') == 1: status = 1
    return re, status


def serviceAuthorizer(serviceid, key):
    fake = [{'serviceid': '1', 'key': '7355608'}]
    re, status = None, -1
    if serviceid not in (None, '') and key not in (None, ''):
        for i in fake:
            if i['serviceid'] == serviceid and i['key'] == key:
                status = 1
                re = {'service_name': '小喵bot', 'service_info': '测试服务'}
    return re, status


@utils.messager
#@authorizeGuard(needLevel=90)
def handleGetCons(data, info='获取查看服务器连接信息', message='', status=-1):
    if data != None: action = data.get('action')
    else: action = ''
    if action == 'filterByOsuid':
        need = otsocketio.indexByOsuid
    elif action == 'filterByConid':
        need = otsocketio.indexByConnectId
    elif action == 'getDiscon':
        need = otsocketio.disconnections
    else:
        need = otsocketio.connections
    data = {'connections': need, 'count': len(need)}
    return data, message, info, 1


@utils.messager
#@authorizeGuard(needLevel=90)
def handleGetRooms(data, info='获取聊天房间列表', message='', status=-1):
    need = otsocketio.createdRooms
    data = {'createdRooms': need, 'count': len(need)}
    return data, message, info, 1


@utils.messager
#@authorizeGuard(needLevel=90)
def handleGetServerStatus(data, info='获取服务器状态', message='', status=-1):
    currentCon = len(otsocketio.connections)
    discon = len(otsocketio.disconnections)
    users = len(otsocketio.indexByOsuid)
    rooms = len(otsocketio.createdRooms)
    data = {'totalCons': currentCon + discon ,'currentCons': currentCon, 'currentUsers': users, 'rooms': rooms, 'disconnetions': discon, }
    message = f'服务器截止目前已经服务了{currentCon + discon}个连接。当前活动连接数：{currentCon}，活动用户数：{users}，聊天房间数：{rooms}。'
    return data, message, info, 1


@utils.messager
#@authorizeGuard(needLevel=90)
def handleSendBroadcast(res, info='向所有连接发送广播', message='', status=-1):
    data = res.get('data')
    text = res.get('text')
    action = res.get('action')
    status = otsocketio.apiSendBroadcast(data, text, action)
    if status == 1:
        data = {'res': f'广播成功！此消息已向{len(otsocketio.indexByOsuid)}个用户推送。连接总数{len(otsocketio.connections)}。'}
    else: 
        data = '广播失败'
    return data, message, info, status


@utils.messager
#@authorizeGuard(needLevel=90)
def handleSendMultiMessage(data, info='发送多人消息', message='', status=-1):
    queue = data.get('queue')
    result = []
    count, failed, success = 0, 0, 0
    if type(queue) == list:
        status = 1
        for dt in queue:
            rss, rsinfo = otsocketio.apiSendRoom(dt.get("target"),dt.get("data"),dt.get("text"),dt.get('action'))
            if rss == 1:
                stat = '成功'
                success += 1
            else: 
                stat = '失败'
                failed += 1
            count += 1
            result.append({'num': count, 'staus': stat, 'data': dt, 'info': rsinfo, 'time': utils.getTime(1)})

    return {'result': result, 'count': count, 'success': success, 'fail': failed}, message, info, status


@utils.messager
#@authorizeGuard(needLevel=90)
def handleMassMessage(data, info='发送群发消息', message='', status=-1):
    queue = data.get('target')
    content = data.get('content')
    result = []
    count, failed, success = 0, 0, 0
    if type(queue) == list:
        status = 1
        for tt in queue:
            rss, rsinfo = otsocketio.apiSendRoom(tt, content.get("data"),content.get("text"),content.get('action'))
            if rss == 1:
                stat = '成功'
                success += 1
            else: 
                stat = '失败'
                failed += 1
            count += 1
            result.append({'num': count, 'staus': stat, 'info': rsinfo, 'time': utils.getTime(1)})

    return {'result': result, 'count': count, 'success': success, 'fail': failed}, message, info, status


# data getter? get my data!!!
def dataGetter(request, needDataKeys=None, error='请求内容不完整', strict=True):
    reqInfo = utils.makeRequestInfo(request)
    if needDataKeys != None:
        data = {k:v for d in [request.get_json(), request.headers] for k,v in d.items() if k in needDataKeys}
        if strict:
            for key in needDataKeys:
                if key not in data or data.get(key) == None: return error, -1, None
    else:
        try:
            data = request.get_json()
        except:
            data = None
    return data, 1, reqInfo


# some content type
formType = 'application/x-www-form-urlencoded'
jsonType = 'application/json'

# base api
baseApi = 'otsu.fun'
#baseApi = '127.0.0.1'

# run? not.
if __name__ == '__main__':
    print('only core, so it doesnt work')
