
import pandas as pd
import numpy as np
from pathlib import Path
import plotly.graph_objects as go
import plotly.io as pio


RACINE = Path(__file__).resolve().parent.parent
DONNEES = RACINE / "donnees"; OUT = RACINE / "outputs"

# Palette "energie" cohérente
TEAL="#0E9384"; AMBER="#E8A33D"; BLEU="#2563A6"; SLATE="#64748B"; ROSE="#B4456B"; VERT="#4D8B3F"; INK="#14202E"
COLORWAY=[TEAL,AMBER,BLEU,ROSE,VERT,SLATE]
FONT="IBM Plex Sans, sans-serif"

def style(fig, h=360, titre=None):
    fig.update_layout(
        template="plotly_white", height=h, colorway=COLORWAY,
        font=dict(family=FONT, size=12, color=INK),
        margin=dict(l=50, r=20, t=40 if titre else 16, b=40),
        title=dict(text=titre, font=dict(size=14, color=INK)) if titre else None,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.2, font=dict(size=11)),
        xaxis=dict(gridcolor="#E7E2D8"), yaxis=dict(gridcolor="#E7E2D8"),
    )
    return fig

def div(fig):
    return pio.to_html(fig, include_plotlyjs=False, full_html=False,
                       config={"displayModeBar": False, "responsive": True})

# ---------- Donnees ----------
df = pd.read_parquet(OUT / "table_analytique.parquet").rename(columns={"type_client_y":"type_client"})
v = df[df["conso"].notna()].copy()
hor = pd.read_csv(DONNEES / "releves_horaires_echantillon.csv", parse_dates=["horodatage"])
inc = pd.read_csv(DONNEES / "incidents_reseau.csv")
rec = pd.read_csv(DONNEES / "reclamations.csv", parse_dates=["date"])
fr = pd.read_csv(DONNEES / "cas_fraude_confirmes.csv")

MOIS_FR = ["Jan","Fév","Mar","Avr","Mai","Juin","Juil","Aoû","Sep","Oct","Nov","Déc"]

# =====================================================================
# VUE 1 - EXPLOITATION RESEAU
# =====================================================================
# Courbe de charge horaire (moyenne par heure de la journee, par type de client)
hor = hor.merge(df[["id_pdl","type_client"]].drop_duplicates(), on="id_pdl", how="left")
hor["heure"] = hor["horodatage"].dt.hour
courbe = hor.groupby(["heure","type_client"])["consommation_kwh"].mean().reset_index()
f_charge = go.Figure()
for tc in ["residentiel","professionnel","industriel"]:
    s = courbe[courbe["type_client"]==tc]
    if len(s):
        f_charge.add_trace(go.Scatter(x=s["heure"], y=s["consommation_kwh"], mode="lines",
                                      name=tc, line=dict(width=3)))
f_charge.update_layout(xaxis_title="Heure de la journée", yaxis_title="kWh moyens / heure")
style(f_charge)

# Saisonnalite : conso totale du reseau par mois (les 2 annees moyennees)
sais = v.groupby("mois")["conso"].mean().reindex(range(1,13))
f_sais = go.Figure(go.Bar(x=MOIS_FR, y=sais.values, marker_color=TEAL))
f_sais.update_layout(xaxis_title="Mois", yaxis_title="Conso moyenne / PDL (kWh/j)")
style(f_sais)

# Effet meteo : conso quotidienne reseau vs DJU, couleur = saison
journalier = v.groupby("date").agg(conso=("conso","sum"), dju=("dju_chauffage","mean")).reset_index()
journalier["saison"] = df.groupby("date")["saison"].first().reindex(journalier["date"]).values
f_meteo = go.Figure()
for sa,c in zip(["Hiver","Printemps","Ete","Automne"],[BLEU,VERT,AMBER,ROSE]):
    s = journalier[journalier["saison"]==sa]
    f_meteo.add_trace(go.Scatter(x=s["dju"], y=s["conso"]/1000, mode="markers", name=sa,
                                 marker=dict(size=5, color=c, opacity=0.6)))
