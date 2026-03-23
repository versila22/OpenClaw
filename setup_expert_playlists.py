import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

def get_spotify_client():
    # Suppression du cache pour assurer les bons scopes
    if os.path.exists(".cache"):
        os.remove(".cache")
    scope = "playlist-modify-public playlist-modify-private playlist-read-private"
    return spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, open_browser=False))

def fill_playlist(sp, playlist_name, queries):
    playlists = sp.current_user_playlists()
    playlist_id = None
    for pl in playlists['items']:
        if pl['name'] == playlist_name:
            playlist_id = pl['id']
            break
    
    if not playlist_id:
        print(f"❌ Playlist '{playlist_name}' non trouvée. Crée-la manuellement d'abord.")
        return

    print(f"⌛ Remplissage de '{playlist_name}'...")
    track_ids = []
    for q in queries:
        results = sp.search(q=q, type='track', limit=1)
        if results['tracks']['items']:
            tid = results['tracks']['items'][0]['id']
            track_ids.append(tid)
            print(f"   + {results['tracks']['items'][0]['name']}")
            
            # Spotify limite à 100 items par ajout
            if len(track_ids) >= 50:
                sp.playlist_add_items(playlist_id, track_ids)
                track_ids = []
                
    if track_ids:
        sp.playlist_add_items(playlist_id, track_ids)
    print(f"✅ Terminé pour '{playlist_name}'.")

def setup_expert_playlists():
    sp = get_spotify_client()
    
    # 1. Match +9 ans (Public 9-65 ans) - 50 titres
    # Mix intergénérationnel : Tubes 70s-2025, énergie positive, ultra-lisible.
    match_9_queries = [
        # Nouveautés / Actuel (2020-2025)
        "Rosé Bruno Mars APT", "Benson Boone Beautiful Things", "Sabrina Carpenter Espresso", 
        "Dua Lipa Levitating", "The Weeknd Blinding Lights", "Harry Styles As It Was",
        "Miley Cyrus Flowers", "Taylor Swift Shake It Off", "Imagine Dragons Believer",
        "BTS Dynamite", "Ed Sheeran Bad Habits", "Gracie Abrams That's So True",
        # Classiques 2000-2010
        "Black Eyed Peas I Gotta Feeling", "Pharrell Williams Happy", "Justin Timberlake Can't Stop the Feeling",
        "Mark Ronson Bruno Mars Uptown Funk", "Beyoncé Crazy In Love", "OutKast Hey Ya!",
        "Lady Gaga Poker Face", "Rihanna Umbrella", "Katy Perry Roar", "Coldplay Viva La Vida",
        # Légendes 80s-90s
        "Michael Jackson Billie Jean", "Cyndi Lauper Girls Just Want to Have Fun", "A-Ha Take on Me",
        "Whitney Houston I Wanna Dance with Somebody", "Bon Jovi Livin' on a Prayer", "Journey Don't Stop Believin'",
        "Queen Don't Stop Me Now", "Spice Girls Wannabe", "Will Smith Gettin' Jiggy wit It",
        "Smash Mouth All Star", "Kool & The Gang Celebration", "Wham! Wake Me Up Before You Go-Go",
        # Fondations 70s
        "ABBA Dancing Queen", "ABBA Gimme! Gimme! Gimme!", "Earth Wind & Fire September",
        "Village People YMCA", "Bee Gees Stayin' Alive", "Gloria Gaynor I Will Survive",
        "Boney M Daddy Cool", "Stevie Wonder Superstition", "Chic Le Freak",
        # French Crowd Pleasers (Bonus France)
        "Indochine L'aventurier", "Jean-Jacques Goldman Envole-moi", "Céline Dion J'irai où tu iras",
        "Louise Attaque J't'emmène au vent", "Daft Punk One More Time", "Daft Punk Get Lucky",
        "Stromae Alors on danse"
    ]
    
    # 2. Cabaret +16 ans (Public 16-50 ans) - 50 titres
    # Ambiance feutrée, suggestive, plus rock, indie ou dark pop.
    cabaret_16_queries = [
        # Dark Pop & Alternative Actuelle
        "Billie Eilish bad guy", "Billie Eilish Birds of a Feather", "Chappell Roan Pink Pony Club",
        "Lana Del Rey Summertime Sadness Remix", "Doja Cat Paint The Town Red", "The Weeknd Save Your Tears",
        "Tove Lo Habits", "Arctic Monkeys Do I Wanna Know?", "Måneskin I Wanna Be Your Slave",
        "Kendrick Lamar Not Like Us", "SZA Kill Bill", "Lorde Royals",
        # Rock & Indie Classiques
        "The White Stripes Seven Nation Army", "The Killers Mr. Brightside", "Gorillaz Feel Good Inc",
        "Nirvana Smells Like Teen Spirit", "Radiohead Creep", "The Strokes Reptilia",
        "Franz Ferdinand Take Me Out", "Muse Supermassive Black Hole", "Blur Song 2",
        "Florence + The Machine Dog Days Are Over", "Amy Winehouse Back to Black", "Amy Winehouse Rehab",
        # Vibe Suggestive / Jazzy / Cabaret
        "Portishead Glory Box", "Massive Attack Teardrop", "Nancy Sinatra These Boots Are Made for Walkin'",
        "Peggy Lee Fever", "Shirley Bassey Big Spender", "Liza Minnelli Mein Herr",
        "Eurythmics Sweet Dreams", "Depeche Mode Enjoy the Silence", "Soft Cell Tainted Love",
        "Nina Simone Feeling Good", "Chet Faker Gold", "Alt-J Breezeblocks",
        # French Vibe 16-50
        "L'Impératrice Agitations tropicales", "Angèle Bruxelles je t'aime", "Clara Luciani La grenade",
        "Gossip Standing in the Way of Control", "MIA Paper Planes", "MGMT Kids",
        "Phoenix Lisztomania", "Daft Punk Instant Crush", "Justice D.A.N.C.E.",
        "Kavinsky Nightcall", "Stromae Papaoutai", "Orelsan La Terre est ronde",
        "Woodkid Iron", "The Gossip Heavy Cross", "Placebo Every You Every Me"
    ]

    fill_playlist(sp, "Impro - Match +9", match_9_queries)
    fill_playlist(sp, "Impro - Cabaret +16", cabaret_16_queries)

if __name__ == "__main__":
    setup_expert_playlists()
