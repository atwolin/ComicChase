from django.contrib.postgres.search import TrigramSimilarity
from rest_framework.filters import BaseFilterBackend


class TrigramSearchFilter(BaseFilterBackend):
    """
    使用 PostgreSQL pg_trgm 進行相似度搜尋
    """

    def filter_queryset(self, request, queryset, view):
        search_query = request.query_params.get("search")
        search_fields = getattr(view, "search_fields", [])

        if not search_query or not search_fields:
            return queryset

        # 建立相似度計算
        total_similarity = None
        for field in search_fields:
            similarity = TrigramSimilarity(field, search_query)
            if total_similarity is None:
                total_similarity = similarity
            else:
                total_similarity += similarity

        if total_similarity is not None:
            return (
                queryset.annotate(similarity=total_similarity)
                .filter(similarity__gt=0.2)
                .order_by("-similarity")
            )

        return queryset

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": "search",
                "required": False,
                "in": "query",
                "description": "A search term.",
                "schema": {
                    "type": "string",
                },
            },
        ]
