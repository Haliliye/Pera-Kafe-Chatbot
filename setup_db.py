import sqlite3

def veritabani_guncelle():
    conn = sqlite3.connect("kafe.db")
    cursor = conn.cursor()

    # Eski tabloyu silip yeniden oluşturuyoruz (Temiz sayfa)
    cursor.execute("DROP TABLE IF EXISTS menu")

    cursor.execute("""
    CREATE TABLE menu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kategori TEXT,
        urun_adi TEXT,
        taban_fiyat INTEGER,
        boyut_var BOOLEAN
    )
    """)

    # Açıklamaları sildik, sadece gerekli teknik veriler kaldı
    veriler = [
        # Sıcaklar
        ("Sıcak İçecekler", "Filtre Kahve", 60, True),
        ("Sıcak İçecekler", "Caffe Latte", 75, True),
        ("Sıcak İçecekler", "Espresso", 50, False), # Boyut yok
        ("Sıcak İçecekler", "Demleme Çay", 30, True),
        
        # Soğuklar
        ("Soğuk İçecekler", "Limonata", 70, True),
        ("Soğuk İçecekler", "Iced Latte", 80, True),
        ("Soğuk İçecekler", "Su", 15, False),
        
        # Tatlılar
        ("Tatlılar", "Brownie", 85, False),
        ("Tatlılar", "Kurabiye", 60, False),
        ("Tatlılar", "San Sebastian", 90, False),
        
        # Tuzlular
        ("Tuzlular", "Kaşarlı Tost", 90, False),
        ("Tuzlular", "Sandviç", 110, False)
    ]

    cursor.executemany("INSERT INTO menu (kategori, urun_adi, taban_fiyat, boyut_var) VALUES (?, ?, ?, ?)", veriler)
    conn.commit()
    conn.close()
    print("Veritabanı güncellendi: Açıklamalar silindi, fiyat yapısı hazır.")

if __name__ == "__main__":
    veritabani_guncelle()