/**
 * app.js
 * Main UI Controller for MindPulse AI (Stitch Design Reference).
 * Integrates real-time ML risk predictions, telemetry gauges, interactive surveys,
 * counselor case management, and responsive navigation.
 */

import { API } from "./api.js";
import { renderTrendChart, renderRadarChart, renderCohortChart, renderBenchmarkChart } from "./charts.js";

// Global Application State
const state = {
  currentRole: "student", // 'student' or 'counselor'
  currentStudentId: null,
  currentStudentProfile: null,
  authenticatedUser: null,
  students: [],
  allUsers: [],
  cachedBenchmark: null,
  selectedMood: "steady",
  lastAssessmentResult: null,
  latestSurveyData: null
};

// DOM Entry Point
document.addEventListener("DOMContentLoaded", async () => {
  initPWA();
  initLandingPageListeners();
  initNavListeners();
  initSliderListeners();
  initDailyPulseWidget();
  initModalListeners();
  initScrollAndMobileNav();
  
  // Check persisted session
  const storedSession = localStorage.getItem("mindpulse_user_session");
  if (storedSession) {
    try {
      state.authenticatedUser = JSON.parse(storedSession);
      showDashboard();
      updateAuthUI();
      await loadInitialUsers();

      // Route to initial page from URL hash or default by role
      const initialHash = window.location.hash.replace("#", "");
      if (initialHash && ["dashboard", "pulse", "survey", "spikes", "care", "counselor"].includes(initialHash)) {
        navigateToPage(initialHash);
      } else if (state.authenticatedUser.role === "counselor") {
        navigateToPage("counselor");
      } else {
        navigateToPage("dashboard");
      }
    } catch (e) {
      localStorage.removeItem("mindpulse_user_session");
      showLandingPage();
    }
  } else {
    showLandingPage();
    // Pre-fetch demo users in background
    API.getUsers().then(users => {
      state.allUsers = users;
      state.students = users.filter(u => u.role === "student");
    }).catch(err => console.error("Initial prefetch error:", err));
  }
});

/**
 * Navigation and Top Bar Listeners
 */
function initNavListeners() {
  const studentSelector = document.getElementById("student-selector");
  const triggerCheckIn = document.getElementById("triggerCheckIn");
  const btnRefresh = document.getElementById("btn-refresh-telemetry");

  // Wire all Desktop Header Nav Tab Links (data-page attributes)
  document.querySelectorAll(".nav-tab-link").forEach(link => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const page = link.dataset.page || "dashboard";
      navigateToPage(page);
    });
  });

  if (studentSelector) {
    studentSelector.addEventListener("change", (e) => {
      state.currentStudentId = parseInt(e.target.value, 10);
      const matched = state.students.find(s => s.student_id === state.currentStudentId);
      state.currentStudentProfile = matched;
      loadStudentDashboard();
    });
  }

  if (triggerCheckIn) {
    triggerCheckIn.addEventListener("click", () => {
      navigateToPage("pulse");
    });
  }

  if (btnRefresh) {
    btnRefresh.addEventListener("click", async () => {
      btnRefresh.classList.add("animate-spin");
      await loadStudentDashboard();
      setTimeout(() => btnRefresh.classList.remove("animate-spin"), 600);
    });
  }

  // ML Benchmark & Crisis buttons
  const btnBenchmark = document.getElementById("btn-view-benchmark");
  if (btnBenchmark) btnBenchmark.addEventListener("click", openBenchmarkModal);

  const btnCrisis = document.getElementById("btn-crisis-helpline");
  if (btnCrisis) btnCrisis.addEventListener("click", openCrisisModal);

  document.querySelectorAll(".btn-open-crisis-helpline").forEach(btn => {
    btn.addEventListener("click", openCrisisModal);
  });

  // Logout button
  const btnLogout = document.getElementById("btn-logout");
  if (btnLogout) {
    btnLogout.addEventListener("click", handleLogout);
  }

  // Print button in counselor view
  const btnPrint = document.getElementById("btn-print-report");
  if (btnPrint) btnPrint.addEventListener("click", () => window.print());

  // Download Student Burnout Report buttons
  const btnDownloadStudent = document.getElementById("btn-download-student-report");
  if (btnDownloadStudent) {
    btnDownloadStudent.addEventListener("click", () => handleDownloadStudentReport());
  }

  const btnModalDownload = document.getElementById("btn-modal-download-report");
  if (btnModalDownload) {
    btnModalDownload.addEventListener("click", () => handleDownloadStudentReport());
  }

  // Browser Back/Forward navigation with URL hash
  window.addEventListener("hashchange", () => {
    const hash = window.location.hash.replace("#", "");
    if (hash && ["dashboard", "pulse", "survey", "spikes", "care", "counselor"].includes(hash)) {
      navigateToPage(hash);
    }
  });
}

/**
 * Tab Switching (Student Dashboard vs Counselor Surveillance)
 * Preserved for backward compatibility, routes cleanly to navigateToPage()
 */
function switchTab(tab) {
  if (tab === "counselor") {
    navigateToPage("counselor");
  } else {
    navigateToPage("dashboard");
  }
}

/**
 * Dedicated Multi-Page SPA Navigation Router
 * Switches between the 6 distinct pages:
 * 1. page-dashboard (Student Dashboard & Key Metrics)
 * 2. page-pulse (60s Daily Pulse Micro-Check-in & Rest Prescriptions)
 * 3. page-survey (10-Factor AI Burnout Assessment & ML Simulator)
 * 4. page-spikes (Academic Pressure Spikes & LMS Planner)
 * 5. page-care (Care Sanctuary & 24/7 Crisis Helplines)
 * 6. page-counselor (Counselor Surveillance & Triage Portal)
 */
