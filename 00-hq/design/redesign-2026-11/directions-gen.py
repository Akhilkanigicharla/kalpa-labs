import math, random, json, datetime
random.seed(7)
C=dict(bg="#F2EEE3",panel="#FCFAF4",fg="#1E2A1F",muted="#5A6152",rule="#DCD5C3",soft="#E9E3D3",accent="#2F6A3A",madder="#8A4A28",gold="#C38E12",hero="#1D3A25",herofg="#F4EEDC",heromute="#BFCDAE",leaf="#5E9E4C",bark="#6B4226",l=["#66655A","#8A4A28","#2F6F78","#3B7A3A","#7A3F5E","#9C700E","#A8324F","#4A5590"],goldink="#241A04",bird="#2A3326")
HEAD='''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Anek+Latin:wght@400;600;700&amp;family=Anek+Telugu:wght@400;700&amp;family=Rozha+One&amp;display=swap" rel="stylesheet">
<style>
body{{margin:0}}
a{{color:{accent}}}a:hover{{color:{fg}}}
</style>
</helmet>
'''
TAIL='''</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":390,"height":{h}}}}}'>
class Component extends DCLogic {{
renderVals() {{ return {{}}; }}
}}
</script>
</body>
</html>
'''
BODY="font-family:'Anek Latin','Anek Telugu',system-ui,sans-serif"
DISP="font-family:'Rozha One',Georgia,serif;font-weight:400"
PRODUCTS=[("BotBhai","WhatsApp front desk for gyms, salons, agents",3),("Exam Kits","Plans and trackers for AP and Telangana exams",7),("Telugu Deals","Checked deals and money calculators",5),("Tab Lifeboat","Never lose your browser tabs",2),("AI Cost X-ray","Cut your AI bill, with the India paperwork",4),("Kalpa App","A mobile app, coming",6),("Trading Lab","Our own money, tested strategies",1)]

def leaf(x,y,ang,L,fill,ink,sw=1.2):
    # almond leaf with a centre vein, pointing at ang degrees
    w=L*0.38
    return (f'<g transform="translate({x:.1f} {y:.1f}) rotate({ang:.1f})">'
            f'<path d="M0 0 Q{L*0.5:.1f} {-w:.1f} {L:.1f} 0 Q{L*0.5:.1f} {w:.1f} 0 0Z" fill="{fill}" stroke="{ink}" stroke-width="{sw}"/>'
            f'<path d="M1 0 L{L*0.82:.1f} 0" stroke="{ink}" stroke-width="{sw*0.7:.2f}" fill="none"/></g>')

def bez(p0,p1,p2,p3,t):
    u=1-t
    return tuple(u**3*a+3*u*u*t*b+3*u*t*t*c+t**3*d for a,b,c,d in zip(p0,p1,p2,p3))

