# 07 — Visual Regression

## Learning Objectives
- Set up visual baselines for web pages
- Compare screenshots against baselines
- Handle visual differences and update baselines

## Concepts
`VisualComparator` takes screenshots and compares them pixel-by-pixel against stored baselines. On first run, baselines are created automatically. Set `UPDATE_VISUAL_BASELINES=1` to refresh baselines. Use `assert_match(threshold=0.01)` to allow minor rendering differences.

## Exercise
1. `exercise_01_baseline.py` — Create a baseline and compare against it

## Verification
```bash
pytest docs/playground/07_visual_regression/ -v
```
