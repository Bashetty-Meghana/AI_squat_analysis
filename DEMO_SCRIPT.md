# Live Demonstration Script: AI Squat Form Coach

This guide provides a structured 5-minute executive pitch and 10-minute technical demonstration walkthrough suitable for startup founders, engineering leads, and investors.

---

## Part 1: The 5-Minute Executive Pitch

### The Hook (Minute 0:00 - 1:00)
> *"Over 50 million people squat every week in gyms around the world. But 80% of lifters either cut their depth too high—risking knee patellar tendonitis—or collapse their back forward into a dangerous 'good morning'. High-end personal trainers cost $100 an hour, and generic fitness apps only count reps without checking whether your form is actually safe.*
>
> *Introducing **IronPath AI**: the world's first consumer-grade AI squat coach grounded strictly in the gold standard of barbell biomechanics: Mark Rippetoe's Starting Strength. A lifter simply records their squat from the side, and within seconds, our computer-vision engine delivers a simple 0–100 form score and 2 actionable fixes in plain English before their next set."*

### The Technology & Moat (Minute 1:00 - 3:00)
> *"What makes IronPath AI fundamentally different from generic fitness apps is our three-layer engineering architecture:
> 1. **Computer Vision Accuracy**: We run YOLOv8s-pose with an adaptive One-Euro temporal filter and multi-modal barbell collar tracking with velocity gating. We don't guess—we track the true 2D sagittal plane.
> 2. **Scientific Grounding with Decoupled Standards**: Our coaching standards aren't hardcoded in python if/else spaghetti. They are codified in a validated, schema-compliant skill engine (`squat_standards.json`) that cites exact textbook pages, figures, and sections. If coaching science evolves, we can change a rule in JSON and update the entire platform dynamically.
> 3. **Honest AI with Boundary Uncertainty**: When a camera angle is wrong (like a front view) or depth is within a borderline margin ($\pm 0.8$ cm), we don't hallucinate a confident answer. We honestly output `CANNOT_ASSESS` and coach the user on how to film properly."*

### Product Duality & Business Model (Minute 3:00 - 5:00)
> *"IronPath AI features a dual-mode interface:
> - **Consumer Mode**: Designed for gym beginners. No confusing angles or jargon—just a big Form Score (0–100), a traffic-light checklist, and clear action cards: 'Squat 2 inches deeper' and 'Look at the floor, not the ceiling'.
> - **Pro / Coach Mode**: Built for powerlifting coaches, strength & conditioning facilities, and physical therapists. Unlocks full Velocity-Based Training (VBT) with concentric speed in $m/s$, tempo breakdown, Starting Strength textbook citations, and synchronized JSON overlay tracks.
> - **Business Model**: Freemium B2C ($9.99/month for lifters) + B2B SaaS ($99/month per gym rack/trainer). Local CPU execution means **zero recurring vision API costs**."*

---

## Part 2: The 10-Minute Technical Live Walkthrough

### Step 1: Launch the Application (0:00 - 1:30)
1. Open terminal and run:
   ```bash
   run.bat
   ```
2. Open your browser at `http://localhost:8501`.
3. Point out the dark-mode obsidian aesthetic, hero banner, and clean dual-mode toggle.

### Step 2: 1-Click Benchmark Analysis (1:30 - 4:00)
1. Click the button: **`🏋️ Load Sample Video (Real Lifter)`**.
2. Click **`🚀 Check My Squat Form Now`**.
3. Watch the real-time stage progress bar (Tracking body joints -> Checking depth against Starting Strength -> Rendering AI visual highlights).
4. **Showcase Consumer Mode**:
   - **Form Score Card**: Displays **75 / 100 (Solid Form B+)**.
   - **Traffic-Light Checklist**:
     - Squat Depth: High on Rep 1 (Pass on 1/2 reps).
     - Head & Eye Direction: Needs fix (looking up at ceiling).
     - Back Posture: Strong, supported back.
   - **Action Cards**:
     - *"🔴 Squat 2 Inches Deeper: You stopped slightly high on Rep 1. Sink your hips until your crease drops below the top of your knee."*
     - *"🟡 Look at the Floor, Not the Ceiling: Keep your chin neutral and fix eyes on a spot 4-5 feet ahead."*
   - **Bottom Position Comparison Photos**:
     - Rep 1 Keyframe: Labeled with high squat indicator.
     - Rep 2 Keyframe: Labeled with borderline/depth plane marker.

### Step 3: Toggle Pro / Coach Mode (4:00 - 6:30)
1. Switch the toggle: **`🔍 Pro / Coach Mode (Show All Numbers & Citations)`**.
2. **Tab 1: Velocity-Based Training (VBT)**:
   - Highlight Set Mean Velocity ($0.52\text{ m/s}$), Peak Velocity, and Rep Tempo ($2.1\text{s} - 0.2\text{s} - 1.5\text{s}$).
   - Show Fatigue Loss % and estimated Reps in Reserve (RIR).
3. **Tab 2: Diagnostic Angles & Drift**:
   - Review Back Angle ($60.6^\circ$ vs $45^\circ$ low-bar standard), Depth Margin in calibrated $cm$, and horizontal Bar Drift.
4. **Tab 3: Starting Strength Textbook Citations**:
   - Walk through the citations citing exact pages: *Ref p. 2, Ref p. 15, Ref p. 17 (Figure 2-1, Figure 2-10)*.
   - Show the honest disclosure of criteria that *cannot* be assessed from a side view (stance width, toe flare, knee valgus) with filming tips for next time.
5. **Tab 4: Skill Schema (JSON)**:
   - Inspect the live schema and the verified evaluation engine status.

### Step 4: Demonstrate Unsuitable Angle Handling (6:30 - 8:00)
1. Click **`❌ Test Frontal Angle (Wrong View)`**.
2. Click **`🚀 Check My Squat Form Now`**.
3. Show the instant **`CAMERA_ANGLE_ERROR`** alert banner:
   - *"The video was recorded from a frontal perspective. In Starting Strength, depth and bar path are defined in the sagittal plane. Camera must be positioned 90 degrees to the side at hip height."*
   - Notice that every sagittal criterion correctly reports **`CANNOT_ASSESS`** without guessing.

### Step 5: Live "Change the Rule" Demonstration (8:00 - 10:00)
1. Switch to terminal and run the decoupled demo script:
   ```bash
   python demo_rule_change.py
   ```
2. Explain the live demonstration:
   - Baseline evaluation evaluated a $60.6^\circ$ torso angle as `MEETS_STANDARD` (within $\le 62.0^\circ$ tolerance).
   - The script edited a single threshold in `skills/squat_standards.json` to $55.0^\circ$.
   - Re-evaluated the cached measurements **with NO code changes and NO video reprocessing**.
   - Show the finding dynamically flipping to `DOES_NOT_MEET_STANDARD` with updated coaching cues.
   - Conclude by showing the automated test suite passing 14/14 tests in 0.018s:
     ```bash
     python -m unittest discover tests -v
     ```
