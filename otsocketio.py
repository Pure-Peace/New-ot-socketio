# -*- coding: utf-8 -*-
'''
otsu.fun - WebSockets

@version: 0.1
@author: PurePeace
@time: 2020-01-06

@describe: there are websockets!!!
'''

import utils, core
from flask import request, copy_current_request_context
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
from initial import app


# initial socketio server
server = SocketIO(app, async_mode='eventlet', cors_allowed_origins='*')

connections = []
disconnections = []
createdRooms = {}

indexByConnectId = {}
indexByOsuid = {}


def logger(text):
    print(f'[{utils.getTime(1)}]：{text}')


def getConnect(connectId, need='osuid'):
    data = indexByConnectId.get(connectId)
    if data != None: 
        if need != 'all':
            data = data.get(need)
    return data


def handleConnect(osuid, nick, request):
    connectid = request.sid
    data = {
        'osuid': osuid,
        'nick': nick,
        'connect_id': connectid,
        'ip': request.remote_addr,
        'user_agent': str(request.user_agent),
        'create_time': utils.getTime(1)
    }
    connections.append(data)
    indexByConnectId[connectid] = data
    if osuid in indexByOsuid:
        indexByOsuid[osuid].append(data)
    else:
        indexByOsuid[osuid] = [data]
    join_room(osuid, sid=connectid, namespace='/test')
    logger(rooms(connectid, namespace='/test'))
    logger(f'[{connectid}] user({osuid}) connected.')


def handleConnect2(serviceid, data, request):
    connectid = request.sid
    data['service_id'] = serviceid
    data['connect_id'] = connectid
    data['ip'] = request.remote_addr
    data['create_time'] = utils.getTime(1)
    connections.append(data)
    indexByConnectId[connectid] = data
    join_room(serviceid, sid=connectid, namespace='/service')
    logger(rooms(connectid, namespace='/service'))
    logger(f'[{connectid}] service({serviceid}) connected.')


def roomNotExists(room):
    if room in indexByOsuid: return False
    if room in indexByConnectId: return False
    if room in createdRooms: return False
    return True


def handelDisconnect(connectid):
    for i in range(len(connections)):
        if connections[i].get('connect_id') == connectid:
            osuid = connections[i].get('osuid')
            disconnections.append(connections[i])
            del(connections[i])
            break

    del(indexByConnectId[connectid])
    del(indexByOsuid[osuid])
    logger(f'[{connectid}] user({osuid}) disconnected.')


def handelDisconnect2(connectid):
    for i in range(len(connections)):
        if connections[i].get('connect_id') == connectid:
            serviceid = connections[i].get('service_id')
            disconnections.append(connections[i])
            del(connections[i])
            break

    logger(f'[{connectid}] service({serviceid}) disconnected.')


def apiSendBroadcast(data='', text='', action=''):
    if type(text) != str: return -1
    if type(action) != str: return -1
    if action in (None, ''): action = "otServer_msg"
    logger(f'server send broadcast, data: {text}')
    emit(action, {'data': data, 'msg': text}, broadcast=True, namespace='/test')
    return 1


def apiSendRoom(target='', data='', text='', action=''):
    if type(target) != str or target in (None, ''): return -1, '无效的收信人'
    if type(action) != str: return -1, '无效的action'
    if roomNotExists(target): return -1, '收信人处于离线状态'
    if action in (None, ''): action = 'otServer_msg'
    logger(f'send data to room: {target}, data: {text}, event: {action}.')
    server.emit(action, {'data': data, 'msg': text}, room=target, namespace='/test')
    return 1, '成功'


@server.on('otClient_sendServerMessage', namespace='/test')
def reciveClientMessage(data):
    message = data.get('message')
    osuid = getConnect(request.sid)

    logger(f'connection: {request.sid}：server recive message from {osuid} <ip: {request.remote_addr}>; text: {message if len(message) <= 300 else message[300]+"..."}.')

    emit('otServer_msg', {'msg': f'服务器已收到您的消息，内容：{message if len(message) <= 300 else message[300]+"..."}'})


