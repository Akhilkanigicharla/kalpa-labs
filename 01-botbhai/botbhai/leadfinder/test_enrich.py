import importlib.util
# Run: python3 leadfinder/test_enrich.py — offline, local test server
import http.server, os, sys, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import enrich as E
PAGES = {"/robots.txt": "User-agent: *\nDisallow: /private\n",
         "/": '<a href="mailto:hello@glowstudio.in">mail</a> <a href="https://wa.me/919876543210">WhatsApp</a> <a href="https://instagram.com/glowstudio.hyd">IG</a>',
         "/private": "secret@hidden.in", "/booked": 'Book online with <a href="https://fresha.com/x">Fresha</a> info@booked.in'}
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = PAGES.get(self.path, "").encode(); self.send_response(200 if self.path in PAGES else 404)
        self.send_header("Content-Type", "text/plain" if self.path == "/robots.txt" else "text/html"); self.end_headers(); self.wfile.write(body)
    def log_message(self, *a): pass
srv = http.server.HTTPServer(("127.0.0.1", 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_port}"
os.environ["NO_PROXY"] = "127.0.0.1"; os.environ.pop("HTTPS_PROXY", None); os.environ.pop("HTTP_PROXY", None); os.environ.pop("http_proxy", None); os.environ.pop("https_proxy", None)
rows = [{"name": "Glow", "website": base + "/", "score": "70"}, {"name": "Hidden", "website": base + "/private", "score": "70"},
        {"name": "Booked", "website": base + "/booked", "score": "70"}, {"name": "No site", "website": "", "score": "85"}]
out = {r["name"]: r for r in E.enrich(rows, delay=0)}
g = out["Glow"]
assert g["email"] == "hello@glowstudio.in" and g["whatsapp_link"] == "919876543210" and g["instagram"] == "glowstudio.hyd" and g["online_booking"] == "no", g
assert out["Hidden"]["enriched"] == "blocked by robots.txt" and not out["Hidden"].get("email")
assert out["Booked"]["online_booking"] == "yes" and int(out["Booked"]["score"]) < 70
assert int(g["score"]) == 90, g["score"]  # 70 +10 no booking +5 email +5 instagram, already has WhatsApp
print("  ✓ emails, WhatsApp, Instagram found; robots.txt respected; booking-tool owners scored down")
# ---- schema.org structured data (Deep Scan v2)
LD = """<html><head><script type="application/ld+json">{ broken json </script>
<script type="application/ld+json">{"@context":"https://schema.org","@graph":[
 {"@type":"WebSite","name":"Lotus"},
 {"@type":"BeautySalon","name":"Lotus Salon","email":"mailto:hello@lotus-salon.test","telephone":"+91 90000 11111",
  "sameAs":["https://www.instagram.com/lotus.salon.hyd","https://facebook.com/lotussalonhyd"],
  "potentialAction":{"@type":"ReserveAction","target":"https://lotus-salon.test/book"}}]}</script></head>
<body>Write to webmaster@agency-decoy.test for site issues.</body></html>"""
for eng in ["stdlib"] + (["extruct"] if importlib.util.find_spec("extruct") else []):
    sd = E.structured(LD, eng)
    assert sd["schema_type"] == "BeautySalon" and sd["email"] == "hello@lotus-salon.test", (eng, sd)
    assert sd["phone"] == "+91 90000 11111" and sd["instagram"] == "lotus.salon.hyd" and sd["facebook"] == "lotussalonhyd", (eng, sd)
    assert sd["online_booking"] == "yes" and sd["engine"] == eng
x = E.extract(LD, "stdlib")
assert x["email"] == "hello@lotus-salon.test" and x["online_booking"] == "yes" and x["schema_type"] == "BeautySalon", x
assert E.structured("<html><body>no schema</body></html>", "stdlib") == {}
print("  ✓ schema.org JSON-LD: @graph, mailto email beats a decoy, sameAs socials, ReserveAction = has booking")
if importlib.util.find_spec("extruct"):
    MD = """<div itemscope itemtype="https://schema.org/HealthClub"><span itemprop="name">Iron Gym</span>
    <a itemprop="email" href="mailto:join@irongym.test">mail</a><span itemprop="telephone">040-1234567</span></div>"""
    sd = E.structured(MD, "extruct")
    assert sd["schema_type"] == "HealthClub" and sd["email"] == "join@irongym.test" and sd["phone"] == "040-1234567", sd
    assert E.structured(MD, "stdlib") == {}   # microdata needs extruct
    print("  ✓ microdata read with extruct (stdlib reader skips it)")
else:
    print("  (extruct not installed: microdata test skipped; pip install extruct==0.18.0)")
print("enrich tests passed")
