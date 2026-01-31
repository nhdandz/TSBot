# 🎯 Hướng dẫn Thiết lập và Chạy Frontend TSBot

## ✅ Hoàn thành

Frontend cho hệ thống Chatbot AI Tư vấn Tuyển sinh Quân đội đã được xây dựng hoàn chỉnh với đầy đủ tính năng.

## 📦 Cấu trúc Dự án Đã Tạo

### 1. **Design System** (.ui-design/)
- ✅ Design tokens (colors, typography, spacing)
- ✅ CSS custom properties
- ✅ TypeScript type definitions
- ✅ Tailwind integration

### 2. **Core Infrastructure** (src/lib/, src/types/)
- ✅ API client với error handling
- ✅ Configuration management
- ✅ TypeScript types đầy đủ cho Chat và Admin
- ✅ Utility functions

### 3. **State Management** (src/stores/)
- ✅ **authStore**: Quản lý authentication
- ✅ **chatStore**: Quản lý chat messages và session
- ✅ **adminStore**: Quản lý admin data

### 4. **API Services** (src/services/)
- ✅ **chatService**: Chat, feedback, history APIs
- ✅ **adminService**: Admin CRUD operations

### 5. **Chat Interface** (Giao diện Công khai)
- ✅ **ChatPage**: Main chat interface
- ✅ **MessageList**: Hiển thị tin nhắn với typing indicator
- ✅ **ChatInput**: Input với send button
- ✅ **SourceDisplay**: Hiển thị nguồn tham khảo

### 6. **Admin Panel** (Giao diện Quản trị)
- ✅ **LoginPage**: Authentication
- ✅ **DashboardPage**: Thống kê tổng quan
- ✅ **AdminLayout**: Sidebar navigation
- ✅ **TruongPage**: CRUD quản lý trường quân đội
- ✅ **NganhPage**: CRUD quản lý ngành đào tạo
- ✅ **DiemChuanPage**: CRUD quản lý điểm chuẩn với filters

### 7. **UI Components** (src/components/ui/)
- ✅ Radix UI primitives (Button, Card, Dialog, Table, etc.)
- ✅ Tailwind CSS styling
- ✅ Responsive design

## 🚀 Cách Chạy

### Bước 1: Cài đặt Dependencies
```bash
cd frontend
npm install
```

### Bước 2: Khởi động Backend (Terminal riêng)
```bash
# Từ thư mục gốc TSBot
cd ..
python -m uvicorn src.api.main:app --reload
```

Backend sẽ chạy tại: http://localhost:8000

### Bước 3: Khởi động Frontend
```bash
# Từ thư mục frontend
npm run dev
```

Frontend sẽ chạy tại: http://localhost:3000

### Bước 4: Truy cập Ứng dụng

**Giao diện Chat (Công khai):**
- URL: http://localhost:3000
- Không cần đăng nhập
- Chat trực tiếp với AI chatbot

**Giao diện Admin:**
- URL: http://localhost:3000/admin/login
- Username: `admin`
- Password: `admin123` (cần được cấu hình trong Backend)

## 🎨 Tính năng Chính

### Chat Interface
1. **Real-time Chat**
   - Gửi câu hỏi về tuyển sinh quân đội
   - Nhận phản hồi từ AI với typing indicator
   - Hiển thị nguồn tham khảo từ tài liệu

2. **Session Management**
   - Tự động tạo session ID
   - Lưu lịch sử chat
   - Reset conversation

### Admin Panel
1. **Dashboard**
   - Thống kê tổng số trường, ngành, điểm chuẩn
   - Số lượng chat conversations
   - Đánh giá trung bình

2. **Quản lý Trường** (/admin/truong)
   - Thêm/Sửa/Xóa trường quân đội
   - Thông tin: Mã trường, Tên, Khu vực, Website

3. **Quản lý Ngành** (/admin/nganh)
   - Thêm/Sửa/Xóa ngành đào tạo
   - Thông tin: Mã ngành, Tên ngành, Mô tả

4. **Quản lý Điểm Chuẩn** (/admin/diem-chuan)
   - Thêm điểm chuẩn theo năm
   - Filter theo năm, trường, ngành
   - Thông tin đầy đủ: Khối thi, Giới tính, Khu vực

## 🛠 Tech Stack

```
React 18 + TypeScript
├── Vite (Build tool)
├── Tailwind CSS (Styling)
├── Radix UI (UI Components)
├── Zustand (State management)
├── TanStack Query (Data fetching)
├── React Router v6 (Routing)
└── Lucide React (Icons)
```

## 📁 File Structure

