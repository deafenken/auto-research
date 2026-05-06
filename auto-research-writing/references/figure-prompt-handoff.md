# Figure Prompt Handoff

Use this when the paper needs conceptual figures such as:

- method pipeline diagrams
- architecture overviews
- idea schematics
- training or inference flowcharts
- comparison diagrams showing "before vs after"

## Principle

If the in-agent drawing quality is likely to be poor, do not fake a bad figure. Instead:

1. reserve the figure in `paper.tex`,
2. define its role clearly in `figure_plan.md`,
3. save a strong external-generation prompt for the user.

This workflow is especially useful when the user prefers a dedicated image model such as Gemini or GPT-image for diagram quality.

## Provider-specific guidance

For text-heavy scientific diagrams, treat image-model choice as part of the prompt strategy.

- `Gemini / Nano Banana`: especially strong when the figure needs real text labels rendered directly into the image.
- `GPT-image`: also suitable, but still use the same high-discipline prompt structure.

When a figure contains many node labels, arrows, captions, or module names, default to **English prompts** even if the final paper is in Chinese. This reduces spelling mistakes and improves the model's understanding of academic terminology. If a Chinese version is needed later, replace labels in a vector editor after generation.

## Text-rendering rules

When the figure includes visible labels, explicitly instruct the model to:

1. use a legible sans-serif font,
2. spell the listed labels **exactly**,
3. keep text sharp and readable at paper scale,
4. avoid decorative typography,
5. keep labels short and structurally important.

If the figure depends on correct wording, include a dedicated section:

```markdown
Required labels:
- ...
- ...

Text constraints:
- exactly spell all labels as written
- no extra text
- use a clean sans-serif font
- keep all labels readable at conference-paper size
```

## Required outputs

For each figure:

- `figures/<name>.pdf` or `figures/<name>.png`
  - this may be missing at draft time; the LaTeX should still reference it as the intended output path
- `figure_prompts/<name>.md`
  - the prompt the user can paste into Gemini, GPT-image, or another image model
- one row in `figure_plan.md`
  - figure name, section, purpose, status, and source prompt file

## What `figure_plan.md` should contain

Use a compact table or bullet list with:

- figure filename
- paper section where it appears
- figure purpose
- visual type: flowchart, pipeline, concept map, comparison diagram, etc.
- status: `placeholder`, `generated externally`, or `finalized`
- prompt file path

## Prompt-writing rules

Each prompt should be self-contained and should specify:

1. the scientific content to depict,
2. the diagram type,
3. the desired visual style,
4. the labels and text that must appear,
5. the layout constraints,
6. what must be avoided.

## Good prompt structure

```markdown
# Prompt for External Image Model

Goal:
Create a clean research-paper flowchart for the method pipeline.

Content:
- show input, retrieval, verifier, adaptive controller, final output
- emphasize that the controller decides whether to spend more test-time compute

Style:
- white background
- crisp vector-like academic figure style
- minimal color palette
- readable text at paper scale

Layout:
- left-to-right flow
- main path thick arrows
- optional feedback loop as dashed arrow

Required labels:
- Input Question
- Base LM Draft
- Verifier Score
- Adaptive Compute Controller
- Refined Answer

Avoid:
- 3D effects
- cartoon styling
- excessive gradients
- tiny unreadable labels
```

## High-end scientific-diagram template

Use this when generating a polished mechanism diagram or system flowchart with strong text rendering requirements.

```markdown
# Prompt for External Image Model

Create a flat vector, academic-style scientific methodology diagram for a top-tier computer science paper.

Topic:
<one-sentence description of the method / framework>

Layout:
- <top-to-bottom | left-to-right | two-column comparison>

Components and workflow:
- <layer or block 1, with exact label and icon idea>
- <layer or block 2, with exact label and icon idea>
- <layer or block 3, with exact label and icon idea>
- specify arrows, loops, dashed boxes, feedback paths, and grouping

Required labels:
- <exact label 1>
- <exact label 2>
- <exact label 3>

Text constraints:
- exactly spell all labels as written above
- use a highly legible sans-serif font
- no spelling mistakes
- no extra text outside the requested labels

Style constraints:
- clean, minimalist lines
- strictly flat design
- no 3D, no shadows
- professional academic figure style suitable for a top-tier conference paper
- white background
- restrained academic color palette

Color palette:
- muted navy blue
- slate gray
- soft teal

Layout constraints:
- balanced spacing
- clear visual hierarchy
- arrows easy to follow
- all text readable at paper scale

Aspect ratio:
- <16:9 | 4:3 | square as needed>

Avoid:
- photorealism
- hand-drawn style
- clip-art look
- excessive gradients
- crowded composition
- tiny labels
```

## Nano Banana / Gemini-optimized example

The following is a strong reference pattern for text-heavy scientific diagrams:

```markdown
A flat vector, academic-style scientific methodology diagram illustrating an "Intelligent Agent Framework for Automated Scientific Research".

Layout: Top-to-bottom pipeline.

Components & Workflow:

Top layer (Input): Labeled "Literature & Log Data Ingestion", showing database and document icons.

Middle layer (Core Mechanism): Labeled "Multi-Agent Collaboration Loop". Inside a dashed bounding box, show three interacting nodes: "Search Agent" (magnifying glass icon), "Reasoning Agent" (brain or gear icon), and "Writing Agent" (pen or document icon). Draw curved arrows connecting them in a cyclic loop.

Bottom layer (Output): Labeled "Automated Paper Generation", showing a formatted scientific paper icon.
Use straight downward arrows to connect the three main layers.

Style constraints:

Clean, minimalist lines, strictly flat design (no 3D, no shadows).

Academic color palette: muted navy blue, slate gray, and soft teal.

Background: Solid white.

Text: Highly legible, sharp sans-serif font for all labels. Exactly spell out the words mentioned above. No decorative elements, highly professional suitable for a top-tier computer science conference paper (e.g., IEEE/ACM).

Aspect ratio: 16:9.
```

## How to adapt the example

Replace the content while preserving the structural discipline:

- swap the topic line with the actual method or framework,
- keep the explicit `Layout`, `Components & Workflow`, `Style constraints`, and `Text` sections,
- keep exact labels quoted when spelling matters,
- keep the academic style language if the figure is for a paper,
- only switch to Chinese labels after generation if necessary.

## LaTeX placeholder pattern

When the final image does not exist yet, still reserve the slot:

```tex
\begin{figure}[t]
  \centering
  % TODO: replace with externally generated figure at figures/pipeline_overview.pdf
  \fbox{\parbox{0.9\linewidth}{
    Placeholder for pipeline overview figure.\\
    See figure_prompts/pipeline_overview.md for the external image-model prompt.
  }}
  \caption{Overview of the proposed method pipeline. Final figure pending external generation.}
  \label{fig:pipeline_overview}
\end{figure}
```

## Default figure candidates

Unless the paper is extremely short, Stage 4 should usually consider:

1. one pipeline / method overview figure
2. one idea or mechanism diagram if the contribution is conceptually non-trivial
3. result plots only if Stage 3 already produced them cleanly

Do not create placeholder prompts for trivial bar charts that are better produced directly from data.
