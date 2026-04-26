import strawberry
from api.queries import Query
from api.mutations import Mutation

schema = strawberry.Schema(query=Query, mutation=Mutation)
