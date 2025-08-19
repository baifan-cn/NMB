# 新闻杂志管理系统

## 项目概述
- **项目名称**：新闻杂志管理系统后端服务
- **技术栈**：Python 3.12 + FastAPI + MySQL + Redis + Elasticsearch + OSS
- **项目管理**：UV工具管理依赖
- **云存储**：阿里云OSS（或腾讯云/七牛云）

## 系统架构

### 技术架构层次
- **表现层**：RESTful API（FastAPI）
- **业务逻辑层**：Service服务层
- **数据访问层**：ORM层（SQLAlchemy）
- **数据存储层**：
  - MySQL：结构化数据存储（用户、杂志、订阅等）
  - Redis：缓存、会话管理、消息队列
  - Elasticsearch：全文搜索引擎
  - OSS：PDF文件云存储

### 核心功能模块
1. **用户认证与授权**：JWT token认证，权限控制
2. **会员等级管理**：5级会员体系，权限差异化
3. **新闻杂志管理**：PDF上传、加密存储、在线查看、下载
4. **文件存储与安全**：AES-256加密，访问控制，防盗链
5. **订阅推送系统**：按分类订阅，定时推送
6. **支付集成**：支付宝/微信支付，自动激活会员
7. **搜索引擎**：基于ES的杂志搜索功能

## 数据库设计

### 核心数据表

#### 1. users（用户表）
```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    real_name VARCHAR(100),
    status ENUM('active', 'inactive', 'banned') DEFAULT 'active',
    last_login_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### 2. member_tiers（会员等级表）
```sql
CREATE TABLE member_tiers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    level INT NOT NULL UNIQUE,
    price_monthly DECIMAL(10,2),
    price_yearly DECIMAL(10,2),
    max_downloads_per_month INT,
    access_history_days INT,
    can_view_current_week BOOLEAN DEFAULT TRUE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. user_memberships（用户会员关系表）
```sql
CREATE TABLE user_memberships (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    tier_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status ENUM('active', 'expired', 'cancelled') DEFAULT 'active',
    payment_id BIGINT,
    auto_renew BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (tier_id) REFERENCES member_tiers(id)
);
```

#### 4. magazines（杂志表）
```sql
CREATE TABLE magazines (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL,
    issue_number VARCHAR(50) NOT NULL,
    publish_date DATE NOT NULL,
    description TEXT,
    cover_image_url VARCHAR(500),
    file_path VARCHAR(500) NOT NULL,
    encrypted_key VARCHAR(255),
    file_size BIGINT,
    page_count INT,
    is_sensitive BOOLEAN DEFAULT FALSE,
    is_published BOOLEAN DEFAULT FALSE,
    view_count INT DEFAULT 0,
    download_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_publish_date (publish_date),
    INDEX idx_issue_number (issue_number)
);
```

#### 5. magazine_categories（杂志分类表）
```sql
CREATE TABLE magazine_categories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_id INT,
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES magazine_categories(id)
);
```

#### 6. subscriptions（订阅表）
```sql
CREATE TABLE subscriptions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    category_id INT NOT NULL,
    frequency ENUM('daily', 'weekly', 'monthly') NOT NULL,
    last_sent_at TIMESTAMP NULL,
    next_send_at TIMESTAMP NOT NULL,
    status ENUM('active', 'paused', 'cancelled') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (category_id) REFERENCES magazine_categories(id),
    INDEX idx_next_send (next_send_at, status)
);
```

#### 7. payments（支付记录表）
```sql
CREATE TABLE payments (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    tier_id INT,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'CNY',
    payment_method ENUM('alipay', 'wechat', 'bank_card') NOT NULL,
    status ENUM('pending', 'success', 'failed', 'cancelled', 'refunded') DEFAULT 'pending',
    transaction_id VARCHAR(100),
    external_transaction_id VARCHAR(100),
    paid_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (tier_id) REFERENCES member_tiers(id)
);
```