f_meteo.update_layout(xaxis_title="Degré-jour de chauffage (DJU)", yaxis_title="Conso totale réseau (MWh/j)")
style(f_meteo)


# Incidents par type
inc_t = inc["type"].value_counts()
f_inc = go.Figure(go.Bar(x=inc_t.values, y=inc_t.index, orientation="h", marker_color=AMBER))
f_inc.update_layout(xaxis_title="Nombre d'incidents (2 ans)", yaxis=dict(autorange="reversed"))
style(f_inc, h=300)

# KPIs vue 1
pic_heure = int(courbe.groupby("heure")["consommation_kwh"].sum().idxmax())
kpi1 = [
    ("Heure de pointe", f"{pic_heure}h", "moment de demande max"),
    ("Conso hiver vs été", f"+{100*(sais[[12,1,2]].mean()/sais[[6,7,8]].mean()-1):.0f}%", "sensibilité saisonnière"),
    ("Corrélation conso/froid", "+0,69", "clients tout-électriques"),
    ("Incidents / an", f"{len(inc)//2}", "à mieux anticiper"),
]

# =====================================================================
# VUE 2 - DIRECTION FINANCIERE
# =====================================================================
# Volume annuel par type de client (somme/2 ans)
vol_tc = (v.groupby("type_client")["conso"].sum()/2/1e6).sort_values()  # GWh/an
f_vol = go.Figure(go.Bar(x=vol_tc.values, y=vol_tc.index, orientation="h", marker_color=BLEU))
f_vol.update_layout(xaxis_title="Énergie distribuée (GWh/an)")
style(f_vol, h=300)

# Top zones par volume
vol_z = (v.groupby("zone")["conso"].sum()/2/1e6).sort_values()
f_volz = go.Figure(go.Bar(x=vol_z.values, y=vol_z.index, orientation="h", marker_color=TEAL))
f_volz.update_layout(xaxis_title="Énergie distribuée (GWh/an)")
style(f_volz, h=320)

# Gisement fraude : nb par type
fr_t = fr["type_fraude"].value_counts()
f_fraude = go.Figure(go.Bar(x=fr_t.index, y=fr_t.values, marker_color=ROSE))
f_fraude.update_layout(xaxis_title="Type de fraude", yaxis_title="Cas confirmés")
style(f_fraude, h=300)

# Volume mensuel (implication achats d'energie)
vol_m = v.groupby("mois")["conso"].sum().reindex(range(1,13))/1e3  # MWh
f_volm = go.Figure(go.Scatter(x=MOIS_FR, y=vol_m.values, mode="lines+markers",
                              line=dict(color=AMBER, width=3), fill="tozeroy",
                              fillcolor="rgba(232,163,61,0.15)"))
f_volm.update_layout(xaxis_title="Mois", yaxis_title="Volume distribué (MWh)")
style(f_volm, h=300)

conso_an_tot = v["conso"].sum()/2/1e6  # GWh/an echantillon
kpi2 = [
    ("Énergie distribuée", f"{conso_an_tot:.1f} GWh/an", "sur l'échantillon (700 PDL)"),
    ("Part industrielle", f"{100*vol_tc.get('industriel',0)/vol_tc.sum():.0f}%", "du volume total"),
    ("Fraudes confirmées", f"{len(fr)}", "soit 3,4 % des compteurs"),
    ("Gain visé an 1", "~1,3 M€", "cf. business case"),
]

# =====================================================================
# VUE 3 - RELATION CLIENT
# =====================================================================
rec["mois_a"] = rec["date"].dt.to_period("M").dt.to_timestamp()
# Satisfaction moyenne par mois
sat_m = rec.groupby("mois_a")["satisfaction"].mean()
f_sat = go.Figure(go.Scatter(x=sat_m.index, y=sat_m.values, mode="lines+markers",
                             line=dict(color=TEAL, width=3)))
