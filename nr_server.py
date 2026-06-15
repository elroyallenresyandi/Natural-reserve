"""
Natural Reserve — Local Token Server v2
Handles: session token auth + static files + Gmail SMTP email API
"""

import sys, os, threading, time, mimetypes, json, secrets, smtplib
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ════════════════════════════════════════════
#  KONFIGURASI GMAIL
#  Isi dengan email & App Password Gmail Anda
#  Cara buat App Password:
#  myaccount.google.com → Keamanan → Sandi Aplikasi
# ════════════════════════════════════════════
GMAIL_SENDER   = "allenresyandi@gmail.com"       # ← Ganti dengan Gmail Anda
GMAIL_APP_PASS = "123456789"       # ← Ganti dengan App Password
ADMIN_NAME     = "Admin Natural Reserve"

# ════════════════════════════════════════════
#  KONFIGURASI SERVER
# ════════════════════════════════════════════
if len(sys.argv) < 3:
    print("Usage: nr_server.py <token> <port>")
    sys.exit(1)

VALID_TOKEN  = sys.argv[1]
PORT         = int(sys.argv[2])
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
ACTIVE_SESS  = set()
MAX_LIFETIME = 3600  # 1 jam

mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
SESSION_COOKIE = "nr_sess"


# ════════════════════════════════════════════
#  EMAIL TEMPLATE
# ════════════════════════════════════════════
def build_email_html(name, username, code):
    return f"""<!DOCTYPE html>
<html lang="id">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kode Akses Natural Reserve</title></head>
<body style="margin:0;padding:0;background:#051a26;font-family:'DM Sans',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#051a26;padding:40px 16px;">
  <tr><td align="center">
    <table width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;">

      <!-- HEADER -->
      <tr><td style="text-align:center;padding-bottom:32px;">
        <div style="display:inline-block;background:linear-gradient(135deg,#0d9488,#0a4a5e);
          border-radius:16px;width:64px;height:64px;line-height:64px;font-size:30px;
          box-shadow:0 0 24px rgba(13,148,136,.4);">🐟</div>
        <h1 style="font-family:Arial,sans-serif;font-size:24px;font-weight:800;
          color:#5eead4;margin:16px 0 4px;">Natural Reserve</h1>
        <p style="color:#64748b;font-size:13px;margin:0;">Fish Feeding Calculator</p>
      </td></tr>

      <!-- CARD -->
      <tr><td style="background:rgba(10,40,56,.8);border:1px solid rgba(13,148,136,.2);
        border-radius:12px;padding:32px;box-shadow:0 8px 40px rgba(0,0,0,.4);">

        <p style="color:#94a3b8;font-size:13px;margin:0 0 8px;">Halo, <strong style="color:#e0f7f4;">{name}</strong> 👋</p>
        <p style="color:#94a3b8;font-size:13px;margin:0 0 24px;line-height:1.7;">
          Permintaan akses Anda ke sistem <strong style="color:#5eead4;">Natural Reserve</strong>
          telah <strong style="color:#5eead4;">disetujui</strong> oleh administrator.
          Berikut adalah kode akses unik Anda:
        </p>

        <!-- CODE BOX -->
        <div style="background:rgba(13,148,136,.08);border:1.5px solid rgba(13,148,136,.3);
          border-radius:10px;padding:24px;text-align:center;margin-bottom:24px;">
          <div style="font-size:11px;color:#64748b;letter-spacing:.1em;text-transform:uppercase;
            margin-bottom:10px;font-family:monospace;">Kode Akses Anda</div>
          <div style="font-family:'Courier New',monospace;font-size:32px;font-weight:700;
            color:#5eead4;letter-spacing:.25em;text-shadow:0 0 20px rgba(94,234,212,.3);">{code}</div>
          <div style="font-size:11px;color:#64748b;margin-top:10px;">
            Kode bersifat <strong style="color:#f59e0b;">permanen</strong> dan unik untuk akun Anda
          </div>
        </div>

        <!-- INFO -->
        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;">
          <tr>
            <td style="background:rgba(5,26,38,.6);border:1px solid rgba(13,148,136,.15);
              border-radius:8px;padding:14px;">
              <p style="margin:0 0 8px;font-size:11px;color:#64748b;letter-spacing:.08em;text-transform:uppercase;">Informasi Login</p>
              <p style="margin:0 0 4px;font-size:13px;color:#94a3b8;">
                👤 Username: <strong style="color:#e0f7f4;font-family:monospace;">{username}</strong>
              </p>
              <p style="margin:0;font-size:13px;color:#94a3b8;">
                🔑 Kode Akses: <strong style="color:#5eead4;font-family:monospace;">{code}</strong>
              </p>
            </td>
          </tr>
        </table>

        <!-- CARA LOGIN -->
        <div style="background:rgba(13,148,136,.05);border-left:3px solid #0d9488;
          border-radius:0 8px 8px 0;padding:14px 16px;margin-bottom:24px;">
          <p style="margin:0 0 8px;font-size:12px;font-weight:700;color:#5eead4;">Cara Login:</p>
          <ol style="margin:0;padding-left:18px;color:#94a3b8;font-size:12px;line-height:2;">
            <li>Buka aplikasi melalui file <code style="color:#5eead4;">buka_aplikasi.bat</code></li>
            <li>Masukkan username: <code style="color:#e0f7f4;">{username}</code></li>
            <li>Masukkan kode akses di atas</li>
            <li>Klik <strong style="color:#5eead4;">Masuk</strong></li>
          </ol>
        </div>

        <p style="color:#475569;font-size:11px;line-height:1.7;margin:0;">
          ⚠️ <strong style="color:#f59e0b;">Jaga kerahasiaan kode ini.</strong>
          Jangan bagikan kepada siapa pun. Jika kode Anda bocor atau perlu diganti,
          hubungi administrator segera.
        </p>
      </td></tr>

      <!-- FOOTER -->
      <tr><td style="text-align:center;padding-top:24px;">
        <p style="color:#1e3a4a;font-size:11px;margin:0;line-height:1.8;">
          Email ini dikirim otomatis oleh sistem Natural Reserve<br>
          Jika Anda tidak merasa mengajukan permintaan ini, abaikan email ini.
        </p>
      </td></tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""


def send_gmail(to_email, name, username, code):
    """Kirim email via Gmail SMTP."""
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🔑 Kode Akses Natural Reserve — {username}"
    msg['From']    = f"{ADMIN_NAME} <{GMAIL_SENDER}>"
    msg['To']      = to_email

    text_body = f"""Halo {name},

