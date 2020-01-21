# -*- coding: utf-8 -*-
'''
otsu.fun - Website Api Initial

@version: 0.9
@author: PurePeace
@time: 2019-12-10

@describe: initial some config.
'''

from flask import Flask
from flask_cors import CORS


# initial(s)
app = Flask('engine')
app.config.update(RESTFUL_JSON=dict(ensure_ascii=False))
CORS(app)



# run? no.
if __name__ == '__main__':
    print('only initial, so it dosent work!!')
