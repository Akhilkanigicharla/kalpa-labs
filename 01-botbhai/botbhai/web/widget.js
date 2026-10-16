/* BotBhai website widget (Kalamkari: hero indigo #1C2463 + turmeric ring #D3940A): <script src="https://SITE/widget.js" data-client="CLIENT-UUID" data-niche="clinic" defer></script> */
(function () {
  var s = document.currentScript, client = s.getAttribute("data-client"), niche = s.getAttribute("data-niche") || "";
  var base = s.src.replace(/widget\.js.*$/, "");
  var btn = document.createElement("button");
  btn.setAttribute("aria-label", "Chat with us"); btn.innerHTML = "💬";
  btn.style.cssText = "position:fixed;right:18px;bottom:18px;width:60px;height:60px;border-radius:50%;border:0;background:#1C2463;color:#F6F2E8;font-size:28px;box-shadow:0 0 0 3px #D3940A,0 6px 20px rgba(28,36,99,.35);cursor:pointer;z-index:2147483646";
  var frame = document.createElement("iframe");
  frame.title = "Chat"; frame.allow = "microphone";
  frame.src = base + "index.html?embed=1&client=" + encodeURIComponent(client) + "&niche=" + encodeURIComponent(niche);
  frame.style.cssText = "position:fixed;right:18px;bottom:88px;width:min(380px,calc(100vw - 36px));height:min(600px,calc(100vh - 120px));border:0;border-radius:16px;box-shadow:0 12px 40px rgba(0,0,0,.3);z-index:2147483647;display:none;background:#fff";
  btn.onclick = function () { frame.style.display = frame.style.display === "none" ? "block" : "none"; };
  document.body.appendChild(frame); document.body.appendChild(btn);
})();