Permintaan akses Anda ke Natural Reserve telah disetujui.

Kode Akses Anda: {code}
Username       : {username}

Cara login:
1. Buka aplikasi melalui buka_aplikasi.bat
2. Masukkan username: {username}
3. Masukkan kode akses: {code}
4. Klik Masuk

Jaga kerahasiaan kode ini.

— Admin Natural Reserve
"""
    msg.attach(MIMEText(text_body, 'plain'))
    msg.attach(MIMEText(build_email_html(name, username, code), 'html'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(GMAIL_SENDER, GMAIL_APP_PASS)
        server.sendmail(GMAIL_SENDER, to_email, msg.as_string())


# ════════════════════════════════════════════
#  HTTP HANDLER
# ════════════════════════════════════════════
class NRHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # suppress logs

    def send_forbidden(self, msg="Akses Ditolak"):
        body = f"""<!DOCTYPE html><html lang="id"><head><meta charset="UTF-8">
<title>Akses Ditolak</title>
<style>body{{font-family:sans-serif;background:#051a26;color:#e0f7f4;
  display:flex;align-items:center;justify-content:center;height:100vh;margin:0}}
.box{{text-align:center;padding:40px;border:1px solid rgba(244,63,94,.3);
  border-radius:12px;background:rgba(244,63,94,.05)}}