#### 8. downloads（下载记录表）
```sql
CREATE TABLE downloads (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    magazine_id BIGINT NOT NULL,
    download_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    file_size BIGINT,
    download_duration INT,
    status ENUM('success', 'failed', 'cancelled') DEFAULT 'success',
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (magazine_id) REFERENCES magazines(id)
);
```

## 会员等级体系

### 等级划分

| 等级 | 名称 | 月费 | 年费 | 下载权限 | 访问历史 | 每月下载限制 |
|------|------|------|------|----------|----------|--------------|
| 0 | 免费用户 | 免费 | - | 仅在线查看本周 | 无 | 0次 |
| 1 | 基础会员 | ¥39 | ¥399 | 下载1个月内 | 30天 | 50次 |
| 2 | 高级会员 | ¥79 | ¥799 | 下载3个月内 | 90天 | 200次 |
| 3 | VIP会员 | ¥159 | ¥1599 | 下载1年内 | 365天 | 无限制 |
| 4 | 终身会员 | - | ¥2999 | 无限制 | 无限制 | 无限制 |

### 权限控制逻辑
```python
def check_access_permission(user_membership, magazine):
    # 免费用户只能查看本周杂志
    if not user_membership or user_membership.status != 'active':
        if is_current_week(magazine.publish_date):
            return {'can_view': True, 'can_download': False}
        return {'can_view': False, 'can_download': False}
    
    # 检查访问历史权限
    days_diff = (datetime.now().date() - magazine.publish_date).days
    if days_diff > user_membership.tier.access_history_days:
        return {'can_view': False, 'can_download': False}
    
    # 检查下载次数限制
    current_month_downloads = get_current_month_downloads(user_membership.user_id)
    can_download = (user_membership.tier.max_downloads_per_month is None or 
                   current_month_downloads < user_membership.tier.max_downloads_per_month)
    
    return {'can_view': True, 'can_download': can_download}
```

## API接口设计

### 基础URL
```
https://api.magazine-system.com/api/v1
```

### 核心接口列表

#### 认证授权
- `POST /auth/register` - 用户注册
- `POST /auth/login` - 用户登录
- `POST /auth/logout` - 用户登出
- `POST /auth/refresh-token` - 刷新token
- `GET /auth/profile` - 获取用户信息
- `PUT /auth/profile` - 更新用户信息

#### 会员管理
- `GET /member-tiers` - 获取会员等级列表
- `POST /memberships/upgrade` - 升级会员
- `GET /memberships/current` - 获取当前会员状态
- `GET /memberships/history` - 获取会员历史

#### 杂志管理
- `GET /magazines` - 获取杂志列表（分页+筛选）
- `GET /magazines/{id}` - 获取杂志详情
- `GET /magazines/{id}/view` - 在线查看（临时链接）
- `POST /magazines/{id}/download` - 下载杂志
- `GET /magazines/current-week` - 本周杂志
- `GET /magazines/categories` - 杂志分类
- `POST /magazines` - 上传杂志（管理员）
- `PUT /magazines/{id}` - 更新杂志（管理员）

#### 订阅管理
- `GET /subscriptions` - 获取订阅列表
- `POST /subscriptions` - 创建订阅
- `PUT /subscriptions/{id}` - 更新订阅
- `DELETE /subscriptions/{id}` - 取消订阅

#### 支付相关
- `POST /payment/create-order` - 创建支付订单
- `GET /payment/orders/{id}` - 获取订单详情
- `POST /payment/callback` - 支付回调
- `GET /payment/history` - 支付历史

#### 搜索功能
- `GET /search/magazines` - 搜索杂志
- `GET /search/suggestions` - 搜索建议

## 文件存储与安全策略

### OSS存储结构
```
magazines/
├── original/           # 加密PDF文件
│   ├── 2024/
│   │   ├── 01/
│   │   │   ├── {uuid}.pdf.enc
├── thumbnails/        # 封面缩略图
│   ├── 2024/
│   │   ├── 01/
│   │   │   ├── {uuid}_cover.jpg
├── temp/              # 临时预览文件
│   ├── {session_id}/
│   │   ├── {uuid}_preview.pdf
```

