import streamlit as st
import pandas as pd
from pymongo import MongoClient
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud

# Setup MongoDB
MONGO_URI = st.secrets["MONGO_URI"]
client = MongoClient(MONGO_URI)
db = client["utercare_db"]
collection = db["article"]

# Load data dari MongoDB
data = list(collection.find())
df = pd.DataFrame(data)

if df.empty:
    st.warning("Tidak ada data artikel yang ditemukan di database.")
    st.stop()

# Preprocessing tanggal
df['tanggal_publish'] = pd.to_datetime(df['tanggal_publish'], errors='coerce')
df = df.dropna(subset=['tanggal_publish'])

# Filter keyword terkait Prolaps Uteri
keyword = ['prolaps uteri', 'turun peranakan', 'panggul', 'uterine']
df = df[df['isi'].str.lower().apply(lambda x: any(k in x for k in keyword) if isinstance(x, str) else False)]

# Hitung jumlah kata
df['jumlah_kata'] = df['isi'].apply(lambda x: len(x.split()) if isinstance(x, str) else 0)

st.title("📈 Visualisasi Artikel Prolaps Uteri")

# --- Filter Menu ---
st.sidebar.header("🔎 Filter")
tahun_list = sorted(df['tanggal_publish'].dt.year.dropna().unique())
selected_year = st.sidebar.selectbox("Pilih Tahun", options=['Semua'] + list(map(str, tahun_list)))

search_query = st.sidebar.text_input("Cari Judul Artikel")

# --- Terapkan Filter ---
if selected_year != 'Semua':
    df = df[df['tanggal_publish'].dt.year == int(selected_year)]

if search_query:
    df = df[df['title'].str.contains(search_query, case=False, na=False)]

# --- Visualisasi 1: Artikel per Bulan ---
st.subheader("1️⃣ Jumlah Artikel per Bulan")
df['bulan'] = df['tanggal_publish'].dt.to_period('M').astype(str)
monthly_counts = df.groupby('bulan').size()

fig1, ax1 = plt.subplots()
monthly_counts.plot(kind='bar', ax=ax1, color='skyblue')
ax1.set_ylabel("Jumlah Artikel")
ax1.set_xlabel("Bulan")
ax1.set_title("Artikel tentang Prolaps Uteri per Bulan")
st.pyplot(fig1)

# --- Visualisasi 2: Distribusi Panjang Artikel ---
st.subheader("2️⃣ Distribusi Panjang Artikel (Jumlah Kata)")
sns.set_theme()
fig2, ax2 = plt.subplots()
sns.histplot(df['jumlah_kata'], bins=20, kde=True, ax=ax2, color='orange')
ax2.set_title("Distribusi Panjang Artikel")
ax2.set_xlabel("Jumlah Kata")
ax2.set_ylabel("Frekuensi")
st.pyplot(fig2)

# --- Visualisasi 3: WordCloud ---
st.subheader("3️⃣ WordCloud dari Konten Artikel")
text = " ".join(df['isi'].dropna().astype(str))
wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)

fig3, ax3 = plt.subplots(figsize=(10, 5))
ax3.imshow(wordcloud, interpolation='bilinear')
ax3.axis("off")
st.pyplot(fig3)

# --- Tabel Artikel Terbaru ---
st.subheader("📋 5 Artikel Terbaru")
tabel = df.sort_values("tanggal_publish", ascending=False)[["title", "tanggal_publish", "sumber", "link"]].head(5)
tabel = tabel.rename(columns={"title": "Judul"})
tabel['tanggal_publish'] = tabel['tanggal_publish'].dt.strftime('%Y-%m-%d')
st.table(tabel)

# --- Download CSV ---
csv = df.to_csv(index=False)
st.download_button("📥 Download CSV", csv, "prolaps_articles.csv", "text/csv")
