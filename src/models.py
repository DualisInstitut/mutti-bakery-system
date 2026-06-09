# src/models.py
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

# ---------- User Roles (FR-11) ----------
class RoleType(Enum):
    ADMIN = "Mutti"
    MANAGER = "Manager"
    BAKER = "Baker"

class User:
    def __init__(self, username: str, role: RoleType):
        self.username = username
        self.role = role

    def can_approve_recipe(self) -> bool:
        return self.role == RoleType.ADMIN

    def can_scale(self) -> bool:
        return True

    def can_audit_log(self) -> bool:
        return self.role in [RoleType.ADMIN, RoleType.MANAGER]

# ---------- Ingredient & Conversion ----------
class Ingredient:
    def __init__(self, name: str, original_amount: float, original_unit: str):
        self.name = name
        self.original_amount = original_amount
        self.original_unit = original_unit
        self.normalized_grams: Optional[float] = None
        self.is_ambiguous = self._check_ambiguity()

    def _check_ambiguity(self) -> bool:
        ambiguous = ["pinch", "to taste", "as needed", "handful"]
        return self.original_unit.lower() in ambiguous

    def normalize(self, conversion_table: Dict[str, float]):
        if self.is_ambiguous:
            raise ValueError(f"Ambiguous unit '{self.original_unit}' for {self.name}")
        if self.original_unit not in conversion_table:
            raise ValueError(f"No conversion rule for {self.original_unit}")
        self.normalized_grams = self.original_amount * conversion_table[self.original_unit]
        return self.normalized_grams

    def to_dict(self):
        return {
            "name": self.name,
            "original_amount": self.original_amount,
            "original_unit": self.original_unit,
            "normalized_grams": self.normalized_grams,
            "is_ambiguous": self.is_ambiguous
        }

    @classmethod
    def from_dict(cls, data):
        ing = cls(data["name"], data["original_amount"], data["original_unit"])
        ing.normalized_grams = data.get("normalized_grams")
        ing.is_ambiguous = data.get("is_ambiguous", False)
        return ing

class NonLinearRule:
    def __init__(self, ingredient_name: str, max_multiplier: float, threshold_servings: int):
        self.ingredient_name = ingredient_name
        self.max_multiplier = max_multiplier
        self.threshold = threshold_servings

    def to_dict(self):
        return {"ingredient_name": self.ingredient_name, "max_multiplier": self.max_multiplier, "threshold": self.threshold}

    @classmethod
    def from_dict(cls, data):
        return cls(data["ingredient_name"], data["max_multiplier"], data["threshold"])

# ---------- Recipe Versioning ----------
class RecipeVersion:
    def __init__(self, version_id: int, recipe_id: str, ingredients: List[Ingredient],
                 non_linear_rules: List[NonLinearRule], base_servings: int,
                 mutti_approved: bool, modified_by: str, timestamp: str):
        self.version_id = version_id
        self.recipe_id = recipe_id
        self.ingredients = ingredients
        self.non_linear_rules = non_linear_rules
        self.base_servings = base_servings
        self.mutti_approved = mutti_approved
        self.modified_by = modified_by
        self.timestamp = timestamp

    def to_dict(self):
        return {
            "version_id": self.version_id,
            "recipe_id": self.recipe_id,
            "ingredients": [i.to_dict() for i in self.ingredients],
            "non_linear_rules": [r.to_dict() for r in self.non_linear_rules],
            "base_servings": self.base_servings,
            "mutti_approved": self.mutti_approved,
            "modified_by": self.modified_by,
            "timestamp": self.timestamp
        }

