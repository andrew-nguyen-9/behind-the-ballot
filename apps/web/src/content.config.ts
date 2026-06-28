import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

// MDX articles with live-figure embedding [P11a,Y8a]. Frontmatter validated at build.
const articles = defineCollection({
  loader: glob({ pattern: "**/*.mdx", base: "./src/content/articles" }),
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    description: z.string(),
    draft: z.boolean().default(false),
  }),
});

export const collections = { articles };
