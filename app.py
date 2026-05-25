import streamlit as st
import pandas as pd
import joblib
import urllib.parse
import requests

# ==========================================
# 1. SETUP HALAMAN & TEMA PREMIUM
# ==========================================
st.set_page_config(page_title="AI Movie Discovery", page_icon="🍿", layout="wide")

st.markdown("""
    <style>
    /* Background utama & Font */
    .main { background-color: #0b0b0c; color: #ffffff; }
    
    /* MODIFIKASI SIDEBAR (Glassmorphism Look) */
    section[data-testid="stSidebar"] {
        background-color: #111112;
        border-right: 1px solid #333;
    }
    
    /* Judul & Header */
    h1, h2, h3 { color: #E50914 !important; font-weight: 800 !important; }
    .st-emotion-cache-10o1f27 { color: #E50914 !important; }

    /* Gaya Label Input Sidebar */
    .stSlider label, .stNumberInput label, .stSelectbox label {
        color: #e0e0e0 !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
    }

    /* Kustomisasi Input */
    .stSelectbox div[data-baseweb="select"], .stNumberInput div[data-baseweb="input"] {
        background-color: #1a1a1b !important;
        border: 1px solid #444 !important;
        border-radius: 10px !important;
    }
    
    /* Tombol Utama (Netflix Red Style) */
    div.stButton > button:first-child {
        background-color: #E50914;
        color: white;
        width: 100%;
        border-radius: 10px;
        border: none;
        padding: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(229, 9, 20, 0.4);
        margin-top: 20px;
    }
    
    div.stButton > button:first-child:hover {
        background-color: #ff0f1a;
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(229, 9, 20, 0.6);
    }

    /* Movie Title Styling */
    .movie-title {
        font-size: 1rem;
        font-weight: 700;
        margin-top: 12px;
        margin-bottom: 2px;
        color: #ffffff;
        display: -webkit-box;
        -webkit-line-clamp: 1;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }

    /* Metric/Rating Box */
    div[data-testid="metric-container"] {
        background-color: #1a1a1a;
        border: 1px solid #333;
        padding: 8px 12px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. KONFIGURASI API & MODEL
# ==========================================
# GANTI DENGAN API KEY TMDB ASLI ANDA
TMDB_API_KEY = "MASUKKAN_API_KEY_KAMU_DISINI" 

@st.cache_resource
def load_model():
    return joblib.load('model_pdm_terbaik.pkl')

@st.cache_data
def load_data():
    df = pd.read_csv('tmdb_movies_dataset.csv')
    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
    df['release_year'] = df['release_date'].dt.year
    df['release_month'] = df['release_date'].dt.month
    df = df.dropna(subset=['title', 'release_year', 'release_month', 'popularity', 'vote_count', 'movie_id'])
    df = df.drop_duplicates(subset=['title'])
    return df

@st.cache_data
def fetch_poster(movie_id):
    if not TMDB_API_KEY or TMDB_API_KEY == "MASUKKAN_API_KEY_KAMU_DISINI":
        return None
    try:
        url = f"https://api.themoviedb.org/3/movie/{int(movie_id)}?api_key={TMDB_API_KEY}&language=en-US"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            path = res.json().get('poster_path')
            if path: return f"https://image.tmdb.org/t/p/w500{path}"
    except: pass
    return None

# ==========================================
# 3. SIDEBAR (CONTROL PANEL)
# ==========================================
with st.sidebar:
    st.markdown("## 🎬 **Control Panel**")
    st.markdown("---")
    
    try:
        df_movies = load_data()
        model = load_model()
        
        min_y, max_y = int(df_movies['release_year'].min()), int(df_movies['release_year'].max())
        
        st.markdown("🔍 **Filter Film**")
        year_range = st.slider("📅 Rentang Tahun Rilis", min_y, max_y, (2018, 2024))
        min_pop = st.number_input("🔥 Minimal Popularitas", min_value=0, value=25)
        
        st.markdown("---")
        st.markdown("📊 **Tampilan**")
        top_n = st.selectbox("Jumlah Rekomendasi", [5, 10, 15], index=0)
        
        btn_cari = st.button("Cari Rekomendasi ✨")
        
        st.markdown("---")
        st.caption("🤖 **AI Model:** Random Forest")
        st.caption("📈 **Fitur:** Popularity, Votes, Year, Month")
        
    except Exception as e:
        st.error(f"Error: {e}")
        st.stop()

# ==========================================
# 4. MAIN CONTENT AREA
# ==========================================
st.title("🍿 AI Movie Recommendation")
st.markdown("Gunakan panel di sebelah kiri untuk menyesuaikan minatmu dan biarkan AI kami bekerja.")

btn_cari = st.button("Cari Film")
if btn_cari:
    # Filter data berdasarkan input user
    data_filter = df_movies[
        (df_movies['release_year'] >= year_range[0]) & 
        (df_movies['release_year'] <= year_range[1]) &
        (df_movies['popularity'] >= min_pop)
    ].copy()

    if data_filter.empty:
        st.warning("⚠️ Tidak ada film yang ditemukan. Coba perkecil filter popularitas.")
    else:
        with st.spinner('AI sedang memprediksi film terbaik untukmu...'):
            # Prediksi rating (4 Fitur)
            X = data_filter[['popularity', 'vote_count', 'release_year', 'release_month']]
            data_filter['predicted_rating'] = model.predict(X)
            
            # Urutkan berdasarkan prediksi tertinggi
            result = data_filter.sort_values(by='predicted_rating', ascending=False).head(top_n)

        st.subheader(f"🏆 Top {top_n} Hasil Prediksi AI")
        st.write("")
        
        # Grid System (5 kolom)
        cols = st.columns(5)
        
        for i, (idx, row) in enumerate(result.iterrows()):
            with cols[i % 5]:
                # Poster logic
                poster = fetch_poster(row['movie_id'])
                if poster:
                    st.image(poster, use_container_width=True)
                else:
                    # Placeholder premium abu-abu gelap
                    st.image("https://placehold.co/300x450/1a1a1a/666666?text=No+Poster", use_container_width=True)
                
                # Detail Movie
                st.markdown(f"<p class='movie-title'>{row['title']}</p>", unsafe_allow_html=True)
                st.caption(f"📅 {int(row['release_year'])} • 🌙 Bln: {int(row['release_month'])}")
                st.metric("AI Score", f"{row['predicted_rating']:.2f} ⭐")
                
                with st.expander("📊 Statistik Data"):
                    st.write(f"**Vote Count:** {int(row['vote_count'])}")
                    st.write(f"**Popularity:** {row['popularity']}")
                    st.write(f"**Rating Asli:** {row['rating']} ⭐")
        st.divider()
else:
    st.info("👈 Silakan atur kriteria di sidebar dan klik 'Cari Rekomendasi' untuk melihat keajaiban AI!")

st.markdown("<br><center><p style='color: #555;'>Eksperimen PDM 2024 - AI Movie Prediction System</p></center>", unsafe_allow_html=True)