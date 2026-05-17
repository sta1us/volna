import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../api";
import { Calendar } from "lucide-react";

const Events = () => {
  const [events, setEvents] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    api
      .get("/events/")
      .then((res) => setEvents(res.data))
      .catch((err) => console.error("Ошибка загрузки событий", err));
  }, []);

  const handleRSVP = async (eventId) => {
    const token = localStorage.getItem("token");

    if (!token) {
      alert("Чтобы записаться, нужно войти через Telegram");
      navigate("/login");
      return;
    }

    try {
      // Передаем токен в заголовке, иначе бэкенд выдаст 401
      await api.post(
        `/events/${eventId}/react`,
        { status: "going" },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      alert("Вы записаны! Ждем вас.");
    } catch (err) {
      console.error(err);
      const msg = err.response?.data?.detail || "Ошибка при записи";
      alert(msg);
    }
  };

  return (
    <div className="p-4 bg-slate-50 min-h-screen pb-24">
      {" "}
      {/* pb-24 чтобы Navbar не закрывал контент */}
      <h1 className="text-2xl font-bold mb-6 text-slate-800">Афиша событий</h1>
      <div className="grid gap-6">
        {events.map((event) => (
          <div
            key={event.id}
            className="bg-white rounded-2xl shadow-sm overflow-hidden border border-slate-100"
          >
            <img
              src={`${event.image_url}`}
              className="w-full h-48 object-cover"
              alt={event.title}
            />
            <div className="p-4">
              <h2 className="text-xl font-bold text-slate-900">
                {event.title}
              </h2>
              <p className="text-slate-600 mt-2 text-sm line-clamp-3">
                {event.description}
              </p>

              <div className="mt-4 flex items-center text-slate-500 text-sm">
                <Calendar className="w-4 h-4 mr-2" />
                {new Date(event.date_time).toLocaleString("ru-RU", {
                  day: "numeric",
                  month: "long",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </div>

              <button
                onClick={() => handleRSVP(event.id)}
                className="w-full mt-6 bg-indigo-600 text-white py-3 rounded-xl font-semibold active:scale-95 transition-transform"
              >
                Я пойду
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Events;