h1{{color:#f43f5e;font-size:48px;margin:0 0 8px}}p{{color:#94a3b8;margin:4px 0}}
small{{color:#475569;font-size:11px}}</style></head><body>
<div class="box"><h1>⛔</h1><h2>{msg}</h2>
<p>Buka aplikasi melalui <strong>buka_aplikasi.bat</strong></p>
<small>URL langsung tidak diizinkan tanpa sesi yang valid.</small>
</div></body></html>""".encode()
        self.send_response(403)
        self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control","no-store")
        self.end_headers()
        self.wfile.write(body)

    def get_session(self):
        cookies = self.headers.get("Cookie","")
        for part in cookies.split(";"):
            part = part.strip()
            if part.startswith(SESSION_COOKIE + "="):
                return part[len(SESSION_COOKIE)+1:]
        return None

    def serve_file(self, filepath, session_id=None):
        if not os.path.isfile(filepath):
            self.send_response(404); self.end_headers()
            self.wfile.write(b"File tidak ditemukan."); return
        mime, _ = mimetypes.guess_type(filepath)
        mime = mime or "application/octet-stream"
        with open(filepath,"rb") as f: data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control","no-store")
        if session_id:
            self.send_header("Set-Cookie",
                f"{SESSION_COOKIE}={session_id}; Path=/; HttpOnly; SameSite=Strict")
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Cache-Control","no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","POST,GET,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/send-email":
            self.handle_send_email()
        else:
            self.send_response(404); self.end_headers()

    def handle_send_email(self):
        try:
            length = int(self.headers.get("Content-Length",0))
            body   = json.loads(self.rfile.read(length))
            to     = body.get("to","")
            name   = body.get("name","")
            username = body.get("username","")
            code   = body.get("code","")
            if not all([to, name, username, code]):
                self.send_json(400, {"ok": False, "error": "Field tidak lengkap"})
                return
            send_gmail(to, name, username, code)
            self.send_json(200, {"ok": True, "message": f"Email terkirim ke {to}"})
        except smtplib.SMTPAuthenticationError:
            self.send_json(500, {"ok": False, "error":
                "Autentikasi Gmail gagal. Periksa GMAIL_SENDER dan GMAIL_APP_PASS di nr_server.py"})
        except Exception as e:
            self.send_json(500, {"ok": False, "error": str(e)})

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path.lstrip("/")
        params = parse_qs(parsed.query)
        token  = params.get("t", [None])[0]
        sess   = self.get_session()

        # ── API endpoint ──
        if parsed.path.startswith("/api/"):
            self.send_json(404, {"error": "Not found"}); return

        # ── HTML pages — butuh sesi ──
        if path in ("", "login.html", "index.html", "admin.html") or not path:
            if sess and sess in ACTIVE_SESS:
                target = path if path else "login.html"
                self.serve_file(os.path.join(BASE_DIR, target)); return
            if token and token == VALID_TOKEN:
                new_sess = secrets.token_hex(24)
                ACTIVE_SESS.add(new_sess)
                target = path if path else "login.html"
                self.send_response(302)
                self.send_header("Location", f"/{target}")
                self.send_header("Set-Cookie",
                    f"{SESSION_COOKIE}={new_sess}; Path=/; HttpOnly; SameSite=Strict")
                self.send_header("Cache-Control","no-store")
                self.end_headers(); return
            self.send_forbidden("Sesi Tidak Valid"); return

        # ── Static files ──
        if sess and sess in ACTIVE_SESS:
            filepath = os.path.join(BASE_DIR, path)
            if not os.path.abspath(filepath).startswith(BASE_DIR):
                self.send_forbidden("Path Tidak Diizinkan"); return
            self.serve_file(filepath); return

        self.send_forbidden("Sesi Tidak Valid")


def auto_shutdown():
    time.sleep(MAX_LIFETIME)
    print(f"\n[NR Server] Sesi berakhir ({MAX_LIFETIME//60} menit). Server dimatikan.")
    os._exit(0)


if __name__ == "__main__":
    threading.Thread(target=auto_shutdown, daemon=True).start()
    server = HTTPServer(("127.0.0.1", PORT), NRHandler)
    print(f"[NR Server] Berjalan di http://127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[NR Server] Dihentikan.")
        sys.exit(0)
