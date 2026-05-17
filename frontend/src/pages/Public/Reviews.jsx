import React, { useEffect, useState } from "react";
import api from "../../api";
import { useNavigate } from "react-router-dom";
import {
  ChevronLeft,
  Lightbulb,
  Send,
  User,
  Star,
  MessageSquareOff,
  MessageCircleCheck,
  MessageCircleOff,
} from "lucide-react";

const Reviews = () => {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);

  // Состояние формы
  const [text, setText] = useState("");
  const [rating, setRating] = useState(5);
  const [guestName, setGuestName] = useState("");
  const [guestContact, setGuestContact] = useState("");
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const navigate = useNavigate();

  const isAuthenticated = !!localStorage.getItem("token");

  useEffect(() => {
    api
      .get("/reviews")
      .then((res) => {
        setReviews(res.data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    setIsSending(true);

    const payload = {
      text,
      rating,
      guest_name: isAnonymous ? "Аноним" : isAuthenticated ? null : guestName,
      guest_contact: isAnonymous ? null : isAuthenticated ? null : guestContact,
      is_anonymous: isAnonymous, // добавим для логики бэкенда
    };

    try {
      await api.post("/reviews", payload);
      alert("Спасибо! Отзыв отправлен на модерацию!");
      setText("");
      setGuestName("");
      setGuestContact("");
      setTimeout(() => navigate("/"), 1000);
    } catch (err) {
      alert("Ошибка при отправке.");
    } finally {
      setIsSending(false);
    }
  };

  if (loading)
    return <div className="p-10 text-center text-slate-400">Загрузка...</div>;

  const hasReviews = reviews.length > 0;

  return (
    <div className="p-6 bg-slate-50 min-h-screen flex flex-col items-center">
      <div className="w-full max-w-md">
        {/* Контейнер заголовка с относительным позиционированием */}
        <div className="relative text-center mb-8 flex flex-col items-center">
          {/* Кнопка назад теперь прижата к левому краю абсолютно */}
          <button
            onClick={() => navigate(-1)}
            className="absolute left-0 top-0 p-3 bg-white rounded-2xl shadow-sm border border-slate-100 text-slate-400 hover:text-slate-900 transition-all active:scale-90"
          >
            <ChevronLeft size={20} />
          </button>

          {/* Иконка лампочки */}
          <div className="bg-lime-100 w-16 h-16 rounded-3xl flex items-center justify-center text-lime-500 mb-4 shadow-sm">
            {hasReviews ? (
              <MessageCircleCheck size={32} />
            ) : (
              <MessageCircleOff size={32} />
            )}
          </div>

          {/* Текстовый блок */}
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            {hasReviews ? "Отзывы" : "Отзывов пока нет"}
          </h1>
          <p className="text-slate-500 text-sm mt-2">
            {hasReviews
              ? "Оставьте отзыв о «Волне». Мы читаем все отзывы!"
              : "Будьте первым, кто поделится впечатлениями!"}
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-white p-6 rounded-[2.5rem] shadow-xl border border-slate-100 space-y-4"
        >
          <h3 className="font-bold text-lg text-slate-800 px-1">
            Оставить отзыв
          </h3>

          {/* Поля для гостя (только если не анонимно и не залогинен) */}
          {!isAuthenticated && !isAnonymous && (
            <div className="space-y-3">
              <input
                type="text"
                placeholder="Ваше имя"
                className="w-full bg-slate-50 p-4 rounded-2xl text-sm outline-none border border-transparent focus:border-indigo-300 transition-all"
                value={guestName}
                onChange={(e) => setGuestName(e.target.value)}
                required
              />
              <input
                type="text"
                placeholder="Телефон или Telegram"
                className="w-full bg-slate-50 p-4 rounded-2xl text-sm outline-none border border-transparent focus:border-indigo-300 transition-all"
                value={guestContact}
                onChange={(e) => setGuestContact(e.target.value)}
              />
            </div>
          )}

          <div className="flex flex-col gap-2 px-1">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Оценка
            </span>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map((num) => (
                <button
                  key={num}
                  type="button" // КРИТИЧНО: чтобы не срабатывал сабмит формы
                  onClick={() => setRating(num)}
                  className="transform active:scale-125 transition-transform duration-100 focus:outline-none"
                >
                  <Star
                    size={28}
                    // Если текущий номер меньше или равен выбранному рейтингу — закрашиваем
                    fill={rating >= num ? "#fbbf24" : "none"}
                    stroke={rating >= num ? "#fbbf24" : "#cbd5e1"}
                    className={rating >= num ? "drop-shadow-sm" : ""}
                  />
                </button>
              ))}
            </div>

            {/* 
            
            <label className="flex items-center gap-2 text-xs font-medium text-slate-500 cursor-pointer select-none">
              <input 
                type="checkbox" 
                checked={isAnonymous} 
                onChange={() => setIsAnonymous(!isAnonymous)}
                className="w-4 h-4 rounded-full border-slate-300 text-indigo-600 focus:ring-indigo-500"
              />
              Анонимно
            </label>

*/}
          </div>

          <textarea
            placeholder="Что вам понравилось больше всего?"
            className="w-full bg-slate-50 p-4 rounded-2xl text-sm outline-none border border-transparent focus:border-indigo-300 transition-all resize-none h-32"
            value={text}
            onChange={(e) => setText(e.target.value)}
            required
          />

          <button
            type="submit"
            disabled={isSending}
            className="w-full bg-indigo-600 text-white p-4 rounded-2xl shadow-lg font-bold flex items-center justify-center gap-2 active:scale-[0.98] transition-all disabled:bg-slate-300"
          >
            {isSending ? (
              "Отправка..."
            ) : (
              <>
                <span>Отправить отзыв</span>
                <Send size={18} />
              </>
            )}
          </button>
        </form>
      </div>
      <div class="w-full">
        {/* Список отзывов */}
        <div
          className={`p-6 min-h-screen bg-slate-50 flex flex-col ${
            !hasReviews ? "justify-center" : ""
          }`}
        >
          {hasReviews && (
            <div className="space-y-4 mb-10">
              {reviews.map((review) => (
                <div
                  key={review.id}
                  className="bg-white p-5 rounded-3xl shadow-sm border border-slate-100"
                >
                  <div className="flex justify-between items-center mb-2">
                    <div className="flex items-center gap-2">
                      <div className="bg-slate-100 p-2 rounded-full text-slate-400">
                        <User size={14} />
                      </div>
                      <span className="font-bold text-sm text-slate-700">
                        {review.guest_name || "Клиент Волны"}
                      </span>
                    </div>
                    <div className="flex text-amber-400">
                      {[...Array(review.rating)].map((_, i) => (
                        <Star key={i} size={12} fill="currentColor" />
                      ))}
                    </div>
                  </div>
                  <p className="text-slate-600 text-sm italic leading-relaxed">
                    «{review.text}»
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Отступ снизу для красоты в скролле */}
        <div className="h-20" />
      </div>
    </div>
  );
};

export default Reviews;
