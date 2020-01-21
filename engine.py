# -*- coding: utf-8 -*-
'''
otsu.fun - Socketio Service With Api

@version: 0.1
@author: PurePeace
@time: 2020-01-07

@describe: run this file to serve.
'''

from flask import request
from flask_restplus import Resource, fields, Api
from otsocketio import app, server
import utils, docs, core


# app config / app设置
api = Api(app, version='0.01',title='otsu.fun - Socketio Service With Api',description='Made by PurePeace', path='/')


# namespace / 命名空间
getConnections = api.namespace('getConnections', description='获取查看服务器连接信息', path='/')
getRooms = api.namespace('getRooms', description='获取聊天房间列表', path='/')
getServerStatus = api.namespace('getServerStatus', description='获取服务器状态', path='/')
getNoSpeaking = api.namespace('getNoSpeaking', description='in Progress // 获取禁言列表', path='/')
getNoConnect = api.namespace('getNoConnect', description='in Progress // 获取禁止连接列表', path='/')
sendBroadcast = api.namespace('sendBroadcast', description='发送广播到所有连接', path='/')
sendMultiMessage = api.namespace('sendMultiMessage', description='发送多人消息（消息内容不同）', path='/')
sendMassMessage = api.namespace('sendMassMessage', description='发送群发消息（消息内容相同）', path='/')
closeRoom = api.namespace('closeRoom', description='in Progress // 将房间关闭', path='/')
joinRoom = api.namespace('joinRoom', description='in Progress // 将某人加入房间', path='/')
kickRoom = api.namespace('kickRoom', description='in Progress // 踢出房间', path='/')
noSpeaking = api.namespace('noSpeaking', description='in Progress // 禁言', path='/')
noConnect = api.namespace('noConnect', description='in Progress // 禁止某ip或用户连接服务器', path='/')
kickServer = api.namespace('kickServer', description='in Progress // 踢出服务器', path='/')



# pasers / 增加的参数
parser_token = api.parser().add_argument('X-OtsuToken', location='headers', type=str)
parser_osuid = api.parser().add_argument('osuid', location='headers', type=str)


# model / 固定参数类型
queryAction = api.model('queryAction', {'action': fields.String(description='查询参数', example='')})

closeRoomModel = api.model('closeRoomModel', {
    'room': fields.String(required=True,description='要关闭的房间（可批量）', example=['房间']),
    'reason': fields.String(description='原因', example='搞黄色')
})

joinRoomModel = api.model('joinRoomModel', {
    'room': fields.String(required=True,description='要加入的房间', example='xxx'),
    'reason': fields.String(description='原因', example='搞黄色'),
    'target': fields.String(required=True,description='将谁加入房间（可批量）', example=['张三','李四','聊天房间1','...'])
})

kickRoomModel = api.model('kickRoomModel', {
    'room': fields.String(required=True,description='要踢出的房间', example='xxx'),
    'reason': fields.String(description='原因', example='搞黄色'),
    'target': fields.String(required=True,description='要踢出谁（可批量）', example=['张三','李四','聊天房间1','...'])
})

noSpeakingModel = api.model('noSpeakingModel', {
    'room': fields.String(required=True,description='房间', example='xxx'),
    'target': fields.String(required=True,description='要禁言谁', example='xxx'),
    'reason': fields.String(description='原因', example='搞黄色'),
    'action': fields.String(required=True,description='动作', example='')
})

noConnectModel = api.model('noConnectModel', {
    'target': fields.String(required=True,description='要禁止谁连接', example='xxx'),
    'type': fields.String(required=True,description='类型', example='ip / osuid'),
    'reason': fields.String(description='原因', example='搞黄色'),
    'duration': fields.String(required=True,description='持续时间', example='')
})

kickServerModel = api.model('kickServerModel', {
    'target': fields.String(required=True,description='要踢出谁', example='xxx'),
    'reason': fields.String(description='原因', example='搞黄色'),
    'action': fields.String(required=True,description='动作', example='')
})

broadcast = api.model('broadcast', {
    'data': fields.String(description='any', example=''),
    'text': fields.String(required=True, description='广播内容', example='你好！'),
    'action': fields.String(required=True, description='动作', example='otServer_msg'),
})

