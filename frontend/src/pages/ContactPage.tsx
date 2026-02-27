import { useState } from 'react'
import { Mail, Phone, MapPin, Send } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

const contactInfo = [
  {
    icon: Mail,
    title: 'Email',
    value: 'tsbot.support@gmail.com',
  },
  {
    icon: Phone,
    title: 'Hỗ trợ',
    value: '24/7 qua chatbot',
  },
  {
    icon: MapPin,
    title: 'Địa chỉ',
    value: 'Việt Nam',
  },
]

export default function ContactPage() {
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitted(true)
  }

  return (
    <div className="pt-24">
      {/* Hero */}
      <section className="py-16 bg-gradient-chat">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-4">
          <h1 className="text-4xl md:text-5xl tracking-tighter font-bold">
            Liên hệ
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Có câu hỏi hoặc góp ý? Hãy liên hệ với chúng tôi
          </p>
        </div>
      </section>

      {/* Content */}
      <section className="py-16">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-5 gap-8">
            {/* Contact info */}
            <div className="md:col-span-2 space-y-6">
              <h2 className="text-xl font-semibold tracking-tighter">
                Thông tin liên hệ
              </h2>
              <div className="space-y-4">
                {contactInfo.map((info) => (
                  <div
                    key={info.title}
                    className="glass-subtle rounded-2xl p-4 border border-border/50 flex items-center gap-4"
                  >
                    <div className="w-10 h-10 rounded-xl bg-gradient-military flex items-center justify-center shrink-0">
                      <info.icon className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <p className="text-sm font-medium">{info.title}</p>
                      <p className="text-sm text-muted-foreground">
                        {info.value}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Form */}
            <div className="md:col-span-3">
              <div className="glass-strong rounded-2xl p-6 md:p-8 border border-border/50 shadow-soft-sm">
                {submitted ? (
                  <div className="text-center py-12 space-y-4">
                    <div className="w-16 h-16 rounded-full bg-success/10 flex items-center justify-center mx-auto">
                      <Send className="w-8 h-8 text-success" />
                    </div>
                    <h3 className="text-xl font-semibold">Đã gửi thành công!</h3>
                    <p className="text-muted-foreground">
                      Cảm ơn bạn đã liên hệ. Chúng tôi sẽ phản hồi sớm nhất có thể.
                    </p>
                    <Button
                      variant="outline"
                      onClick={() => setSubmitted(false)}
                    >
                      Gửi tin nhắn khác
                    </Button>
                  </div>
                ) : (
                  <form onSubmit={handleSubmit} className="space-y-5">
                    <div className="grid sm:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="name">Họ tên</Label>
                        <Input
                          id="name"
                          placeholder="Nguyễn Văn A"
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="email">Email</Label>
                        <Input
                          id="email"
                          type="email"
                          placeholder="email@example.com"
                          required
                        />
                      </div>
                    </div>

                    <div className="grid sm:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="phone">Số điện thoại</Label>
                        <Input
                          id="phone"
                          type="tel"
                          placeholder="0912 345 678"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="subject">Chủ đề</Label>
                        <Select>
                          <SelectTrigger>
                            <SelectValue placeholder="Chọn chủ đề" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="general">Câu hỏi chung</SelectItem>
                            <SelectItem value="feedback">Góp ý</SelectItem>
                            <SelectItem value="bug">Báo lỗi</SelectItem>
                            <SelectItem value="cooperation">Hợp tác</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="message">Nội dung</Label>
                      <Textarea
                        id="message"
                        placeholder="Nhập nội dung tin nhắn của bạn..."
                        rows={5}
                        required
                      />
                    </div>

                    <Button
                      type="submit"
                      size="lg"
                      className="w-full bg-gradient-military text-white hover:brightness-110"
                    >
                      Gửi tin nhắn
                      <Send className="w-4 h-4 ml-1" />
                    </Button>
                  </form>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
