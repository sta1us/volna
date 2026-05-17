import React, { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../../api";
import {
  Calendar,
  Users,
  Utensils,
  MapPin,
  ArrowLeft,
  MessageSquare,
  Lightbulb,
  ChevronRight,
  Star,
  ChartColumn,
  Image,
} from "lucide-react";

const AdminDashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    events: 0,
    pendingReviews: 0,
    newSuggestions: 0,
  });

  useEffect(() => {
    api
      .get("/stats")
      .then((res) => setStats(res.data))
      .catch(() => {});
  }, []);

  const menuItems = [
    {
      title: "События",
      icon: <Calendar />,
      path: "/admin/events",
      color: "bg-indigo-500",
      desc: "Добавить афишу",
    },
    {
      title: "Команда",
      icon: <Users />,
      path: "/admin/team",
      color: "bg-emerald-500",
      desc: "Управление штатом",
    },
    {
      title: "Меню",
      icon: <Utensils />,
      path: "/admin/menu",
      color: "bg-orange-500",
      desc: "Обновить позиции",
    },
    {
      title: "Локация",
      icon: <MapPin />,
      path: "/admin/location",
      color: "bg-rose-500",
      desc: "Адрес и карта",
    },
    {
      title: "Отзывы",
      icon: <MessageSquare />,
      path: "/admin/reviews",
      color: "bg-sky-500",
      count: stats.pendingReviews,
      desc: "Модерация",
    },
    {
      title: "Пользователи",
      icon: <Users />,
      path: "/admin/users",
      color: "bg-sky-500",
      count: stats.pendingReviews,
      desc: "Список пользователей",
    },
    {
      title: "Идеи",
      icon: <Lightbulb />,
      path: "/admin/suggestions",
      color: "bg-amber-500",
      count: stats.newSuggestions,
      desc: "Банк идей",
    },
    {
      title: "Статистика",
      icon: <ChartColumn />,
      path: "/admin/stats",
      color: "bg-purple-500",
      desc: "Статистика по событиям",
    },
    {
      title: "Медиа",
      icon: <Image />,
      path: "/admin/media",
      color: "bg-blue-500",
      desc: "Загрузка медиа",
    },
  ];

  return (
    <div className="p-6 pb-24 bg-slate-50 min-h-screen">
      <div className="flex items-center gap-4 mb-8">
        {/* Кнопка будет слева от контейнера с текстом */}
        <button
          onClick={() => navigate("/")}
          className="p-2 bg-white rounded-xl shadow-sm hover:bg-gray-50 transition-colors"
        >
          <ArrowLeft size={20} />
        </button>

        {/* Группируем заголовок и текст в один блок, чтобы они шли друг под другом */}
        <header>
          <h1 className="text-3xl font-black text-slate-900">
            Администрирование
          </h1>
          <p className="text-slate-500">Добро пожаловать в админку «Волны»</p>
        </header>
      </div>

      {/* Сетка инструментов */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {menuItems.map((item, idx) => (
          <Link
            key={idx}
            to={item.path}
            className="bg-white p-5 rounded-3xl shadow-sm border border-slate-100 flex items-center justify-between active:scale-95 transition"
          >
            <div className="flex items-center">
              <div
                className={`${item.color} text-white p-3 rounded-2xl mr-4 shadow-lg`}
              >
                {item.icon}
              </div>
              <div>
                <h3 className="font-bold text-slate-800">{item.title}</h3>
                <p className="text-xs text-slate-400">{item.desc}</p>
              </div>
            </div>

            <div className="flex items-center">
              {item.count > 0 && (
                <span className="bg-red-500 text-white text-[10px] font-bold px-2 py-1 rounded-full mr-2">
                  +{item.count}
                </span>
              )}
              <ChevronRight className="text-slate-300" size={20} />
            </div>
          </Link>
        ))}
      </div>

      {/* Быстрые действия / Статус системы */}
      <div className="mt-10 bg-slate-900 rounded-3xl p-6 text-white shadow-xl">
        <div className="flex items-center mb-4">
          <Star className="text-amber-400 mr-2" size={20} fill="currentColor" />
          <h2 className="font-bold">Статус заведения</h2>
        </div>
        <p className="text-slate-400 text-sm leading-relaxed">
          Все системы работают штатно. Предложения от гостей модерируются. Не
          забывайте обновлять афишу каждую неделю!
        </p>
      </div>
    </div>
  );
};

export default AdminDashboard;
