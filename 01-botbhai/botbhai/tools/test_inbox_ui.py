#!/usr/bin/env python3
"""Shared inbox (A04) click-through on the built demo (web/dist/inbox.html?demo=1) at 390 px: take over, reply as staff,
resume the bot, go back to the list, and check replying is off for a website visitor. Run after build.py; needs Playwright."""
import pathlib, sys
from playwright.sync_api import sync_playwright
url = (pathlib.Path(__file__).resolve().parent.parent / "web" / "dist" / "inbox.html").as_uri() + "?demo=1"
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 390, "height": 844}); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(url); pg.click(".chip[data-f=bot]"); pg.click(".convo:has-text(\"Priya\")")
    pg.click("button:text-is(\"Take over\")"); pg.wait_for_selector(".banner.human")
    pg.fill("#reply", "Hi Priya, Lakshmi here. See you at 4!"); pg.click(".send")
    pg.wait_for_selector(".b.staff >> text=Lakshmi here")
    pg.click("button:text-is(\"Resume bot\")"); pg.wait_for_selector(".thead .pill.bot")
    pg.click(".back"); assert pg.is_visible("#convos")
    pg.click(".chip[data-f=all]"); pg.click(".convo:has-text(\"Website visitor\")")
    assert pg.is_disabled("#reply") and pg.is_visible(".banner.warn")
    assert not errs, errs; print("demo flow ok: take over → staff reply → resume → back; web visitor reply disabled")
    b.close()
