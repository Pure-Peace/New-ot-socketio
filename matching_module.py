# -*- coding: utf-8 -*-
"""
@name: test
@author: PurePeace
"""
import requests
from utils import getTime


class Matching:
    def __init__(self, name):
        log(f'初始化Matching：name({name})')
        self.name = name
        self.room = Space('room')
        self.queue = Space('queue')
        self.create_time = getTime(1)
    
    
    def create_join(self, *args, **kwargs):
        '''
        初始化玩家并加入空间（默认为room），参数与Player类__init__方法的参数一致
        '''
        player = Player(*args, **kwargs)
        return self.join(player, space='room')
    
    
    def join(self, player, space='room'):
        '''
        将玩家加入空间（默认为room），需要玩家对象已经被初始化
        '''
        return eval(f'self.{space}').join(player)
        

    def find_player(self, player_key, key_type='osuid', space=None):
        '''
        在所有空间中或指定空间中寻找玩家，player_key可以为osuid、osuname等
        '''
        log(f'matching({self.name})：查找玩家{key_type}({player_key})，指定空间：space({space})')
        if space in (None, ''):
            spaces = [self.room, self.queue]
        else:
            spaces = eval(f'self.{space}')
        for space in spaces:
            player = space.find_player(player_key, key_type)
            if player != None:
                return player
        log(f'matching({self.name})中未找到玩家{key_type}({player_key})')
    
    
    @property
    def all_players(self, attr=None):
        '''
        获得所有空间中的玩家对象列表
        '''
        result = self.room.players + self.queue.players
        if attr != None:
            result = [eval(f'i.{attr}') for i in result]
        return result
    
    
class Space:
    def __init__(self, name):
        log(f'初始化Space：name({name})')
        self.name = name
        self.players = []
        self.create_time = getTime(1)
        self.last_update = getTime(1)


    def join(self, player):
        if player.initial_status == True:
            tip =  f'玩家osuid({player.osuid}) osuname({player.osuname})'
            log(f'{tip}请求加入空间{self.name}...')
            if self.find_player(player.osuid) != None:
                log(f'{tip}加入失败，空间{self.name}已经存在此玩家，不可重复加入')
                return False
            self.players.append(player)
            self.last_update = getTime(1)
            log(f'{tip}成功加入空间{self.name}，当前空间大小：{len(self.players)}')
            return True
        log(f'玩家信息尚未初始化，加入{self.name}请求被拒绝')
    
    
    def find_player(self, player_key, key_type='osuid'):
        log(f'正在查找{self.name}中的玩家对象：{key_type}({player_key})')
        key_type = key_type_fixer(player_key, key_type)
        if key_type == 'osuname':
            player_key = player_key.lower()
        for item in self.players:
            s = eval(f'item.{key_type}')
            if key_type == 'osuname':
                s = s.lower()
            if s == player_key:
                log(f'已找到并返回{self.name}中的玩家对象：osuid({item.osuid}) osuname({item.osuname})')
                return item
        log(f'{self.name}：未能找到玩家')

    
    def pop_player(self, osuid):
        index = self.index_player(osuid)
        if index != None:
            item = self.players.pop(index)
            log(f'{self.name}：弹出玩家 osuid({item.osuid}) osuname({item.osuname})')
            return item
        log(f'{self.name}：未找到玩家，弹出失败')
    
    
    def index_player(self, osuid):
        log(f'正在查找{self.name}中的玩家下标：osuid({osuid})')
        for index in range(len(self.players)):
            item = self.players[index]
            if item.osuid == osuid:
                log(f'已找到{self.name}中玩家下标({index})：osuid({item.osuid}) osuname({item.osuname})')
                return index
        log(f'{self.name}未找到玩家下标：osuid({osuid})')


    @property
    def size(self):
        return len(self.players)
    
    
    def group_by_key(self, player_key, key_type='status'):
        return [p for p in self.players if eval(f'p.{key_type}') == player_key]


    @property
    def group_by_elo(self):
        group = {}
        for p in self.players:
            if p.elo_level not in group:
                group[p.elo_level] = [p]
            else:
                group[p.elo_level].append(p)
        return group
    
    
