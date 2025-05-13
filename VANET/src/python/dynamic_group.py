import numpy as np
from sklearn.cluster import DBSCAN
from typing import Dict, List, Tuple
import logging

class DynamicGroupManager:
    def __init__(self, min_samples: int = 3, eps: float = 0.5):
        """
        Initialize the dynamic group manager.
        
        Args:
            min_samples: Minimum points to form a cluster
            eps: DBSCAN neighborhood radius
        """
        self.min_samples = min_samples
        self.eps = eps
        self.previous_clusters = None
        self.logger = logging.getLogger(__name__)

    def compute_feature_vector(self, metrics: Dict) -> np.ndarray:
        """
        Compute feature vector for each RSU from raw metrics.
        
        Args:
            metrics: Dictionary of RSU metrics including vehicle density,
                        link loss, and centrality
            
        Returns:
            numpy array of feature vectors
        """
        return np.array([
            metrics.get('vehicle_density', 0),
            metrics.get('avg_link_loss', 0),
            metrics.get('degree_centrality', 0)
        ])

    def compute_jaccard_similarity(self, set1: set, set2: set) -> float:
        """
        Compute Jaccard similarity between two sets.
        """
        if not set1 or not set2:
            return 0.0
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0.0

    def form_groups(self, rsu_metrics: Dict[str, Dict]) -> Dict[str, int]:
        """
        Form dynamic groups based on current RSU metrics.
        
        Args:
            rsu_metrics: Dictionary of RSU metrics
            
        Returns:
            Dictionary mapping RSU IDs to group IDs
        """
        if not rsu_metrics:
            return {}
            
        # Compute feature vectors
        feature_vectors = []
        rsu_ids = []
        for rsu_id, metrics in rsu_metrics.items():
            feature_vectors.append(self.compute_feature_vector(metrics))
            rsu_ids.append(rsu_id)
            
        # Normalize features
        feature_vectors = np.array(feature_vectors)
        feature_vectors = (feature_vectors - feature_vectors.mean(axis=0)) / feature_vectors.std(axis=0)
        
        # Apply DBSCAN clustering
        clustering = DBSCAN(eps=self.eps, min_samples=self.min_samples)
        labels = clustering.fit_predict(feature_vectors)
        
        # Check stability with previous clusters
        current_clusters = {label: set() for label in set(labels)}
        for rsu_id, label in zip(rsu_ids, labels):
            current_clusters[label].add(rsu_id)
            
        if self.previous_clusters is not None:
            # Compute stability score
            stability_scores = []
            for current_label, current_set in current_clusters.items():
                if current_label == -1:  # Skip noise points
                    continue
                max_similarity = max(
                    self.compute_jaccard_similarity(current_set, prev_set)
                    for prev_set in self.previous_clusters.values()
                )
                stability_scores.append(max_similarity)
            
            # If stability is low, adjust parameters
            if stability_scores and np.mean(stability_scores) < 0.5:
                self.eps *= 0.9  # Reduce eps to form more stable clusters
                
        self.previous_clusters = current_clusters
        
        # Return group assignments
        return {rsu_id: int(label) for rsu_id, label in zip(rsu_ids, labels)}

    def get_group_transfer_weights(self, old_group: int, new_group: int) -> float:
        """
        Compute transfer learning weight when RSU moves between groups.
        
        Args:
            old_group: Previous group ID
            new_group: New group ID
            
        Returns:
            Transfer weight (alpha) between 0 and 1
        """
        # Simple implementation - can be made more sophisticated
        return 0.5 