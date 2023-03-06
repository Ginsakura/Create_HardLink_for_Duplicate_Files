import os
import hashlib
import sqlite3 as sql
import sys
import datetime as dt
import time
# import ctypes

db = sql.connect('./FileData.db')
cur = db.cursor()
res = cur.execute('select * from sqlite_master')
for ids in res:
	res = cur.execute(f'select * from "{ids[1]}" where FileSize=0;')
	for idx in res:
		print(idx)
		os.system(f'del /F /Q "{idx[0]}"')
		with open(idx[0],'w',encoding='utf8') as nf:
			nf.write('')