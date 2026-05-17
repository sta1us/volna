import React, { useEffect, useCallback } from "react";
import { X, ChevronLeft, ChevronRight, Film } from "lucide-react";

const Lightbox = ({ items, currentIndex, onClose, onPrev, onNext }) => {
  const currentItem = items[currentIndex];

  // Обработка клавиш
  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowLeft") onPrev();
      if (e.key === "ArrowRight") onNext();
    },
    [onClose, onPrev, onNext]
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    // Блокируем скролл основной страницы при открытии
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "auto";
    };
  }, [handleKeyDown]);

  if (!currentItem || currentItem.isPlaceholder) return null;

  const apiUrl = import.meta.env.VITE_API_URL;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/95 backdrop-blur-sm transition-all">
      {/* Кнопка закрытия */}
      <button
        onClick={onClose}
        className="absolute top-6 right-6 text-white/70 hover:text-white transition-colors z-[110]"
      >
        <X size={40} />
      </button>

      {/* Стрелка влево */}
      <button
        onClick={onPrev}
        className="absolute left-4 top-1/2 -translate-y-1/2 p-4 text-white/50 hover:text-white transition-all z-[110]"
      >
        <ChevronLeft size={48} />
      </button>

      {/* Контент (Картинка или Видео) */}
      <div className="max-w-[90vw] max-h-[90vh] flex items-center justify-center animate-in zoom-in-95 duration-300">
        {currentItem.media_type === "video" ? (
          <video
            src={`${currentItem.file_path}`}
            controls
            autoPlay
            className="max-w-full max-h-[85vh] rounded-lg shadow-2xl"
          />
        ) : (
          <img
            src={`${currentItem.file_path}`}
            alt="Full size"
            className="max-w-full max-h-[85vh] object-contain rounded-lg shadow-2xl"
          />
        )}
      </div>

      {/* Стрелка вправо */}
      <button
        onClick={onNext}
        className="absolute right-4 top-1/2 -translate-y-1/2 p-4 text-white/50 hover:text-white transition-all z-[110]"
      >
        <ChevronRight size={48} />
      </button>

      {/* Индикатор позиции */}
      <div className="absolute bottom-6 text-white/40 font-medium tracking-widest text-sm">
        {currentIndex + 1} / {items.filter((i) => !i.isPlaceholder).length}
      </div>
    </div>
  );
};

export default Lightbox;
