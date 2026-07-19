/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Le portail parle uniquement à Frappe via le serveur Next (BFF).
  // Aucune URL Frappe n'est exposée au client.
  // "standalone" : sortie de build autonome (server.js + deps minimales),
  // nécessaire pour une image Docker légère qui ne traîne pas node_modules.
  output: "standalone",
};

export default nextConfig;
