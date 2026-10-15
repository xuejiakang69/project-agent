import sys

try:
    import pysqlite3
except ImportError:
    # 本地开发环境未安装兼容包时，使用 Python 默认的 sqlite3。
    pass
else:
    # 让后续导入 sqlite3 的模块使用兼容版本。
    sys.modules["sqlite3"] = pysqlite3
