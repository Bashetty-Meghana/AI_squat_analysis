"""
AI Squat Coach — Consumer & Pro Edition
Grounded in Mark Rippetoe's Starting Strength: Basic Barbell Training.
Features:
- Beginner-Friendly Consumer Mode: Simple Form Score (0-100), Plain-English Mistake Breakdown,
  Traffic-Light Checklist, and Next-Set Actionable Fixes.
- Pro / Coach Mode Toggle: Deep Biomechanics, Angles, Velocity-Based Training (VBT),
  and exact Starting Strength textbook citations.
"""

import os
import tempfile
import json
import streamlit as st
import cv2
import numpy as np
import pandas as pd

from analyzer.tracker import SquatVideoTracker
from analyzer.biomechanics import SquatBiomechanicsAnalyzer
from analyzer.evaluator import SquatStandardsEvaluator
from analyzer.annotator import SquatVideoAnnotator

# Page setup
st.set_page_config(
    page_title="AI Squat Coach | Simple Form Check",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom High-End Styling (Consumer Friendly + Dark Modern Polish)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Main Container Polish */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    /* Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        border: 1px solid #334155;
        border-radius: 18px;
        padding: 24px 30px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38BDF8, #818CF8, #C084FC);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
        letter-spacing: -0.02em;
    }
    .hero-desc {
        color: #94A3B8;
        font-size: 1.05rem;
        margin-bottom: 12px;
    }

    /* Score Card */
    .score-container {
        background: #0F172A;
        border: 2px solid #334155;
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 8px 24px rgba(0,0,0,0.25);
    }
    .score-number {
        font-size: 4rem;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
        line-height: 1;
        margin-bottom: 6px;
    }
    .score-grade {
        font-size: 1.25rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }

    /* Action Tip Cards */
    .tip-card {
        background: #0F172A;
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 12px;
        border-left: 6px solid #38BDF8;
        border-top: 1px solid #1E293B;
        border-right: 1px solid #1E293B;
        border-bottom: 1px solid #1E293B;
    }
    .tip-card-danger {
        border-left-color: #EF4444;
        background: rgba(239, 68, 68, 0.05);
    }
    .tip-card-warning {
        border-left-color: #F59E0B;
        background: rgba(245, 158, 11, 0.05);
    }
    .tip-card-success {
        border-left-color: #10B981;
        background: rgba(16, 185, 129, 0.05);
    }
    .tip-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #F8FAFC;
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 4px;
    }
    .tip-body {
        font-size: 0.95rem;
        color: #CBD5E1;
        line-height: 1.5;
    }

    /* Checklist Grid */
    .checklist-item {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .checklist-name {
        font-weight: 600;
        color: #F8FAFC;
        font-size: 0.95rem;
    }
    .checklist-status-pass {
        background: #064E3B;
        color: #6EE7B7;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.78rem;
    }
    .checklist-status-fail {
        background: #7F1D1D;
        color: #FCA5A5;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.78rem;
    }

    /* Pro Mode KPI Card */
    .pro-kpi-card {
        background: #0F172A;
        border: 1px solid #1E293B;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        text-align: left;
    }
    .pro-kpi-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.6rem;
        font-weight: 700;
        color: #38BDF8;
    }
    .pro-kpi-lbl {
        font-size: 0.78rem;
        color: #64748B;
        text-transform: uppercase;
        font-weight: 700;
        margin-bottom: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Cache analyzers
@st.cache_resource
def get_tracker():
    return SquatVideoTracker()

@st.cache_resource
def get_biomechanics():
    return SquatBiomechanicsAnalyzer()

@st.cache_resource
def get_evaluator():
    return SquatStandardsEvaluator()

@st.cache_resource
def get_annotator():
    return SquatVideoAnnotator()

tracker = get_tracker()
biomech_analyzer = get_biomechanics()
evaluator = get_evaluator()
annotator = get_annotator()

# Helper: Compute Plain English Form Score & Beginner Guidance
def generate_simple_coaching_summary(eval_res, bio_res):
    reps = eval_res.get("repetitions", [])
    if not reps:
        return {
            "score": 0,
            "grade": "CANNOT ASSESS",
            "grade_color": "#EF4444",
            "headline": "Video Angle Unsuitable",
            "fixes": [{"type": "danger", "title": "Move Camera to 90° Side View", "desc": "We couldn't see your squat from the side. Place your phone at hip height, pointing directly at your side."}],
            "checklist": []
        }

    score = 100
    fixes = []
    checklist = []

    # Check Depth across all reps
    depth_passes = [r["depth_metrics"]["meets_standard"] for r in reps if "depth_metrics" in r]
    pass_count = sum(depth_passes)
    total_reps = len(depth_passes)

    if pass_count == total_reps:
        checklist.append({"name": "Squat Depth (Low Enough)", "status": "pass", "note": "Hit full depth on all reps!"})
        fixes.append({
            "type": "success",
            "title": "✅ Depth Was Perfect!",
            "desc": "You sank deep enough on every rep! Your hips dropped below your knees, engaging your full leg muscles and protecting your knees."
        })
    elif pass_count > 0:
        score -= 15 * (total_reps - pass_count)
        checklist.append({"name": "Squat Depth (Low Enough)", "status": "fail", "note": f"Passed on {pass_count}/{total_reps} reps"})
        fixes.append({
            "type": "danger",
            "title": "🔴 Squat 2 Inches Deeper",
            "desc": f"You stopped slightly high on {total_reps - pass_count} of your {total_reps} reps. On your next set, sink your hips about 1 to 2 inches lower until your hip crease drops below the top of your knee before standing up."
        })
    else:
        score -= 30
        checklist.append({"name": "Squat Depth (Low Enough)", "status": "fail", "note": "All reps were high"})
        fixes.append({
            "type": "danger",
            "title": "🔴 Squat Deeper (Below Knee Level)",
            "desc": "Your squats were high (above parallel). Next set, lower your hips until your hip crease is below the top of your knee so your glutes and hamstrings can do the work."
        })

    # Check Head / Eye Gaze
    looking_up = any(any(f["criterion_id"] == "eye_gaze_cervical_spine" and f["result"] == "DOES_NOT_MEET_STANDARD" for f in r["findings"]) for r in reps)
    if looking_up:
        score -= 10
        checklist.append({"name": "Head & Eye Direction", "status": "fail", "note": "Looking up at ceiling"})
        fixes.append({
            "type": "warning",
            "title": "🟡 Look at the Floor, Not the Ceiling",
            "desc": "You're tilting your head up to look at the mirror or ceiling. That puts unwanted strain on your neck. Keep your chin neutral and fix your eyes on a spot on the floor about 4 to 5 feet ahead."
        })
    else:
        checklist.append({"name": "Head & Eye Direction", "status": "pass", "note": "Neutral neck, eyes down"})
        fixes.append({
            "type": "success",
            "title": "✅ Great Head Position",
            "desc": "Your eyes stayed fixed downward on the floor, keeping your cervical spine safe and neutral under the bar."
        })

    # Check Back Posture
    back_bad = any(any(f["criterion_id"] == "back_angle_inclination" and f["result"] == "DOES_NOT_MEET_STANDARD" for f in r["findings"]) for r in reps)
    if back_bad:
        score -= 10
        checklist.append({"name": "Back Posture & Support", "status": "fail", "note": "Torso angle off target"})
        fixes.append({
            "type": "warning",
            "title": "🟡 Adjust Your Back Angle",
            "desc": "Your torso angle shifted off target. Keep your chest tight and maintain a natural ~45° incline without rounding your lower back."
        })
    else:
        checklist.append({"name": "Back Posture & Support", "status": "pass", "note": "Flat, strong back"})
        fixes.append({
            "type": "success",
            "title": "✅ Solid Back Posture",
            "desc": "Your spine stayed flat, strong, and supported throughout the entire set with zero rounding."
        })

    # Check Balance / Bar Path
    balance_bad = any(any(f["criterion_id"] == "bar_path_verticality_midfoot" and f["result"] == "DOES_NOT_MEET_STANDARD" for f in r["findings"]) for r in reps)
    if balance_bad:
        score -= 10
        checklist.append({"name": "Foot Balance (Midfoot)", "status": "fail", "note": "Bar drifted forward"})
        fixes.append({
            "type": "warning",
            "title": "🟡 Keep Weight Over Midfoot",
            "desc": "The barbell drifted slightly forward towards your toes. Keep the weight glued over the middle of your shoelaces to avoid wasting energy."
        })
    else:
        checklist.append({"name": "Foot Balance (Midfoot)", "status": "pass", "note": "Balanced over midfoot"})

    score = max(45, min(100, score))
    if score >= 90:
        grade = "EXCELLENT FORM (A)"
        grade_color = "#10B981"
        headline = "Outstanding Reps! Keep the Weight Moving."
    elif score >= 75:
        grade = "SOLID FORM (B+)"
        grade_color = "#38BDF8"
        headline = "Good Form with 1 or 2 Quick Fixes Needed."
    elif score >= 60:
        grade = "FAIR FORM (B)"
        grade_color = "#F59E0B"
        headline = "Solid Effort — Focus on Depth Before Adding More Weight."
    else:
        grade = "NEEDS WORK (C)"
        grade_color = "#EF4444"
        headline = "Form Needs Adjustment — Review the Tips Below."

    return {
        "score": score,
        "grade": grade,
        "grade_color": grade_color,
        "headline": headline,
        "fixes": fixes,
        "checklist": checklist
    }

# Hero Banner
st.markdown("""
<div class="hero-banner">
    <div class="hero-title">🏋️ AI Squat Form Coach</div>
    <div class="hero-desc">
        Record your squat from the side. Our AI analyzes your form and tells you <strong>exactly what mistakes you made and how to fix them on your next set</strong>.
    </div>
</div>
""", unsafe_allow_html=True)

# Session state init
if "selected_video_path" not in st.session_state:
    st.session_state.selected_video_path = "samples/common_sample.mp4"
    st.session_state.video_source_title = "Benchmark Squat Video (2 Reps)"

# Top Control Bar: Quick Sample or Upload
c_sample, c_upload = st.columns([1.1, 1.9])
with c_sample:
    st.markdown("##### ⚡ Quick Try (1-Click)")
    if st.button("🏋️ Load Sample Video (Real Lifter)", use_container_width=True):
        st.session_state.selected_video_path = "samples/common_sample.mp4"
        st.session_state.video_source_title = "Benchmark Squat Video (2 Reps)"
        st.rerun()
    if st.button("❌ Test Frontal Angle (Wrong View)", use_container_width=True):
        st.session_state.selected_video_path = "samples/unsuitable_front_view.mp4"
        st.session_state.video_source_title = "Frontal View (Incorrect Angle)"
        st.rerun()

with c_upload:
    st.markdown("##### 📤 Or Upload Your Own Squat Video")
    uploaded = st.file_uploader(
        "Upload any side-view squat video",
        type=["mp4", "mov", "avi", "webm"],
        label_visibility="collapsed"
    )
    if uploaded is not None:
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"up_{uploaded.name}")
        with open(temp_path, "wb") as f:
            f.write(uploaded.getbuffer())
        if st.session_state.selected_video_path != temp_path:
            st.session_state.selected_video_path = temp_path
            st.session_state.video_source_title = f"Uploaded: {uploaded.name}"
            st.rerun()

