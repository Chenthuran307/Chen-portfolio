# Chen — Product Design Portfolio

Source for [chenthuran.in](https://chenthuran.in). Static HTML, no build step, deployed on Vercel.

## Structure

```
public/                 Site pages (served at the domain root)
  index.html            Home
  work.html             Selected work
  transforming-a-design-system.html
  horizon-bank-developer-central.html
  dosb-financing-ecosystem.html
  beyond-bau.html       Self-initiated tools and research
  idea-godown.html      Product ideas, including ones not pursued
  blogs.html            Links out to Medium
  dashboard.html        Local-only content editor (excluded from the build)
  01_home.html          Redirect stub -> /
  03_idea_godown_research_ledger.html   Redirect stub -> /idea-godown
  favicon.svg
  images/               Referenced images only
  files/                Resume PDF

api/
  chat.py               Vercel serverless handler for the AI assistant
  prompt_loader.py      Builds the assistant's system prompt
  prompt.json           Assistant content: bio, expertise, projects, awards

server.py               Local dev server + dashboard API (mirrors Vercel routing)
vercel.json             Clean URLs and rewrites
```

Each page carries its own inline Tailwind config. There is no shared token file,
so colour and type changes must be applied per page.

## Running locally

Requires Python 3 and an `NVIDIA_API_KEY`.

```bash
echo "NVIDIA_API_KEY=your-key-here" > .env
python server.py
```

Then open http://localhost:3000. The dashboard is at `/dashboard`.

## Deploying

Vercel is **not** wired to auto-deploy from GitHub, so `git push` alone does not
ship anything. Link the project once, then deploy:

```bash
npx vercel link      # pick the existing portfolio project
npx vercel --prod
```

`NVIDIA_API_KEY` must also be set in the Vercel project's environment variables
for the Production environment, or the AI assistant will fail at runtime.

## Notes

- Never hard-code the API key. It is read from the environment in both
  `server.py` and `api/chat.py`; `.env` is gitignored.
- Case study screens are redrawn mockups with client branding and data removed.
- `public/images/_unused/` holds superseded images. It is gitignored and
  can be deleted once you are sure nothing is coming back.
