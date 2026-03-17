(function () {
    const STORAGE_KEYS = {
        customTasks: 'disciplineai-custom-tasks',
        focusSessions: 'disciplineai-focus-sessions',
        currentFocusTask: 'disciplineai-current-focus-task',
        habitEntries: 'disciplineai-habit-entries',
    };
    const FOCUS_SYNC_URL = '/api/live-stats/focus';

    const safeParse = (value, fallback) => {
        if (!value) {
            return fallback;
        }
        try {
            return JSON.parse(value);
        } catch (error) {
            console.error('Failed to parse local storage payload', error);
            return fallback;
        }
    };

    const localDateString = (value) => {
        const date = value instanceof Date ? value : new Date(value);
        if (Number.isNaN(date.getTime())) {
            return '';
        }
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };

    const nowIso = () => new Date().toISOString();
    const todayIso = () => localDateString(new Date());
    const uniqueId = (prefix) => `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

    const loadJson = (key, fallback) => {
        try {
            return safeParse(window.localStorage.getItem(key), fallback);
        } catch (error) {
            console.error('Failed to read local storage', error);
            return fallback;
        }
    };

    const saveJson = (key, value) => {
        try {
            window.localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.error('Failed to save local storage', error);
        }
    };

    const lastNDates = (days) => {
        const total = Math.max(Number(days || 0), 1);
        const dates = [];
        const start = new Date();
        start.setHours(0, 0, 0, 0);
        start.setDate(start.getDate() - (total - 1));
        for (let index = 0; index < total; index += 1) {
            const value = new Date(start);
            value.setDate(start.getDate() + index);
            dates.push(localDateString(value));
        }
        return dates;
    };

    const getCustomTasks = () => {
        const items = loadJson(STORAGE_KEYS.customTasks, []);
        return Array.isArray(items) ? items : [];
    };

    const saveCustomTasks = (items) => {
        saveJson(STORAGE_KEYS.customTasks, items);
    };

    const addCustomTask = (task) => {
        const items = getCustomTasks();
        const normalized = {
            id: task.id || uniqueId('task'),
            title: String(task.title || '').trim(),
            description: String(task.description || '').trim(),
            priority: String(task.priority || 'medium').toLowerCase(),
            dueDate: String(task.dueDate || todayIso()),
            completed: Boolean(task.completed),
            completedAt: task.completedAt || null,
            createdAt: task.createdAt || nowIso(),
        };
        items.push(normalized);
        saveCustomTasks(items);
        return normalized;
    };

    const updateCustomTask = (taskId, updater) => {
        const items = getCustomTasks();
        const updated = items.map((item) => {
            if (item.id !== taskId) {
                return item;
            }
            const next = typeof updater === 'function' ? updater(item) : item;
            return next;
        });
        saveCustomTasks(updated);
        return updated.find((item) => item.id === taskId) || null;
    };

    const toggleCustomTask = (taskId, completed) => updateCustomTask(taskId, (item) => ({
        ...item,
        completed: Boolean(completed),
        completedAt: completed ? nowIso() : null,
    }));

    const getCompletedCustomTaskCountByDates = (dates) => {
        const items = getCustomTasks();
        const counts = Object.fromEntries(dates.map((date) => [date, 0]));
        items.forEach((item) => {
            if (!item.completed || !item.completedAt) {
                return;
            }
            const completedDate = localDateString(item.completedAt);
            if (!counts[completedDate] && counts[completedDate] !== 0) {
                return;
            }
            counts[completedDate] += 1;
        });
        return counts;
    };

    const getDueTodayIncompleteTasks = (dateValue) => {
        const targetDate = dateValue || todayIso();
        return getCustomTasks().filter((item) => String(item.dueDate) === targetDate && !item.completed);
    };

    const getOverdueCustomTasks = (currentTime) => {
        const now = currentTime instanceof Date ? currentTime : new Date(currentTime || Date.now());
        return getCustomTasks().filter((item) => {
            if (item.completed || !item.dueDate) {
                return false;
            }
            const dueBoundary = new Date(`${String(item.dueDate)}T23:59:59`);
            if (Number.isNaN(dueBoundary.getTime())) {
                return false;
            }
            return dueBoundary.getTime() < now.getTime();
        });
    };

    const getFocusSessions = () => {
        const items = loadJson(STORAGE_KEYS.focusSessions, []);
        return Array.isArray(items) ? items : [];
    };

    const syncFocusSession = (entry) => {
        const payload = JSON.stringify({
            minutes: Math.max(Number(entry.minutes || 0), 0),
            date: String(entry.date || todayIso()),
        });
        if (navigator.sendBeacon) {
            const blob = new Blob([payload], { type: 'application/json' });
            if (navigator.sendBeacon(FOCUS_SYNC_URL, blob)) {
                return;
            }
        }
        fetch(FOCUS_SYNC_URL, {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: payload,
        }).catch((error) => console.error('Failed to sync focus session', error));
    };

    const logFocusSession = (entry) => {
        const minutes = Math.max(0, Math.round(Number(entry.minutes || 0)));
        if (!minutes) {
            return null;
        }
        const items = getFocusSessions();
        const payload = {
            id: entry.id || uniqueId('focus'),
            task: String(entry.task || '').trim() || 'Deep Work Session',
            minutes,
            date: String(entry.date || todayIso()),
            startedAt: entry.startedAt || nowIso(),
            endedAt: entry.endedAt || nowIso(),
            hour: Number.isFinite(Number(entry.hour)) ? Number(entry.hour) : new Date().getHours(),
        };
        items.push(payload);
        saveJson(STORAGE_KEYS.focusSessions, items);
        syncFocusSession(payload);
        window.dispatchEvent(new CustomEvent('disciplineai:focus-session-logged', { detail: payload }));
        return payload;
    };

    const getDailyFocusMinutes = (days) => {
        const dates = lastNDates(days);
        const counts = Object.fromEntries(dates.map((date) => [date, 0]));
        getFocusSessions().forEach((session) => {
            if (!Object.prototype.hasOwnProperty.call(counts, session.date)) {
                return;
            }
            counts[session.date] += Math.max(Number(session.minutes || 0), 0);
        });
        return {
            dates,
            counts,
        };
    };

    const setCurrentFocusTask = (taskName) => {
        try {
            window.localStorage.setItem(STORAGE_KEYS.currentFocusTask, String(taskName || '').trim());
        } catch (error) {
            console.error('Failed to set current focus task', error);
        }
    };

    const getCurrentFocusTask = () => {
        try {
            return String(window.localStorage.getItem(STORAGE_KEYS.currentFocusTask) || '').trim();
        } catch (error) {
            console.error('Failed to read current focus task', error);
            return '';
        }
    };

    const loadHabitEntries = () => {
        const entries = loadJson(STORAGE_KEYS.habitEntries, {});
        return entries && typeof entries === 'object' ? entries : {};
    };

    const saveHabitEntries = (entries) => {
        saveJson(STORAGE_KEYS.habitEntries, entries);
    };

    const habitKey = (dateValue, habitName) => `${dateValue}::${String(habitName || '').trim().toLowerCase()}`;

    const getHabitEntry = (dateValue, habitName) => {
        const entries = loadHabitEntries();
        return Boolean(entries[habitKey(dateValue, habitName)]);
    };

    const setHabitEntry = (dateValue, habitName, completed) => {
        const entries = loadHabitEntries();
        const key = habitKey(dateValue, habitName);
        entries[key] = Boolean(completed);
        saveHabitEntries(entries);
        return entries[key];
    };

    const getHabitCompletionCounts = (dates, habits) => {
        const entries = loadHabitEntries();
        let completed = 0;
        let pending = 0;
        dates.forEach((dateValue) => {
            habits.forEach((habitName) => {
                if (entries[habitKey(dateValue, habitName)]) {
                    completed += 1;
                } else {
                    pending += 1;
                }
            });
        });
        return { completed, pending };
    };

    const getProductiveTimeOfDay = () => {
        const buckets = {
            Morning: 0,
            Afternoon: 0,
            Evening: 0,
        };
        getFocusSessions().forEach((session) => {
            const hour = Number(session.hour);
            if (hour < 12) {
                buckets.Morning += 1;
            } else if (hour < 18) {
                buckets.Afternoon += 1;
            } else {
                buckets.Evening += 1;
            }
        });
        return Object.entries(buckets).sort((left, right) => right[1] - left[1])[0][0];
    };

    const getWeekDates = (anchorDate) => {
        const base = anchorDate ? new Date(anchorDate) : new Date();
        base.setHours(0, 0, 0, 0);
        const day = base.getDay();
        const diff = day === 0 ? -6 : 1 - day;
        base.setDate(base.getDate() + diff);
        return Array.from({ length: 7 }, (_, index) => {
            const dateValue = new Date(base);
            dateValue.setDate(base.getDate() + index);
            return {
                iso: localDateString(dateValue),
                label: dateValue.toLocaleDateString(undefined, { weekday: 'short' }),
                day: String(dateValue.getDate()).padStart(2, '0'),
            };
        });
    };

    const formatMinutes = (minutes) => {
        const value = Math.max(Math.round(Number(minutes || 0)), 0);
        const hours = Math.floor(value / 60);
        const remainder = value % 60;
        if (!hours) {
            return `${remainder}m`;
        }
        if (!remainder) {
            return `${hours}h`;
        }
        return `${hours}h ${remainder}m`;
    };

    const store = {
        todayIso,
        localDateString,
        lastNDates,
        getCustomTasks,
        addCustomTask,
        updateCustomTask,
        toggleCustomTask,
        getCompletedCustomTaskCountByDates,
        getDueTodayIncompleteTasks,
        getOverdueCustomTasks,
        getFocusSessions,
        logFocusSession,
        getDailyFocusMinutes,
        setCurrentFocusTask,
        getCurrentFocusTask,
        getHabitEntry,
        setHabitEntry,
        getHabitCompletionCounts,
        getProductiveTimeOfDay,
        getWeekDates,
        formatMinutes,
    };

    const COMMANDS = [
        { label: 'Start Focus', path: '/focus', hint: 'Open timer' },
        { label: 'Add Task', path: '/tasks/new', hint: 'Create task' },
        { label: 'View Reports', path: '/reports', hint: 'View analytics' },
        { label: 'Open Habits', path: '/habits', hint: 'Weekly tracker' },
        { label: 'Go to Dashboard', path: '/dashboard', hint: 'Overview' },
    ];

    const ensureCommandPalette = () => {
        if (document.getElementById('commandPaletteOverlay')) {
            return;
        }

        const overlay = document.createElement('div');
        overlay.id = 'commandPaletteOverlay';
        overlay.className = 'command-palette-overlay';
        overlay.innerHTML = `
            <div class="command-palette-shell">
                <input id="commandPaletteInput" class="command-palette-input" type="text" placeholder="Search commands">
                <div id="commandPaletteList" class="command-palette-list"></div>
            </div>
        `;
        document.body.appendChild(overlay);

        overlay.addEventListener('click', (event) => {
            if (event.target === overlay) {
                overlay.classList.remove('is-open');
            }
        });
    };

    const renderCommands = (commands, activeIndex) => {
        const listNode = document.getElementById('commandPaletteList');
        if (!listNode) {
            return;
        }
        listNode.innerHTML = '';
        commands.forEach((command, index) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = `command-palette-item${index === activeIndex ? ' is-active' : ''}`;
            button.innerHTML = `<span>${command.label}</span><span>${command.hint}</span>`;
            button.addEventListener('click', () => {
                window.location.href = command.path;
            });
            listNode.appendChild(button);
        });
    };

    const initCommandPalette = () => {
        ensureCommandPalette();
        const overlay = document.getElementById('commandPaletteOverlay');
        const input = document.getElementById('commandPaletteInput');
        if (!overlay || !input) {
            return;
        }

        let filtered = COMMANDS.slice();
        let activeIndex = 0;

        const refresh = () => {
            renderCommands(filtered, activeIndex);
        };

        const open = () => {
            filtered = COMMANDS.slice();
            activeIndex = 0;
            input.value = '';
            overlay.classList.add('is-open');
            refresh();
            window.setTimeout(() => input.focus(), 0);
        };

        const close = () => {
            overlay.classList.remove('is-open');
            input.blur();
        };

        input.addEventListener('input', () => {
            const query = input.value.trim().toLowerCase();
            filtered = COMMANDS.filter((command) => (
                command.label.toLowerCase().includes(query) || command.hint.toLowerCase().includes(query)
            ));
            activeIndex = 0;
            refresh();
        });

        input.addEventListener('keydown', (event) => {
            if (event.key === 'ArrowDown') {
                event.preventDefault();
                activeIndex = Math.min(activeIndex + 1, Math.max(filtered.length - 1, 0));
                refresh();
            } else if (event.key === 'ArrowUp') {
                event.preventDefault();
                activeIndex = Math.max(activeIndex - 1, 0);
                refresh();
            } else if (event.key === 'Enter') {
                event.preventDefault();
                const target = filtered[activeIndex];
                if (target) {
                    window.location.href = target.path;
                }
            } else if (event.key === 'Escape') {
                event.preventDefault();
                close();
            }
        });

        document.addEventListener('keydown', (event) => {
            const target = event.target;
            const typing = target instanceof HTMLElement && (
                target.tagName === 'INPUT' ||
                target.tagName === 'TEXTAREA' ||
                target.isContentEditable
            );
            if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
                event.preventDefault();
                if (overlay.classList.contains('is-open')) {
                    close();
                } else {
                    open();
                }
            } else if (event.key === 'Escape' && overlay.classList.contains('is-open') && !typing) {
                close();
            }
        });

        document.querySelectorAll('[data-open-command-palette]').forEach((node) => {
            node.addEventListener('click', (event) => {
                event.preventDefault();
                open();
            });
        });

        refresh();
    };

    window.DisciplineAIStore = store;
    window.DisciplineAIUI = {
        initCommandPalette,
    };

    document.addEventListener('DOMContentLoaded', initCommandPalette);
})();
