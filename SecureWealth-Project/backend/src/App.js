import { useState, useEffect, useRef, useCallback } from "react";

/* ─────────────────────────────────────────
   API CLIENT
───────────────────────────────────────── */
const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

const api = {
  async post(path, body) {
    const token = localStorage.getItem("access_token");
    const res   = await fetch(`${API_BASE}${path}`, {
      method:  "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Request failed");
    return data;
  },
  async get(path) {
    const token = localStorage.getItem("access_token");
    const res   = await fetch(`${API_BASE}${path}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Request failed");
    return data;
  },
};

/* ─────────────────────────────────────────
   STATIC DATA
───────────────────────────────────────── */
const insights = [
  { id: 1, icon: "◈", title: "Portfolio Drift Detected",      summary: "Equity allocation increased beyond target.",        detail: "Your equity allocation has risen to 72%. Consider rebalancing to maintain diversification and reduce concentration risk.", color: "#f59e0b" },
  { id: 2, icon: "◆", title: "Tax Harvesting Opportunity",    summary: "Unrealized losses detected in 3 assets.",           detail: "Selling specific assets could reduce your taxable gains by est. ₹1.2L and improve overall tax efficiency.", color: "#00c9a7" },
  { id: 3, icon: "◉", title: "Emergency Fund Alert",          summary: "Liquidity level below recommended threshold.",      detail: "Your emergency savings cover only 2.5 months. Recommended minimum is 6 months for financial safety.", color: "#f87171" },
];

const fraudAlerts = [
  { msg: "Login blocked from Georgia, USA",         time: "2 min ago",  level: "high"   },
  { msg: "Unusual transaction attempt — ₹84,000",  time: "15 min ago", level: "high"   },
  { msg: "Behavioral anomaly in payment pattern",   time: "1 hr ago",   level: "medium" },
];

const timeline = [
  { event: "Login blocked from Georgia",             time: "2m" },
  { event: "Portfolio drift detected — Equity 72%",  time: "1h" },
  { event: "Tax harvesting opportunity flagged",     time: "3h" },
  { event: "Unusual transfer attempt flagged",       time: "6h" },
];

const investments = [
  { label: "Equity",        pct: 72, target: 60, color: "#f59e0b" },
  { label: "Fixed Income",  pct: 18, target: 30, color: "#4f8ef7" },
  { label: "International", pct:  6, target: 10, color: "#00c9a7" },
  { label: "Liquid / Cash", pct:  4, target:  5, color: "#a78bfa" },
];

const visionCards = [
  { icon: "⬡", title: "AI Wealth Twin",         desc: "A living digital replica of your financial life — learning, adapting, and acting on your behalf 24/7." },
  { icon: "◈", title: "Predictive Intelligence", desc: "Spot portfolio drift, tax opportunities, and market signals before they affect your returns." },
  { icon: "◉", title: "Fraud Shield",            desc: "Behavioural biometrics and anomaly detection block threats the moment they emerge." },
  { icon: "◆", title: "Unified Strategy",        desc: "Every rupee tracked, every goal mapped — one intelligent dashboard for your entire financial world." },
];

/* ─────────────────────────────────────────
   FORMAT HELPERS
───────────────────────────────────────── */
const fmt = (n) => new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(n);

/* ─────────────────────────────────────────
   MAIN APP
───────────────────────────────────────── */
export default function App() {
  const [page, setPage]           = useState("landing");
  const [loginData, setLoginData] = useState({ email: "", password: "" });
  const [loginError, setLoginError] = useState("");
  const [isLoggingIn, setIsLoggingIn]   = useState(false);
  const [quoteVisible, setQuoteVisible] = useState(false);
  const [visionVisible, setVisionVisible] = useState(false);
  const [authMode, setAuthMode]   = useState("login"); // "login" | "register"

  const [dashSection, setDashSection]   = useState(0);
  const [selectedInsight, setSelectedInsight] = useState(null);
  const [dashVisible, setDashVisible]   = useState([false, false, false]);
  const [botOpen, setBotOpen]           = useState(false);
  const [botInput, setBotInput]         = useState("");

  // Live backend data
  const [netWorth, setNetWorth]         = useState(null);
  const [aaAccounts, setAaAccounts]     = useState([]);
  const [physicalAssets, setPhysicalAssets] = useState([]);
  const [user, setUser]                 = useState(null);
  const [loadingData, setLoadingData]   = useState(false);

  const containerRef = useRef(null);

  /* ── Fetch live dashboard data ── */
  const loadDashboardData = useCallback(async () => {
    setLoadingData(true);
    try {
      const [profileData, nwData, accounts, assets] = await Promise.allSettled([
        api.get("/api/v1/auth/me"),
        api.get("/api/v1/networth"),
        api.get("/api/v1/aggregator/accounts"),
        api.get("/api/v1/assets"),
      ]);
      if (profileData.status === "fulfilled") setUser(profileData.value);
      if (nwData.status     === "fulfilled") setNetWorth(nwData.value);
      if (accounts.status   === "fulfilled") setAaAccounts(accounts.value);
      if (assets.status     === "fulfilled") setPhysicalAssets(assets.value);
    } catch (_) { /* silently degrade */ }
    finally { setLoadingData(false); }
  }, []);

  /* ── Page transitions ── */
  useEffect(() => {
    if (page === "landing") {
      setQuoteVisible(false);
      const t = setTimeout(() => setQuoteVisible(true), 300);
      return () => clearTimeout(t);
    }
  }, [page]);

  useEffect(() => {
    if (page === "vision") {
      setVisionVisible(false);
      const t = setTimeout(() => setVisionVisible(true), 200);
      return () => clearTimeout(t);
    }
  }, [page]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const onScroll = () => {
      const idx = Math.round(el.scrollTop / el.clientHeight);
      setDashSection(Math.min(idx, 2));
    };
    el.addEventListener("scroll", onScroll);
    return () => el.removeEventListener("scroll", onScroll);
  }, [page]);

  useEffect(() => {
    if (page !== "dashboard") return;
    setDashVisible(v => { const n = [...v]; n[dashSection] = true; return n; });
  }, [dashSection, page]);

  useEffect(() => {
    if (page === "dashboard") {
      setTimeout(() => setDashVisible([true, false, false]), 150);
      loadDashboardData();
    }
  }, [page, loadDashboardData]);

  /* ── Auth handlers ── */
  const handleLogin = async () => {
    if (!loginData.email || !loginData.password) {
      setLoginError("Please enter your email and password.");
      return;
    }
    setLoginError("");
    setIsLoggingIn(true);
    try {
      const data = await api.post("/api/v1/auth/login", {
        email:    loginData.email,
        password: loginData.password,
      });
      localStorage.setItem("access_token",  data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      setPage("dashboard");
    } catch (err) {
      setLoginError(err.message || "Login failed. Please check your credentials.");
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleRegister = async () => {
    if (!loginData.email || !loginData.password) {
      setLoginError("Please enter your email and password.");
      return;
    }
    if (loginData.password.length < 8) {
      setLoginError("Password must be at least 8 characters.");
      return;
    }
    setLoginError("");
    setIsLoggingIn(true);
    try {
      const data = await api.post("/api/v1/auth/register", {
        email:    loginData.email,
        password: loginData.password,
      });
      localStorage.setItem("access_token",  data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      setPage("dashboard");
    } catch (err) {
      setLoginError(err.message || "Registration failed.");
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
    setNetWorth(null);
    setAaAccounts([]);
    setPhysicalAssets([]);
    setPage("landing");
  };

  const handleRecomputeNetWorth = async () => {
    try {
      await api.post("/api/v1/networth/recompute", {});
      const nw = await api.get("/api/v1/networth");
      setNetWorth(nw);
    } catch (_) {}
  };

  const scrollDashTo = (i) => {
    const el = containerRef.current;
    if (el) el.scrollTo({ top: i * el.clientHeight, behavior: "smooth" });
  };

  /* ── Page routing ── */
  if (page === "landing") return <LandingPage onEnter={() => setPage("vision")} visible={quoteVisible} />;
  if (page === "vision")  return <VisionPage  visible={visionVisible} onLogin={() => setPage("login")} />;
  if (page === "login")   return (
    <LoginPage
      data={loginData} onChange={setLoginData} onSubmit={authMode === "login" ? handleLogin : handleRegister}
      error={loginError} loading={isLoggingIn} onBack={() => setPage("vision")}
      authMode={authMode} setAuthMode={setAuthMode}
    />
  );

  /* ── Dashboard ── */
  const dashBgs = [
    "radial-gradient(ellipse 80% 60% at 20% 30%, #0d2a2e 0%, #0f172a 60%, #091020 100%)",
    "radial-gradient(ellipse 80% 60% at 80% 20%, #1a1040 0%, #0f172a 60%, #0a1520 100%)",
    "radial-gradient(ellipse 80% 60% at 50% 80%, #2a0d1a 0%, #0f172a 60%, #100a20 100%)",
  ];

  const netWorthValue = netWorth ? parseFloat(netWorth.net_worth) : null;
  const aaBalance     = netWorth ? parseFloat(netWorth.aa_assets)  : null;
  const physValue     = netWorth ? parseFloat(netWorth.physical_assets) : null;

  return (
    <div style={{ position: "relative", width: "100%", height: "100vh", overflow: "hidden", fontFamily: "'Courier New', monospace" }}>
      {dashBgs.map((bg, i) => (
        <div key={i} style={{ position: "fixed", inset: 0, background: bg, opacity: dashSection === i ? 1 : 0, transition: "opacity 1s ease", zIndex: 0 }} />
      ))}
      <Grain />

      {/* HEADER */}
      <header style={{ position: "fixed", top: 0, left: 0, right: 0, zIndex: 50, padding: "14px 32px", display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid rgba(255,255,255,0.06)", backdropFilter: "blur(18px)", background: "rgba(9,12,24,0.7)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <GlowDot color="#00c9a7" />
          <span style={{ fontSize: 13, letterSpacing: "0.18em", color: "#fff", fontWeight: 700 }}>WEALTH TWIN</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <span style={{ fontSize: 11, color: "#00c9a7", letterSpacing: "0.1em" }}>▲ NIFTY +0.84%</span>
          {netWorthValue !== null && (
            <span style={{ fontSize: 12, color: "rgba(255,255,255,0.6)", letterSpacing: "0.05em" }}>
              ₹{fmt(netWorthValue)} net
            </span>
          )}
          {user && (
            <span style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", letterSpacing: "0.06em" }}>
              {user.full_name || user.email.split("@")[0]}
            </span>
          )}
          <button onClick={handleLogout} style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", background: "none", border: "1px solid rgba(255,255,255,0.1)", padding: "4px 12px", borderRadius: 6, cursor: "pointer", letterSpacing: "0.1em", fontFamily: "'Courier New', monospace" }}>
            SIGN OUT
          </button>
        </div>
      </header>

      <div ref={containerRef} style={{ position: "relative", zIndex: 10, height: "100vh", overflowY: "scroll", scrollSnapType: "y mandatory" }}>

        {/* DASH 1: WEALTH */}
        <section style={{ height: "100vh", scrollSnapAlign: "start", display: "flex", flexDirection: "column", justifyContent: "center", padding: "80px 36px 40px" }}>
          <div style={enter(dashVisible[0], 0)}>
            <Tag color="#00c9a7">01 / WEALTH OVERVIEW</Tag>
            <BigTitle gradient="linear-gradient(135deg,#fff 40%,rgba(0,201,167,0.7))">Your AI Wealth<br />Twin is Active</BigTitle>
          </div>

          {/* Live Net Worth Cards */}
          {netWorthValue !== null && (
            <div style={{ ...enter(dashVisible[0], 0), display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 18 }}>
              {[
                { label: "NET WORTH",     value: `₹${fmt(netWorthValue)}`,       color: "#00c9a7" },
                { label: "AA BALANCE",    value: `₹${fmt(aaBalance || 0)}`,       color: "#4f8ef7" },
                { label: "PHYSICAL",      value: `₹${fmt(physValue || 0)}`,       color: "#a78bfa" },
                { label: "LIABILITIES",   value: `₹${fmt(parseFloat(netWorth.total_liabilities || 0))}`, color: "#f87171" },
              ].map((c, i) => (
                <div key={i} style={{ background: `${c.color}0d`, border: `1px solid ${c.color}33`, borderRadius: 10, padding: "10px 18px", minWidth: 130 }}>
                  <p style={{ fontSize: 10, color: c.color, letterSpacing: "0.15em", marginBottom: 4 }}>{c.label}</p>
                  <p style={{ fontSize: 16, fontWeight: 700, color: "#fff" }}>{c.value}</p>
                </div>
              ))}
              <button onClick={handleRecomputeNetWorth} style={{ padding: "10px 16px", borderRadius: 10, border: "1px solid rgba(0,201,167,0.3)", background: "rgba(0,201,167,0.08)", color: "#00c9a7", fontSize: 11, letterSpacing: "0.08em", cursor: "pointer", fontFamily: "'Courier New', monospace", alignSelf: "center" }}>
                ↻ REFRESH
              </button>
            </div>
          )}

          {/* AA Accounts */}
          {aaAccounts.length > 0 && (
            <div style={{ ...enter(dashVisible[0], 1), maxWidth: 640, marginBottom: 16 }}>
              <Tag color="rgba(79,142,247,0.7)">LINKED BANK ACCOUNTS</Tag>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 6 }}>
                {aaAccounts.map((acc, i) => (
                  <div key={i} style={{ background: "rgba(79,142,247,0.06)", border: "1px solid rgba(79,142,247,0.2)", borderRadius: 10, padding: "10px 14px", minWidth: 160 }}>
                    <p style={{ fontSize: 11, color: "#4f8ef7", letterSpacing: "0.1em" }}>{acc.fip_name}</p>
                    <p style={{ fontSize: 13, color: "#fff", fontWeight: 700, marginTop: 4 }}>₹{fmt(acc.current_balance)}</p>
                    <p style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", marginTop: 2 }}>{acc.masked_account_number}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div style={{ ...enter(dashVisible[0], 1), maxWidth: 640 }}>
            <GlassCard accent="#00c9a7">
              <Tag color="rgba(255,255,255,0.35)">LIVE ANALYSIS</Tag>
              <p style={{ fontSize: 14, lineHeight: 1.9, color: "rgba(255,255,255,0.75)", marginTop: 10 }}>
                Continuous monitoring of spending patterns, portfolio allocation, and market signals. Analysis shows <span style={{ color: "#f59e0b" }}>moderate equity concentration</span> and <span style={{ color: "#f87171" }}>insufficient emergency liquidity</span>.
              </p>
              <button style={ctaStyle("#00c9a7")}>Generate Detailed Plan →</button>
            </GlassCard>
          </div>

          <div style={{ ...enter(dashVisible[0], 2), marginTop: 20 }}>
            <Tag color="rgba(255,255,255,0.3)">AI INSIGHTS</Tag>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 10 }}>
              {insights.map((ins) => (
                <div key={ins.id} onClick={() => setSelectedInsight(selectedInsight === ins.id ? null : ins.id)} style={{ background: selectedInsight === ins.id ? `${ins.color}11` : "rgba(255,255,255,0.03)", border: `1px solid ${selectedInsight === ins.id ? ins.color + "44" : "rgba(255,255,255,0.07)"}`, borderRadius: 12, padding: 16, cursor: "pointer", transition: "all 0.3s ease", flex: "1 1 160px", maxWidth: 240 }}>
                  <span style={{ fontSize: 18, color: ins.color }}>{ins.icon}</span>
                  <p style={{ fontWeight: 700, fontSize: 13, marginTop: 8, marginBottom: 4 }}>{ins.title}</p>
                  <p style={{ fontSize: 12, color: "rgba(255,255,255,0.5)", lineHeight: 1.5 }}>{ins.summary}</p>
                  {selectedInsight === ins.id && <p style={{ marginTop: 10, fontSize: 12, color: ins.color, borderTop: `1px solid ${ins.color}33`, paddingTop: 10 }}>{ins.detail}</p>}
                </div>
              ))}
            </div>
          </div>
          <ScrollHint label="Investments" />
        </section>

        {/* DASH 2: INVESTMENTS + PHYSICAL ASSETS */}
        <section style={{ height: "100vh", scrollSnapAlign: "start", display: "flex", flexDirection: "column", justifyContent: "center", padding: "80px 36px 40px" }}>
          <div style={enter(dashVisible[1], 0)}>
            <Tag color="#4f8ef7">02 / INVESTMENT STRATEGY</Tag>
            <BigTitle gradient="linear-gradient(135deg,#fff 40%,rgba(79,142,247,0.7))">Portfolio<br />Allocation</BigTitle>
          </div>
          <div style={{ ...enter(dashVisible[1], 1), maxWidth: 640, display: "flex", flexDirection: "column", gap: 14 }}>
            {investments.map((inv, i) => (
              <div key={i} style={{ background: "rgba(255,255,255,0.03)", border: `1px solid ${inv.color}22`, borderRadius: 12, padding: "14px 20px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8, fontSize: 13 }}>
                  <span style={{ color: "rgba(255,255,255,0.85)" }}>{inv.label}</span>
                  <span><span style={{ color: inv.color, fontWeight: 700 }}>{inv.pct}%</span><span style={{ color: "rgba(255,255,255,0.3)", fontSize: 11, marginLeft: 6 }}>target {inv.target}%</span></span>
                </div>
                <div style={{ height: 5, background: "rgba(255,255,255,0.07)", borderRadius: 999, overflow: "hidden" }}>
                  <div style={{ height: "100%", width: dashVisible[1] ? `${inv.pct}%` : "0%", background: inv.color, borderRadius: 999, transition: `width 1s ${i * 0.15}s cubic-bezier(0.34,1.56,0.64,1)`, boxShadow: `0 0 8px ${inv.color}88` }} />
                </div>
              </div>
            ))}

            {/* Physical Assets from backend */}
            {physicalAssets.length > 0 && (
              <div style={{ background: "rgba(167,139,250,0.06)", border: "1px solid rgba(167,139,250,0.2)", borderRadius: 12, padding: "14px 20px" }}>
                <Tag color="#a78bfa">PHYSICAL ASSETS</Tag>
                <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 8 }}>
                  {physicalAssets.slice(0, 4).map((a, i) => (
                    <div key={i} style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
                      <span style={{ color: "rgba(255,255,255,0.7)" }}>{a.name}</span>
                      <span style={{ color: "#a78bfa", fontWeight: 700 }}>₹{fmt(a.current_value)}</span>
                    </div>
                  ))}
                  {physicalAssets.length > 4 && (
                    <p style={{ fontSize: 11, color: "rgba(255,255,255,0.3)" }}>+ {physicalAssets.length - 4} more assets</p>
                  )}
                </div>
              </div>
            )}

            <div style={{ background: "rgba(167,139,250,0.06)", border: "1px solid rgba(167,139,250,0.2)", borderRadius: 12, padding: "12px 20px", fontSize: 13, color: "rgba(255,255,255,0.6)", lineHeight: 1.7 }}>
              💡 <span style={{ color: "#a78bfa", fontWeight: 600 }}>AI Recommendation:</span> Rebalance equity to 60%, increase fixed income to 30%, automate monthly SIP of ₹15,000.
            </div>
          </div>
          <ScrollHint label="Fraud Shield" />
        </section>

        {/* DASH 3: FRAUD */}
        <section style={{ height: "100vh", scrollSnapAlign: "start", display: "flex", flexDirection: "column", justifyContent: "center", padding: "80px 36px 40px" }}>
          <div style={enter(dashVisible[2], 0)}>
            <Tag color="#f87171">03 / FRAUD SHIELD</Tag>
            <BigTitle gradient="linear-gradient(135deg,#fff 40%,rgba(248,113,113,0.7))">Active<br />Threat Alerts</BigTitle>
          </div>
          <div style={{ ...enter(dashVisible[2], 1), display: "flex", flexDirection: "column", gap: 10, maxWidth: 640 }}>
            {fraudAlerts.map((a, i) => (
              <div key={i} style={{ background: "rgba(248,113,113,0.06)", border: `1px solid ${a.level === "high" ? "rgba(248,113,113,0.35)" : "rgba(248,113,113,0.15)"}`, borderRadius: 12, padding: "14px 20px", display: "flex", justifyContent: "space-between", alignItems: "center", animation: `slideIn 0.5s ${i * 0.12}s both ease` }}>
                <div>
                  <span style={{ fontSize: 10, letterSpacing: "0.1em", padding: "2px 8px", borderRadius: 999, background: a.level === "high" ? "rgba(248,113,113,0.25)" : "rgba(248,113,113,0.1)", color: "#f87171", display: "inline-block", marginBottom: 6 }}>{a.level.toUpperCase()}</span>
                  <p style={{ fontSize: 13, color: "rgba(255,255,255,0.85)" }}>{a.msg}</p>
                </div>
                <span style={{ fontSize: 11, color: "rgba(255,255,255,0.25)" }}>{a.time}</span>
              </div>
            ))}
          </div>
          <div style={{ ...enter(dashVisible[2], 2), marginTop: 24, maxWidth: 640 }}>
            <Tag color="rgba(255,255,255,0.25)">ACTIVITY TIMELINE</Tag>
            <div style={{ borderLeft: "1px solid rgba(255,255,255,0.1)", paddingLeft: 20, marginTop: 10, display: "flex", flexDirection: "column", gap: 10 }}>
              {timeline.map((t, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, animation: `fadeIn 0.4s ${i * 0.1 + 0.3}s both` }}>
                  <div style={{ width: 7, height: 7, borderRadius: "50%", background: "rgba(255,255,255,0.2)", marginLeft: -24, marginRight: 16, flexShrink: 0 }} />
                  <span style={{ fontSize: 12, color: "rgba(255,255,255,0.65)", flex: 1 }}>{t.event}</span>
                  <span style={{ fontSize: 11, color: "rgba(255,255,255,0.25)" }}>{t.time}</span>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>

      {/* SIDE DOTS */}
      <div style={{ position: "fixed", right: 24, top: "50%", transform: "translateY(-50%)", zIndex: 100, display: "flex", flexDirection: "column", gap: 14 }}>
        {["Wealth", "Invest", "Fraud"].map((label, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }} onClick={() => scrollDashTo(i)}>
            <span style={{ fontSize: 10, color: dashSection === i ? "rgba(255,255,255,0.6)" : "transparent", letterSpacing: "0.1em", transition: "color 0.3s" }}>{label}</span>
            <div style={{ width: dashSection === i ? 22 : 6, height: 6, borderRadius: 999, background: dashSection === i ? ["#00c9a7","#4f8ef7","#f87171"][i] : "rgba(255,255,255,0.2)", transition: "all 0.4s cubic-bezier(0.34,1.56,0.64,1)", boxShadow: dashSection === i ? `0 0 10px ${["#00c9a7","#4f8ef7","#f87171"][i]}` : "none" }} />
          </div>
        ))}
      </div>

      {/* BOT */}
      <button onClick={() => setBotOpen(!botOpen)} style={{ position: "fixed", bottom: 30, right: 30, zIndex: 200, width: 54, height: 54, borderRadius: "50%", border: "1px solid rgba(255,255,255,0.1)", background: "linear-gradient(135deg,#00c9a7,#4f8ef7)", color: "#fff", fontSize: 20, cursor: "pointer", boxShadow: "0 8px 32px rgba(0,0,0,0.5)", transition: "transform 0.3s", transform: botOpen ? "rotate(45deg)" : "none" }}>
        {botOpen ? "✕" : "⬡"}
      </button>
      {botOpen && (
        <div style={{ position: "fixed", bottom: 96, right: 30, zIndex: 199, width: 270, padding: 18, borderRadius: 16, background: "rgba(10,14,28,0.95)", border: "1px solid rgba(0,201,167,0.2)", backdropFilter: "blur(20px)", boxShadow: "0 20px 60px rgba(0,0,0,0.6)", animation: "fadeIn 0.3s ease" }}>
          <p style={{ fontSize: 12, fontWeight: 700, color: "#00c9a7", letterSpacing: "0.1em", marginBottom: 8 }}>⬡ AI WEALTH TWIN</p>
          <p style={{ fontSize: 12, color: "rgba(255,255,255,0.5)", marginBottom: 12, lineHeight: 1.6 }}>Ask me about your portfolio, risks, or tax strategy.</p>
          {netWorthValue !== null && (
            <p style={{ fontSize: 11, color: "rgba(0,201,167,0.7)", marginBottom: 10 }}>
              Your net worth: ₹{fmt(netWorthValue)}
            </p>
          )}
          <div style={{ display: "flex", gap: 8 }}>
            <input value={botInput} onChange={e => setBotInput(e.target.value)} placeholder="Ask your twin…" style={{ flex: 1, padding: "8px 12px", borderRadius: 8, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "#fff", fontSize: 12, outline: "none" }} />
            <button onClick={() => setBotInput("")} style={{ padding: "8px 14px", borderRadius: 8, background: "#00c9a7", border: "none", color: "#000", fontSize: 12, cursor: "pointer", fontWeight: 700 }}>→</button>
          </div>
        </div>
      )}
      <GlobalStyles />
    </div>
  );
}

/* ─────────────────────────────────────────
   LANDING PAGE
───────────────────────────────────────── */
function LandingPage({ onEnter, visible }) {
  return (
    <div style={{ position: "relative", width: "100%", height: "100vh", overflow: "hidden", fontFamily: "'Courier New', monospace", cursor: "pointer" }} onClick={onEnter}>
      <video autoPlay muted loop playsInline style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", zIndex: 0 }}>
        <source src="/LANDING_GLOBE.mp4" type="video/mp4" />
      </video>
      <div style={{ position: "absolute", inset: 0, background: "radial-gradient(ellipse at center, rgba(0,0,0,0.3) 0%, rgba(0,0,0,0.72) 100%)", zIndex: 1 }} />
      <div style={{ position: "absolute", inset: 0, zIndex: 2, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", textAlign: "center", padding: "0 40px" }}>
        <p style={{ fontSize: 11, letterSpacing: "0.35em", color: "rgba(255,255,255,0.4)", marginBottom: 28, opacity: visible ? 1 : 0, transform: visible ? "none" : "translateY(10px)", transition: "opacity 1.2s ease, transform 1.2s ease" }}>WEALTH TWIN — AI</p>
        <h1 style={{ fontSize: "clamp(28px,5.5vw,64px)", fontWeight: 800, lineHeight: 1.15, letterSpacing: "-0.02em", color: "#fff", maxWidth: 700, opacity: visible ? 1 : 0, transform: visible ? "none" : "translateY(20px)", transition: "opacity 1.4s 0.2s ease, transform 1.4s 0.2s ease", textShadow: "0 4px 40px rgba(0,0,0,0.6)" }}>
          "SECURE AI WEALTH TWIN.<br />SMART BANKING FUTURE"
        </h1>
        <p style={{ marginTop: 44, fontSize: 11, letterSpacing: "0.25em", color: "rgba(255,255,255,0.35)", opacity: visible ? 1 : 0, transition: "opacity 1.2s 1.2s ease", animation: visible ? "breathe 3s 2s infinite" : "none" }}>
          CLICK ANYWHERE TO ENTER
        </p>
      </div>
      <GlobalStyles />
    </div>
  );
}

/* ─────────────────────────────────────────
   VISION PAGE
───────────────────────────────────────── */
function VisionPage({ visible, onLogin }) {
  return (
    <div style={{ width: "100%", minHeight: "100vh", background: "radial-gradient(ellipse 100% 80% at 50% 0%, #D4AF37 0%, #080c18 100%)", fontFamily: "'Courier New', monospace", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "60px 32px", position: "relative", overflow: "hidden" }}>
      <Grain />
      <div style={{ position: "absolute", top: "-20%", left: "50%", transform: "translateX(-50%)", width: 600, height: 400, borderRadius: "50%", background: "radial-gradient(circle, rgba(0,201,167,0.08) 0%, transparent 70%)", pointerEvents: "none", zIndex: 0 }} />
      <div style={{ position: "relative", zIndex: 1, maxWidth: 800, width: "100%", textAlign: "center" }}>
        <p style={{ fontSize: 11, letterSpacing: "0.35em", color: "#00c9a7", marginBottom: 20, opacity: visible ? 1 : 0, transition: "opacity 0.8s ease" }}>INTRODUCING</p>
        <h1 style={{ fontSize: "clamp(32px,6vw,68px)", fontWeight: 800, letterSpacing: "-0.03em", lineHeight: 1.1, background: "linear-gradient(135deg, #fff 30%, rgba(0,201,167,0.6))", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", marginBottom: 20, opacity: visible ? 1 : 0, transform: visible ? "none" : "translateY(30px)", transition: "opacity 0.9s 0.1s ease, transform 0.9s 0.1s ease" }}>
          SecureAI Wealth Twin
        </h1>
        <p style={{ fontSize: 15, lineHeight: 1.9, color: "rgba(255,255,255,0.5)", maxWidth: 540, margin: "0 auto 48px", opacity: visible ? 1 : 0, transform: visible ? "none" : "translateY(20px)", transition: "opacity 0.9s 0.25s ease, transform 0.9s 0.25s ease" }}>
          A new kind of financial intelligence — one that mirrors your wealth, predicts your risks, and acts before you even ask.
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16, marginBottom: 52 }}>
          {visionCards.map((card, i) => (
            <div key={i} style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)", borderRadius: 16, padding: "22px 18px", textAlign: "left", opacity: visible ? 1 : 0, transform: visible ? "none" : "translateY(30px)", transition: `opacity 0.8s ${0.3 + i * 0.12}s ease, transform 0.8s ${0.3 + i * 0.12}s ease` }}>
              <div style={{ fontSize: 22, color: "#00c9a7", marginBottom: 12 }}>{card.icon}</div>
              <p style={{ fontWeight: 700, fontSize: 13, color: "#fff", marginBottom: 8, letterSpacing: "0.02em" }}>{card.title}</p>
              <p style={{ fontSize: 12, color: "rgba(255,255,255,0.45)", lineHeight: 1.7 }}>{card.desc}</p>
            </div>
          ))}
        </div>
        <div style={{ opacity: visible ? 1 : 0, transition: "opacity 0.8s 0.8s ease", display: "flex", gap: 14, justifyContent: "center", flexWrap: "wrap" }}>
          <button onClick={onLogin} style={{ padding: "14px 36px", borderRadius: 10, border: "none", background: "linear-gradient(135deg,#00c9a7,#4f8ef7)", color: "#FFD700", fontWeight: 800, fontSize: 13, letterSpacing: "0.1em", cursor: "pointer", boxShadow: "0 8px 32px rgba(0,201,167,0.3)", fontFamily: "'Courier New', monospace" }}>
            GET STARTED →
          </button>
          <button style={{ padding: "14px 32px", borderRadius: 10, background: "transparent", border: "1px solid rgba(255,255,255,0.15)", color: "rgba(255,255,255,0.6)", fontWeight: 600, fontSize: 13, letterSpacing: "0.1em", cursor: "pointer", fontFamily: "'Courier New', monospace" }}>
            LEARN MORE
          </button>
        </div>
      </div>
      <GlobalStyles />
    </div>
  );
}

/* ─────────────────────────────────────────
   LOGIN / REGISTER PAGE
───────────────────────────────────────── */
function LoginPage({ data, onChange, onSubmit, error, loading, onBack, authMode, setAuthMode }) {
  const isRegister = authMode === "register";
  return (
    <div style={{ width: "100%", height: "100vh", background: "radial-gradient(ellipse 80% 80% at 60% 40%, #282e0d 0%, #08090f 100%)", fontFamily: "'Courier New', monospace", display: "flex", alignItems: "center", justifyContent: "center", position: "relative", overflow: "hidden" }}>
      <Grain />
      <video autoPlay muted loop playsInline style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", zIndex: 0 }}>
        <source src="/SMOKE_LOGIN.mp4" type="video/mp4" />
      </video>
      <div style={{ position: "absolute", width: 500, height: 500, borderRadius: "50%", background: "radial-gradient(circle, rgba(79,142,247,0.07) 0%, transparent 70%)", top: "50%", left: "50%", transform: "translate(-50%,-50%)", pointerEvents: "none" }} />
      <div style={{ position: "relative", zIndex: 1, width: "100%", maxWidth: 400, padding: "0 24px", animation: "fadeIn 0.6s ease" }}>
        <button onClick={onBack} style={{ background: "none", border: "none", color: "rgba(255,255,255,0.35)", fontSize: 12, letterSpacing: "0.15em", cursor: "pointer", marginBottom: 36, padding: 0, display: "flex", alignItems: "center", gap: 6, fontFamily: "'Courier New', monospace" }}>← BACK</button>
        <p style={{ fontSize: 11, letterSpacing: "0.3em", color: "#4f8ef7", marginBottom: 12 }}>SECURE ACCESS</p>
        <h2 style={{ fontSize: 28, fontWeight: 800, color: "#fff", marginBottom: 6, letterSpacing: "-0.02em" }}>
          {isRegister ? "Create account." : "Welcome back."}
        </h2>
        <p style={{ fontSize: 13, color: "rgba(255,255,255,0.35)", marginBottom: 36, lineHeight: 1.6 }}>
          {isRegister ? "Register to access your AI Wealth Twin." : "Sign in to access your AI Wealth Twin dashboard."}
        </p>
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <input
            id="email-input" type="email" placeholder="Email address"
            value={data.email} onChange={e => onChange({ ...data, email: e.target.value })}
            style={inputStyle}
          />
          <input
            id="password-input" type="password" placeholder={isRegister ? "Password (min 8 chars)" : "Password"}
            value={data.password} onChange={e => onChange({ ...data, password: e.target.value })}
            onKeyDown={e => e.key === "Enter" && onSubmit()}
            style={inputStyle}
          />
          {error && <p style={{ fontSize: 12, color: "#f87171", letterSpacing: "0.05em" }}>{error}</p>}
          <button
            id="submit-btn" onClick={onSubmit} disabled={loading}
            style={{ marginTop: 8, padding: "14px", borderRadius: 10, border: "none", background: loading ? "rgba(79,142,247,0.3)" : "linear-gradient(135deg,#4f8ef7,#00c9a7)", color: loading ? "rgba(255,255,255,0.5)" : "#000", fontWeight: 800, fontSize: 13, letterSpacing: "0.12em", cursor: loading ? "not-allowed" : "pointer", fontFamily: "'Courier New', monospace", transition: "all 0.3s", boxShadow: loading ? "none" : "0 6px 24px rgba(79,142,247,0.3)" }}>
            {loading ? (isRegister ? "CREATING ACCOUNT..." : "AUTHENTICATING...") : (isRegister ? "CREATE ACCOUNT →" : "SIGN IN →")}
          </button>

          {/* Toggle login/register */}
          <button
            onClick={() => { setAuthMode(isRegister ? "login" : "register"); onChange({ email: "", password: "" }); }}
            style={{ background: "none", border: "none", color: "rgba(255,255,255,0.3)", fontSize: 12, letterSpacing: "0.08em", cursor: "pointer", padding: "8px 0", fontFamily: "'Courier New', monospace", textAlign: "center" }}>
            {isRegister ? "Already have an account? SIGN IN" : "No account? CREATE ONE →"}
          </button>
        </div>
      </div>
      <GlobalStyles />
    </div>
  );
}

/* ─────────────────────────────────────────
   SHARED COMPONENTS
───────────────────────────────────────── */
function Grain() {
  return <div style={{ position: "fixed", inset: 0, zIndex: 1, pointerEvents: "none", backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E")`, opacity: 0.35 }} />;
}

function GlowDot({ color }) {
  return <div style={{ width: 8, height: 8, borderRadius: "50%", background: color, boxShadow: `0 0 10px ${color}`, animation: "pulse 2s infinite" }} />;
}

function GlassCard({ accent = "#00c9a7", children }) {
  return <div style={{ background: "rgba(255,255,255,0.03)", border: `1px solid ${accent}22`, borderRadius: 14, padding: 20, backdropFilter: "blur(10px)" }}>{children}</div>;
}

function Tag({ color, children }) {
  return <p style={{ fontSize: 11, letterSpacing: "0.25em", color, marginBottom: 10 }}>{children}</p>;
}

function BigTitle({ gradient, children }) {
  return <h1 style={{ fontSize: "clamp(26px,4.5vw,46px)", fontWeight: 800, letterSpacing: "-0.02em", lineHeight: 1.1, marginBottom: 24, background: gradient, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>{children}</h1>;
}

function ScrollHint({ label }) {
  return <div style={{ marginTop: "auto", paddingTop: 20, display: "flex", alignItems: "center", gap: 8, opacity: 0.3, fontSize: 11, letterSpacing: "0.15em", animation: "fadeIn 1s 1.5s both" }}><div style={{ width: 1, height: 22, background: "rgba(255,255,255,0.4)" }} />{label} ↓</div>;
}

const inputStyle = { padding: "13px 16px", borderRadius: 10, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.1)", color: "#fff", fontSize: 13, outline: "none", fontFamily: "'Courier New', monospace", transition: "border-color 0.2s", width: "100%", boxSizing: "border-box" };

const ctaStyle = (color) => ({ marginTop: 16, padding: "9px 20px", borderRadius: 8, border: `1px solid ${color}44`, background: `${color}11`, color, fontSize: 12, letterSpacing: "0.08em", cursor: "pointer", fontFamily: "'Courier New', monospace" });

function enter(visible, delay) {
  return { opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(28px)", transition: `opacity 0.7s ${delay * 0.18}s ease, transform 0.7s ${delay * 0.18}s cubic-bezier(0.34,1.2,0.64,1)` };
}

function GlobalStyles() {
  return <style>{`
    @keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:0.4;transform:scale(0.8)}}
    @keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
    @keyframes slideIn{from{opacity:0;transform:translateX(-20px)}to{opacity:1;transform:translateX(0)}}
    @keyframes breathe{0%,100%{opacity:0.35}50%{opacity:0.7}}
    *{box-sizing:border-box;margin:0;padding:0;}
    ::-webkit-scrollbar{display:none;}
  `}</style>;
}