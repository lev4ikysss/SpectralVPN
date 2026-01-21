const API_BASE = "https://vpn.spectralvpn.ru:8500";

const getCookie = (name) => {
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? decodeURIComponent(match[2]) : null;
};

const deleteCookie = (name) => {
    document.cookie = `${name}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; Secure; SameSite=Strict`;
};

const sha256 = async (str) => {
    const buf = new TextEncoder().encode(str);
    const hash = await crypto.subtle.digest("SHA-256", buf);
    return Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2, "0")).join("");
};

const showNotification = (text, color = "cyan") => {
    const notification = document.createElement("div");
    notification.textContent = text;
    notification.style.cssText = `
        position: fixed; top: 20px; right: 20px; padding: 15px 25px; border-radius: 12px; 
        z-index: 9999; font-weight: 600; background: ${color === "cyan" ? "#00ffff22" : "#ff444422"};
        color: ${color}; border: 1px solid ${color === "cyan" ? "cyan" : "#f66"};
    `;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
};

let currentEmail = null;
let currentHash = null;

const modal = document.getElementById("loginModal");
const showModal = () => modal.classList.add("active");
const hideModal = () => modal.classList.remove("active");

const showLoginError = (msg) => {
    document.getElementById("loginError").textContent = msg;
};

const renderUrls = (urls) => {
    const container = document.getElementById("urlsList");
    container.innerHTML = "";

    if (urls.length === 0) {
        container.innerHTML = "<p style='text-align:center; color:#666;'>У вас пока нет конфигураций</p>";
        return;
    }

    urls.forEach(name => {
        const card = document.createElement("div");
        card.className = "url-card";

        card.innerHTML = `
            <div>
                <div class="url-name">${name}</div>
            </div>
            <div class="url-actions">
                <button class="btn-copy" data-name="${name}">Скопировать</button>
                <button class="btn-delete" data-name="${name}">Удалить</button>
            </div>
        `;

        card.querySelector(".btn-copy").onclick = async () => {
            try {
                const url = `${API_BASE}/get_url?email=${encodeURIComponent(currentEmail)}&password=${encodeURIComponent(currentHash)}&urls_name=${encodeURIComponent(name)}`;
                const res = await fetch(url);
                const data = await res.json();

                if (res.ok && data.url) {
                    await navigator.clipboard.writeText(data.url);
                    showNotification(`Конфиг "${name}" скопирован!`);
                } else {
                    showNotification("Ошибка получения конфига", "red");
                }
            } catch (e) {
                showNotification("Нет связи с сервером", "red");
            }
        };

        card.querySelector(".btn-delete").onclick = async () => {
            if (!confirm(`Удалить конфиг "${name}"?`)) return;

            try {
                const url = `${API_BASE}/del_url?email=${encodeURIComponent(currentEmail)}&password=${encodeURIComponent(currentHash)}&urls_name=${encodeURIComponent(name)}`;
                const res = await fetch(url, { method: "DELETE" });

                if (res.ok) {
                    card.remove();
                    showNotification(`Конфиг "${name}" удалён`, "red");
                } else {
                    showNotification("Не удалось удалить", "red");
                }
            } catch (e) {
                showNotification("Ошибка сети", "red");
            }
        };

        container.appendChild(card);
    });
};

const tryAutoLogin = async () => {
    currentEmail = getCookie("user_email");
    currentHash = getCookie("user_hash");

    if (!currentEmail || !currentHash) {
        showModal();
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: currentEmail, password: currentHash })
        });

        if (res.ok) {
            const data = await res.json();
            document.getElementById("userEmail").textContent = currentEmail;
            document.getElementById("mainContent").classList.remove("hidden");
            renderUrls(data.urls || []);
        } else {
            deleteCookie("user_email");
            deleteCookie("user_hash");
            showModal();
        }
    } catch (e) {
        showModal();
    }
};

document.getElementById("loginSubmit").onclick = async () => {
    const email = document.getElementById("loginEmail").value.trim();
    const pass = document.getElementById("loginPassword").value;

    if (!email || !pass) {
        showLoginError("Заполните все поля");
        return;
    }

    const hash = await sha256(pass);

    try {
        const res = await fetch(`${API_BASE}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password: hash })
        });

        const data = await res.json();

        if (res.ok) {
            currentEmail = email;
            currentHash = hash;
            document.cookie = `user_email=${encodeURIComponent(email)}; path=/; max-age=2592000; Secure; SameSite=Strict`;
            document.cookie = `user_hash=${hash}; path=/; max-age=2592000; Secure; SameSite=Strict`;

            document.getElementById("userEmail").textContent = email;
            hideModal();
            document.getElementById("mainContent").classList.remove("hidden");
            renderUrls(data.urls || []);
        } else {
            showLoginError("Неверный email или пароль");
        }
    } catch (e) {
        showLoginError("Ошибка подключения");
    }
};

document.getElementById("addUrlBtn").onclick = async () => {
    const name = prompt("Введите название конфигурации:");
    if (!name?.trim()) return;

    try {
        const res = await fetch(`${API_BASE}/add_url`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                email: currentEmail,
                password: currentHash,
                urls_name: name.trim()
            })
        });

        const data = await res.json();

        if (res.ok) {
            renderUrls(data.urls);
            showNotification(`Конфиг "${name}" создан! Скопируйте через кнопку.`);
        } else {
            showNotification("Ошибка: " + (data.detail || "неизвестно"), "red");
        }
    } catch (e) {
        showNotification("Нет связи с сервером", "red");
    }
};

document.getElementById("logoutBtn").onclick = () => {
    deleteCookie("user_email");
    deleteCookie("user_hash");
    location.reload();
};

document.getElementById("closeModal").onclick = hideModal;

tryAutoLogin();