@server.on('otClient_broadcastMessage', namespace='/test')
def clientBroadcastMessage(data):
    osuid = getConnect(request.sid)
    message = data.get('message')

    logger(f'connection：{request.sid}：client trying to broadcast, by {osuid} <ip: {request.remote_addr}>; text: {message if len(message) <= 300 else message[300]+"..."}.')

    if osuid in (None, ''):
        emit('otServer_msg', {'msg': '广播失败，信息不完整。'})
        logger('failed')
    else:
        emit('otServer_msg', {'msg': message, 'type': 'broadcast', 'from': osuid}, broadcast=True)
        logger('success')


@server.on('otClient_joinRoom', namespace='/test')
def clientJoinRoom(data):
    room = data.get('room')
    osuid = getConnect(request.sid)

    logger(f'connection: {request.sid}： tries to join room: {room} <ip: {request.remote_addr}> <by user: {osuid}>.')

    if room in (None, '') or osuid in (None, ''):
        emit('otServer_msg', {'msg': '加入房间失败，信息不完整。'})
        logger('failed')
    else:
        join_room(room)
        createdRooms[room] = {'createTime': utils.getTime(1), 'osuid': osuid, 'conid': request.sid}
        emit('otServer_msg', {'msg': f'用户 {osuid} 加入了房间：{room}'}, room=room)
        logger('success')


@server.on('otClient_leaveRoom', namespace='/test')
def clientLeaveRoom(data):
    @copy_current_request_context
    def realLeaveRoom(clientMessage):
        logger(f'[server do] try to let user {osuid} leave this room: {room}.')
        logger(f'connection：{request.sid}：client message: {clientMessage}')
        leave_room(room)
        logger('success')

    room = data.get('room')
    osuid = getConnect(request.sid)

    if room in (None, '') or osuid in (None, ''):
        emit('otServer_msg', {'msg': '离开房间失败，信息不完整。'})
        logger('failed')
    else:
        logger(f'connection: {request.sid}： tries to leave room: {room} <ip: {request.remote_addr}> <by user: {osuid}>.')
        emit('otServer_msg', {'msg': f'用户 {osuid} 离开了房间： {room}。'}, room=room, callback=realLeaveRoom)


@server.on('otClient_closeRoom', namespace='/test')
def clientCloseRoom(data):
    @copy_current_request_context
    def realCloseRoom(clientMessage):
        logger(f'[server do] server try to close this room: {room}.')
        logger(f'connection：{request.sid}：client message: {clientMessage}')
        close_room(room)
        del(createdRooms[room])
        logger('done')

    room = data.get('room')
    osuid = getConnect(request.sid)

    if room in (None, '') or osuid in (None, ''):
        emit('otServer_msg', {'msg': '关闭房间失败：信息不完整。'})
    if roomNotExists(room):
        emit('otServer_msg', {'msg': '关闭房间失败：房间不存在。'})
    else:
        logger(f'connection: {request.sid}： tries to close room: {room} <ip: {request.remote_addr}> <by user: {osuid}>.')
        emit('otServer_msg', {'msg': f'用户 {osuid} 关闭了房间： {room}。'}, room=room, callback=realCloseRoom)


