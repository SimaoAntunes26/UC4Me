import numpy as np
from collections import deque

class STrack:
    def __init__(self, tlwh, score, cls):
        self.tlwh = np.asarray(tlwh, dtype=np.float32)
        self.score = score
        self.cls = cls
        self.track_id = 0
        self.frame_id = 0
        self.tlbr = self.tlwh_to_tlbr(self.tlwh)
        
    @staticmethod
    def tlwh_to_tlbr(tlwh):
        ret = np.asarray(tlwh)
        ret[2:] += ret[:2]
        return ret

class BYTETracker:
    def __init__(self, track_thresh=0.5, track_buffer=30, match_thresh=0.8):
        self.track_thresh = track_thresh
        self.match_thresh = match_thresh
        self.track_buffer = track_buffer
        self.tracks = []
        self.frame_count = 0
        self.max_time_lost = track_buffer
        self.next_id = 1

    def update(self, dets, img_shape):
        self.frame_count += 1
        activated_stracks = []
        lost_stracks = []
        removed_stracks = []
        
        # Convert detections to STrack objects
        detections = [STrack(d[:4], d[4], d[5]) for d in dets]
        
        # Simple tracking logic (replace with full ByteTrack implementation)
        for track in detections:
            track.track_id = self.next_id
            self.next_id += 1
            activated_stracks.append(track)
        
        self.tracks = [t for t in self.tracks if t not in removed_stracks]
        self.tracks = activated_stracks + lost_stracks
        
        return self.tracks