def kalamkari_tree():
    ink=C["madder"]; s=[]
    s.append(f'<svg viewBox="0 0 360 400" width="358" height="398" aria-hidden="true" style="display:block">')
    # pond and lotus line
    s.append(f'<path d="M20 372 Q180 352 340 372" fill="none" stroke="{C["l"][2]}" stroke-width="2"/>')
    for i in range(9):
        x=36+i*36; s.append(f'<path d="M{x} 380 q8 -10 16 0" fill="none" stroke="{C["l"][2]}" stroke-width="1.6"/>')
    branches=[((178,270),(150,250),(110,230),(70,190)),((182,270),(212,250),(252,230),(292,190)),
              ((177,215),(150,190),(125,160),(108,118)),((183,215),(210,190),(235,160),(252,118)),
              ((180,200),(176,150),(184,110),(180,62)),((179,240),(140,236),(96,252),(54,250)),((181,240),(220,236),(264,252),(306,250))]
    # leaves first (behind branches)
    for bi,b in enumerate(branches):
        for k in range(14):
            t=0.25+0.75*k/13
            x,y=bez(*b,t); dx,dy=(bez(*b,min(1,t+.02))[0]-x),(bez(*b,min(1,t+.02))[1]-y)
            base=math.degrees(math.atan2(dy,dx))
            for side in (-1,1):
                ang=base+side*(55+random.uniform(-12,12))
                L=random.uniform(17,25)*(0.8+0.3*t)
                fill=random.choice([C["leaf"],C["l"][3],"#7DB35E",C["accent"]])
                s.append(leaf(x,y,ang,L,fill,ink,1.1))
    # trunk
    s.append(f'<path d="M150 372 C166 340 170 306 172 268 C174 230 168 200 175 160 L185 160 C192 200 186 230 188 268 C190 306 194 340 210 372 Z" fill="{C["bark"]}" stroke="{ink}" stroke-width="2"/>')
    for i in range(6):  # bark pattern lines
        y=300+i*11; s.append(f'<path d="M{170-i*1.5} {y} q10 -5 20 0" fill="none" stroke="{C["gold"]}" stroke-width="1.2"/>')
    for b in branches:
        (x0,y0),(x1,y1),(x2,y2),(x3,y3)=b
        s.append(f'<path d="M{x0} {y0} C{x1} {y1} {x2} {y2} {x3} {y3}" fill="none" stroke="{C["bark"]}" stroke-width="7" stroke-linecap="round"/>')
        s.append(f'<path d="M{x0} {y0} C{x1} {y1} {x2} {y2} {x3} {y3}" fill="none" stroke="{ink}" stroke-width="1" stroke-linecap="round" stroke-dasharray="2 5"/>')
    # seven fruit medallions at branch ends
    for i,b in enumerate(branches):
        x,y=b[3]; col=C["l"][PRODUCTS[i][2]]
        s.append(f'<circle cx="{x}" cy="{y}" r="14" fill="{C["panel"]}" stroke="{C["gold"]}" stroke-width="2"/><circle cx="{x}" cy="{y}" r="9.5" fill="{col}" stroke="{ink}" stroke-width="1"/>')
        for a in range(8):
            r=a*math.pi/4; s.append(f'<circle cx="{x+12*math.cos(r):.1f}" cy="{y+12*math.sin(r):.1f}" r="1.2" fill="{C["gold"]}"/>')
    # two parrots
    for (px,py,f) in [(96,226,1),(266,226,-1)]:
        s.append(f'<g transform="translate({px} {py}) scale({f} 1)"><path d="M-8 6 L-20 22 L-4 10Z" fill="{C["accent"]}" stroke="{ink}" stroke-width="1"/>'
                 f'<ellipse cx="0" cy="0" rx="10" ry="7" fill="{C["leaf"]}" stroke="{ink}" stroke-width="1.2" transform="rotate(-25)"/>'
                 f'<circle cx="8" cy="-7" r="5.5" fill="{C["leaf"]}" stroke="{ink}" stroke-width="1.2"/><path d="M12.5 -8 q5 1 3 6 q-3 -1 -4 -3z" fill="{C["l"][6]}" stroke="{ink}" stroke-width="1"/><circle cx="9" cy="-8" r="1.3" fill="{C["fg"]}"/></g>')
    # two peacocks at the base
    for (px,f) in [(86,1),(274,-1)]:
        g=[f'<g transform="translate({px} 352) scale({f} 1)">']
        for a in range(7):
            ang=math.radians(-170+a*14); ex,ey=-6+38*math.cos(ang),-6+38*math.sin(ang)
            g.append(f'<path d="M-6 -6 L{ex:.1f} {ey:.1f}" stroke="{C["l"][3]}" stroke-width="2"/><ellipse cx="{ex:.1f}" cy="{ey:.1f}" rx="5" ry="4" fill="{C["l"][2]}" stroke="{ink}" stroke-width="1"/><circle cx="{ex:.1f}" cy="{ey:.1f}" r="1.8" fill="{C["gold"]}"/>')
        g.append(f'<path d="M-10 6 Q-4 -14 8 -10 Q16 -8 14 6 Z" fill="{C["l"][7]}" stroke="{ink}" stroke-width="1.2"/><path d="M10 -9 Q14 -24 20 -28" fill="none" stroke="{C["l"][7]}" stroke-width="5" stroke-linecap="round"/><circle cx="21" cy="-29" r="4" fill="{C["l"][7]}" stroke="{ink}" stroke-width="1"/><path d="M24 -30 l5 1 -5 2z" fill="{C["gold"]}"/><path d="M20 -33 l-2 -6 M22 -33 l1 -6 M18 -32 l-4 -5" stroke="{ink}" stroke-width="1"/></g>')
        s+=g
    s.append('</svg>')
    return "".join(s)

