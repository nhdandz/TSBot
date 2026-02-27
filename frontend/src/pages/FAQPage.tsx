import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'

const faqs = [
  {
    question: 'TSBot là gì?',
    answer:
      'TSBot là một trợ lý AI chuyên tư vấn tuyển sinh quân đội tại Việt Nam. TSBot sử dụng công nghệ trí tuệ nhân tạo để trả lời các câu hỏi về tuyển sinh, điểm chuẩn, ngành đào tạo và thông tin liên quan đến các trường quân đội.',
  },
  {
    question: 'TSBot có miễn phí không?',
    answer:
      'Có, TSBot hoàn toàn miễn phí. Bạn có thể sử dụng tất cả các tính năng mà không cần đăng ký hay thanh toán bất kỳ khoản phí nào.',
  },
  {
    question: 'TSBot có thể trả lời những câu hỏi gì?',
    answer:
      'TSBot có thể trả lời các câu hỏi về: thông tin tuyển sinh các trường quân đội, điểm chuẩn qua các năm, ngành đào tạo, chỉ tiêu tuyển sinh, điều kiện sức khỏe, hồ sơ xét tuyển, và nhiều thông tin liên quan khác.',
  },
  {
    question: 'Thông tin TSBot cung cấp có chính xác không?',
    answer:
      'TSBot sử dụng công nghệ RAG và Text-to-SQL để truy vấn dữ liệu từ cơ sở dữ liệu đã được tổng hợp từ các nguồn chính thức. Tuy nhiên, thông tin mang tính chất tham khảo và bạn nên kiểm tra lại với nguồn chính thức trước khi đưa ra quyết định.',
  },
  {
    question: 'Tôi có thể sử dụng TSBot trên điện thoại không?',
    answer:
      'Có, TSBot được thiết kế với giao diện responsive, hoạt động tốt trên mọi thiết bị bao gồm điện thoại, máy tính bảng và máy tính để bàn.',
  },
  {
    question: 'Dữ liệu cuộc trò chuyện của tôi có được bảo mật không?',
    answer:
      'Chúng tôi tôn trọng quyền riêng tư của bạn. Các cuộc trò chuyện được xử lý để cải thiện chất lượng dịch vụ nhưng không được chia sẻ với bên thứ ba. Bạn không cần cung cấp thông tin cá nhân để sử dụng TSBot.',
  },
]

export default function FAQPage() {
  return (
    <div className="pt-24">
      {/* Hero */}
      <section className="py-16 bg-gradient-chat">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-4">
          <h1 className="text-4xl md:text-5xl tracking-tighter font-bold">
            Câu hỏi thường gặp
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Tìm câu trả lời cho những thắc mắc phổ biến về TSBot
          </p>
        </div>
      </section>

      {/* FAQ list */}
      <section className="py-16">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <Accordion type="single" collapsible className="space-y-4">
            {faqs.map((faq, index) => (
              <AccordionItem
                key={index}
                value={`item-${index}`}
                className="glass-subtle rounded-2xl border border-border/50 px-6 data-[state=open]:shadow-soft-sm transition-shadow duration-300"
              >
                <AccordionTrigger className="text-left font-semibold hover:no-underline py-5">
                  {faq.question}
                </AccordionTrigger>
                <AccordionContent className="text-muted-foreground leading-relaxed">
                  {faq.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-muted/30">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
          <h2 className="text-2xl tracking-tighter font-bold">
            Không tìm thấy câu trả lời?
          </h2>
          <p className="text-muted-foreground">
            Liên hệ với chúng tôi hoặc thử hỏi trực tiếp TSBot
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/lien-he">
              <Button variant="outline" size="lg">
                Liên hệ
              </Button>
            </Link>
            <Link to="/chat">
              <Button
                size="lg"
                className="bg-gradient-military text-white hover:brightness-110"
              >
                Hỏi TSBot
                <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