selected_video_path = st.session_state.get("selected_video_path")
video_title = st.session_state.get("video_source_title")

# Analysis Action
if selected_video_path and os.path.exists(selected_video_path):
    st.markdown("---")
    
    col_act, col_mode = st.columns([2, 1])
    with col_act:
        st.markdown(f"**Selected Video:** `{video_title}`")
        analyze_btn = st.button("🚀 Check My Squat Form Now", type="primary", use_container_width=True)

    with col_mode:
        st.markdown("**View Mode:**")
        pro_mode = st.toggle("🔍 Pro / Coach Mode (Show All Numbers & Citations)", value=False)

    cache_key = f"simple_analysis_{os.path.basename(selected_video_path)}"

    if analyze_btn:
        bar = st.progress(0, text="Tracking your movement & barbell...")
        def t_cb(p): bar.progress(int(p * 45), text=f"AI Vision tracking body joints... ({int(p*100)}%)")
        t_res = tracker.process_video(selected_video_path, progress_callback=t_cb)

        bar.progress(60, text="Checking depth & angles against Starting Strength rules...")
        b_res = biomech_analyzer.analyze_session(t_res)

        bar.progress(80, text="Creating friendly coaching feedback...")
        e_res = evaluator.evaluate_session(t_res, b_res)

        def a_cb(p): bar.progress(80 + int(p * 20), text="Rendering AI video highlights...")
        os.makedirs("output", exist_ok=True)
        annot_path = f"output/annotated_{os.path.basename(selected_video_path)}"
        annotator.generate_annotated_video(selected_video_path, annot_path, t_res, b_res, progress_callback=a_cb)
        bar.progress(100, text="Done!")

        st.session_state[cache_key] = {
            "t_res": t_res,
            "b_res": b_res,
            "e_res": e_res,
            "annot_path": annot_path,
            "source_path": selected_video_path
        }
        st.rerun()

    # Results Presentation
    if cache_key in st.session_state:
        res = st.session_state[cache_key]
        e_res = res["e_res"]
        b_res = res["b_res"]
        annot_path = res["annot_path"]
        reps = e_res.get("repetitions", [])
        
        # Calculate beginner-friendly summary
        coach_sum = generate_simple_coaching_summary(e_res, b_res)

        # Global Camera Error Alert (if wrong angle)
        if e_res.get("global_issues"):
            for issue in e_res["global_issues"]:
                st.error(f"⚠️ **Camera Problem**: {issue['title']}\n\n👉 **How to fix**: {issue['actionable_cue']}")

        st.markdown("<br>", unsafe_allow_html=True)

        # ==========================================
        # SECTION 1: BIG CONSUMER SCORE & WHAT TO FIX
        # ==========================================
        col_score, col_advice = st.columns([1, 2])

        with col_score:
            st.markdown(f"""
            <div class="score-container">
                <div style="font-size: 0.85rem; font-weight: 700; color: #94A3B8; text-transform: uppercase;">Overall Form Score</div>
                <div class="score-number" style="color: {coach_sum['grade_color']};">{coach_sum['score']}</div>
                <div class="score-grade" style="color: {coach_sum['grade_color']};">{coach_sum['grade']}</div>
                <div style="font-size: 0.9rem; color: #E2E8F0; margin-top: 8px;">{coach_sum['headline']}</div>
            </div>
            """, unsafe_allow_html=True)

            # Quick Traffic-Light Checklist
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("##### 📋 Form Checklist")
            for item in coach_sum["checklist"]:
                status_class = "checklist-status-pass" if item["status"] == "pass" else "checklist-status-fail"
                status_label = "PASS" if item["status"] == "pass" else "FIX NEEDED"
                st.markdown(f"""
                <div class="checklist-item">
                    <div>
                        <div class="checklist-name">{item['name']}</div>
                        <div style="font-size: 0.78rem; color: #94A3B8;">{item['note']}</div>
                    </div>
                    <span class="{status_class}">{status_label}</span>
                </div>
                """, unsafe_allow_html=True)

        with col_advice:
            st.markdown("##### 🎯 What to Fix on Your Next Set (Plain English)")
            st.caption("Here is exactly what you should focus on when you step up to the barbell next:")
            for fix in coach_sum["fixes"]:
                tip_class = f"tip-card-{fix['type']}"
                st.markdown(f"""
                <div class="tip-card {tip_class}">
                    <div class="tip-title">{fix['title']}</div>
                    <div class="tip-body">{fix['desc']}</div>
                </div>
                """, unsafe_allow_html=True)

        # ==========================================
        # SECTION 2: VIDEO REVIEW & BOTTOM POSITION PHOTOS
        # ==========================================
        st.markdown("---")
        st.markdown("### 🎬 Video Form Review & Bottom Turnaround Photos")
        st.caption("Watch your squat with AI visual lines showing your balance and bottom depth.")

        v_col1, v_col2 = st.columns(2)
        with v_col1:
            st.markdown("##### 📹 Original Video")
            st.video(res["source_path"])

        with v_col2:
            st.markdown("##### 🎯 AI Form Overlay (Look for the Green Depth Line)")
            if os.path.exists(annot_path):
                st.video(annot_path)

        # Turnaround Photos (Keyframes)
        if reps:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("##### 📸 Bottom Position Comparison (Did You Hit Depth?)")
            st.caption("A Starting Strength squat must sink until your hip crease drops below the top of your knee.")

            kf_cols = st.columns(min(len(reps), 4))
            cap = cv2.VideoCapture(annot_path if os.path.exists(annot_path) else res["source_path"])
            for idx, r in enumerate(reps):
                with kf_cols[idx % len(kf_cols)]:
                    b_frame = r["findings"][0]["supporting_evidence"]["frame_index"]
                    cap.set(cv2.CAP_PROP_POS_FRAMES, b_frame)
                    ret, k_img = cap.read()
                    if ret:
                        k_rgb = cv2.cvtColor(k_img, cv2.COLOR_BGR2RGB)
                        d_pass = r["depth_metrics"]["meets_standard"]
                        is_b = r["depth_metrics"].get("is_borderline", False)
                        d_cm = r["depth_metrics"].get("depth_margin_cm", 0.0)
                        if is_b:
                            status_txt = f"⚠️ BORDERLINE ({d_cm:+.1f} cm at knee level)"
                        elif d_pass:
                            status_txt = f"✅ PASSED ({d_cm:+.1f} cm below knee)"
                        else:
                            status_txt = f"❌ TOO HIGH ({abs(d_cm):.1f} cm above knee)"
                        st.image(k_rgb, caption=f"Rep {r['rep_id']}: {status_txt}")
            cap.release()

        # ==========================================
        # SECTION 3: PRO / COACH MODE (HIDDEN UNLESS TOGGLED)
        # ==========================================
        if pro_mode:
            st.markdown("---")
            st.markdown("### 🔬 Pro / Coach Mode: Technical Biomechanics & Starting Strength Citations")
            st.caption("Advanced data for personal trainers, biomechanists, and startup evaluators.")

            tab_vbt, tab_kin, tab_cite, tab_skill = st.tabs([
                "⚡ Velocity-Based Training (VBT)",
                "📊 Diagnostic Angles & Drift",
                "📚 Starting Strength Textbook Citations",
                "🧠 Agent Skill Schema (JSON)"
            ])

            # Pro Tab 1: VBT
            with tab_vbt:
                set_vbt = e_res.get("set_vbt_summary", {})
                pk1, pk2, pk3, pk4 = st.columns(4)
                with pk1:
                    st.markdown(f"""
                    <div class="pro-kpi-card">
                        <div class="pro-kpi-lbl">Set Mean Velocity (MCV)</div>
                        <div class="pro-kpi-val">{set_vbt.get('mean_set_velocity_mps', 0.0):.2f} m/s</div>
                        <div style="font-size:0.75rem; color:#94A3B8;">Dynamic Strength Zone</div>
                    </div>
                    """, unsafe_allow_html=True)
                with pk2:
                    st.markdown(f"""
                    <div class="pro-kpi-card">
                        <div class="pro-kpi-lbl">Set Velocity Loss %</div>
                        <div class="pro-kpi-val">{set_vbt.get('total_velocity_loss_pct', 0.0):.1f}%</div>
                        <div style="font-size:0.75rem; color:#94A3B8;">Neuromuscular Fatigue Indicator</div>
                    </div>
                    """, unsafe_allow_html=True)
                with pk3:
                    st.markdown(f"""
                    <div class="pro-kpi-card">
                        <div class="pro-kpi-lbl">Rep Tempo (Descent/Pse/Ascent)</div>
                        <div class="pro-kpi-val" style="font-size:1.35rem;">{set_vbt.get('mean_eccentric_duration_s', 0.0):.1f}s / {set_vbt.get('mean_pause_duration_s', 0.0):.1f}s / {set_vbt.get('mean_concentric_duration_s', 0.0):.1f}s</div>
                    </div>
                    """, unsafe_allow_html=True)
                with pk4:
                    cal = e_res.get("calibration", {})
                    st.markdown(f"""
                    <div class="pro-kpi-card">
                        <div class="pro-kpi-lbl">Scale Auto-Calibration</div>
                        <div class="pro-kpi-val">{cal.get('px_per_cm', 6.6):.1f} px/cm</div>
                        <div style="font-size:0.75rem; color:#94A3B8;">Tibial Shank (~40.0 cm)</div>
                    </div>
                    """, unsafe_allow_html=True)

                vbt_data = []
                for r in reps:
                    v = r.get("vbt", {})
                    vbt_data.append({
                        "Repetition": f"Rep {r['rep_id']}",
                        "Mean Velocity": f"{v.get('mean_velocity_mps', 0.0):.2f} m/s",
                        "Peak Velocity": f"{v.get('peak_velocity_mps', 0.0):.2f} m/s",
                        "Tempo": v.get("tempo_notation", "-"),
                        "Range of Motion": f"{v.get('concentric_rom_cm', 0.0):.1f} cm",
                        "Fatigue Zone": v.get("fatigue_zone", "-"),
                        "Estimated RIR": v.get("estimated_rir", "-")
                    })
                st.dataframe(pd.DataFrame(vbt_data), use_container_width=True, hide_index=True)

            # Pro Tab 2: Angles & Drift
            with tab_kin:
                for r in reps:
                    with st.expander(f"Repetition {r['rep_id']} Biomechanical Angles", expanded=True):
                        ak1, ak2, ak3 = st.columns(3)
                        b_ang = next((f["supporting_evidence"]["observed_measurement"] for f in r["findings"] if f["criterion_id"] == "back_angle_inclination"), "N/A")
                        drift = next((f["supporting_evidence"]["observed_measurement"] for f in r["findings"] if f["criterion_id"] == "bar_path_verticality_midfoot"), "N/A")
                        depth_m = next((f["supporting_evidence"]["observed_measurement"] for f in r["findings"] if f["criterion_id"] == "depth_below_parallel"), "N/A")
                        ak1.metric("Back Angle", b_ang)
                        ak2.metric("Depth Margin", depth_m)
                        ak3.metric("Bar Drift", drift)

            # Pro Tab 3: Citations
            with tab_cite:
                for r in reps:
                    st.markdown(f"##### 🏋️ Repetition {r['rep_id']} Starting Strength Verification")
                    for f in r["findings"]:
                        cat = f.get('category', 'biomechanics').upper()
                        st.markdown(f"- **{f['criterion_name']}** `[{cat}]`: `{f['result']}`")
                        st.markdown(f"  *Citation*: `{f.get('source_citation', 'Ref pp. 1-35')}`")
                        st.caption(f"  **Analysis**: {f['explanation']}")
                        if f.get("actionable_feedback"):
                            st.caption(f"  **Coaching Cue**: {f['actionable_feedback']}")
                        if f.get("uncertainty_and_limitations"):
                            st.caption(f"  ⚠️ *Limitations/Uncertainty*: {f['uncertainty_and_limitations']}")
                    st.markdown("---")

                st.markdown("##### 📐 What Starting Strength Criteria Cannot Be Assessed from a Side View")
                st.caption("A pure sagittal side view is necessary for depth, back angle, and bar path, but other criteria require coronal or posterior filming angles:")
                for na in e_res.get("non_assessable_side_view_criteria", []):
                    st.markdown(f"- **{na.get('criterion_name')}**: {na.get('standard_description')}")
                    st.caption(f"  *Why unassessable*: {na.get('why_unassessable')} (Citation: {', '.join(na.get('source_ref_pages', []))})")

            # Pro Tab 4: Skill Schema & Engine Status
            with tab_skill:
                st.markdown(f"**Evaluation Engine:** `{e_res.get('evaluation_engine', 'deterministic_grounded_rules')}`")
                st.markdown(f"**Skill Standards Version:** `{e_res.get('standards_version', '2.0.0')}`")
                st.markdown(f"**Source Document:** {e_res.get('source_document', {}).get('title')} by {e_res.get('source_document', {}).get('author')}")
                st.json(evaluator.standards)
