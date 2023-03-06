import os
import hashlib
import sqlite3 as sql
import sys
import datetime as dt
import time
# import ctypes

db = sql.connect('./FileData.db')
cur = db.cursor()
res = cur.execute('select * from sqlite_master where type=\'table\'')
res = res.fetchall()
for ids in res:
	res = cur.execute(f'select * from "{ids[1]}" where FileSize=0;')
	for idx in res:
		print(idx)
		try:
			res = os.system(f'del /F /Q "{idx[0]}"')
			if res:
				with open('./error.log','a',encoding='utf8') as log:
					log.write(f'{dt.datetime.now()}\t')
					log.write(f'\tDelete File Failure:"{idx[0]}"\n')
			else:
				with open(idx[0],'w',encoding='utf8') as nf:
					nf.write('')
		except Exception as e:
			with open('./error.log','a',encoding='utf8') as log:
				log.write(f'{dt.datetime.now()}\t')
				log.write(f'\t{e}\n')