export function navigateToPage(targetPage) {
  if (!targetPage) return;
  
  // Normalize page name
  let pageId = targetPage.replace(/^#/, "").replace(/^page-/, "").trim().toLowerCase();
  const validPages = ["dashboard", "pulse", "survey", "spikes", "care", "counselor"];
  if (!validPages.includes(pageId)) {
    pageId = "dashboard";
  }

  // Hide all pages, show only the selected page
  const allPages = document.querySelectorAll(".app-page");
  allPages.forEach(p => {
    p.classList.add("hidden");
  });

  const activePage = document.getElementById(`page-${pageId}`);
  if (activePage) {
    activePage.classList.remove("hidden");
  }

  // Update Desktop Header Nav Tab Links
  const activeTabClasses = ["bg-primary-container", "text-on-primary", "font-semibold", "shadow-sm"];
  const inactiveTabClasses = ["text-on-surface-variant", "hover:bg-surface-container-high", "hover:text-on-surface"];
  
  document.querySelectorAll(".nav-tab-link").forEach(tab => {
    const tabTarget = tab.dataset.page;
    if (tabTarget === pageId) {
      tab.classList.add(...activeTabClasses);
      tab.classList.remove(...inactiveTabClasses);
    } else {
      tab.classList.remove(...activeTabClasses);
      tab.classList.add(...inactiveTabClasses);
    }
  });

  // Update Mobile Bottom Nav Buttons
  document.querySelectorAll("#mobile-bottom-nav .mob-nav-btn").forEach(btn => {
    const btnTarget = btn.dataset.page;
    const isCareOrCrisis = btn.id === "mob-nav-care" || btn.id === "mob-nav-crisis";
    const label = btn.querySelector("span.font-label-sm") || btn.querySelector("span:last-child");

    if (btnTarget === pageId) {
      if (isCareOrCrisis) {
        btn.className = "mob-nav-btn flex flex-col items-center justify-center py-1 px-2 rounded-xl text-rose-800 bg-rose-100/70 transition active:scale-95 flex-1 max-w-[70px]";
      } else {
        btn.className = "mob-nav-btn flex flex-col items-center justify-center py-1 px-2 rounded-xl text-primary bg-primary-fixed/40 transition active:scale-95 flex-1 max-w-[70px]";
      }
      if (label) {
        label.classList.add("font-bold");
        label.classList.remove("font-medium");
      }
    } else {
      if (isCareOrCrisis) {
        btn.className = "mob-nav-btn flex flex-col items-center justify-center py-1 px-2 rounded-xl text-rose-700 hover:text-rose-900 transition active:scale-95 flex-1 max-w-[70px]";
      } else {
        btn.className = "mob-nav-btn flex flex-col items-center justify-center py-1 px-2 rounded-xl text-on-surface-variant hover:text-primary transition active:scale-95 flex-1 max-w-[70px]";
      }
      if (label) {
        label.classList.remove("font-bold");
        label.classList.add("font-medium");
      }
    }
  });

  // Reset scroll to top cleanly
  window.scrollTo({ top: 0, behavior: "instant" });

  // Update URL hash safely without scroll jumping
  if (window.location.hash !== `#${pageId}`) {
    history.replaceState(null, "", `#${pageId}`);
  }

  // Manage role and data loading
  const isCounselor = state.authenticatedUser && state.authenticatedUser.role === "counselor";
  const studentSelectorWrap = document.getElementById("student-selector-wrapper");

  if (pageId === "counselor") {
    state.currentRole = "counselor";
    if (studentSelectorWrap) studentSelectorWrap.classList.add("hidden");
    loadCounselorSurveillance();
  } else {
    // Student pages
    if (!isCounselor) {
      state.currentRole = "student";
      if (studentSelectorWrap) studentSelectorWrap.classList.add("hidden");
    } else {
      // Counselor auditing student views
      if (studentSelectorWrap) studentSelectorWrap.classList.remove("hidden");
    }

    if (pageId === "dashboard") {
      loadStudentDashboard();
    }
  }

  // Ensure Chart.js recalculates layout after page unhides
  setTimeout(() => {
    window.dispatchEvent(new Event("resize"));
  }, 60);
}

// Global exposure for inline HTML onclick handlers
window.navigateToPage = navigateToPage;

/**
 * Initialize 10-Factor Range Sliders & Value Displays
 */
function initSliderListeners() {
  const sliders = document.querySelectorAll("input[type=range]");
  sliders.forEach(slider => {
    const valDisplay = document.getElementById(`${slider.id}-val`);
    if (valDisplay) {
      slider.addEventListener("input", () => {
        let suffix = "";
        if (slider.id.includes("hours")) suffix = " hrs";
        else if (slider.id.includes("attendance")) suffix = "%";
        else if (slider.id.includes("days")) suffix = " days";
        valDisplay.textContent = `${slider.value}${suffix}`;
      });
    }
  });

  const surveyForm = document.getElementById("survey-form");
  if (surveyForm) {
    surveyForm.addEventListener("submit", handleSurveySubmit);
  }

  const previewBtn = document.getElementById("btn-preview-risk");
  if (previewBtn) {
    previewBtn.addEventListener("click", handleInstantPreview);
  }

  // Counselor search & filters
  const searchInput = document.getElementById("student-search");
  const riskFilter = document.getElementById("risk-filter-select");
  if (searchInput) searchInput.addEventListener("input", debounce(refreshStudentsRoster, 300));
  if (riskFilter) riskFilter.addEventListener("change", refreshStudentsRoster);

  // Counselor alert tabs
  const alertTabs = document.querySelectorAll(".alert-tab-btn");
  alertTabs.forEach(btn => {
    btn.addEventListener("click", () => {
      alertTabs.forEach(b => {
        b.classList.remove("bg-primary", "text-on-primary", "active");
        b.classList.add("bg-surface-container-high", "text-on-surface-variant");
      });
      btn.classList.add("bg-primary", "text-on-primary", "active");
      btn.classList.remove("bg-surface-container-high", "text-on-surface-variant");
      refreshAlerts(btn.dataset.status);
    });
  });
}

/**
 * Daily Pulse 60s Widget (Stitch Reference Micro-Interaction)
 */
function initDailyPulseWidget() {
  const moodButtons = document.querySelectorAll(".mood-btn");
  const energySlider = document.getElementById("energySlider");
  const sliderValueText = document.getElementById("sliderValueText");
  const feedbackText = document.getElementById("feedbackText");
  const saveBtn = document.getElementById("saveCheckInBtn");

  const moodResponses = {
    overwhelmed: "Take a slow breath. Your schedule has buffer built in—let's prioritize resting tonight.",
    stressed: "Academic pressure noted. We have highlighted low-intensity recovery slots for you.",
    steady: "Steady is wonderful. You are maintaining balance through mid-week transitions.",
    energized: "Great vitality! This is an optimal window for high-retention study sessions.",
    thriving: "Peak equilibrium! Celebrate your momentum and maintain gentle boundaries."
  };

  moodButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      moodButtons.forEach(b => {
        b.classList.remove("bg-primary-fixed/50", "font-semibold");
        const lbl = b.querySelector("span:last-child");
        if (lbl) {
          lbl.classList.remove("text-primary", "font-bold");
          lbl.classList.add("text-on-surface-variant");
        }
      });

      btn.classList.add("bg-primary-fixed/50", "font-semibold");
      const selectedLabel = btn.querySelector("span:last-child");
      if (selectedLabel) {
        selectedLabel.classList.remove("text-on-surface-variant");
        selectedLabel.classList.add("text-primary", "font-bold");
      }

      state.selectedMood = btn.getAttribute("data-mood");
      if (moodResponses[state.selectedMood] && feedbackText) {
        feedbackText.textContent = moodResponses[state.selectedMood];
      }
    });
  });

  if (energySlider && sliderValueText) {
    energySlider.addEventListener("input", (e) => {
      sliderValueText.textContent = `${e.target.value} / 100`;
    });
  }

  if (saveBtn) {
    saveBtn.addEventListener("click", async () => {
      saveBtn.disabled = true;
      const originalText = saveBtn.textContent;
      saveBtn.textContent = "Telemetry Logged ✓";
      saveBtn.classList.remove("bg-surface-container-highest");
      saveBtn.classList.add("bg-primary", "text-on-primary");

      // Sync with full survey values and submit
      try {
        const energyVal = parseInt(energySlider.value, 10);
        const mappedMood = Math.max(1, Math.min(10, Math.round(energyVal / 10)));
        const mappedStress = state.selectedMood === "overwhelmed" ? 9 : state.selectedMood === "stressed" ? 7 : 3;

        document.getElementById("input-mood").value = mappedMood;
        document.getElementById("input-mood-val").textContent = mappedMood;
        document.getElementById("input-stress").value = mappedStress;
        document.getElementById("input-stress-val").textContent = mappedStress;

        const data = getSurveyFormData();
        await API.submitSurvey(state.currentStudentId, data);
        await loadStudentDashboard();
      } catch (e) {
        console.error("Daily pulse log error:", e);
      }

      setTimeout(() => {
        saveBtn.textContent = originalText;
        saveBtn.disabled = false;
        saveBtn.classList.add("bg-surface-container-highest");
        saveBtn.classList.remove("bg-primary", "text-on-primary");
      }, 2000);
    });
  }
}

function initModalListeners() {
  document.querySelectorAll(".modal-close-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".modal-container").forEach(m => m.classList.add("hidden"));
    });
  });
}

