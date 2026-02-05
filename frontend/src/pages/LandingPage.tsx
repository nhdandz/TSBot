import { useEffect, useState, useRef } from 'react'
import { motion, useInView } from 'framer-motion'
import { Link } from 'react-router-dom'
import {
  Bot,
  Search,
  GraduationCap,
  Zap,
  BarChart3,
  ShieldCheck,
  ArrowRight,
  Sparkles,
  MessageCircle,
  ChevronRight,
} from 'lucide-react'
import { ThemeToggle } from '@/components/ui/theme-toggle'

/* ───────────────────────── helpers ───────────────────────── */

const ease = [0.22, 1, 0.36, 1] as const

function Reveal({
  children,
  delay = 0,
  className = '',
}: {
  children: React.ReactNode
  delay?: number
  className?: string
}) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-80px' })
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 32 }}
      animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 32 }}
      transition={{ duration: 0.7, delay, ease }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

/* ────────────────────── bento card ──────────────────────── */

function BentoCard({
  icon: Icon,
  title,
  description,
  className = '',
}: {
  icon: React.ElementType
  title: string
  description: string
  className?: string
}) {
  return (
    <div
      className={`group relative rounded-2xl overflow-hidden ${className}`}
    >
      {/* gradient border */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-indigo-300/40 via-transparent to-purple-300/40 dark:from-indigo-500/[0.15] dark:via-transparent dark:to-purple-500/[0.15] p-px">
        <div className="h-full w-full rounded-2xl bg-white/80 dark:bg-[#0c0c14]/90 backdrop-blur-2xl" />
      </div>

      {/* content */}
      <div className="relative z-10 flex flex-col justify-between h-full p-7">
        <div>
          <div className="mb-5 inline-flex items-center justify-center w-11 h-11 rounded-xl bg-indigo-50 dark:bg-indigo-500/[0.08] border border-indigo-200/60 dark:border-indigo-500/[0.12] transition-colors group-hover:bg-indigo-100 dark:group-hover:bg-indigo-500/[0.14]">
            <Icon className="w-5 h-5 text-indigo-500 dark:text-indigo-400" />
          </div>
          <h3 className="text-[17px] font-semibold tracking-tight text-gray-900 dark:text-white/90 mb-2">
            {title}
          </h3>
          <p className="text-[14px] leading-relaxed text-gray-500 dark:text-white/40">
            {description}
          </p>
        </div>
      </div>

      {/* hover glow */}
      <div className="pointer-events-none absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-gradient-to-br from-indigo-500/[0.02] dark:from-indigo-500/[0.04] to-transparent" />
    </div>
  )
}

/* ────────────────────── features data ───────────────────── */

const features = [
  {
    icon: Bot,
    title: 'AI Tư Vấn Thông Minh',
    description:
      'Công nghệ AI tiên tiến tư vấn tuyển sinh chính xác, cá nhân hóa cho từng thí sinh.',
    className: 'md:col-span-2',
  },
  {
    icon: Search,
    title: 'Tra Cứu Điểm Chuẩn',
    description: 'Tra cứu nhanh điểm chuẩn các trường quân đội qua các năm.',
    className: '',
  },
  {
    icon: GraduationCap,
    title: 'Thông Tin Chi Tiết',
    description:
      'Cập nhật đầy đủ thông tin các trường, ngành đào tạo quân sự toàn quốc.',
    className: '',
  },
  {
    icon: Zap,
    title: 'Phản Hồi Tức Thì',
    description:
      'Nhận câu trả lời ngay lập tức, bất kể thời gian nào trong ngày.',
    className: 'md:col-span-2',
  },
  {
    icon: BarChart3,
    title: 'Dữ Liệu Chính Xác',
    description: 'Nguồn dữ liệu được xác minh từ các cơ quan tuyển sinh chính thức.',
    className: '',
  },
  {
    icon: ShieldCheck,
    title: 'An Toàn & Bảo Mật',
    description: 'Bảo mật thông tin cá nhân tuyệt đối cho mọi thí sinh.',
    className: '',
  },
  {
    icon: MessageCircle,
    title: 'Hỗ Trợ 24/7',
    description: 'Luôn sẵn sàng giải đáp mọi thắc mắc, mọi lúc mọi nơi.',
    className: '',
  },
]

/* ────────────────────── page ────────────────────────────── */

export default function LandingPage() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <div className="min-h-screen bg-[#fafafa] dark:bg-[#08080c] text-gray-900 dark:text-white noise-bg overflow-x-hidden transition-colors duration-300">
      {/* ─── ambient glows ─── */}
      <div className="pointer-events-none fixed inset-0">
        <div className="absolute top-[-20%] left-1/2 -translate-x-1/2 w-[900px] h-[600px] rounded-full bg-indigo-200/40 dark:bg-indigo-500/[0.07] blur-[140px] transition-colors duration-500" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] rounded-full bg-purple-200/20 dark:bg-purple-600/[0.05] blur-[120px] transition-colors duration-500" />
      </div>

      {/* ─── header ─── */}
      <header
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
          scrolled
            ? 'bg-white/70 dark:bg-[#08080c]/70 backdrop-blur-2xl border-b border-gray-200/80 dark:border-white/[0.06]'
            : 'bg-transparent'
        }`}
      >
        <div className="max-w-6xl mx-auto flex items-center justify-between px-6 h-16">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center">
              <Bot className="w-[18px] h-[18px] text-white" />
            </div>
            <span className="text-[15px] font-semibold tracking-tight text-gray-900 dark:text-white/90">
              TSBot
            </span>
          </Link>

          <nav className="hidden md:flex items-center gap-8">
            <a
              href="#features"
              className="text-[13px] font-medium text-gray-400 dark:text-white/40 hover:text-gray-700 dark:hover:text-white/80 transition-colors"
            >
              Tính năng
            </a>
            <a
              href="#about"
              className="text-[13px] font-medium text-gray-400 dark:text-white/40 hover:text-gray-700 dark:hover:text-white/80 transition-colors"
            >
              Giới thiệu
            </a>
            <ThemeToggle />
            <Link
              to="/chat"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-gray-100 dark:bg-white/[0.06] border border-gray-200 dark:border-white/[0.08] text-[13px] font-medium text-gray-600 dark:text-white/80 hover:bg-gray-200 dark:hover:bg-white/[0.1] hover:text-gray-900 dark:hover:text-white transition-all"
            >
              Bắt đầu chat
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </nav>

          {/* mobile nav */}
          <div className="flex md:hidden items-center gap-3">
            <ThemeToggle />
            <Link
              to="/chat"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-500 text-[13px] font-medium text-white"
            >
              Chat
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </header>

      {/* ─── hero ─── */}
      <section className="relative pt-44 pb-32 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease }}
          >
            <span className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-50 dark:bg-indigo-500/[0.08] border border-indigo-200/60 dark:border-indigo-500/[0.15] text-indigo-600 dark:text-indigo-400 text-[13px] font-medium">
              <Sparkles className="w-3.5 h-3.5" />
              Powered by AI
            </span>
          </motion.div>

          <motion.h1
            className="mt-8 text-[clamp(2.8rem,7vw,5.5rem)] font-extrabold tracking-tighter leading-[0.92]"
            initial={{ opacity: 0, y: 32 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1, ease }}
          >
            <span className="text-gray-900 dark:text-white">Tư vấn tuyển sinh</span>
            <br />
            <span className="bg-gradient-to-r from-indigo-500 via-indigo-600 to-purple-600 dark:from-indigo-400 dark:via-indigo-500 dark:to-purple-500 bg-clip-text text-transparent">
              Quân sự
            </span>
          </motion.h1>

          <motion.p
            className="mt-6 text-lg md:text-xl leading-relaxed text-gray-500 dark:text-white/40 max-w-xl mx-auto"
            initial={{ opacity: 0, y: 32 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2, ease }}
          >
            Chatbot AI hỗ trợ thí sinh tìm hiểu thông tin tuyển sinh
            các trường quân đội Việt Nam.
          </motion.p>

          <motion.div
            className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
            initial={{ opacity: 0, y: 32 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3, ease }}
          >
            <Link
              to="/chat"
              className="group inline-flex items-center gap-2.5 px-7 py-3.5 rounded-xl bg-indigo-500 hover:bg-indigo-600 text-[15px] font-semibold text-white transition-all hover:shadow-[0_0_32px_rgba(99,102,241,0.3)]"
            >
              Bắt đầu tư vấn
              <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
            <a
              href="#features"
              className="inline-flex items-center gap-2 px-7 py-3.5 rounded-xl bg-gray-100 dark:bg-white/[0.04] border border-gray-200 dark:border-white/[0.08] text-[15px] font-medium text-gray-600 dark:text-white/60 hover:text-gray-900 dark:hover:text-white/90 hover:bg-gray-200 dark:hover:bg-white/[0.07] transition-all"
            >
              Tìm hiểu thêm
            </a>
          </motion.div>
        </div>
      </section>

      {/* ─── bento grid ─── */}
      <section id="features" className="relative py-28 px-6">
        <div className="max-w-5xl mx-auto">
          <Reveal>
            <p className="text-[13px] font-semibold tracking-widest uppercase text-indigo-500 dark:text-indigo-400/80 text-center mb-3">
              Features
            </p>
            <h2 className="text-4xl md:text-5xl font-extrabold tracking-tighter text-center text-gray-900 dark:text-white/95">
              Tính năng nổi bật
            </h2>
            <p className="mt-4 text-center text-gray-400 dark:text-white/35 max-w-md mx-auto text-[15px] leading-relaxed">
              Hệ thống AI được thiết kế riêng cho lĩnh vực tuyển sinh quân sự
              Việt Nam
            </p>
          </Reveal>

          <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-3.5">
            {features.map((f, i) => (
              <Reveal key={i} delay={i * 0.06} className={f.className}>
                <BentoCard
                  icon={f.icon}
                  title={f.title}
                  description={f.description}
                  className="h-full"
                />
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ─── about ─── */}
      <section id="about" className="relative py-28 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <Reveal>
            <p className="text-[13px] font-semibold tracking-widest uppercase text-indigo-500 dark:text-indigo-400/80 mb-3">
              About
            </p>
            <h2 className="text-4xl md:text-5xl font-extrabold tracking-tighter text-gray-900 dark:text-white/95">
              Được xây dựng bởi AI
            </h2>
            <p className="mt-6 text-gray-400 dark:text-white/35 text-[15px] md:text-base leading-relaxed max-w-lg mx-auto">
              TSBot sử dụng mô hình ngôn ngữ lớn kết hợp cơ sở dữ liệu tuyển
              sinh chính thức, mang đến trải nghiệm tư vấn chính xác và đáng
              tin cậy cho thí sinh toàn quốc.
            </p>
          </Reveal>
        </div>
      </section>

      {/* ─── CTA ─── */}
      <section className="relative py-28 px-6">
        <Reveal>
          <div className="max-w-3xl mx-auto relative rounded-3xl overflow-hidden">
            {/* gradient border */}
            <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-indigo-300/50 via-transparent to-purple-300/50 dark:from-indigo-500/20 dark:via-transparent dark:to-purple-500/20 p-px">
              <div className="h-full w-full rounded-3xl bg-white/80 dark:bg-[#0c0c14]/80 backdrop-blur-2xl" />
            </div>

            <div className="relative z-10 py-16 px-8 text-center">
              <h2 className="text-3xl md:text-4xl font-extrabold tracking-tighter text-gray-900 dark:text-white/95">
                Sẵn sàng tìm hiểu?
              </h2>
              <p className="mt-3 text-gray-400 dark:text-white/35 text-[15px]">
                Bắt đầu trò chuyện với AI ngay bây giờ — hoàn toàn miễn phí.
              </p>
              <Link
                to="/chat"
                className="group mt-8 inline-flex items-center gap-2.5 px-8 py-4 rounded-xl bg-indigo-500 hover:bg-indigo-600 text-[15px] font-semibold text-white transition-all hover:shadow-[0_0_40px_rgba(99,102,241,0.35)]"
              >
                Bắt đầu tư vấn ngay
                <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
              </Link>
            </div>
          </div>
        </Reveal>
      </section>

      {/* ─── footer ─── */}
      <footer className="border-t border-gray-200/60 dark:border-white/[0.04] py-10 px-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center">
              <Bot className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="text-[13px] font-medium text-gray-400 dark:text-white/30">
              TSBot
            </span>
          </div>
          <p className="text-[12px] text-gray-300 dark:text-white/20">
            &copy; 2026 TSBot — Hệ thống chatbot AI tư vấn tuyển sinh quân đội.
            Thông tin chỉ mang tính tham khảo.
          </p>
        </div>
      </footer>
    </div>
  )
}
