#!/bin/bash

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}开始部署自助查询工具到阿里云服务器...${NC}"

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}请使用root用户运行此脚本${NC}"
  exit 1
fi

# 更新系统包
echo -e "${YELLOW}更新系统包...${NC}"
apt-get update
apt-get upgrade -y

# 安装必要的依赖
echo -e "${YELLOW}安装必要的依赖...${NC}"
apt-get install -y curl wget git nginx python3 python3-pip python3-venv nodejs npm fail2ban ufw

# 配置防火墙
echo -e "${YELLOW}配置防火墙...${NC}"
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https
ufw --force enable

# 配置fail2ban防止暴力攻击
echo -e "${YELLOW}配置fail2ban...${NC}"
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 3
EOF

systemctl restart fail2ban

# 配置npm使用淘宝镜像
echo -e "${YELLOW}配置npm使用淘宝镜像...${NC}"
npm config set registry https://registry.npmmirror.com

# 配置pip使用阿里云镜像
echo -e "${YELLOW}配置pip使用阿里云镜像...${NC}"
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << EOF
[global]
index-url = https://mirrors.aliyun.com/pypi/simple/
trusted-host = mirrors.aliyun.com
EOF

# 创建项目目录
echo -e "${YELLOW}创建项目目录...${NC}"
mkdir -p /var/www/mimih2o
cd /var/www/mimih2o

# 克隆项目代码（如果是从Git仓库部署）
# echo -e "${YELLOW}克隆项目代码...${NC}"
# git clone https://github.com/yourusername/mimih2o.git .

# 或者，如果您是上传代码到服务器，请手动上传代码到此目录

# 设置后端
echo -e "${YELLOW}设置后端...${NC}"
cd /var/www/mimih2o/backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 创建上传目录并设置权限
mkdir -p uploads
chown -R www-data:www-data uploads
chmod 750 uploads

# 设置前端
echo -e "${YELLOW}设置前端...${NC}"
cd /var/www/mimih2o/frontend

# 安装依赖
npm install

# 构建前端
npm run build

# 配置Nginx
echo -e "${YELLOW}配置Nginx...${NC}"
cat > /etc/nginx/sites-available/mimih2o << EOF
server {
    listen 80;
    server_name your_domain.com;  # 替换为您的域名

    # 安全头部设置
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:;" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # 限制请求大小
    client_max_body_size 10M;

    # 限制请求速率
    limit_req_zone \$binary_remote_addr zone=one:10m rate=10r/s;
    limit_req zone=one burst=20 nodelay;

    # 前端静态文件
    location / {
        root /var/www/mimih2o/frontend/build;
        try_files \$uri \$uri/ /index.html;
        
        # 缓存静态资源
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 30d;
            add_header Cache-Control "public, no-transform";
        }
    }

    # 后端API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # 限制API请求速率
        limit_req zone=one burst=10 nodelay;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 禁止访问隐藏文件
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    # 禁止访问敏感文件
    location ~* \.(git|svn|env|config|ini|log|sh|inc|bak)$ {
        deny all;
        access_log off;
        log_not_found off;
    }
}
EOF

# 启用站点
ln -sf /etc/nginx/sites-available/mimih2o /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

# 创建系统服务
echo -e "${YELLOW}创建系统服务...${NC}"

# 后端服务
cat > /etc/systemd/system/mimih2o-backend.service << EOF
[Unit]
Description=Mimih2o Backend Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/mimih2o/backend
ExecStart=/var/www/mimih2o/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'
Restart=always
RestartSec=5
StartLimitInterval=0
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF

# 设置文件权限
echo -e "${YELLOW}设置文件权限...${NC}"
chown -R www-data:www-data /var/www/mimih2o
find /var/www/mimih2o -type d -exec chmod 755 {} \;
find /var/www/mimih2o -type f -exec chmod 644 {} \;

# 启动服务
systemctl daemon-reload
systemctl enable mimih2o-backend
systemctl start mimih2o-backend

# 配置日志轮转
echo -e "${YELLOW}配置日志轮转...${NC}"
cat > /etc/logrotate.d/mimih2o << EOF
/var/www/mimih2o/backend/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload mimih2o-backend
    endscript
}
EOF

# 创建安全配置文件
echo -e "${YELLOW}创建安全配置文件...${NC}"
cat > /var/www/mimih2o/backend/security_config.py << EOF
# 安全配置
SECURITY_CONFIG = {
    # 密码策略
    "PASSWORD_MIN_LENGTH": 8,
    "PASSWORD_REQUIRE_UPPER": True,
    "PASSWORD_REQUIRE_LOWER": True,
    "PASSWORD_REQUIRE_NUMBERS": True,
    "PASSWORD_REQUIRE_SPECIAL": True,
    
    # 会话配置
    "SESSION_TIMEOUT": 3600,  # 1小时
    
    # 登录尝试限制
    "MAX_LOGIN_ATTEMPTS": 5,
    "LOGIN_TIMEOUT": 300,  # 5分钟
    
    # API限制
    "API_RATE_LIMIT": 100,  # 每分钟请求数
    "API_BURST_LIMIT": 20,  # 突发请求数
    
    # 文件上传限制
    "MAX_UPLOAD_SIZE": 10 * 1024 * 1024,  # 10MB
    "ALLOWED_EXTENSIONS": [".xlsx", ".xls"],
    
    # SQL注入防护
    "SQL_INJECTION_PATTERNS": [
        "UNION", "SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "EXEC", "--", "/*", "*/"
    ]
}
EOF

echo -e "${GREEN}部署完成！${NC}"
echo -e "${GREEN}请访问 http://your_domain.com 查看应用${NC}"
echo -e "${YELLOW}注意：请将 your_domain.com 替换为您的实际域名${NC}"
echo -e "${YELLOW}安全措施已启用：${NC}"
echo -e "${YELLOW}- 防火墙已配置，只允许SSH、HTTP和HTTPS${NC}"
echo -e "${YELLOW}- fail2ban已配置，防止暴力攻击${NC}"
echo -e "${YELLOW}- Nginx安全头部已设置${NC}"
echo -e "${YELLOW}- 请求速率限制已启用${NC}"
echo -e "${YELLOW}- 文件权限已正确设置${NC}"
echo -e "${YELLOW}- 日志轮转已配置${NC}"
echo -e "${YELLOW}- 安全配置文件已创建${NC}" 