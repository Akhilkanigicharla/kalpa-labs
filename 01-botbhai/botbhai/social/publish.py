"""Publisher: posts approved items to Instagram (and optionally a Facebook Page) through Meta's official Graph API.

Why the official API: browser-automation posting tools risk the account being restricted; the Content Publishing
API is free and allowed for Business/Creator accounts linked to a Facebook Page.
Flow (developers.facebook.com/docs/instagram-platform/content-publishing):
  1. POST /{ig-user-id}/media            -> container id (image_url | video_url + media_type=REELS | STORIES | CAROUSEL)
  2. GET  /{container-id}?fields=status_code  until FINISHED (videos take a while; ERROR/EXPIRED = give up)
  3. POST /{ig-user-id}/media_publish creation_id=<container id>
Limits: JPEG images only; carousels 2-10 items; a rolling 24-hour publishing cap read from
GET /{ig-user-id}/content_publishing_limit. Media must sit at a public HTTPS URL (base_url).

Safety: dry run is the default. A real post needs dry_run=False AND a token in the environment (IG_ACCESS_TOKEN,
set by the client in GitHub/Netlify secrets; this code never asks for or stores it) AND status == "approved".
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request

GRAPH = os.environ.get("META_GRAPH_URL", "https://graph.facebook.com/v23.0")


class GraphError(RuntimeError):
    pass


def http_transport(method: str, path: str, params: dict) -> dict:
    """Real HTTPS call. Token comes from the environment only."""
    params = {**params, "access_token": os.environ["IG_ACCESS_TOKEN"]}
    data = urllib.parse.urlencode(params).encode()
    url = f"{GRAPH}/{path}"
    req = urllib.request.Request(url + ("?" + data.decode() if method == "GET" else ""), data=None if method == "GET" else data,
                                 method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise GraphError(e.read().decode(errors="replace")[:400]) from None


class DryRun:
    """Records the calls a real run would make and returns fake ids. Used by default and in tests."""

    def __init__(self, status_sequence=("FINISHED",), quota=0, cap=100):
        self.calls, self.n, self.status, self.quota, self.cap = [], 0, list(status_sequence), quota, cap

    def __call__(self, method, path, params):
        self.calls.append((method, path, dict(params)))
        if path.endswith("content_publishing_limit"):
            return {"data": [{"quota_usage": self.quota, "config": {"quota_total": self.cap, "quota_duration": 86400}}]}
        if method == "GET":
            return {"status_code": self.status.pop(0) if len(self.status) > 1 else self.status[0]}
        self.n += 1
        return {"id": f"{'pub' if path.endswith('media_publish') else 'c'}{self.n}"}


class Publisher:
    def __init__(self, ig_user_id: str, base_url: str, *, page_id: str | None = None, transport=None, dry_run: bool = True,
                 poll_seconds: float = 5, max_polls: int = 60):
        if not dry_run and not os.environ.get("IG_ACCESS_TOKEN"):
            raise GraphError("IG_ACCESS_TOKEN is not set (the client adds it as a secret); refusing a live run")
        self.ig, self.page, self.base = ig_user_id, page_id, base_url.rstrip("/") + "/"
        self.t = transport or (DryRun() if dry_run else http_transport)
        self.dry, self.poll, self.max_polls = dry_run, poll_seconds, max_polls

    def url(self, filename: str) -> str:
        return self.base + urllib.parse.quote(filename)

    def quota_left(self) -> int:
        d = self.t("GET", f"{self.ig}/content_publishing_limit", {"fields": "config,quota_usage"})["data"][0]
        return int(d["config"]["quota_total"]) - int(d["quota_usage"])

    def _wait(self, cid: str) -> None:
        for _ in range(self.max_polls):
            st = self.t("GET", cid, {"fields": "status_code"}).get("status_code")
            if st in ("FINISHED", "PUBLISHED"):
                return
            if st in ("ERROR", "EXPIRED"):
                raise GraphError(f"container {cid} {st}")
            if not self.dry:
                time.sleep(self.poll)
        raise GraphError(f"container {cid} not ready after {self.max_polls} checks")

    def _container(self, **params) -> str:
        cid = self.t("POST", f"{self.ig}/media", params)["id"]
        self._wait(cid)
        return cid

    def publish(self, item: dict) -> dict:
        """item: a manifest entry {id, kind, caption, alt, files: [names], status}. Returns {id, media_id, fb_post_id}."""
        if item.get("status") != "approved":
            raise GraphError(f"{item['id']} is {item.get('status', 'not approved')}; only approved items are posted")
        if item.get("check") and not item["check"]["ok"]:
            raise GraphError(f"{item['id']} failed compliance: {item['check']['blocked']}")
        if self.quota_left() < 1:
            raise GraphError("24-hour publishing limit reached; try the next run")
        jpgs = [f for f in item["files"] if f.lower().endswith((".jpg", ".jpeg"))]
        mp4 = next((f for f in item["files"] if f.lower().endswith(".mp4")), None)
        kind, cap = item["kind"], item.get("caption", "")
        if kind == "carousel":
            if not 2 <= len(jpgs) <= 10:
                raise GraphError("a carousel needs 2-10 images")
            kids = [self._container(image_url=self.url(f), is_carousel_item="true") for f in jpgs]
            cid = self._container(media_type="CAROUSEL", children=",".join(kids), caption=cap)
        elif kind == "reel" and mp4:
            cid = self._container(media_type="REELS", video_url=self.url(mp4), caption=cap, share_to_feed="true",
                                  cover_url=self.url(jpgs[0]) if jpgs else "")
        elif kind == "story":
            cid = self._container(media_type="STORIES", image_url=self.url(jpgs[0]))
        else:  # single image (also a reel with no video: falls back to its first frame)
            cid = self._container(image_url=self.url(jpgs[0]), caption=cap, alt_text=item.get("alt", "")[:1000])
        media = self.t("POST", f"{self.ig}/media_publish", {"creation_id": cid})["id"]
        fb = None
        if self.page and kind in ("post", "carousel") and jpgs:  # Page photo post (pages_manage_posts)
            fb = self.t("POST", f"{self.page}/photos", {"url": self.url(jpgs[0]), "message": cap}).get("id")
        return {"id": item["id"], "media_id": media, "fb_post_id": fb, "dry_run": self.dry}


def due(items: list[dict], now_iso: str) -> list[dict]:
    """Approved, not yet posted items whose 'date time' (IST) is at or before now_iso ('YYYY-MM-DD HH:MM')."""
    return [it for it in items if it.get("status") == "approved" and not it.get("media_id") and f"{it['date']} {it['time']}" <= now_iso]