function showLandingPage() {
  const landing = document.getElementById("landing-page-view");
  const dashboard = document.getElementById("app-dashboard-view");
  const mobNav = document.getElementById("mobile-bottom-nav");
  if (landing) landing.classList.remove("hidden");
  if (dashboard) dashboard.classList.add("hidden");
  if (mobNav) mobNav.classList.add("hidden");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function showDashboard() {
  const landing = document.getElementById("landing-page-view");
  const dashboard = document.getElementById("app-dashboard-view");
  const mobNav = document.getElementById("mobile-bottom-nav");
  if (landing) landing.classList.add("hidden");
  if (dashboard) dashboard.classList.remove("hidden");
  if (mobNav) mobNav.classList.remove("hidden");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

/**
 * Navigation Enhancements: Quick-Jump Pills, Back-to-Top FAB, and Mobile Bottom Nav
 */
function initScrollAndMobileNav() {
  const backToTopBtn = document.getElementById("btn-back-to-top");
  const mobileNav = document.getElementById("mobile-bottom-nav");

  // 1. Back to Top Scroll Behavior
  const handleScroll = () => {
    if (window.scrollY > 280) {
      if (backToTopBtn) {
        backToTopBtn.classList.remove("opacity-0", "translate-y-3", "pointer-events-none");
        backToTopBtn.classList.add("opacity-100", "translate-y-0", "pointer-events-auto");
      }
    } else {
      if (backToTopBtn) {
        backToTopBtn.classList.add("opacity-0", "translate-y-3", "pointer-events-none");
        backToTopBtn.classList.remove("opacity-100", "translate-y-0", "pointer-events-auto");
      }
    }
  };

  window.addEventListener("scroll", handleScroll, { passive: true });

  if (backToTopBtn) {
    backToTopBtn.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  // 2. Quick-Jump Pill Clicks (Cross-Page Compatible)
  const quickPills = document.querySelectorAll(".quick-nav-pill");
  quickPills.forEach(pill => {
    pill.addEventListener("click", () => {
      const targetId = pill.getAttribute("data-target");
      if (!targetId) return;

      const targetEl = document.getElementById(targetId);
      if (!targetEl) return;

      // Identify which dedicated .app-page contains this target element
      const parentPage = targetEl.closest(".app-page");
      if (parentPage) {
        const pageName = parentPage.id.replace("page-", "");
        navigateToPage(pageName);
      }

      // Smooth scroll to target inside the now-visible page
      setTimeout(() => {
        targetEl.scrollIntoView({ behavior: "smooth", block: "start" });

        // Apply spotlight animation
        targetEl.classList.remove("section-spotlight");
        void targetEl.offsetWidth; // trigger reflow
        targetEl.classList.add("section-spotlight");
        setTimeout(() => targetEl.classList.remove("section-spotlight"), 2000);
      }, 50);

      // Highlight active pill within its container
      const parentNav = pill.parentElement;
      if (parentNav) {
        const isCounselor = parentNav.id === "counselor-quick-nav";
        parentNav.querySelectorAll(".quick-nav-pill").forEach(p => {
          p.className = `quick-nav-pill px-3 py-1.5 rounded-full text-xs font-semibold bg-surface-container-high hover:${isCounselor ? "bg-secondary-fixed" : "bg-primary-fixed"} text-on-surface transition-all shrink-0 flex items-center gap-1 border border-outline-variant/30`;
        });
        pill.className = `quick-nav-pill px-3 py-1.5 rounded-full text-xs font-semibold ${isCounselor ? "bg-secondary text-on-secondary" : "bg-primary text-on-primary"} shadow-sm hover:shadow transition-all shrink-0 flex items-center gap-1`;
      }
    });
  });

  // 3. Mobile Bottom Navigation Handlers (Multi-Page Dedicated Switching)
  document.querySelectorAll("#mobile-bottom-nav .mob-nav-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const isCounselor = state.authenticatedUser && state.authenticatedUser.role === "counselor";

      if (btn.id === "mob-nav-crisis") {
        openCrisisModal();
        return;
      }

      if (isCounselor) {
        if (btn.id === "mob-nav-pulse") {
          // Counselor: Jump to Alert Queue on counselor page
          navigateToPage("counselor");
          setTimeout(() => {
            const alertsSec = document.getElementById("sec-counselor-alerts");
            if (alertsSec) alertsSec.scrollIntoView({ behavior: "smooth", block: "start" });
          }, 80);
          return;
        } else if (btn.id === "mob-nav-survey") {
          // Counselor: Jump to Roster on counselor page
          navigateToPage("counselor");
          setTimeout(() => {
            const dirSec = document.getElementById("sec-counselor-directory");
            if (dirSec) dirSec.scrollIntoView({ behavior: "smooth", block: "start" });
          }, 80);
          return;
        } else if (btn.id === "mob-nav-spikes") {
          // Counselor: Audit student view
          navigateToPage("spikes");
          return;
        }
      }

      const targetPage = btn.dataset.page || "dashboard";
      navigateToPage(targetPage);
    });
  });
}


function initLandingPageListeners() {
  const tabLogin = document.getElementById("landing-tab-login");
  const tabRegister = document.getElementById("landing-tab-register");
  const formLogin = document.getElementById("landing-form-login");
  const formRegister = document.getElementById("landing-form-register");
  const cardTitle = document.getElementById("landing-auth-card-title");
  const toggleAuthLink = document.getElementById("landing-btn-toggle-auth");
  const toggleAuthPrompt = document.getElementById("landing-auth-switch-prompt");
  const roleBtnStudent = document.getElementById("landing-role-student");
  const roleBtnCounselor = document.getElementById("landing-role-counselor");
  const regStudentFields = document.getElementById("landing-reg-student-fields");
  const toggleLoginPwd = document.getElementById("landing-toggle-pwd");
  const loginPassword = document.getElementById("landing-login-password");
  const navLoginBtn = document.getElementById("landing-nav-login-btn");
  const heroCta = document.getElementById("landing-hero-cta");

  let authMode = "login";
  let registerRole = "student";

  const setAuthMode = (mode) => {
    authMode = mode;
    clearLandingAlerts();
    if (mode === "login") {
      if (tabLogin) tabLogin.className = "flex-1 py-1.5 rounded-full text-xs font-semibold transition-all bg-primary text-on-primary shadow-sm";
      if (tabRegister) tabRegister.className = "flex-1 py-1.5 rounded-full text-xs font-semibold transition-all text-on-surface-variant hover:text-on-surface";
      if (formLogin) formLogin.classList.remove("hidden");
      if (formRegister) formRegister.classList.add("hidden");
      if (cardTitle) cardTitle.textContent = "Student Portal Sign In";
      if (toggleAuthPrompt) toggleAuthPrompt.textContent = "Don't have an account?";
      if (toggleAuthLink) toggleAuthLink.textContent = "Create an account";
    } else {
      if (tabRegister) tabRegister.className = "flex-1 py-1.5 rounded-full text-xs font-semibold transition-all bg-primary text-on-primary shadow-sm";
      if (tabLogin) tabLogin.className = "flex-1 py-1.5 rounded-full text-xs font-semibold transition-all text-on-surface-variant hover:text-on-surface";
      if (formRegister) formRegister.classList.remove("hidden");
      if (formLogin) formLogin.classList.add("hidden");
      if (cardTitle) cardTitle.textContent = "Create Student Account";
      if (toggleAuthPrompt) toggleAuthPrompt.textContent = "Already have an account?";
      if (toggleAuthLink) toggleAuthLink.textContent = "Sign In";
    }
  };

  if (tabLogin) tabLogin.addEventListener("click", () => setAuthMode("login"));
  if (tabRegister) tabRegister.addEventListener("click", () => setAuthMode("register"));
  if (toggleAuthLink) {
    toggleAuthLink.addEventListener("click", () => {
      setAuthMode(authMode === "login" ? "register" : "login");
    });
  }

  // Smooth scroll to auth card
  const scrollToAuth = () => {
    const card = document.getElementById("landing-auth-card");
    if (card) {
      card.scrollIntoView({ behavior: "smooth", block: "center" });
      const emailInput = document.getElementById("landing-login-email");
      if (emailInput) setTimeout(() => emailInput.focus(), 350);
    }
  };
  if (navLoginBtn) navLoginBtn.addEventListener("click", scrollToAuth);
  if (heroCta) heroCta.addEventListener("click", scrollToAuth);

  // Role button selection
  if (roleBtnStudent && roleBtnCounselor) {
    roleBtnStudent.addEventListener("click", () => {
      registerRole = "student";
      roleBtnStudent.className = "landing-role-btn py-1.5 px-3 rounded-lg text-xs font-semibold border-2 border-primary bg-primary-fixed/40 text-primary transition flex items-center justify-center gap-1";
      roleBtnCounselor.className = "landing-role-btn py-1.5 px-3 rounded-lg text-xs font-semibold border border-outline-variant/40 bg-surface-container hover:bg-surface-container-high text-on-surface-variant transition flex items-center justify-center gap-1";
      if (regStudentFields) regStudentFields.classList.remove("hidden");
    });

    roleBtnCounselor.addEventListener("click", () => {
      registerRole = "counselor";
      roleBtnCounselor.className = "landing-role-btn py-1.5 px-3 rounded-lg text-xs font-semibold border-2 border-secondary bg-secondary-fixed/40 text-secondary transition flex items-center justify-center gap-1";
      roleBtnStudent.className = "landing-role-btn py-1.5 px-3 rounded-lg text-xs font-semibold border border-outline-variant/40 bg-surface-container hover:bg-surface-container-high text-on-surface-variant transition flex items-center justify-center gap-1";
      if (regStudentFields) regStudentFields.classList.add("hidden");
    });
  }

  // Toggle password visibility
  if (toggleLoginPwd && loginPassword) {
    toggleLoginPwd.addEventListener("click", () => {
      const isPwd = loginPassword.type === "password";
      loginPassword.type = isPwd ? "text" : "password";
      toggleLoginPwd.textContent = isPwd ? "visibility_off" : "visibility";
    });
  }

  // 1-Click Viva Demo Profiles
  document.querySelectorAll(".landing-demo-login").forEach(btn => {
    btn.addEventListener("click", async () => {
      const email = btn.dataset.email;
      const pwd = btn.dataset.pwd;
      const emailInput = document.getElementById("landing-login-email");
      const pwdInput = document.getElementById("landing-login-password");
      if (emailInput) emailInput.value = email;
      if (pwdInput) pwdInput.value = pwd;
      await executeLandingLogin(email, pwd);
    });
  });

  // Login Form Submit
  if (formLogin) {
    formLogin.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = document.getElementById("landing-login-email").value.trim();
      const password = document.getElementById("landing-login-password").value;
      await executeLandingLogin(email, password);
    });
  }

  // Register Form Submit
  if (formRegister) {
    formRegister.addEventListener("submit", async (e) => {
      e.preventDefault();
      clearLandingAlerts();
      const name = document.getElementById("landing-reg-name").value.trim();
      const email = document.getElementById("landing-reg-email").value.trim();
      const password = document.getElementById("landing-reg-password").value;

      const payload = {
        name,
        email,
        password,
        role: registerRole
      };

      if (registerRole === "student") {
        payload.student_id_number = document.getElementById("landing-reg-id")?.value.trim() || undefined;
        payload.department = document.getElementById("landing-reg-dept")?.value.trim() || undefined;
        payload.year_of_study = parseInt(document.getElementById("landing-reg-year")?.value || "3", 10);
      }

      const submitBtn = document.getElementById("landing-btn-register");
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = `<span class="material-symbols-outlined text-base animate-spin">refresh</span> Creating Account...`;
      }

      try {
        const res = await API.register(payload);
        showLandingSuccess("Account created successfully! Transitioning to your dashboard...");
        setTimeout(() => {
          onAuthSuccess(res);
        }, 750);
      } catch (err) {
        showLandingError(err.message || "Registration failed. Please check your inputs.");
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = `<span class="material-symbols-outlined text-base">person_add</span> Create Student Account`;
        }
      }
    });
  }
}

