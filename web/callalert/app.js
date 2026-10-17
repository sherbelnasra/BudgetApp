const DEMO = {
  generated_at: new Date().toISOString(),
  date: new Date().toISOString().slice(0, 10),
  disclaimer:
    "Educational alerts only — not financial advice. Cheap OTM calls can expire worthless.",
  alerts_count: 1,
  alerts: [
    {
      ticker: "DEMO",
      contract_symbol: "DEMO261120C00120000",
      strike: 120,
      expiry: "2026-11-20",
      days_to_expiry: 34,
      mid_price: 0.17,
      open_interest: 850,
      pct_otm: 20,
      reason: "Demo alert — enable Live scan from your API for real contracts.",
      score: 8.5,
      action: "BUY_CALL",
    },
  ],
};

const els = {
  list: document.getElementById("alerts"),
  status: document.getElementById("status"),
  disclaimer: document.getElementById("disclaimer"),
  error: document.getElementById("error"),
  install: document.getElementById("installBanner"),
  installBtn: document.getElementById("installBtn"),
  refreshBtn: document.getElementById("refreshBtn"),
  liveBtn: document.getElementById("liveBtn"),
  demoBtn: document.getElementById("demoBtn"),
  modeTag: document.getElementById("modeTag"),
};

let deferredPrompt = null;
let useDemo = true;
const notifiedKey = "callalert_notified";

function money(n) {
  return `$${Number(n).toFixed(2)}`;
}

function render(payload) {
  els.error.textContent = "";
  els.disclaimer.textContent = payload.disclaimer || "";
  els.modeTag.textContent = payload.demo || useDemo ? "DEMO" : "LIVE";
  els.status.textContent = payload.generated_at
    ? `Updated ${String(payload.generated_at).slice(0, 19)}`
    : "";

  const alerts = payload.alerts || [];
  if (!alerts.length) {
    els.list.innerHTML =
      '<p class="empty">No monthly calls in the $0.15–$0.20 band right now.</p>';
    return;
  }

  els.list.innerHTML = alerts
    .map(
      (a) => `
      <article class="card">
        <div class="card-top">
          <div class="ticker">${a.ticker}</div>
          <div class="premium">${money(a.mid_price)} mid</div>
        </div>
        <p class="meta">Strike ${money(a.strike)} · Exp ${a.expiry} · ${a.days_to_expiry}d · OI ${a.open_interest}</p>
        <p class="reason">${a.reason || ""}</p>
      </article>`
    )
    .join("");

  maybeNotify(alerts);
}

async function maybeNotify(alerts) {
  if (!("Notification" in window)) return;
  if (Notification.permission === "default") {
    try {
      await Notification.requestPermission();
    } catch (_) {
      /* ignore */
    }
  }
  if (Notification.permission !== "granted") return;

  const seen = new Set(JSON.parse(localStorage.getItem(notifiedKey) || "[]"));
  for (const a of alerts) {
    const id = a.contract_symbol || `${a.ticker}-${a.strike}-${a.expiry}`;
    if (seen.has(id)) continue;
    new Notification(`Buy call: ${a.ticker}`, {
      body: `${money(a.mid_price)} mid · strike ${money(a.strike)} · ${a.expiry}`,
      icon: "./icons/icon-192.png",
      badge: "./icons/icon-192.png",
      tag: id,
    });
    seen.add(id);
  }
  localStorage.setItem(notifiedKey, JSON.stringify([...seen].slice(-100)));
}

async function loadAlerts() {
  els.refreshBtn.disabled = true;
  els.error.textContent = "";
  try {
    if (useDemo) {
      try {
        const res = await fetch("/v1/call-alerts/demo");
        if (res.ok) {
          render(await res.json());
          return;
        }
      } catch (_) {
        /* fall through to embedded demo */
      }
      render({ ...DEMO, demo: true });
      return;
    }

    const res = await fetch("/v1/call-alerts?top_n=10&min_premium=0.15&max_premium=0.20");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    render(await res.json());
  } catch (err) {
    els.error.textContent =
      err.message ||
      "Could not reach the CallAlert API. Stay on demo or start uvicorn on your computer.";
    render({ ...DEMO, demo: true });
  } finally {
    els.refreshBtn.disabled = false;
  }
}

function setupInstall() {
  const isStandalone =
    window.matchMedia("(display-mode: standalone)").matches ||
    window.navigator.standalone === true;

  if (isStandalone) return;

  const isIos = /iphone|ipad|ipod/i.test(navigator.userAgent);
  if (isIos) {
    els.install.classList.add("show");
    els.installBtn.style.display = "none";
    return;
  }

  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredPrompt = e;
    els.install.classList.add("show");
  });

  els.installBtn.addEventListener("click", async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    deferredPrompt = null;
    els.install.classList.remove("show");
  });
}

els.demoBtn.addEventListener("click", () => {
  useDemo = true;
  loadAlerts();
});

els.liveBtn.addEventListener("click", () => {
  useDemo = false;
  loadAlerts();
});

els.refreshBtn.addEventListener("click", () => loadAlerts());

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("./sw.js").catch(() => {});
}

setupInstall();
loadAlerts();
setInterval(loadAlerts, 5 * 60 * 1000);