multiMessage = api.model('multiMessage', {
    'queue': fields.String(required=True, description='发送消息列表', example=[
        {'target': '收信人id', 'text': '消息内容', 'action': 'otServer_msg'}
    ])
})

massMessageModel = api.model('massMessageModel', {
    'content': fields.String(required=True,description='消息内容', example={'data': ['测试数据'], 'text': '文本数据', 'action': 'otServer_msg'}),
    'target': fields.String(required=True,description='收信人列表', example=['张三','李四','聊天房间1','...'])
})

# interceptor / 全局拦截器
#@app.before_request
def interceptor():
    if request.remote_addr == None:
        return {'message': 'The server is currently not allowed access', 'status': -1}


# 查看连接列表
@getConnections.route('/getConnections')
#@getConnections.expect(parser_token, parser_osuid)
@getConnections.doc(body=queryAction)
class getConnections(Resource):
    @utils.docsParameter(docs.demo)
    def post(self):
        #authorize, status = utils.makeAuthorizeInfo(request)
        #if status == -1: return utils.messageMaker('授权认证参数不完整', status=-1)

        data, status, reqInfo = core.dataGetter(request, ['action'], strict=False)

        if status == -1: return utils.messageMaker(data, status=-1)
        return core.handleGetCons(data)


# 主动广播
@sendBroadcast.route('/sendBroadcast')
#@sendBroadcast.expect(parser_token, parser_osuid)
@sendBroadcast.doc(body=broadcast)
class sendBroadcast(Resource):
    @utils.docsParameter(docs.demo)
    def post(self):
        #authorize, status = utils.makeAuthorizeInfo(request)
        #if status == -1: return utils.messageMaker('授权认证参数不完整', status=-1)

        res, status, reqInfo = core.dataGetter(request, ['data', 'text', 'action'])

        if status == -1: return utils.messageMaker(res, status=-1)
        return core.handleSendBroadcast(res) # authorization=authorize



# 对目标发送
@sendMultiMessage.route('/sendMultiMessage')
#@multiMessage.expect(parser_token, parser_osuid)
@sendMultiMessage.doc(body=multiMessage)
class sendMultiMessage(Resource):
    @utils.docsParameter(docs.demo)
    def post(self):
        #authorize, status = utils.makeAuthorizeInfo(request)
        #if status == -1: return utils.messageMaker('授权认证参数不完整', status=-1)

        data, status, reqInfo = core.dataGetter(request, ['queue'])

        if status == -1: return utils.messageMaker(data, status=-1)
        return core.handleSendMultiMessage(data) # authorization=authorize


# 群发
@sendMassMessage.route('/sendMassMessage')
#@sendMassMessage.expect(parser_token, parser_osuid)
@sendMassMessage.doc(body=massMessageModel)
class sendMassMessage(Resource):
    @utils.docsParameter(docs.demo)
    def post(self):
        #authorize, status = utils.makeAuthorizeInfo(request)
        #if status == -1: return utils.messageMaker('授权认证参数不完整', status=-1)

        data, status, reqInfo = core.dataGetter(request, ['content','target'])

        if status == -1: return utils.messageMaker(data, status=-1)
        return core.handleMassMessage(data) # authorization=authorize


# 关房间
@closeRoom.route('/closeRoom')
#@closeRoom.expect(parser_token, parser_osuid)
@closeRoom.doc(body=closeRoomModel)
class closeRoom(Resource):
    @utils.docsParameter(docs.demo)
    def post(self):
        #authorize, status = utils.makeAuthorizeInfo(request)
        #if status == -1: return utils.messageMaker('授权认证参数不完整', status=-1)

        data, status, reqInfo = core.dataGetter(request, ['room','reason'])

        if status == -1: return utils.messageMaker(data, status=-1)
        return core.handleCloseRoom(data) # authorization=authorize


