import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro:content';

const articles = defineCollection({
  loader: glob({ base: './src/content/articles', pattern: '**/*.md' }),
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    category: z.string(),
    tags: z.array(z.string()),
    summary: z.string(),
    sources: z.array(z.union([
      z.string(),
      z.object({
        text: z.string(),
        url: z.string().nullable().optional(),
      })
    ])),
    image: z.string().optional(),
  }),
});

export const collections = { articles };