f_sat.update_layout(xaxis_title="Mois", yaxis_title="Satisfaction moyenne (1-5)", yaxis=dict(range=[1,5]))
style(f_sat)

# Volume reclamations par canal
canal = rec["canal"].value_counts()
f_canal = go.Figure(go.Bar(x=canal.index, y=canal.values, marker_color=BLEU))
f_canal.update_layout(xaxis_title="Canal de contact", yaxis_title="Nombre de réclamations")
style(f_canal, h=300)

# Distribution des notes de satisfaction
dist = rec["satisfaction"].value_counts().sort_index()
couleurs_sat = [ROSE,"#D98A5E",AMBER,"#7BA86F",VERT]
f_dist = go.Figure(go.Bar(x=[str(i) for i in dist.index], y=dist.values,
                          marker_color=[couleurs_sat[i-1] for i in dist.index]))
f_dist.update_layout(xaxis_title="Note de satisfaction", yaxis_title="Nombre de messages")
style(f_dist, h=300)

# Volume reclamations par mois
vol_rec = rec.groupby("mois_a").size()
f_volrec = go.Figure(go.Scatter(x=vol_rec.index, y=vol_rec.values, mode="lines",
                                line=dict(color=AMBER, width=2), fill="tozeroy",
                                fillcolor="rgba(232,163,61,0.15)"))
f_volrec.update_layout(xaxis_title="Mois", yaxis_title="Réclamations")
style(f_volrec, h=300)

pct_insat = 100*(rec["satisfaction"]<=2).mean()
kpi3 = [
    ("Réclamations", f"{len(rec):,}".replace(",", " "), "sur la période"),
    ("Satisfaction moyenne", f"{rec['satisfaction'].mean():.1f}/5", "tous canaux"),
    ("Clients insatisfaits", f"{pct_insat:.0f}%", "notes 1-2"),
    ("Canal principal", canal.index[0], f"{canal.iloc[0]} messages"),
]

# =====================================================================
# ASSEMBLAGE HTML
# =====================================================================
def cartes_kpi(kpis):
    out = '<div class="kpis">'
    for titre, val, sous in kpis:
        out += f'<div class="kpi"><div class="kpi-val">{val}</div><div class="kpi-titre">{titre}</div><div class="kpi-sous">{sous}</div></div>'
    return out + "</div>"

def grille(figs):
    out = '<div class="grille">'
    for titre, d in figs:
        out += f'<div class="carte"><h3>{titre}</h3>{d}</div>'
    return out + "</div>"

vue1 = cartes_kpi(kpi1) + grille([
    ("Courbe de charge journalière (heures de pointe)", div(f_charge)),
    ("Effet du froid sur la demande (conso vs degrés-jour)", div(f_meteo)),
    ("Saisonnalité de la consommation", div(f_sais)),
    ("Incidents réseau par type", div(f_inc)),
])
vue2 = cartes_kpi(kpi2) + grille([
    ("Où est le volume : énergie par type de client", div(f_vol)),
    ("Énergie distribuée par zone", div(f_volz)),
    ("Gisement fraude : cas confirmés par type", div(f_fraude)),
    ("Volume mensuel (implication achats d'énergie)", div(f_volm)),
])
vue3 = cartes_kpi(kpi3) + grille([
    ("Évolution de la satisfaction client", div(f_sat)),
    ("Réclamations par canal", div(f_canal)),
    ("Distribution des notes de satisfaction", div(f_dist)),
    ("Volume de réclamations dans le temps", div(f_volrec)),
])

