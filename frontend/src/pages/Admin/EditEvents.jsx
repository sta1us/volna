import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../../api";
import { Save, ArrowLeft, Image as ImageIcon } from "lucide-react";

const EditEvents = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    date: "",
    time: "20:00",
  });

  useEffect(() => {
    if (id) {
      api.get(`/events/${id}`).then((res) => {
        // Приводим дату к формату YYYY-MM-DD для input type="date"
        const eventData = res.data;
        const dateObj = new Date(eventData.date_time);
        eventData.time = dateObj.toLocaleTimeString("ru-RU", {
          hour: "2-digit",
          minute: "2-digit",
        });
        eventData.date = dateObj.toLocaleDateString("en-CA");

        // eventData.date = new Date(eventData.date_time).toISOString().split('T')[0];
        // eventData.time = new Date(eventData.date_time).toISOString().split('T')[1];
        setFormData(eventData);
      });
    }
  }, [id]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const data = new FormData();
    data.append("title", formData.title);
    data.append("description", formData.description);
    data.append("date_time", `${formData.date}T${formData.time}`);
    // Object.keys(formData).forEach(key => data.append(key, formData[key]));
    if (file) data.append("file", file);

    try {
      if (id) {
        await api.put(`/events/${id}`, data);
      } else {
        await api.post("/events/", data);
      }
      navigate("/admin/events");
    } catch (err) {
      alert("Ошибка сохранения");
    }
  };

  return (
    <div className="p-6 pb-24 max-w-sd mx-auto">
      <div className="flex items-center mb-8">
        <button
          onClick={() => navigate(-1)}
          className="mr-4 p-2 bg-slate-100 rounded-xl"
        >
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-xl font-bold">
          {id ? "Изменить событие" : "Новое событие"}
        </h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Загрузка фото */}
        <div className="relative h-64 bg-slate-200 rounded-3xl overflow-hidden border-2 border-dashed border-slate-300">
          {file ? (
            <img
              src={URL.createObjectURL(file)}
              className="w-full h-full object-cover"
            />
          ) : formData.image_url ? (
            <img
              src={`${formData.image_url}`}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-slate-400">
              <ImageIcon size={40} className="mb-2" />
              <span className="text-xs">Загрузить афишу</span>
            </div>
          )}
          <input
            type="file"
            onChange={(e) => setFile(e.target.files[0])}
            className="absolute inset-0 opacity-0 cursor-pointer"
          />
        </div>

        <input
          type="text"
          placeholder="Заголовок"
          value={formData.title}
          required
          className="w-full p-4 bg-white rounded-2xl border outline-none focus:ring-2 ring-indigo-500"
          onChange={(e) => setFormData({ ...formData, title: e.target.value })}
        />

        <div className="grid grid-cols-2 gap-4">
          <input
            type="date"
            value={formData.date}
            required
            className="p-4 bg-white rounded-2xl border outline-none"
            onChange={(e) => setFormData({ ...formData, date: e.target.value })}
          />
          <input
            type="time"
            value={formData.time}
            required
            className="p-4 bg-white rounded-2xl border outline-none"
            onChange={(e) => setFormData({ ...formData, time: e.target.value })}
          />
        </div>

        <textarea
          placeholder="Описание"
          value={formData.description}
          className="w-full p-4 bg-white rounded-2xl border outline-none h-32 resize-none"
          onChange={(e) =>
            setFormData({ ...formData, description: e.target.value })
          }
        />

        <button className="w-full bg-slate-900 text-white py-4 rounded-3xl font-bold shadow-lg flex items-center justify-center gap-2 active:scale-95 transition">
          <Save size={20} /> Опубликовать
        </button>
      </form>
    </div>
  );
};

export default EditEvents;
