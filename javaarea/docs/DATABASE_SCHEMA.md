# AI教育系统 -- 数据库设计文档

## 1. ER关系图

```
+----------------+       +------------------+       +--------------------+
|     user       |       |     course       |       |  knowledge_base    |
|----------------|       |------------------|       |--------------------|
| id (PK)        |<------| teacher_id (FK)  |<------| course_id (FK)     |
| username (UQ)  |       | id (PK)          |       | id (PK)            |
| email (UQ)     |       | title            |       | name               |
| role           |       | category         |       | file_path          |
| status         |       | difficulty       |       | vector_doc_id      |
| ...            |       | status           |       | status             |
+-------+--------+       +--------+---------+       +--------------------+
        |                          |
        |                          |
        v                          v
+------------------+     +------------------+       +--------------------+
| chat_session     |     | learning_path    |       | study_record       |
|------------------|     |------------------|       |--------------------|
| id (PK)          |     | id (PK)          |       | id (PK)            |
| user_id (FK) ----+--+  | user_id (FK) ----+--+    | user_id (FK) ------+--+
| course_id (FK) --+-+|  | course_id (FK) --+-+|    | course_id (FK) ----+-+|
| title            | ||  | title            | ||    | session_id (FK) ---+-++|
+--------+---------+ ||  | total_steps      | ||    | duration           | |||
         |           ||  | completed_steps  | ||    | interaction_count  | |||
         v           ||  | status           | ||    +--------------------+ |||
+------------------+ ||  +--------+---------+ ||                           |||
| chat_message     | ||           |           ||  +----------------------+ |||
|------------------| ||           v           ||  | student_profile      | |||
| id (PK)          | ||  +------------------+ ||  |----------------------| |||
| session_id (FK) -+++| |learning_path_step| ||  | id (PK)              | |||
| role             | ||  |------------------| ||  | user_id (UQ, FK) ----++++
| content          | ||  | id (PK)          | ||  | learning_style       | |||
| token_count      | ||  | path_id (FK) ----+++  | strengths            | |||
+------------------+ ||  | step_order       | ||  | weaknesses           | |||
                     ||  | title            | ||  | interests            | |||
                     ||  | knowledge_base_id| ||  | preferences (JSON)   | |||
                     ||  | status           | ||  +----------------------+ |||
                     ||  +------------------+ ||                           |||
                     ||                       ||                           |||
              user   +--- chat_session        ||    study_record           |||
              user   +--- study_record        ||    student_profile        |||
              user   +--- learning_path       ||                           |||
              course +--- chat_session         ||                           |||
              course +--- study_record         ||                           |||
              course +--- learning_path        ||                           |||
              knowledge_base +--- learning_path_step                       |||
              chat_session +--- chat_message    ||                         |||
              learning_path +--- learning_path_step                        |||
```

**简化的实体关系概览：**

```
user (1) ----< (N) course                  [teacher_id]
user (1) ----< (N) chat_session            [user_id]
user (1) ----< (N) learning_path           [user_id]
user (1) ----< (N) study_record            [user_id]
user (1) ----(1) student_profile           [user_id]

course (1) ----< (N) knowledge_base        [course_id]
course (1) ----< (N) chat_session          [course_id]
course (1) ----< (N) learning_path         [course_id]
course (1) ----< (N) study_record          [course_id]

chat_session (1) ----< (N) chat_message    [session_id]

learning_path (1) ----< (N) learning_path_step  [path_id]

knowledge_base (1) ----< (N) learning_path_step [knowledge_base_id]
```

---

## 2. 各表字段说明

### 2.1 user（用户表）

