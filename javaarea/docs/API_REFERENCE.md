# AI教育系统 -- API接口文档

> 基础路径：`http://localhost:9000`
>
> 认证方式：JWT Bearer Token（Header: `Authorization: Bearer <token>`）
>
> 统一响应格式：
> ```json
> {
>   "code": 200,
>   "message": "success",
>   "data": {}
> }
> ```

---

## 1. 认证模块 `/api/auth`

### 1.1 用户注册

```
POST /api/auth/register
权限要求：公开（无需认证）
```

**请求体：**
```json
{
  "username": "zhangsan",
  "password": "Abc123456",
  "nickname": "张三",
  "email": "zhangsan@example.com",
  "phone": "13800138000"
}
```

**响应（成功）：**
```json
{
  "code": 200,
  "message": "注册成功",
  "data": null
}
```

**说明：** 用户名和邮箱不允许重复。密码需满足长度和复杂度要求。默认角色为 STUDENT。

---

### 1.2 用户登录

```
POST /api/auth/login
权限要求：公开（无需认证）
```

**请求体：**
```json
{
  "username": "zhangsan",
  "password": "Abc123456"
}
```

**响应（成功）：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiJ9...",
    "tokenType": "Bearer",
    "expiresIn": 86400
  }
}
```

---

### 1.3 用户登出

```
POST /api/auth/logout
权限要求：已认证（任意角色）
```

**请求头：**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
```

**响应：**
```json
{
  "code": 200,
  "message": "登出成功",
  "data": null
}
```

**说明：** 将当前Token加入Redis黑名单，后续请求立即失效。

---

### 1.4 获取当前用户信息

```
GET /api/auth/me
权限要求：已认证（任意角色）
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "zhangsan",
    "nickname": "张三",
    "email": "zhangsan@example.com",
    "role": "STUDENT",
    "status": 1
  }
}
```

---

## 2. 用户模块 `/api/users`

### 2.1 获取当前用户详情

```
GET /api/users/me
权限要求：已认证（任意角色）
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "zhangsan",
    "nickname": "张三",
    "email": "zhangsan@example.com",
    "phone": "13800138000",
    "avatar": "https://cdn.example.com/avatar/1.jpg",
    "role": "STUDENT",
    "status": 1,
    "lastLoginTime": "2026-06-03T10:30:00"
  }
}
```

---

### 2.2 更新当前用户信息

```
PUT /api/users/me
权限要求：已认证（任意角色）
```

**请求体：**
```json
{
  "nickname": "张三丰",
  "phone": "13900139000",
  "avatar": "https://cdn.example.com/avatar/new.jpg"
}
```

**响应：**
```json
{
  "code": 200,
  "message": "更新成功",
  "data": null
}
```

---

### 2.3 获取用户列表（分页）

```
GET /api/users/?page=1&size=10
权限要求：ADMIN
```

**查询参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|:----:|--------|------|
| page | int | 否 | 1 | 页码 |
| size | int | 否 | 10 | 每页条数 |

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "records": [
      {
        "id": 1,
        "username": "zhangsan",
        "nickname": "张三",
        "email": "zhangsan@example.com",
        "role": "STUDENT",
        "status": 1,
        "lastLoginTime": "2026-06-03T10:30:00"
      }
    ],
    "total": 50,
    "size": 10,
    "current": 1,
    "pages": 5
  }
}
```

---

### 2.4 根据ID获取用户

```
GET /api/users/{id}
权限要求：ADMIN
```

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | Long | 用户ID |

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "zhangsan",
    "nickname": "张三",
    "email": "zhangsan@example.com",
    "role": "STUDENT",
    "status": 1
  }
}
```

---

### 2.5 更新用户状态

```
PUT /api/users/{id}/status?status=0
权限要求：ADMIN
```

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | Long | 用户ID |

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| status | Integer | 是 | 目标状态：1=启用, 0=禁用 |

**响应：**
```json
{
  "code": 200,
  "message": "状态更新成功",
  "data": null
}
```

---

## 3. 课程模块 `/api/courses`

### 3.1 创建课程

```
POST /api/courses
权限要求：TEACHER
```

**请求体：**
```json
{
  "title": "Python编程入门",
  "description": "面向零基础学生的Python课程",
  "coverImage": "https://cdn.example.com/cover/python.jpg",
  "category": "编程语言",
  "difficulty": "BEGINNER"
}
```

