# Additional papers supplied during development

Checked18 November2026. These notes distinguish inspected primary material from inaccessible full text.

- [HMM-PMM: A Parallel Hidden Markov Model-Based Map-Matching Framework for Large-Scale Trajectory Data](https://pmc.ncbi.nlm.nih.gov/articles/PMC13556171/): direct page access encountered a browser check; the primary indexed abstract was readable. It reorganizes candidate-pair shortest-path work through OD grouping and a distributed workflow. This supports examining repeated routing work if profiling finds a bottleneck. Our local ten-trip HMM inference total was10.70s, so a new distributed runtime was unnecessary. We retained bounded Dijkstra and its existing LRU cache. We did not implement its MapReduce, adaptive Floyd/A* or shortcut scheme, and do not claim full-text review or its reported speedup for our code.
- [Map-matching route reconstruction attack for differential privacy protected location data](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7369078): the abstract/PDF endpoint returned403; primary indexed metadata describes a route-reconstruction attack on DP-perturbed locations. It is background for privacy threat modeling, rather than evidence to change our training objective. No method or results from that paper were copied or claimed as implemented.

The main implemented method reference remains Newson and Krumm2009, documented in `hmm-method.md`. The user-provided Uber Maps summary informed the high-level explanation; no original video URL was available or inspected.
