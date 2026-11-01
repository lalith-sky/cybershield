"""
CyberShield AI - Application Entrypoint
------------------------------------------
This file is intentionally thin. All real logic now lives in the `app/`
package (Blueprints, services, database models) so it can grow without
turning into a single giant file again.

Run exactly as before:
    python run.py

The old single-file implementation is preserved at
app_legacy_backup.py.bak for reference / diffing.
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
