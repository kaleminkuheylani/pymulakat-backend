"""Backend token testi — direkt dene"""
import requests

BASE = "http://localhost:8000"

print("═══════════════════════════════════════════════")
print("🔍 Backend Token Test")
print("═══════════════════════════════════════════════\n")

# 1) Health check
print("1️⃣  /health:")
r = requests.get(f"{BASE}/health")
print(f"   {r.status_code} {r.json()}\n")

# 2) /auth/me token'sız
print("2️⃣  /auth/me (token'sız, 401 beklenir):")
r = requests.get(f"{BASE}/auth/me")
print(f"   {r.status_code} {r.json()}\n")

# 3) /auth/me token'lı
token = input("3️⃣  Token'ı yapıştır (Enter atarsan atlanır): ").strip()
if token:
    print(f"\n   /auth/me (token'lı, 200 beklenir):")
    r = requests.get(f"{BASE}/auth/me", headers={"Authorization": f"Bearer {token}"})
    print(f"   {r.status_code} {r.json()}\n")

    if r.status_code != 200:
        print("   ⚠️  Sorun devam ediyor. Şunları kontrol et:")
        print("   - .env'de SUPABASE_SERVICE_ROLE_KEY var mı?")
        print("   - Backend'i --reload ile başlattıysan yeni .env için restart ettin mi?")
        print("   - Token gerçekten login sonrası alınan access_token mı?")
else:
    print("\n   Atlandı.")

print("\n═══════════════════════════════════════════════")
print("📝 Beklenen sonuçlar:")
print("   /auth/me (token'sız) → 401 + 'Geçersiz token formatı'")
print("   /auth/me (token'lı)   → 200 + user objesi")
print("═══════════════════════════════════════════════")