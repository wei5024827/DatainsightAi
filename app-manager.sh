#!/bin/bash

# DataInsight AI 应用管理脚本
# 用法: ./app-manager.sh [start|stop|status|restart]

# 获取当前脚本的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 配置参数
APP_NAME="DataInsight AI"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
BACKEND_PORT=8000
FRONTEND_PORT=5173
BACKEND_PID_FILE="$SCRIPT_DIR/work/backend.pid"
FRONTEND_PID_FILE="$SCRIPT_DIR/work/frontend.pid"
LOG_DIR="$SCRIPT_DIR/log"
LOG_FILE="$LOG_DIR/app.log"

# 确保日志目录存在
mkdir -p "$LOG_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}


# 安全的端口清理函数
kill_port_if_occupied() {
    local port=$1
    local service_name=$2
    
    local pids=$(lsof -ti:$port)
    if [ -n "$pids" ]; then
        log "找到占用${service_name}端口 ${port} 的进程: $pids"
        kill -9 $pids
        success "已杀掉占用端口 ${port} 的进程"
    # else
    #     log "${service_name}端口 ${port} 未被占用"
    fi
}

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0 # 端口被占用
    else
        return 1 # 端口空闲
    fi
}

# 检查进程是否运行
check_process() {
    local pid_file=$1
    local process_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            return 0 # 进程正在运行
        else
            rm -f "$pid_file" # 清理无效的pid文件
            return 1 # 进程不存在
        fi
    else
        return 1 # pid文件不存在
    fi
}

# 启动后端服务
start_backend() {
    log "启动后端服务..."
    
    if check_port $BACKEND_PORT; then
        error "端口 $BACKEND_PORT 已被占用，后端服务启动失败"
        return 1
    fi
    
    if check_process "$BACKEND_PID_FILE" "backend"; then
        warning "后端服务已经在运行 (PID: $(cat $BACKEND_PID_FILE))"
        return 0
    fi
    
    cd "$BACKEND_DIR"
    
    # 激活虚拟环境
    if [ -f "../.venv/bin/activate" ]; then
        source ../.venv/bin/activate
    elif [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    fi
    
    # 启动后端服务，日志输出到log目录
    nohup uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload > "$LOG_DIR/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$BACKEND_PID_FILE"
    
    cd "$SCRIPT_DIR"
    
    # 等待服务启动
    sleep 3
    if check_port $BACKEND_PORT; then
        success "后端服务启动成功 (PID: $BACKEND_PID, 端口: $BACKEND_PORT)"
        return 0
    else
        error "后端服务启动失败，请检查日志文件: $LOG_DIR/backend.log"
        return 1
    fi
}

# 启动前端服务
start_frontend() {
    log "启动前端服务..."
    
    if check_port $FRONTEND_PORT; then
        error "端口 $FRONTEND_PORT 已被占用，前端服务启动失败"
        return 1
    fi
    
    if check_process "$FRONTEND_PID_FILE" "frontend"; then
        warning "前端服务已经在运行 (PID: $(cat $FRONTEND_PID_FILE))"
        return 0
    fi
    
    cd "$FRONTEND_DIR"
    
    # 启动前端服务，日志输出到log目录
    nohup pnpm dev --host > "$LOG_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$FRONTEND_PID_FILE"
    
    cd "$SCRIPT_DIR"
    
    # 等待服务启动
    sleep 5
    if check_port $FRONTEND_PORT; then
        success "前端服务启动成功 (PID: $FRONTEND_PID, 端口: $FRONTEND_PORT)"
        return 0
    else
        error "前端服务启动失败，请检查日志文件: $LOG_DIR/frontend.log"
        return 1
    fi
}

# 停止服务
stop_service() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            log "停止 $service_name 服务 (PID: $pid)..."
            kill $pid
            sleep 2
            if ps -p $pid > /dev/null 2>&1; then
                warning "$service_name 服务未正常停止，强制终止..."
                kill -9 $pid
            fi
            rm -f "$pid_file"
            success "$service_name 服务已停止"
        else
            warning "$service_name 服务未运行，清理无效的PID文件"
            rm -f "$pid_file"
        fi
    else
        warning "$service_name 服务未运行 (PID文件不存在)"
    fi

    # 最后释放端口上的进程
    kill_port_if_occupied 5173 "前端"
    kill_port_if_occupied 8000 "后端"
}

