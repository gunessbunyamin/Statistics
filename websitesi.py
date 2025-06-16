import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as stats
import math

# Anlamlı sütunlar
spor_sutunlari = {
    "Futbol": ["xG", "Gls", "Sh", "Cmp%", "KP", "xA"],
    "Basketbol": ["PTS", "AST", "TRB", "FG%", "3P%", "FT%", "MP", "TOV", "BLK", "STL"]
}

# Güven aralıkları fonksiyonu
def varyans_guven_araligi(data, confidence=0.95):
    n = len(data)
    df = n - 1
    var = data.var()
    alpha = 1 - confidence
    chi2_lower = stats.chi2.ppf(alpha / 2, df)
    chi2_upper = stats.chi2.ppf(1 - alpha / 2, df)
    return (df * var / chi2_upper, df * var / chi2_lower)

# Örneklem boyutu hesaplama
def orneklem_boyutu_hesapla(std_dev, margin_error=0.1, confidence=0.90):
    z = stats.norm.ppf((1 + confidence) / 2)
    return math.ceil((z * std_dev / margin_error) ** 2)

st.title("Spor Verileri Analizi")

uploaded_file = st.file_uploader("CSV Dosyası Yükle", type=["csv"])
if uploaded_file:
    try:
        # 1) Önce UTF-8, otomatik ayraç (sep=None, engine='python') dene
        try:
            df = pd.read_csv(
                uploaded_file,
                sep=None,            # otomatik delimiter bulsun
                engine="python",     # sep=None için python motoru gerekli
                encoding="utf-8"     # önce UTF-8 dene
            )
        except Exception:
            # Eğer UTF-8 + sep=None işe yaramazsa, Latin-1 + noktalı virgül ayraç dene
            uploaded_file.seek(0)
            df = pd.read_csv(
                uploaded_file,
                sep=";",             # noktalı virgül ayracı
                engine="python",
                encoding="ISO-8859-1"
            )

        # Sütun adlarını baş/son boşluklardan temizle
        df.columns = df.columns.str.strip()

        # Sadece object (muhtemel sayısal string) sütunları sayısala çevir
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Spor türü seçimi
        sport = st.selectbox("Spor Türü Seçin", list(spor_sutunlari.keys()))

        # Anlamlı ve sayısal olan sütunları seç
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        mantikli = [col for col in numeric_cols if col in spor_sutunlari[sport]]

        if mantikli:
            col = st.selectbox("Analiz Edilecek Sütun", mantikli)
            data = df[col].dropna()

            # Hesaplamalar
            mean = data.mean()
            median = data.median()
            std = data.std()
            var = data.var()
            se = std / math.sqrt(len(data))

            # Ortalama için %95 güven aralığı
            z = stats.norm.ppf(0.975)
            moe = z * se
            ci_mean = (mean - moe, mean + moe)

            # Varyans için %95 güven aralığı
            ci_var = varyans_guven_araligi(data)

            # Örnek bir H0: ortalama = 1.5 testi
            t_stat, p_val = stats.ttest_1samp(data, 1.5)
            h_karar = "H₀ REDDEDİLİR" if p_val < 0.05 else "H₀ REDDEDİLEMEZ"

            # Örneklem boyutu hesaplama (90% güven, ±0.1 hata payı)
            n_required = orneklem_boyutu_hesapla(std)

            # Sonuçları yazdır
            st.markdown(f"""
            **Sütun**: {col}  
            **Ortalama**: {mean:.3f}  
            **Medyan**: {median:.3f}  
            **Varyans**: {var:.3f}  
            **Std Sapma**: {std:.3f}  
            **Std Hata**: {se:.3f}  
            **95% Güven Aralığı (Ortalama)**: {ci_mean}  
            **95% Güven Aralığı (Varyans)**: {ci_var}  
            **t**: {t_stat:.3f}, **p**: {p_val:.5f}  
            **Hipotez Sonucu**: {h_karar}  
            **Gerekli Örneklem (90%, ±0.1)**: {n_required}  
            """)

            # Histogram
            fig, ax = plt.subplots()
            ax.hist(data, bins=30, edgecolor='black')
            ax.set_title(f"{col} Histogramı")
            st.pyplot(fig)

            # Boxplot
            fig, ax = plt.subplots()
            ax.boxplot(data, vert=False)
            ax.set_title(f"{col} Boxplot")
            st.pyplot(fig)

        else:
            st.warning(
                "Uygun sayısal sütun bulunamadı. "
                "Lütfen veri setinizde seçili spor türüne ait sayısal sütunlar olduğundan emin olun."
            )

    except Exception as e:
        st.error(f"Dosya okunurken ya da analiz yapılırken hata oluştu:\n{e}")
