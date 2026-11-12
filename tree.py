"""
Interpretability Module: Feature Encoding and Decision Tree Representation
Implementing Section 2.3 & 2.4 of Bertsimas & Paskov (MIT).

Features:
- 15 binary features per guess (3 color states x 5 letter positions)
- 15n features for an n-guess history
- Decision tree policy generation & interactive tree structure export
- Path tracing through the decision tree for any game state
"""

import json
import os
from typing import List, Dict, Any, Tuple, Optional
from sklearn.tree import DecisionTreeClassifier

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
SALET_G2_FILE = os.path.join(DATA_DIR, 'salet_g2_table.json')


def get_feature_names() -> List[str]:
    """Generates the 15 feature names for 5 Wordle tile positions."""
    colors = ['green', 'yellow', 'gray']
    names = []
    for pos in range(5):
        for col in colors:
            names.append(f'tile_{pos+1}_{col}')
    return names


def encode_coloring(coloring: str) -> List[int]:
    """
    Transforms a 5-tile coloring string ('G', 'Y', 'X') into a 15-dimensional binary vector.
    Section 2.4:
      Position i:
        Feature 3i + 0: 1 if Green else 0
        Feature 3i + 1: 1 if Yellow else 0
        Feature 3i + 2: 1 if Gray else 0
    """
    feat = [0] * 15
    for i, ch in enumerate(coloring):
        base = i * 3
        if ch == 'G':
            feat[base + 0] = 1
        elif ch == 'Y':
            feat[base + 1] = 1
        else:
            feat[base + 2] = 1
    return feat


def encode_history(colorings: List[str]) -> List[int]:
    """Encodes a sequence of n colorings into a 15n binary feature vector."""
    res = []
    for c in colorings:
        res.extend(encode_coloring(c))
    return res


class InterpretableTreePolicy:
    """Trains and visualizes decision tree policies over the 15n feature space."""

    def __init__(self, max_depth: int = 10):
        self.max_depth = max_depth
        self.model: Optional[DecisionTreeClassifier] = None
        self.words: List[str] = []
        self.word_to_idx: Dict[str, int] = {}
        self.idx_to_word: Dict[int, str] = {}
        self.feature_names = get_feature_names()
        self.trained_data: Dict[str, str] = {}

    def train_on_salet_g2(self, g2_table: Optional[Dict[str, str]] = None):
        """Trains the decision tree on the 148 second guesses from SALET."""
        if g2_table is None:
            if os.path.exists(SALET_G2_FILE):
                with open(SALET_G2_FILE, 'r', encoding='utf-8') as f:
                    g2_table = json.load(f)
            else:
                g2_table = {}

        self.trained_data = dict(g2_table)
        self.words = sorted(list(set(g2_table.values())))
        self.word_to_idx = {w: i for i, w in enumerate(self.words)}
        self.idx_to_word = {i: w for i, w in enumerate(self.words)}

        X = []
        y = []
        for col, word in g2_table.items():
            X.append(encode_coloring(col))
            y.append(self.word_to_idx[word])

        self.model = DecisionTreeClassifier(
            max_depth=self.max_depth,
            criterion='entropy',
            random_state=42
        )
        self.model.fit(X, y)
        return self

    def predict(self, coloring: str) -> str:
        """Predicts the optimal guess word given the coloring of the first move."""
        if not self.model:
            raise ValueError('Model not trained yet.')
        feat = [encode_coloring(coloring)]
        idx = int(self.model.predict(feat)[0])
        return self.idx_to_word[idx]

    def export_tree_json(self) -> Dict[str, Any]:
        """
        Exports the trained decision tree into a clean JSON structure suitable for
        interactive frontend rendering (reproducing Figure 2 & Figure 5).
        """
        if not self.model:
            self.train_on_salet_g2()

        tree_ = self.model.tree_

        def recurse(node_id: int, depth: int) -> Dict[str, Any]:
            if tree_.feature[node_id] != -2:  # split node
                feat_idx = int(tree_.feature[node_id])
                feat_name = self.feature_names[feat_idx]
                pos = feat_idx // 3 + 1
                color_type = ['Green', 'Yellow', 'Gray'][feat_idx % 3]

                # Tile condition representation for UI
                tile_condition = {
                    'position': pos,
                    'color': color_type.lower(),
                    'question': f'Is Tile {pos} {color_type}?'
                }

                left_child = recurse(int(tree_.children_left[node_id]), depth + 1)
                right_child = recurse(int(tree_.children_right[node_id]), depth + 1)

                return {
                    'type': 'split',
                    'node_id': node_id,
                    'depth': depth,
                    'feature_index': feat_idx,
                    'feature_name': feat_name,
                    'condition': tile_condition,
                    'left': left_child,   # <= 0.5 (No)
                    'right': right_child  # > 0.5 (Yes)
                }
            else:  # leaf node
                class_idx = int(tree_.value[node_id].argmax())
                word = self.idx_to_word.get(class_idx, 'unknown')
                return {
                    'type': 'leaf',
                    'node_id': node_id,
                    'depth': depth,
                    'action': word.upper(),
                    'samples': int(tree_.n_node_samples[node_id])
                }

        return {
            'root_guess': 'SALET',
            'depth': int(self.model.get_depth()),
            'leaves_count': int(self.model.get_n_leaves()),
            'tree': recurse(0, 0)
        }

    def trace_path(self, coloring: str) -> List[Dict[str, Any]]:
        """
        Traces the exact decision sequence (nodes visited and decisions made)
        for a given coloring.
        """
        if not self.model:
            self.train_on_salet_g2()

        feat = encode_coloring(coloring)
        tree_ = self.model.tree_
        curr = 0
        path = []

        while tree_.feature[curr] != -2:
            feat_idx = int(tree_.feature[curr])
            feat_name = self.feature_names[feat_idx]
            pos = feat_idx // 3 + 1
            color_type = ['Green', 'Yellow', 'Gray'][feat_idx % 3]
            is_active = feat[feat_idx] == 1

            path.append({
                'node_id': curr,
                'question': f'Tile {pos} is {color_type}?',
                'evaluated_true': is_active,
                'tile_position': pos,
                'tile_color': color_type.lower()
            })

            if not is_active:
                curr = int(tree_.children_left[curr])
            else:
                curr = int(tree_.children_right[curr])

        class_idx = int(tree_.value[curr].argmax())
        leaf_word = self.idx_to_word.get(class_idx, '')
        path.append({
            'node_id': curr,
            'is_leaf': True,
            'recommended_guess': leaf_word.upper()
        })
        return path

