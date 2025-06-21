cd E:\CRM                 # 移步到你的项目目录
django-admin startproject mycrm .   # 创建项目，注意最后的点，表示“当前目录”
python manage.py startapp bills     # 创建名为bills的子应用

E:\CRM\
├── bills\【业务模块】
│   ├── __init__.py
│   ├── admin.py【配置Django后台如何编辑你的模型（让Bill能在/admin里管理）】
│   ├── apps.py【存放App配置，本地一般不用动。】
│   ├── migrations\【数据库迁移记录的脚本，每加/改模型字段都会多一个脚本，让你数据库和代码同步。】
│   │   └── __init__.py
│   ├── models.py【写数据表解构】
│   ├── tests.py【放自动化测试代码。】
│   └── views.py【写视图，用户请求从这里进，比如API接口，Web界面】
├── mycrm\【主项目目录】
│   ├── __init__.py
│   ├── asgi.py【支持异步服务标准，如Daphe、Channels】
│   ├── settings.py【核心配置文件，数据库连接、已安装的应用、静态文件路径、Django安全参数都在这儿改】
│   ├── urls.py【总路由表，定义URL分发到哪个APP或者视图】
│   └── wsgi.py【用于部署Web Server Gateway Interface配置，外部gunicorn，uwsgi托管Django应用时用到】
├── db.sqlite3【默认生成的SQLite数据库文件，轻量级项目可以直接用】
├── manage.py【操作Django项目入口脚本】

