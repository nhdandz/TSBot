import { Link } from 'react-router-dom'
import { Shield } from 'lucide-react'

const quickLinks = [
  { href: '/', label: 'Trang chủ' },
  { href: '/gioi-thieu', label: 'Giới thiệu' },
  { href: '/cau-hoi-thuong-gap', label: 'FAQ' },
  { href: '/lien-he', label: 'Liên hệ' },
  { href: '/chat', label: 'Trò chuyện' },
]

export default function Footer() {
  return (
    <footer className="bg-sidebar text-sidebar-foreground">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* About */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-xl bg-gradient-military flex items-center justify-center">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <span className="text-lg font-bold tracking-tighter text-white">
                TSBot
              </span>
            </div>
            <p className="text-sm text-sidebar-foreground/80 leading-relaxed">
              Trợ lý AI tư vấn tuyển sinh quân đội, cung cấp thông tin chính xác
              về các trường quân đội tại Việt Nam.
            </p>
          </div>

          {/* Quick links */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-white uppercase tracking-wider">
              Liên kết nhanh
            </h3>
            <ul className="space-y-2">
              {quickLinks.map((link) => (
                <li key={link.href}>
                  <Link
                    to={link.href}
                    className="text-sm text-sidebar-foreground/80 hover:text-white transition-colors duration-200"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact info */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-white uppercase tracking-wider">
              Thông tin liên hệ
            </h3>
            <ul className="space-y-2 text-sm text-sidebar-foreground/80">
              <li>Email: tsbot.support@gmail.com</li>
              <li>Hỗ trợ: 24/7 qua chatbot</li>
              <li>Địa chỉ: Việt Nam</li>
            </ul>
          </div>
        </div>

        {/* Bottom */}
        <div className="mt-10 pt-6 border-t border-sidebar-border">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
            <p className="text-xs text-sidebar-foreground/60">
              &copy; {new Date().getFullYear()} TSBot. All rights reserved.
            </p>
            <p className="text-xs text-sidebar-foreground/60 text-center">
              Thông tin mang tính chất tham khảo. Vui lòng kiểm tra lại với nguồn
              chính thức trước khi đưa ra quyết định.
            </p>
          </div>
        </div>
      </div>
    </footer>
  )
}
