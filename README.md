# MA/EMA Sinyal Bot - Gelişmiş Versiyon v4.0

Bu proje, MetaTrader 5 platformunda çoklu zaman dilimi analizi yapan, mum kapanış zamanlarını bekleyen, gelişmiş tolerans sistemi ile çalışan ve her harfin kendi periyot bilgisini gösteren profesyonel bir sinyal botudur.

## 🚀 Yeni Özellikler v4.0

### 🔤 Her Harfin Kendi Periyotu
- **Birleştirilmiş sinyallerde** her harfin kendi MA/EMA bilgisi gösterilir
- **Format**: `H(MA10 4h), G(MA20 4h), F(MA30 4h)` şeklinde
- **Tam şeffaflık**: Hangi harfin hangi periyotta olduğu net
- **Strateji analizi**: Farklı periyotların birlikte çalışması

### ⏰ Mum Kapanış Sistemi
- **Her zaman dilimi kendi mum kapanışını bekler**
- **1h**: Her saatin başında (00:00, 01:00, 02:00, ...)
- **4h**: 4 saatlik mumların kapanışında (00:00, 04:00, 08:00, 12:00, 16:00, 20:00)
- **8h**: 8 saatlik mumların kapanışında (00:00, 08:00, 16:00)
- **12h**: 12 saatlik mumların kapanışında (00:00, 12:00)
- **1d**: Günlük mumların kapanışında (her gün 00:00)

### 📊 Çoklu Zaman Dilimi Sistemi
- **MA Hesaplama Zaman Dilimleri**: 4h, günlük, haftalık, aylık
- **Sinyal Arama Zaman Dilimleri**: 1h, 4h, 8h, 12h, 1d
- **25 ortalama** × **5 sinyal arama zaman dilimi** = **125 farklı sinyal kontrolü**

### 🎯 MA/EMA Tipine Göre Tolerans Sistemi
- **MA seçilirse**: MA hesaplama mantığı ile tolerans uygulanır
- **EMA seçilirse**: EMA hesaplama mantığı ile tolerans uygulanır
- **Aşağı tolerans**: MA/EMA değerini düşürür (örn: 100 → 99)
- **Yukarı tolerans**: MA/EMA değerini yükseltir (örn: 100 → 101)
- **Çift yön**: Hem yukarı hem aşağı tolerans aynı anda
- **Opsiyonel tolerans**: Hiçbir harf toleransı olmasa da çalışır

### 📱 Birleştirilmiş Sinyal Mesajları
- **Aynı sembol ve zaman diliminde** birden fazla harf sinyal verirse
- **Tek mesajda** tüm harfler birleştirilir
- **Her harfin periyot bilgisi** açıkça gösterilir
- **Yönlere göre gruplandırılmış** (Yukarı/Aşağı)
- **MA tipi ve tolerans bilgisi** her sinyal için gösterilir

### 🔗 Çarpım Grafikleri (Sentetik Enstrümanlar)
- **EURUSD*EURGBP** gibi çarpım grafikleri oluşturma
- **Çarpma (*), Bölme (/), Toplama (+), Çıkarma (-)** işlemleri
- Manuel olarak ayarlanabilir çarpım grafikleri
- Otomatik fiyat hesaplama

### ⚙️ Gelişmiş Sinyal Sistemi
- **Harf bazlı tolerans sistemi** - Her harf için ayrı tolerans
- **Sinyal iptal sistemi** - Fiyat belirli yüzde ilerlediğinde otomatik iptal
- **Periyodik mesaj gönderimi** - Aktif sinyaller için düzenli güncelleme
- **24 saat sinyal takibi** - Eski sinyallerin otomatik temizlenmesi
- **Maksimum periyot 1000** - Daha yüksek periyotlar için destek

### 📱 Telegram Entegrasyonu
- Anlık sinyal bildirimleri
- Detaylı sinyal bilgileri (MA tipi, periyot, tolerans, hesaplama zaman dilimi)
- Periyodik güncelleme mesajları
- Sinyal iptal bildirimleri
- `.env` dosyası ile güvenli konfigürasyon

