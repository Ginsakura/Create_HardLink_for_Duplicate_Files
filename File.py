import os
import hashlib
import sqlite3
import sys
# import time
# import ctypes

class File(object):
	"""docstring for File"""
	def __init__(self, path):
		self.path = path
		self.filePathName = ''
		self.fileSize = ''
		self.fileMD5 = ''
		self.mem=0
		if os.path.isfile('./FileData.db'):
			self.mdb = sqlite3.connect(':memory:')
			self.mcur = self.mdb.cursor()
			self.mem=1
		self.isDB()
		self.db = sqlite3.connect('./FileData.db')
		self.cur = self.db.cursor()
		self.cur.execute('PRAGMA synchronous = OFF')
		if self.mem:
			script = ''.join(self.db.iterdump())
			self.mdb.executescript(script)
			print('Load memory SQLite.')


	def isDB(self):
		db=sqlite3.connect('./FileData.db')
		cur = db.cursor()
		exist = cur.execute(f'select * from sqlite_master where type=\'table\' and name=\'FileList\'')
		exist = exist.fetchone()
		if not exist:
			cur.execute(f'''
				Create table 
				FileList (
				FilePath text Primary Key,
				FileSize int,
				FileMD5 text)''')
			# cur.execute(f'insert into BookList values(?,?,?,?,?)', (0, 'init', 'init', datetime.datetime.now(), 1))
			db.commit()
		db.close()

	def TraversePath(self):
		for filepath,dirnames,filenames in os.walk(self.path):
			for filename in filenames:
				try:
					self.filePathName = os.path.join(filepath,filename)
					print(f'{self.filePathName}')
					self.fileSize = os.stat(self.filePathName).st_size
					r = self.SQLCheck()
					if r:print(f'{self.fileSize}B\tSQL Existed.\t{self.fileMD5}')
					else:
						self.fileMD5 = self.File2md5()
						if r == 2:self.SQLUpdate()
						else:self.SQLInsert()
						print(f'{self.fileSize}B\t{self.fileMD5}')
				except Exception as e:
					print(f'Something is wrong: {e}')
					print(f'Path:{self.filePathName}')
					with open('./log','a',encoding='utf8') as log:
						log.write(str(e)+'\n'+self.filePathName+'\n')


	def SQLCheck(self):
		if self.mem:
			res = self.mcur.execute(f'select FileSize,FileMD5 from FileList where FilePath="{self.filePathName}"')
			for ids in res:
				if self.fileSize == ids[0]:
					self.fileMD5=ids[1]
					return 1
				else:return 2
			else:
				return 0
		else:
			return 0

	def SQLInsert(self):
		self.cur.execute(f'insert into FileList values(?,?,?)', (self.filePathName, self.fileSize, self.fileMD5))
		self.db.commit()

	def File2md5(self):
		md5 = hashlib.md5()
		readed = 0
		with open(self.filePathName,'rb') as f:
			while True:
				data = f.read(8192)
				if not data:break
				readed += len(data)
				print('\r',end='')
				calculating_MD5 = readed/self.fileSize
				print('Calculating MD5: %06.2f%% [%s]'%((calculating_MD5*100),('█'*int(calculating_MD5*50)+' '*(50-int(calculating_MD5*50)))),end='')
				md5.update(data)
			print()
		return md5.hexdigest()

if __name__ == '__main__':
	# ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
	path = input('Path: ')
	# path = 'E:\\'
	File(path).TraversePath()