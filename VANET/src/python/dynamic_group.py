import numpy as np
from sklearn.cluster import DBSCAN
from typing import Dict, List, Tuple, Optional
import logging
import pandas as pd

class DynamicGroupManager:
    def __init__(self, min_samples: int = 3, eps: float = 0.5):
        """
        Initialize the dynamic group manager with dataset support.
        
        Args:
            min_samples: Minimum points to form a cluster
            eps: DBSCAN neighborhood radius
        """
        self.min_samples = min_samples
        self.eps = eps
        self.previous_clusters = None
        self.logger = logging.getLogger(__name__)
        
        # Dataset-related attributes
        self.distance_matrix = None
        self.location_mapping = {}
        self.pdr_data = None
        self.use_distance_features = False

    def load_routing_dataset(self, filepath: str):
        """
        Load the vehicle routing dataset containing distance matrix.
        
        Args:
            filepath: Path to the Vehicle Routing Dataset.csv
        """
        try:
            df = pd.read_csv("Data/Vehicle Routing Dataset.csv")
            
            # Extract location information
            self.location_mapping = {
                notation: location 
                for notation, location in zip(df['Notation'], df['Location'])
            }
            
            # Extract distance matrix
            distance_cols = [col for col in df.columns if 'Distance from' in col]
            self.distance_matrix = df[distance_cols].values
            
            # Convert to symmetric matrix (assuming undirected distances)
            n = len(self.distance_matrix)
            for i in range(n):
                for j in range(i+1, n):
                    # Use average if distances differ
                    avg_dist = (self.distance_matrix[i][j] + self.distance_matrix[j][i]) / 2
                    self.distance_matrix[i][j] = avg_dist
                    self.distance_matrix[j][i] = avg_dist
            
            self.use_distance_features = True
            self.logger.info(f"Loaded routing dataset with {len(self.location_mapping)} locations")
            
        except Exception as e:
            self.logger.error(f"Error loading routing dataset: {str(e)}")

    def load_pdr_dataset(self, filepath: str):
        """
        Load the PDR time-series dataset.
        
        Args:
            filepath: Path to the pdr_vs_time_dataset.csv
        """
        try:
            self.pdr_data = pd.read_csv("Data/pdr_vs_time_dataset.csv")
            self.pdr_data.set_index('Time (s)', inplace=True)
            self.logger.info(f"Loaded PDR dataset with {len(self.pdr_data)} time points")
        except Exception as e:
            self.logger.error(f"Error loading PDR dataset: {str(e)}")

    def get_distance_features(self, rsu_id: str, other_rsus: List[str]) -> float:
        """
        Get average distance from one RSU to others in the network.
        
        Args:
            rsu_id: Current RSU identifier
            other_rsus: List of other RSU identifiers
            
        Returns:
            Average distance to other RSUs
        """
        if self.distance_matrix is None or not self.use_distance_features:
            return 0.0
        
        try:
            # Convert RSU IDs to indices (assuming they map to locations)
            rsu_idx = int(rsu_id) if rsu_id.isdigit() else ord(rsu_id) - ord('A')
            distances = []
            
            for other_id in other_rsus:
                if other_id == rsu_id:
                    continue
                other_idx = int(other_id) if other_id.isdigit() else ord(other_id) - ord('A')
                if 0 <= rsu_idx < len(self.distance_matrix) and 0 <= other_idx < len(self.distance_matrix):
                    distances.append(self.distance_matrix[rsu_idx][other_idx])
            
            return np.mean(distances) if distances else 0.0
        except:
            return 0.0

    def compute_feature_vector(self, metrics: Dict, rsu_id: str = None, 
                             all_rsu_ids: List[str] = None, 
                             current_time: float = None) -> np.ndarray:
        """
        Enhanced feature vector computation incorporating dataset information.
        
        Args:
            metrics: Dictionary of RSU metrics including vehicle density,
                    link loss, and centrality
            rsu_id: Current RSU identifier (for distance features)
            all_rsu_ids: List of all RSU IDs (for distance computation)
            current_time: Current simulation time (for PDR features)
            
        Returns:
            numpy array of feature vectors
        """
        features = [
            metrics.get('vehicle_density', 0),
            metrics.get('avg_link_loss', 0),
            metrics.get('degree_centrality', 0)
        ]
        
        # Add distance-based features if available
        if self.use_distance_features and rsu_id and all_rsu_ids:
            avg_distance = self.get_distance_features(rsu_id, all_rsu_ids)
            # Normalize distance (assuming max distance is around 10-20 km)
            normalized_distance = avg_distance / 20.0
            features.append(normalized_distance)
        
        # Add PDR-based features if available
        if self.pdr_data is not None and current_time is not None:
            # Get PDR value at current time (with interpolation)
            time_idx = current_time % self.pdr_data.index.max()
            pdr = np.interp(time_idx, self.pdr_data.index, self.pdr_data['PDR'])
            # Use PDR to adjust link loss feature
            adjusted_link_loss = metrics.get('avg_link_loss', 0) * (1 - pdr)
            features[1] = adjusted_link_loss  # Replace original link loss
        
        return np.array(features)

    def form_groups(self, rsu_metrics: Dict[str, Dict], 
                   current_time: Optional[float] = None) -> Dict[str, int]:
        """
        Enhanced group formation using dataset information.
        
        Args:
            rsu_metrics: Dictionary of RSU metrics
            current_time: Current simulation time for PDR lookup
            
        Returns:
            Dictionary mapping RSU IDs to group IDs
        """
        if not rsu_metrics:
            return {}
            
        # Compute feature vectors with enhanced features
        feature_vectors = []
        rsu_ids = list(rsu_metrics.keys())
        
        for rsu_id, metrics in rsu_metrics.items():
            features = self.compute_feature_vector(
                metrics, 
                rsu_id=rsu_id,
                all_rsu_ids=rsu_ids,
                current_time=current_time
            )
            feature_vectors.append(features)
            
        # Normalize features
        feature_vectors = np.array(feature_vectors)
        if feature_vectors.shape[1] > 0:
            # Handle division by zero
            stds = feature_vectors.std(axis=0)
            stds[stds == 0] = 1.0
            feature_vectors = (feature_vectors - feature_vectors.mean(axis=0)) / stds
        
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
        
        # Return group assignments with location names if available
        result = {}
        for rsu_id, label in zip(rsu_ids, labels):
            result[rsu_id] = int(label)
            # Optionally add location name
            if self.location_mapping and rsu_id in self.location_mapping:
                result[f"{rsu_id}_location"] = self.location_mapping[rsu_id]
        
        return result

    def compute_jaccard_similarity(self, set1: set, set2: set) -> float:
        """
        Compute Jaccard similarity between two sets.
        """
        if not set1 or not set2:
            return 0.0
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0.0

    def get_group_transfer_weights(self, old_group: int, new_group: int, 
                                  rsu_id: str = None) -> float:
        """
        Enhanced transfer weight computation considering distance information.
        
        Args:
            old_group: Previous group ID
            new_group: New group ID
            rsu_id: RSU identifier for distance-based weighting
            
        Returns:
            Transfer weight (alpha) between 0 and 1
        """
        base_weight = 0.5
        
        # Adjust weight based on group similarity if we have cluster info
        if self.previous_clusters:
            old_members = self.previous_clusters.get(old_group, set())
            new_members = self.previous_clusters.get(new_group, set())
            similarity = self.compute_jaccard_similarity(old_members, new_members)
            
            # Higher similarity means higher transfer weight
            base_weight = 0.3 + (0.7 * similarity)
        
        return base_weight

    def visualize_groups(self, groups: Dict[str, int]) -> Dict[int, List[str]]:
        """
        Create a visualization-friendly representation of groups.
        
        Args:
            groups: Dictionary mapping RSU IDs to group IDs
            
        Returns:
            Dictionary mapping group IDs to lists of RSU IDs
        """
        group_viz = {}
        for rsu_id, group_id in groups.items():
            if group_id not in group_viz:
                group_viz[group_id] = []
            group_viz[group_id].append(rsu_id)
        
        # Add location names if available
        for group_id, members in group_viz.items():
            if self.location_mapping:
                group_viz[f"{group_id}_locations"] = [
                    self.location_mapping.get(m, f"Unknown_{m}") 
                    for m in members
                ]
        
        return group_viz