### 安全措施

#### 1. 文件加密
- **加密算法**：AES-256-CBC
- **密钥管理**：每个文件使用唯一子密钥
- **密钥轮换**：定期更新主密钥

#### 2. 访问控制
- JWT token认证
- 临时访问链接（带过期时间）
- IP限制和访问频率限制
- 下载次数统计和限制

#### 3. 文件上传流程
```python
async def upload_magazine_file(file: UploadFile, magazine_id: int):
    # 1. 验证文件类型和大小
    validate_file_type(file)  # 仅PDF
    validate_file_size(file)  # 限制大小
    
    # 2. 压缩PDF
    compressed_data = compress_pdf(file.file)
    
    # 3. 加密文件
    encryption_key = derive_key(magazine_id, MASTER_KEY)
    encrypted_data = encrypt_file(compressed_data, encryption_key)
    
    # 4. 上传到OSS
    file_path = generate_file_path(magazine_id)
    oss_url = upload_to_oss(encrypted_data, file_path)
    
    # 5. 更新数据库
    update_magazine_file_info(magazine_id, file_path, len(encrypted_data))
    
    return oss_url
```

#### 4. 文件下载流程
```python
async def download_magazine_file(user_id: int, magazine_id: int):
    # 1. 权限验证
    check_download_permission(user_id, magazine_id)
    
    # 2. 检查配额
    check_download_quota(user_id)
    
    # 3. 获取并解密文件
    encrypted_data = download_from_oss(magazine.file_path)
    encryption_key = derive_key(magazine_id, MASTER_KEY)
    decrypted_data = decrypt_file(encrypted_data, encryption_key)
    
    # 4. 记录日志
    log_download_activity(user_id, magazine_id)
    
    return StreamingResponse(decrypted_data, media_type="application/pdf")
```

## 订阅推送系统

### 订阅类型
- **按分类订阅**：用户可选择关注的杂志分类
- **推送频率**：每日/每周/每月
- **内容差异化**：
  - 免费用户：发送查看链接（仅本周杂志）
  - 付费会员：发送下载链接（根据会员等级）

### 推送流程
```python
@celery.task
def process_subscriptions():
    # 查询需要推送的订阅
    due_subscriptions = get_due_subscriptions()
    
    for subscription in due_subscriptions:
        try:
            # 获取该分类最新杂志
            magazines = get_latest_magazines_by_category(
                subscription.category_id,
                subscription.last_sent_at
            )
            
            if magazines:
                # 发送订阅内容
                send_subscription_content(subscription, magazines)
                
                # 更新发送时间
                update_subscription_send_time(subscription.id)
        
        except Exception as e:
            logger.error(f"处理订阅失败: {subscription.id}, 错误: {str(e)}")
```

### 邮件模板
- **会员用户**：提供下载链接（7天有效期）
- **免费用户**：提供在线查看链接 + 升级会员推广

## 支付系统

### 支付流程

#### 1. 会员升级支付
```python
@router.post("/memberships/upgrade")
async def upgrade_membership(request: UpgradeRequest, current_user: User):
    # 验证会员等级
    tier = get_member_tier(request.tier_id)
    
    # 计算支付金额
    amount = tier.price_monthly if request.billing_cycle == 'monthly' else tier.price_yearly
    
    # 创建支付订单
    payment = create_payment_order(
        user_id=current_user.id,
        tier_id=tier.id,
        amount=amount,
        payment_method=request.payment_method
    )
    
    # 调用第三方支付
    if request.payment_method == 'alipay':
        pay_url = create_alipay_order(payment)
    elif request.payment_method == 'wechat':
        pay_url = create_wechat_order(payment)
    
    return {"payment_id": payment.id, "pay_url": pay_url}
```