| 字段名 | 类型 | 可空 | 默认值 | 说明 |
|--------|------|:----:|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| username | VARCHAR(64) | NO | - | 用户名，唯一 |
| password | VARCHAR(255) | NO | - | 密码（BCrypt加密存储） |
| nickname | VARCHAR(64) | YES | NULL | 昵称 |
| email | VARCHAR(128) | YES | NULL | 邮箱，唯一 |
| phone | VARCHAR(32) | YES | NULL | 手机号 |
| avatar | VARCHAR(255) | YES | NULL | 头像URL |
| role | VARCHAR(32) | NO | 'STUDENT' | 角色：STUDENT / TEACHER / ADMIN |
| status | TINYINT | NO | 1 | 状态：1=启用, 0=禁用 |
| last_login_time | DATETIME | YES | NULL | 最近登录时间 |
| create_time | DATETIME | NO | CURRENT_TIMESTAMP | 创建时间 |
| update_time | DATETIME | NO | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| deleted | TINYINT | NO | 0 | 逻辑删除：0=未删, 1=已删 |

### 2.2 course（课程表）

| 字段名 | 类型 | 可空 | 默认值 | 说明 |
|--------|------|:----:|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| title | VARCHAR(255) | NO | - | 课程标题 |
| description | TEXT | YES | NULL | 课程描述 |
| cover_image | VARCHAR(255) | YES | NULL | 封面图片URL |
| category | VARCHAR(64) | YES | NULL | 课程分类 |
| difficulty | VARCHAR(32) | YES | NULL | 难度：BEGINNER / INTERMEDIATE / ADVANCED |
| teacher_id | BIGINT | NO | - | 教师ID，外键关联user.id |
| status | TINYINT | NO | 0 | 状态：0=草稿, 1=已发布 |
| create_time | DATETIME | NO | CURRENT_TIMESTAMP | 创建时间 |
| update_time | DATETIME | NO | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| deleted | TINYINT | NO | 0 | 逻辑删除：0=未删, 1=已删 |

### 2.3 knowledge_base（知识库表）

| 字段名 | 类型 | 可空 | 默认值 | 说明 |
|--------|------|:----:|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| name | VARCHAR(128) | NO | - | 知识条目名称 |
| description | TEXT | YES | NULL | 描述 |
| course_id | BIGINT | YES | NULL | 关联课程ID，外键关联course.id |
| file_path | VARCHAR(512) | NO | - | 文件存储路径 |
| file_type | VARCHAR(32) | YES | NULL | 文件类型：pdf / docx / md / txt |
| file_size | BIGINT | YES | NULL | 文件大小（字节） |
| status | TINYINT | NO | 0 | 处理状态：0=待处理, 1=已索引, 2=处理失败 |
| create_time | DATETIME | NO | CURRENT_TIMESTAMP | 创建时间 |
| update_time | DATETIME | NO | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| deleted | TINYINT | NO | 0 | 逻辑删除：0=未删, 1=已删 |

### 2.4 chat_session（对话会话表）

| 字段名 | 类型 | 可空 | 默认值 | 说明 |
|--------|------|:----:|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| user_id | BIGINT | NO | - | 用户ID，外键关联user.id |
| course_id | BIGINT | YES | NULL | 关联课程ID，外键关联course.id |
| title | VARCHAR(255) | YES | NULL | 会话标题 |
| create_time | DATETIME | NO | CURRENT_TIMESTAMP | 创建时间 |
| update_time | DATETIME | NO | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| deleted | TINYINT | NO | 0 | 逻辑删除：0=未删, 1=已删 |

### 2.5 chat_message（对话消息表）

| 字段名 | 类型 | 可空 | 默认值 | 说明 |
|--------|------|:----:|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| session_id | BIGINT | NO | - | 会话ID，外键关联chat_session.id |
| role | VARCHAR(32) | NO | - | 角色：USER / ASSISTANT / SYSTEM |
| content | TEXT | NO | - | 消息内容 |
| token_count | INT | YES | NULL | Token消耗量 |
| create_time | DATETIME | NO | CURRENT_TIMESTAMP | 创建时间 |
| update_time | DATETIME | NO | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| deleted | TINYINT | NO | 0 | 逻辑删除：0=未删, 1=已删 |

### 2.6 learning_path（学习路线表）

