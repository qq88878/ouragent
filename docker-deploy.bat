@echo off
REM ============================================================
REM Docker部署脚本 (Windows)
REM 用法: docker-deploy.bat [dev|prod|stop|restart|logs|status]
REM ============================================================

setlocal enabledelayedexpansion

REM 检查Docker是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker未安装，请先安装Docker Desktop
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose未安装，请先安装Docker Compose
    exit /b 1
)

echo [SUCCESS] Docker和Docker Compose已安装

REM 检查.env文件
if not exist .env (
    if exist .env.example (
        echo [WARNING] .env文件不存在，正在从.env.example创建...
        copy .env.example .env
        echo [WARNING] 请编辑.env文件配置您的环境变量
    ) else (
        echo [ERROR] .env.example文件不存在
        exit /b 1
    )
)
echo [SUCCESS] .env文件已就绪

REM 解析命令
if "%1"=="" goto help
if "%1"=="dev" goto dev
if "%1"=="prod" goto prod
if "%1"=="stop" goto stop
if "%1"=="restart" goto restart
if "%1"=="logs" goto logs
if "%1"=="status" goto status
if "%1"=="cleanup" goto cleanup
if "%1"=="help" goto help
goto help

:dev
echo [INFO] 启动开发环境...
docker-compose up -d --build
echo [SUCCESS] 开发环境启动完成！
echo [INFO] 服务访问地址：
echo   - Java后端: http://localhost:9000
echo   - Python Agent: http://localhost:8000
echo   - Nginx代理: http://localhost:80
echo   - MySQL: localhost:3306
echo   - PostgreSQL: localhost:5432
echo   - Redis: localhost:6379
goto end

:prod
echo [INFO] 启动生产环境...
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
echo [SUCCESS] 生产环境启动完成！
echo [INFO] 服务访问地址：
echo   - Nginx代理: http://localhost:80
echo   - Java后端: http://localhost:9000 (内部)
echo   - Python Agent: http://localhost:8000 (内部)
goto end

:stop
echo [INFO] 停止所有服务...
docker-compose down
echo [SUCCESS] 所有服务已停止
goto end

:restart
echo [INFO] 重启所有服务...
docker-compose restart
echo [SUCCESS] 所有服务已重启
goto end

:logs
echo [INFO] 查看服务日志...
docker-compose logs -f
goto end

:status
echo [INFO] 查看服务状态...
docker-compose ps
goto end

:cleanup
echo [WARNING] 清理Docker资源...
set /p confirm="确认清理所有未使用的Docker资源？(y/N): "
if /i "!confirm!"=="y" (
    docker system prune -af
    echo [SUCCESS] 清理完成
) else (
    echo [INFO] 取消清理
)
goto end

:help
echo Docker部署脚本
echo.
echo 用法: %0 [命令]
echo.
echo 命令:
echo   dev        启动开发环境
echo   prod       启动生产环境
echo   stop       停止所有服务
echo   restart    重启所有服务
echo   logs       查看服务日志
echo   status     查看服务状态
echo   cleanup    清理Docker资源
echo   help       显示此帮助信息
echo.
echo 示例:
echo   %0 dev      # 启动开发环境
echo   %0 prod     # 启动生产环境
echo   %0 stop     # 停止所有服务
goto end

:end
endlocal
