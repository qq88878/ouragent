# AI教育系统 -- Java后端

基于Spring Boot 3的AI驱动智能教育平台后端服务。教师上传知识库，学生获得基于RAG的AI问答和个性化学习路线。

## 技术栈

- **后端框架：** Spring Boot 3.2
- **ORM：** MyBatis-Plus 3.5.5
- **数据库：** MySQL 8.x
- **缓存：** Redis 7.x
- **安全：** Spring Security + JWT (JJWT 0.12.3)
- **构建：** Maven 3.9+
- **JDK：** 17

## 项目结构

```
src/main/java/com/edu/agent/
├── EduAgentApplication.java              # 启动类
├── common/
│   ├── base/
│   │   └── BaseEntity.java               # 实体基类 (id, createTime, updateTime, deleted)
│   ├── constant/
│   │   └── RoleConstants.java            # 角色常量 (ADMIN, TEACHER, STUDENT)
│   ├── exception/
│   │   ├── BizException.java             # 业务异常
│   │   └── GlobalExceptionHandler.java   # 全局异常处理
│   └── result/
│       ├── Result.java                   # 统一响应包装
│       └── ResultCode.java               # 响应码定义
├── config/
│   ├── AsyncConfig.java                  # 异步配置
│   ├── CorsConfig.java                   # 跨域配置
│   ├── MyBatisPlusConfig.java            # MyBatis-Plus配置
│   ├── RedisConfig.java                  # Redis配置
│   ├── SecurityConfig.java               # Spring Security配置
│   └── WebMvcConfig.java                 # Web MVC配置
├── module/
│   ├── auth/                             # 认证模块
│   │   ├── controller/AuthController.java
│   │   ├── dto/
│   │   │   ├── LoginRequest.java
│   │   │   ├── RegisterRequest.java
│   │   │   └── TokenResponse.java
│   │   └── service/
│   │       ├── AuthService.java
│   │       └── impl/AuthServiceImpl.java
│   ├── user/                             # 用户模块
│   │   ├── controller/UserController.java
│   │   ├── dto/
│   │   │   ├── UserDTO.java
│   │   │   └── UserProfileDTO.java
│   │   ├── entity/User.java
│   │   ├── mapper/UserMapper.java
│   │   └── service/
│   │       ├── UserService.java
│   │       └── impl/UserServiceImpl.java
│   ├── course/                           # 课程模块
│   │   ├── controller/CourseController.java
│   │   ├── dto/
│   │   │   ├── CourseDTO.java
│   │   │   └── CourseQueryDTO.java
│   │   ├── entity/Course.java
│   │   ├── mapper/CourseMapper.java
│   │   └── service/
│   │       ├── CourseService.java
│   │       └── impl/CourseServiceImpl.java
│   ├── knowledge/                        # 知识库模块
│   │   ├── controller/KnowledgeController.java
│   │   ├── dto/
│   │   │   ├── KnowledgeDTO.java
│   │   │   └── KnowledgeUploadDTO.java
│   │   ├── entity/KnowledgeBase.java
│   │   ├── mapper/KnowledgeMapper.java
│   │   └── service/
│   │       ├── KnowledgeService.java
│   │       └── impl/KnowledgeServiceImpl.java
│   ├── chat/                             # AI对话模块 (待实现)
│   ├── learning/                         # 学习路线模块 (待实现)
│   └── admin/                            # 管理后台模块 (待实现)
└── security/
    ├── JwtAuthenticationFilter.java       # JWT过滤器
    ├── LoginUser.java                     # 登录用户信息
    └── UserDetailsServiceImpl.java       # UserDetailsService实现

src/main/resources/
├── application.yml                        # 主配置
├── application-dev.yml                    # 开发环境配置
├── application-prod.yml                   # 生产环境配置
├── db/
│   └── schema.sql                         # 数据库建表SQL (9张表)
└── logback-spring.xml                     # 日志配置
```

## 快速开始

### 环境要求

- JDK 17+
- Maven 3.9+
- MySQL 8.x
- Redis 7.x

### 1. 准备数据库

```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE edu_agent DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 导入表结构
mysql -u root -p edu_agent < src/main/resources/db/schema.sql
```

### 2. 配置应用

编辑 `src/main/resources/application-dev.yml`，修改数据库和Redis连接信息：

```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/edu_agent?useSSL=false&serverTimezone=Asia/Shanghai
    username: root
    password: your_password
  data:
    redis:
      host: localhost
      port: 6379
```

### 3. 构建与运行

```bash
# 编译打包
mvn clean package -DskipTests

# 运行（开发环境）
mvn spring-boot:run -Dspring-boot.run.profiles=dev

# 或运行jar包
java -jar target/edu-agent-1.0.0.jar --spring.profiles.active=dev
```

应用启动后监听端口 `9000`，访问 `http://localhost:9000`。

### 4. 健康检查

```bash
curl http://localhost:9000/api/agent/health
```

## 开发指南

### 添加新模块

以 `module/order` 为例，按以下步骤操作：

**1. 创建实体类 (Entity)**

```java
package com.edu.agent.module.order.entity;

import com.edu.agent.common.base.BaseEntity;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = true)
@TableName("order")
public class Order extends BaseEntity {
    private Long userId;
    private String orderNo;
    private Integer status;
}
```

**2. 创建Mapper接口**

```java
package com.edu.agent.module.order.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.edu.agent.module.order.entity.Order;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface OrderMapper extends BaseMapper<Order> {
}
```

**3. 创建Service接口和实现**

```java
// OrderService.java
public interface OrderService extends IService<Order> {
    // 业务方法定义
}

// impl/OrderServiceImpl.java
@Service
@RequiredArgsConstructor
public class OrderServiceImpl extends ServiceImpl<OrderMapper, Order> implements OrderService {
    // 业务方法实现
}
```

**4. 创建Controller**

```java
@RestController
@RequestMapping("/api/orders")
@RequiredArgsConstructor
public class OrderController {

    private final OrderService orderService;

    @GetMapping
    public Result<List<Order>> list() {
        return Result.ok(orderService.list());
    }
}
```

**5. 创建数据库表**

在 `src/main/resources/db/schema.sql` 中追加建表语句，确保包含 `create_time`、`update_time`、`deleted` 公共字段。

## API文档

详细的API接口文档请参阅 [docs/API_REFERENCE.md](docs/API_REFERENCE.md)

## 分阶段开发

详细的分阶段开发计划请参阅 [docs/JAVA_EDU_SYSTEM_DESIGN.md](docs/JAVA_EDU_SYSTEM_DESIGN.md)

| 阶段 | 内容 | 状态 |
|------|------|------|
| 阶段一 | 基础框架搭建、认证体系、用户模块 | 进行中 |
| 阶段二 | 课程与知识库模块 | 计划中 |
| 阶段三 | AI对话与RAG问答 | 计划中 |
| 阶段四 | 学习路线与学生画像 | 计划中 |
| 阶段五 | 管理后台与性能优化 | 计划中 |
