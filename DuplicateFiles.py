import os
import hashlib
import sqlite3 as sql
import sys
import datetime as dt
import time
# import ctypes

class FileSearch(object):
	"""docstring for File"""
	def __init__(self, path,update=False):
		self.path = path
		self.update = update
		self.filePathName = ''
		self.fileSize = ''
		self.fileMD5 = ''
		self.mem=self.HasTable()
		self.db = sql.connect('./FileData.db')
		self.cur = self.db.cursor()
		self.cur.execute('PRAGMA synchronous = OFF')
		if self.mem or self.update:
			self.mdb = sql.connect(':memory:')
			self.mcur = self.mdb.cursor()
			print('Loading SQLite to memory ...')
			self.db.backup(self.mdb)
			print('Load SQLite to memory success.')

	def HasTable(self, x=1):
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
		fileCount=0
		for filepath,dirnames,filenames in os.walk(self.path):
			for filename in filenames:
				fileCount += 1
				try:
					self.filePathName = os.path.join(filepath,filename)
					print(f'{fileCount}  {self.filePathName}')
					self.fileSize = os.stat(self.filePathName).st_size
					if self.update:
						self.fileMD5 = self.File2md5()
						self.SQLUpdateAll()
					else:
						r = self.SQLCheck()
						if r:print(f'{dt.datetime.now()}\t{self.fileMD5}\t{self.fileSize}B\tSQL Existed.')
						else:
							self.fileMD5 = self.File2md5()
							if r == 2:self.SQLUpdate()
							else:self.SQLInsert()
							print(f'{dt.datetime.now()}\t{self.fileMD5}\t{self.fileSize}B')
				except Exception as e:
					print(f'Something is wrong: {e}')
					print(f'Path:{self.filePathName}')
					with open('./error.log','a',encoding='utf8') as log:
						log.write(f'dt.datetime.now()\t{str(e)}\n{self.filePathName}\n')
		if self.update:
			self.mdb.backup(self.db)
		if self.mem or self.update:
			self.mdb.close()
		self.db.close()

	def SQLUpdateAll(self):
		res = self.mcur.execute(f'select FileSize,FileMD5 from "{self.path}" where FilePath="{self.filePathName}"')
		ids = res.fetchone()
		if ids is None:
			self.mcur.execute(f'insert into `{self.path}` values(?,?,?)', (self.filePathName, self.fileSize, self.fileMD5))
			print(f'{dt.datetime.now()}\t{self.fileMD5}\t{self.fileSize}B')
		elif (self.fileMD5 == ids[1]) and (self.fileSize == ids[0]):
			print(f'{dt.datetime.now()}\t{self.fileMD5}\t{self.fileSize}B\tData not change.')
		else:
			self.mcur.execute(f'update "{self.path}" set FileSize={self.fileSize},FileMD5={self.fileMD5} where FilePath="{self.filePathName}"')
			print(f'{dt.datetime.now()}\
\tNew Hash:{self.fileMD5}\tOld Hash:{ids[1]}\
\tNew Size:{self.fileSize}B\tOld Size:{ids[0]}\
Data not change.')

	def SQLCheck(self):
		if self.mem:
			res = self.mcur.execute(f'select FileSize,FileMD5 from "{self.path}" where FilePath="{self.filePathName}"')
			ids = res.fetchone()
			if ids is None:return 0
			elif (self.fileMD5 == ids[1]) and (self.fileSize == ids[0]):return 1
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
	def __init__(self, path,unsafe=0):
		super(DuplicateFiles, self).__init__()
		self.path = path
		self.unsafe = unsafe
		self.db = sql.connect('./FileData.db')
		self.cur = self.db.cursor()

	def Log(self,s):
		with open('./error.log','a',encoding='utf8') as log:
			log.write(f'{dt.datetime.now()}\t')
			log.write(f'\t{s}\n')

	def Duplicate(self):
		dbres = self.cur.execute(f'''select * from "{self.path}" where ( 
			FileMD5, FileSize) in ( 
			select FileMD5, FileSize from "{self.path}"
			group by FileMD5 having count(*) >= 2) order by FileMD5;''')
		fileNow=list()
		fileNext=dbres.fetchone() #[FilePath,FileSize,FileMD5]
		while not (fileNext is None):
			if fileNext[1] == 0:continue
			fileNow.append(fileNext)
			fileNext = dbres.fetchone()
			# print(fileNow)
			# print(fileNext)
			if (not fileNext is None) and (fileNow[0][2] == fileNext[2]):continue
			else:
				for ids in range(1,len(fileNow)):
					if os.path.isfile(fileNow[ids][0]):
						if self.unsafe:
							res = os.system(f'del /F /Q "{fileNow[ids][0]}"')
							if res:
								self.Log(f'Delete File Failure:"{fileNow[ids][0]}"')
								continue
							os.system(f'mklink /H "{fileNow[ids][0]}" "{fileNow[0][0]}"')
						else:
							res = os.system(f'mklink /H "{fileNow[ids][0]}.tmp" "{fileNow[0][0]}"')
							if res:
								self.Log(f'Create HardLink Failure.\n  Link:"{fileNow[ids][0]}.tmp"\n  Terget:"{fileNow[0][0]}"')
								continue
							res = os.system(f'move "{fileNow[ids][0]}" "{fileNow[ids][0]}.tmp2"')
							if res:
								self.Log(f'Rename File Failure:"{fileNow[ids][0]}" to "{fileNow[ids][0]}.tmp2"')
								os.system(f'del /F /Q "{fileNow[ids][0]}.tmp"')
								continue
							else:
								print(f"Rename File : '{fileNow[ids][0]}' to '{fileNow[ids][0]}.tmp2'")
							res = os.system(f'move "{fileNow[ids][0]}.tmp" "{fileNow[ids][0]}"')
							if res:
								self.Log(f'Rename File Failure:"{fileNow[ids][0]}.tmp" to "{fileNow[ids][0]}"')
								os.system(f'del /F /Q "{fileNow[ids][0]}.tmp"')
								os.system(f'move "{fileNow[ids][0]}.tmp2" "{fileNow[ids][0]}"')
								continue
							else:
								print(f"Rename File : '{fileNow[ids][0]}.tmp' to '{fileNow[ids][0]}'")
							os.system(f'del /F /Q "{fileNow[ids][0]}.tmp2"')
					else:
						os.system(f'mklink /H "{fileNow[ids][0]}" "{fileNow[0][0]}"')
				else:
					fileNow=list()
		

