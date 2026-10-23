/**
 * EventPilot AI — Frontend Application Logic
 * Pure Vanilla JavaScript: Responsive, Accessible, Deterministic Calculations
 */

class EventPilotApp {
  constructor() {
    this.currentPlan = null;
    this.savedEvents = [];
    this.modelStatus = { available: false, model_available: false };
    this.init();
  }

  async init() {
    this.bindEvents();
    this.setDefaultDate();
    await this.checkModelStatus();
    await this.loadSavedEvents();
    if (window.lucide) {
      window.lucide.createIcons();
    }
  }

  bindEvents() {
    // Navigation Tabs
    document.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', (e) => {
        const tab = e.currentTarget.getAttribute('data-tab');
        if (tab) this.switchTab(tab);
      });
    });

    // Mobile menu toggle
    const menuBtn = document.getElementById('mobileMenuBtn');
    if (menuBtn) {
      menuBtn.addEventListener('click', () => {
        document.getElementById('appSidebar').classList.toggle('open');
      });
    }

    // Refresh model status button
    const refreshModelBtn = document.getElementById('btnRefreshModel');
    if (refreshModelBtn) {
      refreshModelBtn.addEventListener('click', () => this.checkModelStatus(true));
    }

    // Form submission
    const form = document.getElementById('createEventForm');
    if (form) {
      form.addEventListener('submit', (e) => this.handleFormSubmit(e));
    }
  }

  setDefaultDate() {
    const dateInput = document.getElementById('eventDate');
    if (dateInput) {
      const defaultDate = new Date();
      defaultDate.setDate(defaultDate.getDate() + 30);
      dateInput.value = defaultDate.toISOString().split('T')[0];
    }
  }

  switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

    const targetTab = document.getElementById(tabId);
    if (targetTab) {
      targetTab.classList.add('active');
    }

    const navLink = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
    if (navLink) {
      navLink.classList.add('active');
    }

    // Close mobile menu if open
    document.getElementById('appSidebar').classList.remove('open');

    // Update Topbar heading
    const headings = {
      'tab-dashboard': 'Dashboard Overview',
      'tab-create': 'Create New Event Plan',
      'tab-saved': 'Saved Event Plans',
      'tab-plan-view': 'Active Event Plan'
    };
    const headingEl = document.getElementById('topbarHeading');
    if (headingEl) {
      headingEl.textContent = headings[tabId] || 'EventPilot AI';
    }

    if (window.lucide) window.lucide.createIcons();
  }

  switchSubTab(subTabId) {
    document.querySelectorAll('.subtab-content').forEach(el => {
      el.style.display = (el.id === subTabId) ? 'block' : 'none';
    });
    document.querySelectorAll('.subnav-btn').forEach(btn => {
      if (btn.getAttribute('data-subtab') === subTabId) {
        btn.classList.add('active');
        btn.style.backgroundColor = 'var(--forest-800)';
        btn.style.color = '#fff';
      } else {
        btn.classList.remove('active');
        btn.style.backgroundColor = 'transparent';
        btn.style.color = 'var(--text-main)';
      }
    });
    if (window.lucide) window.lucide.createIcons();
  }

  async checkModelStatus(notify = false) {
    try {
      const res = await fetch('/api/model/status');
      const data = await res.json();
      this.modelStatus = data;

      const dot = document.getElementById('modelStatusDot');
      const statusText = document.getElementById('modelStatusText');
      const modelNameText = document.getElementById('modelNameText');
      const badge = document.getElementById('activeModelBadge');
      const dashStatus = document.getElementById('dashAiStatus');
      const dashModel = document.getElementById('dashAiModel');

      const configuredModel = data.model_configured || data.configured_model || 'gemma2:2b';

      if (data.available && data.model_available) {
        dot.className = 'status-dot online';
        statusText.textContent = data.provider === 'demo' ? 'Demo Mode Active' : `${configuredModel} Ready`;
        modelNameText.textContent = configuredModel;
        if (badge) badge.textContent = `${data.provider.toUpperCase()}: ${configuredModel} (Online)`;
        if (dashStatus) dashStatus.textContent = 'Gemma engine connected';
        if (dashModel) dashModel.textContent = configuredModel;
        if (notify) this.showToast(`Inference ready: ${configuredModel}`, 'success');
      } else if (data.available) {
        dot.className = 'status-dot offline';
        statusText.textContent = 'Model Missing';
        modelNameText.textContent = `Pull '${configuredModel}'`;
        if (badge) badge.textContent = `${configuredModel} needs setup`;
        if (dashStatus) dashStatus.textContent = 'Model pull needed';
        if (notify) this.showToast(`Endpoint reachable, but ${configuredModel} missing`, 'error');
      } else {
        dot.className = 'status-dot offline';
        statusText.textContent = 'AI Offline';
        modelNameText.textContent = 'Fallback/Demo active';
        if (badge) badge.textContent = `Offline (Instant fallback enabled)`;
        if (dashStatus) dashStatus.textContent = 'Fallback active';
        if (notify) this.showToast('Gemma endpoint offline. Using fallback engine.', 'error');
      }
    } catch (err) {
      console.warn('Could not query model status:', err);
    }
  }

  fillDemoForm() {
    this.switchTab('tab-create');
    document.getElementById('eventName').value = "Aditi's 25th Birthday Bash";
    document.getElementById('eventType').value = 'birthday';
    
    const d = new Date();
    d.setDate(d.getDate() + 25);
    document.getElementById('eventDate').value = d.toISOString().split('T')[0];
    
    document.getElementById('eventLocation').value = 'Indiranagar, Bengaluru';
    document.getElementById('eventGuests').value = '40';
    document.getElementById('eventBudget').value = '35000';
    document.getElementById('eventCurrency').value = 'INR';
    document.getElementById('eventPriority').value = 'balanced';
    document.getElementById('eventVenue').value = 'home';
    document.getElementById('eventFood').value = 'vegetarian';
    document.getElementById('eventTheme').value = 'Boho Garden Party with fairy lights';
    document.getElementById('eventCulture').value = 'Contemporary Indian Fusion';
    document.getElementById('eventNotes').value = 'Include a custom chocolate truffle cake and interactive party games. Keep music acoustic until 9 PM.';
    this.showToast('Sample form details filled! Click "Generate Event Plan" below.', 'success');
  }

  async handleFormSubmit(e) {
    e.preventDefault();
    const submitBtn = document.getElementById('btnSubmitPlan');
    submitBtn.disabled = true;

    const overlay = document.getElementById('loadingOverlay');
    const loadTitle = document.getElementById('loadingTitle');
    const loadSub = document.getElementById('loadingSubtitle');
    overlay.classList.add('active');

    const forceDemo = document.getElementById('checkForceDemo').checked;

    if (forceDemo) {
      loadTitle.textContent = "Crafting Plan in Demo Mode...";
      loadSub.textContent = "Instant deterministic generation without querying external AI.";
    } else {
      const activeModel = this.modelStatus.model_configured || this.modelStatus.configured_model || 'gemma2:2b';
      loadTitle.textContent = "Channeling Your Inner Sloth...";
      loadSub.textContent = `Querying instruction-tuned model (${activeModel})...`;
    }

    const payload = {
      name: document.getElementById('eventName').value.trim(),
      event_type: document.getElementById('eventType').value,
      event_date: document.getElementById('eventDate').value,
      location: document.getElementById('eventLocation').value.trim(),
      guest_count: parseInt(document.getElementById('eventGuests').value, 10),
      budget: parseFloat(document.getElementById('eventBudget').value),
      currency: document.getElementById('eventCurrency').value,
      priority: document.getElementById('eventPriority').value,
      venue_preference: document.getElementById('eventVenue').value,
      food_preference: document.getElementById('eventFood').value,
      theme: document.getElementById('eventTheme').value.trim(),
      cultural_preference: document.getElementById('eventCulture').value.trim(),
      additional_notes: document.getElementById('eventNotes').value.trim()
    };

    try {
      const url = `/api/events/generate?force_demo=${forceDemo}`;
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }

      const plan = await response.json();
      this.currentPlan = plan;
      this.renderPlanView(plan);
      
      // Show active plan tab in sidebar
      const navPlan = document.getElementById('navActivePlan');
      if (navPlan) navPlan.style.display = 'flex';
      
      this.switchTab('tab-plan-view');
      this.showToast('Event plan successfully generated!', 'success');
    } catch (err) {
      console.error('Error generating event:', err);
      this.showToast(`Generation failed: ${err.message}`, 'error');
    } finally {
      overlay.classList.remove('active');
      submitBtn.disabled = false;
    }
  }

  renderPlanView(plan) {
    if (!plan) return;

    // Plan Header
    document.getElementById('planTitle').textContent = plan.name;
    document.getElementById('planTagline').textContent = `"${plan.tagline || 'Relax and celebrate'}"`;
    document.getElementById('planBadgeType').textContent = plan.event_type;
    document.getElementById('planOverviewText').textContent = plan.overview;

    const engineTag = document.getElementById('planEngineTag');
    if (plan.ai_generated) {
      engineTag.textContent = `Generated by ${plan.model_used}`;
      engineTag.style.background = 'var(--forest-100)';
      engineTag.style.color = 'var(--forest-800)';
    } else {
      engineTag.textContent = plan.model_used || 'Deterministic Fallback Planner';
      engineTag.style.background = '#fef3c7';
      engineTag.style.color = '#d97706';
    }

    // Meta Pills
    document.getElementById('planMetaDate').textContent = plan.event_date;
    document.getElementById('planMetaGuests').textContent = `${plan.guest_count} Guests`;
    document.getElementById('planMetaLocation').textContent = plan.location || 'Undecided Location';
    document.getElementById('planMetaFood').textContent = plan.food_preference || 'Standard';

    // Render Subtabs
    this.renderBudgetGuard();
    this.renderTimeline();
    this.renderVendors();
    this.renderShopping();
    this.renderSchedule();
    this.renderInsights();

    // Default to budget subtab
    this.switchSubTab('subtab-budget');
  }

  /* ---------------- BudgetGuard Logic ---------------- */
  renderBudgetGuard() {
    const plan = this.currentPlan;
    if (!plan) return;

    const curr = plan.currency;
    document.querySelectorAll('.currency-label').forEach(el => el.textContent = curr);

    // Compute deterministic numbers directly
    const targetBudget = Number(plan.total_budget);
    let totalEstimated = 0;
    (plan.budget_items || []).forEach(item => {
      totalEstimated += Number(item.estimated_cost);
    });
    totalEstimated = Math.round(totalEstimated * 100) / 100;
    const remaining = Math.round((targetBudget - totalEstimated) * 100) / 100;
    const utilPct = targetBudget > 0 ? Math.round((totalEstimated / targetBudget) * 100) : 0;

    // Update KPI displays
    document.getElementById('bgTargetBudget').textContent = `${curr} ${targetBudget.toLocaleString()}`;
    document.getElementById('bgPlannedSpend').textContent = `${curr} ${totalEstimated.toLocaleString()}`;
    
    const remainingEl = document.getElementById('bgRemainingBalance');
    remainingEl.textContent = `${curr} ${remaining.toLocaleString()}`;
    if (remaining < 0) {
      remainingEl.style.color = 'var(--danger)';
    } else {
      remainingEl.style.color = 'var(--forest-800)';
    }

    document.getElementById('bgUtilizationPct').textContent = `${utilPct}%`;

    // Progress Bar
    const fill = document.getElementById('bgProgressFill');
    fill.style.width = `${Math.min(utilPct, 100)}%`;
    if (utilPct > 100) {
      fill.className = 'progress-bar-fill danger';
    } else if (utilPct > 85) {
      fill.className = 'progress-bar-fill warning';
    } else {
      fill.className = 'progress-bar-fill';
    }

    // Over budget banner
    const warningBanner = document.getElementById('bgOverBudgetWarning');
    if (totalEstimated > targetBudget) {
      warningBanner.style.display = 'flex';
    } else {
      warningBanner.style.display = 'none';
    }

    // Render table rows
    const tbody = document.getElementById('budgetTableBody');
    tbody.innerHTML = '';
    (plan.budget_items || []).forEach((item, idx) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${this.escapeHtml(item.category)}</strong></td>
        <td>${this.escapeHtml(item.item_name)}</td>
        <td>
          <input 
            type="number" 
            class="table-input budget-cost-input" 
            data-index="${idx}" 
            value="${item.estimated_cost}" 
            min="0" 
            step="50"
          >
        </td>
        <td style="color: var(--text-muted); font-size: 0.8rem;">${this.escapeHtml(item.notes || '—')}</td>
        <td class="no-print">
          <button class="btn btn-outline btn-sm" onclick="app.removeBudgetItem(${idx})" title="Delete item">
            <i data-lucide="trash-2" style="width:14px; height:14px; color:var(--danger);"></i>
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    // Attach real-time calculation listener to all cost inputs
    document.querySelectorAll('.budget-cost-input').forEach(input => {
      input.addEventListener('input', (e) => {
        const idx = parseInt(e.target.getAttribute('data-index'), 10);
        const val = parseFloat(e.target.value) || 0;
        this.currentPlan.budget_items[idx].estimated_cost = val;
        this.recalculateAndRefreshBudgetUI();
      });
    });

    if (window.lucide) window.lucide.createIcons();
  }

  recalculateAndRefreshBudgetUI() {
    const plan = this.currentPlan;
    if (!plan) return;

    const curr = plan.currency;
    let totalEstimated = 0;
    plan.budget_items.forEach(item => {
      totalEstimated += Number(item.estimated_cost);
    });
    totalEstimated = Math.round(totalEstimated * 100) / 100;
    plan.total_estimated_budget = totalEstimated;
    plan.remaining_balance = Math.round((plan.total_budget - totalEstimated) * 100) / 100;
    plan.is_over_budget = totalEstimated > plan.total_budget;

    const utilPct = plan.total_budget > 0 ? Math.round((totalEstimated / plan.total_budget) * 100) : 0;

    document.getElementById('bgPlannedSpend').textContent = `${curr} ${totalEstimated.toLocaleString()}`;
    const remainingEl = document.getElementById('bgRemainingBalance');
    remainingEl.textContent = `${curr} ${plan.remaining_balance.toLocaleString()}`;
    remainingEl.style.color = plan.remaining_balance < 0 ? 'var(--danger)' : 'var(--forest-800)';

    document.getElementById('bgUtilizationPct').textContent = `${utilPct}%`;

    const fill = document.getElementById('bgProgressFill');
    fill.style.width = `${Math.min(utilPct, 100)}%`;
    if (utilPct > 100) {
      fill.className = 'progress-bar-fill danger';
    } else if (utilPct > 85) {
      fill.className = 'progress-bar-fill warning';
    } else {
      fill.className = 'progress-bar-fill';
    }

    const warningBanner = document.getElementById('bgOverBudgetWarning');
    warningBanner.style.display = plan.is_over_budget ? 'flex' : 'none';
  }

  promptAddBudgetItem() {
    const category = prompt('Category name (e.g. Venue, Catering, Music, Decor):');
    if (!category) return;
    const itemName = prompt('Item description:');
    if (!itemName) return;
    const cost = parseFloat(prompt('Estimated Cost:', '1000')) || 0;

    this.currentPlan.budget_items.push({
      id: `budget-${Date.now()}`,
      category: category.trim(),
      item_name: itemName.trim(),
      estimated_cost: cost,
      actual_cost: 0,
      notes: 'User added'
    });
    this.renderBudgetGuard();
    this.showToast('Item added to budget plan', 'success');
  }

  removeBudgetItem(idx) {
    if (confirm('Delete this budget item?')) {
      this.currentPlan.budget_items.splice(idx, 1);
      this.renderBudgetGuard();
      this.showToast('Item removed', 'success');
    }
  }

  /* ---------------- LazyTimeline Logic ---------------- */
  renderTimeline() {
    const plan = this.currentPlan;
    if (!plan) return;

    const container = document.getElementById('timelineList');
    container.innerHTML = '';

    const tasks = plan.tasks || [];
    const completed = tasks.filter(t => t.completed).length;
    document.getElementById('taskCompletionStatus').textContent = `${completed}/${tasks.length} completed`;

    const todayStr = new Date().toISOString().split('T')[0];

    tasks.forEach((t, idx) => {
      const isPast = t.due_date < todayStr;
      const isOverdue = isPast && !t.completed;

      const itemEl = document.createElement('div');
      itemEl.className = `timeline-item ${t.completed ? 'completed' : ''} ${isOverdue ? 'overdue' : ''}`;
      itemEl.innerHTML = `
        <input 
          type="checkbox" 
          class="task-checkbox" 
          data-index="${idx}" 
          ${t.completed ? 'checked' : ''}
        >
        <div class="task-content">
          <div class="task-title">
            <span>${this.escapeHtml(t.title)}</span>
            <span class="badge-priority ${t.priority || 'medium'}">${t.priority || 'medium'}</span>
            ${isOverdue ? '<span class="badge-overdue">OVERDUE</span>' : ''}
          </div>
          <div class="task-desc">${this.escapeHtml(t.description)}</div>
          <div class="task-meta">
            <span><i data-lucide="calendar" style="width:12px;height:12px;"></i> Due: <strong>${t.due_date}</strong></span>
            <span>(${t.days_before_event} days before event)</span>
            <span style="color:var(--sage-500); font-weight:600;">Phase: ${this.escapeHtml(t.phase || 'Preparation')}</span>
          </div>
        </div>
        <button class="btn btn-outline btn-sm no-print" onclick="app.removeTask(${idx})" title="Delete task">
          <i data-lucide="trash-2" style="width:13px;height:13px;color:var(--text-light);"></i>
        </button>
      `;
      container.appendChild(itemEl);
    });

    // Checkbox toggle listeners
    container.querySelectorAll('.task-checkbox').forEach(chk => {
      chk.addEventListener('change', (e) => {
        const idx = parseInt(e.target.getAttribute('data-index'), 10);
        this.currentPlan.tasks[idx].completed = e.target.checked;
        this.renderTimeline();
      });
    });

    if (window.lucide) window.lucide.createIcons();
  }

  promptAddTask() {
    const title = prompt('Task title:');
    if (!title) return;
    const desc = prompt('Task description:', '') || '';
    const daysBefore = parseInt(prompt('How many days before event is this due?', '7'), 10) || 7;

    const eventDate = new Date(this.currentPlan.event_date);
    const dueDate = new Date(eventDate);
    dueDate.setDate(dueDate.getDate() - daysBefore);

    this.currentPlan.tasks.push({
      id: `task-${Date.now()}`,
      title: title.trim(),
      description: desc.trim(),
      phase: daysBefore <= 3 ? 'Final Days' : daysBefore <= 14 ? '2 Weeks Before' : '1 Month Before',
      due_date: dueDate.toISOString().split('T')[0],
      days_before_event: daysBefore,
      priority: 'medium',
      completed: false,
      is_overdue: false
    });

    this.currentPlan.tasks.sort((a, b) => a.due_date.localeCompare(b.due_date));
    this.renderTimeline();
    this.showToast('Task added to schedule', 'success');
  }

  removeTask(idx) {
    if (confirm('Delete this task?')) {
      this.currentPlan.tasks.splice(idx, 1);
      this.renderTimeline();
      this.showToast('Task removed', 'success');
    }
  }

  /* ---------------- Vendors & Shopping Logic ---------------- */
  renderVendors() {
    const plan = this.currentPlan;
    if (!plan) return;

    const tbody = document.getElementById('vendorTableBody');
    tbody.innerHTML = '';

    (plan.vendors || []).forEach((v, idx) => {
      const questionsList = (v.key_questions || []).map(q => `<li>${this.escapeHtml(q)}</li>`).join('');
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${this.escapeHtml(v.category)}</strong></td>
        <td>
          <div style="font-weight: 500; margin-bottom: 4px;">${this.escapeHtml(v.recommended_scope)}</div>
          <ul style="font-size: 0.75rem; color: var(--text-muted); padding-left: 14px;">
            ${questionsList}
          </ul>
        </td>
        <td>${plan.currency} ${Number(v.estimated_cost).toLocaleString()}</td>
        <td>
          <input 
            type="text" 
            class="table-input" 
            placeholder="e.g. Royal Caterers" 
            value="${this.escapeHtml(v.vendor_name || '')}"
            onchange="app.currentPlan.vendors[${idx}].vendor_name = this.value"
          >
        </td>
        <td>
          <input 
            type="number" 
            class="table-input" 
            placeholder="Quoted" 
            value="${v.quoted_cost || ''}"
            onchange="app.currentPlan.vendors[${idx}].quoted_cost = parseFloat(this.value) || 0"
          >
        </td>
        <td class="no-print">
          <select 
            class="table-input" 
            onchange="app.currentPlan.vendors[${idx}].status = this.value"
          >
            <option value="pending" ${v.status === 'pending' ? 'selected' : ''}>Pending</option>
            <option value="contacted" ${v.status === 'contacted' ? 'selected' : ''}>Contacted</option>
            <option value="booked" ${v.status === 'booked' ? 'selected' : ''}>Booked</option>
          </select>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  renderShopping() {
    const plan = this.currentPlan;
    if (!plan) return;

    const container = document.getElementById('shoppingChecklistContainer');
    container.innerHTML = '';

    (plan.shopping_list || []).forEach((item, idx) => {
      const card = document.createElement('div');
      card.style.background = '#faf9f5';
      card.style.border = '1px solid var(--border-subtle)';
      card.style.borderRadius = 'var(--radius-sm)';
      card.style.padding = '10px 14px';
      card.style.display = 'flex';
      card.style.alignItems = 'center';
      card.style.gap = '10px';

      card.innerHTML = `
        <input 
          type="checkbox" 
          class="task-checkbox" 
          ${item.purchased ? 'checked' : ''} 
          onchange="app.currentPlan.shopping_list[${idx}].purchased = this.checked"
        >
        <div style="flex:1;">
          <div style="font-size: 0.88rem; font-weight: 600; color: var(--forest-900); ${item.purchased ? 'text-decoration: line-through;' : ''}">
            ${this.escapeHtml(item.item)}
          </div>
          <div style="font-size: 0.75rem; color: var(--text-muted);">
            Qty: <strong>${this.escapeHtml(item.quantity)}</strong> · ${this.escapeHtml(item.category)}
          </div>
        </div>
      `;
      container.appendChild(card);
    });
  }

  /* ---------------- Schedule & Insights ---------------- */
  renderSchedule() {
    const plan = this.currentPlan;
    if (!plan) return;

    const container = document.getElementById('scheduleTimelineContainer');
    container.innerHTML = '';

    (plan.activities_schedule || []).forEach(act => {
      const item = document.createElement('div');
      item.style.display = 'flex';
      item.style.gap = '16px';
      item.style.alignItems = 'flex-start';

      item.innerHTML = `
        <div style="min-width: 90px; font-weight: 700; color: var(--forest-800); font-size: 0.9rem; padding: 4px 8px; background: var(--forest-100); border-radius: 4px; text-align: center;">
          ${this.escapeHtml(act.time || 'TBD')}
        </div>
        <div style="flex:1; border-left: 2px solid var(--sage-400); padding-left: 14px; padding-bottom: 12px;">
          <div style="font-weight: 600; color: var(--forest-900); font-size: 0.95rem;">${this.escapeHtml(act.activity)}</div>
          <div style="font-size: 0.82rem; color: var(--text-muted); margin-top: 2px;">${this.escapeHtml(act.notes || '')}</div>
        </div>
      `;
      container.appendChild(item);
    });
  }

  renderInsights() {
    const plan = this.currentPlan;
    if (!plan) return;

    this.renderListItems('planThemeList', plan.theme_ideas);
    this.renderListItems('planCostSavingList', plan.cost_saving_suggestions);
    this.renderListItems('planContingencyList', plan.contingency_recommendations);
    this.renderListItems('planRisksList', plan.potential_risks);
  }

  renderListItems(elementId, items) {
    const ul = document.getElementById(elementId);
    if (!ul) return;
    ul.innerHTML = '';
    (items || []).forEach(text => {
      const li = document.createElement('li');
      li.style.display = 'flex';
      li.style.gap = '8px';
      li.style.fontSize = '0.88rem';
      li.style.color = 'var(--text-main)';
      li.innerHTML = `<span style="color:var(--sage-500); font-weight:bold;">•</span> <span>${this.escapeHtml(text)}</span>`;
      ul.appendChild(li);
    });
  }

  /* ---------------- Saved Events & SQLite API ---------------- */
  async saveCurrentPlanToDb() {
    if (!this.currentPlan) return;
    const btn = document.getElementById('btnSaveToDb');
    btn.disabled = true;

    try {
      const res = await fetch('/api/events', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(this.currentPlan)
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const saved = await res.json();
      this.currentPlan = saved;
      this.showToast('Plan safely saved to SQLite database!', 'success');
      await this.loadSavedEvents();
    } catch (err) {
      console.error('Failed to save plan:', err);
      this.showToast(`Error saving plan: ${err.message}`, 'error');
    } finally {
      btn.disabled = false;
    }
  }

  async loadSavedEvents() {
    try {
      const res = await fetch('/api/events');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      this.savedEvents = await res.json();
      
      const countBadge = document.getElementById('savedCountBadge');
      if (countBadge) countBadge.textContent = this.savedEvents.length;

      // Update dashboard metric cards
      const totalEventsEl = document.getElementById('dashTotalEvents');
      if (totalEventsEl) totalEventsEl.textContent = this.savedEvents.length;

      let sumBudget = 0;
      let pendingTasks = 0;
      this.savedEvents.forEach(e => {
        sumBudget += e.total_budget || 0;
        pendingTasks += (e.task_count - e.completed_task_count);
      });

      const dashBudgetEl = document.getElementById('dashTotalBudget');
      if (dashBudgetEl) dashBudgetEl.textContent = `₹${sumBudget.toLocaleString()}`;

      const dashTasksEl = document.getElementById('dashPendingTasks');
      if (dashTasksEl) dashTasksEl.textContent = pendingTasks;

      this.renderSavedEventsGrid();
      this.renderDashboardRecentGrid();
    } catch (err) {
      console.warn('Error loading saved events:', err);
    }
  }

  renderSavedEventsGrid() {
    const grid = document.getElementById('savedEventsGrid');
    const empty = document.getElementById('savedEmptyState');
    if (!grid) return;

    if (!this.savedEvents || this.savedEvents.length === 0) {
      grid.style.display = 'none';
      if (empty) empty.style.display = 'block';
      return;
    }

    grid.style.display = 'grid';
    if (empty) empty.style.display = 'none';
    grid.innerHTML = '';

    this.savedEvents.forEach(evt => {
      grid.appendChild(this.createEventCardElement(evt));
    });

    if (window.lucide) window.lucide.createIcons();
  }

  renderDashboardRecentGrid() {
    const grid = document.getElementById('dashboardEventsList');
    const empty = document.getElementById('dashboardEmptyState');
    if (!grid) return;

    if (!this.savedEvents || this.savedEvents.length === 0) {
      grid.style.display = 'none';
      if (empty) empty.style.display = 'block';
      return;
    }

    grid.style.display = 'grid';
    if (empty) empty.style.display = 'none';
    grid.innerHTML = '';

    // Show recent 3
    const recent = this.savedEvents.slice(0, 3);
    recent.forEach(evt => {
      grid.appendChild(this.createEventCardElement(evt));
    });

    if (window.lucide) window.lucide.createIcons();
  }

  createEventCardElement(evt) {
    const card = document.createElement('div');
    card.className = 'event-card';

    card.innerHTML = `
      <div class="event-card-header">
        <span class="event-badge">${this.escapeHtml(evt.event_type)}</span>
        <button class="btn btn-outline btn-sm no-print" onclick="app.deleteEvent('${evt.id}', event)" title="Delete event">
          <i data-lucide="trash-2" style="width:14px;height:14px;color:var(--danger);"></i>
        </button>
      </div>

      <div class="event-card-title">${this.escapeHtml(evt.name)}</div>

      <div class="event-meta">
        <div class="event-meta-item">
          <i data-lucide="calendar" style="width:13px;height:13px;"></i>
          <span>${evt.event_date}</span>
        </div>
        <div class="event-meta-item">
          <i data-lucide="users" style="width:13px;height:13px;"></i>
          <span>${evt.guest_count} guests</span>
        </div>
        <div class="event-meta-item">
          <i data-lucide="wallet" style="width:13px;height:13px;"></i>
          <span>${evt.currency} ${Number(evt.total_budget).toLocaleString()}</span>
        </div>
      </div>

      <div style="font-size: 0.78rem; color: var(--text-muted); margin-bottom: 16px;">
        Tasks progress: <strong>${evt.completed_task_count}/${evt.task_count} completed</strong>
      </div>

      <div style="margin-top: auto; display: flex; gap: 8px;">
        <button class="btn btn-primary btn-sm" style="flex:1;" onclick="app.openSavedEvent('${evt.id}')">
          <i data-lucide="folder-open"></i> Open Plan
        </button>
      </div>
    `;
    return card;
  }

  async openSavedEvent(eventId) {
    try {
      const res = await fetch(`/api/events/${eventId}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const plan = await res.json();
      this.currentPlan = plan;
      this.renderPlanView(plan);
      
      const navPlan = document.getElementById('navActivePlan');
      if (navPlan) navPlan.style.display = 'flex';
      
      this.switchTab('tab-plan-view');
      this.showToast(`Loaded "${plan.name}"`, 'success');
    } catch (err) {
      console.error('Error loading event:', err);
      this.showToast(`Could not load event: ${err.message}`, 'error');
    }
  }

  async deleteEvent(eventId, evt) {
    if (evt) evt.stopPropagation();
    if (!confirm('Are you sure you want to permanently delete this event?')) return;

    try {
      const res = await fetch(`/api/events/${eventId}`, { method: 'DELETE' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      this.showToast('Event deleted', 'success');
      
      // If deleted active plan, reset
      if (this.currentPlan && this.currentPlan.id === eventId) {
        this.currentPlan = null;
        const navPlan = document.getElementById('navActivePlan');
        if (navPlan) navPlan.style.display = 'none';
        this.switchTab('tab-dashboard');
      }

      await this.loadSavedEvents();
    } catch (err) {
      console.error('Error deleting event:', err);
      this.showToast(`Delete failed: ${err.message}`, 'error');
    }
  }

  /* ---------------- Exports & Utilities ---------------- */
  exportCurrentPlanJson() {
    if (!this.currentPlan) return;
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(this.currentPlan, null, 2));
    const downloadAnchor = document.createElement('a');
    const filename = `${this.currentPlan.name.toLowerCase().replace(/[^a-z0-9]/g, '_')}_plan.json`;
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", filename);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    this.showToast('Event plan JSON exported!', 'success');
  }

  showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    container.appendChild(toast);
    setTimeout(() => {
      toast.remove();
    }, 4000);
  }

  escapeHtml(str) {
    if (typeof str !== 'string') return str;
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
}

// Global App Instance
let app;
document.addEventListener('DOMContentLoaded', () => {
  app = new EventPilotApp();
  window.app = app;
});
