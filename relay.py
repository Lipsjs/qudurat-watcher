import http.server
import http.cookiejar
import json
import time
import urllib.request
import urllib.parse
import urllib.error

PORT = 8787
QIYAS_BASE = "https://e-services.etec.gov.sa/Qiyas.TRAS.Web.Internet/"
CHECK_URL = QIYAS_BASE + "Test/GetAvailableCBTCentersBySessionId"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

WAIT_SECONDS = 25
MAX_ATTEMPTS = 3


def _build_cookiejar(cookie_string):
    jar = http.cookiejar.CookieJar()
    for part in cookie_string.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        name, _, value = part.partition("=")
        jar.set_cookie(http.cookiejar.Cookie(
            version=0, name=name.strip(), value=value.strip(),
            port=None, port_specified=False,
            domain="e-services.etec.gov.sa", domain_specified=True, domain_initial_dot=False,
            path="/", path_specified=True,
            secure=True, expires=None, discard=True,
            comment=None, comment_url=None, rest={},
        ))
    return jar


def check_date(opener, session_id, candidate_id, city_id, date_str):
    form = urllib.parse.urlencode({
        "sessionId": session_id,
        "candidateId": candidate_id,
        "action": "scheduleExam",
        "cityId": city_id,
        "date": date_str,
    }).encode()
    headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": QIYAS_BASE + "Test/CBTRegistration",
    }

    for attempt in range(1, MAX_ATTEMPTS + 1):
        req = urllib.request.Request(CHECK_URL, data=form, headers=headers)
        http_error_code = None
        try:
            resp = opener.open(req, timeout=20)
            raw = resp.read()
            set_cookies = resp.headers.get_all("Set-Cookie") or []
        except urllib.error.HTTPError as e:
            raw = e.read()
            set_cookies = e.headers.get_all("Set-Cookie") or []
            http_error_code = e.code
        except urllib.error.URLError as e:
            return {"date": date_str, "error": f"request_failed: {e}"}

        try:
            centers = json.loads(raw.decode("utf-8-sig", errors="ignore"))
        except json.JSONDecodeError:
            centers = None

        if isinstance(centers, list):
            available = []
            for c in centers:
                capacity = c.get("Capacity") or 0
                confirmed = c.get("ConfirmedRegisteredCandidates") or 0
                remaining = capacity - confirmed
                if c.get("IsHaveCBTCenter") or remaining > 0:
                    available.append({"name": c.get("TestCenterName", ""), "remaining": remaining})
            return {
                "date": date_str,
                "available": len(available) > 0,
                "centers": available,
                "totalCenters": len(centers),
            }

        if http_error_code in (401, 403):
            return {"date": date_str, "error": "session_expired"}

        if any("cfwaitingroom" in c.lower() for c in set_cookies):
            if attempt < MAX_ATTEMPTS:
                time.sleep(WAIT_SECONDS)
                continue
            return {"date": date_str, "error": "site_busy"}

        if http_error_code is not None:
            return {"date": date_str, "error": f"http_error_{http_error_code}"}

        return {"date": date_str, "error": "session_expired"}

    return {"date": date_str, "error": "site_busy"}


def check_slots(session_cookie, session_id, candidate_id, city_id, dates):
    jar = _build_cookiejar(session_cookie)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    results = []
    any_available = False
    for d in dates:
        d_norm = d.strip().replace("-", "/")
        if not d_norm:
            continue
        r = check_date(opener, session_id, candidate_id, city_id, d_norm)
        if "error" in r:
            return {"ok": False, "error": r["error"]}
        results.append(r)
        if r["available"]:
            any_available = True
    return {"ok": True, "results": results, "anyAvailable": any_available}


class Handler(http.server.BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        if self.path != "/check":
            self.send_response(404)
            self._cors()
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            payload = {}

        result = check_slots(
            payload.get("sessionCookie", ""),
            payload.get("sessionId", ""),
            payload.get("candidateId", ""),
            payload.get("cityId", "4"),
            payload.get("dates", []),
        )

        body = json.dumps(result).encode()
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    print(f"running at http://localhost:{PORT}")
    http.server.HTTPServer(("localhost", PORT), Handler).serve_forever()