**响应：**
```json
{
  "code": 200,
  "message": "创建成功",
  "data": 1
}
```

**说明：** 返回新创建的课程ID。teacher_id 从当前登录用户自动获取。

---

### 3.2 获取课程列表

```
GET /api/courses?page=1&size=10&category=编程语言&difficulty=BEGINNER&keyword=Python
权限要求：已认证（任意角色）
```

**查询参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|:----:|--------|------|
| page | int | 否 | 1 | 页码 |
| size | int | 否 | 10 | 每页条数 |
| category | String | 否 | - | 课程分类 |
| difficulty | String | 否 | - | 难度级别 |
| keyword | String | 否 | - | 标题关键词 |
| status | Integer | 否 | - | 课程状态筛选 |

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "records": [
      {
        "id": 1,
        "title": "Python编程入门",
        "description": "面向零基础学生的Python课程",
        "coverImage": "https://cdn.example.com/cover/python.jpg",
        "category": "编程语言",
        "difficulty": "BEGINNER",
        "teacherId": 5,
        "status": 1,
        "studentCount": 120
      }
    ],
    "total": 30,
    "size": 10,
    "current": 1,
    "pages": 3
  }
}
```

---

### 3.3 获取课程详情

```
GET /api/courses/{id}
权限要求：已认证（任意角色）
```

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | Long | 课程ID |

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "title": "Python编程入门",
    "description": "面向零基础学生的Python课程",
    "coverImage": "https://cdn.example.com/cover/python.jpg",
    "category": "编程语言",
    "difficulty": "BEGINNER",
    "teacherId": 5,
    "status": 1,
    "studentCount": 120
  }
}
```

---

### 3.4 更新课程

```
PUT /api/courses/{id}
权限要求：TEACHER（仅课程创建者）或 ADMIN
```

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | Long | 课程ID |

**请求体：**
```json
{
  "title": "Python编程入门（修订版）",
  "description": "更新后的课程描述",
  "status": 1
}
```

**响应：**
```json
{
  "code": 200,
  "message": "更新成功",
  "data": null
}
```

---

### 3.5 删除课程

```
DELETE /api/courses/{id}
权限要求：TEACHER（仅课程创建者）或 ADMIN
```

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | Long | 课程ID |

**响应：**
```json
{
  "code": 200,
  "message": "删除成功",
  "data": null
}
```

---

### 3.6 学生选课

```
POST /api/courses/{id}/enroll
权限要求：STUDENT
```

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | Long | 课程ID |

**响应：**
```json
{
  "code": 200,
  "message": "选课成功",
  "data": null
}
```

---

## 4. 知识库模块 `/api/knowledge`

### 4.1 上传知识文件

```
POST /api/knowledge/upload
Content-Type: multipart/form-data
权限要求：TEACHER（仅课程创建者）或 ADMIN
```

**表单参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| file | File | 是 | 教学文件（PDF/DOCX/MD/TXT） |
| courseId | Long | 是 | 关联课程ID |
| name | String | 否 | 知识条目名称（默认取文件名） |
| description | String | 否 | 描述 |

**响应：**
```json
{
  "code": 200,
  "message": "上传成功，正在处理中",
  "data": {
    "id": 1,
    "name": "Python基础教程.pdf",
    "courseId": 1,
    "filePath": "/data/knowledge/2026/06/abc123.pdf",
    "fileType": "pdf",
    "fileSize": 2048576,
    "status": "PENDING"
  }
}
```

**说明：** 上传后系统异步调用Python Agent服务进行文档解析和向量化，处理完成后状态变为 INDEXED。

---

### 4.2 获取课程知识库列表

```
GET /api/knowledge?courseId=1
权限要求：已认证（任意角色）
```

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| courseId | Long | 是 | 课程ID |

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "name": "Python基础教程.pdf",
      "courseId": 1,
      "fileType": "pdf",
      "fileSize": 2048576,
      "status": "INDEXED",
      "createTime": "2026-06-03T10:00:00"
    },
    {
      "id": 2,
      "name": "Python进阶笔记.md",
      "courseId": 1,
      "fileType": "md",
      "fileSize": 51200,
      "status": "INDEXED",
      "createTime": "2026-06-03T11:00:00"
    }
  ]
}
```

---

### 4.3 获取知识条目详情

```
GET /api/knowledge/{id}
权限要求：已认证（任意角色）
```

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | Long | 知识条目ID |

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "name": "Python基础教程.pdf",
    "description": "Python基础语法和常用数据结构",
    "courseId": 1,
    "filePath": "/data/knowledge/2026/06/abc123.pdf",
    "fileType": "pdf",
    "fileSize": 2048576,
    "status": "INDEXED",
    "createTime": "2026-06-03T10:00:00"
  }
}
```

