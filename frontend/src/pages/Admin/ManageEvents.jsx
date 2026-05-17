import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../api";
import {
  CalendarPlus,
  Pencil,
  Trash2,
  ArrowLeft,
  Calendar,
  Images,
} from "lucide-react";

const ManageEvents = () => {
  const [events, setEvents] = useState([]);
  const navigate = useNavigate();

  const fetchEvents = async () => {
    try {
      const res = await api.get("/events/");
      setEvents(res.data);
    } catch (err) {
      console.error("Ошибка загрузки событий", err);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  const handleDelete = async (id) => {
    if (window.confirm("Удалить это событие из афиши?")) {
      try {
        await api.delete(`/events/${id}`);
        setEvents(events.filter((e) => e.id !== id));
      } catch (err) {
        alert("Ошибка при удалении");
      }
    }
  };

  return (
    <div className="p-6 pb-24 bg-slate-50 min-h-screen">
      <div className="flex items-center justify-between mb-8">
        <button
          onClick={() => navigate("/admin")}
          className="p-2 bg-white rounded-xl shadow-sm"
        >
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-xl font-bold">Афиша событий</h1>
        <button
          onClick={() => navigate("/admin/events/new")}
          className="bg-indigo-600 text-white p-2 rounded-xl shadow-lg"
        >
          <CalendarPlus size={20} />
        </button>
      </div>

      <div className="space-y-4">
        {events.map((event) => (
          <div
            key={event.id}
            className="bg-white p-4 rounded-3xl flex items-center shadow-sm border border-slate-100"
          >
            {/* Миниатюра афиши */}
            <div className="w-16 h-20 rounded-xl overflow-hidden bg-slate-100 mr-4">
              <img
                src={`${event.image_url}`}
                className="w-full h-full object-cover"
                alt=""
              />
            </div>

            {/* Инфо */}
            <div className="flex-1">
              <h3 className="font-bold text-slate-800 leading-tight line-clamp-1">
                {event.title}
              </h3>
              <p className="text-xs text-indigo-600 font-medium mt-1">
                {new Date(event.date_time).toLocaleDateString("ru-RU")}
              </p>
            </div>

            {/* Действия */}
            <div className="flex gap-2">
              <button
                title="Загрузить изображения"
                onClick={() => navigate(`/admin/events/media/${event.id}`)}
                className="p-3 bg-slate-50 text-purple-600 rounded-2xl cursor-pointer hover:bg-purple-600 hover:text-white transition-all duration-200"
              >
                <Images size={18} />
              </button>

              <button
                title="Редактировать событие"
                onClick={() => navigate(`/admin/events/edit/${event.id}`)}
                className="p-3 bg-slate-50 text-indigo-600 rounded-2xl cursor-pointer hover:bg-indigo-600 hover:text-white transition-all duration-200"
              >
                <Pencil size={18} />
              </button>

              <button
                title="Удалить событие"
                onClick={() => handleDelete(event.id)}
                className="p-3 bg-slate-50 text-rose-500 rounded-2xl cursor-pointer hover:bg-rose-500 hover:text-white transition-all duration-200"
              >
                <Trash2 size={18} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ManageEvents;
