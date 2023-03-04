import os
import hashlib
import sqlite3 as sql
import sys
# import time
# import ctypes

class FileSearch(object):
	"""docstring for File"""
	def __init__(self, path):
		self.path = path
		self.filePathName = ''
		self.fileSize = ''
		self.fileMD5 = ''
		self.mem=self.HasDB()
		self.db = sql.connect('./FileData.db')
		self.cur = self.db.cursor()
		self.cur.execute('PRAGMA synchronous = OFF')
		if self.mem:
			self.mdb = sql.connect(':memory:')
			self.mcur = self.mdb.cursor()
			print('Loading SQLite to memory ...')
			self.db.backup(self.mdb)
			print('Load SQLite to memory success.')

	def HasDB(self，x = 1):
		db=sql.connect('./FileData.db')
		cur = db.cursor()
		exist = cur.execute(f'select * from sqlite_master where type=\'table\' and name=\'{self.path}\'')
		exist = exist.fetchone()
		if not exist:
			cur.execute(f'''
				Create table 
				`{self.path}` (
				FilePath text Primary Key,
				FileSize int,
				FileMD5 text)''')
			# cur.execute(f'insert into BookList values(?,?,?,?,?)', (0, 'init', 'init', datetime.datetime.now(), 1))
			db.commit()
			x = 0
		db.close()
		return x

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
					with open('./error.log','a',encoding='utf8') as log:
						log.write(str(e)+'\n'+self.filePathName+'\n')


	def SQLCheck(self):
		if self.mem:
			res = self.mcur.execute(f'select FileSize,FileMD5 from `{self.path}` where FilePath="{self.filePathName}"')
			ids = res.fetchone()
			if ids is None:return 0
			elif (self.fileMD5=ids[1]) and (self.fileSize == ids[0]):return 1
			else:return 2
		else:return 0

	def SQLInsert(self):
		self.cur.execute(f'insert into `{self.path}` values(?,?,?)', (self.filePathName, self.fileSize, self.fileMD5))
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

class DuplicateFiles(object):
	"""docstring for DuplicateFiles"""
	def __init__(self, path,):
		super(DuplicateFiles, self).__init__()
		self.path = path
		self.db = sql.connect('./FileData.db')
		self.cur = self.db.cursor()

	def Log(self,s):
		with open('./error.log','a',encoding='utf8') as log:
			log.write(s)

	def Duplicate(self):
		dbres = self.cur.execute(f'''selelct * from "{self.path}" where ( 
			FileMD5, FileSize) in ( 
			select FileMD5, FileSize from "{self.path}"
			group by FileMD5 having count(*) >= 2) order by FileMD5;''')
		fileNow=list()
		fileNext=dbres.fetchone() #[FilePath,FileSize,FileMD5]
		while not (fileNext is None):
			fileNow.append(fileNext)
			fileNext = dbres.fetchone()
			if fileNow[0][2] == fileNext[2]:continue
			else:
				for ids in range(1,len(fileNow)):
					res = os.system(f"del /F /Q '{fileNow[ids][0]}'")
					if res:
						self.Log(f'Delete File Failure:'{fileNow[ids][0]}'')
						continue
					res = os.system(f"mklink /H '{fileNow[ids][0]}' '{fileNow[0][0]}'")
					if res:self.Log(f'Create HardLink Failure.\n  Link:"{fileNow[ids][0]}"\n  Terget:"{fileNow[0][0]}"')
				else:
					fileNow=list()
		

if __name__ == '__main__':
	# ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
	path = input('Path: ')
	# path = 'E:/'
	if sys.argv[1] == '-d':
		DuplicateFiles(path).Duplicate()
	else:
		FileSearch(path).TraversePath()
		DuplicateFiles(path).Duplicate()