#### 2. 支付回调处理
```python
@router.post("/payment/callback/{payment_method}")
async def payment_callback(payment_method: str, request: Request):
    # 验证回调签名
    if not verify_payment_signature(request, payment_method):
        raise HTTPException(400, "签名验证失败")
    
    # 获取支付信息
    payment_data = parse_payment_callback(request, payment_method)
    payment = get_payment_by_transaction_id(payment_data['transaction_id'])
    
    if payment_data['status'] == 'success':
        # 激活会员
        activate_membership(payment.user_id, payment.tier_id, payment.id)
        
        # 发送激活邮件
        send_membership_activation_email(payment.user_id)
    
    return {"message": "处理成功"}
```

#### 3. 账号初始化
```python
def send_membership_activation_email(user_id: int):
    user = get_user(user_id)
    membership = get_current_membership(user_id)
    
    # 生成临时密码（如需要）
    if not user.password_hash:
        temp_password = generate_temp_password()
        update_user_password(user_id, temp_password)
        
        email_content = f"""
        尊敬的用户 {user.username}，
        
        您的会员已成功激活！
        
        登录信息：
        用户名：{user.username}
        临时密码：{temp_password}
        
        会员等级：{membership.tier.name}
        有效期：{membership.start_date} 至 {membership.end_date}
        
        请尽快登录系统修改密码。
        """
    
    send_email(user.email, "会员激活通知", email_content)
```

## 部署架构

### 推荐部署方案

#### Docker容器化部署
```dockerfile
# 应用容器
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 服务架构
- **Web服务**：FastAPI应用（多实例）
- **数据库**：MySQL主从架构
- **缓存**：Redis集群
- **搜索**：Elasticsearch集群
- **消息队列**：Redis/RabbitMQ（异步任务）
- **反向代理**：Nginx
- **监控**：Prometheus + Grafana

#### docker-compose.yml 示例
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - mysql
      - redis
      - elasticsearch
    environment:
      - DATABASE_URL=mysql://user:pass@mysql:3306/magazine_db
      - REDIS_URL=redis://redis:6379
      - ELASTICSEARCH_URL=http://elasticsearch:9200
  
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_DATABASE: magazine_db
      MYSQL_USER: user
      MYSQL_PASSWORD: pass
  
  redis:
    image: redis:7-alpine
  
  elasticsearch:
    image: elasticsearch:8.8.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

## 开发规范

### 项目结构
```
/project_root
├── app/
│   ├── api/                # API路由
│   ├── core/               # 核心配置
│   ├── models/             # 数据模型
│   ├── schemas/            # Pydantic模式
│   ├── services/           # 业务逻辑
│   ├── utils/              # 工具函数
│   └── main.py             # 应用入口
├── alembic/                # 数据库迁移
├── tests/                  # 测试文件
├── docker-compose.yml      # Docker配置
├── requirements.txt        # 依赖文件
└── pyproject.toml          # UV配置
```

### UV工具使用
```bash
# 创建项目
uv init magazine-system
cd magazine-system

# 添加依赖
uv add fastapi uvicorn sqlalchemy pymysql redis elasticsearch

# 添加开发依赖
uv add --dev pytest black isort mypy

# 运行应用
uv run uvicorn app.main:app --reload

# 运行测试
uv run pytest
```

## MCP工具RULES
### MCP Interactive Feedback 规则

1. 在任何流程、任务、对话进行时，无论是询问、回复、或完成阶段性任务，皆必须调用 MCP mcp-feedback-enhanced。
2. 每当收到用户反馈，若反馈内容非空，必须再次调用 MCP mcp-feedback-enhanced，并根据反馈内容调整行为。
3. 仅当用户明确表示「结束」或「不再需要交互」时，才可停止调用 MCP mcp-feedback-enhanced，流程才算结束。
4. 除非收到结束指令，否则所有步骤都必须重复调用 MCP mcp-feedback-enhanced。
5. 完成任务前，必须使用 MCP mcp-feedback-enhanced 工具向用户询问反馈。

## 重要提醒
- 永远不要创建非必要文件
- 优先编辑现有文件而非创建新文件
- 除非明确要求，否则不主动创建文档文件
- 按需求实现功能，不做额外工作