import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://www.gtavice.city',
  trailingSlash: 'never',
  integrations: [
    sitemap({
      changefreq: 'weekly',
      priority: 1.0,
      lastmod: new Date(),
      i18n: {
        defaultLocale: 'en',
        locales: { en: 'en' },
      },
    }),
  ],
  server: {
    port: 4321,
    host: true,
  },
  vite: {
    preview: {
      allowedHosts: ['gtavice.city', 'www.gtavice.city'],
    },
  },
  devToolbar: {
    enabled: false,
  },
});