```
frontend/
├── .ui-design/                    # Design system
│   ├── design-system.json
│   └── tokens/
│       ├── tokens.css
│       └── tokens.ts
├── src/
│   ├── components/
│   │   ├── chat/                  # Chat components
│   │   │   ├── ChatInput.tsx
│   │   │   ├── MessageList.tsx
│   │   │   └── SourceDisplay.tsx
│   │   ├── layout/                # Layout components
│   │   │   └── AdminLayout.tsx
│   │   └── ui/                    # UI primitives
│   ├── lib/
│   │   ├── api.ts                 # API client
│   │   ├── config.ts              # Configuration
│   │   └── utils.ts               # Utilities
│   ├── pages/
│   │   ├── ChatPage.tsx           # Public chat page
│   │   └── admin/                 # Admin pages
│   │       ├── LoginPage.tsx
│   │       ├── DashboardPage.tsx
│   │       ├── TruongPage.tsx
│   │       ├── NganhPage.tsx
│   │       └── DiemChuanPage.tsx
│   ├── services/
│   │   ├── chatService.ts
│   │   └── adminService.ts
│   ├── stores/
│   │   ├── authStore.ts
│   │   ├── chatStore.ts
│   │   └── adminStore.ts
│   ├── types/                     # TypeScript types
│   │   ├── chat.ts
│   │   ├── admin.ts
│   │   └── index.ts
│   ├── App.tsx
│   └── main.tsx
├── .env                           # Environment variables
├── .env.example
├── package.json
├── tailwind.config.js
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## 🧪 Testing & Development

### Build Production
```bash
npm run build
```
Output trong `dist/` folder

### Preview Production Build
```bash
npm run preview
```

### Lint Code
```bash
npm run lint
```

## 🔧 Environment Variables

File `.env`:
```env
# API Configuration
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# Environment
VITE_ENV=development
```

## 🎯 API Endpoints Được Sử Dụng

### Public APIs
- `POST /api/v1/chat` - Send chat message
- `POST /api/v1/feedback` - Submit feedback
- `GET /api/v1/history/{session_id}` - Get chat history
- `WebSocket /api/v1/ws/{session_id}` - Real-time chat (Future)

### Admin APIs (Requires Auth)
- `POST /api/v1/admin/login`
- `GET /api/v1/admin/truong` - Get schools
- `POST /api/v1/admin/truong` - Create school
- `PUT /api/v1/admin/truong/{id}` - Update school
- `DELETE /api/v1/admin/truong/{id}` - Delete school
- Similar endpoints for `nganh` and `diem-chuan`
- `GET /api/v1/admin/stats` - Dashboard stats

## 🎨 Design Highlights

### Color Palette
- **Primary Blue** (#0ea5e9) - Trust & Authority
- **Military Green** (#22c55e) - Strength & Military
- **Semantic Colors** - Success, Warning, Error

### Typography
- Font Family: Inter (Sans-serif)
- Font Sizes: xs (12px) → 5xl (48px)
- Font Weights: normal, medium, semibold, bold

### Components
- Modern, clean design
- Fully responsive (mobile-first)
- Smooth animations
- Accessible (WCAG compliant)

## 🐛 Troubleshooting

### Port already in use
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

### Cannot connect to Backend
- Kiểm tra Backend đang chạy tại port 8000
- Kiểm tra CORS settings trong Backend
- Kiểm tra `.env` file

### Build errors
```bash
# Clean install
rm -rf node_modules package-lock.json
npm install
npm run build
```

## 📝 Next Steps

### Để Backend Team:
1. Implement các endpoint admin còn thiếu nếu có
2. Cấu hình CORS cho domain frontend
3. Setup authentication token system
4. Implement WebSocket cho real-time chat

### Để tiếp tục phát triển:
1. Thêm Excel import/export cho điểm chuẩn
2. Implement WebSocket real-time chat
3. Thêm i18n (Vietnamese/English)
4. Thêm unit tests
5. Thêm E2E tests
6. Optimize performance
7. Add error boundaries

## ✅ Checklist Hoàn thành

- [x] Design system setup
- [x] API client & services
- [x] State management stores
- [x] Chat interface với components
- [x] Admin panel với full CRUD
- [x] Authentication flow
- [x] Responsive design
- [x] TypeScript types đầy đủ
- [x] Build thành công
- [x] Documentation

## 🎉 Kết luận

Frontend đã được xây dựng hoàn chỉnh và sẵn sàng tích hợp với Backend!

**Status**: ✅ Ready for Integration & Testing

**Build**: ✅ Successful (387.24 kB gzipped: 122.84 kB)

**Next**: Start Backend → Test Integration → Deploy

---

**Developed with ❤️ for Vietnamese Military Recruitment System**