def motif_band(color, bg):
    s=[f'<svg viewBox="0 0 390 22" width="390" height="22" aria-hidden="true" style="display:block;background:{bg}">']
    for i in range(14):
        x=6+i*28; s.append(f'<path d="M{x} 18 Q{x+7} 2 {x+14} 18 Q{x+7} 12 {x} 18Z" fill="{color}"/><circle cx="{x+21}" cy="12" r="2" fill="{color}"/>')
    return "".join(s)+'</svg>'

def header(dark=False):
    fg=C["herofg"] if dark else C["fg"]; bd=C["heromute"] if dark else C["rule"]
    mark=f'<svg viewBox="0 0 32 32" width="30" height="30" aria-hidden="true"><path d="M15 30 L15 16 M17 30 L17 16" stroke="{C["bark"] if not dark else C["herofg"]}" stroke-width="2.4"/><circle cx="16" cy="11" r="9" fill="{C["leaf"]}"/><circle cx="12" cy="10" r="2" fill="{C["gold"]}"/><circle cx="19" cy="8" r="2" fill="{C["gold"]}"/><circle cx="17" cy="14" r="2" fill="{C["gold"]}"/></svg>'
    return (f'<header style="display:flex;align-items:center;justify-content:space-between;padding:14px 20px;{BODY}">'
            f'<a href="#" style="display:flex;align-items:center;gap:8px;text-decoration:none;color:{fg};{DISP};font-size:22px;min-height:44px">{mark}Kalpa Labs</a>'
            f'<div style="display:flex;border:1px solid {bd};border-radius:999px;padding:3px"><a href="#" style="min-height:38px;min-width:44px;display:flex;align-items:center;justify-content:center;border-radius:999px;background:{C["hero"] if not dark else C["herofg"]};color:{C["herofg"] if not dark else C["hero"]};text-decoration:none;font-weight:700;font-size:14px">EN</a><a href="#" style="min-height:38px;min-width:56px;display:flex;align-items:center;justify-content:center;color:{fg};text-decoration:none;font-family:\'Anek Telugu\',sans-serif;font-size:15px">తెలుగు</a></div></header>')

def btn(label,bg,fg,border=None):
    b=f"border:2px solid {border};" if border else "border:2px solid transparent;"
    return f'<a href="#" style="display:flex;align-items:center;justify-content:center;min-height:52px;padding:0 20px;border-radius:999px;background:{bg};color:{fg};{b}text-decoration:none;font-weight:700;font-size:17px">{label}</a>'

H1_EN='Replies in <span style="color:{a};text-decoration:underline;text-decoration-color:{g};text-underline-offset:6px;text-decoration-thickness:3px">Telugu, Hindi or English</span>, even at 11 PM.'
LEAD="BotBhai answers customers of gyms, salons and real estate agents on WhatsApp, books the slot and sends reminders. Free 14-day pilot, and no payment until you say yes."

# ---------- A: Kalamkari Tree of Life
def A():
    h=1560; o=[HEAD.format(title="Direction A, Kalamkari Tree of Life",**C)]
    o.append(f'<div style="width:390px;height:{h}px;box-sizing:border-box;background:{C["panel"]};color:{C["fg"]};{BODY};overflow:hidden">')
    o.append(header())
    o.append(motif_band(C["madder"],C["panel"]))
    o.append(f'<div style="margin:18px 16px 0;border:2px solid {C["madder"]};border-radius:180px 180px 16px 16px;padding:22px 0 8px;background:{C["bg"]};display:flex;justify-content:center">{kalamkari_tree()}</div>')
    o.append(f'<div style="padding:26px 22px 0;display:flex;flex-direction:column;gap:16px">')
    o.append(f'<p style="margin:0;font-weight:700;font-size:13px;letter-spacing:.04em;color:{C["madder"]}">A KALPAVRUKSHA FOR SMALL BUSINESSES IN HYDERABAD</p>')
    o.append(f'<h1 style="margin:0;{DISP};font-size:40px;line-height:1.08">{H1_EN.format(a=C["accent"],g=C["gold"])}</h1>')
    o.append(f'<p style="margin:0;font-size:18px;line-height:1.5;color:{C["muted"]}">{LEAD}</p>')
    o.append(f'<div style="display:flex;flex-direction:column;gap:10px">{btn("Get a free 14-day pilot",C["accent"],"#FFFFFF")}{btn("Chat with our AI","transparent",C["accent"],C["accent"])}</div></div>')
    o.append(f'<div style="margin-top:30px">{motif_band(C["gold"],C["panel"])}</div>')
    o.append(f'<section style="padding:26px 22px;display:flex;flex-direction:column;gap:12px"><h2 style="margin:0;{DISP};font-size:30px">Seven fruits, one tree</h2><p style="margin:0;color:{C["muted"]};font-size:16px">Each fruit is a Kalpa Labs product. Tap one to open it.</p>')
    for name,desc,ci in PRODUCTS[:4]:
        o.append(f'<a href="#" style="display:flex;gap:14px;align-items:center;padding:14px;border:1.5px solid {C["rule"]};border-radius:16px;background:{C["bg"]};text-decoration:none;color:{C["fg"]};min-height:44px"><span style="width:40px;height:40px;border-radius:50%;background:{C["l"][ci]};border:3px solid {C["gold"]};flex:none"></span><span style="display:flex;flex-direction:column;gap:2px"><b style="font-size:17px">{name}</b><span style="font-size:14px;color:{C["muted"]}">{desc}</span></span></a>')
    o.append('</section></div>')
    o.append(TAIL.format(h=h)); return "".join(o),h

