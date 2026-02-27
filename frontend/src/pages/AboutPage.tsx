import { Database, Brain, Search, Server } from 'lucide-react'

const technologies = [
  {
    icon: Search,
    title: 'RAG System',
    description:
      'Retrieval-Augmented Generation - Tìm kiếm và trích xuất thông tin từ kho dữ liệu tuyển sinh để đảm bảo câu trả lời chính xác.',
  },
  {
    icon: Database,
    title: 'Text-to-SQL',
    description:
      'Chuyển đổi câu hỏi tự nhiên thành truy vấn SQL để lấy dữ liệu số liệu chính xác như điểm chuẩn, chỉ tiêu.',
  },
  {
    icon: Brain,
    title: 'Large Language Model',
    description:
      'Mô hình ngôn ngữ lớn giúp hiểu câu hỏi và tổng hợp câu trả lời tự nhiên, dễ hiểu.',
  },
  {
    icon: Server,
    title: 'Vector Database',
    description:
      'Cơ sở dữ liệu vector lưu trữ và tìm kiếm ngữ nghĩa tài liệu tuyển sinh với tốc độ cao.',
  },
]

export default function AboutPage() {
  return (
    <div className="pt-24">
      {/* Hero */}
      <section className="py-16 bg-gradient-chat">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-4">
          <h1 className="text-4xl md:text-5xl tracking-tighter font-bold">
            Về TSBot
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Trợ lý AI tư vấn tuyển sinh quân đội, được xây dựng với mục tiêu
            giúp thí sinh tiếp cận thông tin chính xác và nhanh chóng.
          </p>
        </div>
      </section>

      {/* Mission */}
      <section className="py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="glass-strong rounded-2xl p-8 border border-border/50 shadow-soft-sm space-y-4">
            <h2 className="text-2xl tracking-tighter font-bold">Sứ mệnh</h2>
            <p className="text-muted-foreground leading-relaxed">
              TSBot ra đời với sứ mệnh thu hẹp khoảng cách thông tin trong tuyển sinh
              quân đội. Chúng tôi hiểu rằng việc tìm kiếm thông tin tuyển sinh từ nhiều
              nguồn khác nhau có thể mất nhiều thời gian và đôi khi không chính xác.
              TSBot tổng hợp và cung cấp thông tin từ các nguồn chính thức, giúp thí sinh
              và phụ huynh có cái nhìn toàn diện về các trường quân đội tại Việt Nam.
            </p>
            <p className="text-muted-foreground leading-relaxed">
              Với công nghệ AI tiên tiến, TSBot không chỉ trả lời câu hỏi mà còn hỗ trợ
              tra cứu điểm chuẩn, so sánh ngành học, và tư vấn phù hợp với năng lực
              của từng thí sinh.
            </p>
          </div>
        </div>
      </section>

      {/* Technology */}
      <section className="py-16 bg-muted/30">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12 space-y-4">
            <h2 className="text-2xl md:text-3xl tracking-tighter font-bold">
              Công nghệ sử dụng
            </h2>
            <p className="text-muted-foreground">
              Kết hợp các công nghệ AI hiện đại nhất
            </p>
          </div>
          <div className="grid sm:grid-cols-2 gap-6">
            {technologies.map((tech) => (
              <div
                key={tech.title}
                className="glass-subtle rounded-2xl p-6 border border-border/50 hover:shadow-soft-md transition-all duration-300 ease-apple"
              >
                <div className="w-12 h-12 rounded-xl bg-gradient-military flex items-center justify-center mb-4">
                  <tech.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{tech.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {tech.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Disclaimer */}
      <section className="py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="rounded-2xl border border-warning/30 bg-warning/5 p-6 space-y-2">
            <h3 className="font-semibold text-warning">Lưu ý quan trọng</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Thông tin do TSBot cung cấp mang tính chất tham khảo. Dữ liệu được tổng hợp
              từ các nguồn công khai và có thể chưa được cập nhật kịp thời. Vui lòng kiểm
              tra lại thông tin với website chính thức của các trường và Bộ Quốc phòng
              trước khi đưa ra quyết định quan trọng.
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}
