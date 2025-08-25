import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";

export default defineConfig({
  site: "https://YOUR_USER.github.io/YOUR_REPO", // set this for correct URLs
  outDir: "./dist", // build output (workflow will upload this)
  integrations: [
    starlight({
      title: "Your Project",
      description: "Short description of your project.",
      sidebar: [
        { label: "Introduction", link: "/"},
        { label: "Getting Started", link: "/getting-started/" },
        {
          label: "Guides",
          items: [
            { label: "Configuration", link: "/guides/configuration/" },
            { label: "Usage", link: "/guides/usage/" }
          ]
        }
      ],
      social: {
        github: "https://github.com/YOUR_USER/YOUR_REPO"
      },
      // Nice defaults already include dark mode, search, code copy, etc.
    })
  ]
});

