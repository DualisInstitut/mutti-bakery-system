#!/bin/bash
echo "Setting up Mutti's Bakery project structure..."
mkdir -p src data logs
touch src/__init__.py src/models.py src/cache.py src/break_glass.py src/main.py
touch data/recipes.json data/conversions.json
touch logs/app.log
echo "✅ Done. Directories: src/, data/, logs/"
