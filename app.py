"""
AI Squat Analysis Application
Consumer-facing web application grounded in Mark Rippetoe's Starting Strength: Basic Barbell Training.
Provides side-view barbell squat tracking, automated repetition segmentation, visual overlays,
and structured criteria evaluation with document citations.
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
    page_title="AI Squat Coach | Starting Strength Standards",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished consumer UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #0F172A;
    }
    .badge-pass {
        background-color: #DCFCE7;
        color: #166534;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        display: inline-block;
    }
    .badge-fail {
        background-color: #FEE2E2;
        color: #991B1B;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        display: inline-block;
    }
    .badge-warn {
        background-color: #FEF3C7;
        color: #92400E;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        display: inline-block;
    }
    .citation-tag {
        background-color: #EFF6FF;
        color: #1D4ED8;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 4px;
        border: 1px solid #BFDBFE;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 6px;
        font-weight: 600;
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

# Sidebar: Instructions & Camera Guidelines
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/barbell.png", width=64)
    st.title("AI Squat Coach")
    st.caption("Grounded in Mark Rippetoe's *Starting Strength*")
    
    st.markdown("---")
    st.subheader("📋 Recording Requirements")
    st.markdown("""
    - **Camera Angle**: Pure 90° side view (sagittal plane).
    - **Camera Height**: Mid-thigh / hip level.
    - **Framing**: Keep entire lifter and barbell visible from head to feet throughout all repetitions.
    - **Lighting**: Clear contrast between lifter, plates, and background.
    - **Supported Formats**: MP4, MOV, AVI, WEBM.
    - **Recommended Duration**: 5 to 60 seconds.
    """)
    
    st.markdown("---")
    st.subheader("📚 Source Document Reference")
    st.markdown("""
    **Starting Strength: Basic Barbell Training**  
    *Chapter 2: The Squat*  
    Reference Pages: **1–35**  
    Combined PDF Pages: **4–38**  
    
    *Skill Definition*: `skills/squat_standards.json`
    """)

# Main Page Header
st.markdown('<div class="main-header">Barbell Squat Biomechanical Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Upload a side-view squat recording or test with benchmark samples to receive movement annotations and structured feedback grounded in Starting Strength.</div>', unsafe_allow_html=True)

# Initialize session state for selected video
if "selected_video_path" not in st.session_state:
    st.session_state.selected_video_path = "samples/common_sample.mp4"
    st.session_state.video_source_title = "Common Sample Video (YouTube Reference)"

# Sample selector buttons & File Uploader
col_samples, col_upload = st.columns([1.2, 1.8])

with col_samples:
    st.markdown("##### ⚡ Quick Benchmark Samples")
    if st.button("🏋️ Common Sample (Hiring Assignment Video)", use_container_width=True):
        st.session_state.selected_video_path = "samples/common_sample.mp4"
        st.session_state.video_source_title = "Common Sample Video (YouTube Reference)"
        st.rerun()
    if st.button("❌ Unsuitable Angle: Frontal View", use_container_width=True):
        st.session_state.selected_video_path = "samples/unsuitable_front_view.mp4"
        st.session_state.video_source_title = "Unsuitable Sample: Front View (Perspective Violation)"
        st.rerun()
    if st.button("⚠️ Unsuitable Framing & Occlusion", use_container_width=True):
        st.session_state.selected_video_path = "samples/unsuitable_poor_framing_occlusion.mp4"
        st.session_state.video_source_title = "Unsuitable Sample: Framing Cutoff & Safety Rack Occlusion"
        st.rerun()

with col_upload:
    st.markdown("##### 📤 Upload Your Own Squat Video")
    uploaded_file = st.file_uploader(
        "Choose a side-view video file (MP4, MOV, AVI, WEBM)",
        type=["mp4", "mov", "avi", "webm"],
        label_visibility="collapsed"
    )
    if uploaded_file is not None:
        temp_dir = tempfile.gettempdir()
        temp_video_path = os.path.join(temp_dir, f"uploaded_{uploaded_file.name}")
        with open(temp_video_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        if st.session_state.selected_video_path != temp_video_path:
            st.session_state.selected_video_path = temp_video_path
            st.session_state.video_source_title = f"Uploaded Video: {uploaded_file.name}"
            st.rerun()

selected_video_path = st.session_state.get("selected_video_path")
video_source_title = st.session_state.get("video_source_title")

# State management for analysis
if selected_video_path and os.path.exists(selected_video_path):
    st.markdown("---")
    st.markdown(f"#### Active Recording: **{video_source_title}**")

    # Inspect video
    props = tracker.inspect_video_properties(selected_video_path)
    if props:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Resolution", f"{props['width']}x{props['height']}")
        m2.metric("Framerate", f"{props['fps']:.1f} FPS")
        m3.metric("Total Frames", props['frame_count'])
        m4.metric("Duration", f"{props['duration']:.1f}s")

    # Processing block
    analysis_cache_key = f"analysis_{os.path.basename(selected_video_path)}"
    
    col_btn1, col_btn2 = st.columns([2, 1])
    with col_btn1:
        start_analysis = st.button("🚀 Analyze Squat Video", type="primary", use_container_width=True)
    with col_btn2:
        if analysis_cache_key in st.session_state:
            st.success("✅ Analysis Loaded")

    if start_analysis:
        progress_bar = st.progress(0, text="Initializing YOLOv8-pose model...")
        
        # Step 1: Tracking
        def track_cb(pct):
            progress_bar.progress(int(pct * 45), text=f"Tracking lifter & barbell... ({int(pct*100)}%)")

        track_res = tracker.process_video(selected_video_path, progress_callback=track_cb)
        
        # Step 2: Biomechanics
        progress_bar.progress(55, text="Computing Starting Strength diagnostic angles & depth margins...")
        bio_res = biomech_analyzer.analyze_session(track_res)
        
        # Step 3: Evaluation against Starting Strength standards
        progress_bar.progress(75, text="Evaluating against Starting Strength criteria & source citations...")
        eval_res = evaluator.evaluate_session(track_res, bio_res)
        
        # Step 4: Render annotated video
        def annot_cb(pct):
            progress_bar.progress(75 + int(pct * 25), text=f"Rendering browser-ready H.264 annotated video... ({int(pct*100)}%)")

        os.makedirs("output", exist_ok=True)
        annotated_path = f"output/annotated_{os.path.basename(selected_video_path)}"
        annotator.generate_annotated_video(selected_video_path, annotated_path, track_res, bio_res, progress_callback=annot_cb)
        progress_bar.progress(100, text="Analysis complete!")
        
        st.session_state[analysis_cache_key] = {
            "track_res": track_res,
            "bio_res": bio_res,
            "eval_res": eval_res,
            "annotated_path": annotated_path,
            "source_path": selected_video_path
        }
        st.rerun()

    # If results exist in session state, display them
    if analysis_cache_key in st.session_state:
        results = st.session_state[analysis_cache_key]
        eval_res = results["eval_res"]
        bio_res = results["bio_res"]
        track_res = results["track_res"]
        annotated_path = results["annotated_path"]
        reps = eval_res["repetitions"]
        session_sum = eval_res["session_summary"]

        # Global alerts / camera issues
        if eval_res["global_issues"]:
            for issue in eval_res["global_issues"]:
                st.error(f"⚠️ **{issue['title']}**: {issue['message']}\n\n**Action Required**: {issue['actionable_cue']}")

        # Session summary banner
        grade_color = "#166534" if session_sum["grade"] == "COMPLIANT" else ("#991B1B" if "UNSUITABLE" in session_sum["grade"] else "#B45309")
        st.markdown(f"""
        <div style="background-color: #F8FAFC; border-left: 5px solid {grade_color}; padding: 16px; border-radius: 6px; margin: 15px 0;">
            <div style="font-size: 1.25rem; font-weight: 700; color: #0F172A;">{session_sum['headline']}</div>
            <div style="font-size: 1rem; color: #334155; margin-top: 6px;"><strong>Coaching Focus</strong>: {session_sum['primary_coaching_cue']}</div>
        </div>
        """, unsafe_allow_html=True)

        # Tabs for deep exploration
        tab_vid, tab_reps, tab_standards, tab_feasibility, tab_skill = st.tabs([
            "🎬 Video & Overlay Studio",
            "📊 Repetition Biomechanics",
            "📋 Grounded Criteria Findings",
            "🔍 Side-View Feasibility & Limitations",
            "🧠 Agent Skill Inspector"
        ])

        # TAB 1: Video Studio
        with tab_vid:
            v_col1, v_col2 = st.columns(2)
            with v_col1:
                st.markdown("##### 📹 Original Recording")
                st.video(results["source_path"])
            with v_col2:
                st.markdown("##### 🎯 AI Annotated Video (HUD & Overlays)")
                if os.path.exists(annotated_path):
                    st.video(annotated_path)
                    with open(annotated_path, "rb") as vf:
                        st.download_button(
                            "⬇️ Download Annotated Video (H.264 MP4)",
                            vf.read(),
                            file_name=f"annotated_{os.path.basename(selected_video_path)}",
                            mime="video/mp4"
                        )

            # Bottom Position Keyframe Gallery
            if reps:
                st.markdown("---")
                st.markdown("##### 📸 Bottom Position Keyframe Inspection (Depth Turnaround)")
                k_cols = st.columns(min(len(reps), 4))
                cap_temp = cv2.VideoCapture(annotated_path if os.path.exists(annotated_path) else results["source_path"])
                for idx, r in enumerate(reps):
                    with k_cols[idx % len(k_cols)]:
                        b_frame = r["findings"][0]["supporting_evidence"]["frame_index"]
                        cap_temp.set(cv2.CAP_PROP_POS_FRAMES, b_frame)
                        ret, k_img = cap_temp.read()
                        if ret:
                            k_img_rgb = cv2.cvtColor(k_img, cv2.COLOR_BGR2RGB)
                            st.image(k_img_rgb, caption=f"Rep {r['rep_id']} Bottom (Frame {b_frame}, {r['bottom_timestamp']:.2f}s)")
                cap_temp.release()

        # TAB 2: Repetition Biomechanics
        with tab_reps:
            if not reps:
                st.info("No complete repetitions detected for biomechanical breakdown.")
            else:
                rep_ids = [r["rep_id"] for r in reps]
                selected_rep_id = st.selectbox("Select Repetition to Inspect", rep_ids, format_func=lambda x: f"Repetition {x}")
                active_rep_eval = next(r for r in reps if r["rep_id"] == selected_rep_id)
                active_rep_bio = next(r for r in bio_res["repetitions"] if r["rep_id"] == selected_rep_id)

                # Telemetry Cards
                c1, c2, c3, c4 = st.columns(4)
                
                # Depth Card
                with c1:
                    d_pass = active_rep_bio["depth"]["meets_standard"]
                    d_val = active_rep_bio["depth"]["depth_margin_px"]
                    badge = '<span class="badge-pass">MEETS STANDARD</span>' if d_pass else '<span class="badge-fail">HIGH SQUAT</span>'
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Squat Depth</div>
                        <div class="metric-value">{d_val:+.1f} px</div>
                        <div>{badge}</div>
                        <div style="font-size:0.75rem; color:#64748B; margin-top:4px;">Ref p. 2 Fig 2-1 (Below Parallel)</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Bar Path Drift Card
                with c2:
                    bp_pass = active_rep_bio["bar_path"]["meets_standard"]
                    bp_val = active_rep_bio["bar_path"]["max_drift_px"]
                    badge = '<span class="badge-pass">BALANCED</span>' if bp_pass else '<span class="badge-fail">EXCESSIVE DRIFT</span>'
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Bar Path Drift</div>
                        <div class="metric-value">{bp_val:.1f} px</div>
                        <div>{badge}</div>
                        <div style="font-size:0.75rem; color:#64748B; margin-top:4px;">Ref p. 8 Fig 2-5 (Midfoot Balance)</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Back Angle Card
                with c3:
                    ba_pass = active_rep_bio["back_angle"]["meets_standard"]
                    ba_val = active_rep_bio["back_angle"]["bottom_angle_deg"]
                    badge = '<span class="badge-pass">OPTIMAL ~45°</span>' if ba_pass else '<span class="badge-fail">OFF TARGET</span>'
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Back Angle at Bottom</div>
                        <div class="metric-value">{ba_val:.1f}°</div>
                        <div>{badge}</div>
                        <div style="font-size:0.75rem; color:#64748B; margin-top:4px;">Ref p. 22 Fig 2-13 (Low-Bar Torso)</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Hip Drive Card
                with c4:
                    hd_pass = active_rep_bio["hip_drive"]["meets_standard"]
                    hd_shift = active_rep_bio["hip_drive"]["torso_angle_change_early"]
                    badge = '<span class="badge-pass">HIP DRIVE ACTIVE</span>' if hd_pass else '<span class="badge-fail">CHEST LEADING</span>'
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Hip Drive Initiation</div>
                        <div class="metric-value">{hd_shift:+.1f}° Shift</div>
                        <div>{badge}</div>
                        <div style="font-size:0.75rem; color:#64748B; margin-top:4px;">Ref p. 1 & 23 (Drive Butt Up)</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Motion Curves
                st.markdown("---")
                st.markdown("##### 📈 Kinematic Trajectory Charts")
                ts = bio_res["time_series"]
                df_chart = pd.DataFrame({
                    "Timestamp (s)": ts["timestamps"],
                    "Hip Elevation (px inverted)": ts["hip_y"],
                    "Back Angle (deg)": ts["back_angles"]
                }).set_index("Timestamp (s)")
                st.line_chart(df_chart)

        # TAB 3: Grounded Criteria Findings
        with tab_standards:
            st.markdown("##### 📖 Structured Criteria Assessment Against Starting Strength Standards")
            st.caption("Every criterion includes exact citations to the reference document (Ref pp. 1–35 / PDF pp. 4–38).")

            if not reps:
                st.warning("No repetitions could be evaluated due to unsuitable camera angle or framing.")
            else:
                rep_tabs = st.tabs([f"Repetition {r['rep_id']}" for r in reps])
                for idx, r in enumerate(reps):
                    with rep_tabs[idx]:
                        for f in r["findings"]:
                            result_style = "badge-pass" if f["result"] == "MEETS_STANDARD" else ("badge-fail" if f["result"] == "DOES_NOT_MEET_STANDARD" else "badge-warn")
                            with st.expander(f"{f['criterion_name']} — {f['result']}", expanded=(f["result"] != "MEETS_STANDARD")):
                                st.markdown(f"""
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                                    <span class="{result_style}">{f['result']}</span>
                                    <span class="citation-tag">Citation: {f['source_citation']}</span>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                st.markdown(f"**Source Section**: *{f['source_section']}*")
                                st.markdown(f"**Observed Measurement**: `{f['supporting_evidence']['observed_measurement']}` (at frame {f['supporting_evidence']['frame_index']}, {f['supporting_evidence']['timestamp_seconds']:.2f}s)")
                                st.markdown(f"**Standard Benchmark**: {f['supporting_evidence']['standard_benchmark']}")
                                st.markdown(f"**Biomechanical Analysis**: {f['explanation']}")
                                
                                if f["result"] == "DOES_NOT_MEET_STANDARD":
                                    st.error(f"**Actionable Coaching Cue**: {f['actionable_feedback']}")
                                elif f["result"] == "MEETS_STANDARD":
                                    st.success(f"**Coaching Confirmation**: {f['actionable_feedback']}")
                                else:
                                    st.warning(f"**Uncertainty Disclosure**: {f['uncertainty_and_limitations']}")

        # TAB 4: Side-View Feasibility & Limitations
        with tab_feasibility:
            st.markdown("##### 🔬 Side-View (Sagittal Plane) Feasibility & Explicit Limitations")
            st.markdown("""
            A critical requirement of the assignment is the honest disclosure of what can and cannot be measured from a 2D side-view video.
            The Starting Strength squat model establishes standards across multiple 3D planes. The table below discloses which criteria are assessable from a side view, and explains why unassessable criteria return `CANNOT_ASSESS` rather than invented precision.
            """)

            non_assessable_data = eval_res["non_assessable_side_view_criteria"]
            for item in non_assessable_data:
                with st.container():
                    st.markdown(f"""
                    <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:12px; margin-bottom:12px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <strong style="font-size:1.05rem; color:#0F172A;">{item['criterion_name']}</strong>
                            <span class="badge-warn">CANNOT ASSESS FROM SIDE VIEW</span>
                        </div>
                        <div style="font-size:0.85rem; color:#64748B; margin-top:4px;">
                            <strong>Section:</strong> <em>{item['source_section']}</em> | <strong>Citation:</strong> <span class="citation-tag">{item['citation']}</span>
                        </div>
                        <div style="font-size:0.9rem; color:#334155; margin-top:8px;">
                            <strong>Starting Strength Requirement:</strong> {item['standard_description']}
                        </div>
                        <div style="font-size:0.85rem; color:#B45309; margin-top:6px; background:#FEF3C7; padding:8px; border-radius:6px;">
                            <strong>Why Unassessable / System Behavior:</strong> {item['explanation']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # TAB 5: Document Skill Inspector
        with tab_skill:
            st.markdown("##### 🧠 Embedded Reusable Agent Skill (`skills/squat_standards.json`)")
            st.caption("Inspect the exact, version-controlled skill rules and citations loaded by the evaluation engine.")
            st.json(evaluator.standards)