---

### 4.4 删除知识条目

```
DELETE /api/knowledge/{id}
权限要求：TEACHER（仅课程创建者）或 ADMIN
```

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | Long | 知识条目ID |

**响应：**
```json
{
  "code": 200,
  "message": "删除成功",
  "data": null
}
```

---

### 4.5 重新处理知识条目

```
POST /api/knowledge/{id}/reprocess
权限要求：TEACHER（仅课程创建者）或 ADMIN
```

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | Long | 知识条目ID |

**响应：**
```json
{
  "code": 200,
  "message": "重新处理已触发",
  "data": null
}
```

**说明：** 重新向Python Agent发送处理请求，适用于之前处理失败的条目。

---

## 5. AI对话模块 `/api/chat`

### 5.1 创建对话会话

```
POST /api/chat/sessions
权限要求：STUDENT
```

**请求体：**
```json
{
  "courseId": 1,
  "title": "Python基础问题咨询"
}
```

**响应：**
```json
{
  "code": 200,
  "message": "创建成功",
  "data": {
    "id": 1,
    "userId": 2,
    "courseId": 1,
    "title": "Python基础问题咨询",
    "createTime": "2026-06-03T14:00:00"
  }
}
```

---

### 5.2 获取会话列表

```
GET /api/chat/sessions?courseId=1
权限要求：STUDENT
```

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| courseId | Long | 否 | 按课程筛选 |

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "courseId": 1,
      "title": "Python基础问题咨询",
      "createTime": "2026-06-03T14:00:00"
    },
    {
      "id": 2,
      "courseId": 1,
      "title": "函数与模块学习",
      "createTime": "2026-06-03T15:00:00"
    }
  ]
}
```

---

### 5.3 获取会话消息列表

```
GET /api/chat/sessions/{id}/messages?page=1&size=20
权限要求：STUDENT（仅会话创建者）
```

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | Long | 会话ID |

**查询参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|:----:|--------|------|
| page | int | 否 | 1 | 页码 |
| size | int | 否 | 20 | 每页条数 |

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "records": [
      {
        "id": 1,
        "sessionId": 1,
        "role": "USER",
        "content": "Python中列表和元组有什么区别？",
        "createTime": "2026-06-03T14:01:00"
      },
      {
        "id": 2,
        "sessionId": 1,
        "role": "ASSISTANT",
        "content": "列表（list）和元组（tuple）的主要区别如下：\n1. 可变性：列表是可变的...",
        "tokenCount": 256,
        "createTime": "2026-06-03T14:01:05"
      }
    ],
    "total": 10,
    "size": 20,
    "current": 1,
    "pages": 1
  }
}
```

---

### 5.4 发送消息（AI问答）

```
POST /api/chat/sessions/{id}/messages
权限要求：STUDENT（仅会话创建者）
```

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | Long | 会话ID |

**请求体：**
```json
{
  "content": "Python中列表和元组有什么区别？"
}
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 2,
    "sessionId": 1,
    "role": "ASSISTANT",
    "content": "列表（list）和元组（tuple）的主要区别如下：\n1. 可变性：列表是可变的，可以添加、删除元素；元组是不可变的，创建后不能修改。\n2. 语法：列表使用方括号 []，元组使用圆括号 ()。\n3. 性能：元组由于不可变，访问速度略快于列表。\n4. 使用场景：列表适合需要动态增删元素的场景，元组适合存储固定数据（如坐标、RGB值）。",
    "tokenCount": 256,
    "createTime": "2026-06-03T14:01:05"
  }
}
```

**说明：** 系统内部流程：保存用户消息 -> 查询课程知识库 -> 调用Python Agent RAG服务 -> 保存AI回复 -> 返回结果。

---

### 5.5 删除对话会话

```
DELETE /api/chat/sessions/{id}
权限要求：STUDENT（仅会话创建者）
```

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | Long | 会话ID |

**响应：**
```json
{
  "code": 200,
  "message": "删除成功",
  "data": null
}
```

---

