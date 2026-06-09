#!/usr/bin/env python3
# src/main.py - Full implementation with roles, versioning, cache, break-glass
import json
import sys
from models import *
from cache import ScalingCache
from break_glass import emergency_break_glass

def load_conversion_table():
    try:
        with open("data/conversions.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "cup": 240, "tablespoon": 15, "teaspoon": 5,
            "g": 1, "kg": 1000, "ml": 1, "l": 1000, "each": 50
        }

def login() -> User:
    print("=== MUTTI'S BAKERY SYSTEM ===")
    username = input("Username: ")
    role_input = input("Role (admin/manager/baker): ").lower()
    if role_input == "admin":
        role = RoleType.ADMIN
    elif role_input == "manager":
        role = RoleType.MANAGER
    else:
        role = RoleType.BAKER
    return User(username, role)

def main():
    recipes = load_recipes_from_json("data/recipes.json")
    conversion_table = load_conversion_table()
    cache = ScalingCache()

    current_user = login()
    AuditLog.log("LOGIN", current_user.username, f"Role={current_user.role.value}")

    if current_user.role == RoleType.BAKER:
        print("\n👨‍🍳 BAKE MODE (read-only scaling only)")
        if not recipes:
            print("No recipes found.")
            return
        for rid, rec in recipes.items():
            print(f"- {rec.name} (ID: {rid})")
        rid = input("Enter recipe ID to scale: ")
        if rid not in recipes:
            print("Invalid ID")
            return
        recipe = recipes[rid]
        try:
            target = int(input("Portions (10-1000): "))
            cached = cache.get(rid, target)
            if cached:
                print("⚡ Cache hit (NFR-01):")
                scaled = cached
            else:
                scaled = recipe.scale(target, current_user)
                cache.set(rid, target, scaled)
            print("\nScaled recipe:")
            for ing, data in scaled.items():
                print(f"  {ing}: {data['rounded_g']}g ({data['note']})")
            print(recipe.expected_yield(target))
            AuditLog.log("SCALE_BAKER", current_user.username, f"Recipe {rid} to {target}")
        except Exception as e:
            print(f"Error: {e}")
            AuditLog.log("ERROR", current_user.username, str(e))
        return

    while True:
        print("\n--- MAIN MENU ---")
        print("1. List recipes")
        print("2. Add new recipe")
        print("3. Scale a recipe")
        print("4. Approve recipe (admin only)")
        print("5. Emergency break-glass (admin recovery)")
        print("6. Exit")
        choice = input("Choose: ")

        if choice == "1":
            for rid, rec in recipes.items():
                ver = rec.get_current_version()
                approved = ver.mutti_approved if ver else False
                print(f"{rid}: {rec.name} (approved={approved})")

        elif choice == "2":
            name = input("Recipe name: ")
            base = int(input("Base servings (e.g., 10): "))
            rid = name.lower().replace(" ", "_")
            if rid in recipes:
                print("Recipe ID exists. Use a different name.")
                continue
            recipe = Recipe(rid, name, base)
            ingredients = []
            while True:
                ing_name = input("Ingredient name (empty to stop): ")
                if not ing_name:
                    break
                amount = float(input("Amount: "))
                unit = input("Unit (cup, g, ml, tbsp, tsp, each, etc.): ")
                ing = Ingredient(ing_name, amount, unit)
                try:
                    ing.normalize(conversion_table)
                    ingredients.append(ing)
                except ValueError as e:
                    print(f"Error: {e}. Ingredient not added.")
            rules = []
            add_rule = input("Add non-linear rule? (y/n): ").lower()
            if add_rule == 'y':
                ing_name = input("Ingredient name: ")
                max_mult = float(input("Max multiplier (e.g., 1.5): "))
                threshold = int(input("Threshold servings: "))
                rules.append(NonLinearRule(ing_name, max_mult, threshold))
            approved = False
            if current_user.can_approve_recipe():
                ans = input("Approve this recipe now? (y/n): ").lower()
                approved = (ans == 'y')
            recipe.add_version(ingredients, rules, approved, current_user.username)
            recipes[rid] = recipe
            save_recipes_to_json("data/recipes.json", recipes)
            AuditLog.log("CREATE_RECIPE", current_user.username, f"Added {rid}")
            print("Recipe saved.")

        elif choice == "3":
            rid = input("Recipe ID: ")
            if rid not in recipes:
                print("Not found.")
                continue
            recipe = recipes[rid]
            target = int(input("Portions (10-1000): "))
            cached = cache.get(rid, target)
            if cached:
                print("⚡ Cache hit (fast response <2ms simulated)")
                scaled = cached
            else:
                scaled = recipe.scale(target, current_user)
                cache.set(rid, target, scaled)
            print("\nScaled ingredients:")
            for ing, data in scaled.items():
                print(f"  {ing}: {data['rounded_g']}g (original {data['original_g']}g) → {data['note']}")
            print(recipe.expected_yield(target))
            AuditLog.log("SCALE", current_user.username, f"{rid} to {target}")

        elif choice == "4":
            if not current_user.can_approve_recipe():
                print("❌ Only Mutti (admin) can approve recipes.")
                AuditLog.log("UNAUTHORIZED_APPROVE_ATTEMPT", current_user.username, "")
                continue
            rid = input("Recipe ID to approve: ")
            if rid not in recipes:
                print("Not found")
                continue
            recipe = recipes[rid]
            curr = recipe.get_current_version()
            if not curr:
                print("No version exists")
                continue
            recipe.add_version(curr.ingredients, curr.non_linear_rules, True, current_user.username)
            save_recipes_to_json("data/recipes.json", recipes)
            AuditLog.log("APPROVE_RECIPE", current_user.username, rid)
            print(f"✅ Recipe '{recipe.name}' approved by Mutti.")

        elif choice == "5":
            if current_user.role == RoleType.ADMIN:
                print("You are already admin. No need for break-glass.")
                continue
            temp_admin = emergency_break_glass()
            if temp_admin:
                rid = input("Recipe ID to force-approve: ")
                if rid in recipes:
                    recipe = recipes[rid]
                    recipe.add_version(recipe.get_current_version().ingredients,
                                       recipe.get_current_version().non_linear_rules,
                                       True, temp_admin.username)
                    save_recipes_to_json("data/recipes.json", recipes)
                    AuditLog.log("BREAK_GLASS_APPROVE", temp_admin.username, rid)
                    print("Emergency approval done. Logging out.")
                else:
                    print("Invalid ID")
            break

        elif choice == "6":
            print("Goodbye.")
            break

if __name__ == "__main__":
    main()
