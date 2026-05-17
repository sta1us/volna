import React, { useEffect, useState } from "react";
import api from "../../api";
import { MapPin, Clock, Phone, Send, Info } from "lucide-react";

const Contacts = () => {
  const [location, setLocation] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/location")
      .then((res) => {
        setLocation(res.data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Ошибка загрузки контактов", err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="p-10 text-center">Загрузка...</div>;
  if (!location)
    return (
      <div className="p-10 text-center text-slate-400">
        Данные о локации не заполнены
      </div>
    );

  // Формируем ссылку для Яндекс Карт на основе координат
  const mapUrl = `https://yandex.ru/map-widget/v1/?ll=${location.longitude}%2C${location.latitude}&z=16&pt=${location.longitude}%2C${location.latitude},pm2rdm`;

  return (
    <div className="p-6 pb-24 bg-slate-50 min-h-screen">
      <h1 className="text-4xl font-black mb-8 text-slate-900">Контакты</h1>

      {/* Фото заведения (если есть) */}
      {location.image_url && (
        <div className="mb-6 rounded-3xl overflow-hidden h-48 shadow-lg">
          <img
            src={`${location.image_url}`}
            className="w-full h-full object-cover"
            alt="Наше заведение"
          />
        </div>
      )}

      <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-100 mb-6 space-y-6">
        {/* Адрес */}
        <div className="flex items-start">
          <div className="bg-indigo-50 p-3 rounded-2xl mr-4 text-indigo-600">
            <MapPin size={24} />
          </div>
          <div>
            <p className="text-sm text-slate-400 font-medium">Адрес</p>
            <p className="font-bold text-lg leading-tight">
              {location.address}
            </p>
          </div>
        </div>

        {/* Время работы */}
        <div className="flex items-start">
          <div className="bg-orange-50 p-3 rounded-2xl mr-4 text-orange-600">
            <Clock size={24} />
          </div>
          <div>
            <p className="text-sm text-slate-400 font-medium">Режим работы</p>
            <p className="font-bold text-lg whitespace-pre-line">
              {location.working_hours}
            </p>
          </div>
        </div>

        {/* Телефон */}
        <div className="flex items-start">
          <div className="bg-green-50 p-3 rounded-2xl mr-4 text-green-600">
            <Phone size={24} />
          </div>
          <div>
            <p className="text-sm text-slate-400 font-medium">Телефон</p>
            <a href={`tel:${location.phone}`} className="font-bold text-lg">
              {location.phone}
            </a>
          </div>
        </div>
      </div>

      {/* Интерактивная карта */}
      <div className="bg-white p-2 rounded-3xl shadow-sm border border-slate-100 overflow-hidden h-80 relative">
        <iframe
          src={mapUrl}
          width="100%"
          height="100%"
          frameBorder="0"
          allowFullScreen={true}
          className="rounded-2xl"
          title="Yandex Map"
        ></iframe>
      </div>
    </div>
  );
};

export default Contacts;