| 字段名 | 类型 | 可空 | 默认值 | 说明 |
|--------|------|:----:|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| user_id | BIGINT | NO | - | 学生ID，外键关联user.id |
| course_id | BIGINT | NO | - | 课程ID，外键关联course.id |
| title | VARCHAR(255) | NO | - | 路线标题 |
| description | TEXT | YES | NULL | 路线描述 |
| total_steps | INT | NO | 0 | 总步骤数 |
| completed_steps | INT | NO | 0 | 已完成步骤数 |
| status | TINYINT | NO | 0 | 状态：0=进行中, 1=已完成, 2=已放弃 |
| create_time | DATETIME | NO | CURRENT_TIMESTAMP | 创建时间 |
| update_time | DATETIME | NO | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| deleted | TINYINT | NO | 0 | 逻辑删除：0=未删, 1=已删 |

### 2.7 learning_path_step（学习路线步骤表）

| 字段名 | 类型 | 可空 | 默认值 | 说明 |
|--------|------|:----:|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| path_id | BIGINT | NO | - | 路线ID，外键关联learning_path.id |
| step_order | INT | NO | - | 步骤顺序号 |
| title | VARCHAR(255) | NO | - | 步骤标题 |
| description | TEXT | YES | NULL | 步骤描述 |
| knowledge_base_id | BIGINT | YES | NULL | 关联知识库ID，外键关联knowledge_base.id |
| status | TINYINT | NO | 0 | 状态：0=待开始, 1=进行中, 2=已完成 |
| create_time | DATETIME | NO | CURRENT_TIMESTAMP | 创建时间 |
| update_time | DATETIME | NO | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| deleted | TINYINT | NO | 0 | 逻辑删除：0=未删, 1=已删 |

### 2.8 study_record（学习记录表）

| 字段名 | 类型 | 可空 | 默认值 | 说明 |
|--------|------|:----:|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| user_id | BIGINT | NO | - | 学生ID，外键关联user.id |
| course_id | BIGINT | NO | - | 课程ID，外键关联course.id |
| session_id | BIGINT | YES | NULL | 对话会话ID，外键关联chat_session.id |
| duration | INT | YES | NULL | 学习时长（秒） |
| interaction_count | INT | YES | NULL | 交互次数 |
| summary | TEXT | YES | NULL | 学习摘要 |
| create_time | DATETIME | NO | CURRENT_TIMESTAMP | 创建时间 |
| update_time | DATETIME | NO | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| deleted | TINYINT | NO | 0 | 逻辑删除：0=未删, 1=已删 |

### 2.9 student_profile（学生画像表）

| 字段名 | 类型 | 可空 | 默认值 | 说明 |
|--------|------|:----:|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| user_id | BIGINT | NO | - | 学生ID，唯一，外键关联user.id |
| learning_style | VARCHAR(64) | YES | NULL | 学习风格：VISUAL / AUDITORY / READING / KINESTHETIC |
| strengths | VARCHAR(512) | YES | NULL | 优势领域 |
| weaknesses | VARCHAR(512) | YES | NULL | 薄弱环节 |
| interests | VARCHAR(512) | YES | NULL | 兴趣方向 |
| grade_level | VARCHAR(32) | YES | NULL | 年级/水平 |
| preferences | JSON | YES | NULL | 扩展偏好设置（JSON格式） |
| create_time | DATETIME | NO | CURRENT_TIMESTAMP | 创建时间 |
| update_time | DATETIME | NO | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| deleted | TINYINT | NO | 0 | 逻辑删除：0=未删, 1=已删 |

---

## 3. 索引设计

### 3.1 user 表

| 索引名 | 类型 | 字段 | 说明 |
|--------|------|------|------|
| PRIMARY | 主键 | id | 自增主键 |
| uk_username | 唯一索引 | username | 用户名唯一约束 |
| uk_email | 唯一索引 | email | 邮箱唯一约束 |
| idx_role | 普通索引 | role | 按角色查询用户列表 |

### 3.2 course 表

