import React, { useEffect, useState } from "react";
import api from "../../api";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Users,
  ChevronDown,
  ChevronUp,
  CheckCircle,
  XCircle,
  HelpCircle,
} from "lucide-react";

const AdminStats = () => {
  const [stats, setStats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedEvent, setExpandedEvent] = useState(null); // ID раскрытого события
  const navigate = useNavigate();

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await api.get("/stats/events-current");
        setStats(res.data);
      } catch (err) {
        console.error("Ошибка загрузки статистики", err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  const toggleEvent = (id) => {
    setExpandedEvent(expandedEvent === id ? null : id);
  };

  if (loading)
    return (
      <div className="p-10 text-center animate-pulse text-slate-400">
        Загружаем данные участников...
      </div>
    );

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-start gap-5 mb-10">
        {/* Кнопка "Назад" - слева */}
        <button
          onClick={() => navigate("/admin")}
          className="mt-1 p-2.5 bg-white rounded-2xl shadow-sm hover:bg-slate-50 transition-all border border-slate-100 text-slate-600 hover:text-indigo-600"
        >
          <ArrowLeft size={22} />
        </button>

        {/* Правая часть: Заголовок и описание друг под другом */}
        <div className="flex flex-col">
          <h1 className="text-3xl font-black flex items-center gap-3 text-slate-900 leading-tight">
            <Users className="text-indigo-600" size={32} />
            Статистика по событиям
          </h1>
          <p className="text-slate-500 mt-1 font-medium">
            Списки участников и их решения в реальном времени
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {stats.map((event) => (
          <div
            key={event.event_id}
            className="bg-white border border-slate-100 rounded-[2rem] shadow-sm overflow-hidden"
          >
            {/* Шапка карточки (Кликабельная) */}
            <div
              onClick={() => toggleEvent(event.event_id)}
              className="p-6 flex flex-col md:flex-row md:items-center justify-between cursor-pointer hover:bg-slate-50 transition-colors gap-4"
            >
              <h3 className="text-xl font-black text-slate-800">
                {event.event_title}
              </h3>

              <div className="flex items-center gap-4">
                <div className="flex gap-2">
                  <span className="px-3 py-1 bg-emerald-50 text-emerald-600 rounded-full text-xs font-black uppercase">
                    Идут: {event.going.count}
                  </span>
                  <span className="px-3 py-1 bg-amber-50 text-amber-600 rounded-full text-xs font-black uppercase">
                    Думают: {event.maybe.count}
                  </span>
                  <span className="px-3 py-1 bg-rose-50 text-rose-600 rounded-full text-xs font-black uppercase">
                    Нет: {event.not_going.count}
                  </span>
                </div>
                {expandedEvent === event.event_id ? (
                  <ChevronUp size={20} />
                ) : (
                  <ChevronDown size={20} />
                )}
              </div>
            </div>

            {/* Раскрывающийся список участников */}
            {expandedEvent === event.event_id && (
              <div className="px-6 pb-8 border-t border-slate-50 pt-6 animate-in slide-in-from-top-2 duration-300">
                <div className="grid md:grid-cols-3 gap-8">
                  {/* Список: ИДУТ */}
                  <UserList
                    title="Точно придут"
                    users={event.going.users}
                    icon={
                      <CheckCircle className="text-emerald-500" size={16} />
                    }
                    colorClass="text-emerald-700"
                  />

                  {/* Список: ВОЗМОЖНО */}
                  <UserList
                    title="Сомневаются"
                    users={event.maybe.users}
                    icon={<HelpCircle className="text-amber-500" size={16} />}
                    colorClass="text-amber-700"
                  />

                  {/* Список: НЕ ИДУТ */}
                  <UserList
                    title="Отменили"
                    users={event.not_going.users}
                    icon={<XCircle className="text-rose-500" size={16} />}
                    colorClass="text-rose-700"
                  />
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

// Вспомогательный компонент для отрисовки колонки пользователей
const UserList = ({ title, users, icon, colorClass }) => (
  <div>
    <h4
      className={`text-xs font-black uppercase tracking-widest mb-4 flex items-center gap-2 ${colorClass}`}
    >
      {icon} {title} ({users.length})
    </h4>
    <div className="space-y-2">
      {users.length > 0 ? (
        users.map((user) => (
          <div
            key={user.id}
            className="text-sm py-2 px-3 bg-slate-50 rounded-xl flex flex-col"
          >
            <span className="font-bold text-slate-700">
              {user.first_name} {user.last_name || ""}
            </span>
            {user.username && (
              <span className="text-[10px] text-slate-400">
                @{user.username}
              </span>
            )}
          </div>
        ))
      ) : (
        <p className="text-xs text-slate-300 italic">Спискок пуст</p>
      )}
    </div>
  </div>
);

export default AdminStats;