## 🛠️ Kurulum

### Gereksinimler
```bash
pip install customtkinter
pip install MetaTrader5
pip install pandas
pip install ta
pip install python-telegram-bot
pip install python-dotenv
```

### MT5 Kurulumu
1. MetaTrader 5 terminalini indirin ve kurun
2. Hesabınıza giriş yapın
3. **Ayarlar > Expert Advisors** kısmından **"Allow automated trading"** seçeneğini etkinleştirin
4. Terminali açık tutun

### Telegram Bot Kurulumu
1. Telegram'da `@BotFather` ile bot oluşturun
2. Bot token'ını alın
3. Chat ID'nizi alın (`@userinfobot` ile)
4. `.env` dosyası oluşturun:

```env
BOT_TOKEN=your_bot_token_here
CHAT_ID=your_chat_id_here
```

## 📋 Kullanım

### 1. MA/EMA Ayarları
- 25 satırda MA/EMA konfigürasyonları yapın
- Her satır için:
  - **Tip**: MA veya EMA seçin
  - **Periyot**: Sayısal değer girin (1-1000)
  - **MA Hesaplama Zaman Dilimi**: 4h, günlük, haftalık, aylık seçin
  - **Sinyal Harfi**: Tek harf girin (A-Z)

### 2. Harf Tolerans Ayarları
- Her harf için ayrı tolerans ayarı (opsiyonel)
- **Aktif**: Harfi etkinleştir/devre dışı bırak
- **Tolerans %**: Yüzde değeri girin (0-50)
- **Aşağı**: Aşağı yön toleransını etkinleştir
- **Yukarı**: Yukarı yön toleransını etkinleştir

### 3. Sembol Yönetimi
- **Sembol Adı** alanına sembol yazın (örn: EURUSD)
- **"Sembol Ekle"** butonuna tıklayın
- **"Seçili Sembolü Sil"** ile silme işlemi
- Semboller `symbols.json` dosyasına kaydedilir

### 4. Çarpım Grafikleri
- **Sembol 1**: İlk sembol (örn: EURUSD)
- **Sembol 2**: İkinci sembol (örn: EURGBP)
- **Sembol Adı**: Çarpım grafiği için benzersiz isim

### 5. Sinyal İptal
- **İptal Yüzdesi**: Fiyat bu yüzde ilerlediğinde sinyal iptal olur

### 6. Bot Başlatma
- Tüm ayarları kaydettikten sonra **"Botu Başlat"** butonuna tıklayın
- Bot mum kapanış zamanlarını bekleyerek analiz yapacak

## 📁 Dosya Yapısı

```
bionluk/
├── main.py                   # Ana uygulama
├── gui.py                    # GUI bileşenleri
├── .env                      # Telegram bot ayarları
├── ma_config.json            # MA/EMA konfigürasyonları
├── tolerance_config.json     # Harf tolerans ayarları
├── symbols.json              # Özel semboller
├── synthetic_symbols.json    # Çarpım grafikleri
├── signal_cancel_config.json # Sinyal iptal ayarları
├── global_symbols.json       # Tüm semboller (otomatik)
└── README.md                 # Bu dosya
```

## 🔧 Konfigürasyon Dosyaları

### .env
```env
BOT_TOKEN=7872345042:AAERp5jmZmpOve0DuSw5n2Z6cmYbatSQwdc
CHAT_ID=847081095
```

### ma_config.json
```json
[
    {
        "tip": "EMA",
        "periyot": 100,
        "ma_timeframe": "haftalık",
        "harf": "A"
    },
    {
        "tip": "MA",
        "periyot": 50,
        "ma_timeframe": "günlük",
        "harf": "B"
    }
]
```

### tolerance_config.json
```json
{
    "A": {
        "tolerance": 1.0,
        "down": true,
        "up": false
    },
    "B": {
        "tolerance": 2.5,
        "down": true,
        "up": true
    }
}
```

### symbols.json
```json
[
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "XAUUSD",
    "XAGUSD"
]
```

