import React, { useState } from "react";
import {
  Upload,
  X,
  Image as ImageIcon,
  Film,
  CheckCircle,
  ArrowLeft,
  CloudDownload,
} from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import api from "../../api";

const MediaUpload = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
    const newFiles = files.map((file) => ({
      file,
      preview: URL.createObjectURL(file),
      type: file.type.startsWith("video") ? "video" : "image",
    }));
    setSelectedFiles((prev) => [...prev, ...newFiles]);
  };

  const removeFile = (index) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;
    setUploading(true);

    console.log(id);

    const formData = new FormData();
    selectedFiles.forEach((item) => {
      formData.append("files", item.file);
    });
    console.log(formData);

    if (id) {
      formData.append("event_id", id);
    }

    try {
      await api.post("/media/upload-multiple", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setProgress(percentCompleted);
        },
      });
      alert("Все файлы успешно загружены!");
      setSelectedFiles([]);
      navigate(id ? `/admin/events/media/${id}` : "/admin/media");
    } catch (err) {
      console.error(err);
      alert("Ошибка при загрузке");
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="flex items-start gap-5 mb-10">
        {/* Кнопка "Назад" - слева */}
        <button
          onClick={() =>
            navigate(id ? `/admin/events/media/${id}` : "/admin/media")
          }
          className="mt-1 p-2.5 bg-white rounded-2xl shadow-sm hover:bg-slate-50 transition-all border border-slate-100 text-slate-600 hover:text-indigo-600"
        >
          <ArrowLeft size={22} />
        </button>

        {/* Правая часть: Заголовок и описание друг под другом */}
        <div className="flex flex-col">
          <h1 className="text-3xl font-black flex items-center gap-3 text-slate-900 leading-tight">
            <CloudDownload className="text-indigo-600" size={32} />
            Загрузка медиа
          </h1>
          <p className="text-slate-500 mt-1 font-medium">
            Выберите изображения или видео для галереи или событий
          </p>
        </div>
      </div>

      {/* Зона выбора файлов */}
      <div className="relative border-2 border-dashed border-slate-200 rounded-[2rem] p-12 text-center hover:border-indigo-400 transition-colors bg-white shadow-sm">
        <input
          type="file"
          multiple
          accept="image/*,video/*"
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          onChange={handleFileChange}
          disabled={uploading}
        />
        <div className="flex flex-col items-center">
          <div className="p-4 bg-indigo-50 text-indigo-600 rounded-full mb-4">
            <Upload size={32} />
          </div>
          <p className="text-lg font-bold text-slate-700">
            Перетащите файлы сюда или кликните
          </p>
          <p className="text-sm text-slate-400">
            Поддерживаются JPG, PNG, MP4, MOV
          </p>
        </div>
      </div>

      {/* Предпросмотр */}
      {selectedFiles.length > 0 && (
        <div className="mt-10">
          <div className="flex justify-between items-center mb-4">
            <h2 className="font-bold text-xl">
              Выбрано: {selectedFiles.length}
            </h2>
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="px-6 py-3 bg-indigo-600 text-white rounded-2xl font-bold hover:bg-indigo-700 disabled:bg-slate-300 transition-all flex items-center gap-2"
            >
              {uploading ? `Загрузка ${progress}%...` : "Начать загрузку"}
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {selectedFiles.map((item, index) => (
              <div
                key={index}
                className="relative group rounded-2xl overflow-hidden aspect-square bg-slate-100 border border-slate-200"
              >
                {item.type === "image" ? (
                  <img
                    src={item.preview}
                    alt="preview"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-slate-800 text-white">
                    <Film size={32} />
                  </div>
                )}
                <button
                  onClick={() => removeFile(index)}
                  className="absolute top-2 right-2 p-1.5 bg-rose-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X size={16} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default MediaUpload;
