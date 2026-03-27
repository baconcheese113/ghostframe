/** Application configuration loaded from environment variables. */
const config = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000',
  allowedDevOrigins: process.env.NEXT_PUBLIC_ALLOWED_DEV_ORIGINS?.split(',') ?? ['127.0.0.1'],
};

export default config;
