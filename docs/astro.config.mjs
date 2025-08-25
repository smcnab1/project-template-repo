import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";

export default defineConfig({
  site: "https://smcnab1.github.io/project-template-repo", // set this for correct URLs
  outDir: "./dist", // build output (workflow will upload this)
  integrations: [
    starlight({
      title: "Project Template",
      description: "This is a template for projects",
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
        github: "https://github.com/smcnab1/project-template-repo"
      },
      // Nice defaults already include dark mode, search, code copy, etc.
    })
  ]
});

