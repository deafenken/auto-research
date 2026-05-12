# Hero image prompt — `docs/hero.png`

Drop the generated image into `docs/hero.png` (1024×1024 PNG, white-or-very-light
background). The README does not break without it — the mermaid pipeline
diagram is the canonical hero.

## Where to send this prompt

- **GPT-image-1** (`openai.images.generate(model="gpt-image-1", size="1024x1024", prompt=…)`)
- **Midjourney** (paste; add `--ar 1:1 --style raw`)
- **Gemini Image**
- **DALL·E 3** (1024×1024)

## Prompt (paste verbatim)

> A cartoon-illustration hero banner in the style of a friendly Notion blog
> header, warm cream-orange `#FFEDD5` background, crisp confident black
> linework with watercolor fills, soft drop shadows. Friendly, scholarly
> mood.
>
> **Left third** — a cartoon hand holding a phone. The phone screen shows a
> Telegram-style chat with one message bubble: `write me a NeurIPS paper
> on small-LM test-time compute`. Behind the phone is a code editor and a
> floating LaTeX paper preview with section headings (Abstract / Method /
> Experiments) visible. A small `.bib` sticker floats by.
>
> **Center** — five labeled icons in a clockwise circular flow with round
> connecting arrows: (1) "📋 Venue Setup" with NeurIPS/ICLR/ICML logos as
> stylized neutral chips, (2) "💡 Ideation" with three glowing lightbulbs
> labeled v1/v2/v3, (3) "📐 Method" with an equation `f(x) = ∇θ L`,
> (4) "🧪 Execution" with test tubes and a results.csv sticker,
> (5) "📄 Writing" with a paper page being rendered into PDF.
>
> **Right third** — a cute friendly mascot creature (stylized owl or fox
> reading a paper, not a real animal trademark), wearing tiny round glasses,
> holding a pen and a peer-review checklist. A magnifying glass examining
> a citation. A small `verified citations ✓` badge.
>
> **Overlay text, large chunky 3D-drop-shadow sans-serif**, two lines:
>
>   *(top)*    **Chat a Topic. Get a Paper.**
>   *(bottom small)*    auto-research · evidence-first · reviewer-aware · human-signed
>
> No real logos (no actual NeurIPS / ICLR / OpenAI / Anthropic logos —
> the venue chips are stylized neutral labels only). No celebrity faces,
> no real animal trademarks. Type must remain readable when downscaled
> to 800px on GitHub.
