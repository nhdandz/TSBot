const stats = [
  { value: '15+', label: 'Trường quân đội' },
  { value: '100+', label: 'Ngành đào tạo' },
  { value: '1000+', label: 'Câu hỏi đã trả lời' },
  { value: '24/7', label: 'Hỗ trợ liên tục' },
]

export default function StatsSection() {
  return (
    <section className="bg-gradient-navy py-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat) => (
            <div key={stat.label} className="text-center space-y-2">
              <p className="text-5xl font-bold text-gold tracking-tighter">
                {stat.value}
              </p>
              <p className="text-sm text-white/70 font-medium">{stat.label}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
