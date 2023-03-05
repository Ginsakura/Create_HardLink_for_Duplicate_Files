# Create_HardLink_for_Duplicate_Files
Create Hard Links for duplicate files

为指定目录下重复文件创建硬链接以节约磁盘占用
### 用法
- `Python.exe ./DuplicateFiles.py [-operation]`
- `Path:`输入你想查询/去除重复文件的目录
- `-operation`:`-d`,`-u`,`-h`,`-r`,`-show`,`-show-count`

### 功能
1. ## 本脚本对大小写敏感,对`\`,`/`也敏感
    - ## `E:/`,`E:\`,`e:\`,`e:/`是不同的目录
    - ## `E:/temp\`,`e:\tEmp\`也是不同的目录
1. 迭代扫描指定目录的所有文件并写入数据库
    - 仅存储文件路径、文件名、文件大小(Byte)、文件md5
2. 指定`-d`参数可以跳过扫描直接读取数据库进行去重
    - 前提是之前进行过扫描,并且有`FileData.db`文件存在
4. 指定`-u`参数可以更新数据库文件,并进行去重
5. 指定`-r`参数将在开始前删除当前路径的表,重新建表后再去重
6. 指定`-show`参数展示数据库中已有的表
7. 指定`-show-count`参数展示数据库中已有的表,并显示表内记录数