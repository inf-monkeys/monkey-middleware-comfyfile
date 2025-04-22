FROM node:22.5.1-alpine

# 设置工作目录
WORKDIR /app

# 安装 pnpm
RUN npm install -g pnpm

# 复制 package.json 和 pnpm-lock.yaml (如果存在)
COPY package.json pnpm-lock.yaml* ./

# 安装依赖
RUN pnpm install

# 复制源代码
COPY . .

# 构建应用程序
RUN pnpm build

# 暴露端口
EXPOSE 8000

# 启动应用程序
CMD ["pnpm", "prod"]
