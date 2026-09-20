import axios from "axios";

export const api = axios.create({ baseURL: `${process.env.REACT_APP_BACKEND_URL}/api` });
api.interceptors.request.use(config => {
  const token = localStorage.getItem("admin_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
export const money = value => `₹${Number(value || 0).toLocaleString("en-IN")}`;
export const errorMessage = (error, fallback = "Something went wrong. Please try again.") => {
  const detail = error.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map(item => `${item.loc?.slice(1).join(" ")}: ${item.msg}`).join(". ");
  return fallback;
};
export const indiaToday = () => new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Kolkata", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());