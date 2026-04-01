import pickle
import requests
import streamlit as st
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import base64

API_KEY = st.secrets["TMDB_API_KEY"]

movies = pickle.load(open('movie_list.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))

# ── Background ──────────────────────────────────────────────────────────────
def set_background(image_path):
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    css = f"""
    <style>
    .stApp {{
        background-image: url("data:image/webp;base64,{encoded}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}

    /* Dark overlay so text stays readable */
    .stApp::before {{
        content: "";
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background: rgba(0, 0, 0, 0.55);
        z-index: 0;
    }}

    /* Keep content above the overlay */
    .stApp > * {{
        position: relative;
        z-index: 1;
    }}

    /* Title styling */
    h1 {{
        color: #f5c518 !important;
        text-align: center;
        font-size: 3rem !important;
    }}

    /* Movie name text */
    .stText, p {{
        color: white !important;
        font-weight: 600;
        text-align: center;
    }}

    /* Dropdown label */
    label {{
        color: white !important;
        font-size: 1.1rem !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


# ── HTTP Session with retries ────────────────────────────────────────────────
def create_session():
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    })
    return session

session = create_session()


# ── Fetch poster from TMDB ───────────────────────────────────────────────────
def fetch_poster(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}"
        data = session.get(url, timeout=10)
        data.raise_for_status()
        json_data = data.json()
        poster_path = json_data.get('poster_path')
        if poster_path:
            return "https://image.tmdb.org/t/p/w500/" + poster_path
        return "https://via.placeholder.com/500x750?text=No+Poster"
    except Exception as e:
        st.warning(f"Could not fetch poster for movie ID {movie_id}: {e}")
        return "https://via.placeholder.com/500x750?text=No+Poster"


# ── Recommend movies ─────────────────────────────────────────────────────────
def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_movie_names = []
    recommended_movie_posters = []
    for i in distances[1:6]:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movie_posters.append(fetch_poster(movie_id))
        recommended_movie_names.append(movies.iloc[i[0]].title)
    return recommended_movie_names, recommended_movie_posters


# ── App ──────────────────────────────────────────────────────────────────────
set_background("86f199d0c6f5cedd14c121164fa5fafc.webp")

st.title("🎬 Movie Recommendation System")

movie_list = movies['title'].values
selected_movie = st.selectbox(
    "Type or select a movie from the dropdown",
    movie_list
)

if st.button('Show Recommendation'):
    with st.spinner("Fetching recommendations..."):
        recommended_movie_names, recommended_movie_posters = recommend(selected_movie)

    cols = st.columns(5)
    for col, name, poster in zip(cols, recommended_movie_names, recommended_movie_posters):
        with col:
            st.text(name)
            st.image(poster)