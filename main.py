import customtkinter as ctk
from customtkinter import CTkInputDialog
import json
import os
import MetaTrader5 as mt5
from dotenv import load_dotenv
import pandas as pd
from ta.trend import EMAIndicator, SMAIndicator
from telegram.ext import Application
import asyncio
import threading
import time
import itertools
from datetime import datetime, timedelta
from gui import MAConfigGUI

load_dotenv()

CONFIG_FILE = "ma_config.json"
TOLERANCE_FILE = "tolerance_config.json"
SYMBOLS_FILE = "symbols.json"
SYNTHETIC_FILE = "synthetic_symbols.json"
SIGNAL_CANCEL_FILE = "signal_cancel_config.json"
GLOBAL_SYMBOLS_FILE = "global_symbols.json"

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class MAConfigApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MA / EMA Sinyal Harf Atama ve Bot - Gelişmiş Versiyon")
        self.geometry("900x750")
        
        # Pencereyi ekranın ortasında konumlandır
        width = 900
        height = 750
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

        self.entries = []
        self.bot_running = False
        self.bot_thread = None
        self.mt5_initialized = False
        self.bot_token = os.getenv("BOT_TOKEN")
        self.chat_id = os.getenv("CHAT_ID")
        self.telegram_app = None
        self.harf_to_config = {}
        self.active_signals = {}
        self.synthetic_symbols = {}

        # GUI oluştur
        self.gui = MAConfigGUI(self)
        
        # Dosyaları yükle
        self.load_config()
        self.load_tolerance()
        self.load_synthetic_symbols()
        self.load_signal_cancel_config()
        self.load_symbols_from_file()  # Sembolleri yükle
        self.initialize_telegram()
        
        # Arayüz oluşturulduktan sonra MT5'i başlat
        self.after(100, self.initialize_mt5)

    def show_info(self, message):
        """Başarı mesajını göster"""
        def update_gui():
            if hasattr(self, 'gui') and hasattr(self.gui, 'message_label'):
                self.gui.message_label.configure(text=f"✅ {message}", text_color="green")
        
        # GUI güncellemesini ana thread'de yap
        self.after(0, update_gui)
        print(f"BİLGİ: {message}")  # Console'a da yazdır
        
        # 5 saniye sonra mesajı temizle
        def clear_message():
            if hasattr(self, 'gui') and hasattr(self.gui, 'message_label'):
                self.gui.message_label.configure(text="Sistem hazır...")
        
        self.after(5000, clear_message)

    def show_error(self, message):
        """Hata mesajını göster"""
        def update_gui():
            if hasattr(self, 'gui') and hasattr(self.gui, 'message_label'):
                self.gui.message_label.configure(text=f"❌ HATA: {message}", text_color="red")
        
        # GUI güncellemesini ana thread'de yap
        self.after(0, update_gui)
        print(f"HATA: {message}")  # Console'a da yazdır
        
        # 8 saniye sonra mesajı temizle
        def clear_message():
            if hasattr(self, 'gui') and hasattr(self.gui, 'message_label'):
                self.gui.message_label.configure(text="Sistem hazır...")
        
        self.after(8000, clear_message)
    
    def on_closing(self):
        """Uygulama kapatılırken MT5 bağlantısını kapat"""
        if self.mt5_initialized:
            mt5.shutdown()
        self.destroy()

    def initialize_mt5(self):
        """MT5 bağlantısını başlat"""
        try:
            if not mt5.initialize():
                error_code = mt5.last_error()
                self.show_error(f"MT5 başlatılamadı! Hata kodu: {error_code}\nMT5 terminalinin açık ve çalışır durumda olduğundan, doğru hesapla oturum açıldığından emin olun.\n'Ayarlar > Expert Advisors' kısmından 'Allow automated trading' seçeneğini etkinleştirin.")
                self.mt5_initialized = False
                if hasattr(self, 'gui') and hasattr(self.gui, 'mt5_status_label'):
                    self.gui.mt5_status_label.configure(text="🔴 MT5 Bağlantısı Yok", text_color="red")
            else:
                # MT5 bilgilerini al
                account_info = mt5.account_info()
                if account_info:
                    print(f"MT5 başarıyla başlatıldı - Hesap: {account_info.login}")
                    self.mt5_initialized = True
                    if hasattr(self, 'gui') and hasattr(self.gui, 'mt5_status_label'):
                        self.gui.mt5_status_label.configure(text=f"🟢 MT5 Bağlı - Hesap: {account_info.login}", text_color="green")
                else:
                    # Backtest modu için hesap bilgisi olmasa da devam et
                    print("MT5 başlatıldı ama hesap bilgilerine erişilemedi! (Backtest modu için devam ediliyor)")
                    self.mt5_initialized = True  # Backtest için True yap
                    if hasattr(self, 'gui') and hasattr(self.gui, 'mt5_status_label'):
                        self.gui.mt5_status_label.configure(text="🟡 MT5 Bağlantısı Sorunlu", text_color="orange")
        except Exception as e:
            self.show_error(f"MT5 başlatma hatası: {str(e)}\nMT5 kurulu mu kontrol edin.")
            print(f"MT5 BAŞLATMA HATASI: {e}")
            self.mt5_initialized = False
            if hasattr(self, 'gui') and hasattr(self.gui, 'mt5_status_label'):
                self.gui.mt5_status_label.configure(text="🔴 MT5 Bağlantısı Yok", text_color="red")

    def initialize_telegram(self):
        self.telegram_app = Application.builder().token(self.bot_token).build()

    async def send_telegram_message(self, message):
        try:
            await self.telegram_app.bot.send_message(chat_id=self.chat_id, text=message)
        except Exception as e:
            self.show_error(f"Telegram mesajı gönderilemedi: {str(e)}")
    
    def send_telegram_async(self, message):
        """Telegram mesajını ayrı thread'de gönder"""
        try:
            # Ayrı thread'de Telegram mesajı gönder
            import threading
            def send_message():
                try:
                    asyncio.run(self.send_telegram_message(message))
                except Exception as e:
                    print(f"Telegram thread hatası: {e}")
            
            thread = threading.Thread(target=send_message, daemon=True)
            thread.start()
        except Exception as e:
            print(f"Telegram async gönderme hatası: {e}")

    def save_config(self):
        """Konfigürasyon ayarlarını kaydet"""
        try:
            data = []
            harfler = set()
            self.harf_to_config = {}
            errors = []
            
            # Önce tüm hatları kontrol et
            valid_entries = 0
            for i, entry in enumerate(self.entries):
                tip = entry["tip"].get()
                periyot = entry["periyot"].get().strip()
                ma_timeframe = entry["ma_timeframe"].get()  # MA hesaplama zaman dilimi
                harf = entry["harf"].get().strip().upper()

                # Boş satırları atla
                if harf == "" and periyot == "":
                    continue
                
                valid_entries += 1
                row_num = i + 1

                # Harf kontrolü
                if harf == "":
                    errors.append(f"Satır {row_num}: Sinyal harfi boş olamaz")
                    continue
                if len(harf) != 1 or not harf.isalpha():
                    errors.append(f"Satır {row_num}: Sinyal harfi tek harf olmalı (A-Z)")
                    continue
                if harf in harfler:
                    errors.append(f"Satır {row_num}: '{harf}' harfi zaten kullanılmış")
                    continue
                harfler.add(harf)

                # Periyot kontrolü
                if periyot == "":
                    errors.append(f"Satır {row_num}: Periyot boş olamaz")
                    continue
                if not periyot.isdigit():
                    errors.append(f"Satır {row_num}: Periyot sadece sayı olmalı")
                    continue
                if int(periyot) <= 0:
                    errors.append(f"Satır {row_num}: Periyot pozitif olmalı")
                    continue
                if int(periyot) > 1000:
                    errors.append(f"Satır {row_num}: Periyot çok büyük (max 1000)")
                    continue

                # MA hesaplama zaman dilimi kontrolü
                if ma_timeframe not in ["4h", "günlük", "haftalık", "aylık"]:
                    errors.append(f"Satır {row_num}: Geçersiz MA hesaplama zaman dilimi")

                # Geçerli config oluştur
                config = {
                    "tip": tip,
                    "periyot": int(periyot),
                    "ma_timeframe": ma_timeframe,  # MA hesaplama zaman dilimi
                    "harf": harf
                }
                data.append(config)
                self.harf_to_config[harf] = config

            # Hataları göster
            if errors:
                error_msg = "Şu hatalar bulundu:\n" + "\n".join(errors[:5])  # İlk 5 hatayı göster
                if len(errors) > 5:
                    error_msg += f"\n... ve {len(errors)-5} hata daha"
                self.show_error(error_msg)
                return

            # En az bir geçerli config olmalı
            if len(data) == 0:
                self.show_error("En az bir geçerli konfigürasyon girmelisiniz!")
                return

            # Dosyaya kaydet
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            self.show_info(f"{len(data)} konfigürasyon kaydedildi!")
            self.update_selector_values(data)
            if hasattr(self, 'gui') and hasattr(self.gui, 'config_status_label'):
                self.gui.config_status_label.configure(text=f"📋 Konfigürasyon: {len(data)} ayar", text_color="green")
            
        except Exception as e:
            self.show_error(f"Ayarlar kaydedilirken hata: {str(e)}")
            print(f"KAYDETME HATASI: {e}")  # Debug için

    def update_selector_values(self, data):
        # Artık gerekli değil - kontrol menüleri kaldırıldı
        pass

    def save_tolerances(self):
        """Harf tolerans ayarlarını kaydet"""
        try:
            data = {}
            errors = []
            
            for i, entry in enumerate(self.gui.symbol_tolerance_entries):
                harf = entry["harf"]
                active = entry["active"].get()
                tolerance = entry["tolerance"].get().strip()
                down = entry["down"].get()
                up = entry["up"].get()

                # Aktif değilse atla
                if not active:
                    continue
                
                row_num = i + 1

                # Tolerans kontrolü
                if tolerance == "":
                    errors.append(f"Satır {row_num} ({harf}): Tolerans değeri boş olamaz")
                    continue
                else:
                    try:
                        tolerance_val = float(tolerance)
                        if tolerance_val < 0:
                            errors.append(f"Satır {row_num} ({harf}): Tolerans değeri negatif olamaz")
                            continue
                        elif tolerance_val > 50:
                            errors.append(f"Satır {row_num} ({harf}): Tolerans değeri çok büyük (max %50)")
                            continue
                    except ValueError:
                        errors.append(f"Satır {row_num} ({harf}): Tolerans değeri geçerli bir sayı olmalı")
                        continue

                # En az bir yön seçilmeli
                if not down and not up:
                    errors.append(f"Satır {row_num} ({harf}): En az bir yön seçilmelidir (Aşağı veya Yukarı)")
                    continue

                # Geçerli config oluştur
                data[harf] = {
                    "tolerance": float(tolerance),
                    "down": down,
                    "up": up
                }

            # Hataları göster
            if errors:
                error_msg = "Şu hatalar bulundu:\n" + "\n".join(errors[:5])  # İlk 5 hatayı göster
                if len(errors) > 5:
                    error_msg += f"\n... ve {len(errors)-5} hata daha"
                self.show_error(error_msg)
                return

            # Tolerans ayarı opsiyonel - boş olabilir
            if len(data) == 0:
                # Hiç tolerans ayarı yoksa boş dosya oluştur
                with open(TOLERANCE_FILE, "w", encoding="utf-8") as f:
                    json.dump({}, f, indent=4, ensure_ascii=False)
                
                self.show_info("Tolerans ayarları temizlendi!")
                if hasattr(self, 'gui'):
                    self.gui.tolerance_status_label.configure(text="⚙️ Tolerans: Yok", text_color="gray")
                return

            # Dosyaya kaydet
            with open(TOLERANCE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            self.show_info(f"{len(data)} harf tolerans ayarı kaydedildi!")
            if hasattr(self, 'gui'):
                self.gui.tolerance_status_label.configure(text=f"⚙️ Tolerans: {len(data)} harf", text_color="green")
            
        except Exception as e:
            self.show_error(f"Tolerans kaydetme hatası: {str(e)}")
            print(f"TOLERANS HATASI: {e}")  # Debug için

    def load_tolerance(self):
        try:
            if os.path.exists(TOLERANCE_FILE):
                with open(TOLERANCE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    # Eski format kontrolü (tek tolerans değeri)
                    if isinstance(data, dict) and "tolerance" in data and isinstance(data["tolerance"], (int, float)):
                        # Eski format - tek tolerans değeri
                        tolerance = data.get("tolerance", 0)
                        controls = data.get("controls", ["", ""])
                        directions = data.get("directions", ["Aşağı", "Yukarı"])
                        
                        # Yeni format için dönüştür
                        new_data = {}
                        for i, harf in enumerate(["A", "B", "C", "D", "E"]):
                            if i < len(controls):
                                new_data[harf] = {
                                    "tolerance": float(tolerance),
                                    "down": directions[0] == "Aşağı",
                                    "up": directions[1] == "Yukarı"
                                }
                        
                        # GUI'yi güncelle
                        for i, entry in enumerate(self.gui.symbol_tolerance_entries):
                            if i < 5:  # İlk 5 harf için
                                entry["active"].set(True)
                                entry["tolerance"].delete(0, "end")
                                entry["tolerance"].insert(0, str(tolerance))
                                entry["down"].set(directions[0] == "Aşağı")
                                entry["up"].set(directions[1] == "Yukarı")
                            else:
                                entry["active"].set(False)
                                entry["tolerance"].delete(0, "end")
                                entry["down"].set(False)
                                entry["up"].set(False)
                        
                        # Durum etiketini güncelle
                        if hasattr(self, 'gui'):
                            self.gui.tolerance_status_label.configure(text=f"⚙️ Tolerans: {len(new_data)} harf (eski format)", text_color="green")
                        
                        return new_data
                    else:
                        # Yeni format - harf bazlı toleranslar
                        # Önce tüm alanları temizle
                        for entry in self.gui.symbol_tolerance_entries:
                            entry["active"].set(False)
                            entry["tolerance"].delete(0, "end")
                            entry["down"].set(False)
                            entry["up"].set(False)
                        
                        # Veriyi yükle
                        for harf, config in data.items():
                            # Harf için entry bul
                            for entry in self.gui.symbol_tolerance_entries:
                                if entry["harf"] == harf:
                                    entry["active"].set(True)
                                    entry["tolerance"].insert(0, str(config.get("tolerance", 0)))
                                    entry["down"].set(config.get("down", False))
                                    entry["up"].set(config.get("up", False))
                                    break

                        # Durum etiketini güncelle
                        if hasattr(self, 'gui'):
                            self.gui.tolerance_status_label.configure(text=f"⚙️ Tolerans: {len(data)} harf", text_color="green")

                        return data
            return {}
        except Exception as e:
            self.show_error(f"Tolerans yükleme hatası: {str(e)}")
            return {}

    def selector1_changed(self, value):
        if value == self.gui.selector2.get():
            options = self.gui.selector2.cget("values")
            for opt in options:
                if opt != value:
                    self.gui.selector2.set(opt)
                    break

    def selector2_changed(self, value):
        if value == self.gui.selector1.get():
            options = self.gui.selector1.cget("values")
            for opt in options:
                if opt != value:
                    self.gui.selector1.set(opt)
                    break

    def direction1_changed(self):
        dir1 = self.gui.direction_var1.get()
        self.gui.direction_var2.set("Aşağı" if dir1 == "Yukarı" else "Yukarı")

    def direction2_changed(self):
        dir2 = self.gui.direction_var2.get()
        self.gui.direction_var1.set("Aşağı" if dir2 == "Yukarı" else "Yukarı")

    def toggle_bot(self):
        """Bot'u başlat veya durdur"""
        try:
            if not self.bot_running:
                # Kontroller
                if not os.path.exists(CONFIG_FILE):
                    self.show_error("Önce konfigürasyon ayarlarını kaydedin!")
                    return
                if not self.mt5_initialized:
                    self.show_error("MT5 bağlantısı kurulamadı! MT5'in açık olduğundan emin olun.")
                    return
                if len(self.harf_to_config) == 0:
                    self.show_error("Geçerli konfigürasyon bulunamadı!")
                    return
                
                # Bot'u başlat
                self.bot_running = True
                self.gui.bot_button.configure(text="🛑 Botu Durdur")
                self.gui.status_label.configure(text="🟢 Bot Çalışıyor", text_color="green")
                self.show_info("Bot başlatıldı! Mum kapanış zamanlarını bekleyerek sinyal arıyor...")
                
                self.bot_thread = threading.Thread(target=self.run_bot, daemon=True)
                self.bot_thread.start()
            else:
                # Bot'u durdur
                self.bot_running = False
                self.gui.bot_button.configure(text="▶️ Botu Başlat")
                self.gui.status_label.configure(text="🔴 Bot Durduruldu", text_color="red")
                self.show_info("Bot durduruldu")
                self.bot_thread = None
                
        except Exception as e:
            self.show_error(f"Bot kontrol hatası: {str(e)}")
            print(f"BOT TOGGLE HATASI: {e}")

    def load_config(self):
        """Kayıtlı konfigürasyonu yükle"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                # Önce tüm alanları temizle
                for entry in self.entries:
                    entry["periyot"].delete(0, "end")
                    entry["harf"].delete(0, "end")
                    entry["tip"].set("MA")
                    entry["ma_timeframe"].set("4h")  # Varsayılan MA hesaplama zaman dilimi
                
                # Veriyi yükle
                for i, item in enumerate(data):
                    if i >= len(self.entries):
                        break
                    self.entries[i]["tip"].set(item.get("tip", "MA"))
                    self.entries[i]["periyot"].insert(0, str(item.get("periyot", "")))
                    
                    # Eski format kontrolü (timeframe -> ma_timeframe)
                    if "timeframe" in item:
                        # Eski format - timeframe'i ma_timeframe'e dönüştür
                        old_timeframe = item.get("timeframe", "8h")
                        if old_timeframe == "8h":
                            ma_timeframe = "4h"  # 8h -> 4h dönüşümü
                        else:
                            ma_timeframe = old_timeframe
                    else:
                        ma_timeframe = item.get("ma_timeframe", "4h")
                    
                    self.entries[i]["ma_timeframe"].set(ma_timeframe)
                    self.entries[i]["harf"].insert(0, item.get("harf", ""))
                    
                    if "harf" in item and item["harf"]:
                        # Config'i güncelle
                        updated_item = item.copy()
                        updated_item["ma_timeframe"] = ma_timeframe
                        if "timeframe" in updated_item:
                            del updated_item["timeframe"]
                        self.harf_to_config[item["harf"]] = updated_item
                
                self.update_selector_values(data)
                print(f"Konfigürasyon yüklendi: {len(data)} ayar")
                if hasattr(self, 'gui') and hasattr(self.gui, 'config_status_label'):
                    self.gui.config_status_label.configure(text=f"📋 Konfigürasyon: {len(data)} ayar", text_color="green")
                
        except Exception as e:
            self.show_error(f"Konfigürasyon yükleme hatası: {str(e)}")
            print(f"CONFIG YÜKLEME HATASI: {e}")

    def load_symbols(self):
        if os.path.exists(SYMBOLS_FILE):
            with open(SYMBOLS_FILE, "r") as f:
                return json.load(f)
        return []  # JSON dosyası yoksa boş liste döndür

    def fetch_data(self, symbol, timeframe, limit=100):
        """MT5'den veri çek - Çarpım grafikleri desteği ile"""
        try:
            if not self.mt5_initialized:
                self.show_error("MT5 başlatılmamış!")
                return None
            
            # Timeframe dönüşümü - hem sinyal arama hem MA hesaplama için
            timeframe_dict = {
                # Sinyal arama zaman dilimleri
                "1h": mt5.TIMEFRAME_H1,
                "4h": mt5.TIMEFRAME_H4, 
                "8h": mt5.TIMEFRAME_H8,
                "12h": mt5.TIMEFRAME_H12,
                "1d": mt5.TIMEFRAME_D1,
                # MA hesaplama zaman dilimleri
                "günlük": mt5.TIMEFRAME_D1,
                "haftalık": mt5.TIMEFRAME_W1,
                "aylık": mt5.TIMEFRAME_MN1
            }
            
            mt5_timeframe = timeframe_dict.get(timeframe)
            if mt5_timeframe is None:
                self.show_error(f"Desteklenmeyen timeframe: {timeframe}")
                return None
            
            # Çarpım grafiği kontrolü
            if symbol in self.synthetic_symbols:
                return self.fetch_synthetic_data(symbol, timeframe, limit)
            
            # Normal sembol için veri çek
            # Symbol formatını düzelt
            if '/' in symbol:
                symbol_mt5 = symbol.replace("/", "").replace("USDT", "USD")
            else:
                symbol_mt5 = symbol
            
            # Sembol kontrolünü atla - performans için
            # symbols = mt5.symbols_get()
            # if not any(s.name == symbol_mt5 for s in symbols):
            #     print(f"UYARI: Sembol {symbol_mt5} MT5'te bulunamadı, atlanıyor.")
            #     return None
            
            # Veri çek
            rates = mt5.copy_rates_from_pos(symbol_mt5, mt5_timeframe, 0, limit)
            
            if rates is None or len(rates) == 0:
                print(f"UYARI: MT5'den veri alınamadı ({symbol_mt5}), atlanıyor.")
                return None
            
            # DataFrame'e dönüştür
            df = pd.DataFrame(rates)
            df["timestamp"] = pd.to_datetime(df["time"], unit="s")
            df = df[["timestamp", "open", "high", "low", "close", "tick_volume"]]
            df.rename(columns={"tick_volume": "volume"}, inplace=True)
            
            return df
            
        except Exception as e:
            print(f"Veri çekme hatası ({symbol}): {e}")
            return None

    def fetch_synthetic_data(self, synthetic_name, timeframe, limit=100):
        """Çarpım grafiği verilerini hesapla"""
        try:
            if synthetic_name not in self.synthetic_symbols:
                return None
                
            config = self.synthetic_symbols[synthetic_name]
            symbol1 = config["symbol1"]
            symbol2 = config["symbol2"]
            operation = config["operation"]
            
            # Her iki sembolün verilerini çek
            df1 = self.fetch_data(symbol1, timeframe, limit)
            df2 = self.fetch_data(symbol2, timeframe, limit)
            
            if df1 is None or df2 is None:
                return None
                
            # Çarpım grafiği verilerini hesapla
            synthetic_df = df1.copy()
            
            if operation == "*":
                synthetic_df["close"] = df1["close"] * df2["close"]
                synthetic_df["open"] = df1["open"] * df2["open"]
                synthetic_df["high"] = df1["high"] * df2["high"]
                synthetic_df["low"] = df1["low"] * df2["low"]
            elif operation == "/":
                synthetic_df["close"] = df1["close"] / df2["close"]
                synthetic_df["open"] = df1["open"] / df2["open"]
                synthetic_df["high"] = df1["high"] / df2["high"]
                synthetic_df["low"] = df1["low"] / df2["low"]
            elif operation == "+":
                synthetic_df["close"] = df1["close"] + df2["close"]
                synthetic_df["open"] = df1["open"] + df2["open"]
                synthetic_df["high"] = df1["high"] + df2["high"]
                synthetic_df["low"] = df1["low"] + df2["low"]
            elif operation == "-":
                synthetic_df["close"] = df1["close"] - df2["close"]
                synthetic_df["open"] = df1["open"] - df2["open"]
                synthetic_df["high"] = df1["high"] - df2["high"]
                synthetic_df["low"] = df1["low"] - df2["low"]
            
            return synthetic_df
            
        except Exception as e:
            print(f"Çarpım grafiği veri hesaplama hatası ({synthetic_name}): {e}")
            return None

    def calculate_ma(self, df, ma_type, period):
        if ma_type == "EMA":
            indicator = EMAIndicator(df["close"], window=period)
            return indicator.ema_indicator()
        else:
            indicator = SMAIndicator(df["close"], window=period)
            return indicator.sma_indicator()

    def run_bot(self):
        """Bot ana döngüsü - Mum kapanış zamanlarını bekleyerek çalışır"""
        try:
            # Sembol listesi oluştur (özel semboller dahil)
            symbols = self.generate_symbols_list()
            
            if not os.path.exists(CONFIG_FILE):
                self.show_error("Konfigürasyon dosyası bulunamadı!")
                return
                
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                configs = json.load(f)
                
            tolerance_data = self.load_tolerance()
            cancel_data = self.load_signal_cancel_config()
            
            print(f"Bot başlatıldı: {len(symbols)} sembol, {len(configs)} konfigürasyon")
            print(f"Çarpım grafikleri: {len(self.synthetic_symbols)} adet")
            
            # Sinyal arama zaman dilimleri ve kapanış zamanları
            signal_timeframes = ["1h", "4h", "8h", "12h", "1d"]
            
            # Her zaman dilimi için son kontrol zamanını takip et
            last_check_times = {tf: None for tf in signal_timeframes}
            
            cycle_count = 0
            while self.bot_running:
                cycle_count += 1
                current_time = datetime.now()
                print(f"\n--- Bot Döngüsü {cycle_count} - {current_time.strftime('%Y-%m-%d %H:%M:%S')} ---")
                
                # GUI güncellemesi için event kontrolü
                self.update_idletasks()
                
                # Her zaman dilimi için mum kapanış kontrolü yap
                for signal_timeframe in signal_timeframes:
                    if not self.bot_running:
                        break
                        
                    # Bu zaman dilimi için mum kapanış zamanını kontrol et
                    if self.should_check_timeframe(signal_timeframe, current_time, last_check_times[signal_timeframe]):
                        print(f"  📊 {signal_timeframe} mum kapanışı - Analiz başlıyor...")
                        
                        # Bu zaman dilimi için tüm sembolleri analiz et
                        for i, symbol in enumerate(symbols):
                            if not self.bot_running:
                                break
                                
                            try:
                                # Her 25 sembolden sonra GUI güncelle ve kısa bekle
                                if i % 25 == 0:
                                    print(f"    📈 {i}/{len(symbols)} sembol analiz edildi...")
                                    self.update_idletasks()  # GUI güncelle
                                    time.sleep(0.01)  # 10ms bekle
                                
                                # Sinyal arama zaman diliminde veri çek
                                df_signal = self.fetch_data(symbol, signal_timeframe)
                                
                                if df_signal is None or len(df_signal) < 2:
                                    continue
                                    
                                # Bu sembol için MA değerlerini hesaplama zaman dilimlerinde hesapla
                                ma_values_cache = {}  # {ma_calc_tf: {harf: ma_value}}
                                
                                for config in configs:
                                    ma_calc_timeframe = config["ma_timeframe"]
                                    harf = config["harf"]
                                    ma_type = config["tip"]
                                    period = config["periyot"]
                                    
                                    # Bu zaman dilimi için MA değerlerini hesapla
                                    if ma_calc_timeframe not in ma_values_cache:
                                        ma_values_cache[ma_calc_timeframe] = {}
                                        
                                    # MA hesaplama zaman diliminde veri çek
                                    df_ma = self.fetch_data(symbol, ma_calc_timeframe, limit=200)
                                    
                                    if df_ma is not None and len(df_ma) >= period:
                                        ma_value = self.calculate_ma(df_ma, ma_type, period).iloc[-1]
                                        if not pd.isna(ma_value):
                                            ma_values_cache[ma_calc_timeframe][harf] = ma_value
                                
                                # Bu sembol için hesaplanmış MA değerlerini kullanarak sinyal kontrolü yap
                                signals = self.check_signals_with_cached_ma(
                                    df_signal, 
                                    configs, 
                                    tolerance_data, 
                                    signal_timeframe, 
                                    ma_values_cache
                                )
                                
                                if signals:
                                    current_price = df_signal['close'].iloc[-1]
                                    
                                    # Aynı sembol ve zaman dilimi için sinyalleri grupla
                                    signal_key = f"{symbol}_{signal_timeframe}"
                                    
                                    # Yeni sinyaller ve mevcut sinyaller için ayrı işlem
                                    new_signals = []
                                    existing_signals = []
                                    
                                    for signal in signals:
                                        harf = signal["harf"]
                                        signal_id = f"{signal_key}_{harf}"
                                        
                                        # Yeni sinyal mi?
                                        if signal_id not in self.active_signals:
                                            new_signals.append(signal)
                                            # Yeni sinyal oluştur
                                            self.active_signals[signal_id] = {
                                                "symbol": symbol,
                                                "signal_timeframe": signal_timeframe,
                                                "ma_calculation_timeframe": signal["ma_calculation_timeframe"],
                                                "harf": harf,
                                                "signal_price": current_price,
                                                "ma_value": signal["ma_value"],
                                                "direction": signal["direction"],
                                                "signal_type": signal.get("signal_type", "bilinmiyor"),
                                                "candle_color": signal.get("candle_color", "bilinmiyor"),
                                                "created_time": current_time,
                                                "last_sent": current_time
                                            }
                                        else:
                                            existing_signals.append(signal)
                                    
                                    # Yeni sinyaller varsa tek mesajda birleştir
                                    if new_signals:
                                        # Harfleri birleştir
                                        harfler = [s["harf"] for s in new_signals]
                                        harf_str = ", ".join(harfler)
                                        
                                        # Tek mesaj oluştur
                                        message = self.create_combined_signal_message(
                                            symbol, signal_timeframe, harf_str, new_signals, current_price
                                        )
                                        # Telegram mesajını ayrı thread'de gönder
                                        self.send_telegram_async(message)
                                        # Birleştirilmiş sinyal mesajı
                                        if len(new_signals) > 1:
                                            # Her harfin periyot bilgisini al
                                            harf_periods = []
                                            for signal in new_signals:
                                                harf = signal.get('harf', '')
                                                period = signal.get('period', '')
                                                ma_type = signal.get('ma_type', 'MA')
                                                ma_calc_tf = signal.get('ma_calculation_timeframe', '')
                                                harf_periods.append(f"{harf}({ma_type}{period} {ma_calc_tf})")
                                            
                                            harf_period_str = ", ".join(harf_periods)
                                            print(f"  🚨 YENİ SİNYAL: {symbol} ({signal_timeframe}) - {harf_period_str} ({len(new_signals)} harf)")
                                        else:
                                            print(f"  🚨 YENİ SİNYAL: {symbol} ({signal_timeframe}) - {harf_str} [{new_signals[0]['ma_type']}{new_signals[0].get('period', '')} {new_signals[0]['ma_calculation_timeframe']}]")
                                    
                                    # Mevcut sinyaller için iptal kontrolü
                                    for signal in existing_signals:
                                        harf = signal["harf"]
                                        signal_id = f"{signal_key}_{harf}"
                                        active_signal = self.active_signals[signal_id]
                                        
                                        # Sinyal iptal kontrolü
                                        if self.check_signal_cancellation(
                                            symbol, 
                                            active_signal["signal_price"], 
                                            current_price, 
                                            cancel_data["cancel_percentage"]
                                        ):
                                            # Sinyali iptal et
                                            del self.active_signals[signal_id]
                                            cancel_message = f"❌ SİNYAL İPTAL: {symbol} ({signal_timeframe}) - {harf} - Fiyat %{cancel_data['cancel_percentage']} ilerledi"
                                            # Telegram mesajını ayrı thread'de gönder
                                            self.send_telegram_async(cancel_message)
                                            print(f"  ❌ SİNYAL İPTAL: {symbol} ({signal_timeframe}) - {harf}")
                                        else:
                                            # Sinyal devam ediyor - periyodik mesaj gönder
                                            time_diff = current_time - active_signal["last_sent"]
                                            
                                            # Zaman dilimine göre mesaj gönderme sıklığı
                                            send_interval = self.get_send_interval(signal_timeframe)
                                            
                                            if time_diff >= send_interval:
                                                # Periyodik mesaj gönder
                                                message = self.create_periodic_message(signal_id, current_price)
                                                # Telegram mesajını ayrı thread'de gönder
                                                self.send_telegram_async(message)
                                                self.active_signals[signal_id]["last_sent"] = current_time
                                                print(f"  📢 PERİYODİK: {symbol} ({signal_timeframe}) - {harf}")
                                
                            except Exception as e:
                                print(f"  ❌ {symbol} analiz hatası: {e}")
                                continue
                        
                        # Bu zaman dilimi için kontrol zamanını güncelle
                        last_check_times[signal_timeframe] = current_time
                        print(f"  ✅ {signal_timeframe} analizi tamamlandı")
                
                # Eski sinyalleri temizle (24 saatten eski)
                self.cleanup_old_signals()
                
                if self.bot_running:
                    # Kısa bir bekleme süresi (30 saniye)
                    print(f"Bot {cycle_count}. döngüyü tamamladı. 30 saniye bekleniyor...")
                    time.sleep(30)  # 30 saniye bekle
                    
        except Exception as e:
            self.show_error(f"Bot çalışma hatası: {str(e)}")
            print(f"BOT ÇALIŞMA HATASI: {e}")
            self.toggle_bot()  # Bot'u durdur

    def get_send_interval(self, timeframe):
        """Zaman dilimine göre mesaj gönderme aralığı"""
        intervals = {
            "1h": timedelta(hours=1),
            "4h": timedelta(hours=4),
            "8h": timedelta(hours=8),
            "12h": timedelta(hours=12),
            "1d": timedelta(hours=24)
        }
        return intervals.get(timeframe, timedelta(hours=8))

    def create_signal_message(self, signal_id, signal, current_price):
        """Sinyal mesajı oluştur - yeni sinyal mantığı"""
        active_signal = self.active_signals[signal_id]
        symbol = active_signal["symbol"]
        signal_timeframe = active_signal["signal_timeframe"]
        ma_calculation_timeframe = active_signal["ma_calculation_timeframe"]
        harf = active_signal["harf"]
        direction = active_signal["direction"]
        ma_value = active_signal["ma_value"]
        
        # MA tipini, tolerans bilgisini ve sinyal tipini al
        ma_type = signal.get('ma_type', 'MA')
        tolerance_info = ""
        if 'tolerance' in signal:
            tolerance_info = f"\n📊 Tolerans: %{signal['tolerance']:.1f}"
        
        # Sinyal tipini belirle
        signal_type = signal.get('signal_type', 'bilinmiyor')
        candle_color = signal.get('candle_color', 'bilinmiyor')
        
        signal_type_emoji = "🟢" if signal_type == "alış" else "🔴"
        
        message = f"""🚨 YENİ SİNYAL ALARMİ!

📊 Sembol: {symbol}
⏰ Sinyal Zaman Dilimi: {signal_timeframe}
📈 MA Hesaplama Zaman Dilimi: {ma_calculation_timeframe}
🔤 Sinyal Harfi: {harf}
{signal_type_emoji} Sinyal Tipi: {signal_type.upper()} ({candle_color} mum)
💰 Fiyat: {current_price:.4f}
📊 {ma_type} Değeri: {ma_value:.4f}{tolerance_info}
🕐 Zaman: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⚠️ Bu sinyal aktif kalacak ve periyodik olarak güncellenecektir."""
        
        return message

    def create_periodic_message(self, signal_id, current_price):
        """Periyodik sinyal mesajı oluştur"""
        active_signal = self.active_signals[signal_id]
        symbol = active_signal["symbol"]
        signal_timeframe = active_signal["signal_timeframe"]
        ma_calculation_timeframe = active_signal["ma_calculation_timeframe"]
        harf = active_signal["harf"]
        direction = active_signal["direction"]
        signal_price = active_signal["signal_price"]
        
        # Fiyat değişimi hesapla
        price_change = ((current_price - signal_price) / signal_price) * 100
        
        message = f"""📢 SİNYAL GÜNCELLEME

📊 Sembol: {symbol}
⏰ Sinyal Zaman Dilimi: {signal_timeframe}
📈 MA Hesaplama Zaman Dilimi: {ma_calculation_timeframe}
🔤 Sinyal Harfi: {harf}
📈 Yön: {direction}
💰 Mevcut Fiyat: {current_price:.4f}
📊 Sinyal Fiyatı: {signal_price:.4f}
📈 Değişim: {price_change:+.2f}%
🕐 Zaman: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        return message

    def cleanup_old_signals(self):
        """24 saatten eski sinyalleri temizle"""
        try:
            current_time = datetime.now()
            old_signals = []
            
            for signal_id, signal_data in self.active_signals.items():
                age = current_time - signal_data["created_time"]
                if age > timedelta(hours=24):
                    old_signals.append(signal_id)
            
            for signal_id in old_signals:
                del self.active_signals[signal_id]
                
            if old_signals:
                print(f"  🧹 {len(old_signals)} eski sinyal temizlendi")
                
        except Exception as e:
            print(f"Sinyal temizleme hatası: {e}")

    def create_ma_config_tab(self):
        """MA/EMA konfigürasyon tab'ını oluştur"""
        # Arayüz: Scrollable Frame
        self.scroll_frame = ctk.CTkScrollableFrame(self.ma_tab, width=450, height=400)
        self.scroll_frame.pack(pady=5, fill="both", expand=True)

        headers = ["No", "Tip (MA/EMA)", "Periyot", "Zaman Dilimi", "Sinyal Harfi"]
        for col, text in enumerate(headers):
            label = ctk.CTkLabel(self.scroll_frame, text=text, font=("Arial", 12, "bold"))
            label.grid(row=0, column=col, padx=5, pady=3)

        self.timeframes = ["8h"]  # Sadece 8h zaman dilimi
        for i in range(25):
            ctk.CTkLabel(self.scroll_frame, text=str(i+1)).grid(row=i+1, column=0, padx=5, pady=2)
            tip_option = ctk.CTkOptionMenu(self.scroll_frame, values=["MA", "EMA"], width=100)
            tip_option.grid(row=i+1, column=1, padx=5, pady=2)
            period_entry = ctk.CTkEntry(self.scroll_frame, width=80)
            period_entry.grid(row=i+1, column=2, padx=5, pady=2)
            timeframe_option = ctk.CTkOptionMenu(self.scroll_frame, values=self.timeframes, width=100)
            timeframe_option.grid(row=i+1, column=3, padx=5, pady=2)
            harf_entry = ctk.CTkEntry(self.scroll_frame, width=80)
            harf_entry.grid(row=i+1, column=4, padx=5, pady=2)
            self.entries.append({
                "tip": tip_option,
                "periyot": period_entry,
                "timeframe": timeframe_option,
                "harf": harf_entry
            })

        # Kaydet butonu
        self.save_button = ctk.CTkButton(self.ma_tab, text="📝 MA/EMA Konfigürasyonu Kaydet", command=self.save_config)
        self.save_button.pack(pady=5)

        # Tolerans ayarları
        self.tolerance_frame = ctk.CTkFrame(self.ma_tab)
        self.tolerance_frame.pack(pady=5, fill="x")

        self.tolerance_label = ctk.CTkLabel(self.tolerance_frame, text="Tolerans Ayarları", font=("Arial", 14, "bold"))
        self.tolerance_label.pack(pady=3)

        self.tolerance_entry = ctk.CTkEntry(self.tolerance_frame, placeholder_text="Tolerans %", width=150)
        self.tolerance_entry.pack(pady=3)

        self.selector_frame = ctk.CTkFrame(self.tolerance_frame)
        self.selector_frame.pack(pady=3)

        self.selector1 = ctk.CTkOptionMenu(self.selector_frame, values=[], width=100, command=self.selector1_changed)
        self.selector1.grid(row=0, column=0, padx=5)
        self.selector2 = ctk.CTkOptionMenu(self.selector_frame, values=[], width=100, command=self.selector2_changed)
        self.selector2.grid(row=0, column=1, padx=5)

        self.direction_var1 = ctk.StringVar(value="Aşağı")
        self.down_radio1 = ctk.CTkRadioButton(self.selector_frame, text="Aşağı", variable=self.direction_var1, value="Aşağı", command=self.direction1_changed)
        self.up_radio1 = ctk.CTkRadioButton(self.selector_frame, text="Yukarı", variable=self.direction_var1, value="Yukarı", command=self.direction1_changed)
        self.down_radio1.grid(row=1, column=0, pady=3)
        self.up_radio1.grid(row=2, column=0, pady=3)

        self.direction_var2 = ctk.StringVar(value="Yukarı")
        self.down_radio2 = ctk.CTkRadioButton(self.selector_frame, text="Aşağı", variable=self.direction_var2, value="Aşağı", command=self.direction2_changed)
        self.up_radio2 = ctk.CTkRadioButton(self.selector_frame, text="Yukarı", variable=self.direction_var2, value="Yukarı", command=self.direction2_changed)
        self.down_radio2.grid(row=1, column=1, pady=3)
        self.up_radio2.grid(row=2, column=1, pady=3)

        self.save_tolerance_button = ctk.CTkButton(self.tolerance_frame, text="⚙️ Toleransları Kaydet", command=self.save_tolerances)
        self.save_tolerance_button.pack(pady=5)

    def create_symbols_tab(self):
        """Sembol yönetimi tab'ını oluştur"""
        # Başlık
        title_label = ctk.CTkLabel(self.symbols_tab, text="Sembol Yönetimi", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Açıklama
        desc_label = ctk.CTkLabel(self.symbols_tab, text="Analiz edilecek sembolleri ekleyin veya silin", font=("Arial", 12))
        desc_label.pack(pady=5)
        
        # Sembol ekleme frame'i
        add_frame = ctk.CTkFrame(self.symbols_tab)
        add_frame.pack(pady=10, fill="x", padx=10)
        
        # Sembol ekleme
        symbol_frame = ctk.CTkFrame(add_frame)
        symbol_frame.pack(pady=5, fill="x")
        
        ctk.CTkLabel(symbol_frame, text="Sembol Adı:").grid(row=0, column=0, padx=5, pady=5)
        self.symbol_entry = ctk.CTkEntry(symbol_frame, placeholder_text="EURUSD", width=150)
        self.symbol_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Ekle butonu
        add_button = ctk.CTkButton(add_frame, text="➕ Sembol Ekle", command=self.add_custom_symbol)
        add_button.pack(pady=5)
        
        # Mevcut semboller listesi
        list_frame = ctk.CTkFrame(self.symbols_tab)
        list_frame.pack(pady=10, fill="both", expand=True, padx=10)
        
        ctk.CTkLabel(list_frame, text="Mevcut Semboller:", font=("Arial", 14, "bold")).pack(pady=5)
        
        # Textbox kullan (tıklanabilir liste için farklı yaklaşım)
        self.symbols_listbox = ctk.CTkTextbox(list_frame, height=300)
        self.symbols_listbox.pack(pady=5, fill="both", expand=True, padx=10)
        
        # Sil butonu
        delete_button = ctk.CTkButton(list_frame, text="🗑️ Seçili Sembolü Sil", command=self.delete_custom_symbol)
        delete_button.pack(pady=5)
        
        self.update_symbols_list()

    def add_custom_symbol(self):
        """Sembol ekle"""
        try:
            symbol = self.gui.symbol_entry.get().strip().upper()
            
            if not symbol:
                self.show_error("Sembol adı boş olamaz!")
                return
                
            symbols = self.load_symbols()
            
            if symbol in symbols:
                self.show_error("Bu sembol zaten mevcut!")
                return
                
            symbols.append(symbol)
            self.save_symbols(symbols)
            self.update_symbols_list()
            self.show_info(f"Sembol eklendi: {symbol}")
            
            self.gui.symbol_entry.delete(0, "end")
            
        except Exception as e:
            self.show_error(f"Sembol ekleme hatası: {str(e)}")

    def delete_custom_symbol(self):
        """Seçili sembolü sil"""
        try:
            try:
                selected = self.gui.symbols_listbox.get("sel.first", "sel.last")
            except:
                selected = ""
            
            if not selected:
                all_text = self.gui.symbols_listbox.get("0.0", "end").strip()
                if not all_text:
                    self.show_error("Silinecek sembol bulunamadı!")
                    return
                
                dialog = ctk.CTkInputDialog(text="Silinecek sembol adını girin:", title="Sembol Sil")
                symbol = dialog.get_input()
                
                if not symbol:
                    return
            else:
                symbol = selected.strip()
            
            symbol = symbol.split(":")[0].strip() if ":" in symbol else symbol.strip()
            symbol = symbol.upper()
            
            symbols = self.load_symbols()
            
            if symbol in symbols:
                symbols.remove(symbol)
                self.save_symbols(symbols)
                self.update_symbols_list()
                self.show_info(f"Sembol silindi: {symbol}")
            else:
                self.show_error("Bu sembol bulunamadı!")
                
        except Exception as e:
            self.show_error(f"Sembol silme hatası: {str(e)}")

    def update_symbols_list(self):
        """Semboller listesini güncelle"""
        self.gui.symbols_listbox.delete("0.0", "end")
        symbols = self.load_symbols()
        for symbol in symbols:
            self.gui.symbols_listbox.insert("end", symbol + "\n")

    def create_synthetic_tab(self):
        """Çarpım grafikleri tab'ını oluştur"""
        # Başlık
        title_label = ctk.CTkLabel(self.synthetic_tab, text="Çarpım Grafikleri (Sentetik Enstrümanlar)", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Açıklama
        desc_label = ctk.CTkLabel(self.synthetic_tab, text="EURUSD*EURGBP gibi çarpım grafikleri oluşturun", font=("Arial", 12))
        desc_label.pack(pady=5)
        
        # Çarpım grafiği ekleme frame'i
        add_frame = ctk.CTkFrame(self.synthetic_tab)
        add_frame.pack(pady=10, fill="x", padx=10)
        
        # Sembol seçimi
        symbol_frame = ctk.CTkFrame(add_frame)
        symbol_frame.pack(pady=5, fill="x")
        
        ctk.CTkLabel(symbol_frame, text="Sembol 1:").grid(row=0, column=0, padx=5, pady=5)
        self.symbol1_entry = ctk.CTkEntry(symbol_frame, placeholder_text="EURUSD", width=100)
        self.symbol1_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(symbol_frame, text="İşlem:").grid(row=0, column=2, padx=5, pady=5)
        self.operation_var = ctk.StringVar(value="*")
        operation_menu = ctk.CTkOptionMenu(symbol_frame, values=["*", "/", "+", "-"], variable=self.operation_var, width=60)
        operation_menu.grid(row=0, column=3, padx=5, pady=5)
        
        ctk.CTkLabel(symbol_frame, text="Sembol 2:").grid(row=0, column=4, padx=5, pady=5)
        self.symbol2_entry = ctk.CTkEntry(symbol_frame, placeholder_text="EURGBP", width=100)
        self.symbol2_entry.grid(row=0, column=5, padx=5, pady=5)
        
        ctk.CTkLabel(symbol_frame, text="Sembol Adı:").grid(row=0, column=6, padx=5, pady=5)
        self.synthetic_name_entry = ctk.CTkEntry(symbol_frame, placeholder_text="EURUSD_EURGBP_MULT", width=150)
        self.synthetic_name_entry.grid(row=0, column=7, padx=5, pady=5)
        
        # Ekle butonu
        add_button = ctk.CTkButton(add_frame, text="➕ Çarpım Grafiği Ekle", command=self.add_synthetic_symbol)
        add_button.pack(pady=5)
        
        # Mevcut çarpım grafikleri listesi
        list_frame = ctk.CTkFrame(self.synthetic_tab)
        list_frame.pack(pady=10, fill="both", expand=True, padx=10)
        
        ctk.CTkLabel(list_frame, text="Mevcut Çarpım Grafikleri:", font=("Arial", 14, "bold")).pack(pady=5)
        
        # Textbox kullan (tıklanabilir liste için farklı yaklaşım)
        self.synthetic_listbox = ctk.CTkTextbox(list_frame, height=300)
        self.synthetic_listbox.pack(pady=5, fill="both", expand=True, padx=10)
        
        # Sil butonu
        delete_button = ctk.CTkButton(list_frame, text="🗑️ Seçili Çarpım Grafiğini Sil", command=self.delete_synthetic_symbol)
        delete_button.pack(pady=5)

    def create_signal_cancel_tab(self):
        """Sinyal iptal ve filtre ayarları tab'ını oluştur"""
        # Başlık
        title_label = ctk.CTkLabel(self.cancel_tab, text="Sinyal İptal & Filtre Ayarları", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Sinyal İptal Bölümü
        cancel_frame = ctk.CTkFrame(self.cancel_tab)
        cancel_frame.pack(pady=10, fill="x", padx=10)
        
        ctk.CTkLabel(cancel_frame, text="🛑 Sinyal İptal Ayarları", font=("Arial", 14, "bold")).pack(pady=5)
        ctk.CTkLabel(cancel_frame, text="Fiyat belirli bir yüzde ilerlediğinde sinyal iptal edilir", font=("Arial", 12)).pack(pady=5)
        
        ctk.CTkLabel(cancel_frame, text="Sinyal İptal Yüzdesi (%):").pack(pady=5)
        self.cancel_percentage_entry = ctk.CTkEntry(cancel_frame, placeholder_text="5.0", width=150)
        self.cancel_percentage_entry.pack(pady=5)
        
        # Filtre Bölümü
        filter_frame = ctk.CTkFrame(self.cancel_tab)
        filter_frame.pack(pady=10, fill="x", padx=10)
        
        ctk.CTkLabel(filter_frame, text="🔍 Sinyal Filtre Ayarları", font=("Arial", 14, "bold")).pack(pady=5)
        ctk.CTkLabel(filter_frame, text="MQL5 v5 algoritması için sinyal filtre periyodu", font=("Arial", 12)).pack(pady=5)
        
        ctk.CTkLabel(filter_frame, text="Filtre Periyodu (Mum Sayısı):").pack(pady=5)
        self.filter_period_entry = ctk.CTkEntry(filter_frame, placeholder_text="5", width=150)
        self.filter_period_entry.pack(pady=5)
        
        # Kaydet butonu
        save_cancel_button = ctk.CTkButton(self.cancel_tab, text="💾 Tüm Ayarları Kaydet", command=self.save_signal_cancel_config)
        save_cancel_button.pack(pady=10)

    def create_right_panel(self):
        """Sağ panel oluştur"""
        # Sağ taraf başlık
        self.right_title = ctk.CTkLabel(self.right_frame, text="📢 Bildirimler ve Durum", font=("Arial", 16, "bold"))
        self.right_title.pack(pady=10)
        
        # Mesaj etiketi (hata/bilgi mesajları için)
        self.message_label = ctk.CTkLabel(self.right_frame, text="Sistem hazır...", text_color="blue", wraplength=280, justify="left", height=100)
        self.message_label.pack(pady=10, padx=10, anchor="w", fill="y")
        
        # MT5 durum bilgisi
        self.mt5_status_label = ctk.CTkLabel(self.right_frame, text="🔴 MT5 Bağlantısı Yok", text_color="red", wraplength=280)
        self.mt5_status_label.pack(pady=5, padx=10, anchor="w")
        
        # Konfigürasyon bilgisi
        self.config_status_label = ctk.CTkLabel(self.right_frame, text="📋 Konfigürasyon: 0 ayar", text_color="gray", wraplength=280)
        self.config_status_label.pack(pady=5, padx=10, anchor="w")
        
        # Tolerans bilgisi
        self.tolerance_status_label = ctk.CTkLabel(self.right_frame, text="⚙️ Tolerans: Ayarlanmamış", text_color="gray", wraplength=280)
        self.tolerance_status_label.pack(pady=5, padx=10, anchor="w")
        
        # Çarpım grafikleri bilgisi
        self.synthetic_status_label = ctk.CTkLabel(self.right_frame, text="🔗 Çarpım Grafikleri: 0 adet", text_color="gray", wraplength=280)
        self.synthetic_status_label.pack(pady=5, padx=10, anchor="w")
        
        # İptal ayarları bilgisi
        self.cancel_status_label = ctk.CTkLabel(self.right_frame, text="❌ İptal: Ayarlanmamış", text_color="gray", wraplength=280)
        self.cancel_status_label.pack(pady=5, padx=10, anchor="w")
        
        # Bot başlat/durdur butonu
        self.button_frame = ctk.CTkFrame(self.right_frame)
        self.button_frame.pack(fill="x", pady=10, padx=10)
        self.bot_button = ctk.CTkButton(self.button_frame, text="▶️ Botu Başlat", command=self.toggle_bot)
        self.bot_button.pack(fill="x")

        # Durum etiketi
        self.status_label = ctk.CTkLabel(self.right_frame, text="🔴 Bot Durduruldu", text_color="red")
        self.status_label.pack(pady=5)

    def add_synthetic_symbol(self):
        """Çarpım grafiği ekle"""
        try:
            symbol1 = self.gui.symbol1_entry.get().strip().upper()
            symbol2 = self.gui.symbol2_entry.get().strip().upper()
            operation = "*"  # Otomatik olarak * işlemi
            synthetic_name = self.gui.synthetic_name_entry.get().strip().upper()
            
            if not all([symbol1, symbol2, synthetic_name]):
                self.show_error("Tüm alanları doldurun!")
                return
                
            if synthetic_name in self.synthetic_symbols:
                self.show_error("Bu isimde bir çarpım grafiği zaten var!")
                return
                
            self.synthetic_symbols[synthetic_name] = {
                "symbol1": symbol1,
                "symbol2": symbol2,
                "operation": operation,
                "formula": f"{symbol1}{operation}{symbol2}"
            }
            
            self.save_synthetic_symbols()
            self.update_synthetic_list()
            self.update_global_symbols()  # Global sembolleri güncelle
            self.show_info(f"Çarpım grafiği eklendi: {synthetic_name}")
            
            # Alanları temizle
            self.gui.symbol1_entry.delete(0, "end")
            self.gui.symbol2_entry.delete(0, "end")
            self.gui.synthetic_name_entry.delete(0, "end")
            
        except Exception as e:
            self.show_error(f"Çarpım grafiği ekleme hatası: {str(e)}")

    def delete_synthetic_symbol(self):
        """Seçili çarpım grafiğini sil"""
        try:
            try:
                selected = self.gui.synthetic_listbox.get("sel.first", "sel.last")
            except:
                selected = ""
            
            if not selected:
                all_text = self.gui.synthetic_listbox.get("0.0", "end").strip()
                if not all_text:
                    self.show_error("Silinecek çarpım grafiği bulunamadı!")
                    return
                
                dialog = ctk.CTkInputDialog(text="Silinecek çarpım grafiği adını girin:", title="Çarpım Grafiği Sil")
                synthetic_name = dialog.get_input()
                
                if not synthetic_name:
                    return
            else:
                synthetic_name = selected.strip()
            
            synthetic_name = synthetic_name.split(":")[0].strip() if ":" in synthetic_name else synthetic_name.strip()
            synthetic_name = synthetic_name.upper()
            
            if synthetic_name in self.synthetic_symbols:
                del self.synthetic_symbols[synthetic_name]
                self.save_synthetic_symbols()
                self.update_synthetic_list()
                self.update_global_symbols()  # Global sembolleri güncelle
                self.show_info(f"Çarpım grafiği silindi: {synthetic_name}")
            else:
                self.show_error("Bu çarpım grafiği bulunamadı!")
                
        except Exception as e:
            self.show_error(f"Çarpım grafiği silme hatası: {str(e)}")

    def update_synthetic_list(self):
        """Çarpım grafikleri listesini güncelle"""
        self.gui.synthetic_listbox.delete("0.0", "end")
        for name, config in self.synthetic_symbols.items():
            self.gui.synthetic_listbox.insert("end", f"{name}: {config['formula']}\n")

    def save_synthetic_symbols(self):
        """Çarpım grafiklerini kaydet"""
        try:
            with open(SYNTHETIC_FILE, "w", encoding="utf-8") as f:
                json.dump(self.synthetic_symbols, f, indent=4, ensure_ascii=False)
            if hasattr(self, 'gui') and hasattr(self.gui, 'synthetic_status_label'):
                self.gui.synthetic_status_label.configure(text=f"🔗 Çarpım Grafikleri: {len(self.synthetic_symbols)} adet", text_color="green")
        except Exception as e:
            self.show_error(f"Çarpım grafikleri kaydetme hatası: {str(e)}")

    def load_synthetic_symbols(self):
        """Çarpım grafiklerini yükle"""
        try:
            if os.path.exists(SYNTHETIC_FILE):
                with open(SYNTHETIC_FILE, "r", encoding="utf-8") as f:
                    self.synthetic_symbols = json.load(f)
                if hasattr(self, 'gui') and hasattr(self.gui, 'synthetic_status_label'):
                    self.gui.synthetic_status_label.configure(text=f"🔗 Çarpım Grafikleri: {len(self.synthetic_symbols)} adet", text_color="green")
                    self.update_synthetic_list()
        except Exception as e:
            self.show_error(f"Çarpım grafikleri yükleme hatası: {str(e)}")
            self.synthetic_symbols = {}

    def save_signal_cancel_config(self):
        """Sinyal iptal ve filtre ayarlarını kaydet"""
        try:
            cancel_percentage = float(self.gui.cancel_percentage_entry.get())
            filter_period = int(self.gui.filter_period_entry.get())
            
            config = {
                "cancel_percentage": cancel_percentage,
                "filter_period": filter_period
            }
            
            with open(SIGNAL_CANCEL_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
                
            if hasattr(self, 'gui') and hasattr(self.gui, 'cancel_status_label'):
                self.gui.cancel_status_label.configure(text=f"❌ İptal: %{cancel_percentage} | 🔍 Filtre: {filter_period}", text_color="green")
            self.show_info(f"Sinyal iptal ve filtre ayarları kaydedildi: İptal %{cancel_percentage}, Filtre {filter_period}")
            
        except Exception as e:
            self.show_error(f"Sinyal iptal ve filtre ayarları kaydetme hatası: {str(e)}")

    def load_signal_cancel_config(self):
        """Sinyal iptal ve filtre ayarlarını yükle"""
        try:
            if os.path.exists(SIGNAL_CANCEL_FILE):
                with open(SIGNAL_CANCEL_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                cancel_percentage = config.get("cancel_percentage", 5.0)
                filter_period = config.get("filter_period", 5)
                
                self.gui.cancel_percentage_entry.delete(0, "end")
                self.gui.cancel_percentage_entry.insert(0, str(cancel_percentage))
                
                self.gui.filter_period_entry.delete(0, "end")
                self.gui.filter_period_entry.insert(0, str(filter_period))
                
                if hasattr(self, 'gui') and hasattr(self.gui, 'cancel_status_label'):
                    self.gui.cancel_status_label.configure(text=f"❌ İptal: %{cancel_percentage} | 🔍 Filtre: {filter_period}", text_color="green")
                    
        except Exception as e:
            self.show_error(f"Sinyal iptal ve filtre ayarları yükleme hatası: {str(e)}")

    def generate_symbols_list(self):
        """Analiz edilecek sembol listesini oluştur"""
        symbols = self.load_symbols()
        synthetic_names = list(self.synthetic_symbols.keys())
        return symbols + synthetic_names

    def calculate_synthetic_price(self, symbol1, symbol2, operation):
        """Çarpım grafiği fiyatını hesapla"""
        try:
            # Her iki sembolün güncel fiyatını al
            price1 = self.get_current_price(symbol1)
            price2 = self.get_current_price(symbol2)
            
            if price1 is None or price2 is None:
                return None
                
            # İşlemi uygula
            if operation == "*":
                return price1 * price2
            elif operation == "/":
                return price1 / price2 if price2 != 0 else None
            elif operation == "+":
                return price1 + price2
            elif operation == "-":
                return price1 - price2
            else:
                return None
                
        except Exception as e:
            print(f"Çarpım grafiği hesaplama hatası: {e}")
            return None

    def get_current_price(self, symbol):
        """Sembolün güncel fiyatını al"""
        try:
            if not self.mt5_initialized:
                return None
                
            # MT5'ten son fiyatı al
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                return (tick.bid + tick.ask) / 2
            return None
            
        except Exception as e:
            print(f"Fiyat alma hatası ({symbol}): {e}")
            return None

    def check_signal_cancellation(self, symbol, signal_price, current_price, cancel_percentage):
        """Gelişmiş sinyal iptal kontrolü - fiyat ilerlediğinde iptal, geri çekilirse devam"""
        try:
            if signal_price is None or current_price is None:
                return False
                
            # Fiyat değişimi hesapla
            price_change = ((current_price - signal_price) / signal_price) * 100
            
            # Eğer fiyat iptal yüzdesini geçtiyse sinyal iptal
            if abs(price_change) >= cancel_percentage:
                return True
                
            return False
            
        except Exception as e:
            print(f"Sinyal iptal kontrolü hatası: {e}")
            return False

    def check_signals_with_cached_ma(self, df, configs, tolerance_data, signal_timeframe, ma_values_cache, filter_period=None):
        """
        MQL5 MABounceSignal_v5 algoritması birebir Python'a çevrilmiş hali:
        
        Alış Sinyali Kuralı:
        1. Test Mumu (bir önceki mum):
           a) MA'nın üstünde açılır
           b) Fitiliyle MA'nın altına sarkar (delme)
           c) Tekrar MA'nın üstünde kapanır (güçlü reddetme)
        2. Onay Mumu (mevcut mum):
           a) Bir yükseliş mumudur
           b) Test mumunun en yüksek seviyesinin üzerinde kapanır (güçlü teyit)
        3. Filtre Kuralı (YENİ):
           a) Son 5 mum içinde MA altında kapanış olmamalı
        
        Satış Sinyali Kuralı:
        1. Test Mumu (bir önceki mum):
           a) MA'nın altında açılır
           b) Fitiliyle MA'nın üstüne çıkar (delme)
           c) Tekrar MA'nın altında kapanır (güçlü reddetme)
        2. Onay Mumu (mevcut mum):
           a) Bir düşüş mumudur
           b) Test mumunun en düşük seviyesinin altında kapanır (güçlü teyit)
        3. Filtre Kuralı (YENİ):
           a) Son 5 mum içinde MA üstünde kapanış olmamalı
        """
        signals = []

        # MQL5 v5: inpFilterPeriod + 2 mum gerekli (5 + 2 = 7)
        if len(df) < 7:
            return signals

        # Son iki mumun verilerini al
        test_candle = df.iloc[-2]  # Test Mumu (bir önceki mum)
        confirm_candle = df.iloc[-1]  # Onay Mumu (mevcut mum)
        
        # Test mumu verileri
        test_open = test_candle["open"]
        test_high = test_candle["high"]
        test_low = test_candle["low"]
        test_close = test_candle["close"]
        
        # Onay mumu verileri
        confirm_open = confirm_candle["open"]
        confirm_close = confirm_candle["close"]
        
        # Mum renklerini belirle
        test_is_green = test_close >= test_open
        confirm_is_green = confirm_close >= confirm_open

        # MQL5 v5 Filtre Periyodu - parametre veya config'den al veya varsayılan 5
        if filter_period is None:
            filter_period = 5  # Varsayılan değer
            if hasattr(self, 'gui') and hasattr(self.gui, 'filter_period_entry'):
                try:
                    filter_period = int(self.gui.filter_period_entry.get())
                except:
                    filter_period = 5  # Hata durumunda varsayılan

        # Bu mum için sinyal veren MA'ları bul
        buy_signals = []
        sell_signals = []
        
        for config in configs:
            ma_type = config["tip"]  # MA veya EMA
            period = config["periyot"]
            harf = config["harf"]
            ma_calculation_timeframe = config["ma_timeframe"]

            # Bu harf için tolerans ayarı var mı?
            harf_tolerance = tolerance_data.get(harf, {})
            
            # Cache'den MA değerini al
            original_ma_value = ma_values_cache.get(ma_calculation_timeframe, {}).get(harf)
            
            if original_ma_value is None or pd.isna(original_ma_value):
                continue
                
            # Tolerans ayarı varsa uygula
            if harf_tolerance and harf_tolerance.get("active", True):
                tolerance = harf_tolerance.get("tolerance", 0) / 100
                down_enabled = harf_tolerance.get("down", False)
                up_enabled = harf_tolerance.get("up", False)
                
                # Tolerans uygulanmış MA değerlerini hesapla
                if down_enabled:
                    ma_value = original_ma_value * (1 - tolerance)
                elif up_enabled:
                    ma_value = original_ma_value * (1 + tolerance)
                else:
                    ma_value = original_ma_value
            else:
                # Tolerans yoksa orijinal MA değerini kullan
                ma_value = original_ma_value

            # MQL5 MABounceSignal_v5 algoritması birebir uygulama
            # Alış Sinyali Koşulları
            bullish_rejection_candle = (test_open > ma_value and test_low < ma_value and test_close > ma_value)
            bullish_confirmation_candle = (confirm_close > confirm_open and confirm_close > test_high)

            if bullish_rejection_candle and bullish_confirmation_candle:
                # --- FİLTRE KONTROLÜ (MQL5 v5 YENİ KURAL) ---
                is_signal_valid = True
                # Son 'filter_period' muma bak, MA altında kapanış var mı?
                for k in range(1, filter_period + 1):
                    if len(df) <= k + 1:  # +1 çünkü -1 onay mumu, -2 test mumu
                        continue
                    
                    # k. mumun kapanış fiyatı (test mumundan önceki mumlar)
                    candle_close = df.iloc[-(k+2)]["close"]  # -k-2 çünkü -1 onay mumu, -2 test mumu
                    
                    # Bu mum için MA değerini hesapla (geçmiş veri kullanarak)
                    if len(df) >= k + period + 2:  # +2 çünkü onay ve test mumu
                        df_ma_calc = df.iloc[:-(k+2)]  # k+2 mum öncesine kadar
                        if len(df_ma_calc) >= period:
                            ma_value_for_candle = self.calculate_ma(df_ma_calc, ma_type, period).iloc[-1]
                            
                            if not pd.isna(ma_value_for_candle) and candle_close < ma_value_for_candle:
                                is_signal_valid = False  # MA altında kapanış var, sinyal geçersiz
                                break
                
                if is_signal_valid:
                    buy_signals.append({
                    "harf": harf,
                    "ma_type": ma_type,
                    "ma_value": original_ma_value,
                    "tolerance_ma_value": ma_value,
                    "price": confirm_close,
                    "signal_timeframe": signal_timeframe,
                    "ma_calculation_timeframe": ma_calculation_timeframe,
                    "direction": "Yukarı",
                    "tolerance": harf_tolerance.get("tolerance", 0) if harf_tolerance else 0,
                    "candle_color": "yeşil",
                    "signal_type": "alış",
                    "period": period,
                    "test_candle_rejection": True,
                    "confirm_candle_breakout": True
                })

            # Satış Sinyali Koşulları
            bearish_rejection_candle = (test_open < ma_value and test_high > ma_value and test_close < ma_value)
            bearish_confirmation_candle = (confirm_close < confirm_open and confirm_close < test_low)

            if bearish_rejection_candle and bearish_confirmation_candle:
                # --- FİLTRE KONTROLÜ (MQL5 v5 YENİ KURAL) ---
                is_signal_valid = True
                # Son 'filter_period' muma bak, MA üstünde kapanış var mı?
                for k in range(1, filter_period + 1):
                    if len(df) <= k + 1:  # +1 çünkü -1 onay mumu, -2 test mumu
                        continue
                    
                    # k. mumun kapanış fiyatı (test mumundan önceki mumlar)
                    candle_close = df.iloc[-(k+2)]["close"]  # -k-2 çünkü -1 onay mumu, -2 test mumu
                    
                    # Bu mum için MA değerini hesapla (geçmiş veri kullanarak)
                    if len(df) >= k + period + 2:  # +2 çünkü onay ve test mumu
                        df_ma_calc = df.iloc[:-(k+2)]  # k+2 mum öncesine kadar
                        if len(df_ma_calc) >= period:
                            ma_value_for_candle = self.calculate_ma(df_ma_calc, ma_type, period).iloc[-1]
                            
                            if not pd.isna(ma_value_for_candle) and candle_close > ma_value_for_candle:
                                is_signal_valid = False  # MA üstünde kapanış var, sinyal geçersiz
                                break
                
                if is_signal_valid:
                    sell_signals.append({
                    "harf": harf,
                    "ma_type": ma_type,
                    "ma_value": original_ma_value,
                    "tolerance_ma_value": ma_value,
                    "price": confirm_close,
                    "signal_timeframe": signal_timeframe,
                    "ma_calculation_timeframe": ma_calculation_timeframe,
                    "direction": "Aşağı",
                    "tolerance": harf_tolerance.get("tolerance", 0) if harf_tolerance else 0,
                    "candle_color": "kırmızı",
                    "signal_type": "satış",
                    "period": period,
                    "test_candle_rejection": True,
                    "confirm_candle_breakout": True
                })
            

        
        # Alış sinyallerini birleştir
        if buy_signals:
            # Harfleri ve periyotları birleştir
            buy_harfler = []
            buy_periods = []
            for s in buy_signals:
                harf = s["harf"]
                period = s.get("period", "")
                ma_type = s.get("ma_type", "MA")
                ma_calc_tf = s.get("ma_calculation_timeframe", "")
                buy_harfler.append(f"{harf}({ma_type}{period} {ma_calc_tf})")
                buy_periods.append(f"{ma_type}{period}")
            
            buy_harf_str = ", ".join(buy_harfler)
            buy_period_str = ", ".join(buy_periods)
            
            # İlk sinyalin bilgilerini kullan, harfleri ve periyotları birleştir
            combined_buy_signal = buy_signals[0].copy()
            combined_buy_signal["harf"] = buy_harf_str
            combined_buy_signal["period"] = buy_period_str
            combined_buy_signal["combined_harfler"] = [s["harf"] for s in buy_signals]
            combined_buy_signal["signal_count"] = len(buy_signals)
            signals.append(combined_buy_signal)
        
        # Satış sinyallerini birleştir
        if sell_signals:
            # Harfleri ve periyotları birleştir
            sell_harfler = []
            sell_periods = []
            for s in sell_signals:
                harf = s["harf"]
                period = s.get("period", "")
                ma_type = s.get("ma_type", "MA")
                ma_calc_tf = s.get("ma_calculation_timeframe", "")
                sell_harfler.append(f"{harf}({ma_type}{period} {ma_calc_tf})")
                sell_periods.append(f"{ma_type}{period}")
            
            sell_harf_str = ", ".join(sell_harfler)
            sell_period_str = ", ".join(sell_periods)
            
            # İlk sinyalin bilgilerini kullan, harfleri ve periyotları birleştir
            combined_sell_signal = sell_signals[0].copy()
            combined_sell_signal["harf"] = sell_harf_str
            combined_sell_signal["period"] = sell_period_str
            combined_sell_signal["combined_harfler"] = [s["harf"] for s in sell_signals]
            combined_sell_signal["signal_count"] = len(sell_signals)
            signals.append(combined_sell_signal)

        return signals

    def save_symbols(self, symbols):
        """Sembolleri kaydet"""
        try:
            with open(SYMBOLS_FILE, "w", encoding="utf-8") as f:
                json.dump(symbols, f, indent=4, ensure_ascii=False)
            self.update_global_symbols()
        except Exception as e:
            self.show_error(f"Semboller kaydetme hatası: {str(e)}")

    def load_symbols_from_file(self):
        """Sembolleri dosyadan yükle"""
        try:
            if os.path.exists(SYMBOLS_FILE):
                with open(SYMBOLS_FILE, "r", encoding="utf-8") as f:
                    symbols = json.load(f)
                if hasattr(self, 'gui') and hasattr(self.gui, 'symbols_listbox'):
                    self.gui.symbols_listbox.delete("0.0", "end")
                    for symbol in symbols:
                        self.gui.symbols_listbox.insert("end", symbol + "\n")
                return symbols
            return []
        except Exception as e:
            self.show_error(f"Semboller yükleme hatası: {str(e)}")
            return []

    def update_global_symbols(self):
        """Global sembolleri güncelle"""
        try:
            symbols = self.load_symbols()
            synthetic_names = list(self.synthetic_symbols.keys())
            global_symbols = symbols + synthetic_names
            
            with open(GLOBAL_SYMBOLS_FILE, "w", encoding="utf-8") as f:
                json.dump(global_symbols, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.show_error(f"Global semboller güncelleme hatası: {str(e)}")

    def should_check_timeframe(self, timeframe, current_time, last_check_time):
        """Belirtilen zaman dilimi için mum kapanış zamanını kontrol eder"""
        if last_check_time is None:
            return True  # İlk çalıştırma
            
        # Her zaman dilimi için mum kapanış zamanlarını hesapla
        if timeframe == "1h":
            # 1h mumları her saatin başında kapanır (00:00, 01:00, 02:00, ...)
            current_hour = current_time.replace(minute=0, second=0, microsecond=0)
            last_hour = last_check_time.replace(minute=0, second=0, microsecond=0)
            return current_hour > last_hour
            
        elif timeframe == "4h":
            # 4h mumları 00:00, 04:00, 08:00, 12:00, 16:00, 20:00'da kapanır
            current_4h = current_time.replace(minute=0, second=0, microsecond=0)
            last_4h = last_check_time.replace(minute=0, second=0, microsecond=0)
            
            # 4 saatlik periyotları hesapla
            current_4h_period = current_4h.hour // 4
            last_4h_period = last_4h.hour // 4
            
            return current_4h_period > last_4h_period or current_4h.date() > last_4h.date()
            
        elif timeframe == "8h":
            # 8h mumları 00:00, 08:00, 16:00'da kapanır
            current_8h = current_time.replace(minute=0, second=0, microsecond=0)
            last_8h = last_check_time.replace(minute=0, second=0, microsecond=0)
            
            # 8 saatlik periyotları hesapla
            current_8h_period = current_8h.hour // 8
            last_8h_period = last_8h.hour // 8
            
            return current_8h_period > last_8h_period or current_8h.date() > last_8h.date()
            
        elif timeframe == "12h":
            # 12h mumları 00:00, 12:00'da kapanır
            current_12h = current_time.replace(minute=0, second=0, microsecond=0)
            last_12h = last_check_time.replace(minute=0, second=0, microsecond=0)
            
            # 12 saatlik periyotları hesapla
            current_12h_period = current_12h.hour // 12
            last_12h_period = last_12h.hour // 12
            
            return current_12h_period > last_12h_period or current_12h.date() > last_12h.date()
            
        elif timeframe == "1d":
            # Günlük mumlar her gün 00:00'da kapanır
            current_day = current_time.date()
            last_day = last_check_time.date()
            return current_day > last_day
            
        else:
            # Bilinmeyen timeframe için 1 dakika bekle
            return (current_time - last_check_time).total_seconds() >= 60

    def create_combined_signal_message(self, symbol, signal_timeframe, harf_str, signals, current_price):
        """Birden fazla harf sinyalini tek mesajda birleştir - yeni sinyal mantığı"""
        
        # Yönleri grupla
        buy_signals = [s for s in signals if s.get("signal_type") == "alış"]
        sell_signals = [s for s in signals if s.get("signal_type") == "satış"]
        
        # MA hesaplama zaman dilimlerini al
        ma_timeframes = list(set([s.get("ma_calculation_timeframe", "") for s in signals if s.get("ma_calculation_timeframe")]))
        ma_timeframe_str = ", ".join(ma_timeframes) if ma_timeframes else "Bilinmiyor"
        
        message = f"""🚨 YENİ SİNYAL ALARMİ!

📊 Sembol: {symbol}
⏰ Sinyal Zaman Dilimi: {signal_timeframe}
📈 MA Hesaplama Zaman Dilimi: {ma_timeframe_str}
🔤 Sinyal Harfi: {harf_str}
💰 Fiyat: {current_price:.4f}
🕐 Zaman: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📈 Sinyal Detayları:"""

        # Alış sinyalleri (yeşil mumlar)
        if buy_signals:
            message += f"\n\n🟢 ALIŞ SİNYALLERİ (Yeşil Mum):"
            for signal in buy_signals:
                ma_type = signal.get('ma_type', 'MA')
                period = signal.get('period', '')
                ma_calc_tf = signal.get('ma_calculation_timeframe', '')
                tolerance_info = f" (Tolerans: %{signal['tolerance']:.1f})" if 'tolerance' in signal else ""
                message += f"\n• {signal['harf']}: {ma_type}{period} {ma_calc_tf} {signal['ma_value']:.4f}{tolerance_info}"
        
        # Satış sinyalleri (kırmızı mumlar)
        if sell_signals:
            message += f"\n\n🔴 SATIŞ SİNYALLERİ (Kırmızı Mum):"
            for signal in sell_signals:
                ma_type = signal.get('ma_type', 'MA')
                period = signal.get('period', '')
                ma_calc_tf = signal.get('ma_calculation_timeframe', '')
                tolerance_info = f" (Tolerans: %{signal['tolerance']:.1f})" if 'tolerance' in signal else ""
                message += f"\n• {signal['harf']}: {ma_type}{period} {ma_calc_tf} {signal['ma_value']:.4f}{tolerance_info}"

        message += "\n\n⚠️ Bu sinyaller aktif kalacak ve periyodik olarak güncellenecektir."
        
        return message

    def run_backtest(self):
        """Backtest fonksiyonu - 15 günlük geçmiş veri üzerinden sinyal analizi"""
        try:
            print("🔍 BACKTEST BAŞLATILIYOR...")
            print("=" * 60)
            
            # 1. Konfigürasyon dosyalarını yükle
            print("📋 Konfigürasyon dosyaları yükleniyor...")
            
            # MA/EMA konfigürasyonları
            if not os.path.exists(CONFIG_FILE):
                print("❌ MA_CONFIG.json dosyası bulunamadı!")
                return
                
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                configs = json.load(f)
            print(f"✅ {len(configs)} MA/EMA konfigürasyonu yüklendi")
            
            # Tolerans ayarları
            tolerance_data = {}
            if os.path.exists(TOLERANCE_FILE):
                with open(TOLERANCE_FILE, "r", encoding="utf-8") as f:
                    tolerance_data = json.load(f)
                print(f"✅ {len(tolerance_data)} tolerans ayarı yüklendi")
            else:
                print("ℹ️ Tolerans dosyası bulunamadı, tolerans olmadan devam ediliyor")
            
            # Sinyal iptal ve filtre ayarları
            cancel_data = {"cancel_percentage": 5.0, "filter_period": 5}  # Varsayılan değerler
            if os.path.exists(SIGNAL_CANCEL_FILE):
                with open(SIGNAL_CANCEL_FILE, "r", encoding="utf-8") as f:
                    cancel_data = json.load(f)
                print(f"✅ Sinyal iptal yüzdesi: %{cancel_data.get('cancel_percentage', 5.0)}")
                print(f"✅ Filtre periyodu: {cancel_data.get('filter_period', 5)} mum")
            else:
                print("ℹ️ Sinyal iptal dosyası bulunamadı, varsayılan değerler kullanılıyor")
            
            # 2. Sembol listesini oluştur
            print("\n📈 Sembol listesi oluşturuluyor...")
            symbols = self.generate_symbols_list()
            print(f"✅ {len(symbols)} sembol bulundu")
            
            # 3. Sinyal arama zaman dilimleri
            signal_timeframes = ["1h", "4h", "8h", "12h", "1d"]
            
            # 4. Backtest sonuçları için veri yapıları
            backtest_results = {
                "start_time": datetime.now(),
                "total_signals": 0,
                "all_signals": [],
                "signals_by_timeframe": {},
                "signals_by_symbol": {},
                "summary": {}
            }
            
            # 5. 15 günlük veri için tarih aralığı
            end_date = datetime.now()
            start_date = end_date - timedelta(days=15)
            print(f"\n📅 Tarih aralığı: {start_date.strftime('%Y-%m-%d %H:%M')} - {end_date.strftime('%Y-%m-%d %H:%M')}")
            
            # 6. Her sembol için backtest
            print(f"\n🔍 {len(symbols)} sembol analiz ediliyor...")
            
            for symbol_index, symbol in enumerate(symbols):
                print(f"\n📊 Sembol {symbol_index + 1}/{len(symbols)}: {symbol}")
                
                # Her zaman dilimi için analiz
                for signal_timeframe in signal_timeframes:
                    try:
                        # Sinyal arama zaman diliminde veri çek
                        df_signal = self.fetch_data(symbol, signal_timeframe, limit=500)  # Daha fazla veri
                        
                        if df_signal is None or len(df_signal) < 10:
                            continue
                        
                        # 15 günlük veriyi filtrele
                        df_signal['timestamp'] = pd.to_datetime(df_signal['timestamp'])
                        df_filtered = df_signal[(df_signal['timestamp'] >= start_date) & (df_signal['timestamp'] <= end_date)]
                        
                        if len(df_filtered) < 2:
                            continue
                        
                        print(f"  ⏰ {signal_timeframe}: {len(df_filtered)} mum bulundu")
                        
                        # Her mum için sinyal kontrolü
                        for i in range(1, len(df_filtered)):
                            current_candle = df_filtered.iloc[i]
                            prev_candle = df_filtered.iloc[i-1]
                            
                            # Bu mum için MA değerlerini hesapla
                            ma_values_cache = {}
                            
                            for config in configs:
                                ma_calc_timeframe = config["ma_timeframe"]
                                harf = config["harf"]
                                ma_type = config["tip"]
                                period = config["periyot"]
                                
                                # MA hesaplama zaman diliminde veri çek
                                df_ma = self.fetch_data(symbol, ma_calc_timeframe, limit=500)
                                
                                if df_ma is not None and len(df_ma) >= period:
                                    # Sadece bu mum zamanına kadar olan veriyi kullan
                                    df_ma['timestamp'] = pd.to_datetime(df_ma['timestamp'])
                                    df_ma_filtered = df_ma[df_ma['timestamp'] <= current_candle['timestamp']]
                                    
                                    if len(df_ma_filtered) >= period:
                                        ma_value = self.calculate_ma(df_ma_filtered, ma_type, period).iloc[-1]
                                        if not pd.isna(ma_value):
                                            if ma_calc_timeframe not in ma_values_cache:
                                                ma_values_cache[ma_calc_timeframe] = {}
                                            ma_values_cache[ma_calc_timeframe][harf] = ma_value
                            
                            # Sinyal kontrolü
                            if ma_values_cache:
                                # Sinyal arama zaman diliminde sadece bu mum için veri
                                df_signal_check = df_filtered.iloc[:i+1]
                                
                                signals = self.check_signals_with_cached_ma(
                                    df_signal_check,
                                    configs,
                                    tolerance_data,
                                    signal_timeframe,
                                    ma_values_cache,
                                    cancel_data.get("filter_period", 5)
                                )
                                
                                if signals:
                                    for signal in signals:
                                        # Sinyal detayları - sadece gerekli alanlar
                                        signal_info = {
                                            "symbol": symbol,
                                            "signal_timeframe": signal_timeframe,
                                            "ma_calculation_timeframe": signal.get("ma_calculation_timeframe", ""),
                                            "harf": signal["harf"],
                                            "signal_type": signal.get("signal_type", ""),
                                            "timestamp": current_candle['timestamp']
                                        }
                                        
                                        # Sonuçlara ekle - sadeleştirilmiş
                                        backtest_results["all_signals"].append(signal_info)
                                        backtest_results["total_signals"] += 1
                                        
                                        # Birleştirilmiş sinyal mesajı
                                        if "combined_harfler" in signal:
                                            print(f"    🚨 SİNYAL: {signal['harf']} ({signal['signal_count']} harf) - {signal['direction']} - {signal['signal_type']} - {signal['price']:.5f}")
                                        else:
                                            print(f"    🚨 SİNYAL: {signal['harf']} - {signal['ma_type']}{signal.get('period', '')} {signal.get('ma_calculation_timeframe', '')} - {signal['direction']} - {signal['signal_type']} - {signal['price']:.5f}")
                    
                    except Exception as e:
                        print(f"    ❌ {signal_timeframe} analiz hatası: {e}")
                        continue
            
            # 7. Backtest sonuçlarını kaydet
            print(f"\n💾 Backtest sonuçları kaydediliyor...")
            
            # Sonuç dosyası oluştur
            backtest_file = f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # JSON için datetime'ları string'e çevir
            backtest_results_copy = backtest_results.copy()
            backtest_results_copy["start_time"] = backtest_results_copy["start_time"].strftime('%Y-%m-%d %H:%M:%S')
            backtest_results_copy["end_time"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for signal in backtest_results_copy["all_signals"]:
                signal["timestamp"] = signal["timestamp"].strftime('%Y-%m-%d %H:%M:%S')
            
            with open(backtest_file, "w", encoding="utf-8") as f:
                json.dump(backtest_results_copy, f, indent=4, ensure_ascii=False)
            
            # 8. Özet raporu oluştur
            print(f"\n📊 BACKTEST ÖZET RAPORU")
            print("=" * 60)
            print(f"📅 Tarih Aralığı: {start_date.strftime('%Y-%m-%d %H:%M')} - {end_date.strftime('%Y-%m-%d %H:%M')}")
            print(f"📈 Analiz Edilen Sembol: {len(symbols)}")
            print(f"⚙️ MA/EMA Konfigürasyonu: {len(configs)}")
            print(f"🎯 Toplam Sinyal: {backtest_results['total_signals']}")
            print()
            
            # Basit özet
            print("✅ Backtest başarıyla tamamlandı!")
            print(f"📊 Toplam {backtest_results['total_signals']} sinyal bulundu")
            print(f"📁 Sonuçlar kaydedildi: {backtest_file}")
            
            print()
            print(f"💾 Detaylı sonuçlar: {backtest_file}")
            print("=" * 60)
            print("✅ BACKTEST TAMAMLANDI!")
            
            return backtest_results
            
        except Exception as e:
            print(f"❌ Backtest hatası: {e}")
            import traceback
            traceback.print_exc()
            return None

    def analyze_backtest_results(self, results):
        """Backtest sonuçlarını basit analiz et"""
        if not results:
            print("❌ Analiz edilecek sonuç bulunamadı!")
            return
        
        print("\n🔍 BACKTEST ANALİZİ")
        print("=" * 50)
        
        # 1. Genel istatistikler
        total_signals = results["total_signals"]
        all_signals = results["all_signals"]
        
        if total_signals == 0:
            print("❌ Hiç sinyal bulunamadı!")
            return
        
        print(f"📊 GENEL İSTATİSTİKLER:")
        print(f"  🎯 Toplam Sinyal: {total_signals}")
        print(f"  📅 Analiz Süresi: 15 gün")
        print(f"  📈 Günlük Ortalama: {total_signals / 15:.1f} sinyal")
        
        # 2. Sinyal türü analizi
        buy_signals = [s for s in all_signals if s["signal_type"] == "alış"]
        sell_signals = [s for s in all_signals if s["signal_type"] == "satış"]
        
        print(f"\n📈 SİNYAL TÜRÜ ANALİZİ:")
        print(f"  🟢 Alış Sinyalleri: {len(buy_signals)} (%{len(buy_signals)/total_signals*100:.1f})")
        print(f"  🔴 Satış Sinyalleri: {len(sell_signals)} (%{len(sell_signals)/total_signals*100:.1f})")
        
        # 3. Zaman dilimi analizi
        timeframe_counts = {}
        for signal in all_signals:
            tf = signal["signal_timeframe"]
            if tf not in timeframe_counts:
                timeframe_counts[tf] = 0
            timeframe_counts[tf] += 1
        
        print(f"\n⏰ ZAMAN DİLİMİ ANALİZİ:")
        for tf, count in sorted(timeframe_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {tf:>4}: {count:>3} sinyal (%{count/total_signals*100:.1f})")
        
        # 4. Sembol analizi
        symbol_counts = {}
        for signal in all_signals:
            symbol = signal["symbol"]
            if symbol not in symbol_counts:
                symbol_counts[symbol] = 0
            symbol_counts[symbol] += 1
        
        print(f"\n🏆 SEMBOL ANALİZİ:")
        for symbol, count in sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {symbol}: {count} sinyal (%{count/total_signals*100:.1f})")
        
        # 5. MA hesaplama zaman dilimi analizi
        ma_timeframe_counts = {}
        for signal in all_signals:
            ma_tf = signal.get("ma_calculation_timeframe", "bilinmiyor")
            if ma_tf not in ma_timeframe_counts:
                ma_timeframe_counts[ma_tf] = 0
            ma_timeframe_counts[ma_tf] += 1
        
        print(f"\n⏱️ MA HESAPLAMA ZAMAN DİLİMİ:")
        for ma_tf, count in sorted(ma_timeframe_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {ma_tf:>8}: {count:>3} sinyal (%{count/total_signals*100:.1f})")
        
        print("\n✅ Analiz tamamlandı!")
        
        print("=" * 80)
        print("✅ DETAYLI ANALİZ TAMAMLANDI!")
        
        return True

if __name__ == "__main__":
    app = MAConfigApp()
    
    # Backtest modu kontrolü
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--backtest":
        print("🔍 BACKTEST MODU BAŞLATILIYOR...")
        print("GUI açılmayacak, sadece backtest çalışacak.")
        
        # Backtest modu için MT5'i manuel olarak başlat
        print("🔧 MT5 bağlantısı başlatılıyor...")
        app.initialize_mt5()
        
        # MT5 bağlantısını kontrol et
        if not app.mt5_initialized:
            print("❌ MT5 bağlantısı kurulamadı! Backtest iptal ediliyor.")
            sys.exit(1)
        
        # Backtest çalıştır
        results = app.run_backtest()
        
        if results:
            print(f"\n🎉 Backtest başarıyla tamamlandı!")
            print(f"📊 Toplam {results['total_signals']} sinyal bulundu.")
            
            # Detaylı analiz yap
            app.analyze_backtest_results(results)
        else:
            print(f"\n❌ Backtest başarısız!")
        
        sys.exit(0)
    else:
        # Normal GUI modu
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.mainloop()