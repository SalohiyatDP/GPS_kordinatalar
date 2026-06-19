# Aqlli Koordinata va Kadastr Tahlilchisi

Koordinatalarni qayta ishlash, poligonlar yaratish, GIS fayllarni eksport qilish
va kadastr konturlarini tahlil qilish uchun professional, GIS darajasidagi veb
ilova. Kadastr mutaxassislari, GIS muhandislari, yer boshqaruvi tashkilotlari,
geodezistlar va davlat idoralari uchun moʻljallangan.

> Tillar: **Oʻzbekcha** (asosiy), **Ruscha**, **Inglizcha**.

---

## ✨ Imkoniyatlar

| Bosqich | Imkoniyat |
|---------|-----------|
| **1. Normallashtirish** | Koordinatalarni DMS, oʻnli, ruscha kirill belgilari (`С/Ю/В/З`), aralash formatlar, xarita havolalari (Google / Yandex / 2GIS) va TXT/CSV/XLSX fayllaridan oʻqish. `41°07'54.29"N 71°37'49.17"E` standart koʻrinishiga keltirish, qiymatlarni tekshirish, dublikatlarni olib tashlash. |
| **2. Geometriya va Eksport** | Tahrirlanadigan, tartibi oʻzgartiriladigan nuqtalar jadvali → poligon qurish → geodezik maydon (m² / gektar / km² / sotix) va perimetr (m / km). **XLSX, KML, KMZ, GeoJSON, PDF** eksporti. |
| **3. Kadastr tahlili** | `kontur.zip` shapefayl yuklash, CRS ni avtomatik aniqlash va qayta proyeksiyalash, nuqtaning konturga tegishliligini aniqlash, poligon kesishuvi/qoplanishi tahlili va **toʻliq / qisman (`q`)** biznes qoidasi. |
| **4. Interaktiv xarita** | Leaflet GIS xaritasi: nuqtalar (koʻk), poligon (qizil), toʻliq konturlar (yashil), qisman konturlar (sariq); masshtablash, qatlam almashtirish, asosiy/sun'iy yoʻldosh qatlamlari. |
| **5. Hisobotlar** | Bir tugma bilan `Analysis.xlsx`, `Analysis.pdf`, `Analysis.kmz`, `Analysis.geojson`. |

### Toʻliq / qisman biznes qoidasi

```
qoplanish_foizi = kesishuv_maydoni / kontur_maydoni × 100
qoplanish ≥ 99.9%  →  "145"   (Toʻliq)
qoplanish  < 99.9% →  "145q"  (Qisman — q = qism)
```

Misol xulosa: *“Poligon quyidagilar bilan kesishadi: 145, 146q, 147, 148q.”*

---

## 🧱 Texnologiyalar

**Frontend:** React 19 · TypeScript · Vite · Tailwind CSS · Leaflet · React Query · Zustand
**Backend:** Python · FastAPI · GeoPandas · Shapely · PyProj · Fiona · Pyogrio · RTree
**Eksportlar:** openpyxl (XLSX) · simplekml (KML/KMZ) · ReportLab (PDF) · GeoJSON
**Maʼlumotlar bazasi:** SQLite (SQLAlchemy 2.0)

---

## 🚀 Tez ishga tushirish (Docker)

```bash
docker compose up --build
```

- Frontend: <http://localhost:8080>
- Backend API + Swagger hujjatlari: <http://localhost:8000/docs>

## 🛠️ Lokal ishlab chiqish

Toʻliq koʻrsatma uchun [docs/INSTALL.md](docs/INSTALL.md) ga qarang.

**Talablar:**
[Python 3.10+](https://www.python.org/downloads/) va
[Node.js 18+](https://nodejs.org/en/download) oʻrnatilgan boʻlishi kerak.
Backend va frontend uchun **alohida ikkita terminal** oching.

> 💡 **Windows uchun eng oson yoʻl:** loyiha papkasidagi **`start.bat`** faylini
> ikki marta bosing — u backend va frontendni avtomatik oʻrnatadi, ishga
> tushiradi va brauzerda <http://localhost:5173> ni ochadi.

### 🪟 Windows (PowerShell)

> PowerShell `&&` belgisini qoʻllamaydi — har bir buyruqni **alohida qatorda** kiriting.

**1-terminal — Backend:**
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

> Agar `Activate.ps1` "running scripts is disabled" xatosini bersa, avval shuni
> bajaring (faqat shu oyna uchun amal qiladi), keyin yana activate qiling:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> ```

Activate boʻlgach qator boshida `(.venv)` koʻrinadi. Backend manzili:
<http://localhost:8000> · Swagger: <http://localhost:8000/docs>

**2-terminal — Frontend:**
```powershell
cd frontend
npm install
npm run dev
```
Brauzerda oching: <http://localhost:5173>

### 🐧 Linux / 🍎 macOS

**1-terminal — Backend:**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload          # http://localhost:8000
```

**2-terminal — Frontend:**
```bash
cd frontend
npm install
npm run dev                            # http://localhost:5173
```

Vite ishlab chiqish serveri `/api` soʻrovlarini `http://localhost:8000` ga
yoʻnaltiradi (proxy), shuning uchun ikkala server ham ishlab turishi kerak.

---

## 🧪 Testlar

**Windows (PowerShell):**
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest -q
```

**Linux / macOS:**
```bash
cd backend && source .venv/bin/activate
pytest -q
```

> 31 ta test: normallashtirish, geometriya, eksportlar, kadastr (toʻliq/qisman),
> shapefayl yuklash va toʻliq API ish jarayoni.

---

## 📚 Hujjatlar

- [Oʻrnatish qoʻllanmasi](docs/INSTALL.md)
- [API maʼlumotnomasi](docs/API.md)
- [Maʼlumotlar bazasi sxemasi](docs/DATABASE.md)

---

## 📈 Unumdorlik

Katta hajmdagi maʼlumotlar uchun moʻljallangan (100 000+ kontur poligoni,
10 000+ koordinata). Kesishuv amallari uchun GeoPandas/RTree fazoviy indekslashdan
va xaritada koʻrsatish uchun geometriyani soddalashtirishdan foydalaniladi.