### synthetic_symbols.json
```json
{
    "EURUSD_EURGBP_MULT": {
        "symbol1": "EURUSD",
        "symbol2": "EURGBP",
        "operation": "*",
        "formula": "EURUSD*EURGBP"
    }
}
```

### signal_cancel_config.json
```json
{
    "cancel_percentage": 5.0
}
```

## 📊 Sinyal Mantığı

### Mum Kapanış Sistemi
1. **Her zaman dilimi** kendi mum kapanışını bekler
2. **Mum kapandığında** sinyal kontrolü yapılır
3. **MA değerleri** hesaplama zaman dilimlerinde hesaplanır
4. **Tolerans** MA değerine uygulanır
5. **Sinyal kontrolü** yapılır

### Tolerans Sistemi
- **A harfi**: MA 100, tolerans %1, aşağı seçili
- **Hesaplama**: 100 × (1 - 0.01) = 99
- **Sinyal**: Fiyat 99'un altına düştüğünde

### Birleştirilmiş Mesaj Örneği
```
🚨 YENİ SİNYAL ALARMİ!

📊 Sembol: EURUSD
⏰ Sinyal Zaman Dilimi: 1h
📈 MA Hesaplama Zaman Dilimi: haftalık, günlük
🔤 Sinyal Harfi: A(EMA100 haftalık), B(MA50 günlük), F(MA30 4h)
💰 Fiyat: 1.0850

📈 Sinyal Detayları:

🟢 ALIŞ SİNYALLERİ (Yeşil Mum):
• A(EMA100 haftalık): EMA100 haftalık 1.0800 (Tolerans: %1.0)
• F(MA30 4h): MA30 4h 1.0750 (Tolerans: %2.0)

🔴 SATIŞ SİNYALLERİ (Kırmızı Mum):
• B(MA50 günlük): MA50 günlük 1.0900 (Tolerans: %1.5)
```

## 🔍 Backtest Sistemi

Bot, algoritmanızı test etmek için kapsamlı bir backtest sistemi içerir. Bu sistem GUI'ye ihtiyaç duymadan çalışır ve 15 günlük geçmiş veri üzerinden sinyal analizi yapar.

### **Backtest Çalıştırma:**

```bash
python main.py --backtest
```

### **Backtest Özellikleri:**

#### **📋 Otomatik Veri Yükleme:**
- **MA/EMA Konfigürasyonları**: `ma_config.json` dosyasından
- **Tolerans Ayarları**: `tolerance_config.json` dosyasından (opsiyonel)
- **Sinyal İptal Ayarları**: `signal_cancel_config.json` dosyasından
- **Sembol Listesi**: Global semboller + özel semboller + sentetik semboller

#### **📊 Analiz Kapsamı:**
- **Tarih Aralığı**: Son 15 gün
- **Zaman Dilimleri**: 1h, 4h, 8h, 12h, 1d
- **Sinyal Türleri**: Alış/Satış sinyalleri
- **MA/EMA Tipleri**: MA ve EMA ayrı ayrı analiz edilir

#### **📈 Detaylı Raporlama:**
- **Genel İstatistikler**: Toplam sinyal sayısı, günlük ortalama
- **Sinyal Türü Analizi**: Alış vs satış oranları
- **MA/EMA Analizi**: MA vs EMA performansı
- **Harf Bazında Analiz**: Her harfin sinyal performansı
- **Zaman Dilimi Analizi**: Her zaman diliminin performansı
- **Sembol Analizi**: En aktif semboller
- **Tolerans Analizi**: Toleranslı vs toleranssız sinyaller
- **Mum Rengi Analizi**: Yeşil vs kırmızı mum oranları
- **Fiyat Analizi**: Fiyat aralıkları ve ortalamalar

#### **💾 Sonuç Dosyaları:**
- **JSON Formatında**: `backtest_results_YYYYMMDD_HHMMSS.json`
- **Detaylı Sinyal Bilgileri**: Her sinyalin tam detayları
- **Zaman Damgası**: Sinyal oluşma zamanları
- **Fiyat Bilgileri**: OHLC değerleri

