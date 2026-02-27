import { Target, Clock, Heart, Database, Smile, ShieldCheck } from 'lucide-react'

const features = [
  {
    icon: Target,
    title: 'Trả lời chính xác',
    description:
      'Sử dụng công nghệ RAG và Text-to-SQL để truy vấn dữ liệu chính xác từ nguồn đáng tin cậy.',
  },
  {
    icon: Clock,
    title: 'Hoạt động 24/7',
    description:
      'Luôn sẵn sàng hỗ trợ bạn mọi lúc, mọi nơi, không giới hạn thời gian.',
  },
  {
    icon: Heart,
    title: 'Miễn phí hoàn toàn',
    description:
      'Không tốn bất kỳ chi phí nào. Tất cả tính năng đều miễn phí cho mọi người.',
  },
  {
    icon: Database,
    title: 'Đa dạng thông tin',
    description:
      'Bao phủ thông tin tuyển sinh của 15+ trường quân đội với hơn 100 ngành đào tạo.',
  },
  {
    icon: Smile,
    title: 'Giao diện thân thiện',
    description:
      'Trải nghiệm trò chuyện tự nhiên, dễ sử dụng như nhắn tin với một người bạn.',
  },
  {
    icon: ShieldCheck,
    title: 'Nguồn đáng tin cậy',
    description:
      'Dữ liệu được tổng hợp từ các nguồn chính thức của Bộ Quốc phòng và các trường.',
  },
]

export default function FeaturesSection() {
  return (
    <section className="py-24 bg-muted/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-2xl mx-auto mb-16 space-y-4">
          <h2 className="text-3xl md:text-4xl tracking-tighter font-bold">
            Tính năng nổi bật
          </h2>
          <p className="text-lg text-muted-foreground">
            Tại sao chọn TSBot cho hành trình tuyển sinh của bạn?
          </p>
        </div>

        {/* Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <div
              key={feature.title}
              className="glass-subtle rounded-2xl p-6 border border-border/50 hover:shadow-soft-md transition-all duration-300 ease-apple group animate-fade-in-up"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="w-12 h-12 rounded-xl bg-gradient-military flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300 ease-apple">
                <feature.icon className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
