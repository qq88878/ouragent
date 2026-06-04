#!/bin/bash

# ============================================================
# Docker部署脚本
# 用法: ./docker-deploy.sh [dev|prod|stop|restart|logs|status]
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker未安装，请先安装Docker"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi

    print_success "Docker和Docker Compose已安装"
}

# 检查.env文件
check_env() {
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            print_warning ".env文件不存在，正在从.env.example创建..."
            cp .env.example .env
            print_warning "请编辑.env文件配置您的环境变量"
        else
            print_error ".env.example文件不存在"
            exit 1
        fi
    fi
    print_success ".env文件已就绪"
}

# 开发环境启动
start_dev() {
    print_info "启动开发环境..."
    check_env

    # 构建并启动服务
    docker-compose up -d --build

    print_success "开发环境启动完成！"
    print_info "服务访问地址："
    echo "  - Java后端: http://localhost:9000"
    echo "  - Python Agent: http://localhost:8000"
    echo "  - Nginx代理: http://localhost:80"
    echo "  - MySQL: localhost:3306"
    echo "  - PostgreSQL: localhost:5432"
    echo "  - Redis: localhost:6379"
}

# 生产环境启动
start_prod() {
    print_info "启动生产环境..."
    check_env

    # 使用生产配置启动
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

    print_success "生产环境启动完成！"
    print_info "服务访问地址："
    echo "  - Nginx代理: http://localhost:80"
    echo "  - Java后端: http://localhost:9000 (内部)"
    echo "  - Python Agent: http://localhost:8000 (内部)"
}

# 停止服务
stop_services() {
    print_info "停止所有服务..."
    docker-compose down
    print_success "所有服务已停止"
}

# 重启服务
restart_services() {
    print_info "重启所有服务..."
    docker-compose restart
    print_success "所有服务已重启"
}

# 查看日志
view_logs() {
    print_info "查看服务日志..."
    docker-compose logs -f
}

# 查看状态
view_status() {
    print_info "查看服务状态..."
    docker-compose ps
}

# 清理资源
cleanup() {
    print_warning "清理Docker资源..."
    read -p "确认清理所有未使用的Docker资源？(y/N): " confirm
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        docker system prune -af
        print_success "清理完成"
    else
        print_info "取消清理"
    fi
}

# 显示帮助
show_help() {
    echo "Docker部署脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  dev        启动开发环境"
    echo "  prod       启动生产环境"
    echo "  stop       停止所有服务"
    echo "  restart    重启所有服务"
    echo "  logs       查看服务日志"
    echo "  status     查看服务状态"
    echo "  cleanup    清理Docker资源"
    echo "  help       显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 dev      # 启动开发环境"
    echo "  $0 prod     # 启动生产环境"
    echo "  $0 stop     # 停止所有服务"
}

# 主函数
main() {
    # 检查Docker
    check_docker

    # 解析命令
    case "${1:-help}" in
        dev)
            start_dev
            ;;
        prod)
            start_prod
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        logs)
            view_logs
            ;;
        status)
            view_status
            ;;
        cleanup)
            cleanup
            ;;
        help|*)
            show_help
            ;;
    esac
}

# 执行主函数
main "$@"
