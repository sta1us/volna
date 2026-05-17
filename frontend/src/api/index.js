import axios from "axios";

const DOMAIN = import.meta.env.VITE_DOMAIN;
const API_URL = `https://${DOMAIN}/api`;

const api = axios.create({
  baseURL: API_URL,
});

// Перехватчик: добавляет токен в каждый запрос, если он есть
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
