# MA/EMA Sinyal Bot - Gelişmiş Versiyon v3.0

Bu proje, MetaTrader 5 platformunda çoklu zaman dilimi analizi yapan, mum kapanış zamanlarını bekleyen ve gelişmiş tolerans sistemi ile çalışan profesyonel bir sinyal botudur.

## 🚀 Yeni Özellikler v3.0

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

### 📱 Birleştirilmiş Sinyal Mesajları
- **Aynı sembol ve zaman diliminde** birden fazla harf sinyal verirse
- **Tek mesajda** tüm harfler birleştirilir
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

### 📱 Telegram Entegrasyonu
- Anlık sinyal bildirimleri
- Detaylı sinyal bilgileri (MA tipi, tolerans, hesaplama zaman dilimi)
- Periyodik güncelleme mesajları
- Sinyal iptal bildirimleri

## 🛠️ Kurulum

### Gereksinimler
```bash
pip install customtkinter
pip install MetaTrader5
pip install pandas
pip install ta
pip install python-telegram-bot
```

### MT5 Kurulumu
1. MetaTrader 5 terminalini indirin ve kurun
2. Hesabınıza giriş yapın
3. **Ayarlar > Expert Advisors** kısmından **"Allow automated trading"** seçeneğini etkinleştirin
4. Terminali açık tutun

## 📋 Kullanım

### 1. MA/EMA Ayarları
- 25 satırda MA/EMA konfigürasyonları yapın
- Her satır için:
  - **Tip**: MA veya EMA seçin
  - **Periyot**: Sayısal değer girin (1-200)
  - **MA Hesaplama Zaman Dilimi**: 4h, günlük, haftalık, aylık seçin
  - **Sinyal Harfi**: Tek harf girin (A-Z)

### 2. Harf Tolerans Ayarları
- Her harf için ayrı tolerans ayarı
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
├── ozgur_bey.py              # Ana uygulama
├── gui.py                    # GUI bileşenleri
├── ma_config.json            # MA/EMA konfigürasyonları
├── tolerance_config.json     # Harf tolerans ayarları
├── symbols.json              # Özel semboller
├── synthetic_symbols.json    # Çarpım grafikleri
├── signal_cancel_config.json # Sinyal iptal ayarları
├── global_symbols.json       # Tüm semboller (otomatik)
└── README.md                 # Bu dosya
```

## 🔧 Konfigürasyon Dosyaları

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
🔤 Sinyal Harfi: A, B, F
💰 Fiyat: 1.0850

📈 Sinyal Detayları:

📈 YUKARI YÖN:
• A: EMA 1.0800 (Tolerans: %1.0)
• F: MA 1.0750 (Tolerans: %2.0)

📉 AŞAĞI YÖN:
• B: EMA 1.0900 (Tolerans: %1.5)
```

## 🔍 Backtest Sistemi

Bot, algoritmanızı test etmek için kapsamlı bir backtest sistemi içerir. Bu sistem GUI'ye ihtiyaç duymadan çalışır ve 15 günlük geçmiş veri üzerinden sinyal analizi yapar.

### **Backtest Çalıştırma:**

```bash
python ozgur_bey.py --backtest
```

### **Backtest Özellikleri:**

#### **📋 Otomatik Veri Yükleme:**
- **MA/EMA Konfigürasyonları**: `MA_CONFIG.json` dosyasından
- **Tolerans Ayarları**: `TOLERANCE.json` dosyasından (opsiyonel)
- **Sinyal İptal Ayarları**: `SIGNAL_CANCEL.json` dosyasından
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
✅ 5 MA/EMA konfigürasyonu yüklendi
✅ 3 tolerans ayarı yüklendi
✅ Sinyal iptal yüzdesi: %5.0

📈 Sembol listesi oluşturuluyor...
✅ 150 sembol bulundu

📅 Tarih aralığı: 2024-01-15 10:30 - 2024-01-30 10:30

🔍 150 sembol analiz ediliyor...

📊 Sembol 1/150: EURUSD
  ⏰ 1h: 360 mum bulundu
    🚨 SİNYAL: A - Yukarı - alış - 1.0850
    🚨 SİNYAL: B - Aşağı - satış - 1.0845

📊 BACKTEST ÖZET RAPORU
============================================================
📅 Tarih Aralığı: 2024-01-15 10:30 - 2024-01-30 10:30
📈 Analiz Edilen Sembol: 150
⚙️ MA/EMA Konfigürasyonu: 5
🎯 Toplam Sinyal: 1,247

⏰ ZAMAN DİLİMİ BAZINDA SONUÇLAR:
   1h: 456 sinyal (234 alış, 222 satış)
   4h: 298 sinyal (145 alış, 153 satış)
   8h: 234 sinyal (118 alış, 116 satış)
  12h: 156 sinyal ( 78 alış,  78 satış)
   1d: 103 sinyal ( 52 alış,  51 satış)

🏆 EN ÇOK SİNYAL VEREN SEMBOLLER:
   1. EURUSD: 45 sinyal
   2. GBPUSD: 38 sinyal
   3. USDJPY: 32 sinyal

💾 Detaylı sonuçlar: backtest_results_20240130_103045.json
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

Bu backtest sistemi, algoritmanızın performansını değerlendirmek ve optimize etmek için güçlü bir araçtır.

## ⚠️ Önemli Notlar

1. **MT5 Bağlantısı**: Terminal açık ve oturum açılmış olmalı
2. **Sembol Erişimi**: MT5'te sembolün mevcut olduğundan emin olun
3. **Telegram Bot**: Bot token ve chat ID doğru olmalı
4. **Mum Kapanışı**: Bot sadece mum kapanışlarında analiz yapar
5. **Performans**: Optimize edilmiş performans

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
- Bot token doğru mu kontrol edin
- Chat ID doğru mu kontrol edin
- İnternet bağlantısı var mı kontrol edin

## 📈 Performans İpuçları

1. **Sembol Sayısını Sınırlayın**: Çok fazla sembol performansı düşürür
2. **MA Sayısını Azaltın**: Önce az MA ile test edin
3. **Toleransı Artırın**: Daha az sinyal için toleransı artırın
4. **Mum Kapanışı**: Sadece mum kapanışlarında analiz yaparak optimize edilmiş performans

## 🔄 Güncellemeler

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
5. Mum kapanış zamanlarını kontrol edin#   M A - E M A - o k l u - Z a m a n - D i l i m i - S i n y a l  
 