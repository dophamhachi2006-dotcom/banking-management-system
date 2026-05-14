#!/usr/bin/env bash
# ============================================================
#  Banking Management System – One-click starter
#  Chạy: ./start.sh
#  Yêu cầu: Docker Desktop đang chạy
# ============================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${CYAN}[•]${NC} $*"; }
success() { echo -e "${GREEN}[✓]${NC} $*"; }
warn()    { echo -e "${YELLOW}[!]${NC} $*"; }
error()   { echo -e "${RED}[✗]${NC} $*"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BOLD}${CYAN}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║     Emerald Bank – Docker Launcher       ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${NC}"

# ── 1. Kiểm tra Docker ──────────────────────────────────────
info "Kiểm tra Docker..."
command -v docker &>/dev/null || error "Docker chưa được cài. Tải tại: https://docs.docker.com/get-docker/"
docker info &>/dev/null       || error "Docker Desktop chưa chạy. Hãy mở Docker Desktop trước."

if docker compose version &>/dev/null 2>&1; then
  DC="docker compose"
elif command -v docker-compose &>/dev/null; then
  DC="docker-compose"
else
  error "Không tìm thấy Docker Compose."
fi
success "Docker OK – dùng: $DC"

# ── 2. Kiểm tra file cần thiết ──────────────────────────────
info "Kiểm tra file project..."
[[ -f "docker-compose.yml" ]]       || error "Không tìm thấy docker-compose.yml"
[[ -f "database/00_init_all.sql" ]] || error "Không tìm thấy database/00_init_all.sql"
[[ -f "Dockerfile.backend" ]]       || error "Không tìm thấy Dockerfile.backend"
[[ -f "Dockerfile.frontend" ]]      || error "Không tìm thấy Dockerfile.frontend"
[[ -f "docker-entrypoint.sh" ]]     || error "Không tìm thấy docker-entrypoint.sh"
success "Tất cả file đã đủ."

# ── 3. Tạo .env nếu chưa có ────────────────────────────────
if [[ ! -f .env ]]; then
  cp .env.example .env
  warn ".env được tạo từ .env.example"
else
  success ".env đã tồn tại."
fi

# ── 4. Dừng container cũ ────────────────────────────────────
info "Dừng container cũ (nếu có)..."
$DC down --remove-orphans 2>/dev/null || true

# ── 5. Hỏi có muốn xóa data cũ không ───────────────────────
echo ""
echo -e "  ${YELLOW}Bạn có muốn xóa dữ liệu DB cũ và bắt đầu lại từ đầu?${NC}"
echo "  (Chọn 'y' nếu lần đầu chạy hoặc muốn reset sạch)"
read -rp "  Xóa data cũ? [y/N]: " RESET_DATA
if [[ "${RESET_DATA,,}" == "y" ]]; then
  info "Xóa volume MySQL cũ..."
  $DC down -v 2>/dev/null || true
  success "Đã xóa data cũ."
fi
echo ""

# ── 6. Build & khởi động ────────────────────────────────────
info "Build images (lần đầu có thể mất 3-5 phút)..."
$DC build --parallel
success "Build xong!"

info "Khởi động tất cả services..."
$DC up -d

# ── 7. Chờ MySQL healthy ────────────────────────────────────
info "Chờ MySQL khởi động (tối đa 120s)..."
elapsed=0
until $DC ps mysql 2>/dev/null | grep -q "healthy"; do
  if (( elapsed >= 120 )); then
    error "MySQL không khởi động được sau 120s. Chạy '$DC logs mysql' để xem lỗi."
  fi
  sleep 3; elapsed=$((elapsed+3)); echo -n "."
done
echo ""; success "MySQL sẵn sàng!"

# ── 8. Chờ Backend API ─────────────────────────────────────
info "Chờ Backend API (tối đa 90s)..."
elapsed=0
until curl -sf http://localhost:5000/api/health &>/dev/null; do
  if (( elapsed >= 90 )); then
    warn "Backend chưa phản hồi. Xem logs: $DC logs backend"
    break
  fi
  sleep 3; elapsed=$((elapsed+3)); echo -n "."
done
echo ""; success "Backend API sẵn sàng!"

# ── 9. Chờ Frontend ────────────────────────────────────────
info "Chờ Frontend (tối đa 60s)..."
elapsed=0
until curl -sf http://localhost:5173 &>/dev/null; do
  if (( elapsed >= 60 )); then
    warn "Frontend chưa phản hồi. Xem logs: $DC logs frontend"
    break
  fi
  sleep 3; elapsed=$((elapsed+3)); echo -n "."
done
echo ""; success "Frontend sẵn sàng!"

# ── 10. Tổng kết ───────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════════════╗"
echo -e "║       ✅  Hệ thống đã khởi động thành công!     ║"
echo -e "╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  🌐  Mở trình duyệt: ${CYAN}http://localhost:5173${NC}"
echo ""
echo -e "  ${BOLD}Đăng nhập:${NC}"
echo -e "    👤 admin   / admin123    (Quản trị viên)"
echo -e "    👤 teller1 / teller123  (Giao dịch viên)"
echo -e "    👤 audit1  / audit123   (Kiểm toán)"
echo ""
echo -e "  ${BOLD}Lệnh hữu ích:${NC}"
echo -e "    Xem logs   : ${CYAN}$DC logs -f${NC}"
echo -e "    Dừng       : ${CYAN}$DC down${NC}"
echo -e "    Reset sạch : ${CYAN}$DC down -v${NC} rồi chạy lại ${CYAN}./start.sh${NC}"
echo ""
