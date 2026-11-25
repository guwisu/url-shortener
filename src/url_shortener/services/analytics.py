from datetime import UTC, datetime
from typing import Any

from pymongo.asynchronous.collection import AsyncCollection

from url_shortener.core.exceptions import LinkNotFound
from url_shortener.repositories import LinkRepository
from url_shortener.schemas.analytics import (
    DailyClicks,
    DeviceStat,
    LinkStatsResponse,
    RefererStat,
)


class AnalyticsService:
    def __init__(self, link_repo: LinkRepository, collection: AsyncCollection):
        self.link_repo = link_repo
        self.collection = collection

    async def get_link_stats(
        self,
        user_id: int,
        code: str,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
    ) -> LinkStatsResponse:
        link = await self.link_repo.get_by_code(user_id, code)
        if not link:
            raise LinkNotFound

        match_stage: dict[str, Any] = {"short_code": code}
        if from_dt or to_dt:
            ts_filter: dict[str, datetime] = {}
            if from_dt:
                ts_filter["$gte"] = (
                    from_dt if from_dt.tzinfo else from_dt.replace(tzinfo=UTC)
                )
            if to_dt:
                ts_filter["$lte"] = to_dt if to_dt.tzinfo else to_dt.replace(tzinfo=UTC)
            match_stage["timestamp"] = ts_filter

        pipeline: list[dict[str, Any]] = [
            {"$match": match_stage},
            {
                "$facet": {
                    "total": [{"$count": "count"}],
                    "by_day": [
                        {
                            "$group": {
                                "_id": {
                                    "$dateToString": {
                                        "format": "%Y-%m-%d",
                                        "date": "$timestamp",
                                    }
                                },
                                "clicks": {"$sum": 1},
                            }
                        },
                        {"$sort": {"_id": 1}},
                        {"$project": {"_id": 0, "date": "$_id", "clicks": 1}},
                    ],
                    "top_referers": [
                        {
                            "$group": {
                                "_id": {"$ifNull": ["$referer", "direct"]},
                                "clicks": {"$sum": 1},
                            }
                        },
                        {"$sort": {"clicks": -1}},
                        {"$limit": 5},
                        {"$project": {"_id": 0, "referer": "$_id", "clicks": 1}},
                    ],
                    "devices": [
                        {
                            "$project": {
                                "device": {
                                    "$switch": {
                                        "branches": [
                                            {
                                                "case": {
                                                    "$regexMatch": {
                                                        "input": {
                                                            "$ifNull": [
                                                                "$user_agent",
                                                                "",
                                                            ]
                                                        },
                                                        "regex": "bot|crawler|spider|curl|httpx",
                                                        "options": "i",
                                                    }
                                                },
                                                "then": "bot",
                                            },
                                            {
                                                "case": {
                                                    "$regexMatch": {
                                                        "input": {
                                                            "$ifNull": [
                                                                "$user_agent",
                                                                "",
                                                            ]
                                                        },
                                                        "regex": "mobile|android|iphone|ipad",
                                                        "options": "i",
                                                    }
                                                },
                                                "then": "mobile",
                                            },
                                        ],
                                        "default": "desktop",
                                    }
                                }
                            }
                        },
                        {"$group": {"_id": "$device", "clicks": {"$sum": 1}}},
                        {"$sort": {"clicks": -1}},
                        {"$project": {"_id": 0, "device": "$_id", "clicks": 1}},
                    ],
                }
            },
        ]

        cursor = await self.collection.aggregate(pipeline)
        raw_results = await cursor.to_list(length=1)

        if not raw_results:
            return LinkStatsResponse(
                short_code=code,
                total_clicks=0,
                by_day=[],
                top_referers=[],
                devices=[],
            )

        facet = raw_results[0]
        total_clicks = facet["total"][0]["count"] if facet["total"] else 0

        return LinkStatsResponse(
            short_code=code,
            total_clicks=total_clicks,
            by_day=[DailyClicks(**item) for item in facet["by_day"]],
            top_referers=[RefererStat(**item) for item in facet["top_referers"]],
            devices=[DeviceStat(**item) for item in facet["devices"]],
        )