HTML = f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Néovolt Grid+ — Tableau de bord décisionnel</title>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,800&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root{{ --ink:#14202E; --teal:#0E9384; --amber:#E8A33D; --paper:#F6F4EF; --card:#FFFFFF; --line:#E7E2D8; --muted:#64748B; }}
  *{{box-sizing:border-box;}}
  body{{margin:0;background:var(--paper);color:var(--ink);font-family:'IBM Plex Sans',sans-serif;}}
  header{{padding:28px 36px 18px;border-bottom:1px solid var(--line);background:linear-gradient(180deg,#FBFAF7,transparent);}}
  .eyebrow{{font-size:12px;letter-spacing:.18em;text-transform:uppercase;color:var(--teal);font-weight:600;}}
  h1{{font-family:'Bricolage Grotesque',sans-serif;font-weight:800;font-size:30px;margin:6px 0 2px;letter-spacing:-.01em;}}
  .soustitre{{color:var(--muted);font-size:14px;}}
  nav{{display:flex;gap:6px;padding:16px 36px 0;border-bottom:1px solid var(--line);}}
  .tab{{padding:11px 20px;border:none;background:transparent;font-family:inherit;font-size:14px;font-weight:600;color:var(--muted);cursor:pointer;border-radius:10px 10px 0 0;border-bottom:3px solid transparent;}}
  .tab:hover{{color:var(--ink);}}
  .tab.actif{{color:var(--ink);border-bottom-color:var(--teal);background:#fff;}}
  main{{padding:24px 36px 60px;}}
  .vue{{display:none;}} .vue.actif{{display:block;animation:fade .35s ease;}}
  @keyframes fade{{from{{opacity:0;transform:translateY(6px);}}to{{opacity:1;transform:none;}}}}
  .kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin-bottom:22px;}}
  .kpi{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px;border-left:4px solid var(--teal);}}
  .kpi-val{{font-family:'Bricolage Grotesque',sans-serif;font-weight:800;font-size:26px;line-height:1;}}
  .kpi-titre{{font-weight:600;font-size:13px;margin-top:8px;}}
  .kpi-sous{{color:var(--muted);font-size:12px;margin-top:2px;}}
  .grille{{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:18px;}}
  .carte{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px 8px;box-shadow:0 1px 2px rgba(20,32,46,.04);}}
  .carte h3{{font-size:14px;font-weight:600;margin:0 0 8px;color:var(--ink);}}
  footer{{padding:20px 36px;color:var(--muted);font-size:12px;border-top:1px solid var(--line);}}
</style></head>
<body>
<header>
  <div class="eyebrow">Néovolt Grid+ · Volet Data Analyst</div>
  <h1>Tableau de bord décisionnel</h1>
  <div class="soustitre">Trois lectures des mêmes données, une par décideur. Graphiques interactifs (survol, zoom).</div>
</header>
<nav>
  <button class="tab actif" data-vue="v1">⚡ Exploitation réseau</button>
  <button class="tab" data-vue="v2">€ Direction financière</button>
  <button class="tab" data-vue="v3">☎ Relation client</button>
</nav>
<main>
  <section class="vue actif" id="v1">{vue1}</section>
  <section class="vue" id="v2">{vue2}</section>
  <section class="vue" id="v3">{vue3}</section>
</main>
<footer>Source : données du dossier de cas Néovolt (2024-2025). Prototype d'examen — chiffres de cadrage à valider.</footer>
<script>
  document.querySelectorAll('.tab').forEach(t=>t.addEventListener('click',()=>{{
    document.querySelectorAll('.tab').forEach(x=>x.classList.remove('actif'));
    document.querySelectorAll('.vue').forEach(x=>x.classList.remove('actif'));
    t.classList.add('actif');
    document.getElementById(t.dataset.vue).classList.add('actif');
    window.dispatchEvent(new Event('resize'));
  }}));
</script>
</body></html>"""

chemin = OUT / "dashboard_neovolt.html"
chemin.write_text(HTML, encoding="utf-8")
print("Dashboard ecrit :", chemin, f"({len(HTML)//1024} Ko)")