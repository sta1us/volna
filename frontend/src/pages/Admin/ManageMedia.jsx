import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Trash2,
  Plus,
  CheckSquare,
  Square,
  RefreshCcw,
  ArrowLeft,
  Image as ImageIcon,
  Film,
} from "lucide-react";
import api from "../../api";

const ManageMedia = () => {
  const navigate = useNavigate();
  const [media, setMedia] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [loading, setLoading] = useState(true);

  // 1. Загрузка списка файлов
  const fetchMedia = async () => {
    setLoading(true);
    try {
      const res = await api.get("/media/gallery");
      setMedia(res.data);
    } catch (err) {
      console.error("Ошибка загрузки:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMedia();
  }, []);

  // 2. Логика выбора
  const toggleSelect = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    if (selectedIds.length === media.length) setSelectedIds([]);
    else setSelectedIds(media.map((m) => m.id));
  };

  // 3. Удаление (одиночное и массовое)
  const handleDelete = async (ids) => {
    if (
      !window.confirm(
        `Удалить ${ids.length} файл(ов)? Это действие необратимо.`
      )
    )
      return;

    try {
      await api.delete("/media/delete-multiple", { data: ids });
      setMedia((prev) => prev.filter((m) => !ids.includes(m.id)));
      setSelectedIds((prev) => prev.filter((id) => !ids.includes(id)));
    } catch (err) {
      alert("Ошибка при удалении");
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto bg-slate-50 min-h-screen">
      {/* Шапка */}
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate("/admin")}
            className="p-3 bg-white rounded-2xl shadow-sm hover:bg-slate-50"
          >
            <ArrowLeft size={24} />
          </button>
          <div>
            <h1 className="text-3xl font-black text-slate-900">
              Управление медиа
            </h1>
            <p className="text-slate-500">Всего файлов: {media.length}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {selectedIds.length > 0 && (
            <button
              onClick={() => handleDelete(selectedIds)}
              className="px-5 py-3 bg-rose-500 text-white rounded-2xl font-bold hover:bg-rose-600 transition-all flex items-center gap-2 shadow-lg shadow-rose-200"
            >
              <Trash2 size={20} /> Удалить выбранные ({selectedIds.length})
            </button>
          )}
          <button
            onClick={() => navigate("/admin/media/upload")}
            className="px-5 py-3 bg-indigo-600 text-white rounded-2xl font-bold hover:bg-indigo-700 transition-all flex items-center gap-2 shadow-lg shadow-indigo-200"
          >
            <Plus size={20} /> Добавить медиа
          </button>
        </div>
      </div>

      {/* Панель инструментов */}
      <div className="flex items-center justify-between bg-white p-4 rounded-2xl mb-6 shadow-sm border border-slate-100">
        <button
          onClick={toggleSelectAll}
          className="flex items-center gap-2 text-slate-600 font-semibold hover:text-indigo-600 transition-colors"
        >
          {selectedIds.length === media.length && media.length > 0 ? (
            <CheckSquare />
          ) : (
            <Square />
          )}
          Выбрать все
        </button>
        <button
          onClick={fetchMedia}
          className="p-2 text-slate-400 hover:text-indigo-600"
        >
          <RefreshCcw size={20} className={loading ? "animate-spin" : ""} />
        </button>
      </div>

      {/* Сетка файлов */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-6">
        {media.map((item) => (
          <div
            key={item.id}
            className={`group relative bg-white rounded-[2rem] p-3 border-2 transition-all ${
              selectedIds.includes(item.id)
                ? "border-indigo-500 ring-4 ring-indigo-50"
                : "border-transparent shadow-sm hover:shadow-md"
            }`}
          >
            {/* Чекбокс */}
            <button
              onClick={() => toggleSelect(item.id)}
              className={`absolute top-5 left-5 z-10 p-1.5 rounded-lg transition-all ${
                selectedIds.includes(item.id)
                  ? "bg-indigo-600 text-white"
                  : "bg-white/80 text-slate-400 opacity-0 group-hover:opacity-100"
              }`}
            >
              <CheckSquare size={18} />
            </button>

            {/* Контент */}
            <div className="aspect-square rounded-[1.5rem] overflow-hidden bg-slate-100 mb-3 relative">
              {item.media_type === "video" ? (
                <div className="w-full h-full flex items-center justify-center bg-slate-800">
                  <Film size={40} className="text-slate-600" />
                  <video
                    src={
                      item.file_path.startsWith("http")
                        ? item.file_path
                        : `/${item.file_path}`
                    }
                    className="absolute inset-0 w-full h-full object-cover opacity-50"
                  />
                </div>
              ) : (
                <img
                  src={
                    item.file_path.startsWith("http")
                      ? item.file_path
                      : `/${item.file_path}`
                  }
                  alt="media"
                  className="w-full h-full object-cover"
                />
              )}
            </div>

            {/* Инфо и Удаление */}
            <div className="flex items-center justify-between px-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                {item.media_type}
              </span>
              <button
                onClick={() => handleDelete([item.id])}
                className="p-2 text-slate-300 hover:text-rose-500 transition-colors"
              >
                <Trash2 size={18} />
              </button>
            </div>
          </div>
        ))}
      </div>

      {media.length === 0 && !loading && (
        <div className="text-center py-20 bg-white rounded-[3rem] border-2 border-dashed border-slate-200">
          <ImageIcon size={64} className="mx-auto text-slate-200 mb-4" />
          <p className="text-slate-400 font-medium">Медиафайлов пока нет</p>
        </div>
      )}
    </div>
  );
};

export default ManageMedia;
