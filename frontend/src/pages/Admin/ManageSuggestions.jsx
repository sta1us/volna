import React, { useEffect, useState } from "react";
import api from "../../api";
import { useNavigate } from "react-router-dom";
import {
  Check,
  X,
  Trash2,
  MessageSquare,
  Eye,
  Clock,
  ArrowLeft,
} from "lucide-react";

const ManageSuggestions = () => {
  const [suggestions, setSuggestions] = useState([]);
  const [viewAll, setViewAll] = useState(false); // Режим: только PENDING или ВСЕ
  const navigate = useNavigate();

  const fetchSuggestions = async () => {
    try {
      // Если viewAll = false, фильтруем на фронте или бэкенде.
      // /suggestions возвращает список.
      const res = await api.get("/suggestions/");
      setSuggestions(res.data);
    } catch (err) {
      console.error("Ошибка загрузки отзывов", err);
    }
  };

  useEffect(() => {
    fetchSuggestions();
  }, [viewAll]);

  const updateStatus = async (id, newStatus) => {
    try {
      // Используем твою ручку /suggestions/{id}/status
      await api.patch(`/suggestions/${id}/status`, { status: newStatus });
      fetchSuggestions(); // Обновляем список
    } catch (err) {
      alert("Не удалось обновить статус");
    }
  };

  const deleteSuggestion = async (id) => {
    if (window.confirm("Удалить предложение безвозвратно?")) {
      try {
        await api.delete(`/suggestion/${id}`);
        setSuggestions(suggestions.filter((r) => r.id !== id));
      } catch (err) {
        alert("Ошибка при удалении");
      }
    }
  };

  // Фильтруем отзывы для отображения
  const displayedSuggestions = viewAll
    ? suggestions
    : suggestions.filter((r) => r.status === "pending");

  return (
    <div className="p-6 pb-24 bg-slate-50 min-h-screen">
      <div className="flex items-center justify-between mb-8">
        <button
          onClick={() => navigate("/admin")}
          className="p-2 bg-white rounded-xl shadow-sm"
        >
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <MessageSquare className="text-indigo-600" />
          {viewAll ? "Все идеи" : "Новые идеи"}
        </h1>
        <button
          onClick={() => setViewAll(!viewAll)}
          className="flex items-center gap-2 text-sm font-bold bg-white px-4 py-2 rounded-xl shadow-sm border border-slate-100"
        >
          {viewAll ? <Clock size={18} /> : <Eye size={18} />}
          {viewAll ? "Нужны проверки" : "Показать все"}
        </button>
      </div>

      <div className="space-y-4">
        {displayedSuggestions.map((suggestion) => (
          <div
            key={suggestion.id}
            className="bg-white p-5 rounded-3xl border border-slate-100 shadow-sm"
          >
            <div className="flex justify-between items-start mb-3">
              <div>
                <p className="font-bold text-slate-800">
                  {suggestion.guest_name || `Юзер #${suggestion.user_id}`}
                </p>
                <p className="text-[10px] text-slate-400 uppercase tracking-widest">
                  {new Date(suggestion.created_at).toLocaleDateString()}
                </p>
              </div>
              <StatusBadge status={suggestion.status} />
            </div>

            <p className="text-slate-600 text-sm italic mb-5 leading-relaxed">
              «{suggestion.text}»
            </p>

            <div className="flex gap-2">
              {/* Кнопки управления статусом */}
              {suggestion.status !== "planned" && (
                <button
                  onClick={() => updateStatus(suggestion.id, "planned")}
                  className="flex-1 bg-emerald-50 text-emerald-600 py-3 rounded-2xl font-bold text-xs flex items-center justify-center gap-1"
                >
                  <Check size={14} /> Добавить в планы
                </button>
              )}

              {suggestion.status !== "rejected" && (
                <button
                  onClick={() => updateStatus(suggestion.id, "rejected")}
                  className="flex-1 bg-amber-50 text-amber-600 py-3 rounded-2xl font-bold text-xs flex items-center justify-center gap-1"
                >
                  <X size={14} /> Отклонить
                </button>
              )}

              <button
                onClick={() => deleteSuggestion(suggestion.id)}
                className="bg-rose-50 text-rose-500 px-4 py-3 rounded-2xl"
              >
                <Trash2 size={18} />
              </button>
            </div>
          </div>
        ))}

        {displayedSuggestions.length === 0 && (
          <div className="text-center py-20 text-slate-400">
            {viewAll
              ? "Предложений пока нет"
              : "Все предложения рассмотрены! ✨"}
          </div>
        )}
      </div>
    </div>
  );
};

// Вспомогательный компонент для красивых статусов
const StatusBadge = ({ status }) => {
  const styles = {
    pending: "bg-indigo-100 text-indigo-600",
    approved: "bg-emerald-100 text-emerald-600",
    rejected: "bg-slate-200 text-slate-500",
  };
  const labels = { pending: "Новый", approved: "Виден", rejected: "Скрыт" };

  return (
    <span
      className={`text-[10px] font-black px-2 py-1 rounded-lg uppercase ${styles[status]}`}
    >
      {labels[status]}
    </span>
  );
};

export default ManageSuggestions;
