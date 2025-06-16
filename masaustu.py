import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as stats
import math

df_global = pd.DataFrame()

# Spor türüne göre anlamlı sütunlar
spor_sutunlari = {
    "Futbol": ["xG", "Gls", "Sh", "Cmp%", "KP", "xA"],
    "Basketbol": ["PTS", "AST", "TRB", "FG%", "3P%", "FT%", "MP", "TOV", "BLK", "STL"]
}

def varyans_guven_araligi(data, confidence=0.95):
    n = len(data)
    df = n - 1
    var = data.var()
    alpha = 1 - confidence
    chi2_lower = stats.chi2.ppf(alpha / 2, df)
    chi2_upper = stats.chi2.ppf(1 - alpha / 2, df)
    return (df * var / chi2_upper, df * var / chi2_lower)

def orneklem_boyutu_hesapla(std_dev, margin_error=0.1, confidence=0.90):
    z = stats.norm.ppf((1 + confidence) / 2)
    return math.ceil((z * std_dev / margin_error) ** 2)

def dosya_sec():
    global df_global
    dosya = filedialog.askopenfilename()
    try:
        # Önce utf-8 ile dene, olmazsa Latin-1 ve sep=";"
        try:
            df = pd.read_csv(dosya)
        except UnicodeDecodeError:
            df = pd.read_csv(dosya, encoding="ISO-8859-1", sep=";")
        df_global = df
        file_path.set(dosya)
        spor_turu_sec()
    except Exception as e:
        messagebox.showerror("Hata", str(e))

def spor_turu_sec(*args):
    secili_spor = spor_secim.get()
    if secili_spor not in spor_sutunlari:
        return

    numeric_cols = df_global.select_dtypes(include=['float64', 'int64']).columns.tolist()
    mantikli = [col for col in numeric_cols if col in spor_sutunlari[secili_spor]]
    combo_box['values'] = mantikli
    if mantikli:
        combo_box.current(0)
    else:
        combo_box.set('')
        messagebox.showwarning("Uyarı", f"{secili_spor} için uygun sayısal sütun bulunamadı.")

def analiz_yap():
    try:
        col = combo_box.get()
        data = df_global[col].dropna()

        mean = data.mean()
        median = data.median()
        std = data.std()
        var = data.var()
        se = std / math.sqrt(len(data))

        z = stats.norm.ppf(0.975)
        moe = z * se
        ci_mean = (mean - moe, mean + moe)

        ci_var = varyans_guven_araligi(data)
        t_stat, p_val = stats.ttest_1samp(data, 1.5)
        h_karar = "H₀ REDDEDİLİR" if p_val < 0.05 else "H₀ REDDEDİLEMEZ"
        n_required = orneklem_boyutu_hesapla(std)

        output_text.set(
            f"Sütun: {col}\n"
            f"Ortalama: {mean:.3f}\n"
            f"Medyan: {median:.3f}\n"
            f"Varyans: {var:.3f}\n"
            f"Std Sapma: {std:.3f}\n"
            f"Std Hata: {se:.3f}\n"
            f"95% Güven Aralığı (Ortalama): {ci_mean}\n"
            f"95% Güven Aralığı (Varyans): {ci_var}\n"
            f"t: {t_stat:.3f}, p: {p_val:.5f}\n"
            f"Hipotez Sonucu: {h_karar}\n"
            f"Gerekli Örneklem (90%, ±0.1): {n_required}"
        )

    except Exception as e:
        messagebox.showerror("Analiz Hatası", str(e))

def grafik_goster():
    try:
        col = combo_box.get()
        data = df_global[col].dropna()

        plt.figure(figsize=(8, 5))
        plt.hist(data, bins=30, edgecolor='black')
        plt.title(f"{col} Histogramı")
        plt.xlabel(col)
        plt.ylabel("Oyuncu Sayısı")
        plt.grid(True)
        plt.show()

        plt.figure(figsize=(6, 4))
        plt.boxplot(data, vert=False)
        plt.title(f"{col} Boxplot")
        plt.grid(True)
        plt.show()
    except Exception as e:
        messagebox.showerror("Grafik Hatası", str(e))

# GUI Arayüzü
pencere = tk.Tk()
pencere.title("Spor Türüne Göre Otomatik Veri Analizi")

file_path = tk.StringVar()
output_text = tk.StringVar()

tk.Label(pencere, text="CSV Dosyası:").pack()
tk.Entry(pencere, textvariable=file_path, width=50).pack()
tk.Button(pencere, text="Dosya Seç", command=dosya_sec).pack(pady=5)

tk.Label(pencere, text="Spor Türü Seçin:").pack()
spor_secim = ttk.Combobox(pencere, values=list(spor_sutunlari.keys()), state="readonly")
spor_secim.bind("<<ComboboxSelected>>", spor_turu_sec)
spor_secim.pack(pady=5)

tk.Label(pencere, text="Analiz Edilecek Sütun:").pack()
combo_box = ttk.Combobox(pencere, state="readonly")
combo_box.pack(pady=5)

tk.Button(pencere, text="Analizi Yap", command=analiz_yap).pack(pady=5)
tk.Button(pencere, text="Grafikleri Göster", command=grafik_goster).pack(pady=5)
tk.Label(pencere, textvariable=output_text, justify="left", fg="blue").pack(pady=10)

pencere.mainloop()
