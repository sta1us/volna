import React, { useState } from "react";
import api from "../../api";
import { Lightbulb, Send, User, ChevronLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";

const Suggestions = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    subject: "",
    text: "",
    guest_name: "",
    guest_contact: "",
  });
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [isSending, setIsSending] = useState(false);

  const isAuthenticated = !!localStorage.getItem("token");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSending(true);

    const payload = {
      ...formData,
      guest_name: isAnonymous
        ? "Аноним"
        : isAuthenticated
        ? null
        : formData.guest_name,
      guest_contact: isAnonymous
        ? null
        : isAuthenticated
        ? null
        : formData.guest_contact,
    };

    try {
      await api.post("/suggestions/", payload);
      alert("Спасибо! Ваша идея передана руководству.");
      setFormData({ subject: "", text: "", guest_name: "", guest_contact: "" });
      navigate(-1); // Возвращаемся назад после отправки
    } catch (err) {
      alert("Ошибка отправки");
    } finally {
      setIsSending(false);
    }
  };

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
          <div className="bg-amber-100 w-16 h-16 rounded-3xl flex items-center justify-center text-amber-500 mb-4 shadow-sm">
            <Lightbulb size={32} />
          </div>

          {/* Текстовый блок */}
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            Банк идей
          </h1>
          <p className="text-slate-500 text-sm mt-2">
            Помогите «Волне» стать лучше. Мы читаем каждое предложение.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-white p-6 rounded-[2.5rem] shadow-xl space-y-4 border border-slate-100"
        >
          {!isAuthenticated && !isAnonymous && (
            <div className="grid grid-cols-2 gap-2">
              <input
                type="text"
                placeholder="Имя"
                className="bg-slate-50 p-4 rounded-2xl text-sm outline-none border border-transparent focus:border-amber-300 transition-all"
                value={formData.guest_name}
                onChange={(e) =>
                  setFormData({ ...formData, guest_name: e.target.value })
                }
                required
              />
              <input
                type="text"
                placeholder="Контакты"
                className="bg-slate-50 p-4 rounded-2xl text-sm outline-none border border-transparent focus:border-amber-300 transition-all"
                value={formData.guest_contact}
                onChange={(e) =>
                  setFormData({ ...formData, guest_contact: e.target.value })
                }
              />
            </div>
          )}

          {/* 
          <div className="flex justify-end px-1">
            <label className="flex items-center gap-2 text-xs font-medium text-slate-500 cursor-pointer">
              <input 
                type="checkbox" checked={isAnonymous} 
                onChange={() => setIsAnonymous(!isAnonymous)}
                className="w-4 h-4 rounded-full border-slate-300 text-amber-500 focus:ring-amber-500"
              />
              Анонимно
            </label>
          </div>
*/}

          <input
            type="text"
            placeholder="Тема (например: Сотрудничество,  Музыка, ...)"
            className="w-full bg-slate-50 p-4 rounded-2xl text-sm outline-none border border-transparent focus:border-amber-300 transition-all"
            value={formData.subject}
            onChange={(e) =>
              setFormData({ ...formData, subject: e.target.value })
            }
          />

          <textarea
            placeholder="Опишите вашу идею подробно..."
            className="w-full bg-slate-50 p-4 rounded-2xl text-sm outline-none border border-transparent focus:border-amber-300 transition-all h-40 resize-none"
            value={formData.text}
            onChange={(e) => setFormData({ ...formData, text: e.target.value })}
            required
          />

          <button
            type="submit"
            disabled={isSending}
            className="w-full bg-slate-900 text-white p-4 rounded-2xl shadow-lg font-bold flex items-center justify-center gap-2 active:scale-95 transition-all disabled:bg-slate-300"
          >
            {isSending ? (
              "Отправка..."
            ) : (
              <>
                <Send size={18} /> Отправить идею
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Suggestions;
