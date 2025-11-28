const port = 8000;
const API_URL = "https://spectralvpn.ru:${port}";

async function sha256(text) {
    const encoder = new TextEncoder();
    const data = encoder.encode(text);
    const hash = await crypto.subtle.digest('SHA-256', data);
    return Array.from(new Uint8Array(hash))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
}

function clearErrors() {
    document.querySelectorAll('.error').forEach(el => {
        el.textContent = '';
        el.classList.remove('active');
    });
    document.querySelectorAll('.input, .checkbox').forEach(el => {
        el.classList.remove('invalid');
    });
}

function showError(fieldId, message) {
    const errorEl = document.getElementById(fieldId);
    errorEl.textContent = message;
    errorEl.classList.add('active');
    
    const input = document.getElementById(fieldId.replace('Error', ''));
    if (input) input.classList.add('invalid');
}

async function registration(e) {
    e.preventDefault();
    clearErrors();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const passwordReply = document.getElementById("password_reply").value;
    const terms = document.getElementById("terms").checked;

    let hasError = false;

    if (!email) {
        showError("emailError", "Введите email");
        hasError = true;
    } else if (!/^\S+@\S+\.\S+$/.test(email)) {
        showError("emailError", "Некорректный email");
        hasError = true;
    }

    if (!password) {
        showError("passwordError", "Введите пароль");
        hasError = true;
    } else if (password.length < 6) {
        showError("passwordError", "Пароль должен быть не менее 6 символов");
        hasError = true;
    }

    if (password !== passwordReply) {
        showError("passwordReplyError", "Пароли не совпадают");
        hasError = true;
    }

    if (!terms) {
        showError("termsError", "Необходимо принять пользовательское соглашение");
        document.getElementById("terms").classList.add('invalid');
        hasError = true;
    }

    if (hasError) return;

    const submitBtn = e.target.querySelector("button[type='submit']");
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = "Создаём аккаунт...";

    try {
        const hashedPassword = await sha256(password);

        const response = await fetch(`${API_URL}/registration`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email: email,
                password: hashedPassword
            })
        });

        const data = await response.json();

        if (response.ok) {
            setCookie("email", email, 365);
            setCookie("hash_passwd", hashedPassword, 365);
            window.location.href = "control-panel.html";

        } else {
            if (data.detail === "Email is busy.") {
                showError("emailError", "Этот email уже зарегистрирован");
            } else {
                alert("Ошибка регистрации: " + (data.detail || "Попробуйте позже"));
            }
        }
    } catch (err) {
        console.error("Registration error:", err);
        alert("Нет соединения с сервером. Проверьте интернет или попробуйте позже.");
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("registerForm");
    if (form) {
        form.addEventListener("submit", registration);
    }

    document.querySelectorAll('.input').forEach(input => {
        input.addEventListener('focus', () => {
            input.classList.remove('invalid');
            const errorId = input.id + "Error";
            const errorEl = document.getElementById(errorId);
            if (errorEl) {
                errorEl.textContent = '';
                errorEl.classList.remove('active');
            }
        });
    });
});