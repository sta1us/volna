import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../api";

const Login = () => {
  const navigate = useNavigate();

  const handleTelegramAuth = async (user) => {
    try {
      // Отправляем данные от Telegram на наш бэкенд
      const response = await api.post("/auth/telegram", user);

      // Сохраняем токен и роль в память браузера
      localStorage.setItem("token", response.data.access_token);
      localStorage.setItem("role", response.data.role);

      // Если админ — редирект в админку, если нет — на главную
      navigate("/");
    } catch (error) {
      console.error("Ошибка авторизации", error);
      alert("Не удалось войти через Telegram");
    }
  };

  useEffect(() => {
    // Настраиваем callback для виджета
    window.onTelegramAuth = handleTelegramAuth;

    // Создаем сам скрипт кнопки (нужно заменить bot_domain и bot_name)
    const script = document.createElement("script");
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.setAttribute("data-telegram-login", "volnaufa_bot");
    script.setAttribute("data-size", "large");
    script.setAttribute("data-onauth", "onTelegramAuth(user)");
    script.setAttribute("data-request-access", "write");

    document.getElementById("telegram-login-container").appendChild(script);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-6 bg-slate-50">
      <h1 className="text-3xl font-black mb-8">VOLNA</h1>
      <p className="text-slate-500 mb-8 text-center">
        Войдите, чтобы записываться на события и оставлять отзывы
      </p>

      {/* Сюда скрипт вставит кнопку */}
      <div id="telegram-login-container"></div>
    </div>
  );
};

export default Login;
