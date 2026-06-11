# Can You Think Like an Engineer? — Public Online Event Version

This version is designed for the event situation where students use **mobile data** or a different Wi‑Fi network.

Your laptop and the phones must open the **same public deployed Streamlit app**. Do not run only from your laptop if students are on mobile data.

## 1. Install locally for testing
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 2. Deploy online using Streamlit Community Cloud
1. Create a GitHub repository.
2. Upload these files:
   - `app.py`
   - `requirements.txt`
   - `README.md`
3. Go to Streamlit Community Cloud.
4. Create a new app from your GitHub repository.
5. Set the main file path to:
   ```text
   app.py
   ```
6. Deploy.

You will get a public link, for example:
```text
https://your-engineering-crisis-game.streamlit.app
```

## 3. Add your public URL to Streamlit Secrets
In Streamlit Cloud, open your app settings and add this secret:
```toml
PUBLIC_APP_URL = "https://your-engineering-crisis-game.streamlit.app"
```

Restart the app after adding the secret.

## 4. Event setup
On your laptop, open the public app link and choose:
```text
Host Screen + Live Leaderboard
```

The app will show a QR code. Students scan it and play from any network/mobile data.

Your laptop leaderboard updates live because everyone is using the same online app.

## 5. Leaderboard behavior
Each player name appears only once. If the exact same name plays again, their previous score is replaced by the newest score.

## Important note
The built-in JSON leaderboard is suitable for an event session. If Streamlit Cloud restarts the app, the leaderboard may reset. For a normal 2-hour event, this is usually fine. For permanent storage, the app can be upgraded later to Google Sheets, Supabase, or Firebase.