async function executeLandingLogin(email, password) {
  clearLandingAlerts();
  const submitBtn = document.getElementById("landing-btn-login");
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span class="material-symbols-outlined text-base animate-spin">refresh</span> Signing In...`;
  }

  try {
    const res = await API.login(email, password);
    showLandingSuccess(`Welcome back, ${res.user.name}! Loading your dashboard...`);
    setTimeout(() => {
      onAuthSuccess(res);
    }, 600);
  } catch (err) {
    showLandingError(err.message || "Invalid credentials. Please check your email and password.");
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `<span class="material-symbols-outlined text-base">login</span> Sign In to Dashboard`;
    }
  }
}

function showLandingError(msg) {
  const banner = document.getElementById("landing-auth-error");
  const text = document.getElementById("landing-auth-error-text");
  if (banner && text) {
    text.textContent = msg;
    banner.classList.remove("hidden");
    document.getElementById("landing-auth-success")?.classList.add("hidden");
  }
}

function showLandingSuccess(msg) {
  const banner = document.getElementById("landing-auth-success");
  const text = document.getElementById("landing-auth-success-text");
  if (banner && text) {
    text.textContent = msg;
    banner.classList.remove("hidden");
    document.getElementById("landing-auth-error")?.classList.add("hidden");
  }
}

function clearLandingAlerts() {
  const errBanner = document.getElementById("landing-auth-error");
  const succBanner = document.getElementById("landing-auth-success");
  if (errBanner) errBanner.classList.add("hidden");
  if (succBanner) succBanner.classList.add("hidden");
}

function onAuthSuccess(authRes) {
  state.authenticatedUser = authRes.user;
  localStorage.setItem("mindpulse_user_session", JSON.stringify(authRes.user));
  showDashboard();
  updateAuthUI();

  API.getUsers().then(users => {
    state.allUsers = users;
    state.students = users.filter(u => u.role === "student");
    const studentSelect = document.getElementById("student-selector");
    if (studentSelect) {
      studentSelect.innerHTML = "";
      state.students.forEach(s => {
        const opt = document.createElement("option");
        opt.value = s.student_id;
        opt.textContent = `${s.name} (${s.student_id_number})`;
        studentSelect.appendChild(opt);
      });
    }

    if (authRes.user.role === "student" && authRes.user.student_id) {
      state.currentStudentId = authRes.user.student_id;
      state.currentStudentProfile = authRes.user;
      if (studentSelect) studentSelect.value = authRes.user.student_id;
      navigateToPage("dashboard");
    } else if (authRes.user.role === "counselor") {
      navigateToPage("counselor");
    } else if (state.students.length > 0) {
      state.currentStudentId = state.students[0].student_id;
      state.currentStudentProfile = state.students[0];
      if (studentSelect) studentSelect.value = state.students[0].student_id;
      navigateToPage("dashboard");
    }
  });
}

function updateAuthUI() {
  const initialsEl = document.getElementById("nav-user-initials");
  const nameEl = document.getElementById("nav-user-name");
  const roleBadge = document.getElementById("nav-user-role-badge");
  const navCounselor = document.getElementById("nav-counselor-portal");
  const navStudent = document.getElementById("nav-student-dashboard");
  const navTrends = document.getElementById("nav-burnout-trends");
  const studentSelectorWrap = document.getElementById("student-selector-wrapper");
  const statusText = document.getElementById("nav-status-text");

  const isCounselor = state.authenticatedUser && state.authenticatedUser.role === "counselor";

  if (state.authenticatedUser) {
    const name = state.authenticatedUser.name || "User";
    const initials = name.split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();
    if (initialsEl) initialsEl.textContent = initials;
    if (nameEl) nameEl.textContent = name.split(" ")[0];
    if (roleBadge) {
      roleBadge.textContent = isCounselor ? "Counselor" : "Student";
      roleBadge.className = isCounselor 
        ? "px-1.5 py-0.5 rounded-full bg-secondary-fixed text-on-secondary-fixed text-[9px] font-bold uppercase"
        : "px-1.5 py-0.5 rounded-full bg-primary-fixed text-on-primary-fixed text-[9px] font-bold uppercase";
    }
  } else {
    if (initialsEl) initialsEl.textContent = "MP";
    if (nameEl) nameEl.textContent = "Guest";
    if (roleBadge) roleBadge.textContent = "Student";
  }

  // Strict Role Separation:
  if (isCounselor) {
    if (navCounselor) {
      navCounselor.classList.remove("hidden");
      navCounselor.textContent = "Counselor Surveillance";
    }
    if (navStudent) navStudent.textContent = "Student View (Audit)";
    if (navTrends) navTrends.classList.add("hidden");
    if (studentSelectorWrap) studentSelectorWrap.classList.remove("hidden");
    if (statusText) statusText.textContent = "Clinical Oversight";
  } else {
    // For Students: Counselor Surveillance is COMPLETELY HIDDEN!
    if (navCounselor) navCounselor.classList.add("hidden");
    if (navStudent) navStudent.textContent = "My Dashboard";
    if (navTrends) {
      navTrends.classList.remove("hidden");
      navTrends.textContent = "10-Factor AI Survey";
    }
    if (studentSelectorWrap) studentSelectorWrap.classList.add("hidden");
    if (statusText) statusText.textContent = "Balanced";
  }

  // Mobile Bottom Nav Role Customization:
  const mobPulseIcon = document.querySelector("#mob-nav-pulse span.material-symbols-outlined");
  const mobPulseText = document.querySelector("#mob-nav-pulse span.font-label-sm");
  const mobSurveyIcon = document.querySelector("#mob-nav-survey span.material-symbols-outlined");
  const mobSurveyText = document.querySelector("#mob-nav-survey span.font-label-sm");
  const mobSpikesIcon = document.querySelector("#mob-nav-spikes span.material-symbols-outlined");
  const mobSpikesText = document.querySelector("#mob-nav-spikes span.font-label-sm");

  if (isCounselor) {
    if (mobPulseIcon) mobPulseIcon.textContent = "crisis_alert";
    if (mobPulseText) mobPulseText.textContent = "Alerts";
    if (mobSurveyIcon) mobSurveyIcon.textContent = "badge";
    if (mobSurveyText) mobSurveyText.textContent = "Roster";
    if (mobSpikesIcon) mobSpikesIcon.textContent = "visibility";
    if (mobSpikesText) mobSpikesText.textContent = "Audit";
  } else {
    if (mobPulseIcon) mobPulseIcon.textContent = "self_improvement";
    if (mobPulseText) mobPulseText.textContent = "Pulse";
    if (mobSurveyIcon) mobSurveyIcon.textContent = "tune";
    if (mobSurveyText) mobSurveyText.textContent = "10-Factor";
    if (mobSpikesIcon) mobSpikesIcon.textContent = "event_upcoming";
    if (mobSpikesText) mobSpikesText.textContent = "Spikes";
  }
}

function handleLogout() {
  state.authenticatedUser = null;
  localStorage.removeItem("mindpulse_user_session");
  showLandingPage();
}

/**
 * Load Initial Demo Cohort Users
 */
async function loadInitialUsers() {
  try {
    const users = await API.getUsers();
    state.allUsers = users;
    const studentUsers = users.filter(u => u.role === "student");
    state.students = studentUsers;

    const studentSelect = document.getElementById("student-selector");
    if (studentSelect) {
      studentSelect.innerHTML = "";
      studentUsers.forEach(s => {
        const opt = document.createElement("option");
        opt.value = s.student_id;
        opt.textContent = `${s.name} (${s.student_id_number})`;
        studentSelect.appendChild(opt);
      });
    }

    updateAuthUI();
    if (state.authenticatedUser) {
      if (state.authenticatedUser.role === "counselor") {
        navigateToPage("counselor");
        return;
      } else if (state.authenticatedUser.student_id) {
        state.currentStudentId = state.authenticatedUser.student_id;
        state.currentStudentProfile = state.authenticatedUser;
        if (studentSelect) studentSelect.value = state.authenticatedUser.student_id;
        navigateToPage("dashboard");
        return;
      }
    } else if (studentUsers.length > 0) {
      state.currentStudentId = studentUsers[0].student_id;
      state.currentStudentProfile = studentUsers[0];
      if (studentSelect) studentSelect.value = studentUsers[0].student_id;
    }

    await loadStudentDashboard();
  } catch (err) {
    console.error("Failed to load demo accounts:", err);
  }
}

/**
 * Loads Student Dashboard Data (Stitch Telemetry Cards, Charts & Recommendations)
 */
async function loadStudentDashboard() {
  if (!state.currentStudentId) return;

  try {
    const history = await API.getSurveyHistory(state.currentStudentId);
    renderTrendChart("student-trend-chart", history);

    const latest = (history && history.length > 0) ? history[history.length - 1] : null;
    if (latest) {
      updateStitchTelemetryCards(latest);
    }
    renderRadarChart("student-radar-chart", latest);
  } catch (err) {
    console.error("Error loading student telemetry:", err);
  }
}

/**
 * Updates Top Hero & 4 Metric Cards matching Stitch Reference
 */
function updateStitchTelemetryCards(latest) {
  state.latestSurveyData = latest;
  const profile = state.currentStudentProfile;
  const name = profile ? profile.name.split(" ")[0] : "Student";
  const initials = profile ? profile.name.split(" ").map(n => n[0]).join("") : "MP";

  document.getElementById("hero-greeting-text").textContent = `Good afternoon, ${name}.`;
  document.getElementById("nav-user-initials").textContent = initials;

  const riskScore = latest.risk_score !== null ? latest.risk_score : 25.0;
  const riskLevel = latest.risk_level || "Low";

  // Cognitive battery = 100 - risk_score
  const batteryPct = Math.max(15, Math.min(95, Math.round(100 - riskScore)));
  const batteryBadge = document.getElementById("hero-battery-badge");
  const batteryText = document.getElementById("hero-battery-score");

  batteryText.textContent = `${batteryPct}% (${riskLevel === 'Low' ? 'Optimal Balance' : riskLevel === 'Moderate' ? 'Guarded Reserve' : 'Depleted State'})`;

  // Status Pill in header
  const statusDot = document.getElementById("nav-status-dot");
  const statusText = document.getElementById("nav-status-text");
  statusText.textContent = riskLevel === "Low" ? "Balanced" : riskLevel === "Moderate" ? "Watchlist" : "High Risk";
  
  if (riskLevel === "High") {
    statusDot.className = "w-2 h-2 rounded-full bg-error animate-ping";
    statusText.className = "font-label-sm text-label-sm text-error font-semibold";
  } else if (riskLevel === "Moderate") {
    statusDot.className = "w-2 h-2 rounded-full bg-tertiary animate-pulse";
    statusText.className = "font-label-sm text-label-sm text-tertiary font-semibold";
  } else {
    statusDot.className = "w-2 h-2 rounded-full bg-primary animate-pulse";
    statusText.className = "font-label-sm text-label-sm text-primary font-semibold";
  }

  // Metric Card 1: Burnout Risk
  document.getElementById("metric-risk-val").textContent = riskScore.toFixed(0);
  const riskBadge = document.getElementById("metric-risk-badge");
  riskBadge.textContent = `${riskLevel} Risk`;
  riskBadge.className = `px-space-xs py-0.5 rounded-full font-caption text-caption font-semibold ${riskLevel === 'High' ? 'badge-high alert-pulse-high' : riskLevel === 'Moderate' ? 'badge-moderate' : 'badge-low'}`;
  document.getElementById("metric-risk-gauge").style.width = `${Math.min(100, Math.max(10, riskScore))}%`;

  // Metric Card 2: Study Load
  const studyDaily = latest.study_hours_per_day || 5.0;
  const weeklyStudyEst = Math.round(studyDaily * 5);
  document.getElementById("metric-study-hours").textContent = weeklyStudyEst;
  const studyCapPct = Math.min(100, Math.round((weeklyStudyEst / 35) * 100));
  document.getElementById("metric-study-gauge").style.width = `${studyCapPct}%`;

  // Metric Card 3: Sleep & Recovery
  const sleepHours = latest.sleep_hours_per_night || 7.5;
  document.getElementById("metric-sleep-hours").textContent = sleepHours.toFixed(1);
  const sleepBadge = document.getElementById("metric-sleep-badge");
  if (sleepHours >= 7.5) {
    sleepBadge.textContent = "Optimal";
    sleepBadge.className = "px-space-xs py-0.5 rounded-full bg-primary-fixed/70 text-on-primary-fixed font-caption text-caption font-semibold";
  } else if (sleepHours >= 6.0) {
    sleepBadge.textContent = "Moderate";
    sleepBadge.className = "px-space-xs py-0.5 rounded-full bg-tertiary-fixed text-on-tertiary-fixed font-caption text-caption font-semibold";
  } else {
    sleepBadge.textContent = "Deficit";
    sleepBadge.className = "px-space-xs py-0.5 rounded-full bg-error-container text-on-error-container font-caption text-caption font-semibold";
  }
  document.getElementById("metric-sleep-gauge").style.width = `${Math.min(100, Math.round((sleepHours / 9) * 100))}%`;

  // Metric Card 4: Mood & Clarity
  const stress = latest.self_reported_stress || 4;
  const moodText = document.getElementById("metric-mood-text");
  if (stress >= 8) {
    moodText.textContent = "Cognitive Strain";
  } else if (stress >= 6) {
    moodText.textContent = "Active Focus";
  } else {
    moodText.textContent = "Calm & Grounded";
  }
}

/**
 * Reads Survey Form Values
 */
function getSurveyFormData() {
  return {
    gpa: parseFloat(document.getElementById("input-gpa").value),
    study_hours_per_day: parseFloat(document.getElementById("input-study-hours").value),
    academic_workload: parseInt(document.getElementById("input-workload").value, 10),
    exam_pressure: parseInt(document.getElementById("input-exam-pressure").value, 10),
    attendance_percentage: parseFloat(document.getElementById("input-attendance").value),
    sleep_hours_per_night: parseFloat(document.getElementById("input-sleep-hours").value),
    sleep_quality: parseInt(document.getElementById("input-sleep-quality").value, 10),
    screen_time_hours: parseFloat(document.getElementById("input-screen-time").value),
    exercise_days: parseInt(document.getElementById("input-exercise").value, 10),
    social_support: parseInt(document.getElementById("input-social").value, 10),
    mood_energy: parseInt(document.getElementById("input-mood").value, 10),
    self_reported_stress: parseInt(document.getElementById("input-stress").value, 10),
    feeling_overwhelmed: parseInt(document.getElementById("input-overwhelmed").value, 10),
    notes: document.getElementById("input-notes")?.value || ""
  };
}

/**
 * Instant Simulator Preview (What-If sensitivity exploration)
 */
async function handleInstantPreview() {
  const data = getSurveyFormData();
  try {
    const result = await API.evaluateRiskPreview(data);
    displayAssessmentModal(result, true);
  } catch (err) {
    alert("Simulation failed: " + err.message);
  }
}

/**
 * Handles Form Submission -> Commits to DB, updates alerts & trend charts
 */
async function handleSurveySubmit(e) {
  e.preventDefault();
  if (!state.currentStudentId) {
    alert("Please select a student profile.");
    return;
  }

  const submitBtn = document.getElementById("btn-submit-survey");
  submitBtn.disabled = true;
  submitBtn.innerHTML = `
    <span class="material-symbols-outlined text-lg animate-spin">refresh</span>
    <span>Analyzing Telemetry...</span>`;

  try {
    const data = getSurveyFormData();
    const result = await API.submitSurvey(state.currentStudentId, data);
    displayAssessmentModal(result, false);
    await loadStudentDashboard();
  } catch (err) {
    alert("Submission error: " + err.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = `
      <span class="material-symbols-outlined text-lg">model_training</span>
      <span>Submit Telemetry & Execute AI Risk Prediction</span>`;
  }
}

/**
 * Displays Assessment Modal with Circular Gauge, Risk Drivers, and Recommendations
 */
function displayAssessmentModal(assessment, isPreview = false) {
  state.lastAssessmentResult = assessment;
  const modal = document.getElementById("assessment-modal");
  const title = document.getElementById("modal-risk-title");
  const score = document.getElementById("modal-risk-score");
  const badge = document.getElementById("modal-risk-badge");
  const driversList = document.getElementById("modal-drivers-list");
  const protectiveList = document.getElementById("modal-protective-list");
  const recsContainer = document.getElementById("modal-recs-container");
  const meterArc = document.getElementById("modal-meter-arc");
  const previewBanner = document.getElementById("modal-preview-banner");

  previewBanner.classList.toggle("hidden", !isPreview);

  title.textContent = `${assessment.risk_level} Risk Level Detected`;
  score.textContent = `${assessment.risk_score.toFixed(0)}%`;
  badge.textContent = assessment.risk_level;

  badge.className = "px-3 py-1 text-xs font-semibold rounded-full uppercase tracking-wider ";
  let strokeColor = "#355f4d";

  if (assessment.risk_level === "High") {
    badge.classList.add("badge-high", "alert-pulse-high");
    strokeColor = "#ba1a1a";
  } else if (assessment.risk_level === "Moderate") {
    badge.classList.add("badge-moderate");
    strokeColor = "#734f2d";
  } else {
    badge.classList.add("badge-low");
    strokeColor = "#355f4d";
  }

  meterArc.style.stroke = strokeColor;
  const offset = 283 - (assessment.risk_score / 100) * 283;
  meterArc.style.strokeDashoffset = Math.max(0, offset);

  // Contributing Drivers
  driversList.innerHTML = "";
  assessment.primary_drivers.forEach(d => {
    const li = document.createElement("li");
    li.className = "flex items-start text-xs text-on-surface-variant gap-2";
    li.innerHTML = `
      <span class="text-error font-bold">•</span>
      <span>${d}</span>
    `;
    driversList.appendChild(li);
  });

  // Protective Buffers
  protectiveList.innerHTML = "";
  assessment.protective_factors.forEach(p => {
    const li = document.createElement("li");
    li.className = "flex items-start text-xs text-on-surface-variant gap-2";
    li.innerHTML = `
      <span class="text-primary font-bold">✓</span>
      <span>${p}</span>
    `;
    protectiveList.appendChild(li);
  });

  // Recommendations
  recsContainer.innerHTML = "";
  assessment.recommendations.forEach(r => {
    const card = document.createElement("div");
    card.className = "p-4 rounded-lg bg-surface-container border border-outline-variant/30 space-y-1.5";
    
    let priorityBadge = `<span class="text-xs px-2.5 py-0.5 rounded-full font-medium bg-surface-container-high text-on-surface-variant">${r.category}</span>`;
    if (r.priority === "High") {
      priorityBadge = `<span class="text-xs px-2.5 py-0.5 rounded-full font-semibold bg-error-container text-on-error-container">High Priority</span>`;
    }

    const stepsHtml = r.action_steps.map(s => `<li class="text-xs text-on-surface-variant">• ${s}</li>`).join("");

    card.innerHTML = `
      <div class="flex items-center justify-between">
        <h4 class="font-headline-sm font-semibold text-on-surface text-xs">${r.title}</h4>
        ${priorityBadge}
      </div>
      <ul class="space-y-1 mt-1">
        ${stepsHtml}
      </ul>
    `;
    recsContainer.appendChild(card);
  });

  modal.classList.remove("hidden");
}

/**
 * Loads Counselor Surveillance & Cohort Analytics
 */
async function loadCounselorSurveillance() {
  try {
    const summary = await API.getCohortSummary();
    updateCounselorKPIs(summary);
    renderCohortChart("cohort-doughnut-chart", summary);

    await refreshAlerts("ALL");
    await refreshStudentsRoster();
  } catch (err) {
    console.error("Error loading counselor surveillance:", err);
  }
}
const loadCounselorDashboard = loadCounselorSurveillance;

function updateCounselorKPIs(summary) {
  document.getElementById("kpi-total-students").textContent = summary.total_students || 0;
  document.getElementById("kpi-high-risk").textContent = summary.high_risk_count || 0;
  document.getElementById("kpi-active-alerts").textContent = summary.active_alerts || 0;
  document.getElementById("kpi-avg-stress").textContent = `${summary.average_stress || 5.0}/10`;
  document.getElementById("kpi-avg-sleep").textContent = `${summary.average_sleep || 6.5}h`;
}

/**
 * Loads High-Risk Alerts Queue
 */
async function refreshAlerts(status = "ALL") {
  const container = document.getElementById("alerts-table-body");
  container.innerHTML = `<tr><td colspan="6" class="text-center py-6 text-on-surface-variant">Loading alert queue...</td></tr>`;

  try {
    const alerts = await API.getAlerts(status);
    if (alerts.length === 0) {
      container.innerHTML = `<tr><td colspan="6" class="text-center py-6 text-on-surface-variant italic">No alerts found under "${status}".</td></tr>`;
      return;
    }

    container.innerHTML = "";
    alerts.forEach(a => {
      const tr = document.createElement("tr");
      tr.className = "border-b border-outline-variant/20 hover:bg-surface-container-high/40 transition";

      let statusBadge = "";
      if (a.status === "NEW") {
        statusBadge = `<span class="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-error-container text-on-error-container">NEW</span>`;
      } else if (a.status === "IN_REVIEW") {
        statusBadge = `<span class="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-tertiary-fixed text-on-tertiary-fixed">IN REVIEW</span>`;
      } else if (a.status === "CONTACTED") {
        statusBadge = `<span class="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-secondary-fixed text-on-secondary-fixed">CONTACTED</span>`;
      } else {
        statusBadge = `<span class="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-primary-fixed text-on-primary-fixed">RESOLVED</span>`;
      }

      const dateStr = new Date(a.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });

      tr.innerHTML = `
        <td class="py-3 px-3 font-semibold text-on-surface">${a.student_name} <br><span class="text-xs text-on-surface-variant font-normal">${a.student_id_number}</span></td>
        <td class="py-3 px-3"><span class="font-bold text-error">${a.risk_score.toFixed(0)}%</span></td>
        <td class="py-3 px-3">${statusBadge}</td>
        <td class="py-3 px-3 text-xs text-on-surface-variant max-w-[200px] truncate">${a.alert_reason || 'Severe burnout metrics'}</td>
        <td class="py-3 px-3 text-xs text-on-surface-variant">${dateStr}</td>
        <td class="py-3 px-3 text-right">
          <button class="btn-manage-alert px-3 py-1 text-xs font-medium bg-surface-container-high hover:bg-surface-container-highest rounded-full text-on-surface transition" data-alert-id="${a.id}">Triage (${a.notes_count})</button>
        </td>
      `;
      container.appendChild(tr);
    });

    document.querySelectorAll(".btn-manage-alert").forEach(btn => {
      btn.addEventListener("click", () => {
        const alertId = parseInt(btn.dataset.alertId, 10);
        const alertObj = alerts.find(x => x.id === alertId);
        openManageAlertModal(alertObj);
      });
    });
  } catch (err) {
    container.innerHTML = `<tr><td colspan="6" class="text-center py-6 text-error">Failed to load alerts: ${err.message}</td></tr>`;
  }
}

/**
 * Loads Student Directory Roster
 */
async function refreshStudentsRoster() {
  const container = document.getElementById("roster-table-body");
  const filter = document.getElementById("risk-filter-select")?.value || "ALL";
  const search = document.getElementById("student-search")?.value || "";

  try {
    const roster = await API.getStudentsRoster(filter, search);
    if (roster.length === 0) {
      container.innerHTML = `<tr><td colspan="6" class="text-center py-6 text-on-surface-variant">No matching student records found.</td></tr>`;
      return;
    }

    container.innerHTML = "";
    roster.forEach(s => {
      const tr = document.createElement("tr");
      tr.className = "border-b border-outline-variant/20 hover:bg-surface-container-high/40 cursor-pointer transition";
      
      let badge = `<span class="px-2.5 py-0.5 text-xs font-semibold rounded-full badge-low">Balanced</span>`;
      if (s.latest_risk_level === "High") {
        badge = `<span class="px-2.5 py-0.5 text-xs font-semibold rounded-full badge-high">Triage (${s.latest_risk_score.toFixed(0)}%)</span>`;
      } else if (s.latest_risk_level === "Moderate") {
        badge = `<span class="px-2.5 py-0.5 text-xs font-semibold rounded-full badge-moderate">Watch (${s.latest_risk_score.toFixed(0)}%)</span>`;
      }

      tr.innerHTML = `
        <td class="py-3 px-3 font-semibold text-on-surface">${s.name} <br><span class="text-xs text-on-surface-variant font-normal">${s.student_id_number}</span></td>
        <td class="py-3 px-3 text-xs text-on-surface-variant">${s.department} (Yr ${s.year_of_study})</td>
        <td class="py-3 px-3">${badge}</td>
        <td class="py-3 px-3 text-xs text-on-surface-variant">${s.sleep_hours ? s.sleep_hours + 'h' : 'N/A'}</td>
        <td class="py-3 px-3 text-xs text-on-surface-variant">${s.stress_level ? s.stress_level + '/10' : 'N/A'}</td>
        <td class="py-3 px-3 text-xs text-on-surface-variant">${s.last_check_in}</td>
      `;

      tr.addEventListener("click", () => openStudentDrillDown(s.id));
      container.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load student roster:", err);
  }
}

/**
 * Manage Alert Modal (Triage & Case Notes)
 */
function openManageAlertModal(alertObj) {
  if (!alertObj) return;
  const modal = document.getElementById("manage-alert-modal");
  document.getElementById("modal-alert-student").textContent = `${alertObj.student_name} (${alertObj.student_id_number})`;
  document.getElementById("modal-alert-score").textContent = `${alertObj.risk_score.toFixed(0)}% (${alertObj.risk_level} Risk)`;
  document.getElementById("modal-alert-status-select").value = alertObj.status;

  const notesList = document.getElementById("modal-alert-notes-list");
  notesList.innerHTML = "";
  if (alertObj.recent_notes && alertObj.recent_notes.length > 0) {
    alertObj.recent_notes.forEach(n => {
      const div = document.createElement("div");
      div.className = "p-3 bg-surface-container-lowest rounded-lg text-xs space-y-1 border border-outline-variant/30";
      div.innerHTML = `
        <div class="flex justify-between font-semibold text-on-surface">
          <span>${n.counselor_name}</span>
          <span class="text-on-surface-variant">${new Date(n.created_at).toLocaleDateString()}</span>
        </div>
        <p class="text-on-surface-variant">${n.note_content}</p>
        <span class="inline-block px-2 py-0.5 bg-surface-container rounded text-on-surface-variant font-mono text-[10px]">${n.action_taken}</span>
      `;
      notesList.appendChild(div);
    });
  } else {
    notesList.innerHTML = `<p class="text-xs text-on-surface-variant italic">No clinical notes recorded yet.</p>`;
  }

  const saveBtn = document.getElementById("btn-save-alert-update");
  saveBtn.onclick = async () => {
    const newStatus = document.getElementById("modal-alert-status-select").value;
    const newNote = document.getElementById("modal-alert-new-note").value;
    const newAction = document.getElementById("modal-alert-action-taken").value;

    try {
      await API.updateAlertStatus(alertObj.id, {
        status: newStatus,
        counselor_name: "Dr. Sarah Jenkins - Campus Psychologist",
        note_content: newNote,
        action_taken: newAction
      });
      document.getElementById("modal-alert-new-note").value = "";
      modal.classList.add("hidden");
      await loadCounselorSurveillance();
    } catch (e) {
      alert("Error updating alert: " + e.message);
    }
  };

  modal.classList.remove("hidden");
}

/**
 * Student Profile Drilldown Modal
 */
async function openStudentDrillDown(studentId) {
  const modal = document.getElementById("student-drilldown-modal");
  try {
    const detail = await API.getStudentDetail(studentId);
    document.getElementById("drilldown-name").textContent = detail.name;
    document.getElementById("drilldown-meta").textContent = `${detail.student_id_number} • ${detail.department} • Year ${detail.year_of_study}`;

    const scoreElem = document.getElementById("drilldown-risk-score");
    const levelElem = document.getElementById("drilldown-risk-level");
    if (detail.latest_assessment) {
      scoreElem.textContent = `${detail.latest_assessment.risk_score.toFixed(0)}%`;
      levelElem.textContent = detail.latest_assessment.risk_level;
      levelElem.className = `font-bold ${detail.latest_assessment.risk_level === 'High' ? 'text-error' : detail.latest_assessment.risk_level === 'Moderate' ? 'text-tertiary' : 'text-primary'}`;
    } else {
      scoreElem.textContent = "N/A";
      levelElem.textContent = "Unassessed";
    }

    renderTrendChart("drilldown-trend-chart", detail.history);
    modal.classList.remove("hidden");
  } catch (err) {
    alert("Could not load student profile: " + err.message);
  }
}

/**
 * Benchmark Modal (Algorithm Comparison & Explainable AI)
 */
async function openBenchmarkModal() {
  const modal = document.getElementById("benchmark-modal");
  const tbody = document.getElementById("benchmark-table-body");
  tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-on-surface-variant">Loading benchmark metrics...</td></tr>`;
  modal.classList.remove("hidden");

  try {
    if (!state.cachedBenchmark) {
      state.cachedBenchmark = await API.getModelInfo();
    }
    const data = state.cachedBenchmark;
    renderBenchmarkChart("benchmark-bar-chart", data);

    tbody.innerHTML = "";
    Object.entries(data.models_benchmark).forEach(([name, metrics]) => {
      const tr = document.createElement("tr");
      tr.className = "border-b border-outline-variant/20 text-xs";
      const isChamp = (name === data.best_model);

      tr.innerHTML = `
        <td class="py-2.5 px-4 font-semibold text-on-surface">${name} ${isChamp ? '<span class="text-[10px] ml-1.5 bg-primary-fixed text-on-primary-fixed px-2 py-0.5 rounded-full font-bold">Champion</span>' : ''}</td>
        <td class="py-2.5 px-4 font-mono font-medium">${(metrics.accuracy * 100).toFixed(2)}%</td>
        <td class="py-2.5 px-4 font-mono font-medium">${(metrics.f1_weighted * 100).toFixed(2)}%</td>
        <td class="py-2.5 px-4 font-mono">${(metrics.precision_macro * 100).toFixed(2)}%</td>
        <td class="py-2.5 px-4 font-mono">${(metrics.recall_macro * 100).toFixed(2)}%</td>
      `;
      tbody.appendChild(tr);
    });

    const champ = data.models_benchmark[data.best_model];
    if (champ && champ.feature_importances) {
      const featBox = document.getElementById("benchmark-features-container");
      featBox.innerHTML = "";
      Object.entries(champ.feature_importances).slice(0, 7).forEach(([f, imp]) => {
        const item = document.createElement("div");
        item.className = "flex justify-between items-center text-xs py-1 border-b border-outline-variant/20";
        item.innerHTML = `
          <span class="text-on-surface-variant">${f.replace(/_/g, " ")}</span>
          <span class="font-mono font-semibold text-primary">${(imp * 100).toFixed(1)}% influence</span>
        `;
        featBox.appendChild(item);
      });
    }
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-error">Benchmark error: ${err.message}</td></tr>`;
  }
}

