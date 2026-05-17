import React, { useState, useEffect } from "react";
import api from "../../api";
import { useNavigate } from "react-router-dom";
import {
  Save,
  Map,
  ArrowLeft,
  Mail,
  Phone,
  Clock,
  FileImage,
  Globe,
} from "lucide-react";

const EditLocation = () => {
  const [formData, setFormData] = useState({
    address: "",
    latitude: "",
    longitude: "",
    working_hours: "",
    phone: "",
    email: "",
  });

  // Отдельные состояния для двух картинок
  const [entranceFile, setEntranceFile] = useState(null);
  const [mapFile, setMapFile] = useState(null);

  // Ссылки на текущие изображения с бэкенда для превью
  const [currentEntranceImg, setCurrentEntranceImg] = useState("");
  const [currentMapImg, setCurrentMapImg] = useState("");

  const [isSaving, setIsSaving] = useState(false);
  const navigate = useNavigate();
  const API_URL = import.meta.env.VITE_API_URL || "";

  useEffect(() => {
    api
      .get("/location")
      .then((res) => {
        if (res.data) {
          setFormData({
            address: res.data.address || "",
            latitude: res.data.latitude || "",
            longitude: res.data.longitude || "",
            working_hours: res.data.working_hours || "",
            phone: res.data.phone || "",
            email: res.data.email || "",
          });
          setCurrentEntranceImg(res.data.image_path || "");
          setCurrentMapImg(res.data.map_image_path || "");
        }
      })
      .catch((e) => console.error("Ошибка загрузки локации", e));
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setIsSaving(true);

    const data = new FormData();
    // Добавляем текстовые поля
    Object.keys(formData).forEach((key) => data.append(key, formData[key]));

    // Добавляем файлы, если они выбраны
    if (entranceFile) data.append("file_entrance", entranceFile);
    if (mapFile) data.append("file_map", mapFile);

    try {
      await api.put("/location", data);
      alert("Данные локации успешно обновлены!");
      // Перезагружаем страницу или обновляем ссылки на превью, если бэкенд возвращает новые пути
    } catch (err) {
      alert("Ошибка при сохранении данных");
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="p-6 max-w-2xl mx-auto pb-24 bg-slate-50 min-h-screen">
      {/* Кнопка Назад */}
      <button
        onClick={() => navigate("/admin")}
        className="mb-6 p-3 bg-white rounded-2xl shadow-sm border border-slate-100 text-slate-600 hover:text-indigo-600 hover:bg-slate-50 cursor-pointer transition-all duration-200"
      >
        <ArrowLeft size={20} />
      </button>

      <div className="flex items-center gap-3 mb-8">
        <div className="p-3 bg-indigo-50 text-indigo-600 rounded-2xl">
          <Map size={28} />
        </div>
        <div>
          <h2 className="text-3xl font-black text-slate-900 tracking-tight">
            Настройка локации
          </h2>
          <p className="text-slate-400 font-medium text-sm">
            Управление контактами и картой на главном экране
          </p>
        </div>
      </div>

      <form
        onSubmit={handleSave}
        className="space-y-6 bg-white p-8 md:p-10 rounded-[2.5rem] shadow-xl shadow-slate-200/50 border border-slate-100"
      >
        {/* Адрес */}
        <div>
          <label className="text-xs font-bold text-slate-400 ml-2 uppercase tracking-wider block mb-2">
            Адрес
          </label>
          <div className="relative">
            <input
              type="text"
              value={formData.address}
              required
              className="w-full p-4 pl-12 bg-slate-50 focus:bg-white border border-transparent focus:border-indigo-500 rounded-2xl outline-none transition-all font-medium text-slate-800"
              onChange={(e) =>
                setFormData({ ...formData, address: e.target.value })
              }
            />
            <Map className="absolute left-4 top-4.5 text-slate-400" size={18} />
          </div>
        </div>

        {/* Координаты */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-bold text-slate-400 ml-2 uppercase tracking-wider block mb-2">
              Широта (Lat)
            </label>
            <div className="relative">
              <input
                type="number"
                step="any"
                value={formData.latitude}
                required
                className="w-full p-4 pl-12 bg-slate-50 focus:bg-white border border-transparent focus:border-indigo-500 rounded-2xl outline-none transition-all font-medium text-slate-800"
                onChange={(e) =>
                  setFormData({ ...formData, latitude: e.target.value })
                }
              />
              <Globe
                className="absolute left-4 top-4.5 text-slate-400"
                size={18}
              />
            </div>
          </div>
          <div>
            <label className="text-xs font-bold text-slate-400 ml-2 uppercase tracking-wider block mb-2">
              Долгота (Lng)
            </label>
            <div className="relative">
              <input
                type="number"
                step="any"
                value={formData.longitude}
                required
                className="w-full p-4 pl-12 bg-slate-50 focus:bg-white border border-transparent focus:border-indigo-500 rounded-2xl outline-none transition-all font-medium text-slate-800"
                onChange={(e) =>
                  setFormData({ ...formData, longitude: e.target.value })
                }
              />
              <Globe
                className="absolute left-4 top-4.5 text-slate-400"
                size={18}
              />
            </div>
          </div>
        </div>

        {/* Почта и Телефон */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-bold text-slate-400 ml-2 uppercase tracking-wider block mb-2">
              Телефон
            </label>
            <div className="relative">
              <input
                type="text"
                value={formData.phone}
                className="w-full p-4 pl-12 bg-slate-50 focus:bg-white border border-transparent focus:border-indigo-500 rounded-2xl outline-none transition-all font-medium text-slate-800"
                onChange={(e) =>
                  setFormData({ ...formData, phone: e.target.value })
                }
              />
              <Phone
                className="absolute left-4 top-4.5 text-slate-400"
                size={18}
              />
            </div>
          </div>
          <div>
            <label className="text-xs font-bold text-slate-400 ml-2 uppercase tracking-wider block mb-2">
              Email
            </label>
            <div className="relative">
              <input
                type="email"
                value={formData.email}
                className="w-full p-4 pl-12 bg-slate-50 focus:bg-white border border-transparent focus:border-indigo-500 rounded-2xl outline-none transition-all font-medium text-slate-800"
                onChange={(e) =>
                  setFormData({ ...formData, email: e.target.value })
                }
              />
              <Mail
                className="absolute left-4 top-4.5 text-slate-400"
                size={18}
              />
            </div>
          </div>
        </div>

        {/* Режим работы */}
        <div>
          <label className="text-xs font-bold text-slate-400 ml-2 uppercase tracking-wider block mb-2">
            Часы работы
          </label>
          <div className="relative">
            <textarea
              value={formData.working_hours}
              className="w-full p-4 pl-12 bg-slate-50 focus:bg-white border border-transparent focus:border-indigo-500 rounded-2xl outline-none transition-all font-medium text-slate-800 h-24 resize-none"
              onChange={(e) =>
                setFormData({ ...formData, working_hours: e.target.value })
              }
            />
            <Clock
              className="absolute left-4 top-4.5 text-slate-400"
              size={18}
            />
          </div>
        </div>

        <hr className="border-slate-100 my-4" />

        {/* БЛОК ИЗОБРАЖЕНИЙ */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Фото входа */}
          <div className="p-4 bg-slate-50 rounded-3xl border border-slate-100">
            <label className="text-xs font-black text-slate-400 uppercase tracking-wider block mb-3">
              Фото входа / здания
            </label>
            {currentEntranceImg && (
              <div className="w-full h-32 rounded-2xl overflow-hidden mb-3 bg-slate-200">
                <img
                  src={
                    currentEntranceImg.startsWith("http")
                      ? currentEntranceImg
                      : `${API_URL}/${currentEntranceImg}`
                  }
                  className="w-full h-full object-cover"
                  alt="Превью входа"
                />
              </div>
            )}
            <label className="w-full flex flex-col items-center justify-center p-4 bg-white border-2 border-dashed border-slate-200 rounded-2xl hover:border-indigo-500 cursor-pointer transition-colors">
              <FileImage className="text-slate-400 mb-1" size={20} />
              <span className="text-xs font-bold text-slate-500">
                {entranceFile ? entranceFile.name : "Выбрать фото"}
              </span>
              <input
                type="file"
                className="hidden"
                onChange={(e) => setEntranceFile(e.target.files[0])}
              />
            </label>
          </div>

          {/* Фото карты */}
          <div className="p-4 bg-slate-50 rounded-3xl border border-slate-100">
            <label className="text-xs font-black text-slate-400 uppercase tracking-wider block mb-3">
              Схема проезда / Карта
            </label>
            {currentMapImg && (
              <div className="w-full h-32 rounded-2xl overflow-hidden mb-3 bg-slate-200">
                <img
                  src={
                    currentMapImg.startsWith("http")
                      ? currentMapImg
                      : `${API_URL}/${currentMapImg}`
                  }
                  className="w-full h-full object-cover"
                  alt="Превью карты"
                />
              </div>
            )}
            <label className="w-full flex flex-col items-center justify-center p-4 bg-white border-2 border-dashed border-slate-200 rounded-2xl hover:border-indigo-500 cursor-pointer transition-colors">
              <FileImage className="text-slate-400 mb-1" size={20} />
              <span className="text-xs font-bold text-slate-500">
                {mapFile ? mapFile.name : "Выбрать схему"}
              </span>
              <input
                type="file"
                className="hidden"
                onChange={(e) => setMapFile(e.target.files[0])}
              />
            </label>
          </div>
        </div>

        {/* Кнопка отправки */}
        <button
          disabled={isSaving}
          className="w-full bg-slate-900 hover:bg-indigo-600 text-white py-5 rounded-2xl font-black uppercase tracking-widest text-xs flex items-center justify-center gap-2 transition-all active:scale-[0.98] cursor-pointer shadow-xl shadow-slate-900/10 disabled:bg-slate-300 disabled:cursor-not-allowed"
        >
          <Save size={18} />{" "}
          {isSaving ? "Сохранение..." : "Сохранить изменения"}
        </button>
      </form>
    </div>
  );
};

export default EditLocation;
