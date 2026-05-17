import React, { useEffect, useState } from "react";
import api from "../../api";
import Lightbox from "../../components/Lightbox";
import { useNavigate } from "react-router-dom";
import {
  MapPin,
  Mail,
  Phone,
  Clock,
  Image as ImageIcon,
  Map as MapIcon,
  LogOut,
  Send,
  Smartphone,
  Users,
  Calendar,
  Camera,
  Info,
  Film,
  ArrowRight,
  Instagram,
  Youtube,
  Menu,
  User,
  Settings,
  X,
} from "lucide-react";

import { isAdmin, getRoleFromToken } from "../../utils/auth";

const Home = () => {
  const [events, setEvents] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [team, setTeam] = useState([]);
  const [contacts, setContacts] = useState(null);
  const [activeTab, setActiveTab] = useState("entrance");
  const [media, setMedia] = useState([]);
  // Состояние для лайтбокса
  const [selectedIndex, setSelectedIndex] = useState(null);

  const [loading, setLoading] = useState(true);

  const toggleMenu = () => setIsOpen(!isOpen);

  const role = getRoleFromToken();
  const isUserAdmin = isAdmin();

  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("role");

    // Используем navigate для плавного перехода без перезагрузки всей страницы
    navigate("/");
    // Чтобы React понял, что юзер вышел и скрыл элементы, нужно обновить стейт
    window.location.reload();
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [evRes, teamRes, contactRes, mediaRes] = await Promise.all([
          api.get("/events/"),
          api.get("/team/"),
          api.get("/location/"),
          api.get("/media/gallery"),
        ]);
        console.log(evRes);
        setEvents(evRes.data);
        setTeam(teamRes.data);
        setContacts(contactRes.data);
        setMedia(mediaRes.data);
      } catch (err) {
        console.error("Ошибка загрузки данных", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const scrollTo = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  };

  // Логика заполнения: берем реальные данные и дополняем заглушками до 4 штук
  const displayItems = [...media];
  while (displayItems.length < 4) {
    displayItems.push({
      isPlaceholder: true,
      id: `empty-${displayItems.length}`,
    });
  }

  // Ограничиваем, например, 8 элементами, если фото много
  const finalItems = displayItems.slice(0, 8);

  // Функции навигации
  const handleNext = () => {
    const realMediaCount = media.length;
    setSelectedIndex((prev) => (prev + 1) % realMediaCount);
  };

  const handlePrev = () => {
    const realMediaCount = media.length;
    setSelectedIndex((prev) => (prev - 1 + realMediaCount) % realMediaCount);
  };

  // Функция для клика по ссылке в мобильном меню
  const handleNavClick = (target) => {
    setIsOpen(false); // Закрываем меню
    if (typeof target === "string") {
      scrollTo(target);
    } else {
      target(); // Если передана функция навигации
    }
  };

  return (
    <div className="bg-white text-slate-900 font-sans selection:bg-indigo-100">
      <nav className="fixed top-0 w-full bg-white/90 backdrop-blur-xl z-[100] border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          {/* Логотип */}
          <div
            className="font-black text-2xl tracking-tighter cursor-pointer flex items-center gap-2"
            onClick={() => {
              navigate("/");
              window.scrollTo(0, 0);
            }}
          >
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white text-sm">
              В
            </div>
            <span>Волна</span>
          </div>

          {/* Десктопное меню */}
          <div className="hidden md:flex items-center gap-6 text-[11px] font-black uppercase tracking-[0.2em] text-slate-500">
            <button
              onClick={() => scrollTo("main")}
              className="hover:text-indigo-600 transition-colors"
            >
              Главная
            </button>
            <button
              onClick={() => scrollTo("events")}
              className="hover:text-indigo-600 transition-colors"
            >
              Афиша
            </button>
            <button
              onClick={() => scrollTo("media")}
              className="hover:text-indigo-600 transition-colors"
            >
              Галерея
            </button>
            <button
              onClick={() => scrollTo("team")}
              className="hover:text-indigo-600 transition-colors"
            >
              Команда
            </button>
            <button
              onClick={() => scrollTo("contacts")}
              className="hover:text-indigo-600 transition-colors"
            >
              Контакты
            </button>

            <div className="h-4 w-px bg-slate-200 mx-2" />

            {isUserAdmin && (
              <button
                onClick={() => navigate("/admin")}
                className="text-indigo-600 hover:opacity-70 transition"
              >
                Админ
              </button>
            )}

            {role ? (
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-5 py-2.5 bg-slate-900 text-white rounded-2xl hover:bg-rose-600 transition-all active:scale-95 shadow-lg shadow-slate-200"
              >
                ВЫЙТИ <LogOut size={14} />
              </button>
            ) : (
              <button
                onClick={() => navigate("/login")}
                className="px-6 py-2.5 bg-indigo-600 text-white rounded-2xl hover:bg-indigo-700 transition-all active:scale-95 shadow-lg shadow-indigo-100"
              >
                ВОЙТИ
              </button>
            )}
          </div>

          {/* Кнопка бургера (только мобильный) */}
          <button
            onClick={toggleMenu}
            className="md:hidden p-3 bg-slate-50 text-slate-900 rounded-2xl active:scale-90 transition-all"
          >
            {isOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Мобильное меню (выезжающая панель) */}
        <div
          className={`
  fixed inset-0 top-0 h-screen w-full bg-white z-[150] md:hidden transition-all duration-500 ease-in-out
  ${
    isOpen
      ? "translate-x-0 opacity-100"
      : "translate-x-full opacity-0 pointer-events-none"
  }
`}
        >
          {/* Шапка внутри меню, чтобы была кнопка закрыть на том же месте */}
          <div className="flex items-center justify-between px-6 h-20 border-b border-slate-50">
            <div className="font-black text-2xl tracking-tighter">Волна</div>
            <button
              onClick={toggleMenu}
              className="p-3 bg-slate-50 text-slate-900 rounded-2xl"
            >
              <X size={24} />
            </button>
          </div>

          {/* Ссылки */}
          <div className="flex flex-col p-8 gap-6 text-3xl font-black tracking-tighter text-slate-900">
            <button
              onClick={() => handleNavClick("main")}
              className="text-left py-2 border-b border-slate-50"
            >
              Главная
            </button>
            <button
              onClick={() => handleNavClick("events")}
              className="text-left py-2 border-b border-slate-50"
            >
              Афиша
            </button>
            <button
              onClick={() => handleNavClick("media")}
              className="text-left py-2 border-b border-slate-50"
            >
              Галерея
            </button>
            <button
              onClick={() => handleNavClick("team")}
              className="text-left py-2 border-b border-slate-50"
            >
              Команда
            </button>
            <button
              onClick={() => handleNavClick("contacts")}
              className="text-left py-2 border-b border-slate-50"
            >
              Контакты
            </button>

            <div className="mt-4 flex flex-col gap-4">
              {role ? (
                <button
                  onClick={() => {
                    handleLogout();
                    setIsOpen(false);
                  }}
                  className="flex items-center justify-center gap-3 w-full py-6 bg-rose-50 text-rose-600 rounded-[2rem] text-xl font-bold"
                >
                  Выйти <LogOut size={24} />
                </button>
              ) : (
                <button
                  onClick={() => {
                    navigate("/login");
                    setIsOpen(false);
                  }}
                  className="flex items-center justify-center gap-3 w-full py-6 bg-indigo-600 text-white rounded-[2rem] text-xl font-bold shadow-xl shadow-indigo-200"
                >
                  Войти <User size={24} />
                </button>
              )}

              {isUserAdmin && (
                <button
                  onClick={() => handleNavClick(() => navigate("/admin"))}
                  className="text-center text-sm font-black uppercase tracking-widest text-indigo-400 py-4"
                >
                  Админ-панель
                </button>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* --- Навигация --- */}
      <nav className="fixed top-0 w-full bg-white/80 backdrop-blur-md z-50 border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div
            className="font-black text-xl tracking-tighter cursor-pointer"
            onClick={() => window.scrollTo(0, 0)}
          >
            Волна
            {/* ---  <img src="uploads/logo2.gif" alt="Волна" />  --- */}
          </div>
          <div className="hidden md:flex gap-8 text-sm font-bold uppercase tracking-widest text-slate-500">
            <button
              onClick={() => scrollTo("main")}
              className="hover:text-slate-900"
            >
              Главная
            </button>
            <button
              onClick={() => scrollTo("events")}
              className="hover:text-indigo-600 transition"
            >
              Афиша
            </button>
            <button
              onClick={() => scrollTo("media")}
              className="hover:text-indigo-600 transition"
            >
              Фото и видео
            </button>
            <button
              onClick={() => scrollTo("team")}
              className="hover:text-indigo-600 transition"
            >
              Наша команда
            </button>
            <button
              onClick={() => scrollTo("contacts")}
              className="hover:text-indigo-600 transition"
            >
              Контакты
            </button>
            {isUserAdmin && (
              <button
                onClick={() => navigate("/admin")}
                className="hover:text-indigo-600 transition"
              >
                Админ-панель
              </button>
            )}
            {role ? (
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-4 py-2 bg-rose-50 text-rose-600 rounded-xl font-bold hover:bg-rose-100 transition-colors"
              >
                {" "}
                <LogOut size={18} /> Выйти{" "}
              </button>
            ) : (
              <button
                onClick={() => navigate("/login")}
                className="px-4 py-2 bg-indigo-600 text-white rounded-xl font-bold"
              >
                {" "}
                Войти{" "}
              </button>
            )}
          </div>
        </div>
      </nav>

      {/* --- Геро-блок --- */}
      <section
        id="main"
        className="pt-40 pb-20 px-6 max-w-7xl mx-auto text-center md:text-left"
      >
        {/* Общий контейнер для Лого + Заголовка */}
        <div className="flex flex-col md:flex-row items-center md:items-start justify-between gap-6 mb-6">
          {/* Заголовок */}
          <h1 className="text-6xl md:text-8xl font-black tracking-tighter leading-none">
            Молодежный клуб <br />{" "}
            <span className="text-indigo-600">Волна.</span>
          </h1>

          {/* Логотип (теперь он справа от текста на десктопе) */}
          <div className="inline-block bg-slate-900 rounded-2xl overflow-hidden shrink-0">
            <div className="w-100 h-50 flex items-center justify-center">
              <img
                className="w-full h-full"
                alt="Логотип"
                src="uploads/promologo.png"
              />
            </div>
          </div>
        </div>

        <p className="text-xl md:text-2xl text-slate-500 font-medium max-w-2xl mb-8">
          Мы делаем вечеринки, концерты, фестивали и не только. Создаем смыслы и
          объединяем людей через музыку и вайб.
          <br />
          <br />
          Волна — это не просто организация мероприятий, это целая экосистема
          для творческих людей.
        </p>
      </section>

      {/* --- Бот блок --- */}
      <section
        id="botinfo"
        className="py-20 px-6 bg-indigo-600 text-white overflow-hidden"
      >
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center gap-12">
          <div className="bg-white p-4 rounded-[2rem] shadow-2xl rotate-3 hover:rotate-0 transition-transform">
            {/* Заглушка под QR */}
            <div className="w-48 h-48 bg-slate-200 flex items-center justify-center text-slate-400">
              <img
                className="w-full h-full object-cover"
                alt=""
                src="uploads/qrcode.jpg"
              />
            </div>
          </div>
          <div>
            <h2 className="text-4xl md:text-6xl font-black mb-4">
              Есть вопросы?
            </h2>
            <p className="text-2xl font-bold opacity-90">
              Задай их нашему чат-боту!
            </p>
            <a
              href="https://t.me/volnaufa_bot"
              className="mt-8 inline-flex items-center gap-3 bg-white text-indigo-600 px-8 py-4 rounded-2xl font-black hover:bg-slate-100 transition shadow-lg"
            >
              <Smartphone size={20} /> ПЕРЕЙТИ В TELEGRAM
            </a>
          </div>
        </div>
      </section>

      {/* --- Афиша (Events) --- */}
      <section id="events" className="py-24 px-6 max-w-7xl mx-auto">
        <div className="flex justify-between items-end mb-12">
          <h2 className="text-5xl font-black tracking-tight">Афиша</h2>
          <Calendar className="text-slate-200" size={60} />
        </div>

        <div className="flex overflow-x-auto gap-6 pb-8 snap-x no-scrollbar">
          {events.length > 0 ? (
            events.map((event) => (
              <div
                key={event.id}
                className="min-w-[320px] md:min-w-[400px] snap-start cursor-pointer"
                onClick={() => navigate(`/events/${event.id}`)}
              >
                <div className="bg-white rounded-[2.5rem] overflow-hidden border border-slate-100 shadow-sm hover:shadow-xl transition-all group">
                  <div className="h-64 bg-slate-200 relative">
                    {event.image_path && (
                      <img
                        src={event.image_path}
                        className="w-full h-full object-cover"
                        alt=""
                      />
                    )}
                    <div className="absolute top-4 left-4 bg-white/90 backdrop-blur px-4 py-1 rounded-full text-xs font-black uppercase tracking-widest">
                      {new Date(event.date_time).toLocaleDateString()}
                    </div>
                  </div>
                  <div className="p-8">
                    <h3 className="text-2xl font-black mb-2">{event.title}</h3>
                    <p className="text-slate-500 text-sm mb-6 line-clamp-2">
                      {event.description}
                    </p>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <p className="text-slate-400 italic">Событий пока нет...</p>
          )}
        </div>
      </section>

      {/* --- Фото и Видео --- */}
      <section id="media" className="py-24 px-6 bg-slate-900 text-white">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-5xl font-black mb-12 flex items-center gap-4">
            Медиа <Camera size={40} className="text-indigo-500" />
          </h2>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {displayItems.map((item, index) => (
              <div
                key={item.id || index}
                onClick={() => !item.isPlaceholder && setSelectedIndex(index)}
                className={`aspect-square bg-slate-800 rounded-3xl overflow-hidden flex items-center justify-center group relative ${
                  !item.isPlaceholder ? "cursor-pointer" : ""
                }`}
              >
                {!item.isPlaceholder ? (
                  <>
                    {item.media_type === "video" ? (
                      <div className="w-full h-full relative">
                        <video
                          src={`${item.file_path}`}
                          className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-all"
                          muted
                          playsInline
                        />
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className="bg-black/20 backdrop-blur-md p-3 rounded-full text-white group-hover:scale-110 transition-transform">
                            <Film size={24} />
                          </div>
                        </div>
                      </div> /* <-- закрывает relative контейнер видео */
                    ) : (
                      <img
                        src={`${item.file_path}`}
                        className="w-full h-full object-cover opacity-80 group-hover:opacity-100 group-hover:scale-105 transition-all duration-500"
                        alt="Gallery item"
                      />
                    )}
                  </> /* <-- Фрагмент закрывается здесь */
                ) : (
                  <span className="text-slate-600 italic font-medium">
                    Coming Soon
                  </span>
                )}
              </div> /* <-- Главный контейнер карточки */
            ))}
          </div>
        </div>

        {/* Рендерим лайтбокс, если индекс не null */}
        {selectedIndex !== null && (
          <Lightbox
            items={media}
            currentIndex={selectedIndex}
            onClose={() => setSelectedIndex(null)}
            onNext={handleNext}
            onPrev={handlePrev}
          />
        )}
      </section>

      {/* --- Команда --- */}
      <section id="team" className="py-24 px-6 max-w-7xl mx-auto">
        <h2 className="text-5xl font-black mb-12">Команда</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-12">
          {team.map((member) => (
            <div key={member.id} className="text-center group">
              <div className="w-40 h-40 mx-auto bg-slate-100 rounded-full mb-4 overflow-hidden grayscale group-hover:grayscale-0 transition-all">
                {member.image_path ? (
                  <img
                    src={member.image_path}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <Users size={40} className="text-slate-300" />
                  </div>
                )}
              </div>
              <h4 className="font-black text-lg">
                {member.first_name} {member.last_name}
              </h4>
              <p className="text-indigo-600 text-xs font-bold uppercase tracking-widest">
                {member.role}
              </p>
            </div>
          ))}
        </div>
      </section>

      <section
        id="contacts"
        className="py-24 bg-slate-950 text-slate-100 w-full"
      >
        <div className="max-w-7xl mx-auto px-6 grid md:grid-cols-2 gap-16 md:gap-24 items-center">
          {/* ЛЕВАЯ СТОРОНА: Контакты */}
          <div>
            <div className="h-2 w-16 bg-indigo-500 rounded-full mb-6 shadow-lg shadow-indigo-500/40" />
            <h2 className="text-5xl font-black mb-12 text-white tracking-tight">
              Контакты
            </h2>

            <div className="space-y-8">
              {contacts ? (
                <>
                  {/* Адрес */}
                  <div className="flex gap-5 items-start">
                    <div className="p-4 bg-slate-900 border border-slate-800 rounded-2xl text-indigo-400 shrink-0 shadow-xl">
                      <MapPin size={24} />
                    </div>
                    <div>
                      <p className="text-xs font-black text-slate-500 uppercase tracking-widest mb-1.5">
                        Где мы
                      </p>
                      <p className="text-xl font-bold text-slate-200 leading-snug tracking-tight">
                        {contacts.address}
                      </p>
                      {contacts.latitude && contacts.longitude && (
                        <a
                          href={`https://www.google.com/maps/search/?api=1&query=${contacts.latitude},${contacts.longitude}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-block text-xs font-black uppercase tracking-wider text-indigo-400 hover:text-indigo-300 mt-2.5 transition-colors"
                        >
                          Открыть карту →
                        </a>
                      )}
                    </div>
                  </div>

                  {/* Режим работы */}
                  {contacts.working_hours && (
                    <div className="flex gap-5 items-start">
                      <div className="p-4 bg-slate-900 border border-slate-800 rounded-2xl text-indigo-400 shrink-0 shadow-xl">
                        <Clock size={24} />
                      </div>
                      <div>
                        <p className="text-xs font-black text-slate-500 uppercase tracking-widest mb-1.5">
                          Часы работы
                        </p>
                        <p className="text-xl font-bold text-slate-200 whitespace-pre-wrap leading-snug tracking-tight">
                          {contacts.working_hours}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Связь: Телефон и Почта */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-6 border-t border-slate-900">
                    {contacts.phone && (
                      <div className="flex gap-4 items-center">
                        <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl text-slate-400 shrink-0">
                          <Phone size={18} />
                        </div>
                        <div>
                          <p className="text-[10px] font-black text-slate-500 uppercase tracking-wider mb-0.5">
                            Телефон
                          </p>
                          <a
                            href={`tel:${contacts.phone}`}
                            className="text-base font-bold text-slate-200 hover:text-indigo-400 transition-colors"
                          >
                            {contacts.phone}
                          </a>
                        </div>
                      </div>
                    )}

                    {contacts.email && (
                      <div className="flex gap-4 items-center">
                        <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl text-slate-400 shrink-0">
                          <Mail size={18} />
                        </div>
                        <div>
                          <p className="text-[10px] font-black text-slate-500 uppercase tracking-wider mb-0.5">
                            Почта
                          </p>
                          <a
                            href={`mailto:${contacts.email}`}
                            className="text-base font-bold text-slate-200 hover:text-indigo-400 transition-colors"
                          >
                            {contacts.email}
                          </a>
                        </div>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <div className="flex flex-col gap-4 animate-pulse">
                  <div className="h-16 bg-slate-900 rounded-2xl w-3/4" />
                  <div className="h-16 bg-slate-900 rounded-2xl w-1/2" />
                </div>
              )}
            </div>
          </div>

          {/* ПРАВАЯ СТОРОНА: Медиа-контейнер */}
          {contacts && (contacts.image_path || contacts.map_image_path) ? (
            <div className="relative w-full aspect-square md:aspect-[4/3] bg-slate-900 rounded-[3rem] overflow-hidden group border border-slate-800/80 shadow-2xl shadow-indigo-500/[0.02]">
              <div className="w-full h-full relative overflow-hidden">
                {activeTab === "entrance" && contacts.image_path && (
                  <img
                    src={
                      contacts.image_path.startsWith("http")
                        ? contacts.image_path
                        : `/${contacts.image_path}`
                    }
                    alt="Вход"
                    className="w-full h-full object-cover opacity-85 group-hover:opacity-100 transition-opacity duration-500 animate-in fade-in zoom-in-95"
                  />
                )}
                {activeTab === "map" && contacts.map_image_path && (
                  <img
                    src={
                      contacts.map_image_path.startsWith("http")
                        ? contacts.map_image_path
                        : `/${contacts.map_image_path}`
                    }
                    alt="Карта проезда"
                    className="w-full h-full object-cover opacity-85 group-hover:opacity-100 transition-opacity duration-500 animate-in fade-in zoom-in-95"
                  />
                )}
              </div>

              {/* Вкладки переключения поверх картинки */}
              <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-slate-950/80 backdrop-blur-xl p-1.5 rounded-2xl flex gap-1 border border-slate-800/60 shadow-2xl">
                {contacts.image_path && (
                  <button
                    onClick={() => setActiveTab("entrance")}
                    className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-black uppercase tracking-wider transition-all cursor-pointer ${
                      activeTab === "entrance"
                        ? "bg-white text-slate-950 shadow-md"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    <ImageIcon size={14} /> Вход
                  </button>
                )}
                {contacts.map_image_path && (
                  <button
                    onClick={() => setActiveTab("map")}
                    className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-black uppercase tracking-wider transition-all cursor-pointer ${
                      activeTab === "map"
                        ? "bg-white text-slate-950 shadow-md"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    <MapIcon size={14} /> Схема
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="w-full aspect-square md:aspect-[4/3] bg-slate-900 border-2 border-dashed border-slate-800 rounded-[3rem] flex items-center justify-center text-slate-600 font-black uppercase tracking-widest text-xs">
              Медиа материалы отсутствуют
            </div>
          )}
        </div>
      </section>

      {/* --- Отзывы и предложения --- */}

      <section id="feedback" className="py-24 px-6 max-w-7xl mx-auto">
        <div className="grid md:grid-cols-2 gap-8">
          {/* Отзывы */}
          <div className="bg-slate-50 p-12 rounded-[4rem] flex flex-col justify-between items-start border border-slate-100 hover:shadow-xl transition-all duration-500">
            <div>
              <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center text-indigo-500 mb-8 shadow-sm">
                <ImageIcon size={24} />
              </div>
              <h3 className="text-3xl font-black mb-4">Обратная связь</h3>
              <p className="text-slate-500 font-medium mb-10 leading-relaxed">
                Расскажите о своих впечатлениях. Ваш отзыв появится на сайте
                после модерации.
              </p>
            </div>
            <button
              onClick={() => navigate("/reviews")}
              className="group flex items-center gap-3 bg-white px-8 py-5 rounded-3xl font-black text-xs tracking-widest shadow-sm hover:bg-slate-900 hover:text-white transition-all active:scale-95"
            >
              ОСТАВИТЬ ОТЗЫВ{" "}
              <ArrowRight
                size={18}
                className="group-hover:translate-x-1 transition-transform"
              />
            </button>
          </div>

          {/* Предложения */}
          <div className="bg-indigo-600 p-12 rounded-[4rem] flex flex-col justify-between items-start text-white hover:shadow-2xl hover:shadow-indigo-200 transition-all duration-500">
            <div>
              <div className="w-12 h-12 bg-white/10 rounded-2xl flex items-center justify-center text-white mb-8">
                <MapIcon size={24} />
              </div>
              <h3 className="text-3xl font-black mb-4">Предложения</h3>
              <p className="text-indigo-100 font-medium mb-10 leading-relaxed">
                Есть идеи, как сделать нас лучше? Мы внимательно изучаем каждое
                предложение.
              </p>
            </div>
            <button
              onClick={() => navigate("/suggestions")}
              className="group flex items-center gap-3 bg-white px-8 py-5 rounded-3xl font-black text-xs tracking-widest text-indigo-600 shadow-xl hover:bg-slate-900 hover:text-white transition-all active:scale-95"
            >
              ОСТАВИТЬ ПРЕДЛОЖЕНИЕ{" "}
              <ArrowRight
                size={18}
                className="group-hover:translate-x-1 transition-transform"
              />
            </button>
          </div>
        </div>
      </section>

      {/* --- Подвал (Footer) --- */}
      <footer className="bg-white pt-32 pb-12 px-6 border-t border-slate-100">
        <div className="max-w-7xl mx-auto">
          {/* Верхняя часть: Контакты и Навигация */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-16 mb-20">
            {/* Лого и Телефон (5 колонок) */}
            <div className="lg:col-span-5 space-y-8">
              <div className="text-2xl font-black tracking-tighter text-slate-900">
                МОЛОДЕЖНЫЙ КЛУБ <span className="text-indigo-600">ВОЛНА</span>
              </div>
              <a
                href={`tel:${contacts?.phone}`}
                className="block text-4xl md:text-5xl font-black tracking-tighter text-slate-900 hover:text-indigo-600 transition-colors"
              >
                {contacts?.phone || "+7 (999) 000-00-00"}
              </a>
              <p className="text-slate-400 font-medium max-w-xs text-sm leading-relaxed">
                Создаем пространство для творчества, общения и развития молодежи
                в нашем городе.
              </p>
            </div>

            {/* Навигация (4 колонки) */}
            <div className="lg:col-span-4">
              <p className="text-[10px] font-black uppercase tracking-[0.2em] text-indigo-600 mb-8">
                Навигация
              </p>
              <div className="grid grid-cols-2 gap-y-4 gap-x-8">
                {[
                  { id: "main", label: "Главная" },
                  { id: "events", label: "Афиша" },
                  { id: "media", label: "Галерея" },
                  { id: "team", label: "Команда" },
                  { id: "contacts", label: "Контакты" },
                  { id: "reviews", label: "Отзывы" },
                ].map((item) => (
                  <button
                    key={item.id}
                    onClick={() => scrollTo(item.id)}
                    className="text-left text-sm font-bold text-slate-500 hover:text-slate-900 transition-colors flex items-center group"
                  >
                    <span className="w-0 group-hover:w-4 h-[2px] bg-indigo-600 transition-all mr-0 group-hover:mr-2"></span>
                    {item.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Соцсети (3 колонки) */}
            <div className="lg:col-span-3 flex flex-col items-start lg:items-end">
              <p className="text-[10px] font-black uppercase tracking-[0.2em] text-indigo-600 mb-8">
                Мы в сети
              </p>
              <div className="flex gap-4">
                <a
                  href="https://t.me/volnaufa_bot"
                  className="p-4 bg-slate-50 text-slate-600 rounded-2xl hover:bg-indigo-600 hover:text-white transition-all duration-300"
                >
                  <Send size={20} />
                </a>
                <a
                  href="#"
                  className="p-4 bg-slate-50 text-slate-600 rounded-2xl hover:bg-rose-500 hover:text-white transition-all duration-300"
                >
                  <Instagram size={20} />
                </a>
                <a
                  href="#"
                  className="p-4 bg-slate-50 text-slate-600 rounded-2xl hover:bg-red-600 hover:text-white transition-all duration-300"
                >
                  <Youtube size={20} />
                </a>
              </div>
            </div>
          </div>

          {/* Нижняя часть: Копирайт и Telegram-баннер */}
          <div className="pt-10 border-t border-slate-50 flex flex-col md:flex-row justify-between items-center gap-8">
            {/* Кнопка Telegram более компактная */}
            <a href="https://t.me/volnaufa_bot" className="group relative">
              <div className="absolute inset-0 bg-indigo-600 blur-xl opacity-20 group-hover:opacity-40 transition-opacity" />
              <div className="relative flex items-center gap-3 bg-indigo-600 text-white px-8 py-4 rounded-2xl font-black text-xs tracking-widest group-hover:translate-y-[-2px] transition-transform shadow-xl shadow-indigo-600/20">
                ПОДПИСАТЬСЯ НА TELEGRAM <Send size={16} />
              </div>
            </a>

            <div className="text-right">
              <p className="text-[10px] text-slate-400 font-bold uppercase tracking-[0.3em]">
                © 2026 VOLNA YOUTH CLUB
              </p>
              <p className="text-[9px] text-slate-300 font-bold uppercase tracking-[0.2em] mt-1">
                Developed with ♡ for the youth
              </p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Home;