## 6. 学习路线模块 `/api/learning/paths`

### 6.1 AI生成学习路线

```
POST /api/learning/paths/generate
权限要求：STUDENT
```

**请求体：**
```json
{
  "courseId": 1
}
```

**响应：**
```json
{
  "code": 200,
  "message": "学习路线生成成功",
  "data": {
    "id": 1,
    "userId": 2,
    "courseId": 1,
    "title": "Python编程入门 - 个性化学习路线",
    "description": "根据您的学习风格和水平，为您定制的学习路线",
    "totalSteps": 5,
    "completedSteps": 0,
    "status": 0,
    "steps": [
      {
        "id": 1,
        "pathId": 1,
        "stepOrder": 1,
        "title": "Python基础语法",
        "description": "学习变量、数据类型、运算符等基础概念",
        "knowledgeBaseId": 1,
        "status": 0
      },
      {
        "id": 2,
        "pathId": 1,
        "stepOrder": 2,
        "title": "控制流与函数",
        "description": "掌握条件判断、循环和函数定义",
        "knowledgeBaseId": 2,
        "status": 0
      },
      {
        "id": 3,
        "pathId": 1,
        "stepOrder": 3,
        "title": "数据结构",
        "description": "列表、字典、集合、元组的使用",
        "knowledgeBaseId": null,
        "status": 0
      },
      {
        "id": 4,
        "pathId": 1,
        "stepOrder": 4,
        "title": "面向对象编程",
        "description": "类、继承、多态等OOP概念",
        "knowledgeBaseId": null,
        "status": 0
      },
      {
        "id": 5,
        "pathId": 1,
        "stepOrder": 5,
        "title": "项目实战",
        "description": "综合运用所学知识完成一个小型项目",
        "knowledgeBaseId": null,
        "status": 0
      }
    ],
    "createTime": "2026-06-03T16:00:00"
  }
}
```

**说明：** 系统收集学生画像和历史学习记录，调用Python Agent生成个性化路线。AI会根据学生的薄弱环节和学习风格调整步骤顺序和内容侧重。

---

### 6.2 获取学习路线列表

```
GET /api/learning/paths?courseId=1
权限要求：STUDENT
```

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| courseId | Long | 否 | 按课程筛选 |

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "courseId": 1,
      "title": "Python编程入门 - 个性化学习路线",
      "totalSteps": 5,
      "completedSteps": 2,
      "status": 0,
      "createTime": "2026-06-03T16:00:00"
    }
  ]
}
```

---

### 6.3 获取学习路线详情

```
GET /api/learning/paths/{id}
权限要求：STUDENT（仅路线拥有者）
```

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | Long | 路线ID |

**响应：** 同 6.1 的 data 结构（包含完整步骤列表）。

---

### 6.4 更新学习步骤状态

```
PUT /api/learning/paths/{pathId}/steps/{stepId}
权限要求：STUDENT（仅路线拥有者）
```

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| pathId | Long | 路线ID |
| stepId | Long | 步骤ID |

**请求体：**
```json
{
  "status": 2
}
```

**说明：** status 值：0=待开始, 1=进行中, 2=已完成。当所有步骤完成时，路线状态自动更新为已完成。

**响应：**
```json
{
  "code": 200,
  "message": "步骤状态更新成功",
  "data": null
}
```

---

### 6.5 删除学习路线

```
DELETE /api/learning/paths/{id}
权限要求：STUDENT（仅路线拥有者）
```

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | Long | 路线ID |

**响应：**
```json
{
  "code": 200,
  "message": "删除成功",
  "data": null
}
```

---

## 7. 学习记录模块 `/api/study/records`

### 7.1 创建学习记录

```
POST /api/study/records
权限要求：STUDENT
```

**请求体：**
```json
{
  "courseId": 1,
  "sessionId": 1,
  "duration": 1800,
  "interactionCount": 15,
  "summary": "学习了Python基础语法，重点练习了变量和数据类型"
}
```

**响应：**
```json
{
  "code": 200,
  "message": "记录创建成功",
  "data": {
    "id": 1,
    "userId": 2,
    "courseId": 1,
    "sessionId": 1,
    "duration": 1800,
    "interactionCount": 15,
    "summary": "学习了Python基础语法，重点练习了变量和数据类型",
    "createTime": "2026-06-03T17:00:00"
  }
}
```

---

### 7.2 获取学习记录列表

```
GET /api/study/records?courseId=1
权限要求：STUDENT
```

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| courseId | Long | 否 | 按课程筛选 |

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "courseId": 1,
      "duration": 1800,
      "interactionCount": 15,
      "summary": "学习了Python基础语法",
      "createTime": "2026-06-03T17:00:00"
    }
  ]
}
```

