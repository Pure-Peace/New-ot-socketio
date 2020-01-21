# -*- coding: utf-8 -*-
'''
otsu.fun - SSWA Utils

@version: 0.1
@author: PurePeace
@time: 2020-01-07

@describe: a treasure house!!!
'''

import time, datetime


# way to return utInfo, decorator
def messager(func):
    def wrapper(*args, **kwargs):
        data, message, info, status = func(*args,**kwargs)
        if message == '': message = info
        return messageMaker(data, message, info + statusInfo.get(status,'状态未知'), status)
    return wrapper


# make messager
def messageMaker(data=None, message=None, info=None, status=None):
    return {'message':message, 'data':data, 'status':status, 'info': info, 'time':getTime(1)}


# get now timeString or timeStamp
def getTime(needFormat=0, formatMS=True):
    if needFormat != 0:
        return datetime.datetime.now().strftime(f'%Y-%m-%d %H:%M:%S{r".%f" if formatMS else ""}')
    else:
        return time.time()


# timeString to timeStamp
def toTimeStamp(timeString):
    if '.' not in timeString: getMS = False
    else: getMS=True
    timeTuple = datetime.datetime.strptime(timeString, f'%Y-%m-%d %H:%M:%S{r".%f" if getMS else ""}')
    return float(f'{str(int(time.mktime(timeTuple.timetuple())))}' + (f'.{timeTuple.microsecond}' if getMS else ''))


# timeStamp to timeString
def toTimeString(timeStamp):
    if type(timeStamp) == int: getMS = False
    else: getMS = True
    timeTuple = datetime.datetime.utcfromtimestamp(timeStamp + 8 * 3600)
    return timeTuple.strftime(f'%Y-%m-%d %H:%M:%S{r".%f" if getMS else ""}')


# generate method docs str
def docsParameter(sub):
    def dec(obj):
       obj.__doc__ = sub
       return obj
    return dec


# make text include time
def logtext(text):
    logtext = f'[{getTime(1)}]: {text}'
    print(logtext)
    return logtext


# make request record info
def makeRequestInfo(request):
    return {
        'remote_addr': request.remote_addr,
        'system': request.headers.get('system_info'),
        'request': {
            'environ': request.environ,
            'url': request.url
        }
    }


# make authorize info
def makeAuthorizeInfo(request):
    otsuToken, osuid = request.headers.get('X-Otsutoken'), request.headers.get('osuid')
    if otsuToken == None or osuid == None: status = -1
    else: status = 1
    return {'otsuToken': otsuToken, 'osuid': osuid, 'path': request.path.strip('/')}, status


statusInfo = {
    1: '成功',
    -1: '失败'
}


# run? not.
if __name__ == '__main__':
    print('wow, you find a treasure house!!! so it dosent work')