### **Backtest Çıktı Örneği:**

```
🔍 BACKTEST BAŞLATILIYOR...
============================================================
📋 Konfigürasyon dosyaları yükleniyor...
✅ 25 MA/EMA konfigürasyonu yüklendi
✅ 3 tolerans ayarı yüklendi
✅ Sinyal iptal yüzdesi: %5.0

📈 Sembol listesi oluşturuluyor...
✅ 5 sembol bulundu

📅 Tarih aralığı: 2025-07-15 01:07 - 2025-07-30 01:07

🔍 5 sembol analiz ediliyor...

📊 Sembol 1/5: EURUSD
  ⏰ 1h: 264 mum bulundu
    🚨 SİNYAL: H(MA10 4h) (1 harf) - Yukarı - alış - 1.34551
    🚨 SİNYAL: G(MA20 4h), F(MA30 4h) (2 harf) - Aşağı - satış - 1.34426
    🚨 SİNYAL: H(MA10 4h), G(MA20 4h), F(MA30 4h), E(EMA40 4h), D(MA50 4h), C(MA60 4h), B(MA70 4h) (7 harf) - Yukarı - alış - 1.34232

📊 BACKTEST ÖZET RAPORU
============================================================
📅 Tarih Aralığı: 2025-07-15 01:07 - 2025-07-30 01:07
📈 Analiz Edilen Sembol: 5
⚙️ MA/EMA Konfigürasyonu: 25
🎯 Toplam Sinyal: 1,183

⏰ ZAMAN DİLİMİ BAZINDA SONUÇLAR:
    1h: 629 sinyal (328 alış, 301 satış)
    4h: 255 sinyal (128 alış, 127 satış)
    8h: 150 sinyal ( 82 alış,  68 satış)
   12h:  97 sinyal ( 56 alış,  41 satış)
    1d:  52 sinyal ( 27 alış,  25 satış)

🏆 EN ÇOK SİNYAL VEREN SEMBOLLER:
   1. NZDUSD: 204 sinyal
   2. USDJPY: 195 sinyal
   3. AUDUSD: 181 sinyal

💾 Detaylı sonuçlar: backtest_results_20250730_011028.json
============================================================
✅ BACKTEST TAMAMLANDI!
```

### **Backtest Avantajları:**

✅ **Gerçek Zamanlı Test**: Algoritmanızı gerçek verilerle test edin
✅ **Performans Analizi**: Hangi ayarların daha iyi çalıştığını görün
✅ **Optimizasyon**: Parametreleri optimize etmek için kullanın
✅ **Risk Analizi**: Sinyal sıklığını ve dağılımını analiz edin
✅ **Strateji Geliştirme**: Yeni stratejiler geliştirmek için kullanın

### **Backtest Kullanım İpuçları:**

1. **Önce Konfigürasyonları Kaydedin**: Backtest çalıştırmadan önce MA/EMA ayarlarınızı kaydedin
2. **MT5 Bağlantısını Kontrol Edin**: MT5'in açık ve bağlı olduğundan emin olun
3. **Sonuçları Analiz Edin**: JSON dosyasını inceleyerek detaylı analiz yapın
4. **Parametreleri Optimize Edin**: Sonuçlara göre ayarlarınızı güncelleyin
5. **Düzenli Test Yapın**: Stratejinizi düzenli olarak test edin

### **Normal Çalıştırma:**

```bash
python main.py
```

Bu backtest sistemi, algoritmanızın performansını değerlendirmek ve optimize etmek için güçlü bir araçtır.

## ⚠️ Önemli Notlar

1. **MT5 Bağlantısı**: Terminal açık ve oturum açılmış olmalı
2. **Sembol Erişimi**: MT5'te sembolün mevcut olduğundan emin olun
3. **Telegram Bot**: Bot token ve chat ID doğru olmalı
4. **Mum Kapanışı**: Bot sadece mum kapanışlarında analiz yapar
5. **Performans**: Optimize edilmiş performans
6. **Tolerans**: Opsiyonel - hiçbir harf toleransı olmasa da çalışır
7. **Periyot Limiti**: Maksimum 1000 periyot desteklenir

