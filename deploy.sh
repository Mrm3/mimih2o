#!/bin/bash

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}请使用root权限运行此脚本${NC}"
    exit 1
fi

echo -e "${GREEN}开始部署自助查询工具...${NC}"

# 更新系统包
echo -e "${YELLOW}更新系统包...${NC}"
apt-get update
apt-get upgrade -y

# 安装必要的依赖
echo -e "${YELLOW}安装必要的依赖...${NC}"
apt-get install -y curl wget git nginx python3 python3-pip python3-venv

# 安装 Node.js 18.x
echo -e "${YELLOW}安装 Node.js 18.x...${NC}"
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

# 验证 Node.js 版本
echo -e "${YELLOW}验证 Node.js 版本...${NC}"
node --version
npm --version

# 配置npm使用淘宝镜像
echo -e "${YELLOW}配置npm镜像...${NC}"
npm config set registry https://registry.npmmirror.com

# 配置pip使用阿里云镜像
echo -e "${YELLOW}配置pip镜像...${NC}"
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << EOF
[global]
index-url = https://mirrors.aliyun.com/pypi/simple/
trusted-host = mirrors.aliyun.com
EOF

# 创建项目目录并复制文件
echo -e "${YELLOW}创建项目目录并复制文件...${NC}"
mkdir -p /var/www/mimih2o
cp -r /root/mimih2o/* /var/www/mimih2o/
chown -R www-data:www-data /var/www/mimih2o
chmod -R 755 /var/www/mimih2o

# 设置后端
echo -e "${YELLOW}设置后端...${NC}"
cd /var/www/mimih2o/backend
python3 -m venv venv
source venv/bin/activate

# 安装后端依赖
echo -e "${YELLOW}安装后端依赖...${NC}"
pip install --upgrade pip
pip install fastapi==0.68.1
pip install uvicorn==0.15.0
pip install gunicorn==20.1.0
pip install python-multipart==0.0.5
pip install python-jose[cryptography]==3.3.0
pip install passlib[bcrypt]==1.7.4
pip install sqlalchemy==1.4.23
pip install pandas==1.3.3
pip install openpyxl==3.0.9
pip install python-dotenv==0.19.0
pip install pydantic==1.8.2
pip install email-validator==1.1.3

# 创建上传目录并设置权限
mkdir -p /var/www/mimih2o/backend/uploads
chown -R www-data:www-data /var/www/mimih2o/backend/uploads
chmod 750 /var/www/mimih2o/backend/uploads

# 设置前端
echo -e "${YELLOW}设置前端...${NC}"
cd /var/www/mimih2o/frontend

# 清理旧的 node_modules
echo -e "${YELLOW}清理旧的依赖...${NC}"
rm -rf node_modules package-lock.json

# 安装依赖
echo -e "${YELLOW}安装前端依赖...${NC}"
npm install --legacy-peer-deps

# 构建前端
echo -e "${YELLOW}构建前端...${NC}"
timeout 300 npm run build || {
    echo -e "${RED}前端构建超时，尝试重新构建...${NC}"
    npm run build
}

# 配置Nginx
echo -e "${YELLOW}配置Nginx...${NC}"
cat > /etc/nginx/sites-available/mimih2o << EOF
server {
    listen 80;
    server_name www.minih2o.top minih2o.top;

    location / {
        root /var/www/mimih2o/frontend/build;
        try_files \$uri \$uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

# 启用站点配置
ln -sf /etc/nginx/sites-available/mimih2o /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

# 创建系统服务
echo -e "\033[32m[INFO] 创建系统服务...\033[0m"
cat > /etc/systemd/system/mimih2o.service << EOF
[Unit]
Description=MimiH2O Backend Service
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/mimih2o/backend
Environment="PATH=/var/www/mimih2o/backend/venv/bin"
ExecStart=/var/www/mimih2o/backend/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 初始化数据库
echo -e "\033[32m[INFO] 初始化数据库...\033[0m"
cd /var/www/mimih2o/backend
source venv/bin/activate
python3 init_db.py
deactivate

# 设置权限
echo -e "${YELLOW}设置权限...${NC}"
chown -R www-data:www-data /var/www/mimih2o
chmod -R 755 /var/www/mimih2o
find /var/www/mimih2o -type d -exec chmod 755 {} \;
find /var/www/mimih2o -type f -exec chmod 644 {} \;
chmod 755 /var/www/mimih2o/backend/venv/bin/python
chmod 755 /var/www/mimih2o/backend/venv/bin/gunicorn

# 检查前端构建文件
echo -e "${YELLOW}检查前端构建文件...${NC}"
if [ ! -d "/var/www/mimih2o/frontend/build" ]; then
    echo -e "${RED}前端构建文件不存在，重新构建...${NC}"
    cd /var/www/mimih2o/frontend
    npm run build
fi

# 确保 index.html 存在
if [ ! -f "/var/www/mimih2o/frontend/build/index.html" ]; then
    echo -e "${RED}index.html 不存在，重新构建前端...${NC}"
    cd /var/www/mimih2o/frontend
    rm -rf build
    npm run build
fi

# 重启 Nginx
echo -e "${YELLOW}重启 Nginx...${NC}"
nginx -t
systemctl restart nginx

# 启动服务
echo -e "\033[32m[INFO] 启动服务...\033[0m"
systemctl daemon-reload
systemctl enable mimih2o
systemctl start mimih2o

# 检查服务状态
echo -e "\033[32m[INFO] 检查服务状态...\033[0m"
sleep 5
systemctl status mimih2o

echo -e "${GREEN}部署完成！${NC}"
echo -e "${YELLOW}请确保：${NC}"
echo "1. 域名 www.minih2o.top 已正确解析到服务器IP"
echo "2. 阿里云安全组已开放80端口"
echo "3. 检查服务状态：systemctl status mimih2o"
echo "4. 检查Nginx状态：systemctl status nginx" 