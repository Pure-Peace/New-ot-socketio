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

connections = []
disconnections = []
createdRooms = {}

indexByConnectId = {}
indexByOsuid = {}


# initial socketio server
server = SocketIO(app, async_mode='eventlet', cors_allowed_origins='*')


def logger(text):
    print(f'[{utils.getTime(1)}]：{text}')


def getOsuid(connectId):
    data = indexByConnectId.get(connectId)
    if data != None: data = data.get('osuid')
    return data


def handleConnect(osuid, request):
    connectid = request.sid
    data = {
        'osuid': osuid,
        'connectid': connectid,
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
    logger(f'connection：{connectid} authenticated and joined to the session, <by(user): {osuid}> .')


def roomNotExists(room):
    if room in indexByOsuid: return False
    if room in indexByConnectId: return False
    if room in createdRooms: return False
    return True


def handelDisconnect(connectid):
    for i in range(len(connections)):
        if connections[i].get('connectid') == connectid:
            osuid = connections[i].get('osuid')
            disconnections.append(connections[i])
            del(connections[i])
            break

    del(indexByConnectId[connectid])
    del(indexByOsuid[osuid])
    logger(f'connection：{connectid} has disconnected the server, <by(user): {osuid}> .')



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
    osuid = getOsuid(request.sid)

    logger(f'connection: {request.sid}：server recive message from {osuid} <ip: {request.remote_addr}>; text: {message if len(message) <= 300 else message[300]+"..."}.')

    emit('otServer_msg', {'msg': f'服务器已收到您的消息，内容：{message if len(message) <= 300 else message[300]+"..."}'})


@server.on('otClient_broadcastMessage', namespace='/test')
def clientBroadcastMessage(data):
    osuid = getOsuid(request.sid)
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
    osuid = getOsuid(request.sid)

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
    osuid = getOsuid(request.sid)

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
    osuid = getOsuid(request.sid)

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
    osuid = getOsuid(request.sid)
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
        emit('otClient_msg', {'msg': text, 'from': osuid, 'from_conn': request.sid}, room=room, callback=sendMsgStatus)
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
    logger(f'connection: {request.sid}：a connection request has been received, the upcoming user authentication <ip: {request.remote_addr}>.')

    osuid = request.args.get('osuid')
    token = request.args.get('otsu_token')
    re, status = core.authorizer(osuid, token)
    if status == 1:
        handleConnect(osuid, request)
        emit('otClient_connected', {'connection': request.sid, 'osuid': osuid})
        emit('otServer_msg', {'msg': f'user：{osuid}，您已经成功连接服务器。'})
    else:
        logger(f'connection: {request.sid}：user authentication failed, connection request was rejected <ip: {request.remote_addr}>.')
        disconnect()
        logger('success')






@server.on('disconnect', namespace='/test')
def serverDisconnect():
    logger(f'connection: {request.sid} disconnect.')
    try:
        handelDisconnect(request.sid)
    except:
        pass
    emit('otServer_msg', {'msg': f'您已经从服务器断开连接。'})


if __name__ == '__main__':
    print('just websocket server.but it dosnt work')