# ---------- B: Painted dawn
def B():
    h=1560; o=[HEAD.format(title="Direction B, Painted dawn",**C)]
    o.append(f'<div style="width:390px;height:{h}px;box-sizing:border-box;background:{C["panel"]};color:{C["fg"]};{BODY};overflow:hidden">')
    o.append(f'<div style="background:{C["hero"]};color:{C["herofg"]}">{header(True)}')
    o.append(f'<div style="padding:18px 22px 0;display:flex;flex-direction:column;gap:16px"><h1 style="margin:0;{DISP};font-size:42px;line-height:1.06">Replies in <span style="color:{C["gold"]}">Telugu, Hindi or English</span>, even at 11 PM.</h1>'
             f'<p style="margin:0;font-size:18px;line-height:1.5;color:{C["heromute"]}">{LEAD}</p>'
             f'<div style="display:flex;flex-direction:column;gap:10px">{btn("Get a free 14-day pilot",C["gold"],C["goldink"])}{btn("Chat with our AI","transparent",C["herofg"],C["heromute"])}</div></div>')
    # painted landscape: flat layered shapes, sun, hills, tree silhouette, flock
    sv=[f'<svg viewBox="0 0 390 330" width="390" height="330" aria-hidden="true" style="display:block;margin-top:18px">']
    sv.append(f'<circle cx="250" cy="210" r="70" fill="{C["gold"]}" opacity=".9"/>')
    sv.append(f'<circle cx="250" cy="210" r="96" fill="none" stroke="{C["gold"]}" stroke-opacity=".25" stroke-width="10"/>')
    sv.append(f'<path d="M0 230 Q90 190 190 225 T390 210 V330 H0Z" fill="#2E5A35"/>')
    sv.append(f'<path d="M0 262 Q120 228 230 258 T390 250 V330 H0Z" fill="#3B7A3A"/>')
    sv.append(f'<path d="M0 296 Q150 270 260 292 T390 286 V330 H0Z" fill="{C["leaf"]}"/>')
    # tree silhouette on the middle hill
    tx,ty=118,250
    sv.append(f'<path d="M{tx-5} {ty} C{tx-3} {ty-30} {tx-6} {ty-50} {tx-2} {ty-72} L{tx+4} {ty-72} C{tx+7} {ty-50} {tx+4} {ty-30} {tx+7} {ty} Z" fill="#1A2E1E"/>')
    for (cx,cy,r) in [(tx,ty-96,34),(tx-34,ty-78,26),(tx+34,ty-80,27),(tx-18,ty-118,24),(tx+20,ty-120,25),(tx,ty-136,20),(tx-50,ty-62,16),(tx+52,ty-62,17)]:
        sv.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#1A2E1E"/>')
    for i,(fx,fy) in enumerate([(tx-30,ty-90),(tx+28,ty-96),(tx,ty-120),(tx-46,ty-62),(tx+46,ty-64),(tx-10,ty-70),(tx+14,ty-140)]):
        sv.append(f'<circle cx="{fx}" cy="{fy}" r="5" fill="{C["gold"]}"/>')
    # flock in a loose V
    for i in range(11):
        k=i-5; x=262+k*15+random.uniform(-3,3); y=64+abs(k)*9+random.uniform(-3,3); s=6+random.uniform(-1,1.5)
        sv.append(f'<path d="M{x-s:.1f} {y:.1f} Q{x-s/2:.1f} {y-s*0.7:.1f} {x:.1f} {y:.1f} Q{x+s/2:.1f} {y-s*0.7:.1f} {x+s:.1f} {y:.1f}" fill="none" stroke="{C["herofg"]}" stroke-width="1.8" stroke-linecap="round"/>')
    sv.append('</svg>'); o.append("".join(sv)+'</div>')
    o.append(f'<section style="padding:28px 22px 10px;display:flex;flex-direction:column;gap:12px"><h2 style="margin:0;{DISP};font-size:30px">One tree, seven fruits</h2><p style="margin:0;color:{C["muted"]};font-size:16px">Small tools for real work in Telugu states. Each one is built, tested on a phone, and priced before it opens.</p></section>')
    o.append(f'<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;padding:6px 22px 24px">')
    for name,desc,ci in PRODUCTS[:6]:
        o.append(f'<a href="#" style="display:flex;flex-direction:column;gap:8px;padding:16px;border-radius:18px;background:{C["bg"]};text-decoration:none;color:{C["fg"]};min-height:44px"><span style="width:30px;height:30px;border-radius:50%;background:{C["l"][ci]}"></span><b style="font-size:16px">{name}</b><span style="font-size:13px;color:{C["muted"]};line-height:1.35">{desc}</span></a>')
    o.append('</div></div>'); o.append(TAIL.format(h=h)); return "".join(o),h