## 🚨 Hata Giderme

### MT5 Bağlantı Hatası
- Terminal açık mı kontrol edin
- Doğru hesaba giriş yapıldı mı kontrol edin
- Expert Advisors etkin mi kontrol edin

### Sembol Bulunamadı Hatası
- MT5 Market Watch'ta sembolün mevcut olduğunu kontrol edin
- Sembol adını doğru yazdığınızdan emin olun
- Bulunamayan semboller atlanır ve console'da uyarı mesajı gösterilir

### Telegram Mesaj Hatası
- `.env` dosyası doğru formatta mı kontrol edin
- Bot token doğru mu kontrol edin
- Chat ID doğru mu kontrol edin
- İnternet bağlantısı var mı kontrol edin

### Tolerans Hatası
- Tolerans ayarları opsiyonel - boş bırakabilirsiniz
- Hiçbir harf toleransı olmasa da bot çalışır
- Tolerans değerleri 0-50 arasında olmalı

## 📈 Performans İpuçları

1. **Sembol Sayısını Sınırlayın**: Çok fazla sembol performansı düşürür
2. **MA Sayısını Azaltın**: Önce az MA ile test edin
3. **Toleransı Artırın**: Daha az sinyal için toleransı artırın
4. **Mum Kapanışı**: Sadece mum kapanışlarında analiz yaparak optimize edilmiş performans
5. **Periyot Optimizasyonu**: Çok yüksek periyotlar hesaplama süresini artırır

## 🔄 Güncellemeler

- **v4.0**: Her harfin kendi periyot bilgisi gösterimi
- **v4.0**: Birleştirilmiş sinyallerde detaylı periyot bilgisi
- **v4.0**: Maksimum periyot 1000'e çıkarıldı
- **v4.0**: Tolerans ayarları opsiyonel hale getirildi
- **v4.0**: .env dosyası desteği eklendi
- **v3.0**: Mum kapanış sistemi eklendi
- **v3.0**: Çoklu zaman dilimi sistemi
- **v3.0**: MA/EMA tipine göre tolerans sistemi
- **v3.0**: Birleştirilmiş sinyal mesajları
- **v3.0**: Harf bazlı tolerans ayarları
- **v3.0**: Gelişmiş GUI arayüzü
- **v2.1**: Çarpım grafikleri desteği
- **v2.1**: Sinyal iptal sistemi
- **v2.1**: Periyodik mesaj sistemi

## 📞 Destek

Herhangi bir sorun yaşarsanız:
1. Console çıktılarını kontrol edin
2. Konfigürasyon dosyalarını kontrol edin
3. MT5 bağlantısını test edin
4. Telegram bot ayarlarını kontrol edin
5. Mum kapanış zamanlarını kontrol edin
6. .env dosyasının doğru formatta olduğunu kontrol edin

## 📊 Örnek Çıktılar

### Tek Harf Sinyali:
```
🚨 SİNYAL: H - MA10 4h - Yukarı - alış - 1.34551
```

### Birleştirilmiş Sinyal:
```
🚨 SİNYAL: H(MA10 4h), G(MA20 4h), F(MA30 4h) (3 harf) - Yukarı - alış - 1.34232
```

### Ana Bot Konsol Çıktısı:
```
🚨 YENİ SİNYAL: EURUSD (1h) - H(MA10 4h), G(MA20 4h) (2 harf)
```

### Telegram Mesajı:
```
🚨 YENİ SİNYAL ALARMİ!

📊 Sembol: EURUSD
⏰ Sinyal Zaman Dilimi: 1h
📈 MA Hesaplama Zaman Dilimi: 4h
🔤 Sinyal Harfi: H(MA10 4h), G(MA20 4h), F(MA30 4h)
💰 Fiyat: 1.3455

🟢 ALIŞ SİNYALLERİ (Yeşil Mum):
• H(MA10 4h): MA10 4h 1.3452
• G(MA20 4h): MA20 4h 1.3448
• F(MA30 4h): MA30 4h 1.3445
```