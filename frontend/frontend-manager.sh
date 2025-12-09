#!/bin/bash

# 仅管理前端服务的启动/停止脚本
# 用法: ./frontend-manager.sh {start|stop|status|restart|help}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="DataInsight Frontend"
FRONTEND_DIR="$SCRIPT_DIR"
FRONTEND_PORT=5174
PID_FILE="$SCRIPT_DIR/../work/frontend.pid"
LOG_DIR="$SCRIPT_DIR/../log"
LOG_FILE="$LOG_DIR/frontend.log"

mkdir -p "$LOG_DIR" "$SCRIPT_DIR/../work"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

check_process() {
    if [ -f "$PID_FILE" ]; then
        local pid
        pid=$(cat "$PID_FILE")
        if ps -p $pid >/dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
        fi
    fi
    return 1
}

start_frontend() {
    log "启动前端服务..."

    if check_port $FRONTEND_PORT; then
        error "端口 $FRONTEND_PORT 已被占用，前端服务启动失败"
        return 1
    fi

    if check_process; then
        warning "前端服务已经在运行 (PID: $(cat $PID_FILE))"
        return 0
    fi

    cd "$FRONTEND_DIR" || exit 1

    # 如有需要可在此添加前端依赖检查
    nohup pnpm dev --host 0.0.0.0 --port $FRONTEND_PORT > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"

    sleep 3
    if check_port $FRONTEND_PORT; then
        success "前端服务启动成功 (PID: $(cat $PID_FILE), 端口: $FRONTEND_PORT)"
        return 0
    else
        error "前端服务启动失败，请检查日志文件: $LOG_FILE"
        return 1
    fi
}

stop_frontend() {
    if check_process; then
        local pid
        pid=$(cat "$PID_FILE")
        log "停止前端服务 (PID: $pid)..."
        kill $pid 2>/dev/null
        sleep 2
        if ps -p $pid >/dev/null 2>&1; then
            warning "前端服务未正常停止，强制终止..."
            kill -9 $pid 2>/dev/null
        fi
        rm -f "$PID_FILE"
        success "前端服务已停止"
    else
        warning "前端服务未运行"
    fi

    local pids
    pids=$(lsof -ti:$FRONTEND_PORT)
    if [ -n "$pids" ]; then
        log "清理占用端口 $FRONTEND_PORT 的进程: $pids"
        kill -9 $pids 2>/dev/null
    fi
}

status_frontend() {
    echo -e "${BLUE}$APP_NAME 状态${NC}"
    echo "========================================"

    if check_process && check_port $FRONTEND_PORT; then
        echo -e "前端服务: ${GREEN}运行中${NC} (PID: $(cat $PID_FILE), 端口: $FRONTEND_PORT)"
    elif check_port $FRONTEND_PORT; then
        echo -e "前端服务: ${YELLOW}端口被占用${NC} (但 PID 文件不存在，可能是其他进程)"
    else
        echo -e "前端服务: ${RED}未运行${NC}"
    fi
}

show_help() {
    echo "用法: $0 {start|stop|status|restart|help}"
}

main() {
    case "$1" in
        start)
            start_frontend
            ;;
        stop)
            stop_frontend
            ;;
        status)
            status_frontend
            ;;
        restart)
            stop_frontend
            sleep 1
            start_frontend
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

if [ $# -eq 0 ]; then
    show_help
    exit 1
fi

main "$1"
