const API_BASE = "https://spectralvpn.ru:8000";

const getToken = () => localStorage.getItem("access_token");

const showNotification = (message, type = "success") => {
    const color = type === "success" ? "#00ffff" : "#ff5555";
    const notification = document.createElement("div");
    notification.style.cssText = `
        position: fixed; top: 20px; right: 20px; padding: 15px 25px; border-radius: 12px;
        background: rgba(0,0,0,0.95); border: 1px solid ${color}; color: ${color};
        z-index: 10000; font-weight: 500; box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 4000);
};

async function loadPanel() {
    const token = getToken();
    if (!token) {
        window.location.href = "register.html";
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/config/get_info`, {
            method: "GET",
            headers: { "X-API-KEY": token }
        });

        if (res.status === 401) {
            localStorage.removeItem("access_token");
            window.location.href = "register.html";
            return;
        }

        if (!res.ok) throw new Error("Failed to load configs");

        const data = await res.json();
        document.getElementById("userEmail").textContent = "Аккаунт активен";
        renderConfigs(data.configs || []);

    } catch (err) {
        console.error(err);
        showNotification("Ошибка загрузки данных", "error");
    }
}

function renderConfigs(configs) {
    const container = document.getElementById("urlsList");
    container.innerHTML = "";

    if (configs.length === 0) {
        container.innerHTML = `<p style="text-align:center; color:#666; padding:40px 20px;">
            У вас пока нет конфигураций.<br>Нажмите кнопку ниже, чтобы создать первую.
        </p>`;
        return;
    }

    configs.forEach(cfg => {
        const trafficGB = (cfg.bytes_used / (1024 ** 3)).toFixed(2);

        const card = document.createElement("div");
        card.className = "url-card";
        card.innerHTML = `
            <div>
                <div class="url-name">${cfg.name}</div>
                <div style="font-size:13px; color:#888; margin-top:6px;">
                    Использовано: ${trafficGB} ГБ
                </div>
            </div>
            <div class="url-actions">
                <button class="btn-copy" data-config="${cfg.config}">Скопировать ссылку</button>
                <button class="btn-delete" data-name="${cfg.name}">Удалить</button>
            </div>
        `;

        card.querySelector(".btn-copy").addEventListener("click", async () => {
            try {
                await navigator.clipboard.writeText(cfg.config);
                showNotification(`Конфиг "${cfg.name}" скопирован в буфер`);
            } catch (e) {
                showNotification("Не удалось скопировать", "error");
            }
        });

        card.querySelector(".btn-delete").addEventListener("click", async () => {
            if (!confirm(`Удалить конфигурацию "${cfg.name}"?`)) return;

            const token = getToken();
            try {
                const res = await fetch(`${API_BASE}/config/delete`, {
                    method: "DELETE",
                    headers: {
                        "X-API-KEY": token,
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ name: cfg.name })
                });

                if (res.ok) {
                    card.remove();
                    showNotification(`Конфиг "${cfg.name}" удалён`, "error");
                } else {
                    showNotification("Не удалось удалить конфиг", "error");
                }
            } catch (e) {
                showNotification("Ошибка сети", "error");
            }
        });

        container.appendChild(card);
    });
}

document.getElementById("addConfigBtn").addEventListener("click", async () => {
    const name = prompt("Введите название конфигурации (например: Телефон, Ноутбук, Рабочий):");
    if (!name || !name.trim()) return;

    const token = getToken();

    try {
        const res = await fetch(`${API_BASE}/config/add`, {
            method: "POST",
            headers: {
                "X-API-KEY": token,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ name: name.trim() })
        });

        const data = await res.json();

        if (res.ok) {
            showNotification(`Конфиг "${name}" успешно создан!`);
            loadPanel();
        } else {
            showNotification(data.detail || "Ошибка при создании конфига", "error");
        }
    } catch (e) {
        showNotification("Нет связи с сервером", "error");
    }
});

document.getElementById("deleteAccountBtn").addEventListener("click", async () => {
    if (!confirm("Вы уверены, что хотите удалить аккаунт? Это действие необратимо!")) return;

    const token = getToken();
    try {
        const res = await fetch(`${API_BASE}/user/delete`, {
            method: "DELETE",
            headers: { "X-API-KEY": token }
        });

        if (res.ok) {
            localStorage.removeItem("access_token");
            alert("Аккаунт успешно удалён.");
            window.location.href = "index.html";
        } else {
            showNotification("Не удалось удалить аккаунт", "error");
        }
    } catch (e) {
        showNotification("Ошибка сети", "error");
    }
});

document.getElementById("logoutBtn").addEventListener("click", () => {
    if (confirm("Выйти из аккаунта?")) {
        localStorage.removeItem("access_token");
        window.location.href = "index.html";
    }
});

document.addEventListener("DOMContentLoaded", loadPanel);