class Recipe:
    def __init__(self, recipe_id: str, name: str, base_servings: int):
        self.recipe_id = recipe_id
        self.name = name
        self.base_servings = base_servings
        self.versions: List[RecipeVersion] = []
        self.current_version_id = 0

    def add_version(self, ingredients: List[Ingredient], rules: List[NonLinearRule],
                    mutti_approved: bool, modified_by: str) -> RecipeVersion:
        new_id = len(self.versions) + 1
        timestamp = datetime.now().isoformat()
        version = RecipeVersion(new_id, self.recipe_id, ingredients, rules,
                                self.base_servings, mutti_approved, modified_by, timestamp)
        self.versions.append(version)
        self.current_version_id = new_id
        return version

    def get_current_version(self) -> Optional[RecipeVersion]:
        if not self.versions:
            return None
        return self.versions[-1]

    def scale(self, target_servings: int, user: User) -> Dict[str, Any]:
        version = self.get_current_version()
        if not version:
            raise ValueError("Recipe has no version")
        if not version.mutti_approved and user.role != RoleType.ADMIN:
            raise PermissionError("Recipe not approved by Mutti. Only Mutti can scale unapproved recipes for testing.")

        if target_servings < 10 or target_servings > 1000:
            raise ValueError("Target servings must be between 10 and 1000")

        scaling_factor = target_servings / self.base_servings
        result = {}

        for ing in version.ingredients:
            if ing.normalized_grams is None:
                raise ValueError(f"Ingredient {ing.name} not normalized")
            rule = next((r for r in version.non_linear_rules if r.ingredient_name == ing.name), None)
            if rule and target_servings > rule.threshold:
                applied_factor = min(scaling_factor, rule.max_multiplier)
                note = f"Non-linear: capped at {rule.max_multiplier}x (>{rule.threshold})"
            else:
                applied_factor = scaling_factor
                note = "Linear scaling"

            scaled_grams = ing.normalized_grams * applied_factor
            rounded = self._round_quantity(scaled_grams)
            result[ing.name] = {
                "original_g": round(ing.normalized_grams, 1),
                "scaled_g": round(scaled_grams, 1),
                "rounded_g": rounded,
                "note": note
            }
        return result

    def _round_quantity(self, grams: float) -> float:
        if grams < 5:
            return round(grams * 2) / 2.0
        elif grams <= 100:
            return round(grams / 5) * 5
        else:
            return round(grams / 10) * 10

    def expected_yield(self, target_servings: int, piece_weight_grams: float = 65) -> str:
        version = self.get_current_version()
        if not version:
            return "No version available"
        total_weight = sum(ing.normalized_grams for ing in version.ingredients) * (target_servings / self.base_servings)
        pieces = total_weight / piece_weight_grams
        return f"Expected yield: ~{int(pieces)} pieces at approx. {piece_weight_grams}g each"

# ---------- Audit Log ----------
class AuditLog:
    LOG_FILE = "logs/app.log"

    @classmethod
    def log(cls, action: str, user: str, details: str):
        timestamp = datetime.now().isoformat()
        entry = f"[{timestamp}] USER={user} ACTION={action} DETAILS={details}\n"
        with open(cls.LOG_FILE, "a") as f:
            f.write(entry)
        print(f"📝 Logged: {action} by {user}")

# ---------- Persistence ----------
def load_recipes_from_json(filepath: str) -> Dict[str, Recipe]:
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {}

    recipes = {}
    for rid, rdata in data.items():
        recipe = Recipe(rid, rdata["name"], rdata["base_servings"])
        for vdata in rdata.get("versions", []):
            ingredients = [Ingredient.from_dict(i) for i in vdata["ingredients"]]
            rules = [NonLinearRule.from_dict(r) for r in vdata.get("non_linear_rules", [])]
            version = RecipeVersion(
                vdata["version_id"], rid, ingredients, rules,
                vdata["base_servings"], vdata["mutti_approved"],
                vdata["modified_by"], vdata["timestamp"]
            )
            recipe.versions.append(version)
        recipes[rid] = recipe
    return recipes

def save_recipes_to_json(filepath: str, recipes: Dict[str, Recipe]):
    data = {}
    for rid, recipe in recipes.items():
        data[rid] = {
            "name": recipe.name,
            "base_servings": recipe.base_servings,
            "versions": [v.to_dict() for v in recipe.versions]
        }
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
