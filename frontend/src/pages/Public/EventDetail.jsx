import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../../api";
import {
  Camera,
  Calendar,
  ChevronLeft,
  Film,
  CheckCircle2,
  XCircle,
  HelpCircle,
  X,
} from "lucide-react";
import Lightbox from "../../components/Lightbox"; // Убедись, что путь верный

const EventDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  // Состояния данных
  const [event, setEvent] = useState(null);
  const [media, setMedia] = useState([]);
  const [loading, setLoading] = useState(true);

  // Состояния интерфейса
  const [showThanks, setShowThanks] = useState(false);
  const [userReaction, setUserReaction] = useState(null);
  const [selectedIndex, setSelectedIndex] = useState(null);

  const isAuthenticated = !!localStorage.getItem("token");
  const API_URL = import.meta.env.VITE_API_URL || "";

  useEffect(() => {
    const fetchEventData = async () => {
      try {
        const [evRes, mediaRes] = await Promise.all([
          api.get(`/events/${id}`),
          api.get(`/media/${id}`),
        ]);
        setEvent(evRes.data);
        setMedia(mediaRes.data);
      } catch (err) {
        console.error("Ошибка загрузки события", err);
      } finally {
        setLoading(false);
      }
    };
    fetchEventData();
  }, [id]);

  const handleReaction = async (status) => {
    if (!isAuthenticated) {
      alert("Пожалуйста, авторизуйтесь через бота, чтобы отметить участие");
      return;
    }
    try {
      await api.post(`/events/${id}/react`, { status });
      setUserReaction(status.toUpperCase());
      setShowThanks(true);
      setTimeout(() => setShowThanks(false), 5000);
    } catch (err) {
      alert("Ошибка при сохранении выбора");
    }
  };

  // Подготовка айтемов для сетки (минимум 4 для красоты)
  const displayItems = [...media];
  while (displayItems.length < 4) {
    displayItems.push({
      isPlaceholder: true,
      id: `empty-${displayItems.length}`,
    });
  }

  const handleNext = () =>
    setSelectedIndex((prev) => (prev + 1) % media.length);
  const handlePrev = () =>
    setSelectedIndex((prev) => (prev - 1 + media.length) % media.length);

  if (loading)
    return (
      <div className="flex flex-col justify-center items-center h-screen bg-white">
        <div className="w-12 h-12 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mb-4"></div>
        <p className="text-slate-400 font-black uppercase tracking-widest text-xs">
          Загрузка волны...
        </p>
      </div>
    );

  if (!event)
    return <div className="p-10 text-center font-bold">Событие не найдено</div>;

  return (
    <div className="bg-slate-50 min-h-screen pb-20">
      {/* --- ГЛАВНОЕ ФОТО (HERO) --- */}
      <div className="relative h-[60vh] w-full overflow-hidden">
        <img
          src={
            event.image_path?.startsWith("http")
              ? event.image_path
              : `${API_URL}/${event.image_path}`
          }
          alt={event.title}
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-900/90 via-slate-900/20 to-transparent" />

        <div className="absolute top-8 left-6">
          <button
            onClick={() => navigate(-1)}
            className="p-4 bg-white/10 backdrop-blur-md border border-white/20 rounded-3xl text-white hover:bg-white/20 transition-all active:scale-95"
          >
            <ChevronLeft size={28} />
          </button>
        </div>

        <div className="absolute bottom-20 left-8 right-8 text-white">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 rounded-full text-[10px] font-black uppercase tracking-[0.2em] mb-6 shadow-xl shadow-indigo-600/40">
            <Calendar size={14} />
            {new Date(event.date_time).toLocaleDateString("ru-RU", {
              day: "numeric",
              month: "long",
              hour: "2-digit",
              minute: "2-digit",
            })}
          </div>
          <h1 className="text-5xl md:text-8xl font-black tracking-tighter leading-[0.9]">
            {event.title}
          </h1>
        </div>
      </div>

      {/* --- ОСНОВНОЙ КОНТЕНТ (С НАЕЗДОМ) --- */}
      <div className="max-w-5xl mx-auto px-6 -mt-12 relative z-10">
        <div className="bg-white rounded-[3.5rem] shadow-2xl shadow-slate-200/50 p-8 md:p-16 border border-slate-100">
          {/* Описание */}
          <div className="max-w-3xl">
            <div className="flex items-center gap-3 mb-8">
              <div className="h-10 w-2 bg-indigo-600 rounded-full" />
              <h3 className="text-2xl font-black uppercase tracking-tight text-slate-900">
                О событии
              </h3>
            </div>
            <p className="text-slate-600 text-xl leading-relaxed whitespace-pre-wrap font-medium">
              {event.description || "Описание скоро появится..."}
            </p>
          </div>

          {/* Галерея */}
          {media.length > 0 && (
            <div className="mt-24">
              <div className="flex items-end justify-between mb-12">
                <div>
                  <h2 className="text-4xl font-black text-slate-900 flex items-center gap-4">
                    Медиа <Camera size={36} className="text-indigo-500" />
                  </h2>
                  <p className="text-slate-400 font-bold mt-2 uppercase tracking-widest text-xs">
                    Галерея моментов
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                {displayItems.map((item, index) => (
                  <div
                    key={item.id || index}
                    onClick={() =>
                      !item.isPlaceholder && setSelectedIndex(index)
                    }
                    className={`
                    group relative aspect-square rounded-[2.5rem] overflow-hidden transition-all duration-500
                    ${
                      item.isPlaceholder
                        ? "bg-slate-50 border-2 border-dashed border-slate-200 flex flex-col items-center justify-center"
                        : "bg-slate-100 cursor-pointer hover:shadow-2xl hover:shadow-indigo-200 hover:-translate-y-3"
                    }
                  `}
                  >
                    {!item.isPlaceholder ? (
                      <>
                        {item.media_type === "video" ? (
                          <div className="w-full h-full relative">
                            <video
                              src={
                                item.file_path?.startsWith("http")
                                  ? item.file_path
                                  : `${API_URL}/${item.file_path}`
                              }
                              className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                              muted
                              playsInline
                            />
                            <div className="absolute inset-0 bg-black/20 flex items-center justify-center group-hover:bg-black/40 transition-all">
                              <div className="bg-white/20 backdrop-blur-xl p-5 rounded-full text-white transform scale-90 group-hover:scale-110 transition-all shadow-2xl">
                                <Film size={24} fill="white" />
                              </div>
                            </div>
                          </div>
                        ) : (
                          <img
                            src={
                              item.file_path?.startsWith("http")
                                ? item.file_path
                                : `${API_URL}/${item.file_path}`
                            }
                            className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                            alt="Moment"
                          />
                        )}
                        <div className="absolute inset-0 bg-gradient-to-t from-indigo-900/40 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                      </>
                    ) : (
                      <>
                        <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-sm mb-3">
                          <Camera size={20} className="text-slate-300" />
                        </div>
                        <span className="text-[10px] font-black text-slate-300 uppercase tracking-widest">
                          Скоро
                        </span>
                      </>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Секция реакций */}
          <div className="mt-16 pt-16 border-t border-slate-50">
            <h4 className="text-center font-black text-2xl text-slate-900 mb-10">
              Будешь на волне?
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {[
                {
                  id: "going",
                  label: "Пойду",
                  icon: <CheckCircle2 />,
                  color: "emerald",
                },
                {
                  id: "maybe",
                  label: "Возможно",
                  icon: <HelpCircle />,
                  color: "amber",
                },
                {
                  id: "not",
                  label: "Пропущу",
                  icon: <XCircle />,
                  color: "rose",
                },
              ].map((btn) => (
                <button
                  key={btn.id}
                  onClick={() => handleReaction(btn.id)}
                  className={`
                    flex items-center justify-center gap-4 p-6 rounded-[2rem] font-black uppercase tracking-wider transition-all transform hover:-translate-y-1 active:scale-95
                    ${
                      userReaction === btn.id.toUpperCase()
                        ? `bg-${btn.color}-500 text-white shadow-2xl shadow-${btn.color}-200 ring-8 ring-${btn.color}-50`
                        : "bg-slate-50 text-slate-600 hover:bg-white hover:shadow-xl border border-transparent hover:border-slate-100"
                    }
                  `}
                >
                  {btn.icon}
                  {btn.label}
                </button>
              ))}
            </div>

            {!isAuthenticated && (
              <p className="text-center text-slate-400 text-[10px] font-bold uppercase tracking-widest mt-8">
                Авторизуйся в боте для отметки
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Лайтбокс */}
      {selectedIndex !== null && (
        <Lightbox
          items={media}
          currentIndex={selectedIndex}
          onClose={() => setSelectedIndex(null)}
          onNext={handleNext}
          onPrev={handlePrev}
        />
      )}

      {/* Модалка Спасибо */}
      {showThanks && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-slate-900/40 backdrop-blur-md animate-in fade-in duration-300">
          <div className="bg-white w-full max-w-sm rounded-[3.5rem] p-10 shadow-2xl text-center transform animate-in zoom-in duration-300">
            <div className="w-24 h-24 bg-emerald-50 text-emerald-500 rounded-full flex items-center justify-center mx-auto mb-8 shadow-inner">
              <CheckCircle2 size={48} />
            </div>
            <h3 className="text-3xl font-black text-slate-900 mb-4 tracking-tighter">
              Супер!
            </h3>
            <p className="text-slate-500 font-medium leading-relaxed">
              Твой выбор важен для нас. Скоро увидимся!
            </p>
            <button
              onClick={() => setShowThanks(false)}
              className="mt-10 w-full bg-slate-900 text-white py-5 rounded-3xl font-black uppercase tracking-widest hover:bg-indigo-600 transition-all active:scale-95 shadow-xl"
            >
              Закрыть
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default EventDetail;