/**
 * 24/7 Crisis Helplines Modal
 */
function openCrisisModal() {
  document.getElementById("crisis-modal").classList.remove("hidden");
}

function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

/**
 * =========================================================================
 * Progressive Web App (PWA) & Report Download Management
 * =========================================================================
 */
let deferredInstallPrompt = null;

function initPWA() {
  // 1. Register Service Worker
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker
        .register("/sw.js", { scope: "/" })
        .then((reg) => {
          console.log("[PWA] Service Worker registered with root scope:", reg.scope);
        })
        .catch((err) => {
          console.warn("[PWA] Service Worker registration failed:", err);
        });
    });
  }

  // 2. Capture 'beforeinstallprompt' Event
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredInstallPrompt = e;
    console.log("[PWA] beforeinstallprompt captured.");
    
    // Highlight install buttons
    document.querySelectorAll(".btn-install-pwa").forEach((btn) => {
      btn.classList.add("ring-2", "ring-primary-fixed");
    });
  });

  // 3. Listen for 'appinstalled' Event
  window.addEventListener("appinstalled", () => {
    console.log("[PWA] MindPulse AI installed successfully.");
    deferredInstallPrompt = null;
    showToast("MindPulse AI App installed successfully! Ready for offline use.");
    
    document.querySelectorAll(".btn-install-pwa").forEach((btn) => {
      btn.innerHTML = `<span class="material-symbols-outlined text-base text-primary">check_circle</span><span>App Installed</span>`;
      btn.classList.remove("ring-2", "ring-primary-fixed");
    });
  });

  // 4. Bind Install Buttons
  document.querySelectorAll(".btn-install-pwa").forEach((btn) => {
    btn.addEventListener("click", handlePWAInstallClick);
  });

  const modalInstallBtn = document.getElementById("pwa-modal-install-btn");
  if (modalInstallBtn) {
    modalInstallBtn.addEventListener("click", () => {
      const modal = document.getElementById("pwa-install-modal");
      if (modal) modal.classList.add("hidden");
      triggerNativeInstall();
    });
  }

  // Detect standalone mode
  const isStandalone = window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
  if (isStandalone) {
    document.querySelectorAll(".btn-install-pwa").forEach((btn) => {
      btn.innerHTML = `<span class="material-symbols-outlined text-base">verified</span><span>Installed</span>`;
      btn.title = "Running as installed PWA";
    });
  }
}

