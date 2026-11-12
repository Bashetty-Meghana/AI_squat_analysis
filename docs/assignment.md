# HIRING ASSIGNMENT: Build an AI Squat Analysis Application

## Assignment Page 1

HIRING ASSIGNMENT  |  All roles and seniority levels
1
Build an AI squat analysis application
Open ended assignment for all roles and seniority levels
Why this assignment exists
We hire technical generalists who take an ambiguous customer objective and turn it into a working product.
AI agents enable one person to work across product, design, engineering, testing, sales and support. We
expect broad ownership backed by enough technical depth to verify the result and recognize when specialist
input is needed.
This is an open ended assignment for candidates across all roles and seniority levels. Your position within
the company, including your role and seniority, will be determined by the quality of your submission.
Demonstrate what you can build, how well you understand it and the judgment behind your decisions.
This exercise tests how effectively you use AI to tackle an unfamiliar, non-trivial problem. We value initiative,
resourcefulness and a shipped result, together with the judgment to distinguish a convincing demonstration
from a trustworthy assessment.
Your objective
Build a consumer-facing application that accepts a side-view video of a person performing barbell squats,
annotates the movement, and provides structured feedback against the attached reference document. You
may use any side-view squat video available online; you do not need to record your own. Include a run on
the common sample below so submissions can be compared on the same input.
Common sample: View squat video on YouTube
The reference PDF follows the assignment in this file. Parse it into a reusable skill for an AI agent embedded
in your application. The document must drive the assessment; generic squat advice from a model is not
enough. All candidates receive the same reference and common sample.
Time box and freedom
Time box the build to approximately 4-6 hours and report your actual time. Aim for an end-to-end working
prototype. This is a time box for exploring and demonstrating the solution, not an expectation of
production-grade accuracy across every video. Submit what works, what you verified and what remains
unresolved. We assess scope and judgment alongside delivery.
Choose web, Android or iOS, and any stack, models, agents, libraries or managed services. Use AI
extensively. You own the resulting behavior and should understand the important code and decisions,
regardless of who or what generated them.
Make reasonable assumptions and document them. Choose the smallest implementation that proves the
complete experience. We are assessing your ability to work through an unfamiliar, non-trivial problem, not
your prior knowledge of exercise science.


---

## Assignment Page 2

HIRING ASSIGNMENT  |  All roles and seniority levels
2
What the application must do
Turn the document into an agent skill
Extract the supplied standards into a reusable, inspectable set of instructions or rules that the embedded
agent actually uses. The format is your choice. Cite source pages or sections for each criterion and keep the
skill separate enough to update without rewriting the application. Identify which criteria can be assessed from
a side-view video and which cannot.
Accept and process a squat video
Let a user upload a side-view video and understand upload progress, processing status and any failure.
Support multiple repetitions. State supported formats, duration limits and recording requirements in the
interface.
Identify and annotate the movement
Identify and track the relevant visible landmarks, including hips, knees, ankles and the points needed to
estimate torso or back angle. Track the barbell and show its path. Identify repetitions and their bottom
positions. Return playable annotated video or synchronized video overlays, with markings that follow the
actual movement.
Make measurements and evidence understandable. Distinguish observed points from estimates. Handle
occlusion, poor framing and uncertain tracking explicitly; an unassessable result is preferable to invented
precision.
Assess against the supplied standards
Use the movement evidence and document-derived skill to assess each repetition. Present a clear overall
summary and structured findings. Each finding should include:
• The repetition and criterion being assessed, with its source section in the document.
 • A result of meets standard, does not meet standard, or cannot assess.
 • The supporting timestamp or frame, observed measurement where relevant, and a short explanation.
 • Actionable feedback grounded in the supplied standard, plus any uncertainty that affects the conclusion.
 Do not add unsupported thresholds or rules and present them as document requirements. Explain how the
system behaves when the document or video does not provide enough information.
Deliver a consumer experience
Make the path from upload to useful feedback feel coherent and polished. A non-technical user should
understand what happened, where the evidence is and what to do next. Use your judgment on visual design,
navigation and presentation.
The required upload > analysis > annotation > feedback flow must run on a newly uploaded video. Disclose
mocked components and manual steps. A prepared result or a video of an interface alone does not
demonstrate the working flow.


---

## Assignment Page 3

HIRING ASSIGNMENT  |  All roles and seniority levels
3
What to submit
 • A working application link or installable build, with any access instructions. A reproducible local launch is
 acceptable if hosting is impractical; explain the constraint.
• The source repository, document-derived skill and concise setup instructions, including required services
 and environment variable names. Do not include secret values.
• A short build note covering architecture, model and tool choices, actual time spent, approximate build and
 per-video costs, key trade-offs and known limitations.
• A brief account of how you used AI: what you delegated, what you inspected, and one meaningful mistake
 or failure you caught and corrected. Selected prompts or agent traces are welcome; an exhaustive
transcript is unnecessary.
• Evidence from the common sample video and at least one additional difficult or unsuitable recording. Show
 what you verified about landmark placement, bar path, source grounding and final feedback. If the
common sample is inaccessible, report that and identify your substitute.
Demonstration and discussion
Prepare a 15-minute walkthrough: about 5 minutes presenting the product and its value to a prospective
customer, then 10 minutes demonstrating the application and explaining how it works. We may supply a new
video or change a rule in the source document during the review.
Be ready to explain the critical path through the system, investigate an incorrect result, and show how a
change to the skill affects the assessment. We want to see your understanding of what the AI produced.
How we evaluate
Accuracy and defensible evidence carry more weight than visual polish. A simpler application with verified
results will score above a polished one with incorrect annotations or unsupported conclusions.
• Ownership and delivery - Did you make progress through ambiguity, resolve obstacles and ship a useful
 core experience with a clear account of unfinished work?
• AI fluency and understanding - Did you use agents effectively, verify their output and demonstrate
 command of the resulting system?
• Architecture and efficiency - Are the choices appropriate to the time box, with sensible trade-offs in
 accuracy, complexity, latency and cost?
• Evidence and reliability - Do annotations match the video, do conclusions follow the supplied standards,
 and are limitations represented honestly?
• Product and commercial judgment - Is the experience usable, and can you discover a customer need,
 communicate value and respond thoughtfully to objections and changed constraints?
The decisive question is what you shipped, what you verified, what you understood and how you responded
when it failed. Sound technical judgment and honest limitations matter more than confident claims.
Reference PDF follows
Document_for_skill.pdf is appended in full on the following pages. Use this reference to build the agent skill.
Cite its page numbers as reference pages 1-35 (combined PDF pages 4-38).


---

