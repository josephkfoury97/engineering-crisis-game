# CHEN212 Mission 01 — Professional Edition

A phone-first Streamlit activity for CHEN212, with:

- polished student mission flow;
- immediate feedback on taught concepts;
- drag-and-drop matching (with dropdown fallback);
- scale-up reasoning;
- individual engineering recommendation;
- ungraded readiness diagnostic in mathematics, chemistry, physics, and process reasoning;
- written reflection;
- instructor dashboard with live monitoring;
- per-student response inspection;
- class-level diagnostic snapshot;
- CSV export;
- run codes and open/close control;
- built-in QR generation;
- printable Engineering Entry Profile PDF.

## Recommended production architecture

**Streamlit Community Cloud** hosts the app.  
**Supabase** stores responses so the instructor dashboard can monitor students live and data persist across app restarts.

If Supabase secrets are absent, the app falls back to a local SQLite demo database. That is useful for local testing but is **not recommended for real class data** on Community Cloud because local files are ephemeral.

## Files

- `app.py` — complete app
- `requirements.txt` — Python dependencies
- `supabase_schema.sql` — run once in Supabase SQL Editor
- `.streamlit/secrets.example.toml` — template only; never commit real keys
- `assets/CHEN212_Engineering_Entry_Profile.pdf` — paper hand-in sheet

## Student URL

The instructor dashboard generates a URL such as:

`https://YOUR-APP.streamlit.app/?view=student&run=CHEN212-M01-F26`

and renders it as a downloadable QR code.

## Instructor URL

Open:

`https://YOUR-APP.streamlit.app/?view=instructor`

and enter the private PIN stored in Streamlit Secrets.

## Local test

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Without Supabase secrets, local test mode uses SQLite automatically.

## Production setup

1. Create a free Supabase project.
2. Open Supabase SQL Editor and run `supabase_schema.sql`.
3. Create a GitHub repository and upload this project.
4. Deploy the repository on Streamlit Community Cloud with `app.py` as the entrypoint.
5. In Streamlit App Settings -> Secrets, paste the values based on `.streamlit/secrets.example.toml`.
6. Reboot/redeploy the app if required.
7. Open `?view=instructor`, create a run code, save it, and download the QR.
8. Test the QR from a phone before class.

## Security

- Never put the Supabase server-side Secret key (or legacy service-role key) or instructor PIN in GitHub.
- Keep them in Streamlit Secrets only.
- The student-facing browser never receives those secrets; database calls run server-side in Streamlit.
