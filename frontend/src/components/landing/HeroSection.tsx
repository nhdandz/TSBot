import { Link } from 'react-router-dom'
import { ArrowRight, Bot, User } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function HeroSection() {
  return (
    <section className="min-h-screen bg-gradient-chat flex items-center relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gold/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-olive/5 rounded-full blur-3xl" />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-16 w-full">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Left: Content */}
          <div className="space-y-8 animate-fade-in-up">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 rounded-full border border-gold/20 bg-gold/10 px-4 py-1.5 text-sm font-medium text-gold">
              <Bot className="w-4 h-4" />
              AI Tư vấn Tuyển sinh
            </div>

            {/* Heading */}
            <div className="space-y-4">
              <h1 className="text-5xl md:text-7xl tracking-tighter font-bold leading-[1.1]">
                Tư vấn tuyển sinh
                <br />
                <span className="text-gradient-military">quân đội</span>
              </h1>
              <h2 className="text-5xl md:text-7xl tracking-tighter font-bold leading-[1.1]">
                Thông minh với{' '}
                <span className="text-gradient-military">AI</span>
              </h2>
            </div>

            {/* Subtitle */}
            <p className="text-lg text-muted-foreground max-w-lg leading-relaxed">
              Trợ lý AI giúp bạn tìm hiểu thông tin tuyển sinh các trường quân đội
              tại Việt Nam. Nhanh chóng, chính xác và hoàn toàn miễn phí.
            </p>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row gap-4">
              <Link to="/chat">
                <Button
                  size="lg"
                  className="bg-gradient-military text-white hover:brightness-110 shadow-soft-md w-full sm:w-auto"
                >
                  Bắt đầu trò chuyện
                  <ArrowRight className="w-4 h-4 ml-1" />
                </Button>
              </Link>
              <Link to="/gioi-thieu">
                <Button
                  size="lg"
                  variant="outline"
                  className="w-full sm:w-auto"
                >
                  Tìm hiểu thêm
                </Button>
              </Link>
            </div>
          </div>

          {/* Right: Chat mockup */}
          <div className="animate-fade-in-up [animation-delay:200ms]">
            <div className="glass-strong rounded-2xl shadow-soft-lg p-6 space-y-4 border border-border/50">
              {/* Header */}
              <div className="flex items-center gap-3 pb-4 border-b border-border/50">
                <div className="w-10 h-10 rounded-xl bg-gradient-military flex items-center justify-center">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="font-semibold text-sm">TSBot</p>
                  <p className="text-xs text-muted-foreground">Trực tuyến</p>
                </div>
                <div className="ml-auto w-2 h-2 rounded-full bg-success animate-pulse" />
              </div>

              {/* Messages */}
              <div className="space-y-3">
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center shrink-0">
                    <User className="w-4 h-4 text-muted-foreground" />
                  </div>
                  <div className="bg-muted/60 rounded-2xl rounded-tl-md px-4 py-2.5 text-sm max-w-[80%]">
                    Điểm chuẩn Học viện Quân y năm 2024 là bao nhiêu?
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-lg bg-gradient-military flex items-center justify-center shrink-0">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                  <div className="bg-primary/5 border border-primary/10 rounded-2xl rounded-tl-md px-4 py-2.5 text-sm max-w-[80%]">
                    Điểm chuẩn Học viện Quân y năm 2024 dao động từ{' '}
                    <span className="font-semibold text-primary">24.5 - 27.8</span>{' '}
                    điểm tùy theo ngành và đối tượng...
                  </div>
                </div>
              </div>

              {/* Input mockup */}
              <div className="flex gap-2 pt-2">
                <div className="flex-1 h-10 rounded-xl bg-muted/40 border border-border/50 flex items-center px-3">
                  <span className="text-sm text-muted-foreground">
                    Nhập câu hỏi của bạn...
                  </span>
                </div>
                <div className="w-10 h-10 rounded-xl bg-gradient-military flex items-center justify-center">
                  <ArrowRight className="w-4 h-4 text-white" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
