import cv2, os, numpy as np
from analyzer.tracker import SquatVideoTracker

tracker = SquatVideoTracker()
os.makedirs('evidence/audit_frames', exist_ok=True)

samples = [
    ('samples/common_sample.mp4', 'common'),
    ('samples/unsuitable_front_view.mp4', 'front_view'),
    ('samples/unsuitable_poor_framing_occlusion.mp4', 'framing_occl')
]

audit_log = []

for vid_path, name in samples:
    print(f'Auditing {name} ({vid_path})...')
    res = tracker.process_video(vid_path)
    total_f = res['total_frames']
    fps = res['fps']
    is_side = res['is_side_view']
    facing = res['dominant_facing']
    print(f'  {name}: {total_f} frames, fps={fps:.1f}, side_view={is_side}, facing={facing}')
    
    # Sample 8 equidistant timestamps
    step = max(1, total_f // 8)
    sample_indices = [min(total_f - 1, i * step) for i in range(8)]
    
    cap = cv2.VideoCapture(vid_path)
    for s_idx in sample_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, s_idx)
        ret, frame = cap.read()
        if not ret: continue
        
        f_info = res['frames_data'][s_idx]
        bar_pos = f_info.get('bar_pos')
        obs = f_info.get('observed_kpts', {})
        side = f_info.get('primary_side', 'left')
        
        vis = frame.copy()
        for k_name, k_data in obs.items():
            if k_data['is_observed']:
                pt = (int(k_data['pt'][0]), int(k_data['pt'][1]))
                color = (0, 255, 0) if side in k_name else (255, 128, 0)
                cv2.circle(vis, pt, 5, color, -1)
        
        if bar_pos is not None:
            bp = (int(bar_pos[0]), int(bar_pos[1]))
            cv2.circle(vis, bp, 10, (0, 0, 255), 2)
            cv2.putText(vis, 'BAR', (bp[0]+12, bp[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
        
        t_sec = s_idx / fps
        cv2.putText(vis, f'{name} f={s_idx} t={t_sec:.2f}s bar={bar_pos is not None}', (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
        out_file = f'evidence/audit_frames/{name}_f{s_idx:03d}.jpg'
        cv2.imwrite(out_file, vis)
        audit_log.append({
            'video': name,
            'frame': s_idx,
            'timestamp': round(t_sec, 2),
            'bar_detected': bar_pos is not None,
            'bar_pos': bar_pos,
            'primary_side': side,
            'facing_dir': f_info.get('facing_dir'),
            'out_file': out_file
        })
    cap.release()

print('Audit frames extracted successfully! Total images:', len(audit_log))
import json
with open('evidence/audit_frames_summary.json', 'w') as f:
    json.dump(audit_log, f, indent=2)
