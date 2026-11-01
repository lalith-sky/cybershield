// CyberShield AI — frontend logic
// Handles tab switching, calling the Flask prediction API, and rendering
// the verdict / confidence / explainability panel.

(function () {
  const state = {
    activeTab: "job", // "job" | "phishing"
  };

  const LANE_LABELS = {
    job: "PASTE JOB OFFER TEXT",
    phishing: "PASTE EMAIL CONTENT",
  };

  const PROB_LABELS = {
    job: { neg: "Genuine", pos: "Fraudulent" },
    phishing: { neg: "Legitimate", pos: "Phishing" },
  };

  const SAMPLES = {
    job: {
      threat: "Congratulations! You have been selected for the Data Entry Operator position at Global Tech Solutions. No interview required. Pay a refundable registration fee of ₹1,000 to activate your employee account and start earning ₹2000 per day from home immediately.",
      safe: "Hi Priya, thank you for applying to the Software Developer position at Nexora Corp. We would like to invite you for a video interview with our hiring team next Tuesday at 10 AM. Please confirm your availability by replying to this email.",
    },
    phishing: {
      threat: "URGENT: Your Netflix account has been temporarily suspended due to unusual activity. Click here to verify your identity immediately: http://secure-login-verify.com/account or your account will be permanently deleted within 24 hours.",
      safe: "Hi, this is a reminder that your Amazon subscription will renew automatically on your billing date. You can review or manage your subscription anytime from your account settings on our official app or website.",
    },
  };

  // ---------- elements ----------
  const tabs = document.querySelectorAll(".tab");
  const laneLabel = document.getElementById("laneLabel");
  const inputText = document.getElementById("inputText");
  const scanBtn = document.getElementById("scanBtn");
  const scanBtnLabel = document.getElementById("scanBtnLabel");
  const scanline = document.getElementById("scanline");

  const resultEmpty = document.getElementById("resultEmpty");
  const resultCard = document.getElementById("resultCard");
  const resultError = document.getElementById("resultError");

  const verdictStamp = document.getElementById("verdictStamp");
  const verdictText = document.getElementById("verdictText");
  const confidenceValue = document.getElementById("confidenceValue");
  const confidenceBarFill = document.getElementById("confidenceBarFill");
  const probLabelNeg = document.getElementById("probLabelNeg");
  const probLabelPos = document.getElementById("probLabelPos");
  const probValueNeg = document.getElementById("probValueNeg");
  const probValuePos = document.getElementById("probValuePos");
  const termsBlock = document.getElementById("termsBlock");
  const termChips = document.getElementById("termChips");

  const sampleThreatBtn = document.getElementById("sampleThreat");
  const sampleSafeBtn = document.getElementById("sampleSafe");

  // ---------- tab switching ----------
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => {
        t.classList.remove("active");
        t.setAttribute("aria-selected", "false");
      });
      tab.classList.add("active");
      tab.setAttribute("aria-selected", "true");
      state.activeTab = tab.dataset.tab;
      laneLabel.textContent = LANE_LABELS[state.activeTab];
      resetResultPanel();
    });
  });

  function resetResultPanel() {
    resultCard.style.display = "none";
    resultError.style.display = "none";
    resultEmpty.style.display = "block";
  }

  // ---------- samples ----------
  sampleThreatBtn.addEventListener("click", () => {
    inputText.value = SAMPLES[state.activeTab].threat;
  });
  sampleSafeBtn.addEventListener("click", () => {
    inputText.value = SAMPLES[state.activeTab].safe;
  });

  // ---------- scan action ----------
  scanBtn.addEventListener("click", runScan);
  inputText.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") runScan();
  });

  async function runScan() {
    const text = inputText.value.trim();
    if (!text) {
      showError("Please enter some text to analyze.");
      return;
    }

    setLoading(true);
    resultError.style.display = "none";

    const endpoint = state.activeTab === "job" ? "/predict/job" : "/predict/phishing";

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const data = await res.json();

      if (data.error) {
        showError(data.error);
      } else {
        renderResult(data);
      }
    } catch (err) {
      showError("Could not reach the detection service. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  function setLoading(isLoading) {
    scanBtn.disabled = isLoading;
    scanBtnLabel.textContent = isLoading ? "Scanning..." : "Analyze Content";
    scanline.classList.toggle("active", isLoading);
  }

  function showError(message) {
    resultEmpty.style.display = "none";
    resultCard.style.display = "none";
    resultError.style.display = "block";
    resultError.textContent = message;
  }

  function renderResult(data) {
    resultEmpty.style.display = "none";
    resultError.style.display = "none";
    resultCard.style.display = "flex";

    // restart the stamp animation
    resultCard.style.animation = "none";
    void resultCard.offsetWidth;
    resultCard.style.animation = "";

    const labels = PROB_LABELS[state.activeTab];

    verdictText.textContent = data.is_threat ? "THREAT DETECTED" : "VERIFIED SAFE";
    verdictStamp.classList.toggle("threat", data.is_threat);

    confidenceValue.textContent = `${data.confidence}%`;
    requestAnimationFrame(() => {
      confidenceBarFill.style.width = `${data.confidence}%`;
    });

    probLabelNeg.textContent = labels.neg;
    probLabelPos.textContent = labels.pos;

    const negKey = Object.keys(data.probabilities).find((k) => k !== getPositiveKey(data));
    const posKey = getPositiveKey(data);
    probValueNeg.textContent = `${data.probabilities[negKey]}%`;
    probValuePos.textContent = `${data.probabilities[posKey]}%`;

    termChips.innerHTML = "";
    if (data.top_terms && data.top_terms.length) {
      termsBlock.style.display = "flex";
      data.top_terms.forEach((term) => {
        const chip = document.createElement("span");
        chip.className = "term-chip";
        chip.textContent = term;
        termChips.appendChild(chip);
      });
    } else {
      termsBlock.style.display = "none";
    }
  }

  function getPositiveKey(data) {
    // the positive (threat) label is whichever key matches data.prediction
    // when is_threat is true, otherwise it's the OTHER key
    const keys = Object.keys(data.probabilities);
    if (data.is_threat) return data.prediction;
    return keys.find((k) => k !== data.prediction);
  }

  // ---------- metrics ----------
  async function loadMetrics() {
    try {
      const res = await fetch("/api/metrics");
      const data = await res.json();
      populateHeroStats(data);
      populateMetricsGrid(data);
    } catch (err) {
      // fail silently — hero stats keep their placeholder dashes
    }
  }

  function populateHeroStats(data) {
    document.querySelectorAll("[data-metric]").forEach((el) => {
      const path = el.dataset.metric.split(".");
      let value = data;
      path.forEach((p) => (value = value ? value[p] : undefined));
      if (typeof value === "number") {
        el.textContent = `${Math.round(value * 1000) / 10}%`;
      }
    });
  }

  function populateMetricsGrid(data) {
    const grid = document.getElementById("metricsGrid");
    if (!grid) return;

    const cards = [
      { title: "FAKE JOB OFFER DETECTION", m: data.job_scam },
      { title: "PHISHING EMAIL DETECTION", m: data.phishing },
    ];

    grid.innerHTML = cards
      .map(
        (c) => `
      <div class="metric-card">
        <span class="metric-card-title mono">${c.title}</span>
        <div class="metric-row"><span>Accuracy</span><span>${pct(c.m.accuracy)}</span></div>
        <div class="metric-row"><span>Precision</span><span>${pct(c.m.precision)}</span></div>
        <div class="metric-row"><span>Recall</span><span>${pct(c.m.recall)}</span></div>
        <div class="metric-row"><span>F1-score</span><span>${pct(c.m.f1_score)}</span></div>
        <div class="metric-row"><span>Test samples</span><span>${c.m.test_size}</span></div>
      </div>
    `
      )
      .join("");
  }

  function pct(v) {
    return `${Math.round(v * 1000) / 10}%`;
  }

  loadMetrics();
})();
