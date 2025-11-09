# 中间件小工具

from django.db import connection, reset_queries


class QueryCountMiddleware:
    # 用于查询某个操作执行的SQL语句
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        reset_queries()  # 每次请求前清空SQL记录
        response = self.get_response(request)
        num_queries = len(connection.queries)
        print(f"[SQL 查询次数] {request.path}: {num_queries}")
        for q in connection.queries:
            print(q['sql'], q['time'])
        return response