# 启动所有服务
start_all() {
    log "开始启动 $APP_NAME..."
    
    # 检查必要的依赖
    if [ ! -d "$BACKEND_DIR" ]; then
        error "后端目录不存在: $BACKEND_DIR"
        return 1
    fi
    
    if [ ! -d "$FRONTEND_DIR" ]; then
        error "前端目录不存在: $FRONTEND_DIR"
        return 1
    fi
    
    # 启动后端
    if ! start_backend; then
        error "后端服务启动失败，停止启动流程"
        return 1
    fi
    
    # 启动前端
    if ! start_frontend; then
        error "前端服务启动失败，停止后端服务"
        stop_service "$BACKEND_PID_FILE" "后端"
        return 1
    fi
    
    success "$APP_NAME 启动完成!"
    echo ""
    echo "访问地址:"
    echo "前端: http://ai:$FRONTEND_PORT"
    echo "后端API: http://ai:$BACKEND_PORT"
    echo "后端文档: http://ai:$BACKEND_PORT/docs"
    echo ""
    echo "日志文件:"
    echo "后端日志: $LOG_DIR/backend.log"
    echo "前端日志: $LOG_DIR/frontend.log"
    echo "管理脚本日志: $LOG_FILE"
}

# 停止所有服务
stop_all() {
    log "开始停止 $APP_NAME..."
    
    stop_service "$FRONTEND_PID_FILE" "前端"
    stop_service "$BACKEND_PID_FILE" "后端"
    
    success "$APP_NAME 已停止"
}

# 查看服务状态
status_all() {
    echo -e "${BLUE}$APP_NAME 服务状态${NC}"
    echo "========================================"
    
    # 检查后端状态
    backend_running=false
    frontend_running=false
    
    if check_process "$BACKEND_PID_FILE" "后端"; then
        local backend_pid=$(cat "$BACKEND_PID_FILE")
        if check_port $BACKEND_PORT; then
            echo -e "后端服务: ${GREEN}运行中${NC} (PID: $backend_pid, 端口: $BACKEND_PORT)"
            backend_running=true
        else
            echo -e "后端服务: ${YELLOW}异常${NC} (进程存在但端口未监听)"
        fi
    else
        echo -e "后端服务: ${RED}未运行${NC}"
    fi
    
    # 检查前端状态
    if check_process "$FRONTEND_PID_FILE" "前端"; then
        local frontend_pid=$(cat "$FRONTEND_PID_FILE")
        if check_port $FRONTEND_PORT; then
            echo -e "前端服务: ${GREEN}运行中${NC} (PID: $frontend_pid, 端口: $FRONTEND_PORT)"
            frontend_running=true
        else
            echo -e "前端服务: ${YELLOW}异常${NC} (进程存在但端口未监听)"
        fi
    else
        echo -e "前端服务: ${RED}未运行${NC}"
    fi
    
    echo "========================================"
    
    # 显示访问信息 - 只有当服务确实由本脚本启动时才显示
    if [ "$backend_running" = true ] && [ "$frontend_running" = true ]; then
        echo -e "${GREEN}服务正常运行，可以访问:${NC}"
        echo "前端: http://localhost:$FRONTEND_PORT"
        echo "后端API: http://localhost:$BACKEND_PORT"
    elif check_port $BACKEND_PORT || check_port $FRONTEND_PORT; then
        echo -e "${YELLOW}警告: 端口被占用，但可能不是本应用的服务${NC}"
        echo "请检查是否有其他进程占用了这些端口:"
        if check_port $BACKEND_PORT; then
            echo "端口 $BACKEND_PORT 被占用，使用命令查看: lsof -i :$BACKEND_PORT"
        fi
        if check_port $FRONTEND_PORT; then
            echo "端口 $FRONTEND_PORT 被占用，使用命令查看: lsof -i :$FRONTEND_PORT"
        fi
    fi
}

# 重启服务
restart_all() {
    log "重启 $APP_NAME..."
    stop_all
    sleep 2
    start_all
}

# 显示帮助信息
show_help() {
    echo "用法: $0 {start|stop|status|restart|help}"
    echo ""
    echo "命令说明:"
    echo "  start    - 启动所有服务（后端 + 前端）"
    echo "  stop     - 停止所有服务"
    echo "  status   - 查看服务状态"
    echo "  restart  - 重启所有服务"
    echo "  help     - 显示此帮助信息"
    echo ""
    echo "配置信息:"
    echo "  后端端口: $BACKEND_PORT"
    echo "  前端端口: $FRONTEND_PORT"
    echo "  后端目录: $BACKEND_DIR"
    echo "  前端目录: $FRONTEND_DIR"
}

# 主函数
main() {
    case "$1" in
        start)
            start_all
            ;;
        stop)
            stop_all
            ;;
        status)
            status_all
            ;;
        restart)
            restart_all
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo "错误: 未知命令 '$1'"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 检查参数
if [ $# -eq 0 ]; then
    echo "错误: 需要指定命令"
    echo ""
    show_help
    exit 1
fi

# 执行主函数
main "$1"