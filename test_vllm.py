import asyncio, time, httpx
                                                                                                                   
BASE_URL = "http://localhost:8003"                        
MODEL = "Qwen/Qwen3-8B"                                                                                              
                                                        
LONG_PROMPT = """Bạn là chuyên gia tư vấn tuyển sinh quân sự Việt Nam. Dưới đây là thông tin điểm chuẩn các trường
quân đội năm 2023-2024:

Học viện Kỹ thuật Quân sự (HVKTQS):
- Công nghệ thông tin: Nam miền Bắc 28.5, Nam miền Nam 27.8, Nữ miền Bắc 29.0
- Kỹ thuật điện tử: Nam miền Bắc 27.0, Nam miền Nam 26.5
- Cơ khí động lực: Nam miền Bắc 25.5, Nam miền Nam 25.0

Học viện Hải quân (HVHQ):
- Kỹ thuật tàu quân sự: Nam miền Bắc 24.0, Nam miền Nam 23.5
- Điện tử viễn thông: Nam miền Bắc 25.0, Nam miền Nam 24.5

Trường Sĩ quan Lục quân 1:
- Chỉ huy tham mưu lục quân: Nam miền Bắc 22.0, Nam miền Nam 21.5

Tiêu chuẩn tuyển sinh: Thí sinh phải đủ 18 tuổi, có sức khỏe loại 1-2, lý lịch trong sáng, không có tiền án tiền sự.
Thí sinh nữ chỉ một số trường tuyển với chỉ tiêu hạn chế.

Câu hỏi: Tôi là nam, 18 tuổi, thi khối A00 được 26.5 điểm, quê miền Bắc. Với điểm này tôi có thể đăng ký vào những
trường và ngành nào? Tôi cần chuẩn bị những giấy tờ gì để đăng ký? Thời hạn nộp hồ sơ là khi nào?"""

VERY_LONG_PROMPT = """Bạn là chuyên gia tư vấn tuyển sinh quân sự Việt Nam với hơn 20 năm kinh nghiệm.
Dưới đây là thông tin chi tiết điểm chuẩn và chỉ tiêu các trường quân đội năm 2022-2024:

=== HỌC VIỆN KỸ THUẬT QUÂN SỰ (HVKTQS) ===
Năm 2024:
- Công nghệ thông tin (A00/A01): Nam MB 28.5, Nam MN 27.8, Nữ MB 29.0, Nữ MN 28.5
- Kỹ thuật điện tử viễn thông (A00): Nam MB 27.0, Nam MN 26.5, Nữ MB 27.5
- Cơ khí động lực (A00): Nam MB 25.5, Nam MN 25.0
- Kỹ thuật hóa học (B00): Nam MB 24.0, Nam MN 23.5
- Xây dựng công trình quân sự (A00): Nam MB 23.5, Nam MN 23.0
Chỉ tiêu 2024: ~800 SV, trong đó nữ ~50 SV

Năm 2023:
- Công nghệ thông tin: Nam MB 28.0, Nam MN 27.5, Nữ MB 28.5
- Kỹ thuật điện tử: Nam MB 26.5, Nam MN 26.0
- Cơ khí động lực: Nam MB 25.0, Nam MN 24.5

Năm 2022:
- Công nghệ thông tin: Nam MB 27.5, Nam MN 27.0, Nữ MB 28.0
- Kỹ thuật điện tử: Nam MB 26.0, Nam MN 25.5

=== HỌC VIỆN HẢI QUÂN (HVHQ) ===
Năm 2024:
- Kỹ thuật tàu quân sự (A00): Nam MB 24.0, Nam MN 23.5
- Điện tử viễn thông (A00): Nam MB 25.0, Nam MN 24.5
- Chỉ huy tham mưu hải quân (A00): Nam MB 22.0, Nam MN 21.5
Chỉ tiêu: ~300 SV/năm, không tuyển nữ

=== TRƯỜNG SĨ QUAN LỤC QUÂN 1 (SQLQ1) ===
Năm 2024:
- Chỉ huy tham mưu lục quân (A00/C00): Nam MB 22.0, Nam MN 21.5
- Chính trị viên (C00): Nam MB 21.0, Nam MN 20.5
Chỉ tiêu: ~500 SV/năm

=== TRƯỜNG SĨ QUAN LỤC QUÂN 2 (SQLQ2) ===
Năm 2024:
- Chỉ huy tham mưu lục quân (A00): Nam MB 21.5, Nam MN 21.0
- Hậu cần (A00/B00): Nam MB 20.5, Nam MN 20.0
Chỉ tiêu: ~400 SV/năm

=== HỌC VIỆN PHÒNG KHÔNG KHÔNG QUÂN (HVPKKQ) ===
Năm 2024:
- Kỹ thuật ra đa (A00): Nam MB 26.0, Nam MN 25.5
- Điều khiển tên lửa phòng không (A00): Nam MB 25.5, Nam MN 25.0
- Chỉ huy tham mưu phòng không (A00): Nam MB 23.0, Nam MN 22.5
Chỉ tiêu: ~350 SV/năm, không tuyển nữ

=== HỌC VIỆN AN NINH NHÂN DÂN (HVANNĐ) ===
Năm 2024:
- An ninh nhân dân (A00/C00): Nam MB 27.5, Nam MN 27.0, Nữ MB 28.0, Nữ MN 27.5
- Điều tra tội phạm (A00): Nam MB 27.0, Nam MN 26.5
- An toàn thông tin (A00): Nam MB 27.5, Nam MN 27.0
Chỉ tiêu: ~600 SV/năm, nữ ~100 SV

=== HỌC VIỆN CẢNH SÁT NHÂN DÂN (HVCSND) ===
Năm 2024:
- Cảnh sát điều tra (A00/C00): Nam MB 27.0, Nam MN 26.5, Nữ MB 27.5
- Cảnh sát kinh tế (A00): Nam MB 26.5, Nam MN 26.0
- Cảnh sát môi trường (A00/B00): Nam MB 25.5, Nam MN 25.0
Chỉ tiêu: ~700 SV/năm

=== QUY TRÌNH ĐĂNG KÝ VÀ YÊU CẦU ===
Tiêu chuẩn chung:
- Tuổi: 17-21 (một số trường 17-22)
- Sức khỏe: Loại 1 hoặc 2 theo tiêu chuẩn Bộ Quốc phòng
- Chiều cao nam: tối thiểu 164cm, nữ: 158cm
- Cân nặng: phù hợp BMI
- Thị lực: không quá 1.5 diop (một số ngành đặc thù yêu cầu cao hơn)
- Lý lịch: trong sáng, không có tiền án tiền sự bản thân và gia đình
- Hộ khẩu: phải đăng ký tại tỉnh/thành phố nộp hồ sơ

Hồ sơ cần nộp:
1. Đơn đăng ký dự tuyển (theo mẫu)
2. Học bạ THPT (bản gốc hoặc bản sao có công chứng)
3. Bằng tốt nghiệp THPT hoặc giấy chứng nhận tốt nghiệp tạm thời
4. Giấy khai sinh (bản sao có công chứng)
5. Sơ yếu lý lịch có xác nhận của UBND xã/phường
6. Giấy chứng nhận sức khỏe do hội đồng tuyển sinh cấp
7. 6 ảnh 4x6 (chụp trong vòng 6 tháng)
8. Giấy xác nhận hộ khẩu

Thời gian:
- Đăng ký nguyện vọng trên hệ thống: tháng 4-5
- Nộp hồ sơ gốc về Phòng Tuyển sinh quân sự tỉnh: tháng 6
- Thi tốt nghiệp THPT: tháng 6
- Xét tuyển: tháng 7-8
- Nhập học: tháng 8-9

Câu hỏi chi tiết: Tôi là nam, sinh năm 2006, quê Hà Nội (miền Bắc), thi khối A00 được 26.5 điểm (Toán 9.0,
Lý 8.75, Hóa 8.75), chiều cao 168cm, cân nặng 62kg, sức khỏe tốt, không có tiền án tiền sự.
Hãy phân tích chi tiết:
1. Tôi có thể đăng ký vào những trường và ngành nào với điểm này? Xếp theo thứ tự ưu tiên từ cao đến thấp.
2. Đánh giá cơ hội trúng tuyển của tôi ở từng trường (cao/trung bình/thấp).
3. Xu hướng điểm chuẩn 3 năm gần đây cho thấy điều gì? Năm tới có thể tăng hay giảm?
4. Tôi cần chuẩn bị những gì từ bây giờ đến khi nộp hồ sơ?
5. Nếu không đủ điểm vào trường quân đội, tôi nên xét tuyển trường dân sự nào phù hợp?"""

