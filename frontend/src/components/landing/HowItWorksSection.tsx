import { MessageSquare, Cpu, CheckCircle } from 'lucide-react'

const steps = [
  {
    icon: MessageSquare,
    step: '01',
    title: 'Đặt câu hỏi',
    description:
      'Nhập câu hỏi về tuyển sinh quân đội mà bạn muốn tìm hiểu. Có thể hỏi bằng ngôn ngữ tự nhiên.',
  },
  {
    icon: Cpu,
    step: '02',
    title: 'AI phân tích',
    description:
      'Hệ thống AI sử dụng RAG và Text-to-SQL để tìm kiếm và phân tích thông tin chính xác nhất.',
  },
  {
    icon: CheckCircle,
    step: '03',
    title: 'Nhận câu trả lời',
    description:
      'Nhận câu trả lời chi tiết kèm nguồn tham khảo đáng tin cậy chỉ trong vài giây.',
  },
]

export default function HowItWorksSection() {
  return (
    <section className="py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-2xl mx-auto mb-16 space-y-4">
          <h2 className="text-3xl md:text-4xl tracking-tighter font-bold">
            Cách hoạt động
          </h2>
          <p className="text-lg text-muted-foreground">
            Chỉ 3 bước đơn giản để nhận tư vấn tuyển sinh
          </p>
        </div>

        {/* Steps */}
        <div className="grid md:grid-cols-3 gap-8">
          {steps.map((item, index) => (
            <div
              key={item.step}
              className="relative animate-fade-in-up"
              style={{ animationDelay: `${index * 150}ms` }}
            >
              {/* Connector line (desktop) */}
              {index < steps.length - 1 && (
                <div className="hidden md:block absolute top-6 left-[calc(50%+32px)] w-[calc(100%-64px)] h-px bg-border" />
              )}

              <div className="glass rounded-2xl p-6 border border-border/50 text-center space-y-4 relative">
                {/* Step badge */}
                <div className="w-12 h-12 rounded-full bg-gradient-military flex items-center justify-center mx-auto">
                  <item.icon className="w-6 h-6 text-white" />
                </div>

                {/* Step number */}
                <span className="text-xs font-bold text-gold uppercase tracking-widest">
                  Bước {item.step}
                </span>

                <h3 className="text-lg font-semibold">{item.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {item.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
