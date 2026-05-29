(function () {
  // =============================================
  // SVG Icons (Lucide-style, 16×16 stroke icons)
  // =============================================
  const ICONS = {
    folder: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>`,
    folderOpen: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2"/></svg>`,
    chevronDown: `<svg class="chevron" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>`,
    home: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`,
    folderPlus: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/><line x1="12" y1="11" x2="12" y2="17"/><line x1="9" y1="14" x2="15" y2="14"/></svg>`,
    x: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`,
    check: `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`,
    layers: `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>`,
    trash: `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>`,
  };

  // =============================================
  // Cookie helpers
  // =============================================
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return null;
  }
  function setCookie(name, value) {
    document.cookie = `${name}=${encodeURIComponent(value)}; path=/; max-age=31536000`;
  }
  function clearCookie(name) {
    document.cookie = `${name}=; path=/; max-age=0`;
  }

  // =============================================
  // State
  // =============================================
  const activeProject = getCookie("active_project")
    ? decodeURIComponent(getCookie("active_project"))
    : null;
  const activeProjectId = getCookie("active_project_id")
    ? decodeURIComponent(getCookie("active_project_id"))
    : null;

  let btn = null;

  // =============================================
  // API: Delete Project
  // =============================================
  async function deleteProject(id) {
    try {
      const url = `/api/projects/delete-project?project_id=${encodeURIComponent(id)}`;
      const response = await fetch(url, { method: "DELETE" });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Failed to delete project");
      }
      return await response.json();
    } catch (error) {
      console.error("Error deleting project:", error);
      return false;
    }
  }

  // =============================================
  // Sidebar detection — works with Chainlit's Shadcn UI
  // =============================================

  /**
   * Find the sidebar element using multiple strategies.
   * Chainlit uses Shadcn/Tailwind and the sidebar may not be a plain <aside>.
   */
  function findSidebarElement() {
    // Strategy 1: Shadcn data-sidebar attribute (most reliable for modern Chainlit)
    let el =
      document.querySelector('[data-sidebar="sidebar"]') ||
      document.querySelector("[data-sidebar]");
    if (el && isSidebarLike(el)) return el;

    // Strategy 2: Standard <aside> element
    el = document.querySelector("aside");
    if (el && isSidebarLike(el)) return el;

    // Strategy 3: Class-based selectors (sidebar, drawer)
    const classSelectors = [
      '[class*="Sidebar"]',
      '[class*="sidebar"]',
      '[class*="Drawer"]',
      '[class*="drawer"]',
      "nav[class]",
    ];
    for (const sel of classSelectors) {
      const candidates = document.querySelectorAll(sel);
      for (const c of candidates) {
        if (isSidebarLike(c)) return c;
      }
    }

    // Strategy 4: Heuristic scan — find the first tall, narrow, left-anchored panel
    // Look in #root or #app first, then body
    const root =
      document.getElementById("root") ||
      document.getElementById("app") ||
      document.body;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, {
      acceptNode: (node) => {
        // Skip our own elements
        if (node.id && node.id.startsWith("project-"))
          return NodeFilter.FILTER_REJECT;
        // Skip tiny elements or deeply nested ones
        if (node.children.length === 0) return NodeFilter.FILTER_SKIP;
        return NodeFilter.FILTER_ACCEPT;
      },
    });
    let best = null;
    let bestWidth = 0;
    let node;
    while ((node = walker.nextNode())) {
      if (isSidebarLike(node)) {
        const w = node.getBoundingClientRect().width;
        if (w > bestWidth) {
          best = node;
          bestWidth = w;
        }
        // Don't go deeper into this node
        walker.currentNode = node;
      }
    }
    if (best) return best;

    return null;
  }

  /**
   * Check if an element visually looks like a sidebar:
   * - Positioned near the left edge (left < 20px)
   * - Narrow-ish (width between 100–500px)
   * - Tall (height > 60% of viewport)
   */
  function isSidebarLike(el) {
    const r = el.getBoundingClientRect();
    const style = window.getComputedStyle(el);
    if (style.display === "none" || style.visibility === "hidden") return false;
    return (
      r.left < 20 &&
      r.width >= 100 &&
      r.width <= 500 &&
      r.height > window.innerHeight * 0.5
    );
  }

  // =============================================
  // Position tracking — follow sidebar's right edge
  // =============================================
  let lastLeft = -1;
  let cachedSidebar = null;
  let cacheTime = 0;

  function trackPosition() {
    if (!btn) return;

    const GAP = 16;
    const now = Date.now();

    // Re-scan for sidebar element every 500ms (not every frame — perf)
    if (!cachedSidebar || now - cacheTime > 500) {
      cachedSidebar = findSidebarElement();
      cacheTime = now;
    }

    let targetLeft = GAP; // default if no sidebar found

    if (cachedSidebar) {
      const rect = cachedSidebar.getBoundingClientRect();
      if (rect.width > 0) {
        targetLeft = Math.round(rect.right) + GAP;
      }
    }

    // Clamp so button never goes off-screen left
    targetLeft = Math.max(GAP, targetLeft);

    // Only update DOM if value actually changed
    if (targetLeft !== lastLeft) {
      btn.style.left = targetLeft + "px";
      lastLeft = targetLeft;
    }

    requestAnimationFrame(trackPosition);
  }

  // =============================================
  // Create Button (instant, fixed position)
  // =============================================
  function createButton() {
    if (document.getElementById("project-dropdown-btn")) return;

    btn = document.createElement("button");
    btn.id = "project-dropdown-btn";
    btn.title = activeProject || "All Chats";
    btn.innerHTML = activeProject
      ? `${ICONS.folderOpen}<span>${activeProject}</span>${ICONS.chevronDown}`
      : `${ICONS.layers}<span>All Chats</span>${ICONS.chevronDown}`;
    btn.addEventListener("click", () => openModal());

    document.body.appendChild(btn);

    // Start tracking sidebar position
    lastLeft = -1;
    requestAnimationFrame(trackPosition);
  }

  // =============================================
  // Modal
  // =============================================
  // --- Fetch projects list from backend ---
  async function listProjects() {
    try {
      const response = await fetch(`/api/projects/projects-list`);
      if (!response.ok) throw new Error("Error fetching projects");
      return await response.json();
    } catch (error) {
      console.error("Error fetching projects", error);
      return [];
    }
  }

  // ==============================================================
  // PATH VALIDATION
  // ==============================================================
  async function validatePath(path) {
    try {
      const url = `/api/projects/validate-path?path=${encodeURIComponent(path)}`;
      const response = await fetch(url);
      if (!response.ok) throw new Error("Network response was not ok");
      const result = await response.json();
      return result.exists;
    } catch (error) {
      console.error("Error validating path:", error);
      return false;
    }
  }

  // ==============================================================
  // Render the list view into #project-modal
  // ==============================================================
  async function showListView() {
    const modal = document.getElementById("project-modal");
    if (!modal) return;

    modal.innerHTML = `
      <div class="pm-header">
        <h2>Projects</h2>
        <button class="pm-close-btn" id="pm-close">${ICONS.x}</button>
      </div>

      <button class="pm-action-btn" id="pm-btn-all-chats">
        ${ICONS.home}
        All Chats
        ${activeProjectId ? "" : `<span style="margin-left:auto">${ICONS.check}</span>`}
      </button>

      <button class="pm-action-btn" id="pm-btn-new">
        ${ICONS.folderPlus}
        New Project
      </button>

      <div class="pm-section-label">Workspaces</div>
      <div id="pm-project-list">
        <div style="padding:10px;text-align:center;font-size:13px;opacity:0.4;">Loading...</div>
      </div>
    `;

    document.getElementById("pm-close").addEventListener("click", closeModal);

    document.getElementById("pm-btn-all-chats").addEventListener("click", () => {
      clearCookie("active_project");
      clearCookie("active_project_id");
      window.location.href = "/";
    });

    document.getElementById("pm-btn-new").addEventListener("click", () => showNewProjectForm());

    // Fetch and render projects
    const projects_list = await listProjects();
    renderProjects(projects_list);
  }

  // ==============================================================
  // Render the New Project form into #project-modal
  // ==============================================================
  function showNewProjectForm() {
    const modal = document.getElementById("project-modal");
    if (!modal) return;

    modal.innerHTML = `
      <div class="pm-header">
        <h2>New Project</h2>
        <button class="pm-close-btn" id="pm-close-form">${ICONS.x}</button>
      </div>
      <form id="pm-new-form">
        <div class="pm-form-group">
          <label>Name</label>
          <input type="text" id="pm-input-name" class="pm-input" required placeholder="My Awesome Project" />
        </div>
        <div class="pm-form-group">
          <label>Description</label>
          <input type="text" id="pm-input-desc" class="pm-input" required placeholder="A brief description" data-auto="true" />
        </div>
        <div class="pm-form-group">
          <label>Absolute Path</label>
          <input type="text" id="pm-input-path" class="pm-input" required placeholder="C:/projects/my-awesome-project" />
          <div id="pm-path-error" class="pm-error-msg">Path does not exist on this machine.</div>
        </div>
        <div class="pm-form-group">
          <label>Instructions (Optional)</label>
          <textarea id="pm-input-inst" class="pm-input" placeholder="Specific instructions for the agent..."></textarea>
        </div>
        <div class="pm-form-actions">
          <button type="button" class="pm-btn-secondary" id="pm-btn-cancel">Cancel</button>
          <button type="submit" class="pm-btn-primary">Create Project</button>
        </div>
      </form>
    `;

    // X button → close entire modal
    document.getElementById("pm-close-form").addEventListener("click", closeModal);

    // Cancel → go back to list view (no close/reopen flicker)
    document.getElementById("pm-btn-cancel").addEventListener("click", () => showListView());

    const nameInput = document.getElementById("pm-input-name");
    const descInput = document.getElementById("pm-input-desc");
    const pathInput = document.getElementById("pm-input-path");
    const pathError = document.getElementById("pm-path-error");

    nameInput.addEventListener("input", () => {
      if (descInput.dataset.auto === "true") descInput.value = nameInput.value;
    });
    descInput.addEventListener("input", () => { descInput.dataset.auto = "false"; });
    pathInput.addEventListener("input", () => {
      pathInput.classList.remove("error");
      pathError.style.display = "none";
    });

    // Real-time path hint on blur (non-blocking — doesn't prevent submission)
    pathInput.addEventListener("blur", async () => {
      const p = pathInput.value.trim();
      if (!p) return;
      const ok = await validatePath(p);
      if (!ok) {
        pathInput.classList.add("error");
        pathError.textContent = "Path does not exist on this machine.";
        pathError.style.display = "block";
      } else {
        pathInput.classList.remove("error");
        pathError.style.display = "none";
      }
    });

    document.getElementById("pm-new-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const name = nameInput.value.trim();
      const desc = descInput.value.trim();
      const path = pathInput.value.trim();
      const inst = document.getElementById("pm-input-inst").value.trim();

      pathInput.classList.remove("error");
      pathError.style.display = "none";

      const submitBtn = e.target.querySelector('button[type="submit"]');
      const originalText = submitBtn.textContent;
      submitBtn.disabled = true;
      submitBtn.textContent = "Creating...";

      try {
        const response = await fetch("/api/projects/create-project", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, path, description: desc, instructions: inst }),
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          const detail = errData.detail || "Failed to create project";
          // If it's a path problem (400 from backend), show it inline
          if (response.status === 400 && detail.toLowerCase().includes("path")) {
            pathInput.classList.add("error");
            pathError.textContent = "Path does not exist on this machine.";
            pathError.style.display = "block";
          } else {
            alert(`Error: ${detail}`);
          }
          submitBtn.disabled = false;
          submitBtn.textContent = originalText;
          return;
        }

        const resData = await response.json();
        setCookie("active_project", name);
        setCookie("active_project_id", resData.project_id);
        window.location.href = "/";
      } catch (error) {
        alert(`Network error: ${error.message}`);
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
      }
    });
  }

  async function openModal() {
    if (btn) btn.classList.add("open");

    let overlay = document.getElementById("project-modal-overlay");
    if (!overlay) {
      overlay = document.createElement("div");
      overlay.id = "project-modal-overlay";
      overlay.innerHTML = `<div id="project-modal"></div>`;
      document.body.appendChild(overlay);

      overlay.addEventListener("click", (e) => {
        if (e.target === overlay) closeModal();
      });
    }

    await showListView();
    setTimeout(() => overlay.classList.add("open"), 10);
  }

  function closeModal() {
    const overlay = document.getElementById("project-modal-overlay");
    if (overlay) overlay.classList.remove("open");
    if (btn) btn.classList.remove("open");
  }

  function renderProjects(projects) {
    const list = document.getElementById("pm-project-list");
    if (!list) return;
    list.innerHTML = "";

    if (!projects || projects.length === 0) {
      list.innerHTML = `<div style="padding:10px;text-align:center;font-size:13px;opacity:0.4;">No projects yet</div>`;
      return;
    }

    projects.forEach((proj) => {
      const isActive = activeProjectId === proj.id;
      const card = document.createElement("button");
      card.className = `pm-project-card${isActive ? " active" : ""}`;
      card.innerHTML = `
        <span class="pm-card-icon">${ICONS.folder}</span>
        <span class="pm-card-info">
          <span class="pm-card-name">${proj.name}</span>
          <span class="pm-card-path">${proj.path}</span>
        </span>
        ${isActive ? `<span class="pm-card-check">${ICONS.check}</span>` : ""}
        <span class="pm-card-delete" title="Delete project">${ICONS.trash}</span>
      `;

      // Select project on card click
      card.addEventListener("click", (e) => {
        // Don't select if delete button was clicked
        if (e.target.closest(".pm-card-delete")) return;
        setCookie("active_project", proj.name);
        setCookie("active_project_id", proj.id);
        window.location.href = "/";
      });

      // Delete button handler
      const deleteBtn = card.querySelector(".pm-card-delete");
      deleteBtn.addEventListener("click", async (e) => {
        e.stopPropagation();
        if (!confirm(`Delete project "${proj.name}"? This cannot be undone.`))
          return;

        const result = await deleteProject(proj.id);
        if (result) {
          // If the deleted project was active, clear cookies
          if (activeProjectId === proj.id) {
            clearCookie("active_project");
            clearCookie("active_project_id");
            window.location.href = "/";
          }
          // Remove the card with animation
          card.style.transition = "opacity 0.25s ease, transform 0.25s ease";
          card.style.opacity = "0";
          card.style.transform = "translateX(-12px)";
          setTimeout(() => {
            card.remove();
            // If no projects left, show empty state
            if (list.children.length === 0) {
              list.innerHTML = `<div style="padding:10px;text-align:center;font-size:13px;opacity:0.4;">No projects yet</div>`;
            }
            // Reload if the active project was deleted
            if (activeProjectId === proj.id) {
              window.location.reload();
            }
          }, 250);
        } else {
          alert("Failed to delete the project. Please try again.");
        }
      });

      list.appendChild(card);
    });
  }

  // =============================================
  // Boot
  // =============================================
  function boot() {
    createButton();

    // Watch for React re-renders removing our button
    const mo = new MutationObserver(() => {
      if (!document.getElementById("project-dropdown-btn")) {
        btn = null;
        createButton();
      }
    });
    mo.observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