async def req(client, idx, input_text, max_tokens):
  start = time.time()
  try:
      r = await client.post(f"{BASE_URL}/v1/chat/completions", json={
          "model": MODEL,
          "messages": [{"role": "user", "content": input_text}],
          "max_tokens": max_tokens,
          "temperature": 0.1,
      }, timeout=180.0)
      ok = r.status_code == 200
      tokens_out = r.json().get("usage", {}).get("completion_tokens", 0) if ok else 0
      return {"ok": ok, "lat": time.time() - start, "tokens": tokens_out}
  except Exception as e:
      return {"ok": False, "lat": time.time() - start, "err": str(e)}

async def test(n, input_text, max_tokens, label):
  print(f"\n=== {label} | {n} concurrent ===")
  async with httpx.AsyncClient() as c:
      t0 = time.time()
      results = await asyncio.gather(*[req(c, i, input_text, max_tokens) for i in range(n)])
  total = time.time() - t0
  lats = sorted(r["lat"] for r in results if r["ok"])
  ok = len(lats)
  total_tokens = sum(r.get("tokens", 0) for r in results if r["ok"])
  if lats:
      print(f"  OK: {ok}/{n} | Total: {total:.1f}s | Throughput: {ok/total:.2f} req/s")
      print(f"  P50: {lats[len(lats)//2]:.1f}s | P95: {lats[int(len(lats)*0.95)]:.1f}s | Max: {lats[-1]:.1f}s")
      if total_tokens:
          print(f"  Tokens/s: {total_tokens/total:.1f} tok/s (tổng {total_tokens} tokens)")
  else:
      print(f"  FAILED: {[r.get('err','?') for r in results[:2]]}")

SHORT = "Điểm chuẩn HVKTQS 2024 là bao nhiêu?"

async def main():
  print("### SHORT context (input ~20 tokens, output 200) ###")
  for n in [1, 10, 30, 50]:
      await test(n, SHORT, 200, "short")
      await asyncio.sleep(5)

  print("\n### LONG context (input ~400 tokens, output 500) ###")
  for n in [1, 10, 20, 50]:
      await test(n, LONG_PROMPT, 500, "long")
      await asyncio.sleep(8)

  print("\n### VERY LONG context (input ~1200 tokens, output 1000) ###")
  for n in [1, 10, 20, 50]:
      await test(n, VERY_LONG_PROMPT, 1000, "very_long")
      await asyncio.sleep(10)

asyncio.run(main())