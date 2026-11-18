Raw dataset (.track, .nodes, .arcs, .route per trip). Contents are git-ignored.
- raw/train/ — 80 training trips (fitting, CV, HPO)
- raw/student_test/ — 10 student-testing trips (model comparison)
- raw/evaluator_test/ — 10 evaluator trips: untouched during development; used only by the API on Laptop 1
- processed/ — derived tables built from train/student_test only