# 将xx加入房间
@joinRoom.route('/joinRoom')
#@joinRoom.expect(parser_token, parser_osuid)
@joinRoom.doc(body=joinRoomModel)
class joinRoom(Resource):
    @utils.docsParameter(docs.demo)
    def post(self):
        #authorize, status = utils.makeAuthorizeInfo(request)
        #if status == -1: return utils.messageMaker('授权认证参数不完整', status=-1)

        data, status, reqInfo = core.dataGetter(request, ['room','reason','target'])

        if status == -1: return utils.messageMaker(data, status=-1)
        return core.handleJoinRoom(data) # authorization=authorize


# 将xx踢出房间
@kickRoom.route('/kickRoom')
#@kickRoom.expect(parser_token, parser_osuid)
@kickRoom.doc(body=kickRoomModel)
class kickRoom(Resource):
    @utils.docsParameter(docs.demo)
    def post(self):
        #authorize, status = utils.makeAuthorizeInfo(request)
        #if status == -1: return utils.messageMaker('授权认证参数不完整', status=-1)

        data, status, reqInfo = core.dataGetter(request, ['room','target','reason'])

        if status == -1: return utils.messageMaker(data, status=-1)
        return core.handleKickRoom(data) # authorization=authorize


# 将xx踢出服务器
@kickServer.route('/kickServer')
#@kickServer.expect(parser_token, parser_osuid)
@kickServer.doc(body=kickServerModel)
class kickServer(Resource):
    @utils.docsParameter(docs.demo)
    def post(self):
        #authorize, status = utils.makeAuthorizeInfo(request)
        #if status == -1: return utils.messageMaker('授权认证参数不完整', status=-1)

        data, status, reqInfo = core.dataGetter(request, ['target','reason','action'])

        if status == -1: return utils.messageMaker(data, status=-1)
        return core.handleKickServer(data) # authorization=authorize


# 将xx禁言
@noSpeaking.route('/noSpeaking')
#@noSpeaking.expect(parser_token, parser_osuid)
@noSpeaking.doc(body=noSpeakingModel)
class noSpeaking(Resource):
    @utils.docsParameter(docs.demo)
    def post(self):
        #authorize, status = utils.makeAuthorizeInfo(request)
        #if status == -1: return utils.messageMaker('授权认证参数不完整', status=-1)

        data, status, reqInfo = core.dataGetter(request, ['room','target','reason','action'])

        if status == -1: return utils.messageMaker(data, status=-1)
        return core.handleNoSpeaking(data) # authorization=authorize


# 禁止xx连接服务器
@noConnect.route('/noConnect')
#@noConnect.expect(parser_token, parser_osuid)
@noConnect.doc(body=noConnectModel)
class noConnect(Resource):
    @utils.docsParameter(docs.demo)
    def post(self):
        #authorize, status = utils.makeAuthorizeInfo(request)
        #if status == -1: return utils.messageMaker('授权认证参数不完整', status=-1)

        data, status, reqInfo = core.dataGetter(request, ['target','type','reason','duration'])

        if status == -1: return utils.messageMaker(data, status=-1)
        return core.handleNoConnect(data) # authorization=authorize


# 查看room列表
@getRooms.route('/getRooms')
#@getRooms.expect(parser_token, parser_osuid)
class getRooms(Resource):
    @utils.docsParameter(docs.demo)
    def post(self):
        #authorize, status = utils.makeAuthorizeInfo(request)
        #if status == -1: return utils.messageMaker('授权认证参数不完整', status=-1)

        data, status, reqInfo = core.dataGetter(request)

        if status == -1: return utils.messageMaker(data, status=-1)
        return core.handleGetRooms(data) # authorization=authorize


# server status
@getServerStatus.route('/getServerStatus')
#@getServerStatus.expect(parser_token, parser_osuid)
class getServerStatus(Resource):
    @utils.docsParameter(docs.demo)
    def post(self):
        #authorize, status = utils.makeAuthorizeInfo(request)
        #if status == -1: return utils.messageMaker('授权认证参数不完整', status=-1)

        data, status, reqInfo = core.dataGetter(request)

        if status == -1: return utils.messageMaker(data, status=-1)
        return core.handleGetServerStatus(data) # authorization=authorize

# run? yes!
if __name__ == '__main__':
    utils.logtext('starting service...')
    server.run(app, host='0.0.0.0', port=9530)
    # app.run(port=9530)