function handlePWAInstallClick() {
  if (deferredInstallPrompt) {
    triggerNativeInstall();
  } else {
    openInstallModal();
  }
}

function triggerNativeInstall() {
  if (deferredInstallPrompt) {
    deferredInstallPrompt.prompt();
    deferredInstallPrompt.userChoice.then((choiceResult) => {
      if (choiceResult.outcome === "accepted") {
        console.log("[PWA] User accepted installation prompt");
      } else {
        console.log("[PWA] User dismissed installation prompt");
      }
      deferredInstallPrompt = null;
    });
  } else {
    openInstallModal();
  }
}

function openInstallModal() {
  const modal = document.getElementById("pwa-install-modal");
  if (modal) modal.classList.remove("hidden");
}

/**
 * Download Student Burnout & Well-being Assessment Report
 * Generates an institutional health record JSON download and triggers print/PDF preview.
 */
function handleDownloadStudentReport() {
  const profile = state.currentStudentProfile;
  const assessment = state.lastAssessmentResult;
  const latestSurvey = state.latestSurveyData;

  const studentName = profile ? profile.name : "Student";
  const studentId = profile ? profile.student_id : (state.currentStudentId || 101);
  const department = profile ? profile.department : "Computer Science";
  const semester = profile ? profile.semester : 4;
  
  const riskLevel = assessment?.risk_level || latestSurvey?.risk_level || "Low";
  const riskScore = assessment?.risk_score !== undefined ? assessment.risk_score : (latestSurvey?.risk_score || 22.0);
  const batteryPct = Math.max(15, Math.min(95, Math.round(100 - riskScore)));

  const drivers = assessment?.contributing_risk_drivers || [
    "High Perceived Academic Stress",
    "Restricted Sleep Quality Duration",
    "Screen Over-exposure Before Sleep"
  ];

  const protective = assessment?.protective_factors || [
    "Consistent Academic Attendance",
    "Active Peer & Social Support Network",
    "Regular Physical Movement"
  ];

  const recommendations = assessment?.personalized_recommendations || [
    { title: "Sleep Hygiene Optimization", rationale: "Target 7.5 - 8.5 hours with consistent wind-down routine.", category: "Lifestyle" },
    { title: "Pomodoro Workload Pacing", rationale: "Structured 25-minute study intervals with 5-minute active recovery breaks.", category: "Academic" },
    { title: "Digital Evening Sanctuary", rationale: "Disable high-stimulation displays 45 minutes prior to sleep.", category: "Digital" }
  ];

  const timestamp = new Date().toISOString();
  const dateFormatted = new Date().toLocaleString();

  const reportPayload = {
    institution: "MindPulse AI — Campus Health Surveillance System",
    documentTitle: "Student Burnout & Mental Health Early Warning Report",
    generatedAt: timestamp,
    generatedDateString: dateFormatted,
    studentProfile: {
      studentId: studentId,
      name: studentName,
      department: department,
      semester: semester,
      academicStatus: "Active Monitored Cohort"
    },
    riskAssessment: {
      riskLevel: riskLevel,
      riskScorePercent: Number(riskScore.toFixed(1)),
      cognitiveReserveBatteryPercent: batteryPct,
      classificationTiers: {
        low: "0 - 35% (Optimal Balance)",
        moderate: "36 - 65% (Early Warning Alert)",
        high: "66 - 100% (Urgent Counselor Triage)"
      }
    },
    explainableAIFactors: {
      primaryRiskDrivers: drivers,
      positiveProtectiveBuffers: protective
    },
    actionablePrescriptions: recommendations,
    ethicalDisclaimer: "Ethical Safeguard Notice: MindPulse AI operates strictly as an educational risk-screening and early-warning decision tool. It does not provide psychiatric diagnoses. High-risk indicators prompt human counselor triage.",
    crisisHelplines: {
      suicideAndCrisisLifeline: "988 (Call or Text 24/7)",
      crisisTextLine: "Text HOME to 741741",
      teleMANAS: "14416 / 1800 891 4416"
    }
  };

  // 1. Generate downloadable JSON report
  const blob = new Blob([JSON.stringify(reportPayload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  const safeName = studentName.toLowerCase().replace(/[^a-z0-9]/g, "_");
  const dateStr = timestamp.slice(0, 10);
  a.download = `mindpulse-burnout-report-${safeName}-${dateStr}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  showToast(`Assessment Report downloaded for ${studentName}! Opening PDF print view...`);

  // 2. Open print preview after short delay so download completes cleanly
  setTimeout(() => {
    window.print();
  }, 400);
}

/**
 * Toast Notification Helper
 */
function showToast(message) {
  let toast = document.getElementById("mindpulse-toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "mindpulse-toast";
    toast.className = "fixed bottom-6 right-6 z-50 px-5 py-3 rounded-full bg-primary text-on-primary text-xs font-semibold shadow-2xl flex items-center gap-2 transform transition-all duration-300 translate-y-20 opacity-0 no-print";
    document.body.appendChild(toast);
  }
  toast.innerHTML = `<span class="material-symbols-outlined text-base">check_circle</span><span>${message}</span>`;
  toast.classList.remove("translate-y-20", "opacity-0");
  setTimeout(() => {
    toast.classList.add("translate-y-20", "opacity-0");
  }, 4000);
}