| 索引名 | 类型 | 字段 | 说明 |
|--------|------|------|------|
| PRIMARY | 主键 | id | 自增主键 |
| idx_teacher_id | 普通索引 | teacher_id | 按教师查询课程 |
| idx_category | 普通索引 | category | 按分类筛选课程 |

### 3.3 knowledge_base 表

| 索引名 | 类型 | 字段 | 说明 |
|--------|------|------|------|
| PRIMARY | 主键 | id | 自增主键 |
| idx_course_id | 普通索引 | course_id | 按课程查询知识条目 |

### 3.4 chat_session 表

| 索引名 | 类型 | 字段 | 说明 |
|--------|------|------|------|
| PRIMARY | 主键 | id | 自增主键 |
| idx_user_id | 普通索引 | user_id | 按用户查询会话列表 |
| idx_course_id | 普通索引 | course_id | 按课程筛选会话 |

### 3.5 chat_message 表

| 索引名 | 类型 | 字段 | 说明 |
|--------|------|------|------|
| PRIMARY | 主键 | id | 自增主键 |
| idx_session_id | 普通索引 | session_id | 按会话查询消息列表 |

### 3.6 learning_path 表

| 索引名 | 类型 | 字段 | 说明 |
|--------|------|------|------|
| PRIMARY | 主键 | id | 自增主键 |
| idx_user_id | 普通索引 | user_id | 按学生查询学习路线 |
| idx_course_id | 普通索引 | course_id | 按课程查询学习路线 |

### 3.7 learning_path_step 表

| 索引名 | 类型 | 字段 | 说明 |
|--------|------|------|------|
| PRIMARY | 主键 | id | 自增主键 |
| idx_path_id | 普通索引 | path_id | 按路线查询步骤 |
| idx_knowledge_base_id | 普通索引 | knowledge_base_id | 按知识库查询关联步骤 |

### 3.8 study_record 表

| 索引名 | 类型 | 字段 | 说明 |
|--------|------|------|------|
| PRIMARY | 主键 | id | 自增主键 |
| idx_user_id | 普通索引 | user_id | 按学生查询学习记录 |
| idx_course_id | 普通索引 | course_id | 按课程查询学习记录 |

### 3.9 student_profile 表

| 索引名 | 类型 | 字段 | 说明 |
|--------|------|------|------|
| PRIMARY | 主键 | id | 自增主键 |
| uk_user_id | 唯一索引 | user_id | 每个学生一条画像记录 |

---

## 4. 建表SQL

完整的建表DDL语句位于：

```
src/main/resources/db/schema.sql
```

包含全部9张表的 `CREATE TABLE IF NOT EXISTS` 语句，可直接在MySQL 8.x中执行。

---

## 5. 字段命名规范

### 5.1 命名规则

- **表名**：`snake_case`，使用英文名词复数或单数（本项目使用单数，如 `user`、`course`）
- **字段名**：`snake_case`，如 `create_time`、`teacher_id`、`file_path`
- **索引名**：主键 `PRIMARY`，唯一索引 `uk_字段名`，普通索引 `idx_字段名`
- **外键**：逻辑外键（不建物理外键约束），字段名以 `_id` 结尾，如 `teacher_id`、`course_id`

### 5.2 公共字段（每张表都有）

| 字段名 | 类型 | 说明 | 自动填充 |
|--------|------|------|:--------:|
| id | BIGINT AUTO_INCREMENT | 主键 | - |
| create_time | DATETIME DEFAULT CURRENT_TIMESTAMP | 创建时间 | INSERT |
| update_time | DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE | 更新时间 | INSERT + UPDATE |
| deleted | TINYINT DEFAULT 0 | 逻辑删除标志 | - |

对应Java基类 `BaseEntity`（`com.edu.agent.common.base.BaseEntity`）：

```java
@Data
public class BaseEntity implements Serializable {
    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;

    @TableLogic
    private Integer deleted;
}
```

### 5.3 字符集与引擎

- **存储引擎**：InnoDB（支持事务、行级锁）
- **字符集**：utf8mb4
- **排序规则**：utf8mb4_unicode_ci