@server.on('otClient_sendRoomMessage', namespace='/test')
def clientSendRoomMessage(data):
    @copy_current_request_context
    def sendMsgStatus(re):
        logger(f'[status] message sent {"successfully" if re == 1 else "failed"}.')

    room = data.get('room')
    connectInfo = getConnect(request.sid, 'all')
    osuid, nick = connectInfo.get('osuid'), connectInfo.get('nick')
    text = data.get('message')

    logger(f'connection: {request.sid}：tries to send a message to room {room} <ip: {request.remote_addr}> <by user: {osuid}>; text: text.')

    if room in (None, '') or osuid in (None, ''):
        emit('otServer_msg', {'msg': '发送失败，信息不完整。'})
    else:
        if type(text) != str:
            emit('otServer_msg', {'msg': '发送失败，消息类型错误。'}, callback=sendMsgStatus)
            logger('failed')
            return -1
        if len(text.encode()) > 1000:
            emit('otServer_msg', {'msg': f'发送失败，消息内容超长，请分{len(text.encode())//1000+1}次发送。'}, callback=sendMsgStatus)
            logger('failed')
            return -1

        logger(f'connection: {request.sid} try to sends a message to target: {room}')
        emit('otClient_msg', {'msg': text, 'from': osuid, 'nick': nick, 'from_conn': request.sid}, room=room, callback=sendMsgStatus)
        return 1



@server.on('otClient_disconnet', namespace='/test')
def clientDisconnect():
    @copy_current_request_context
    def realDisconnect(clientMessage):
        logger(f'[server do] server try to do disconnect.')
        logger(f'client message: {clientMessage}')
        disconnect()
        logger('success')

    logger(f'[server try] connection: {request.sid}： requests to disconnect <ip: {request.remote_addr}>.')

    emit('otServer_msg',{'msg': f'您主动与服务器断开连接。'}, callback=realDisconnect)


@server.on('otServer_stat', namespace='/test')
def serverMyStatus():
    emit('otServer_stat', {'c': len(indexByConnectId), 'u': len(indexByOsuid), 'r': list(indexByOsuid.keys()), 't': list(createdRooms.keys())})


@server.on('connect', namespace='/test')
def serverConnect():
    logger(f'[{request.sid}] try to connect user. do authentication <ip: {request.remote_addr}>.')

    osuid = request.args.get('osuid')
    token = request.args.get('otsu_token')
    re, status = core.authorizer(osuid, token)
    if status == 1:
        reData = re.get('data')
        if reData not in (None, ''): nick = reData.get('osuname')
        else: nick = '未知'
        handleConnect(osuid, nick, request)
        emit('otClient_connected', {'connection': request.sid, 'osuid': osuid})
        emit('otServer_msg', {'msg': f'user：{osuid}，您已经成功连接服务器。'})
    else:
        logger(f'[{request.sid}] user({osuid}) authentication failed, rejected.')
        disconnect()
        logger('disconnet success')



@server.on('connect', namespace='/service')
def serverConnect2():
    logger(f'[{request.sid}] try to connect service. do authentication <ip: {request.remote_addr}>.')
    serviceid = request.args.get('service_id')
    key = request.args.get('key')
    re, status = core.serviceAuthorizer(serviceid, key)
    if status == 1:
        handleConnect2(serviceid, re, request)
        servicename = re.get('service_name')
        emit('otClient_connected', {
            'connection': request.sid, 
            'service_id': serviceid, 
            'service_name': servicename,
            'service_info': re.get('service_info')
            }
        )
        emit('otServer_msg', {'msg': f'service：{servicename}({serviceid})，您已经成功连接到中间api。'})
    else:
        logger(f'[{request.sid}] service({serviceid}) authentication failed, rejected.')
        disconnect()
        logger('disconnet success')


@server.on('disconnect', namespace='/service')
def serverDisconnect2():
    logger(f'[{request.sid}] disconnect.')
    try:
        handelDisconnect2(request.sid)
    except:
        pass
    emit('otServer_msg', {'msg': f'您已经从服务器断开连接。'})



@server.on('disconnect', namespace='/test')
def serverDisconnect():
    logger(f'[{request.sid}] disconnect.')
    try:
        handelDisconnect(request.sid)
    except:
        pass
    emit('otServer_msg', {'msg': f'您已经从服务器断开连接。'})


if __name__ == '__main__':
    print('just websocket server.but it dosnt work')