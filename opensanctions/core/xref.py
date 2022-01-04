import structlog
from nomenklatura.index import Index

from opensanctions.core.dataset import Dataset
from opensanctions.core.loader import Database
from opensanctions.core.resolver import get_resolver

log = structlog.get_logger(__name__)


async def blocking_xref(dataset: Dataset, limit: int = 5000, fuzzy: bool = False):
    resolver = await get_resolver()
    resolver.prune()
    db = Database(dataset, resolver, cached=True)
    loader = await db.view(dataset)
    index = Index(loader)
    await index.build(fuzzy=fuzzy)
    suggested = 0
    for idx, (pair, score) in enumerate(index.pairs()):
        if idx % 1000 == 0:
            log.info("Evaluating pairs: %d (%d candidates)..." % (idx, suggested))
        left = await loader.get_entity(str(pair[0]))
        right = await loader.get_entity(str(pair[1]))
        if left is None or right is None:
            continue
        if left.schema not in right.schema.matchable_schemata:
            if right.schema not in left.schema.matchable_schemata:
                continue
        if not await resolver.check_candidate(left.id, right.id):
            continue
        await resolver.suggest(left.id, right.id, score)
        if suggested > limit:
            break
        suggested += 1
    await resolver.save()
