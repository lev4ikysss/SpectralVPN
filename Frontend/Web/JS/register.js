document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("registerForm");
    const submitButton = form.querySelector("button[type='submit']");

    const setError = (fieldId, message) => {
        const errorEl = document.getElementById(fieldId);
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.classList.add("active");
        }
        const input = document.getElementById(fieldId.replace("Error", ""));
        if (input) input.classList.add("invalid");
    };

    const clearErrors = () => {
        document.querySelectorAll(".error").forEach(el => {
            el.textContent = "";
            el.classList.remove("active");
        });
        document.querySelectorAll(".input").forEach(el => el.classList.remove("invalid"));
    };

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        clearErrors();

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;
        const passwordReply = document.getElementById("password_reply").value;
        const promo_code = document.getElementById("promo_code") ? document.getElementById("promo_code").value.trim() : "";

        if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            setError("emailError", "Введите корректный email");
            return;
        }
        if (!password || password.length < 6) {
            setError("passwordError", "Пароль минимум 6 символов");
            return;
        }
        if (password !== passwordReply) {
            setError("passwordReplyError", "Пароли не совпадают");
            return;
        }

        submitButton.disabled = true;
        submitButton.textContent = "Создаём аккаунт...";

        try {
            const response = await fetch("https://spectralvpn.ru:8000/user/signup", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    email: email,
                    password: password,
                    promo_code: promo_code
                })
            });

            const result = await response.json();

            if (response.ok) {
                // Сохраняем токен
                localStorage.setItem("access_token", result.access_token);

                window.location.href = "control-panel.html";
            } else {
                if (result.detail?.includes("Promo-code")) {
                    setError("promoError", "Неверный промокод");
                } else if (result.detail?.includes("Email") || result.detail?.includes("busy")) {
                    setError("emailError", "Этот email уже используется");
                } else {
                    setError("emailError", result.detail || "Ошибка регистрации");
                }
            }
        } catch (err) {
            console.error(err);
            setError("emailError", "Нет связи с сервером");
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = "Зарегистрироваться";
        }
    });
});