---

### 7.3 获取学习统计数据

```
GET /api/study/records/stats?courseId=1
权限要求：STUDENT
```

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| courseId | Long | 否 | 按课程统计 |

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "totalDuration": 36000,
    "totalSessions": 20,
    "totalInteractions": 300,
    "averageDuration": 1800,
    "studyDays": 15,
    "streakDays": 5
  }
}
```

---

## 8. 学生画像模块 `/api/profile`

### 8.1 获取学生画像

```
GET /api/profile
权限要求：STUDENT
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "userId": 2,
    "learningStyle": "VISUAL",
    "strengths": "逻辑思维,数学推理",
    "weaknesses": "记忆类知识,英语阅读",
    "interests": "编程,数据分析",
    "gradeLevel": "大学一年级",
    "preferences": {
      "language": "zh",
      "difficulty": "medium",
      "pace": "moderate"
    }
  }
}
```

---

### 8.2 更新学生画像

```
PUT /api/profile
权限要求：STUDENT
```

**请求体：**
```json
{
  "learningStyle": "VISUAL",
  "strengths": "逻辑思维,数学推理,编程能力",
  "weaknesses": "英语阅读",
  "interests": "编程,数据分析,机器学习",
  "gradeLevel": "大学一年级",
  "preferences": {
    "language": "zh",
    "difficulty": "medium",
    "pace": "fast"
  }
}
```

**响应：**
```json
{
  "code": 200,
  "message": "画像更新成功",
  "data": null
}
```

---

### 8.3 获取画像雷达图数据

```
GET /api/profile/radar
权限要求：STUDENT
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "dimensions": [
      { "name": "编程基础", "score": 75 },
      { "name": "算法思维", "score": 60 },
      { "name": "数据结构", "score": 45 },
      { "name": "项目实践", "score": 30 },
      { "name": "理论知识", "score": 55 },
      { "name": "问题解决", "score": 65 }
    ],
    "overallScore": 55
  }
}
```

**说明：** 雷达图数据基于学生的学习记录、AI问答表现和学习路线完成情况综合计算。

---

## 9. 管理后台模块 `/api/admin`

### 9.1 获取仪表盘数据

```
GET /api/admin/dashboard
权限要求：ADMIN
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "userStats": {
      "totalUsers": 500,
      "totalStudents": 450,
      "totalTeachers": 48,
      "totalAdmins": 2,
      "activeToday": 120
    },
    "courseStats": {
      "totalCourses": 80,
      "publishedCourses": 65,
      "draftCourses": 15
    },
    "knowledgeStats": {
      "totalDocuments": 320,
      "indexedDocuments": 310,
      "pendingDocuments": 8,
      "failedDocuments": 2
    },
    "chatStats": {
      "totalSessions": 1500,
      "totalMessages": 45000,
      "messagesToday": 500
    },
    "learningStats": {
      "totalPaths": 600,
      "completedPaths": 180,
      "inProgressPaths": 420
    }
  }
}
```

---

### 9.2 系统健康检查

```
GET /api/admin/system/health
权限要求：ADMIN
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "status": "UP",
    "java": {
      "status": "UP",
      "version": "17.0.8",
      "uptime": "3d 12h 30m"
    },
    "mysql": {
      "status": "UP",
      "version": "8.0.35",
      "activeConnections": 10,
      "maxConnections": 100
    },
    "redis": {
      "status": "UP",
      "usedMemory": "128MB",
      "connectedClients": 5
    },
    "agentService": {
      "status": "UP",
      "url": "http://agent-service:8000",
      "responseTime": "45ms"
    }
  }
}
```

---

## 附录：错误码

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证（Token无效或已过期） |
| 403 | 无权限（角色不足） |
| 404 | 资源不存在 |
| 409 | 资源冲突（如用户名已存在） |
| 429 | 请求过于频繁（限流） |
| 500 | 服务器内部错误 |
| 503 | Agent服务不可用 |

**错误响应示例：**
```json
{
  "code": 401,
  "message": "Token已过期，请重新登录",
  "data": null
}
```
