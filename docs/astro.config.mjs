import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  site: "https://hammadxcm.github.io",
  base: "/go-phantom",
  vite: {
    plugins: [tailwindcss()],
  },
});