class Player:
    def __init__(self, player_key=None, key_type='osuid', matching_mode='default', initial_from='default', info='', contact=''):
        self.osuid = None
        self.osuname = None
        self.elo = None
        self.init_elo = None
        self.elo_time = None
        self.pp = None
        self.rank = None
        self.country = None
        self.info = info
        self.contact = contact
        self.status = 'idle'
        self.initial_status = False
        self.initial_from = initial_from
        self.matching_mode = matching_mode

            
        if player_key not in (None, ''):
            log(f'初始化玩家信息：key({player_key}) type({key_type})')
            if not isinstance(player_key, str):
                player_key = str(player_key)
            if key_type not in ('osuid', 'osuname'):
                key_type = 'osuid'
                log(f'key({player_key})：不合法的type({key_type})，将其重置为默认值(osuid)')
                
            key_type = key_type_fixer(player_key, key_type)
            
            if self.get_osu_data(player_key, key_type) == True:
                if self.get_elo_data(self.osuid) == True:
                    self.initial_status = True
                    log(f'初始化玩家信息成功：osuid({self.osuid}) osuname({self.osuname}) {str(self.__dict__)}')
                
            self.create_time = getTime(1)
            if self.initial_status == False:
                log(f'初始化玩家信息失败：key({player_key}) type({key_type})')
        else:
            log(f'未发现player_key，玩家信息为空，请后续手动执行玩家初始化')


    def get_elo_data(self, osuid=None):
        if osuid == None: osuid = self.osuid
        tip = f'osuid({osuid})'
        for i in range(3):
            log(f'正在请求玩家elo数据({i})：{tip}')
            resp = requests.get(f'http://api.osuwiki.cn:5005/api/users/elo/{osuid}')
            if resp.status_code in range(200, 207):
                data = resp.json()
                elo_time = getTime(1)
                elo = data.get('elo')
                init_elo = data.get('init_elo')
                elo_rank = data.get('rank')
                never_match = (elo_rank == None)
                
                if elo or init_elo:
                    self.elo = elo
                    self.init_elo = init_elo
                    self.elo_time = elo_time
                    self.elo_rank = elo_rank
                    self.never_match = never_match
                    self.elo_level, self.elo_level_range = self.get_elo_level()
                    log(f'成功取得玩家elo数据({i})：{tip} elo({elo}) init_elo({init_elo}) elo_time({elo_time}) never_match({never_match}) {str(data)}')
                    return True
                
            if i < 2:
                log(f'玩家elo数据请求失败，准备进行重试({i})：{tip}')
            else:
                log(f'玩家elo数据请求失败，重试次数已达上限({i})，请重新提交初始化请求：{tip}')
    
    
    def get_elo_level(self, elo=None):
        if elo == None: elo = self.elo
        ranges = {
            '青铜': range(0, 600),
            '白银': range(601, 1000),
            '黄金': range(1001, 1400),
            '白金': range(1401, 1800),
            '钻石': range(1801, 2200),
            '王者': range(2201, 9999)
        }
        for k, v in ranges.items():
            if elo in v:
                log(f'玩家elo{elo}，段位：{k}')
                return k, v
        log(f'无法找到玩家段位')
        return None, None
        
        
    def get_osu_data(self, player_key=None, key_type='osuid'):
        if player_key == None: player_key = self.osuid
        key_type = key_type_fixer(player_key, key_type)
        osuData = {}
        tip = f'key({player_key}) type({key_type})'
        for i in range(3):
            log(f'正在请求玩家osu数据({i})：{tip}')
            resp = requests.get(f'http://otsu.fun:9529/getPlayerDataV1?playerKey={player_key}&action=simple&keyType={key_type}')
            if resp.status_code == 200:
                data = resp.json()
                if data.get('status') == 1:
                    osuData = data.get('data', {})

                osuid = osuData.get('osuid')
                osuname = osuData.get('osuname')
                country = osuData.get('country')
                pp = osuData.get('pp')
                rank = osuData.get('rank')
                
                if osuid and osuname :
                    self.osuid = osuid
                    self.osuname = osuname
                    self.pp = pp
                    self.rank = rank
                    self.country = country
                    log(f'成功取得玩家osu数据({i})：osuid({osuid}) osuname({osuname}) {str(osuData)}')
                    return True
                
            if i < 2:
                log(f'玩家osu数据请求失败，准备进行重试({i})：{tip}')
            else:
                log(f'玩家osu数据请求失败，重试次数已达上限({i})，请重新提交初始化请求：{tip}')


def key_type_fixer(player_key, key_type):
    if key_type == 'osuid' and player_key.isdigit() == False:
        key_type = 'osuname'
        log(f'key({player_key})：type应为(osuname)而非(osuid)，将对其进行修正')
    return key_type


def log(text):
    print(f'[{getTime(1)}] {text}')


# apis
m = Matching('main') # 创建matching对象
p = Player('5084172') # 创建player
p.__dict__ # 查看player所有属性


# 创建加入玩家
m.create_join('5084172') 
m.join(Player('5084172')) # 等同于上

# 在matching对象的所有空间中寻找玩家
m.find_player('5084172')
m.all_players

# 分组
m.room.size
m.room.group_by_elo
m.room.group_by_key('idle') 

# 查找
m.room.find_player('5084172')
m.room.find_player('白金', 'elo_level')  # 按段位查找
m.room.find_player('purePeace', 'osuname') 

# 查找玩家下标
m.room.index_player('5084172')

# 弹出room中指定玩家
m.room.pop_player('5084172') 
m.room.size
m.all_players # 取matching对象中所有玩家

# 刷新玩家数据
p.get_elo_data() 
p.get_osu_data()
p.__dict__

# 懒创建
p2 = Player()
p2.__dict__
m.join(p2) # 无法加入未初始化的玩家对象
m.room.join(p2) # 同上
p2.__init__('5084172') # 初始化
p2.__dict__
p2.get_elo_level()
