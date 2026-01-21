document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("registerForm");
    const submitButton = form.querySelector("button[type='submit']");

    const setError = (fieldId, message) => {
        const errorEl = document.getElementById(fieldId);
        const inputEl = errorEl.previousElementSibling;
        errorEl.textContent = message;
        errorEl.classList.add("active");
        if (inputEl) inputEl.classList.add("invalid");
    };

    const clearErrors = () => {
        form.querySelectorAll(".error").forEach(el => {
            el.textContent = "";
            el.classList.remove("active");
        });
        form.querySelectorAll(".invalid").forEach(el => el.classList.remove("invalid"));
        document.querySelector(".checkbox-container")?.classList.remove("invalid");
    };

    const sha256 = async (message) => {
        const msgBuffer = new TextEncoder().encode(message);
        const hashBuffer = await crypto.subtle.digest("SHA-256", msgBuffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, "0")).join("");
    };

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        clearErrors();

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;
        const passwordReply = document.getElementById("password_reply").value;
        const terms = document.getElementById("terms").checked;

        let hasError = false;

        if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            setError("emailError", "Введите корректный email");
            hasError = true;
        }
        if (!password || password.length < 6 || !/(?=.*[A-Za-z])(?=.*\d)/.test(password)) {
            setError("passwordError", "Минимум 6 символов, буквы + цифры");
            hasError = true;
        }
        if (password !== passwordReply) {
            setError("passwordReplyError", "Пароли не совпадают");
            hasError = true;
        }
        if (!terms) {
            setError("termsError", "Принять условия обязательно");
            document.querySelector(".checkbox-container").classList.add("invalid");
            hasError = true;
        }

        if (hasError) return;

        submitButton.disabled = true;
        submitButton.textContent = "Создаём аккаунт...";

        try {
            const passwordHash = await sha256(password);

            const response = await fetch("https://vpn.spectralvpn.ru:8500/registration", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    email: email,
                    password: passwordHash
                })
            });

            const result = await response.json();

            if (response.ok) {
                Cookies.set("user_email", email, { expires: 30, sameSite: "strict" });
                Cookies.set("user_hash", passwordHash, { expires: 30, sameSite: "strict" });

                window.location.href = "control-panel.html";
            } else {
                if (result.detail === "Email is busy.") {
                    setError("emailError", "Этот email уже зарегистрирован");
                } else {
                    setError("emailError", result.detail || "Ошибка сервера");
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