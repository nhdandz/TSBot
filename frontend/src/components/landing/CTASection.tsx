import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function CTASection() {
  return (
    <section className="py-24">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="glass-strong rounded-2xl p-12 shadow-soft-lg text-center border border-border/50 space-y-6">
          <h2 className="text-3xl md:text-4xl tracking-tighter font-bold">
            Sẵn sàng khám phá?
          </h2>
          <p className="text-lg text-muted-foreground max-w-lg mx-auto">
            Bắt đầu trò chuyện với TSBot ngay hôm nay để nhận tư vấn tuyển sinh
            quân đội chính xác và nhanh chóng.
          </p>
          <Link to="/chat">
            <Button
              size="lg"
              className="bg-gradient-military text-white hover:brightness-110 shadow-soft-md mt-2"
            >
              Bắt đầu trò chuyện
              <ArrowRight className="w-4 h-4 ml-1" />
            </Button>
          </Link>
        </div>
      </div>
    </section>
  )
}