# ---------- C: Living canopy (modern product page)
def C_():
    h=1560; o=[HEAD.format(title="Direction C, Living canopy",**C)]
    o.append(f'<div style="width:390px;height:{h}px;box-sizing:border-box;background:{C["bg"]};color:{C["fg"]};{BODY};overflow:hidden;position:relative">')
    # canopy across the top: big foreground leaves, mid clusters, a few birds
    sv=[f'<svg viewBox="0 0 390 230" width="390" height="230" aria-hidden="true" style="position:absolute;top:0;left:0">']
    for k in range(70):
        x=random.uniform(-20,410); y=random.uniform(-30,110)+ (abs(x-195)/195)*-30
        L=random.uniform(26,46); ang=random.uniform(40,140)
        fill=random.choice([C["leaf"],C["l"][3],C["accent"],"#7DB35E","#4E8A3E"])
        sv.append(leaf(x,y,ang,L,fill,"#24402A",0.9))
    for (fx,fy,ci) in [(70,70,3),(190,96,7),(312,72,5)]:
        sv.append(f'<circle cx="{fx}" cy="{fy}" r="9" fill="{C["l"][ci]}" stroke="{C["gold"]}" stroke-width="2"/>')
    sv.append(f'<g transform="translate(250 104)"><ellipse cx="0" cy="0" rx="9" ry="6" fill="{C["bird"]}" transform="rotate(-14)"/><circle cx="8" cy="-6" r="4.5" fill="{C["bird"]}"/><path d="M12 -7 l5 1 -5 2z" fill="{C["gold"]}"/><path d="M-8 1 l-9 4 8 -1z" fill="{C["bird"]}"/></g>')
    sv.append('</svg>'); o.append("".join(sv))
    o.append(f'<div style="position:relative;padding-top:0">{header()}</div>')
    o.append(f'<div style="position:relative;padding:150px 22px 0;display:flex;flex-direction:column;gap:16px">')
    o.append(f'<span style="align-self:flex-start;padding:6px 12px;border-radius:999px;background:{C["panel"]};border:1px solid {C["rule"]};font-size:14px;font-weight:600;color:{C["accent"]}">For gyms, salons and real estate agents</span>')
    o.append(f'<h1 style="margin:0;{DISP};font-size:44px;line-height:1.04">Your front desk on WhatsApp, in your customer&#39;s language.</h1>')
    o.append(f'<p style="margin:0;font-size:18px;line-height:1.5;color:{C["muted"]}">It answers at 11 PM, books the slot and sends reminders, in English, Telugu, Hindi, Tenglish or Hinglish. Set up and run by us.</p>')
    o.append(f'<div style="display:flex;gap:10px;flex-wrap:wrap">{btn("Free 14-day pilot",C["accent"],"#FFFFFF")}{btn("See it reply","transparent",C["accent"],C["accent"])}</div></div>')
    # product moment: a real chat
    o.append(f'<div style="position:relative;margin:28px 22px 0;padding:16px;border-radius:24px;background:#E7DDD3;display:flex;flex-direction:column;gap:10px">'
             f'<div style="display:flex;align-items:center;gap:10px;padding-bottom:8px;border-bottom:1px solid #D6CABD"><span style="width:34px;height:34px;border-radius:50%;background:{C["accent"]}"></span><span style="display:flex;flex-direction:column"><b style="font-size:15px">Sri Lakshmi Salon</b><span style="font-size:12px;color:{C["muted"]}">replies in seconds</span></span></div>'
             f'<p style="margin:0;align-self:flex-end;max-width:78%;padding:10px 12px;border-radius:14px 14px 4px 14px;background:#D9FDD3;color:#111B21;font-family:\'Anek Telugu\',sans-serif;font-size:16px">రేపు సాయంత్రం హెయిర్ కట్ కి స్లాట్ ఉందా?</p>'
             f'<p style="margin:0;align-self:flex-start;max-width:82%;padding:10px 12px;border-radius:14px 14px 14px 4px;background:#FFFFFF;color:#111B21;font-family:\'Anek Telugu\',sans-serif;font-size:16px">ఉంది! రేపు 6:30 PM ఖాళీగా ఉంది. బుక్ చేయమంటారా?</p>'
             f'<p style="margin:0;align-self:flex-end;max-width:60%;padding:10px 12px;border-radius:14px 14px 4px 14px;background:#D9FDD3;color:#111B21;font-size:16px">Haan book karo 👍</p></div>'.replace(" 👍",""))
    o.append(f'<div style="position:relative;margin:24px 22px 0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px">')
    for big,small in [("5","languages"),("₹0","to try"),("14","day pilot")]:
        o.append(f'<div style="padding:14px 10px;border-radius:16px;background:{C["panel"]};border:1px solid {C["rule"]};display:flex;flex-direction:column;gap:2px;align-items:center"><b style="{DISP};font-size:30px;color:{C["accent"]}">{big}</b><span style="font-size:13px;color:{C["muted"]}">{small}</span></div>')
    o.append('</div>')
    o.append(f'<section style="position:relative;padding:28px 22px;display:flex;flex-direction:column;gap:10px"><h2 style="margin:0;{DISP};font-size:28px">Also growing on the tree</h2>')
    for name,desc,ci in PRODUCTS[1:5]:
        o.append(f'<a href="#" style="display:flex;justify-content:space-between;align-items:center;gap:12px;padding:14px 16px;border-radius:14px;background:{C["panel"]};text-decoration:none;color:{C["fg"]};min-height:44px"><span style="display:flex;gap:12px;align-items:center"><span style="width:12px;height:12px;border-radius:50%;background:{C["l"][ci]};flex:none"></span><span style="display:flex;flex-direction:column"><b style="font-size:16px">{name}</b><span style="font-size:13px;color:{C["muted"]}">{desc}</span></span></span><svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M9 6l6 6-6 6" fill="none" stroke="{C["accent"]}" stroke-width="2"/></svg></a>')
    o.append('</section></div>'); o.append(TAIL.format(h=h)); return "".join(o),h

files=[("Main.dc.html","A · Kalamkari Tree of Life",A),("Painted-Dawn.dc.html","B · Painted dawn",B),("Living-Canopy.dc.html","C · Living canopy",C_)]
boards={}; order=[]; x=0
for fn,title,f in files:
    html,h=f(); open(f"project/{fn}","w").write(html)
    boards[fn]={"x":x,"y":0,"w":390,"h":h,"title":title}; order.append(fn); x+=390+80
idx={"v":3,"createdOnFiles":{"v":1,"at":datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")},"title":"Kalpa Labs site redesign: 3 directions",
     "launch":{"view":"canvas"},"pages":[],"boards":boards,"order":order,
     "notes":{"t":{"x":0,"y":-300,"text":"Kalpa Labs home page: three directions (phone, first screen + one section)","kind":"title1","maxW":1330}},"designSystems":[]}
open("project/canvas.json","w").write(json.dumps(idx,ensure_ascii=False))
print("written", order)
