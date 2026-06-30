# .env dosyasını düzelt
# Bu script .env'e JWT_SECRET ekler, eğer yoksa

import os
from pathlib import Path

ENV_PATH = Path(r"C:\projelerim\gozbegim\backend\.env")

# JWT_SECRET — Supabase Dashboard'dan al
# Settings → API → "JWT Settings" → "JWT Secret"
JWT_SECRET = input("JWT Secret'ı yapıştır (Supabase Dashboard'dan): ").strip()

if not JWT_SECRET:
    print("❌ Secret boş, çıkılıyor")
    exit(1)

# .env var mı?
if ENV_PATH.exists():
    content = ENV_PATH.read_text(encoding="utf-8")
    
    # Eğer zaten varsa, değiştir
    if "SUPABASE_JWT_SECRET=" in content:
        lines = content.split("\n")
        new_lines = []
        replaced = False
        for line in lines:
            if line.startswith("SUPABASE_JWT_SECRET="):
                new_lines.append(f"SUPABASE_JWT_SECRET={JWT_SECRET}")
                replaced = True
            else:
                new_lines.append(line)
        
        if not replaced:
            new_lines.append(f"SUPABASE_JWT_SECRET={JWT_SECRET}")
        
        ENV_PATH.write_text("\n".join(new_lines), encoding="utf-8")
        print(f"✅ JWT_SECRET .env'e eklendi (replace edildi)")
    else:
        # Yoksa ekle
        with open(ENV_PATH, "a", encoding="utf-8") as f:
            f.write(f"\nSUPABASE_JWT_SECRET={JWT_SECRET}\n")
        print(f"✅ JWT_SECRET .env'e eklendi (appended)")
else:
    # .env yoksa oluştur
    ENV_PATH.write_text(f"SUPABASE_JWT_SECRET={JWT_SECRET}\n", encoding="utf-8")
    print(f"✅ .env oluşturuldu ve JWT_SECRET eklendi")

print(f"\nŞimdi backend'i restart et:")
print(f"  uvicorn main:app --reload --port 8000")
