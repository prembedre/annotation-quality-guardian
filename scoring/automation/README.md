\# Phase 4 Scoring \& Automation



This module contains the reusable scoring and automation logic for Phase 4 of Annotation Quality Guardian (AQG).



\## 1. Underperforming Annotator Detection



The underperformer detector combines:



\- Rolling gold-standard accuracy

\- TrustScore history

\- Minimum annotation history



\### Default thresholds



| Setting | Default |

|---|---:|

| Gold accuracy threshold | 0.90 |

| Trust score threshold | 0.60 |

| Minimum annotations | 10 |

| Rolling evaluation window | 30 days |



An annotator is considered underperforming when they have at least the minimum number of annotations in the rolling window and either:



1\. Their rolling gold accuracy is below `0.90`, or

2\. Their average available TrustScore is below `0.60`.



Annotators with insufficient annotation history are not flagged.



\## 2. Task Re-routing Logic



The rerouting module recommends a replacement annotator for a task that requires reassignment.



\### Default eligibility thresholds



| Setting | Default |

|---|---:|

| Minimum rolling accuracy | 0.90 |

| Minimum trust score | 0.60 |



A candidate is excluded when:



\- They are the original annotator.

\- They are marked as underperforming.

\- Their rolling accuracy is below `0.90`.

\- Their available trust score is below `0.60`.



Eligible annotators are ranked by:



1\. Rolling accuracy

2\. Average trust score as the secondary criterion



The highest-ranked eligible annotator is recommended.



If no eligible annotator exists, the module returns a recommendation with no replacement annotator.



The scoring layer only recommends the replacement annotator. The backend rerouting service is responsible for performing the actual task reassignment.



\## 3. A/B Testing Analysis



The A/B testing module compares label schema variants `A` and `B`.



The analysis includes:



\- Total annotations

\- Gold-standard annotations

\- Gold-standard correct annotations

\- Gold accuracy

\- Average annotation confidence

\- Average annotation duration



Schema variants are read from annotation metadata using the `schema\_version` field.



The variant with higher gold accuracy is recommended. If both variants have equal accuracy, no variant is recommended.



\## 4. Ambiguous Class Detection



The ambiguity detector uses annotator disagreement patterns from the existing scoring system.



\### Default thresholds



| Setting | Default |

|---|---:|

| Disagreement threshold | 0.50 |

| Minimum comparisons | 5 |



A class is considered ambiguous when:



\- It has at least 5 comparison events, and

\- Its disagreement rate is at least 50%.



Classes are returned with their disagreement count, occurrence count, total comparison count, and disagreement rate.



\## 5. Backend Integration



`scoring/phase4.py` provides reusable entry points for backend integration:



\- `build\_underperformer\_analytics()`

\- `build\_rerouting\_recommendation()`

\- `build\_ab\_test\_analytics()`

\- `build\_ambiguity\_analytics()`



These functions expose the Phase 4 decision-making logic without requiring the backend to duplicate the scoring algorithms.



\## 6. Phase 4 Automation Flow



```text

Annotation History + TrustScore

&#x20;             |

&#x20;             v

&#x20;   Underperformer Detection

&#x20;             |

&#x20;             v

&#x20;     Task Needs Re-routing

&#x20;             |

&#x20;             v

&#x20;   Eligible Annotator Filter

&#x20;             |

&#x20;             v

&#x20;    Best Annotator Selected

&#x20;             |

&#x20;             v

&#x20;      Backend Reassignment





Annotation Data + Gold Labels

&#x20;             |

&#x20;             v

&#x20;       A/B Analysis

&#x20;             |

&#x20;             v

&#x20;    Better Schema Recommendation





Annotation Disagreement Patterns

&#x20;             |

&#x20;             v

&#x20;   Ambiguous Class Detection

&#x20;             |

&#x20;             v

&#x20;      Label Clarity Insight