if __name__ == '__main__':
	# ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
	if sys.argv[-1] == '-h':
		print('Memu:\n \
-h\t\tHelp\n\
-d\t\t直接根据数据库进行文件去重\n\
-r\t\t删除表重新建立并去重\n\
-u\t\t更新表内容并去重\n\
-unsafe\t\t在-d、-r、-u模式下，使用-unsafe参数可以切换去重操作为不安全模式，至于有没有更快……谁知道呢~)\
-show\t\t展示数据库中的所有表以及表内条目数\n\
-show-count\t展示数据库中的所有表以及表内条目数')
		os.system("pause")
		sys.exit()
	elif sys.argv[-1] == '-show':
		db = sql.connect('./FileData.db')
		cur = db.cursor()
		res = cur.execute('select * from sqlite_master where type=\'table\'')
		resNum=0
		for ids in res:
			resNum += 1
			print(f'{resNum}\t{ids[1]}')
		db.close()
		os.system("pause")
		sys.exit()
	elif sys.argv[-1] == '-show-count':
		db = sql.connect('./FileData.db')
		cur = db.cursor()
		res = cur.execute('select * from sqlite_master where type=\'table\'')
		res = res.fetchall()
		resNum=0
		print(f'  num  |  path  |  count  ')
		for idx in res:
			resNum += 1
			count = cur.execute(f'select count(*) from "{idx[1]}"')
			print(f'{resNum}\t{idx[1]}\t{count.fetchone()[0]}')
		db.close()
		os.system("pause")
		sys.exit()
	path = input('Path: ')
	# path = 'E:/'
	argu = sys.argv[1:]
	if path.strip() is None:sys.exit()
	if '-unsafe' in argu:unsafe=1
	else:unsafe=0
	if '-d' in argu:
		DuplicateFiles(path,unsafe).Duplicate()
	elif '-r' in argu:
		db = sql.connect('./FileData.db')
		cur = db.cursor()
		cur.execute(f'drop table if exists "{path}"')
		FileSearch(path).TraversePath()
		time.sleep(0.1)
		DuplicateFiles(path,unsafe).Duplicate()
	elif '-u' in argu:
		FileSearch(path,update=True).TraversePath()
		time.sleep(0.1)
		DuplicateFiles(path,unsafe).Duplicate()
	else:
		FileSearch(path).TraversePath()
		time.sleep(0.1)
		DuplicateFiles(path).Duplicate()
	os.system("pause")