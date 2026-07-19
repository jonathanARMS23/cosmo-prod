/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Le portail parle uniquement à Frappe via le serveur Next (BFF).
  // Aucune URL Frappe n'est exposée au client.
};

export default nextConfig;
