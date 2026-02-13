# 后端改造迁移指南

## 概述

本次改造完成了以下目标：
1. 删除博客遗留模块（Posts、Categories、Tags、Archive、Interaction）
2. 实现 JWT 认证强制校验
3. 实现用户数据隔离（工单和快速回复）
4. 确保项目可正常运行

## 数据库迁移说明

### 需要执行的数据库变更

由于删除了博客相关模块并为 QuickReply 添加了 user_id 字段，需要执行以下数据库迁移：

#### 1. 删除博客相关表

```sql
-- 删除博客相关的表
DROP TABLE IF EXISTS post_tag;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS category;
DROP TABLE IF EXISTS tag;
```

#### 2. 为 QuickReply 表添加 user_id 字段

```sql
-- 为 quick_reply 表添加 user_id 外键
ALTER TABLE quick_reply ADD COLUMN user_id INT;
ALTER TABLE quick_reply ADD CONSTRAINT fk_quick_reply_user 
    FOREIGN KEY (user_id) REFERENCES user(id);
```

**注意**: 如果 quick_reply 表中已有数据，需要先为这些记录分配 user_id，否则会因为外键约束失败。

#### 3. 数据迁移脚本示例

如果已有数据需要迁移，可以使用以下脚本：

```sql
-- 假设将所有现有的 quick_reply 分配给 ID 为 1 的用户
UPDATE quick_reply SET user_id = 1 WHERE user_id IS NULL;

-- 然后再添加外键约束
ALTER TABLE quick_reply ADD CONSTRAINT fk_quick_reply_user 
    FOREIGN KEY (user_id) REFERENCES user(id);
```

## API 变更说明

### 删除的端点

以下端点已被删除：
- `GET/POST /api/posts/*` - 所有文章相关端点
- `GET /api/categories/*` - 所有分类相关端点
- `GET /api/tags/*` - 所有标签相关端点
- `GET /api/archive/*` - 所有归档相关端点
- `POST /api/interaction/*` - 所有互动相关端点（点赞等）

### 保留的公开端点

以下端点**不需要**认证：
- `POST /api/login` - 用户登录
- `POST /api/register` - 用户注册
- `POST /api/logout` - 用户登出

### 需要认证的端点

以下端点**现在需要**在请求头中提供 JWT token：

#### SiteInfo 和 Menus
- `GET /api/siteinfo` - 需要认证
- `GET /api/menus` - 需要认证

#### Tickets（已实现用户数据隔离）
- `GET /api/tickets` - 只返回当前用户的工单
- `GET /api/tickets/{id}` - 只能查看自己的工单，否则返回 403
- `PUT /api/tickets/{id}` - 只能更新自己的工单，否则返回 403
- `DELETE /api/tickets/{id}` - 只能删除自己的工单，否则返回 403
- `POST /api/tickets` - 自动关联当前用户

#### Quick Replies（已实现用户数据隔离）
- `GET /api/quick-replies` - 只返回当前用户的快速回复
- `GET /api/quick-replies/{id}` - 只能查看自己的快速回复，否则返回 403
- `PUT /api/quick-replies/{id}` - 只能更新自己的快速回复，否则返回 403
- `DELETE /api/quick-replies/{id}` - 只能删除自己的快速回复，否则返回 403
- `POST /api/quick-replies` - 自动关联当前用户

## 前端适配说明

### 1. 认证 Token 的使用

所有需要认证的请求都必须在请求头中包含 JWT token：

```javascript
// 登录后获取 token
const loginResponse = await fetch('/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: 'user', password: 'pass' })
});
const { token } = await loginResponse.json();

// 存储 token
localStorage.setItem('token', token);

// 后续请求使用 token
const response = await fetch('/api/tickets', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});
```

### 2. 处理 401 和 403 响应

```javascript
// 401 - 未认证，需要重新登录
if (response.status === 401) {
    // 清除 token
    localStorage.removeItem('token');
    // 跳转到登录页
    window.location.href = '/login';
}

// 403 - 已认证但无权访问
if (response.status === 403) {
    // 显示错误提示
    alert('您没有权限访问此资源');
}
```

### 3. 移除博客相关功能

前端需要移除以下功能模块：
- 文章列表和详情页面
- 分类浏览页面
- 标签浏览页面
- 归档页面
- 文章点赞和浏览计数

### 4. 数据隔离的影响

- **工单系统**: 用户只能看到和操作自己创建的工单
- **快速回复**: 用户只能看到和操作自己创建的快速回复
- **统计数据**: 如果有统计功能，需要确保只统计当前用户的数据

## 测试建议

### 1. 认证测试

```bash
# 测试未认证访问
curl http://localhost:8000/api/tickets
# 应返回 401

# 测试登录
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'
# 应返回包含 token 的响应

# 测试带认证的访问
TOKEN="your-jwt-token"
curl http://localhost:8000/api/tickets \
  -H "Authorization: Bearer $TOKEN"
# 应返回工单列表
```

### 2. 数据隔离测试

1. 创建两个测试用户
2. 使用用户1创建工单
3. 使用用户2的token尝试访问用户1的工单
4. 应返回 403 或在列表中看不到

### 3. 公开端点测试

```bash
# 这些端点不需要认证
curl -X POST http://localhost:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"newuser","password":"newpass"}'

curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"newuser","password":"newpass"}'
```

## 注意事项

1. **数据库备份**: 在执行数据库迁移之前，请务必备份数据库
2. **现有数据**: 如果 QuickReply 表中已有数据，需要为这些记录分配 user_id
3. **Token 过期**: JWT token 默认 30 分钟过期，可通过环境变量 `JWT_EXPIRE_MINUTES` 配置
4. **Secret Key**: 生产环境必须设置 `JWT_SECRET_KEY` 环境变量
5. **前端适配**: 确保前端正确处理 401 和 403 响应

## 回滚方案

如果需要回滚此次更改：

1. 恢复数据库备份
2. 使用 git 回滚到改造前的提交：
   ```bash
   git checkout <previous-commit-hash>
   ```

## 支持

如有问题，请查看：
- JWT_QUICKSTART.md - JWT 认证快速入门
- auth_utils.py - 认证工具实现
- 各 API 文件中的文档字符串
