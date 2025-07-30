import customtkinter as ctk
from customtkinter import CTkInputDialog

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class MAConfigGUI:
    def __init__(self, app):
        self.app = app
        
        # Ana frame
        self.main_frame = ctk.CTkFrame(self.app)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Sol taraf
        self.left_frame = ctk.CTkFrame(self.main_frame)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Notebook
        self.notebook = ctk.CTkTabview(self.left_frame)
        self.notebook.pack(fill="both", expand=True, pady=5)
        
        # Tab'lar
        self.ma_tab = self.notebook.add("MA/EMA Ayarları")
        self.symbols_tab = self.notebook.add("Sembol Yönetimi")
        self.synthetic_tab = self.notebook.add("Çarpım Grafikleri")
        self.cancel_tab = self.notebook.add("Sinyal İptal & Filtre")
        
        # GUI oluştur
        self.create_ma_config_tab()
        self.create_symbols_tab()
        self.create_synthetic_tab()
        self.create_signal_cancel_tab()
        
        # Sağ taraf
        self.right_frame = ctk.CTkFrame(self.main_frame, width=300)
        self.right_frame.pack(side="right", fill="y", padx=(10, 0))
        self.right_frame.pack_propagate(False)
        
        self.create_right_panel()

    def create_ma_config_tab(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self.ma_tab, width=450, height=250)
        self.scroll_frame.pack(pady=5, fill="both", expand=True)

        headers = ["No", "Tip (MA/EMA)", "Periyot", "MA Hesaplama Zaman Dilimi", "Sinyal Harfi"]
        for col, text in enumerate(headers):
            label = ctk.CTkLabel(self.scroll_frame, text=text, font=("Arial", 12, "bold"))
            label.grid(row=0, column=col, padx=5, pady=3)

        # MA hesaplama zaman dilimleri (hareketli ortalama hangi zaman diliminde hesaplanacak)
        self.ma_calculation_timeframes = ["4h", "günlük", "haftalık", "aylık"]
        
        for i in range(25):
            ctk.CTkLabel(self.scroll_frame, text=str(i+1)).grid(row=i+1, column=0, padx=5, pady=2)
            tip_option = ctk.CTkOptionMenu(self.scroll_frame, values=["MA", "EMA"], width=100)
            tip_option.grid(row=i+1, column=1, padx=5, pady=2)
            period_entry = ctk.CTkEntry(self.scroll_frame, width=80)
            period_entry.grid(row=i+1, column=2, padx=5, pady=2)
            ma_timeframe_option = ctk.CTkOptionMenu(self.scroll_frame, values=self.ma_calculation_timeframes, width=100)
            ma_timeframe_option.grid(row=i+1, column=3, padx=5, pady=2)
            harf_entry = ctk.CTkEntry(self.scroll_frame, width=80)
            harf_entry.grid(row=i+1, column=4, padx=5, pady=2)
            self.app.entries.append({
                "tip": tip_option,
                "periyot": period_entry,
                "ma_timeframe": ma_timeframe_option,  # MA hesaplama zaman dilimi
                "harf": harf_entry
            })

        self.save_button = ctk.CTkButton(self.ma_tab, text="📝 MA/EMA Konfigürasyonu Kaydet", command=self.app.save_config)
        self.save_button.pack(pady=5)

        self.tolerance_frame = ctk.CTkFrame(self.ma_tab)
        self.tolerance_frame.pack(pady=5, fill="x")

        self.tolerance_label = ctk.CTkLabel(self.tolerance_frame, text="Harf Tolerans Ayarları", font=("Arial", 14, "bold"))
        self.tolerance_label.pack(pady=3)

        # Sembol tolerans ayarları için scrollable frame
        self.tolerance_scroll_frame = ctk.CTkScrollableFrame(self.tolerance_frame, width=400, height=200)
        self.tolerance_scroll_frame.pack(pady=5, fill="both", expand=True)

        # Başlık satırı
        headers = ["Aktif", "Harf", "Tolerans %", "Aşağı", "Yukarı"]
        for col, text in enumerate(headers):
            label = ctk.CTkLabel(self.tolerance_scroll_frame, text=text, font=("Arial", 10, "bold"))
            label.grid(row=0, column=col, padx=5, pady=3)

        # Harf tolerans girişleri (25 satır)
        self.symbol_tolerance_entries = []
        harfler = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y"]
        
        for i in range(25):
            row = i + 1
            
            # Aktif checkbox
            active_var = ctk.BooleanVar(value=True)
            active_checkbox = ctk.CTkCheckBox(self.tolerance_scroll_frame, text="", variable=active_var, width=20)
            active_checkbox.grid(row=row, column=0, padx=2, pady=2)
            
            # Harf (otomatik doldurulmuş)
            harf_label = ctk.CTkLabel(self.tolerance_scroll_frame, text=harfler[i], font=("Arial", 12, "bold"))
            harf_label.grid(row=row, column=1, padx=2, pady=2)
            
            # Tolerans değeri
            tolerance_entry = ctk.CTkEntry(self.tolerance_scroll_frame, placeholder_text="1.0", width=80)
            tolerance_entry.grid(row=row, column=2, padx=2, pady=2)
            
            # Aşağı checkbox
            down_var = ctk.BooleanVar(value=True)
            down_checkbox = ctk.CTkCheckBox(self.tolerance_scroll_frame, text="", variable=down_var, width=20)
            down_checkbox.grid(row=row, column=3, padx=2, pady=2)
            
            # Yukarı checkbox
            up_var = ctk.BooleanVar(value=False)
            up_checkbox = ctk.CTkCheckBox(self.tolerance_scroll_frame, text="", variable=up_var, width=20)
            up_checkbox.grid(row=row, column=4, padx=2, pady=2)
            
            self.symbol_tolerance_entries.append({
                "harf": harfler[i],
                "active": active_var,
                "tolerance": tolerance_entry,
                "down": down_var,
                "up": up_var
            })

        self.save_tolerance_button = ctk.CTkButton(self.tolerance_frame, text="⚙️ Harf Toleranslarını Kaydet", command=self.app.save_tolerances)
        self.save_tolerance_button.pack(pady=5)

    def create_symbols_tab(self):
        # Scrollable frame ekle (diğer tab'larla aynı boyut)
        self.symbols_scroll_frame = ctk.CTkScrollableFrame(self.symbols_tab, width=450, height=400)
        self.symbols_scroll_frame.pack(pady=5, fill="both", expand=True)
        
        title_label = ctk.CTkLabel(self.symbols_scroll_frame, text="Sembol Yönetimi", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        desc_label = ctk.CTkLabel(self.symbols_scroll_frame, text="Analiz edilecek sembolleri ekleyin veya silin", font=("Arial", 12))
        desc_label.pack(pady=5)
        
        add_frame = ctk.CTkFrame(self.symbols_scroll_frame)
        add_frame.pack(pady=10, fill="x", padx=10)
        
        symbol_frame = ctk.CTkFrame(add_frame)
        symbol_frame.pack(pady=5, fill="x")
        
        ctk.CTkLabel(symbol_frame, text="Sembol Adı:").grid(row=0, column=0, padx=5, pady=5)
        self.symbol_entry = ctk.CTkEntry(symbol_frame, placeholder_text="EURUSD", width=150)
        self.symbol_entry.grid(row=0, column=1, padx=5, pady=5)
        
        add_button = ctk.CTkButton(add_frame, text="➕ Sembol Ekle", command=self.app.add_custom_symbol)
        add_button.pack(pady=5)
        
        list_frame = ctk.CTkFrame(self.symbols_scroll_frame)
        list_frame.pack(pady=10, fill="both", expand=True, padx=10)
        
        ctk.CTkLabel(list_frame, text="Mevcut Semboller:", font=("Arial", 14, "bold")).pack(pady=5)
        
        self.symbols_listbox = ctk.CTkTextbox(list_frame, height=300)
        self.symbols_listbox.pack(pady=5, fill="both", expand=True, padx=10)
        
        delete_button = ctk.CTkButton(list_frame, text="🗑️ Seçili Sembolü Sil", command=self.app.delete_custom_symbol)
        delete_button.pack(pady=5)

    def create_synthetic_tab(self):
        # Scrollable frame ekle (diğer tab'larla aynı boyut)
        self.synthetic_scroll_frame = ctk.CTkScrollableFrame(self.synthetic_tab, width=450, height=400)
        self.synthetic_scroll_frame.pack(pady=5, fill="both", expand=True)
        
        title_label = ctk.CTkLabel(self.synthetic_scroll_frame, text="Çarpım Grafikleri (Sentetik Enstrümanlar)", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        desc_label = ctk.CTkLabel(self.synthetic_scroll_frame, text="EURUSD*EURGBP gibi çarpım grafikleri oluşturun", font=("Arial", 12))
        desc_label.pack(pady=5)
        
        add_frame = ctk.CTkFrame(self.synthetic_scroll_frame)
        add_frame.pack(pady=10, fill="x", padx=10)
        
        # Sembol 1 ve 2 yan yana
        symbols_frame = ctk.CTkFrame(add_frame)
        symbols_frame.pack(pady=5, fill="x", padx=10)
        
        ctk.CTkLabel(symbols_frame, text="Sembol 1:").grid(row=0, column=0, padx=5, pady=5)
        self.symbol1_entry = ctk.CTkEntry(symbols_frame, placeholder_text="EURUSD", width=100)
        self.symbol1_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(symbols_frame, text="Sembol 2:").grid(row=0, column=2, padx=5, pady=5)
        self.symbol2_entry = ctk.CTkEntry(symbols_frame, placeholder_text="EURGBP", width=100)
        self.symbol2_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # Sembol Adı
        name_frame = ctk.CTkFrame(add_frame)
        name_frame.pack(pady=5, fill="x", padx=10)
        ctk.CTkLabel(name_frame, text="Sembol Adı:").pack(side="left", padx=5, pady=5)
        self.synthetic_name_entry = ctk.CTkEntry(name_frame, placeholder_text="EURUSD_EURGBP_MULT", width=200)
        self.synthetic_name_entry.pack(side="left", padx=5, pady=5)
        
        add_button = ctk.CTkButton(add_frame, text="➕ Çarpım Grafiği Ekle", command=self.app.add_synthetic_symbol)
        add_button.pack(pady=10)
        
        list_frame = ctk.CTkFrame(self.synthetic_scroll_frame)
        list_frame.pack(pady=10, fill="both", expand=True, padx=10)
        
        ctk.CTkLabel(list_frame, text="Mevcut Çarpım Grafikleri:", font=("Arial", 14, "bold")).pack(pady=5)
        
        self.synthetic_listbox = ctk.CTkTextbox(list_frame, height=300)
        self.synthetic_listbox.pack(pady=5, fill="both", expand=True, padx=10)
        
        delete_button = ctk.CTkButton(list_frame, text="🗑️ Seçili Çarpım Grafiğini Sil", command=self.app.delete_synthetic_symbol)
        delete_button.pack(pady=5)

    def create_signal_cancel_tab(self):
        # Scrollable frame ekle (diğer tab'larla aynı boyut)
        self.cancel_scroll_frame = ctk.CTkScrollableFrame(self.cancel_tab, width=450, height=400)
        self.cancel_scroll_frame.pack(pady=5, fill="both", expand=True)
        
        title_label = ctk.CTkLabel(self.cancel_scroll_frame, text="Sinyal İptal & Filtre Ayarları", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Sinyal İptal Bölümü
        cancel_frame = ctk.CTkFrame(self.cancel_scroll_frame)
        cancel_frame.pack(pady=10, fill="x", padx=10)
        
        ctk.CTkLabel(cancel_frame, text="🛑 Sinyal İptal Ayarları", font=("Arial", 14, "bold")).pack(pady=5)
        ctk.CTkLabel(cancel_frame, text="Fiyat belirli bir yüzde ilerlediğinde sinyal iptal edilir", font=("Arial", 12)).pack(pady=5)
        
        ctk.CTkLabel(cancel_frame, text="Sinyal İptal Yüzdesi (%):").pack(pady=5)
        self.cancel_percentage_entry = ctk.CTkEntry(cancel_frame, placeholder_text="5.0", width=150)
        self.cancel_percentage_entry.pack(pady=5)
        
        # Filtre Bölümü
        filter_frame = ctk.CTkFrame(self.cancel_scroll_frame)
        filter_frame.pack(pady=10, fill="x", padx=10)
        
        ctk.CTkLabel(filter_frame, text="🔍 Sinyal Filtre Ayarları", font=("Arial", 14, "bold")).pack(pady=5)
        ctk.CTkLabel(filter_frame, text="MQL5 v5 algoritması için sinyal filtre periyodu", font=("Arial", 12)).pack(pady=5)
        
        ctk.CTkLabel(filter_frame, text="Filtre Periyodu (Mum Sayısı):").pack(pady=5)
        self.filter_period_entry = ctk.CTkEntry(filter_frame, placeholder_text="5", width=150)
        self.filter_period_entry.pack(pady=5)
        
        # Kaydet butonu
        save_cancel_button = ctk.CTkButton(self.cancel_scroll_frame, text="💾 Tüm Ayarları Kaydet", command=self.app.save_signal_cancel_config)
        save_cancel_button.pack(pady=10)

    def create_right_panel(self):
        self.right_title = ctk.CTkLabel(self.right_frame, text="📢 Bildirimler ve Durum", font=("Arial", 16, "bold"))
        self.right_title.pack(pady=10)
        
        self.message_label = ctk.CTkLabel(self.right_frame, text="Sistem hazır...", text_color="blue", wraplength=280, justify="left", height=100)
        self.message_label.pack(pady=10, padx=10, anchor="w", fill="y")
        
        self.mt5_status_label = ctk.CTkLabel(self.right_frame, text="🔴 MT5 Bağlantısı Yok", text_color="red", wraplength=280)
        self.mt5_status_label.pack(pady=5, padx=10, anchor="w")
        
        self.config_status_label = ctk.CTkLabel(self.right_frame, text="📋 Konfigürasyon: 0 ayar", text_color="gray", wraplength=280)
        self.config_status_label.pack(pady=5, padx=10, anchor="w")
        
        self.tolerance_status_label = ctk.CTkLabel(self.right_frame, text="⚙️ Tolerans: Ayarlanmamış", text_color="gray", wraplength=280)
        self.tolerance_status_label.pack(pady=5, padx=10, anchor="w")
        
        self.synthetic_status_label = ctk.CTkLabel(self.right_frame, text="🔗 Çarpım Grafikleri: 0 adet", text_color="gray", wraplength=280)
        self.synthetic_status_label.pack(pady=5, padx=10, anchor="w")
        
        self.cancel_status_label = ctk.CTkLabel(self.right_frame, text="❌ İptal: Ayarlanmamış", text_color="gray", wraplength=280)
        self.cancel_status_label.pack(pady=5, padx=10, anchor="w")
        
        self.button_frame = ctk.CTkFrame(self.right_frame)
        self.button_frame.pack(fill="x", pady=10, padx=10)
        self.bot_button = ctk.CTkButton(self.button_frame, text="▶️ Botu Başlat", command=self.app.toggle_bot)
        self.bot_button.pack(fill="x")

        self.status_label = ctk.CTkLabel(self.right_frame, text="🔴 Bot Durduruldu", text_color="red")
        self.status_label.pack(pady=5)