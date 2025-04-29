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
apt-get install -y curl wget git nginx python3 python3-pip python3-venv nodejs npm

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
pip install -r requirements.txt

# 创建上传目录并设置权限
mkdir -p /var/www/mimih2o/backend/uploads
chown -R www-data:www-data /var/www/mimih2o/backend/uploads
chmod 750 /var/www/mimih2o/backend/uploads

# 设置前端
echo -e "${YELLOW}设置前端...${NC}"
cd /var/www/mimih2o/frontend
npm install
npm run build

# 配置Nginx
echo -e "${YELLOW}配置Nginx...${NC}"
cat > /etc/nginx/sites-available/mimih2o << EOF
server {
    listen 80;
    server_name _;  # 替换为您的域名

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
echo -e "${YELLOW}创建系统服务...${NC}"
cat > /etc/systemd/system/mimih2o.service << EOF
[Unit]
Description=Mimih2o Backend Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/mimih2o/backend
Environment="PATH=/var/www/mimih2o/backend/venv/bin"
ExecStart=/var/www/mimih2o/backend/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
echo -e "${YELLOW}启动服务...${NC}"
systemctl daemon-reload
systemctl enable mimih2o
systemctl start mimih2o

echo -e "${GREEN}部署完成！${NC}"
echo -e "${YELLOW}请确保：${NC}"
echo "1. 在Nginx配置中替换server_name为您的域名"
echo "2. 配置SSL证书（如需要）"
echo "3. 检查防火墙设置，确保80端口（和443端口如果使用SSL）已开放"
echo "4. 检查服务状态：systemctl status mimih2o" 