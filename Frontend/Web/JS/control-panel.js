const API_BASE = "https://spectralvpn.ru:8000";

const getToken = () => localStorage.getItem("access_token");

const showNotification = (message, type = "success") => {
    const color = type === "success" ? "#00ffff" : "#ff5555";
    const notif = document.createElement("div");
    notif.style.cssText = `
        position: fixed; top: 20px; right: 20px; padding: 14px 24px; border-radius: 12px;
        background: rgba(0,0,0,0.96); border: 1px solid ${color}; color: ${color};
        z-index: 10000; font-weight: 500; box-shadow: 0 4px 20px rgba(0,0,0,0.6);
    `;
    notif.textContent = message;
    document.body.appendChild(notif);
    setTimeout(() => notif.remove(), 4500);
};

async function apiRequest(endpoint, options = {}) {
    const token = getToken();
    if (!token) {
        showLoginModal();
        return null;
    }

    const res = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers: {
            "X-API-KEY": token,
            "Content-Type": "application/json",
            ...options.headers
        }
    });

    if (res.status === 401) {
        localStorage.removeItem("access_token");
        showNotification("Сессия истекла. Войдите заново.", "error");
        showLoginModal();
        return null;
    }

    return res;
}

// Показать окно логина
function showLoginModal() {
    document.getElementById("loginModal").classList.add("active");
    document.getElementById("mainContent").classList.add("hidden");
    document.getElementById("userInfo").style.display = "none";
}

// Скрыть окно логина и показать кабинет
function hideLoginModal() {
    document.getElementById("loginModal").classList.remove("active");
    document.getElementById("mainContent").classList.remove("hidden");
    document.getElementById("userInfo").style.display = "flex";
}

async function loadPanel() {
    const token = getToken();
    if (!token) {
        showLoginModal();
        return;
    }

    const res = await apiRequest("/config/get_info", { method: "GET" });
    if (!res) return;

    if (!res.ok) {
        showNotification("Ошибка загрузки данных", "error");
        return;
    }

    const data = await res.json();
    
    document.getElementById("userEmail").textContent = data.email || "Аккаунт активен";
    hideLoginModal();           // ← Важно!
    renderConfigs(data.configs || []);
}

function renderConfigs(configs) {
    const container = document.getElementById("urlsList");
    container.innerHTML = "";

    if (configs.length === 0) {
        container.innerHTML = `<p style="text-align:center; color:#666; padding:50px 20px; font-size:15px;">
            У вас пока нет конфигураций.<br>Нажмите кнопку ниже, чтобы создать первую.
        </p>`;
        return;
    }

    configs.forEach(cfg => {
        const trafficGB = (cfg.bytes_used / (1024 ** 3)).toFixed(2);

        const card = document.createElement("div");
        card.className = "url-card";
        card.innerHTML = `
            <div class="url-info">
                <div class="url-name">${cfg.name}</div>
                <div class="traffic">Использовано: ${trafficGB} ГБ</div>
            </div>
            <div class="url-actions">
                <button class="btn btn-copy" data-config="${cfg.config}">Скопировать</button>
                <button class="btn btn-delete" data-name="${cfg.name}">Удалить</button>
            </div>
        `;

        card.querySelector(".btn-copy").addEventListener("click", async () => {
            try {
                await navigator.clipboard.writeText(cfg.config);
                showNotification(`Конфиг "${cfg.name}" скопирован`);
            } catch (e) {
                showNotification("Не удалось скопировать", "error");
            }
        });

        card.querySelector(".btn-delete").addEventListener("click", async () => {
            if (!confirm(`Удалить конфигурацию "${cfg.name}"?`)) return;

            const res = await apiRequest("/config/delete", {
                method: "DELETE",
                body: JSON.stringify({ name: cfg.name })
            });

            if (res && res.ok) {
                showNotification(`Конфиг "${cfg.name}" удалён`);
                loadPanel();
            } else {
                showNotification("Не удалось удалить конфиг", "error");
            }
        });

        container.appendChild(card);
    });
}

// ==================== ЛОГИН ====================
document.getElementById("loginSubmit").addEventListener("click", async () => {
    const email = document.getElementById("loginEmail").value.trim();
    const password = document.getElementById("loginPassword").value;
    const errorEl = document.getElementById("loginError");

    errorEl.textContent = "";

    if (!email || !password) {
        errorEl.textContent = "Введите email и пароль";
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/user/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        const data = await res.json();

        if (res.ok && data.access_token) {
            localStorage.setItem("access_token", data.access_token);
            showNotification("Вход выполнен успешно!");
            document.getElementById("loginEmail").value = "";
            document.getElementById("loginPassword").value = "";
            loadPanel();                    // ← Главное исправление
        } else {
            errorEl.textContent = data.detail || "Неверный email или пароль";
        }
    } catch (err) {
        console.error(err);
        errorEl.textContent = "Нет связи с сервером. Попробуйте позже.";
    }
});

// ==================== Создание конфига ====================
document.getElementById("addConfigBtn").addEventListener("click", () => {
    document.getElementById("addModal").classList.add("active");
    document.getElementById("configName").focus();
});

document.getElementById("addCancel").addEventListener("click", () => {
    document.getElementById("addModal").classList.remove("active");
    document.getElementById("addError").textContent = "";
});

document.getElementById("addSubmit").addEventListener("click", async () => {
    const name = document.getElementById("configName").value.trim();
    const errorEl = document.getElementById("addError");

    if (!name) {
        errorEl.textContent = "Введите название конфигурации";
        return;
    }

    const res = await apiRequest("/config/add", {
        method: "POST",
        body: JSON.stringify({ name })
    });

    if (res && res.ok) {
        showNotification(`Конфигурация "${name}" создана!`);
        document.getElementById("addModal").classList.remove("active");
        document.getElementById("configName").value = "";
        loadPanel();
    } else {
        const errData = await res.json().catch(() => ({}));
        errorEl.textContent = errData.detail || "Ошибка при создании";
    }
});

// ==================== Выход ====================
document.getElementById("logoutBtn").addEventListener("click", async () => {
    if (!confirm("Выйти из аккаунта?")) return;

    const token = getToken();
    if (token) {
        await fetch(`${API_BASE}/user/logout`, {
            method: "POST",
            headers: { "X-API-KEY": token, "Content-Type": "application/json" },
            body: JSON.stringify({ token_to_revoke: token })
        }).catch(() => {});
    }

    localStorage.removeItem("access_token");
    showLoginModal();
});

// ==================== Удаление аккаунта ====================
document.getElementById("deleteAccountBtn").addEventListener("click", async () => {
    if (!confirm("Вы уверены? Это действие необратимо!")) return;

    const res = await apiRequest("/user/delete", { method: "DELETE" });

    if (res && res.ok) {
        localStorage.removeItem("access_token");
        alert("Аккаунт успешно удалён.");
        showLoginModal();
    } else {
        showNotification("Не удалось удалить аккаунт", "error");
    }
});

// Табы "Как подключиться"
document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");

        document.querySelectorAll(".instructions").forEach(instr => instr.classList.add("hidden"));
        document.getElementById(btn.dataset.platform + "-instructions").classList.remove("hidden");
    });
});

// Закрытие модалки создания конфига кликом вне
document.getElementById("addModal").addEventListener("click", (e) => {
    if (e.target === document.getElementById("addModal")) {
        document.getElementById("addModal").classList.remove("active");
    }
});

document.addEventListener("DOMContentLoaded", loadPanel);