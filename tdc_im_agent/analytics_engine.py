import math
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
from .models import CanonicalRow

class AnalyticsEngine:
    """
    100% Deterministic analytics engine for TDC Influencer Marketing.
    Handles KPI calculations, dimensional aggregations, relationship checks,
    and statistical correlations without AI guesswork or causal claims.
    """

    @classmethod
    def compute_summary_table(
        cls,
        rows: List[CanonicalRow],
        dimension_attr: str
    ) -> List[Dict[str, Any]]:
        """
        Aggregates Total Spend, Views, Count, CPV, and Spend % for any dimension.
        dimension_attr can be: 'bucket', 'language', 'category', 'gender', 'creator'
        """
        groups: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"spend": 0.0, "views": 0, "count": 0})
        total_spend = sum(r.total_spends for r in rows)

        for r in rows:
            dim_val = getattr(r, dimension_attr, None)
            dim_str = str(dim_val or "Unspecified").strip()
            if not dim_str:
                dim_str = "Unspecified"
            
            groups[dim_str]["spend"] += float(r.total_spends)
            # Use views_brand_collab as primary metric, fallback to views_organic
            v = r.views_brand_collab if r.views_brand_collab > 0 else r.views_organic
            groups[dim_str]["views"] += int(v)
            groups[dim_str]["count"] += 1

        summary_rows = []
        for dim_name in sorted(groups.keys()):
            data = groups[dim_name]
            sp = data["spend"]
            vw = data["views"]
            cnt = data["count"]
            cpv = (sp / vw) if vw > 0 else 0.0
            sp_share = (sp / total_spend) if total_spend > 0 else 0.0
            summary_rows.append({
                "dimension": dim_name,
                "total_spends": sp,
                "views": vw,
                "count": cnt,
                "cpv": cpv,
                "spends_share": sp_share
            })

        return summary_rows

    @classmethod
    def compute_executive_metrics(cls, rows: List[CanonicalRow]) -> Dict[str, Any]:
        """Computes top-level campaign totals and deterministic KPIs."""
        total_reels = len(rows)
        total_spend = sum(r.total_spends for r in rows)
        total_views = sum(r.views_brand_collab if r.views_brand_collab > 0 else r.views_organic for r in rows)
        total_likes = sum(r.likes for r in rows)
        total_comments = sum(r.comments for r in rows)
        unique_creators = len(set(r.creator.strip().lower() for r in rows if r.creator.strip()))
        unique_skus = len(set(r.normalized_sku or r.product for r in rows if (r.normalized_sku or r.product).strip()))

        avg_cpv = (total_spend / total_views) if total_views > 0 else 0.0
        avg_er = ((total_likes + total_comments) / total_views) if total_views > 0 else 0.0

        # Quality metrics
        transcribed_count = sum(1 for r in rows if "Transcribed" in str(r.script_scraping_status))
        no_speech_count = sum(1 for r in rows if "no spoken" in str(r.script_scraping_status).lower())
        caption_only_count = sum(1 for r in rows if "cant scrap" in str(r.script_scraping_status).lower() or ("caption" in str(r.script_scraping_status).lower() and "no spoken" not in str(r.script_scraping_status).lower()))
        needs_review_count = sum(1 for r in rows if r.confidence_score < 0.7 or "Needs Review" in r.verification_notes)

        return {
            "total_reels": total_reels,
            "total_spend": total_spend,
            "total_views": total_views,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "unique_creators": unique_creators,
            "unique_skus": unique_skus,
            "avg_cpv": avg_cpv,
            "avg_er": avg_er,
            "transcribed_count": transcribed_count,
            "no_speech_count": no_speech_count,
            "caption_only_count": caption_only_count,
            "needs_review_count": needs_review_count
        }

    @classmethod
    def calculate_correlation(
        cls,
        x_vals: List[float],
        y_vals: List[float],
        x_label: str = "Spend",
        y_label: str = "Views"
    ) -> Optional[Dict[str, Any]]:
        """
        Calculates Pearson correlation coefficient ONLY if sample size >= 10.
        Adheres to Section 21: Never implies causation.
        """
        n = len(x_vals)
        if n < 10 or len(y_vals) != n:
            return None

        # Filter out invalid numbers
        pairs = [(float(x), float(y)) for x, y in zip(x_vals, y_vals) if not (math.isnan(x) or math.isnan(y))]
        if len(pairs) < 10:
            return None

        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]

        mean_x = sum(xs) / n
        mean_y = sum(ys) / n

        var_x = sum((x - mean_x) ** 2 for x in xs)
        var_y = sum((y - mean_y) ** 2 for y in ys)

        if var_x == 0 or var_y == 0:
            return {
                "metric": f"{x_label} vs {y_label}",
                "sample_size": n,
                "method": "Pearson",
                "coefficient": 0.0,
                "interpretation": "No variance in one of the variables",
                "limitations": "Zero variance detected. No correlation possible. Does not imply causation."
            }

        cov_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
        r = cov_xy / math.sqrt(var_x * var_y)

        if abs(r) > 0.7:
            interp = f"Strong statistical relationship (r={r:.2f})"
        elif abs(r) > 0.4:
            interp = f"Moderate statistical relationship (r={r:.2f})"
        else:
            interp = f"Weak or negligible statistical relationship (r={r:.2f})"

        return {
            "metric": f"{x_label} vs {y_label}",
            "sample_size": n,
            "method": "Pearson Correlation",
            "coefficient": round(r, 4),
            "interpretation": interp,
            "limitations": "Correlation measures linear association only and strictly does not imply causation."
        }
