# 只用 nginx 运行静态资源
FROM nginx:alpine

# 删除默认 nginx 静态文件
RUN rm -rf /usr/share/nginx/html/*

# 将 HBuilderX 发行的文件复制进去
COPY ./unpackage/dist/build/web /usr/share/nginx/html/crm

# 暴露端口
EXPOSE 80

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]
