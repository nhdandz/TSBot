# TSBot Frontend - Hệ thống Tư vấn Tuyển sinh Quân đội

Frontend application cho chatbot AI tư vấn tuyển sinh quân sự Việt Nam.

## 🚀 Tính năng

### Giao diện Công khai (Chat Interface)
- 💬 Chat realtime với AI chatbot
- 📚 Hiển thị nguồn tham khảo từ tài liệu pháp luật
- 🔄 Lưu lịch sử hội thoại
- ⚡ Phản hồi nhanh với typing indicator
- 📱 Responsive design cho mobile và desktop

### Giao diện Admin
- 🏫 **Quản lý Trường**: CRUD operations cho danh sách trường quân đội
- 🎓 **Quản lý Ngành**: Quản lý các ngành đào tạo
- 📊 **Quản lý Điểm chuẩn**: Import/export và quản lý điểm chuẩn theo năm
- 📈 **Dashboard**: Thống kê và analytics hệ thống
- 🔐 **Authentication**: Đăng nhập bảo mật cho admin

## 🛠 Tech Stack

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS + Radix UI
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **Routing**: React Router v6
- **Form Handling**: React Hook Form + Zod
- **Icons**: Lucide React

## 📋 Yêu cầu hệ thống

- Node.js >= 18.x
- npm hoặc yarn
- Backend API đang chạy tại `http://localhost:8000`

## 🔧 Cài đặt

### 1. Clone repository (nếu chưa có)
```bash
git clone <repository-url>
cd TSBot/frontend
```

### 2. Cài đặt dependencies
```bash
npm install
```

### 3. Cấu hình môi trường
Tạo file `.env` từ `.env.example`:
```bash
cp .env.example .env
```

Chỉnh sửa `.env` nếu cần:
```env
# API Configuration
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# Environment
VITE_ENV=development
```

### 4. Chạy development server
```bash
npm run dev
```

Frontend sẽ chạy tại: http://localhost:3000

## 📦 Build cho production

```bash
npm run build
```

Build output sẽ nằm trong thư mục `dist/`

### Preview production build
```bash
npm run preview
```

## 🎨 Design System

Dự án sử dụng design system tùy chỉnh với:
- **Color Palette**:
  - Primary (Blue) - Niềm tin và uy tín
  - Military (Green) - Sức mạnh quân đội
  - Semantic colors - Success, Warning, Error
- **Typography**: Inter font family
- **Spacing**: Linear scale (4px base)
- **Components**: Radix UI primitives

Design tokens được định nghĩa trong `.ui-design/` folder.

## 📁 Cấu trúc thư mục

```
frontend/
├── .ui-design/              # Design system tokens
│   ├── design-system.json
│   └── tokens/
│       ├── tokens.css
│       └── tokens.ts
├── src/
│   ├── components/          # React components
│   │   ├── chat/           # Chat components
│   │   ├── layout/         # Layout components
│   │   └── ui/             # UI primitives (Radix UI)
│   ├── hooks/              # Custom React hooks
│   ├── lib/                # Utilities & config
│   │   ├── api.ts          # API client
│   │   ├── config.ts       # App configuration
│   │   └── utils.ts        # Utility functions
│   ├── pages/              # Page components
│   │   ├── admin/          # Admin pages
│   │   └── ChatPage.tsx    # Public chat page
│   ├── services/           # API services
│   │   ├── chatService.ts
│   │   └── adminService.ts
│   ├── stores/             # Zustand stores
│   │   ├── authStore.ts
│   │   ├── chatStore.ts
│   │   └── adminStore.ts
│   ├── styles/             # Global styles
│   ├── types/              # TypeScript types
│   ├── App.tsx             # Main app component
│   └── main.tsx            # Entry point
├── public/                 # Static assets
├── .env.example            # Environment variables template
├── package.json
├── tailwind.config.js
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## 🔌 API Integration

Frontend kết nối với Backend qua các endpoints:

### Public APIs
- `POST /api/v1/chat` - Gửi tin nhắn chat
- `POST /api/v1/feedback` - Gửi feedback
- `GET /api/v1/history/{session_id}` - Lấy lịch sử chat
- `WebSocket /api/v1/ws/{session_id}` - Real-time chat

### Admin APIs
- `POST /api/v1/admin/login` - Đăng nhập admin
- `GET/POST/PUT/DELETE /api/v1/admin/truong` - Quản lý trường
- `GET/POST/PUT/DELETE /api/v1/admin/nganh` - Quản lý ngành
- `GET/POST/PUT/DELETE /api/v1/admin/diem-chuan` - Quản lý điểm chuẩn
- `GET /api/v1/admin/stats` - Thống kê dashboard

## 👤 Tài khoản Admin mặc định

```
Username: admin
Password: admin123
```

**⚠️ Lưu ý**: Đổi mật khẩu trong môi trường production!

## 🧪 Development

### Linting
```bash
npm run lint
```

### Type checking
```bash
npx tsc --noEmit
```

## 🚀 Deployment

### Deploy với Docker
Backend repository có sẵn `docker-compose.yml` để deploy full stack.

### Deploy riêng Frontend
1. Build production:
```bash
npm run build
```

2. Deploy folder `dist/` lên hosting (Vercel, Netlify, etc.)

3. Cấu hình environment variables trên hosting platform

## 🐛 Troubleshooting

### CORS errors
- Kiểm tra Backend có bật CORS cho domain của Frontend
- Kiểm tra `VITE_API_URL` trong `.env`

### API connection failed
- Đảm bảo Backend đang chạy tại port 8000
- Kiểm tra network và firewall

### Build errors
```bash
rm -rf node_modules package-lock.json
npm install
npm run build
```

## 📝 Contributing

1. Tạo feature branch từ `main`
2. Commit changes với conventional commits
3. Tạo Pull Request
4. Đợi review và merge

## 📄 License

Copyright © 2026 TSBot Team. All rights reserved.

## 📞 Liên hệ

- Project Lead: AI Team
- Email: support@tsbot.vn
- Documentation: https://docs.tsbot.vn

---

**Built with ❤️ for Vietnamese Military Recruitment**
