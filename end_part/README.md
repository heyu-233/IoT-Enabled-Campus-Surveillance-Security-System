# 后端项目说明

## 项目概述

本项目是一个基于Spring Boot的后端服务，提供了与前端API文件中定义的所有接口完全匹配的后端服务。主要功能包括：

- 用户认证和授权（登录、注册、登出、获取当前用户信息）
- 摄像头管理（获取列表、获取详情、获取直播流、刷新状态、添加、更新、删除）
- 可疑行为管理（获取列表、获取详情、删除、实时推送）
- 告警管理（获取列表、获取详情、标记为已处理、搜索）
- 数据分析（行为类型分布、每日告警统计、区域热力图、行为类型详情）
- 系统配置（获取和更新告警设置）

## 技术栈

- Java 17
- Spring Boot 4.0.2
- Spring Security
- MyBatis
- H2内存数据库（开发环境）
- MySQL（生产环境）
- JWT（JSON Web Token）
- Lombok

## 项目结构

```
end_part/
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/
│   │   │       └── example/
│   │   │           └── end_part/
│   │   │               ├── config/          # 配置类
│   │   │               ├── controller/       # 控制器
│   │   │               ├── dto/              # 数据传输对象
│   │   │               ├── entity/           # 实体类
│   │   │               ├── exception/        # 异常处理
│   │   │               ├── mapper/           # MyBatis映射器
│   │   │               ├── service/          # 服务类
│   │   │               ├── utils/            # 工具类
│   │   │               └── EndPartApplication.java  # 应用程序入口
│   │   └── resources/
│   │       ├── db/           # 数据库初始化脚本
│   │       ├── application.properties  # 应用程序配置
│   └── test/
├── pom.xml  # Maven依赖配置
└── README.md  # 项目说明文档
```

## API接口说明

### 认证相关API

| 接口路径 | 方法 | 功能 |
|---------|------|------|
| `/auth/login` | POST | 用户登录 |
| `/auth/register` | POST | 用户注册 |
| `/auth/logout` | POST | 用户登出 |
| `/auth/me` | GET | 获取当前用户信息 |

### 摄像头相关API

| 接口路径 | 方法 | 功能 |
|---------|------|------|
| `/cameras` | GET | 获取摄像头列表 |
| `/cameras/{id}` | GET | 获取摄像头详情 |
| `/cameras/{id}/stream` | GET | 获取摄像头直播流 |
| `/cameras/{id}/refresh` | POST | 刷新摄像头状态 |
| `/cameras` | POST | 添加摄像头 |
| `/cameras/{id}` | PUT | 更新摄像头 |
| `/cameras/{id}` | DELETE | 删除摄像头 |

### 可疑行为相关API

| 接口路径 | 方法 | 功能 |
|---------|------|------|
| `/behaviors` | GET | 获取可疑行为列表 |
| `/behaviors/{id}` | GET | 获取可疑行为详情 |
| `/behaviors/{id}` | DELETE | 删除可疑行为 |
| `/behaviors/stream` | GET | 订阅可疑行为实时推送（SSE） |

### 告警相关API

| 接口路径 | 方法 | 功能 |
|---------|------|------|
| `/alerts` | GET | 获取告警列表 |
| `/alerts/{id}` | GET | 获取告警详情 |
| `/alerts/{id}/process` | POST | 标记告警为已处理 |
| `/alerts/search` | GET | 搜索告警 |

### 数据分析相关API

| 接口路径 | 方法 | 功能 |
|---------|------|------|
| `/analytics/type-distribution` | GET | 获取行为类型分布 |
| `/analytics/daily-alerts` | GET | 获取每日告警统计 |
| `/analytics/area-heatmap` | GET | 获取区域热力图 |
| `/analytics/types/{type}` | GET | 获取行为类型详情 |

### 系统配置相关API

| 接口路径 | 方法 | 功能 |
|---------|------|------|
| `/config/alert-settings` | GET | 获取告警设置 |
| `/config/alert-settings` | PUT | 更新告警设置 |

## 部署和运行说明

### 开发环境

1. 克隆项目到本地
2. 确保安装了Java 17
3. 确保安装了Maven
4. 运行以下命令启动应用程序：

```bash
mvn spring-boot:run
```

应用程序将在 `http://localhost:8080/api` 上运行，使用H2内存数据库。

### 生产环境

1. 克隆项目到服务器
2. 确保安装了Java 17
3. 确保安装了Maven
4. 确保安装了MySQL数据库
5. 修改 `application.properties` 文件中的数据库连接信息
6. 运行以下命令构建应用程序：

```bash
mvn clean package
```

7. 运行以下命令启动应用程序：

```bash
java -jar target/end_part-0.0.1-SNAPSHOT.jar
```

## 数据库配置

### 开发环境

使用H2内存数据库，无需额外配置。

### 生产环境

使用MySQL数据库，需要创建数据库和表结构。可以使用 `src/main/resources/db/init.sql` 脚本初始化数据库。

## 安全配置

- 使用JWT进行身份认证
- 密码使用BCrypt加密存储
- 所有API接口（除了登录和注册）都需要认证

## 错误处理和日志记录

- 实现了全局异常处理器，捕获和处理所有异常
- 使用SLF4J进行日志记录

## 测试

可以使用Postman或其他API测试工具测试API接口。

### 测试步骤

1. 启动应用程序
2. 发送POST请求到 `/auth/register` 注册新用户
3. 发送POST请求到 `/auth/login` 登录获取token
4. 在后续请求的请求头中添加 `Authorization: Bearer {token}`
5. 测试其他API接口

## 注意事项

- 本项目使用H2内存数据库，@Override
public void addCorsMappings(CorsRegistry registry) {
    registry.addMapping("/**")
            .allowedOriginPatterns("*")  // 这里是修改的部分
            .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
            .allowedHeaders("*").allowCredentials(true);
}@Override
public void addCorsMappings(CorsRegistry registry) {
    registry.addMapping("/**")
            .allowedOriginPatterns("*")  // 这里是修改的部分
            .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
            .allowedHeaders("*").allowCredentials(true);
}@Override
public void addCorsMappings(CorsRegistry registry) {
    registry.addMapping("/**")
            .allowedOriginPatterns("*")  // 这里是修改的部分
            .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
            .allowedHeaders("*").allowCredentials(true);
}@Override
public void addCorsMappings(CorsRegistry registry) {
    registry.addMapping("/**")
            .allowedOriginPatterns("*")  // 这里是修改的部分
            .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
            .allowedHeaders("*").allowCredentials(true);
}@Override
public void addCorsMappings(CorsRegistry registry) {
    registry.addMapping("/**")
            .allowedOriginPatterns("*")  // 这里是修改的部分
            .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
            .allowedHeaders("*").allowCredentials(true);
}@Override
public void addCorsMappings(CorsRegistry registry) {
    registry.addMapping("/**")
            .allowedOriginPatterns("*")  // 这里是修改的部分
            .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
            .allowedHeaders("*").allowCredentials(true);
}重启应用程序后数据会丢失
- 生产环境需要使用MySQL数据库，并配置正确的数据库连接信息
- JWT密钥在 `application.properties` 文件中配置，生产环境需要使用强密钥

## 联系方式

如有问题，请联系项目维护人员。
